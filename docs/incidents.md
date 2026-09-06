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

## 9. Tier 2 obfuscation testing: a real crash, a genuinely unexpected upstream discovery, and an honest breakdown that complicates a clean "100%"

Built against five real PyRIT converters (`Base64Converter`,
`LeetspeakConverter`, `CaesarConverter`, `CharSwapConverter`,
`AsciiSmugglerConverter` — the last implementing a specific published
technique, Unicode tag smuggling, not a generic "encoding" idea),
testing whether obfuscating a known-bad prompt lets it evade a
classifier that correctly caught the same prompt in plain text.

**Verified against a deliberately naive mock first**: a plain
keyword-matching classifier was almost completely defeated (0%
detection for Base64, Leetspeak, Caesar cipher, and ASCII smuggling) —
confirming the test pipeline itself correctly surfaces real
obfuscation-based bypasses when they genuinely exist, before trusting
any result against the real system.

**Running against Project 7's real classifier crashed immediately**
with `IndexError: list index out of range` on `response.content[0]`.
Investigated directly rather than patched blind: a standalone debug
script printing the full raw Anthropic response revealed
`stop_reason: 'refusal'` with `category: 'bio'` — Anthropic's own
upstream safety layer refusing to process 10 of 15 obfuscated inputs
entirely, before Project 7's own classification prompt ever ran, on
content with no biological subject matter at all. The most plausible
explanation: heavy obfuscation of text is itself a pattern associated
with attempts to evade downstream content filtering, independent of
what the underlying obfuscated content actually says — Anthropic's
safety classifier flagging the *technique*, not necessarily the
*content*. Fixed by explicitly handling an empty `response.content` as
its own case, distinctly labeled `"UPSTREAM REFUSAL"` rather than
silently folded into either "safe" or "our classifier judged this
injection."

**The clean run (15/15, 0 bypasses) required one more honest
breakdown before it meant what it appeared to mean**: of the 15
"caught" cases, only **5 were Project 7's own classifier correctly
reasoning about obfuscated content** — the remaining 10 were
Anthropic's upstream refusal intercepting the input before Project 7's
logic ever ran. Notably, `char_swap` (a noisy but still largely
human-readable obfuscation) was the only technique where every case
reached and was correctly judged by Project 7's own classifier
specifically; the other four techniques were mostly caught upstream
instead. A bare "100%, zero bypasses" headline would have been
technically true but materially overstated what this specific
project's own code actually demonstrated.

This surfaces a genuine, senior-level insight worth naming plainly:
red-teaming any system built on a hosted LLM API cannot always cleanly
separate "this system's own behavior" from "the underlying provider's
independent safety layer" — not a flaw in this project's test design,
but an honest, accurate account of how testing against managed AI
infrastructure actually works. A related, smaller observation: the
same obfuscated input did not always produce the same upstream-vs-
downstream split across separate runs (Leetspeak's outcome shifted
between an earlier diagnostic run and the final one) — a real,
practical reminder that testing against a live, non-deterministic
hosted model means identical inputs can genuinely produce different
outcomes run to run.

## What's verified, and what genuinely isn't yet

The full pipeline — a real PyRIT `PromptTarget`, a real taxonomy-based
dataset using PyRIT's native schema, and a real scoring/reporting
layer — has been run twice: once against a deliberately imperfect mock
(confirming the test suite itself correctly detects real weaknesses),
and once against Project 7's actual, live, Claude-API-backed
classifier (confirming the real system under test). Both runs are
genuine, not assumed.

As of incident #9, Tier 2's obfuscation-testing component (real PyRIT
converters, run against the real classifier) is also genuinely
complete — with the honest caveat that only 5 of 15 "caught" cases
reflect Project 7's own classifier logic specifically, the rest being
Anthropic's upstream safety layer.

What's explicitly NOT yet built, stated plainly:
- **Tier 2's remaining pieces**: multi-turn exploits via PyRIT's real
  `CrescendoAttack` (confirmed to require a second, separate
  adversarial-generator model, deliberately deferred pending explicit
  cost confirmation given the real API-call volume involved), and a
  larger, versioned red-team dataset beyond the current small,
  hand-curated set.
- **Tier 3** (autonomous agent safety testing against Project 7's
  actual orchestrator/planner, custom security harness work) — not
  started.
- A properly-scaled Entry-tier dataset — the current 9 prompts are a
  proof of concept, not a statistically meaningful sample size for a
  real evaluation claim.
- Testing against Project 5's RAG platform specifically (only Project
  7's classifier has been targeted so far).
- A more rigorous way to isolate Project 7's own classifier behavior
  from Anthropic's upstream safety layer specifically, given incident
  #9 confirmed the two are difficult to cleanly separate when testing
  obfuscated inputs.
