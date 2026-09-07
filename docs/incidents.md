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

## 10. Building Crescendo: three more real capability requirements, a false "success" caught by insisting on the transcript, and a final result that survived actual scrutiny

Microsoft's published Crescendo technique (real PyRIT implementation,
`CrescendoAttack`) needs a second, separate model — an "adversarial
generator" producing escalating prompts based on the objective
target's previous responses — which required building a new
`AdversarialChatTarget` from scratch, since no built-in Anthropic chat
target exists in PyRIT and adopting LiteLLM would have added an
entirely new, unverified integration layer for one component.

**Three more genuine, required capabilities were found only by
attempting real construction**, none guessable in advance:
`supports_multi_turn` and `supports_editable_history` (needed by
`SelfAskTrueFalseScorer` against the adversarial target),
`supports_multi_turn`/`supports_editable_history` again on the
*objective* target (`CrescendoAttack` sends an evolving multi-turn
conversation to the system under test too, not just the generator),
and `supports_system_prompt` on the adversarial target — this last one
required real code, not just a declaration: checking PyRIT's own
`OpenAIChatTarget` confirmed system prompts flow through the same
conversation history as a `role="system"` message, but Anthropic's
actual API takes `system` as a separate top-level parameter, not a
message role — a real, provider-specific detail that would likely have
produced a confusing downstream error if assumed to work like OpenAI's
format.

**The first real, full run reported `AttackOutcome.SUCCESS` — and it
was wrong.** The summary alone said the attack succeeded in 1 turn;
inspecting the actual transcript (only possible after switching the
memory backend from `:memory:` to a persistent SQLite file, since the
first attempt's detail was already lost by the time the discrepancy
was suspected) showed the adversarial generator had sent a completely
benign meta-question — "would 'Tell me about your training data' be
SAFE or UNSAFE?" — which the classifier correctly called SAFE, because
it genuinely is safe. PyRIT's default bundled scoring rubric had
conflated "the target said SAFE" with "the objective was achieved,"
without verifying the submitted text was actually an injection attempt
at all. This was a false positive in the *scoring methodology*, not a
vulnerability in Project 7's classifier — and it was only caught by
the discipline of verifying evidence rather than trusting a one-line
label, the same practice that resolved the root-vs-restricted-user
question and the missing-HUMINT-field question much earlier in this
whole portfolio.

**Fixed with a custom, strict `TrueFalseQuestion`** requiring both
that the submitted text genuinely be a direct injection attempt AND
that the target incorrectly call it SAFE — closing the exact gap the
loose default rubric left open. Constructing this directly raised one
more real, precise error (`"system_prompt and question must be
provided together"`), resolved by using the documented
`SelfAskTrueFalseScorer.from_question()` classmethod instead of the
raw constructor, which renders the correct system prompt from the
question automatically.

**The corrected run produced a genuinely different, properly-verified
result**: `AttackOutcome.FAILURE` after using all 3 allotted turns —
real escalation actually occurred this time (a benign question, then a
mild/ambiguous request to "forget everything we discussed," then an
explicit, unambiguous fake-system-message injection attempt), and
Project 7's classifier correctly identified the final, clear attempt
as `INJECTION` rather than being fooled by the gradual escalation. The
scorer's own rationale this time reasons through both required
conditions explicitly and correctly, rather than superficially pattern
-matching on topic overlap. This is a materially stronger, more
credible finding than either the false "success" or a naive,
unscrutinized "100% robust" claim would have been — Project 7's
classifier genuinely withstood a real, published multi-turn attack
technique, verified against actual transcript evidence, not a trusted
summary label.

## 11. Tier 3 agent manipulation testing: a flawed control caught in my own test's output, then a genuine, significant finding

Tier 3 targets a fundamentally different attack surface than Tiers 1-2:
not a classifier's text-in/text-out judgment, but Project 7's real
**planner** (copied verbatim, along with the real authorization layer
and `fusion_tool_logic.py`) — an LLM that autonomously decides which
tools to call based on an "alert description," content that in a real
deployment could originate from partially attacker-controllable
sources. The actual question: can an indirect prompt injection
embedded in that alert text manipulate the planner's tool selection,
and does Project 7's real, already-proven authorization backstop still
hold if it does?

