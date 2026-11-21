"""Idempotent Google Colab setup for the GDG Essex data-agent workshop.

Participant authentication is through Colab Application Default Credentials (ADC).
Vertex AI is selected explicitly; no Gemini API key is required.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TABLE_NAMES = ("suppliers", "products", "inventory_snapshot", "fulfillment_orders")
VIEW_NAMES = (
    "v_inventory_product_risk",
    "v_supplier_delivery_performance",
    "v_fulfillment_order_exposure",
    "v_inventory_risk_summary",
    "v_fulfillment_risk_summary",
    "v_supplier_cross_domain_risk",
)
EXPECTED_ROWS = {
    "suppliers": 8,
    "products": 60,
    "inventory_snapshot": 60,
    "fulfillment_orders": 500,
}
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass
class WorkshopEnvironment:
    config: dict[str, Any]
    bigquery: Any
    project_id: str
    dataset_id: str
    location: str
    model_id: str
    model_location: str
    repo_dir: Path


def _read_config(config_path: str | Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is missing. Run the notebook bootstrap/install cell first.") from exc
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Workshop config not found: {path}")
    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    required = {
        "project_id": config.get("google_cloud", {}).get("project_id"),
        "source_project_id": config.get("source_data", {}).get("project_id"),
        "source_dataset_id": config.get("source_data", {}).get("dataset_id"),
    }
    placeholders = [k for k, v in required.items() if not v or str(v).startswith("REPLACE_")]
    if placeholders:
        raise ValueError(
            "Complete these values in config/workshop_config.yaml before setup: "
            + ", ".join(placeholders)
        )
    for key in ("project_id", "source_project_id", "source_dataset_id"):
        if not _IDENTIFIER.fullmatch(str(required[key])):
            raise ValueError(f"Invalid identifier for {key}: {required[key]!r}")
    dataset_id = config.get("google_cloud", {}).get("dataset_id", "essex_workshop")
    if not _IDENTIFIER.fullmatch(str(dataset_id)):
        raise ValueError(f"Invalid BigQuery dataset_id: {dataset_id!r}")
    return config


def _configure_vertex_ai(config: dict[str, Any]) -> tuple[str, str, str]:
    project_id = config["google_cloud"]["project_id"]
    model_id = config.get("vertex_ai", {}).get("model_id", "gemini-3.8-flash")
    model_location = config.get("vertex_ai", {}).get("location", "global")
    # Explicitly select Vertex AI for both ADK and the Google Gen AI SDK.
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = model_location
    # Avoid accidentally inheriting an AI Studio key from the Colab environment.
    os.environ.pop("GOOGLE_API_KEY", None)
    return project_id, model_id, model_location


def _ensure_colab_adc() -> None:
    try:
        from google.colab import auth
    except ImportError as exc:
        raise RuntimeError(
            "This participant setup is designed for Google Colab. Open the notebook in Colab."
        ) from exc
    # Safe to call again in the same runtime; Colab manages the credential flow.
    auth.authenticate_user()


def _prepare_bigquery(config: dict[str, Any], repo_dir: Path):
    from google.cloud import bigquery
    from google.api_core.exceptions import NotFound

    project_id = config["google_cloud"]["project_id"]
    dataset_id = config["google_cloud"].get("dataset_id", "essex_workshop")
    location = config["google_cloud"].get("bigquery_location", "US")
    source_project = config["source_data"]["project_id"]
    source_dataset = config["source_data"]["dataset_id"]

    client = bigquery.Client(project=project_id, location=location)
    destination_id = f"{project_id}.{dataset_id}"

    try:
        destination = client.get_dataset(destination_id)
        if destination.location.upper() != location.upper():
            raise ValueError(
                f"Destination dataset {destination_id} is in {destination.location}, "
                f"not configured location {location}."
            )
        print(f"Reusing destination dataset {destination_id} ({destination.location}).")
    except NotFound:
        dataset = bigquery.Dataset(destination_id)
        dataset.location = location
        dataset.description = "GDG Essex enterprise data agents workshop dataset"
        client.create_dataset(dataset)
        print(f"Created destination dataset {destination_id} ({location}).")

    source_id = f"{source_project}.{source_dataset}"
    source_meta = client.get_dataset(source_id)
    if source_meta.location.upper() != location.upper():
        raise ValueError(
            f"Source dataset is in {source_meta.location}; destination is {location}. "
            "BigQuery copy jobs require compatible locations."
        )

    for table_name in TABLE_NAMES:
        src = f"{source_id}.{table_name}"
        dst = f"{destination_id}.{table_name}"
        try:
            client.get_table(src)
        except NotFound as exc:
            raise FileNotFoundError(f"Required workshop source table not found: {src}") from exc
        try:
            existing = client.get_table(dst)
            print(f"Keeping existing table {dst} ({existing.num_rows:,} rows); not overwritten.")
            continue
        except NotFound:
            pass
        job = client.copy_table(
            src, dst,
            job_config=bigquery.CopyJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_EMPTY
            ),
            location=location,
        )
        job.result()
        copied = client.get_table(dst)
        print(f"Copied {table_name}: {copied.num_rows:,} rows.")

    sql_path = repo_dir / "semantic_catalogue" / "sql" / "metric_views.sql"
    sql = sql_path.read_text(encoding="utf-8")
    sql = sql.replace(
        "PROJECT_ID.gdg_essex_data_agents",
        f"{project_id}.{dataset_id}",
    )
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    if len(statements) != len(VIEW_NAMES):
        raise ValueError(f"Expected {len(VIEW_NAMES)} view statements, found {len(statements)}.")

    for view_name, statement in zip(VIEW_NAMES, statements):
        view_id = f"{destination_id}.{view_name}"
        try:
            client.get_table(view_id)
            print(f"Keeping existing view {view_name}; not replaced.")
            continue
        except NotFound:
            pass
        statement = re.sub(
            r"^CREATE\s+OR\s+REPLACE\s+VIEW",
            "CREATE VIEW",
            statement,
            flags=re.IGNORECASE,
        )
        client.query(statement, location=location).result()
        print(f"Created semantic view {view_name}.")

    # Structural validation; existing objects are never deleted or overwritten.
    for table_name, expected_rows in EXPECTED_ROWS.items():
        table = client.get_table(f"{destination_id}.{table_name}")
        if table.num_rows != expected_rows:
            raise ValueError(
                f"{table_name} has {table.num_rows} rows; expected {expected_rows}. "
                "Use a fresh destination dataset if this is unrelated existing data."
            )
    for view_name in VIEW_NAMES:
        view = client.get_table(f"{destination_id}.{view_name}")
        if view.table_type != "VIEW":
            raise ValueError(f"{view_name} exists but is not a view.")
    print("BigQuery tables and semantic views validated.")
    return client


def initialise_workshop(
    config_path: str | Path | None = None,
    repo_dir: str | Path | None = None,
    authenticate: bool = True,
    prepare_data: bool = True,
) -> WorkshopEnvironment:
    """Authenticate, configure Vertex AI, prepare BigQuery, and return shared clients."""
    repo_dir = Path(repo_dir or Path.cwd()).resolve()
    config_path = Path(config_path or repo_dir / "config" / "workshop_config.yaml")
    config = _read_config(config_path)

    if authenticate:
        _ensure_colab_adc()

    project_id, model_id, model_location = _configure_vertex_ai(config)
    location = config["google_cloud"].get("bigquery_location", "US")
    dataset_id = config["google_cloud"].get("dataset_id", "essex_workshop")

    if prepare_data:
        bq = _prepare_bigquery(config, repo_dir)
    else:
        from google.cloud import bigquery
        bq = bigquery.Client(project=project_id, location=location)

    # Persist only non-secret runtime configuration outside the repository.
    runtime_config = {
        "project_id": project_id,
        "dataset_id": dataset_id,
        "bigquery_location": location,
        "model_id": model_id,
        "model_location": model_location,
        "repository_dir": str(repo_dir),
    }
    Path("/content/.gdg_essex_workshop_config.json").write_text(
        json.dumps(runtime_config, indent=2), encoding="utf-8"
    )
    return WorkshopEnvironment(
        config=config,
        bigquery=bq,
        project_id=project_id,
        dataset_id=dataset_id,
        location=location,
        model_id=model_id,
        model_location=model_location,
        repo_dir=repo_dir,
    )
