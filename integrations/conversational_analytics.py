"""Optional ADK integration with a pre-configured Conversational Analytics Data Agent.

Requires a Data Agent resource already created in Google Cloud and IAM access.
This is intentionally separate from the core workshop path.
"""
from __future__ import annotations
from typing import Any


def build_data_agent_toolset():
    """Return the ADK DataAgentToolset with ADC-backed credentials."""
    try:
        import google.auth
        from google.adk.tools.data_agent.config import DataAgentToolConfig
        from google.adk.tools.data_agent.credentials import DataAgentCredentialsConfig
        from google.adk.tools.data_agent.data_agent_toolset import DataAgentToolset
    except ImportError as exc:
        raise RuntimeError(
            "Install the optional ADK Data Agent integration dependencies and use an ADK version that includes DataAgentToolset."
        ) from exc
    credentials, _ = google.auth.default()
    return DataAgentToolset(
        credentials_config=DataAgentCredentialsConfig(credentials=credentials),
        data_agent_tool_config=DataAgentToolConfig(max_query_result_rows=100),
        tool_filter=["list_accessible_data_agents", "get_data_agent_info", "ask_data_agent"],
    )


def build_conversational_analytics_agent(data_agent_resource_name: str, model: str = "gemini-2.5-flash") -> Any:
    """Create an ADK agent that can call an existing governed data agent.

    data_agent_resource_name is the full resource name used in the prompt, e.g.
    projects/PROJECT/locations/LOCATION/dataAgents/AGENT_ID.
    """
    if not data_agent_resource_name or "/dataAgents/" not in data_agent_resource_name:
        raise ValueError("Provide the full projects/.../locations/.../dataAgents/... resource name.")
    try:
        from google.adk.agents import Agent
    except ImportError as exc:
        raise RuntimeError("Install google-adk to use this optional integration.") from exc
    toolset = build_data_agent_toolset()
    return Agent(
        name="gdg_essex_conversational_analytics_bridge",
        model=model,
        description="Optional ADK bridge to a pre-configured governed Conversational Analytics Data Agent.",
        instruction=(
            "Use ask_data_agent for all business data questions. The configured Data Agent resource is "
            f"{data_agent_resource_name}. Do not query raw tables directly, do not write data, and do not invent results. "
            "Preserve the workshop's semantic distinctions and cite the returned evidence."
        ),
        tools=[toolset],
    )
