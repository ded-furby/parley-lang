# Agent efficiency experiment log

This is the durable memory for the fresh-context Parley agent benchmark.
Every material compiler, skill, harness, or diagnostic change gets a new
entry, a new immutable HTML report, and a commit before the next experiment.
Prior reports are never replaced or deleted.

## Acceptance target

Parley must preserve hidden-case correctness while reaching at least baseline
efficiency parity on the same declared task matrix and agent configuration.
The primary gate is median reported total tokens no higher than the better of
Python and Rust. Supporting gates are first-public-check success and median
elapsed time no worse than the better baseline. A result is directional until
confirmed with at least 10 replicates per task-language cell.

## 001 — Original pilot baseline

- Date: 2026-07-29
- Compiler: Parley 0.3.138, commit `98e613daeba50fdfe5c6e801e1365b920cb9ac4b`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `a94989fd901133ac7ffeefccf8f934885d437bc63aab7f752bc5a85382a5baf9`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `ca6a5034b736b16c1eda5529202c36887d951b28c046c1b2d2dc4516dbcc70bc`
- Report: `benchmarks/reports/001-pilot-baseline.html`

| Language | Hidden success | First public pass | Median checks | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 1/6 | 3.0 | 174,124.0 | 55.4335 | 10 |
| Python | 6/6 | 5/6 | 1.0 | 49,837.5 | 23.5351 | 1 |
| Rust | 6/6 | 5/6 | 1.0 | 57,275.5 | 24.2891 | 1 |

### Observed causes

1. The complete shipped skill contributed a median 22,473 prompt characters,
   versus 1,202 for Python and 1,213 for Rust. The skill itself was 21,264
   characters.
2. Agents missed typed empty-list syntax, literal-brace escaping, promptless
   input syntax, and parenthesized expression calls.
3. Two bracket runs hit P901 after emitting a mutable list removal whose index
   also borrowed the list immutably.
4. One inventory run received cascading maybe/map diagnostics that obscured
   the first actionable type mistake.
5. Some sessions tried a global `parley` command before the required `./check`,
   adding setup noise in the isolated environment.

### Next experiment

Create a compact task-facing Parley skill that retains the syntax and repair
rules needed for ordinary programs without embedding the full package catalog.
Make the benchmark command path explicit, add regression tests for the four
missed syntax forms, and fix the list-removal backend borrow conflict. Rerun the
same matrix before expanding the sample.

## Engineering changes after 001

### 2026-07-29 — Parley 0.3.139 borrow-safe item mutation

- Changed list/map `set item` and `remove item` lowering to evaluate indexes,
  keys, and replacement values before mutably borrowing the target.
- Added emitter and native-binary regression coverage for mutations whose
  arguments read the same collection.
- Verification: 261 tests passed.
- Expected benchmark effect: remove the P901 repair turn observed in both
  Parley bracket-report runs. This expectation remains unproven until the next
  fresh-session report.
