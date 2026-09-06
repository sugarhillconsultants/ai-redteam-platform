"""
reports/entry_tier_report.py

Runs the Entry-tier taxonomy-based prompt dataset through a target
(InjectionGuardrailTarget wrapping the classifier under test), and
produces a structured report — per-category detection rate, overall
accuracy, and specific misses — matching the "looks like a real
pentest report" standard: a clear threat model (the taxonomy), the
actual success/failure rate per category, and reproducible cases, not
a vague pass/fail summary.
"""

import asyncio
from collections import defaultdict

from pyrit.models.messages.message import Message
from pyrit.models.messages.message_piece import MessagePiece


async def run_entry_tier_report(target, prompts):
    """Runs every prompt in `prompts` (a list of PyRIT SeedPrompt
    objects) through `target`, comparing the actual result against
    each prompt's expected_flagged ground truth. Returns a structured
    report dict, not just printed output — so this can be consumed
    programmatically by later tiers, not only read by a human."""
    results = []

    for seed_prompt in prompts:
        msg = Message(message_pieces=[
            MessagePiece(role="user", original_value=seed_prompt.value)
        ])
        response = await target.send_prompt_async(message=msg)
        response_text = response[0].message_pieces[0].original_value

        actual_flagged = response_text.startswith("FLAGGED")
        expected_flagged = seed_prompt.metadata["expected_flagged"]

        results.append({
            "name": seed_prompt.name,
            "categories": seed_prompt.harm_categories,
            "prompt": seed_prompt.value,
            "expected_flagged": expected_flagged,
            "actual_flagged": actual_flagged,
            "correct": actual_flagged == expected_flagged,
            "response": response_text,
        })

    # Aggregate by category — a single overall pass rate hides which
    # SPECIFIC attack technique a classifier is actually weak against,
    # which is the whole point of a taxonomy-based test in the first place.
    by_category = defaultdict(lambda: {"total": 0, "correct": 0})
    for r in results:
        for category in r["categories"]:
            by_category[category]["total"] += 1
            if r["correct"]:
                by_category[category]["correct"] += 1

    overall_correct = sum(1 for r in results if r["correct"])

    return {
        "total_prompts": len(results),
        "overall_correct": overall_correct,
        "overall_accuracy": overall_correct / len(results) if results else 0,
        "by_category": dict(by_category),
        "failures": [r for r in results if not r["correct"]],
        "all_results": results,
    }


def print_report(report):
    print(f"Entry-Tier Report: {report['overall_correct']}/{report['total_prompts']} correct "
          f"({report['overall_accuracy']:.0%} accuracy)\n")

    print("By category:")
    for category, stats in sorted(report["by_category"].items()):
        rate = stats["correct"] / stats["total"] if stats["total"] else 0
        print(f"  {category}: {stats['correct']}/{stats['total']} ({rate:.0%})")

    if report["failures"]:
        print(f"\n{len(report['failures'])} failure(s) — reproducible cases:")
        for f in report["failures"]:
            print(f"  [{f['name']}] expected_flagged={f['expected_flagged']}, "
                  f"got actual_flagged={f['actual_flagged']}")
            print(f"    Prompt: {f['prompt'][:80]}")
    else:
        print("\nNo failures — classifier correctly handled every case in this tier.")
