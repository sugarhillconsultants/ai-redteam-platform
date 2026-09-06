"""
run_mid_tier_obfuscation_real.py

Runs the obfuscation testing suite against Project 7's REAL
llm_injection_classifier — 15 real Claude API calls (5 techniques x 3
base prompts). Genuinely the first time this has been run against the
real classifier.

Requires ANTHROPIC_API_KEY and ANTHROPIC_WORKSPACE_ID set.
Run: python3 run_mid_tier_obfuscation_real.py
"""
import asyncio
import sys

sys.path.insert(0, ".")

from pyrit.memory import CentralMemory
from pyrit.memory.sqlite_memory import SQLiteMemory

from targets.injection_guardrail_target import InjectionGuardrailTarget
from mid_tier.obfuscation_testing import run_obfuscation_report, print_obfuscation_report
from systems_under_test.project7_injection_classifier import llm_injection_classifier


async def main():
    CentralMemory.set_memory_instance(SQLiteMemory(db_path=":memory:"))

    target = InjectionGuardrailTarget(classifier_fn=llm_injection_classifier)

    print("Running 15 real obfuscated prompts (5 techniques x 3 base attacks) "
          "against Project 7's actual llm_injection_classifier...\n")

    report = await run_obfuscation_report(target)
    print_obfuscation_report(report)


if __name__ == "__main__":
    asyncio.run(main())
