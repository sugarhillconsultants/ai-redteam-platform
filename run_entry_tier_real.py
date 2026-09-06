"""
run_entry_tier_real.py

Runs the Entry-tier taxonomy-based test suite against Project 7's REAL
llm_injection_classifier — not a mock. This is genuinely the first
time this exact dataset has been run against the real classifier;
written but never executed until now.

Requires ANTHROPIC_API_KEY and ANTHROPIC_WORKSPACE_ID set in your
environment (the same real credentials already confirmed working for
Project 7's own manual classifier test).

Run: python3 run_entry_tier_real.py
"""
import asyncio
import sys

sys.path.insert(0, ".")

from pyrit.memory import CentralMemory
from pyrit.memory.sqlite_memory import SQLiteMemory

from targets.injection_guardrail_target import InjectionGuardrailTarget
from redteam_datasets.entry_tier_injection_prompts import ENTRY_TIER_PROMPTS
from reports.entry_tier_report import run_entry_tier_report, print_report
from systems_under_test.project7_injection_classifier import llm_injection_classifier


async def main():
    CentralMemory.set_memory_instance(SQLiteMemory(db_path=":memory:"))

    target = InjectionGuardrailTarget(classifier_fn=llm_injection_classifier)

    print(f"Running {len(ENTRY_TIER_PROMPTS)} real prompts against Project 7's actual "
          f"llm_injection_classifier via a live Claude API call per prompt...\n")

    report = await run_entry_tier_report(target, ENTRY_TIER_PROMPTS)
    print_report(report)


if __name__ == "__main__":
    asyncio.run(main())
