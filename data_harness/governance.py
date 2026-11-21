"""Schema discovery, conservative SQL validation and evidence provenance.

The workshop deliberately supports a narrow, reviewable SELECT-only surface.
It is not a general SQL parser or a substitute for BigQuery IAM.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class SchemaColumn:
    name: str
    field_type: str
    mode: str = "NULLABLE"
    description: str | None = None


@dataclass(frozen=True)
class SchemaSnapshot:
    table_id: str
    table_type: str
    columns: tuple[SchemaColumn, ...]
    discovered_at_utc: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "table_type": self.table_type,
            "columns": [asdict(column) for column in self.columns],
            "discovered_at_utc": self.discovered_at_utc,
        }


class BigQuerySchemaDiscovery:
    """Discover schemas only for explicitly approved tables/views."""
    def __init__(self, client: Any, project_id: str, dataset_id: str, approved_objects: tuple[str, ...]):
        self.client = client
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.approved_objects = frozenset(approved_objects)

    def discover(self, object_name: str) -> SchemaSnapshot:
        if object_name not in self.approved_objects:
            raise PermissionError(f"Schema discovery is not allowed for '{object_name}'.")
        table_id = f"{self.project_id}.{self.dataset_id}.{object_name}"
        table = self.client.get_table(table_id)
        columns = tuple(
            SchemaColumn(
                name=field.name,
                field_type=field.field_type,
                mode=getattr(field, "mode", "NULLABLE"),
                description=getattr(field, "description", None),
            )
            for field in table.schema
        )
        return SchemaSnapshot(
            table_id=table_id,
            table_type=getattr(table, "table_type", "UNKNOWN"),
            columns=columns,
            discovered_at_utc=datetime.now(timezone.utc).isoformat(),
        )


@dataclass(frozen=True)
class QueryValidationResult:
    approved: bool
    normalized_sql: str
    referenced_objects: tuple[str, ...]
    checks: tuple[str, ...]
    reason: str | None = None


class ReadOnlyQueryValidator:
    """Conservative guard for workshop SELECTs over approved semantic views."""
    FORBIDDEN = re.compile(
        r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|EXPORT|CALL|EXECUTE|GRANT|REVOKE|LOAD|DECLARE|BEGIN|COMMIT|ROLLBACK)\b",
        re.IGNORECASE,
    )
    TABLE_REF = re.compile(r"(?:FROM|JOIN)\s+`?([A-Za-z0-9_.-]+)`?", re.IGNORECASE)

    def __init__(self, project_id: str, dataset_id: str, approved_views: tuple[str, ...], require_limit: bool = True):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.approved_views = frozenset(approved_views)
        self.require_limit = require_limit

    def validate(self, sql: str) -> QueryValidationResult:
        if not isinstance(sql, str) or not sql.strip():
            return QueryValidationResult(False, "", (), (), "SQL is empty.")
        statement = sql.strip()
        # Allow one optional trailing semicolon, but reject multi-statement input.
        if ";" in statement.rstrip(";"):
            return QueryValidationResult(False, statement, (), (), "Only one SQL statement is allowed.")
        statement = statement.rstrip(";").strip()
        if not re.match(r"^(SELECT|WITH)\b", statement, re.IGNORECASE):
            return QueryValidationResult(False, statement, (), (), "Only SELECT or WITH ... SELECT statements are allowed.")
        if self.FORBIDDEN.search(statement):
            return QueryValidationResult(False, statement, (), (), "A prohibited SQL operation was detected.")
        if re.search(r"\b(EXTERNAL_QUERY|ML\.PREDICT|REMOTE_FUNCTION)\s*\(", statement, re.IGNORECASE):
            return QueryValidationResult(False, statement, (), (), "External or remote function calls are not allowed in this lab.")
        refs = tuple(dict.fromkeys(self.TABLE_REF.findall(statement)))
        if not refs:
            return QueryValidationResult(False, statement, (), (), "The query must read an approved semantic view.")
        allowed_full = {f"{self.project_id}.{self.dataset_id}.{name}" for name in self.approved_views}
        allowed_short = set(self.approved_views)
        invalid = [ref for ref in refs if ref not in allowed_full and ref not in allowed_short]
        if invalid:
            return QueryValidationResult(False, statement, refs, (), f"Unapproved source(s): {', '.join(invalid)}")
        if self.require_limit and not re.search(r"\bLIMIT\s+\d+\b", statement, re.IGNORECASE):
            return QueryValidationResult(False, statement, refs, (), "A numeric LIMIT is required for workshop queries.")
        checks = ("single_statement", "select_only", "approved_semantic_views", "bounded_result")
        return QueryValidationResult(True, statement, refs, checks)


def build_evidence_provenance(
    *, metric: dict[str, Any], source_view: str, sql: str,
    query_job: Any | None = None, snapshot_date: str | None = None,
    row_count: int | None = None, validation_checks: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Create a compact, serialisable evidence lineage record."""
    job_stats = getattr(query_job, "_properties", {}).get("statistics", {}) if query_job is not None else {}
    query_stats = job_stats.get("query", {}) if isinstance(job_stats, dict) else {}
    return {
        "metric_id": metric.get("id"),
        "metric_name": metric.get("name"),
        "metric_unit": metric.get("unit"),
        "metric_grain": metric.get("entity_grain"),
        "metric_formula": metric.get("formula"),
        "source_view": source_view,
        "snapshot_date": snapshot_date,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "query_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        "query_job_id": getattr(query_job, "job_id", None) if query_job is not None else None,
        "bytes_processed": query_stats.get("totalBytesProcessed"),
        "row_count": row_count,
        "validation_checks": list(validation_checks),
        "read_only": True,
    }


def run_validated_bigquery_query(
    *, client: Any, validator: ReadOnlyQueryValidator, sql: str,
    location: str = "US", maximum_bytes_billed: int = 50_000_000,
    query_parameters: list[Any] | None = None,
) -> dict[str, Any]:
    """Validate, dry-run, then execute one bounded SELECT with a cost ceiling."""
    result = validator.validate(sql)
    if not result.approved:
        raise PermissionError(f"Query rejected by Data Harness: {result.reason}")
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise RuntimeError("Install google-cloud-bigquery to execute the validated query.") from exc

    dry_config = bigquery.QueryJobConfig(
        query_parameters=query_parameters or [], dry_run=True, use_query_cache=False,
        maximum_bytes_billed=maximum_bytes_billed,
    )
    dry_job = client.query(result.normalized_sql, job_config=dry_config, location=location)
    estimated_bytes = getattr(dry_job, "total_bytes_processed", None)
    if estimated_bytes is not None and estimated_bytes > maximum_bytes_billed:
        raise PermissionError(
            f"Query estimate {estimated_bytes:,} bytes exceeds the {maximum_bytes_billed:,}-byte workshop ceiling."
        )

    run_config = bigquery.QueryJobConfig(
        query_parameters=query_parameters or [], use_query_cache=True,
        maximum_bytes_billed=maximum_bytes_billed,
    )
    job = client.query(result.normalized_sql, job_config=run_config, location=location)
    rows = [dict(row.items()) for row in job.result()]
    return {
        "rows": rows,
        "row_count": len(rows),
        "validation": {
            "approved": result.approved,
            "referenced_objects": list(result.referenced_objects),
            "checks": list(result.checks),
            "estimated_bytes": estimated_bytes,
            "maximum_bytes_billed": maximum_bytes_billed,
        },
        "query_job": job,
        "sql": result.normalized_sql,
    }
