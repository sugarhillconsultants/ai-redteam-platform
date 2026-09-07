"""agents/orchestrator.py - the minimal real structure Project 7's
planner.py needs (InvestigationStep), copied verbatim."""
from dataclasses import dataclass, field


@dataclass
class InvestigationStep:
    agent_name: str
    tool_fn: object
    kwargs: dict = field(default_factory=dict)
