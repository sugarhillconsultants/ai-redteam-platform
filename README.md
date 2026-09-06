# AI Red-Teaming / Adversarial AI Testing Platform

The eighth project in this portfolio — a systematic, tiered adversarial
testing platform built around Microsoft's real PyRIT (Python Risk
Identification Tool) framework, directly targeting the actual LLM/agent
systems already built in Projects 5 and 7 of this portfolio, rather
than a generic, disconnected demo target.

## The three-tier structure

Modeled on real industry contract-tier descriptions for AI red-teaming
work:

1. **Entry-tier** (this repo's current state): standardized safety
   taxonomies (OWASP LLM Top 10), manual prompt injection, basic
   content classification — targeting Project 7's real injection
   classifier.
2. **Mid-tier** (planned): systemic model weaknesses, multi-turn
   exploits, a structured/versioned red-team dataset, using PyRIT's
   `converter` module for encoding-based jailbreak techniques.
3. **Senior-tier** (planned): autonomous agent safety — testing
   whether Project 7's actual orchestrator/planner and pre-dispatch
   authorization layer can be manipulated through indirect, multi-step
   interaction, plus custom security harness construction.

## Status: Entry-tier fully verified against real, live infrastructure

The full pipeline — a real PyRIT `PromptTarget` wrapping Project 7's
actual classifier, a taxonomy-based dataset using PyRIT's native
`SeedPrompt` schema, and a scoring/reporting layer — has been run
twice: once against a deliberately imperfect mock (confirming the test
suite itself correctly detects real weaknesses, not just always
passing), and once against Project 7's real, live,
Claude-API-backed classifier, scoring **9/9 (100%)**.

Getting here required finding and fixing 8 distinct real issues — three
genuine PyRIT API corrections (a keyword-only-init contract, a private
method requiring implementation, an undocumented-to-us memory backend
requirement), a real naming collision with an installed dependency, and
a real credential mix-up — full account in
[`docs/incidents.md`](docs/incidents.md).

**Stated honestly**: a 9/9 result on 9 curated prompts is a genuine,
positive sanity check, not yet a statistically meaningful, senior-level
adversarial evaluation. See `docs/incidents.md` #8 for the full,
calibrated account of what this result does and doesn't prove.

## What's in this repo

| Path | What it does | Verified? |
|---|---|---|
| `targets/injection_guardrail_target.py` | Real PyRIT `PromptTarget` wrapping the system under test | **Yes** — tested against both a mock and the real classifier |
| `redteam_datasets/entry_tier_injection_prompts.py` | 9 taxonomy-organized (OWASP LLM01) test prompts, using PyRIT's native schema | **Yes** |
| `reports/entry_tier_report.py` | Scoring/reporting logic, per-category breakdown | **Yes** — proven to correctly surface real weaknesses via the mock-classifier test |
| `systems_under_test/project7_injection_classifier.py` | Project 7's real classifier, copied verbatim | Same verification status as Project 7's own copy |
| `run_entry_tier_real.py` | Runs the suite against the real, live classifier | **Yes** — 9/9, confirmed |

## What I'd add next

1. Scale the Entry-tier dataset well beyond 9 prompts — automated
   paraphrasing/variant generation, not just hand-written examples.
2. Build Tier 2: multi-turn exploit chains and PyRIT's `converter`
   module for encoding-based obfuscation attacks.
3. Build Tier 3: target Project 7's actual orchestrator/planner and
   authorization layer directly, not just the standalone classifier.
4. Extend testing to Project 5's RAG platform.
