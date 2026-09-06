# Real Findings From Building This Project

Same rationale as every other project in this portfolio: an honest
account of what was actually discovered while writing and testing this
code, not a cleaned-up version of events.

## 1. PyPI package naming — `pyrit-ai` doesn't exist; the real name is just `pyrit`

`pip install pyrit-ai` (a plausible-sounding guess, matching the
"Python Risk Identification Tool" name) failed immediately with "no
matching distribution." Confirmed via a real search rather than
guessing further: Microsoft's actual PyPI package is named simply
`pyrit`.

## 2. A real system-package conflict, resolved with a standard, legitimate flag

The genuine `pip install pyrit` attempt got through most of its
dependency chain, then failed at the very end trying to replace
`PyJWT` — a package that had been installed via `apt`, not `pip`, on
this system, which pip can't cleanly manage. Confirmed the package had
actually failed to complete by checking `import pyrit` directly rather
than trusting the installer's own summary output. Fixed with
`pip install pyrit --ignore-installed PyJWT`, a standard, documented
way to tell pip to proceed around a specific system-managed package
rather than trying to replace it.

## 3. Three genuine PyRIT API corrections, found only by actually running the code

Writing `InjectionGuardrailTarget` (a `PromptTarget` subclass wrapping
Project 7's real injection classifier) against PyRIT's documented
public interface produced three distinct, real errors in sequence,
each requiring checking PyRIT's actual source rather than guessing
further:

- **Keyword-only `__init__` contract**: PyRIT's own "brick contract"
  enforcement rejects any `PromptTarget` subclass with positional
  `__init__` parameters after `self` — confirmed by the actual
  `TypeError` naming the exact violation, not documented anywhere I'd
  read beforehand.
- **The actual method to implement is private**: the documented public
  `send_prompt_async` is a concrete base-class method handling
  validation and normalization; the real abstract method requiring
  implementation is `_send_prompt_to_target_async`, only found by
  attempting to instantiate the class and reading the resulting
  `TypeError` naming the missing method. This method's real signature
  also turned out to receive the *full conversation history*, not
  just the current message — a detail directly useful for this
  project's planned multi-turn (Tier 2) work, discovered as a
  byproduct of fixing an unrelated error.
- **A required, undocumented-to-us memory backend**: constructing any
  `PromptTarget` at all raised `ValueError: Central memory instance
  has not been set` until `CentralMemory.set_memory_instance()` was
  called first with a real `SQLiteMemory` instance — PyRIT's actual
  architecture tracks all conversation state in a memory backend by
  design, not an optional add-on.

## 4. A real naming collision: this project's own `datasets/` package shadowed the real, installed `datasets` PyPI library

Naming this project's own test-data module `datasets/` — a reasonable,
obvious choice in isolation — collided with the actual Hugging Face
`datasets` package, pulled in as one of PyRIT's own dependencies.
Python silently resolved imports to the real installed package instead
of the local directory, producing a confusing `ModuleNotFoundError`
for a module that very much existed on disk. The same category of
mistake as Project 7's `fusion_server.py` naming collision (a local
name shadowing something already in scope) — fixed by renaming to
`redteam_datasets/`, a more specific, collision-resistant name.

## 5. Building the taxonomy dataset against PyRIT's own native schema, not an invented format

Before writing any test prompts, checking PyRIT's actual `SeedPrompt`
class directly (rather than assuming a format) confirmed it already
has a built-in `harm_categories: list[str]` field — genuinely PyRIT's
own intended data model for exactly this taxonomy-based use case, not
something to bolt on separately. The Entry-tier dataset was built
directly against this real schema, organized by OWASP LLM Top 10
(2025)'s LLM01: Prompt Injection sub-techniques — a real, standardized
taxonomy directly referenced in the job postings this project targets.

## 6. Proving the test suite itself works, before trusting its results

Before running the real dataset against Project 7's actual classifier,
it was run first against a deliberately imperfect mock classifier
(simple keyword matching) specifically to confirm the report correctly
surfaces *real* weaknesses rather than trivially reporting 100% success
regardless of input. It worked exactly as intended: the mock's real,
substantive gaps were correctly caught — a persona-jailbreak variant
using no hardcoded keyword (a genuine miss), and a false positive on
content merely *discussing* injection techniques (correctly flagged as
wrong, not accepted as correct). This is a test of the test itself,
not just the system under test — a real, deliberate verification step
before trusting any subsequent result.

## 7. A real credential mix-up caught before it produced a misleading result

The first live run against Project 7's actual classifier failed with
`AuthenticationError: invalid x-api-key` — not because of any code
defect, but because the exported environment variables held the
literal placeholder text from an example command (`"your-existing-key"`)
rather than the real credential values, copy-pasted without
substitution. Confirmed directly by echoing the variable's actual
value rather than assuming the export had worked correctly. A small,
human mistake, but a real one, worth recording honestly rather than
omitting — this project's discipline applies to procedural errors as
much as code defects.

## 8. The real result — and an honest calibration of what it does and doesn't prove

With the real classifier and real credentials correctly wired up, the
Entry-tier suite scored **9/9 (100%)** against Project 7's actual
`llm_injection_classifier`, across every category including the two
hardest cases (a persona-jailbreak variant, and correctly *not*
flagging content that merely discusses injection technique).

Stated plainly, to avoid overclaiming from a small sample: nine
curated, fairly clear-cut examples passing perfectly is a genuine,
positive sanity-check result — it is not yet the scale or adversarial
sophistication (hundreds of automatically-generated variants, novel
paraphrasing, techniques the classifier's prompt was never explicitly
written to anticipate) that a senior-level red-team evaluation
requires. This result confirms the Entry-tier foundation is correctly
built end to end; it is the right moment to build toward Tier 2's
larger, more adversarial testing, not a basis for declaring the
classifier definitively robust.

## What's verified, and what genuinely isn't yet

The full pipeline — a real PyRIT `PromptTarget`, a real taxonomy-based
dataset using PyRIT's native schema, and a real scoring/reporting
layer — has been run twice: once against a deliberately imperfect mock
(confirming the test suite itself correctly detects real weaknesses),
and once against Project 7's actual, live, Claude-API-backed
classifier (confirming the real system under test). Both runs are
genuine, not assumed.

What's explicitly NOT yet built, stated plainly:
- **Tier 2** (multi-turn exploits, PyRIT's `converter` module for
  encoding/obfuscation-based jailbreaks, a larger and versioned
  red-team dataset) — not started.
- **Tier 3** (autonomous agent safety testing against Project 7's
  actual orchestrator/planner, custom security harness work) — not
  started.
- A properly-scaled Entry-tier dataset — the current 9 prompts are a
  proof of concept, not a statistically meaningful sample size for a
  real evaluation claim.
- Testing against Project 5's RAG platform specifically (only Project
  7's classifier has been targeted so far).
