"""mcp_servers/fusion_tool_logic.py - copied verbatim from Project 7's
real, already-proven per-field authorized Accumulo access logic."""
from dataclasses import dataclass, field

from systems_under_test.agents.authorization import SessionContext, ToolCallRequest, authorize_tool_call

FIELD_VISIBILITY_MAP = {
    "sensor": "U",
    "enrichment": "U",
    "attribution": "S&REL_TO_FVEY",
    "humint": "TS&SI&NOFORN",
}


@dataclass
class FusionQueryResult:
    indicator: str
    authorized_data: dict = field(default_factory=dict)
    denied_fields: list = field(default_factory=list)
    audit_trail: list = field(default_factory=list)


def query_fusion_data(session, indicator, requested_families, data_source):
    result = FusionQueryResult(indicator=indicator)

    for family in requested_families:
        visibility = FIELD_VISIBILITY_MAP.get(family)

        if visibility is None:
            result.denied_fields.append({
                "field": family,
                "reason": f"Unknown data family '{family}' — no visibility mapping defined, denying by default",
            })
            continue

        request = ToolCallRequest(
            agent_name="FusionAgent", tool_name="query_fusion_data",
            required_visibility=visibility,
            description=f"Requesting '{family}' data for indicator {indicator}",
        )
        decision = authorize_tool_call(request, session)
        result.audit_trail.append(decision)

        if decision.allowed:
            value = data_source(indicator, family)
            if value is not None:
                result.authorized_data[family] = value
        else:
            result.denied_fields.append({"field": family, "reason": decision.reason})

    return result
