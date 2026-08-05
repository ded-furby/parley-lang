# Workflow capability evidence

This record decides whether product work has earned a new general capability.
It exists to prevent benchmark transcripts or one-off implementations from
driving Parley's syntax and standard library.

## 2026-08-05 — v0.3.159 agent-data boundary

New evidence did **not** overturn the v0.3.158 workflow finding: only Release
Steward has weak structured-input pressure, and CSV still has none. The new
requirement is platform-level and independently useful: agents routinely
receive JSON context, and current TOON evidence suggests some uniform shapes
can be smaller while non-uniform or output-heavy use can be less reliable.

Decision: admit a **CLI translation layer**, not language syntax or a workflow
stdlib parser. `parley data` keeps the JSON data model as the semantic contract,
tries a conservative TOON 4.1 subset, proves exact decode equality, and selects
TOON only when a declared tokenizer measures strictly fewer tokens. All other
shapes retain compact JSON. The feature has no grammar, checker, emitter,
runtime, generated-Rust, workflow-manifest, or compact-skill change.

This is general because it operates on arbitrary strict JSON and publishes its
selection evidence; it is maintainable because it has no new runtime dependency
and unsupported forms fail or fall back deterministically. The next evidence
gate is a frozen, shape-diverse corpus followed by repeated comprehension tests.
Static compression alone will not justify claims about model accuracy. CSV,
HTTP, and JSON values inside Parley programs remain deferred until real product
pressure recurs.

The subsequent frozen iteration 033 diagnostic supported this boundary rather
than expanding it: exactness and adaptive coverage passed, but real-tokenizer
savings were about 4.57% and missed the 5% aggregate gate. Three record-heavy
documents benefited; nine retained JSON. Preserve the CLI layer and do not tune
the profile, workflow contracts, or language syntax from that corpus.

Iteration 034 independently confirms the narrow positive case without changing
that decision. Across 90 fresh exact-answer sessions on record-heavy contexts,
JSON and TOON are both 45/45 correct, while TOON uses fewer total tokens in all
45 matched pairs and passes the frozen 5/5 gate. This earns the adaptive CLI
input layer as a maintained feature. It still does not earn JSON/TOON language
syntax, agent-generated TOON, a workflow runtime parser, or removal of JSON
fallback.

## 2026-08-05 — v0.3.158 catalog review

Evidence reviewed:

| Workflow | Inputs | Structured-data pressure |
|---|---|---|
| Release Steward | three `key=value` evidence files and one Markdown checklist | Low; one local helper reads eight known scalar keys |
| Log Summary | plain-text service log | None; line matching is the product contract |
| Checklist Report | Markdown checklist | None; checklist lines are the product contract |

Decision: **defer JSON and CSV**. JSON pressure appears in one of three
products, only for flat scalar fields; CSV pressure appears in zero. Release
Steward's local `release_value` helper is shorter and clearer than introducing
a parser, typed data model, dependency, or new language syntax. It has not
recurred across unrelated workflows, so it is not promoted into `std/workflow`.

Reconsider structured input when at least two unrelated maintained workflows
need nested values, escaped text, typed rows, or repeated records and their
local parsing code is materially harder to test or maintain. Prefer a general
standard-library API with deterministic failures before considering syntax.

No compiler, grammar, checker, emitter, skill, or benchmark instruction changed
as a result of this review.
