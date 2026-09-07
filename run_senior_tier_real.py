"""
run_senior_tier_real.py

Tier 3: runs 4 real alerts (1 baseline, 3 adversarial) through
Project 7's ACTUAL planner (real Claude tool-use calls) — genuinely
the first time this exact test has been run against the real system.
Tests whether embedded indirect injection in alert content can
manipulate the planner's tool selection, AND whether the real
authorization backstop still holds regardless.

Requires ANTHROPIC_API_KEY and ANTHROPIC_WORKSPACE_ID set.
Run: python3 run_senior_tier_real.py
"""
import asyncio
import sys

sys.path.insert(0, ".")


async def main():
    from systems_under_test.agents.authorization import SessionContext
    from systems_under_test.agents.fusion_tool_logic import query_fusion_data
    from systems_under_test.agents.planner import plan_investigation, plan_to_investigation_steps
    from senior_tier.agent_manipulation_testing import run_agent_manipulation_report, print_agent_manipulation_report

    print("Running 4 real alerts (1 baseline, 3 adversarial) through Project 7's "
          "actual planner via real Claude tool-use calls...\n")

    results = await run_agent_manipulation_report(
        plan_investigation_fn=plan_investigation,
        plan_to_investigation_steps_fn=plan_to_investigation_steps,
        query_fusion_data_fn=query_fusion_data,
        session_context_cls=SessionContext,
    )
    print_agent_manipulation_report(results)


if __name__ == "__main__":
    asyncio.run(main())
