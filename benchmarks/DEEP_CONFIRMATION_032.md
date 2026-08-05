# Iteration 032 independent deeper-project corpus

Frozen on 2026-08-05 before protocol creation or measured model output.

## Independence

The four mechanisms were selected after the v0.3.158 product phase and are not
derived from any task, failure, repair, or metric in report 031. Report 031 was
used only to preserve the same five-module workload shape and predeclared
correctness, efficiency, first-check, and root-cause judgments.

Each issue supplies a semantic mechanism only. The deterministic fixtures,
module names, source, tests, and reference fixes are new cross-language
adaptations and copy no upstream implementation or test code.

## Historical grounding

- [Quarkus issue 35861](https://github.com/quarkusio/quarkus/issues/35861):
  quoted `.env` values retained their quote representation. The adaptation uses
  explicit `dq:` / `sq:` markers so all three benchmark languages receive the
  same line-oriented input without needing a JSON or dotenv dependency.
- [Microsoft Graph JavaScript SDK issue 42](https://github.com/microsoftgraph/msgraph-sdk-javascript/issues/42):
  `Retry-After` response evidence was not surfaced to callers. The adaptation
  tests server-header precedence over configured and default backoff.
- [Stripe Node issue 331](https://github.com/stripe/stripe-node/issues/331):
  webhook signature verification depends on access to the unparsed raw body.
  The adaptation compares deterministic signature tokens against captured and
  normalized representations; it does not implement or benchmark cryptography.
- [Langfuse discussion 7623](https://github.com/orgs/langfuse/discussions/7623):
  pagination returned duplicates when ordering used a non-unique timestamp.
  The adaptation requires a stable `(created_time, unique_id)` total order.

## Frozen structure

- Manifest: `agent_tasks_deep_confirmation_032.json`
- Manifest SHA-256:
  `49df28a27ce00ac58d898a386fcee1cae46fd15fd02c38ec82272b39a326bb1f`
- Reference fixes: `deep_reference_fixes_032.json`
- Reference SHA-256:
  `03e14e19bd608654dbc7b5bce0057b37789cecddae9d8541b72ce65cc1936e70`
- Builder: `build_deep_confirmation_032.py`
- Validator: `validate_deep_corpus_032.py`

Every task/language cell contains five editable modules and three visibly
read-only evidence files (`ISSUE.md`, `architecture/flow.md`, and
`tests/regression.txt`). Read-only evidence is byte-identical across languages.
Each task has one public multi-case group and four withheld case groups. The
owning defect file is frozen per language before any model session.

| Language | Editable chars | Editable lines | Rough editable tokens | Evidence chars | Evidence lines | Rough evidence tokens |
|---|---:|---:|---:|---:|---:|---:|
| Parley | 5,334 | 127 | 1,068 | 3,178 | 40 | 590 |
| Python | 3,895 | 95 | 894 | 3,178 | 40 | 590 |
| Rust | 4,926 | 125 | 1,493 | 3,178 | 40 | 590 |

## Pre-output validation

The production task loader accepts all four tasks. All 12 seeded language cells
compile and fail hidden/public behavior. Every isolated reference patch changes
only its frozen root file, compiles, and passes all five case groups: 60/60
cross-language case groups exact. Seed success counts are symmetric by task:
2/5 quoted environment, 3/5 retry precedence, 1/5 webhook body, and 3/5 stable
pagination.

No grammar, AST, checker, emitter, runtime, diagnostic, standard library,
Parley skill, agent instruction, runner, or scoring metric changed for this
corpus. The one instruction-compression experiment remains closed.
