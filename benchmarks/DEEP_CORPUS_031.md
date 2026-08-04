# Iteration 031 deeper-project corpus record

Frozen on 2026-08-05 before any measured agent output.

## Purpose

Iteration 030 showed that the diagnosis benchmark's Parley/Rust crossover is
mostly fixed-session amortization, while a small positive residual remains
against Python. Iteration 031 changes the workload shape, not the language or
instruction: each episode has five editable modules and three visibly
read-only evidence files. The task requires locating a policy or state defect
through multiple dependency layers, then repairing the predeclared owning
module.

These are deterministic cross-language adaptations, not reproductions of
upstream repositories. No upstream source code, test code, fixture, project
name, identifier, or prose is copied into the executable fixture.

## Primary issue sources and adaptations

| Frozen task | Primary source | Mechanism retained | Synthetic adaptation |
| --- | --- | --- | --- |
| Redirect credential scope | [OPA issue #3093](https://github.com/open-policy-agent/opa/issues/3093) | Proxy credentials can escape their hop boundary across a redirect | A five-module redirect auditor separates target rendering, end-to-end Authorization policy, hop-specific proxy policy, orchestration, and output |
| Empty collection configuration | [.NET Extensions issue #5858](https://github.com/dotnet/extensions/issues/5858) | An explicit empty array is semantically different from null or an absent value | A layered classifier/selector/count/formatter pipeline must preserve missing, null, empty, and populated states through precedence fallback |
| Forwarded external origin | [oauth2-proxy issue #724](https://github.com/oauth2-proxy/oauth2-proxy/issues/724) | An internal request host can replace the external host when constructing an OAuth redirect behind a gateway | A trust-aware header selector feeds origin construction, path joining, formatting, and orchestration, with per-field fallback |
| Terminal liveness reconciliation | [Codex issue #12321](https://github.com/openai/codex/issues/12321) | Persisted UI terminal state can remain “running” after the actual process has died | A five-module tracker reconciles cached state against an authoritative liveness probe before deriving reasons and summary counts |

The selected mechanisms cover four distinct semantic families: credential
scope, value-state preservation, trust-boundary reconstruction, and lifecycle
reconciliation. None is an arithmetic spelling or a narrow syntax transcript.

## Frozen corpus shape

- Four task repositories.
- Three languages: Parley, Python, Rust.
- Exactly five editable modules per task/language.
- Exactly three byte-identical read-only evidence files per task/language:
  issue, architecture flow, and regression record.
- One public multi-case bundle and four independently hidden cases per task.
- Exactly one predeclared root-defect file per task/language.
- The public prompt hides all concrete examples; agents receive evidence only
  through the protected `./sources` command and test only through `./check`.

| Language | Total source chars | Total source lines | Total rough source tokens | Median rough source tokens/task |
| --- | ---: | ---: | ---: | ---: |
| Parley | 6,297 | 162 | 1,306 | 338.0 |
| Python | 4,877 | 133 | 1,121 | 279.0 |
| Rust | 6,162 | 183 | 1,847 | 459.5 |

Read-only evidence is identical across languages: 3,454 characters, 48 lines,
and 634 rough lexical tokens for the complete four-task bundle. Median evidence
per task is 872 characters, 12 lines, and 159.5 rough tokens.

For comparison, iteration 029's median Parley task had 205 rough editable
tokens and 92.5 rough evidence tokens. Iteration 031 increases those medians by
64.9% and 72.4%, respectively, while moving from three to five editable
modules. The comparison is workload-shape context, not a gate.

## Pre-output validation

`validate_deep_corpus_031.py` materializes every seed and reference root fix in
an isolated temporary repository, compiles it with the pinned Parley binary,
Python, or Rust, and runs the public plus hidden cases.

- 12/12 buggy seed cells compile.
- Every buggy seed fails at least two of its five case groups.
- 12/12 isolated root-fix cells compile.
- 60/60 reference case groups pass exactly.
- Each reference changes only the frozen root file.
- Context files are byte-identical across languages.
- Task-schema validation passes through the production agent runner.

The reference fixes are validation evidence only. They are not copied into a
measured task workspace, prompt, checker output, or hidden judgment.

## Decision boundary

No compiler, grammar, diagnostic, prompt, skill, or runner change is part of
this corpus. The single allowed instruction-compression experiment remains
closed. A compiler proposal is eligible only if a semantic failure recurs
across independent project episodes and the proposed design is generally
useful, semantically consistent, maintainable, fully tested, and documented.

Efficiency alone cannot authorize syntax. A positive result must be reported
with the same strict better-baseline conditions as earlier work; a negative
result cannot trigger task selection, reference rewriting, or same-corpus
tuning.
