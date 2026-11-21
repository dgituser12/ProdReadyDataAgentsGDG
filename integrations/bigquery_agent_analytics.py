"""Optional BigQuery Agent Analytics plugin wiring for ADK Apps."""
from __future__ import annotations
from typing import Any


def attach_bigquery_agent_analytics(root_agent: Any, project_id: str, dataset_id: str, location: str = "US", app_name: str = "gdg_essex_agent_with_analytics") -> Any:
    """Wrap an existing ADK root agent in an App with BigQuery analytics enabled.

    Creates/uses the analytics events table in the target dataset. Grant the
    runtime identity the required BigQuery dataset/table and Storage Write API
    permissions. Consider payload redaction and retention before enabling.
    """
    try:
        from google.adk.apps import App
        from google.adk.plugins.bigquery_agent_analytics_plugin import BigQueryAgentAnalyticsPlugin
    except ImportError as exc:
        raise RuntimeError('The BigQuery Agent Analytics extra is included in requirements-agent.txt; rerun the notebook bootstrap if it is unavailable.') from exc
    plugin = BigQueryAgentAnalyticsPlugin(project_id=project_id, dataset_id=dataset_id, location=location)
    return App(name=app_name, root_agent=root_agent, plugins=[plugin])
