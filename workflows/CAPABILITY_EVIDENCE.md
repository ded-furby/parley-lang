# Workflow capability evidence

This record decides whether product work has earned a new general capability.
It exists to prevent benchmark transcripts or one-off implementations from
driving Parley's syntax and standard library.

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