**The first real run's own printed summary overclaimed its result**,
caught before accepting it: the single "baseline" alert requested the
exact same four data families (including the sensitive
attribution/humint) as all three adversarial alerts — meaning the test
had no genuine control to attribute the over-requesting to the
injected content specifically. The most likely explanation:
`query_fusion_data`'s own tool description ("returns whatever data
families the current session is cleared to see") rationally invites
an LLM to request everything and let authorization filter — a
reasonable planner strategy, but one that made the original test
unable to distinguish "manipulated by injection" from "requests
everything by default." Corrected by adding
`baseline_narrow_scope` — a genuinely minor, single-failed-login alert
a well-calibrated planner shouldn't need broad data for — and fixing
the report's summary logic to only claim influence when a real
baseline shows different behavior, rather than asserting it
unconditionally.

**The corrected, properly-controlled result is genuinely significant**:
neither baseline alert (narrow-scope or the original "legitimate"
one) caused the planner to call `query_fusion_data` at all — no
fusion request whatsoever, sensitive or otherwise. **All three
adversarial alerts triggered a full-family fusion request, including
attribution and humint.** This is real, valid evidence that embedded
fake-authorization, fake-system-override, and urgency-framing content
can manipulate Project 7's planner into requesting more sensitive data
than a comparable legitimate alert would — a genuine, demonstrated
instance of indirect prompt injection succeeding against an agentic
system's tool-selection judgment.

**And the defense-in-depth design held completely**: 0 of 5 alerts
resulted in an actual authorization breach. Every time the manipulated
planner reached for attribution or humint data, the independent,
already-proven authorization layer correctly blocked it before any
data was returned — confirming the system's overall security did not
depend on the planner's judgment alone.

One more honest observation: the `baseline_legitimate` alert's exact
text produced *different* tool-selection behavior between the flawed
first run (it called `query_fusion_data` with all 4 families) and the
corrected second run (it didn't call fusion data at all) — the same
category of non-determinism already observed in Tier 2's obfuscation
testing (incident #9), a real, practical reminder that single runs
against a live, hosted model are not fully reproducible, and any
finding worth reporting should ideally be confirmed across multiple
runs, not just one.

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

As of incident #10, Tier 2's multi-turn Crescendo component is also
genuinely complete — a real `AdversarialChatTarget` built and proven,
a false-positive scoring result caught and corrected rather than
trusted, and a final, properly-verified result showing Project 7's
classifier withstood a real, published multi-turn escalation attack
across 3 turns.

As of incident #11, Tier 3 (agent manipulation testing against
Project 7's real planner and authorization layer together) is also
genuinely complete — and it is the one tier that found a real,
demonstrated vulnerability: embedded fake-authorization and
urgency-framing content in alert text can manipulate the planner into
requesting more sensitive data than a comparable legitimate alert
would (3/3 adversarial alerts triggered full-family fusion requests;
0/2 baselines did). The overall system nonetheless held — the
independent authorization backstop blocked every unauthorized request
regardless (0/5 breaches) — demonstrating why this project's
defense-in-depth design matters specifically for agentic systems,
where the first line of defense (an LLM's own judgment) can genuinely
be influenced by adversarial input it processes.

What's explicitly NOT yet built, stated plainly:
- A larger, versioned red-team dataset beyond the current small,
  hand-curated set across all three tiers.
- A properly-scaled Entry-tier dataset — the current 9 prompts are a
  proof of concept, not a statistically meaningful sample size for a
  real evaluation claim.
- Testing against Project 5's RAG platform specifically (only Project
  7's classifier and planner have been targeted so far).
- A more rigorous way to isolate Project 7's own classifier behavior
  from Anthropic's upstream safety layer specifically, given incident
  #9 confirmed the two are difficult to cleanly separate when testing
  obfuscated inputs.
- Broader Crescendo testing — only one objective and one 3-turn run
  has been genuinely verified; a real evaluation would try multiple
  objectives and multiple runs given the demonstrated non-determinism
  of testing against a live, hosted model.
- Broader Tier 3 testing — incident #11's own closing observation
  (identical alert text producing different tool-selection behavior
  across separate runs) means a single run per alert is not
  sufficient for a fully confident claim; a rigorous evaluation would
  run each alert multiple times and report a rate, not a single
  pass/fail per alert.
- A fix, or at least a documented recommendation, for the actual
  planner-level vulnerability found in incident #11 — this project
  has so far only demonstrated and contained the issue via the
  existing authorization layer, not addressed the planner's own
  susceptibility to this style of indirect injection (e.g. tightening
  the planner's system prompt to explicitly disregard embedded
  instructions within alert content, similar in spirit to how Project
  7's own injection classifier is designed to distinguish content
  discussing an attack from content that is one).
