"""agents/authorization.py - copied verbatim from Project 7's real,
already-proven pre-dispatch authorization layer. See docs/incidents.md."""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from systems_under_test.agents.visibility import evaluate_visibility, VisibilityParseError


@dataclass
class SessionContext:
    session_id: str
    held_authorizations: set


@dataclass
class ToolCallRequest:
    agent_name: str
    tool_name: str
    required_visibility: str
    description: str = ""


@dataclass
class AuthorizationDecision:
    request: object
    session_id: str
    allowed: bool
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def authorize_tool_call(request, session):
    try:
        allowed = evaluate_visibility(request.required_visibility, session.held_authorizations)
    except VisibilityParseError as e:
        return AuthorizationDecision(
            request=request, session_id=session.session_id, allowed=False,
            reason=f"Malformed visibility expression, denying by default: {e}",
        )

    if allowed:
        reason = (
            f"Session {session.session_id} holds authorizations "
            f"{sorted(session.held_authorizations)}, satisfying "
            f"required visibility '{request.required_visibility}'"
        )
    else:
        reason = (
            f"Session {session.session_id} holds authorizations "
            f"{sorted(session.held_authorizations)}, which do NOT satisfy "
            f"required visibility '{request.required_visibility}' — "
            f"tool call blocked before dispatch, not attempted"
        )

    return AuthorizationDecision(request=request, session_id=session.session_id, allowed=allowed, reason=reason)
