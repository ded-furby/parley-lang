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

### 2026-07-29 — Parley 0.3.140 compact core skill

- Reduced the always-injected skill from 21,264 to 7,168 characters (66.3%)
  while retaining the prior exhaustive reference as an on-demand file.
- Added exact first-pass forms for typed empty lists, promptless input,
  literal braces, expression calls, conversion maybes, and direct map lookup.
- Made `./check` explicitly authoritative in isolated benchmark workspaces so
  sessions do not spend tool calls probing for a global compiler.
- Added a hard test gate keeping the core below 8,000 characters and covering
  the syntax patterns implicated by experiment 001.
- The three Parley task prompts now contain 8,615–8,659 characters, down from
  a baseline median of 22,473 characters (about 61.5%).
- Expected benchmark effect: fewer initial prompt tokens and fewer public-check
  repair turns. The next fresh-session report is the acceptance evidence.

## 002 — Compact-skill efficiency parity pilot

- Date: 2026-07-29
- Compiler: Parley 0.3.140, commit `b4bd7a4054db2ec967ddb04ad0288eb3dfb48776`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `1f0198f8fbbe0281f8a5a8f52e27d2de03b00c29f36b0a37d44fa8dedc2d445b`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `2718c72f8d9644ed2b9b41cda1f9dabf1095a45dd5b6f3d52864223f80d567d6`
- Report: `benchmarks/reports/002-efficiency-parity.html`

| Language | Hidden success | First public pass | Median checks | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 6/6 | 1.0 | 32,770.0 | 17.5059 | 0 |
| Python | 6/6 | 4/6 | 1.0 | 43,471.0 | 21.3212 | 2 |
| Rust | 6/6 | 6/6 | 1.0 | 43,249.0 | 20.0211 | 0 |

### Interpretation

Parley met the pilot acceptance gate: final correctness was preserved, median
reported tokens were 24.6% below Python and 24.2% below Rust, median elapsed
time was 17.9% below Python and 12.6% below Rust, and every Parley session
passed its first public check. Versus iteration 001, Parley's median tokens
fell 81.2%, median time fell 68.4%, and repair turns fell from 10 to 0.

The result is not uniform by task. Parley led compact ranges, was between the
baselines on bracket reporting, and trailed both baselines on inventory totals.
With only two replicates per cell, this establishes directional parity but not
a stable population estimate.

### Next experiment

Freeze Parley 0.3.140 and the current compact skill, then run 10 replicates per
task-language cell. Do not optimize against those confirmation outcomes until
the full 90-session matrix is complete. Preserve the result and report as
iteration 003.

## 003 — Ten-replicate confirmation

- Date: 2026-07-29
- Compiler: Parley 0.3.140, code/skill unchanged from iteration 002
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 10 replicates = 90 fresh sessions
- Result JSON SHA-256: `1ae43a70982986342ae893a14697e9c70c24f821d520eb72fe68b4dca5a1247f`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `2718c72f8d9644ed2b9b41cda1f9dabf1095a45dd5b6f3d52864223f80d567d6`
- Report: `benchmarks/reports/003-confirmation-gap.html`

| Language | Hidden success | First public pass | Median checks | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 30/30 | 23/30 | 1.0 | 33,100.0 | 21.6486 | 11 |
| Python | 30/30 | 24/30 | 1.0 | 28,711.5 | 16.0883 | 6 |
| Rust | 30/30 | 30/30 | 1.0 | 43,139.5 | 18.2593 | 0 |

### Gate result

Strict parity was **not confirmed**. Parley preserved 100% hidden success and
used 23.3% fewer median tokens than Rust, but used 15.3% more tokens than
Python and took longer than both baselines. The better-baseline gate therefore
fails.

### Diagnosed concentration

- Bracket report: Parley 8/10 first-pass, 41,027.5 median tokens; better token
  median than both baselines.
- Inventory totals: Parley 10/10 first-pass, 32,409.5 median tokens; above
  Python but below Rust.
- Compact ranges: Parley 5/10 first-pass, 66,314.5 median tokens; above both
  baselines and responsible for eight of Parley's eleven repair turns.
- The failed Parley first attempts used reserved `position` as a variable,
  command words such as `add` at the start of helper names, `changing` at call
  sites, or unparenthesized complex item/call expressions.

### Next experiment

Make one predeclared skill/compiler pass against these exact failure classes,
reduce the clean-run prompt overhead further, add direct regression coverage,
then run a new immutable matrix. Do not alter or selectively rerun iteration
003.

## Engineering changes after 003

### 2026-07-29 — Parley 0.3.141 first-pass safe forms

- Reduced the always-injected skill from 7,168 to 4,340 characters (39.5%)
  while retaining the complete 21,224-character reference on demand.
- Reduced the three metered Parley task prompts to 5,787–5,831 characters,
  down about 32.8% from iteration 003's 8,615–8,659-character range.
- Put the four observed parse choices at the top of the core: never use
  reserved `position`, use one snake_case identifier for every name,
  parenthesize expression calls, and write `changing` only in declarations.
- Added exact P101 repair hints for reserved `position`, space-separated
  function names, unparenthesized condition calls, and `changing` at a call
  site.
- Added regression coverage for each diagnostic and for a clean compact-range
  program using temporary item values and a changing list helper.
- Expected benchmark effect: remove the seven Parley non-first-pass sessions
  seen in iteration 003 and reduce repeated prompt input on clean runs. This
  expectation remains unproven until iteration 004.

## 004 — First-pass safe-forms pilot

- Date: 2026-07-29
- Compiler: Parley 0.3.141, commit `79ecfbb6e63952edda41113df9ece5cd70aad59d`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `4c2e898195dadc2e53e5193d215cdaa49d99681d96451647856e24ea091f3ad7`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `35f535243703a2a66ed5dccf81f15d597619d59488a7aca9e63db187bc8acf16`
- Report: `benchmarks/reports/004-first-pass-pilot.html`

| Language | Hidden success | First public pass | Median checks | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 6/6 | 1.0 | 31,636.5 | 19.9827 | 0 |
| Python | 6/6 | 6/6 | 1.0 | 28,687.5 | 15.4619 | 0 |
| Rust | 6/6 | 6/6 | 1.0 | 43,202.0 | 19.8809 | 0 |

### Gate result

The targeted directional first-pass gate passed: all seven failure patterns
from iteration 003 were absent, and all Parley sessions passed their first
public check and the hidden cases. Strict efficiency parity still **failed**.
Parley used 10.3% more median tokens and 29.2% more median time than Python,
although it used 26.8% fewer median tokens than Rust.

### Integrity note

An initial sandboxed launcher attempt could not write the configured Codex
state database and exited all workers before session creation with zero
tokens. It was rejected as an infrastructure incident. The recorded matrix is
the subsequent complete rerun: 18 unique threads, no timeouts, no agent
failures, and no checker-integrity failures.

### Next experiment

Reduce clean-run prompt overhead again without removing the four rules that
prevented repairs. Run another immutable two-replicate pilot before spending
90 sessions on confirmation. Do not alter or selectively rerun iteration 004.

## Engineering changes after 004

### 2026-07-29 — Parley 0.3.142 sub-3k safe-forms core

- Reduced the always-injected skill from 4,340 to 2,998 characters (31.0%)
  without removing the first-pass rules validated directionally in iteration
  004; the 21,224-character extended reference remains unchanged.
- Reduced the metered Parley task prompts from 5,787–5,831 to
  4,445–4,489 characters (about 23.1%).
- Kept hard regression assertions for typed collections, promptless input,
  literal braces, map lookup, single-token names, reserved `position`,
  expression calls, declaration-only `changing`, temporary item values, and
  exclusive use of the supplied checker.
- Expected benchmark effect: reduce the 2,680-token median input gap observed
  in iteration 004 without reintroducing public-check repairs. This remains
  unproven until iteration 005.

## 005 — Sub-3k core regression pilot

- Date: 2026-07-29
- Compiler: Parley 0.3.142, commit `eaf63dbb5cbf63cc600c658c3ae25fcb62d45869`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `85bcc25c87ac2d54b99816b69df463efa556bc81bbc21de3d27fd25b93a4d4e5`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `15d71d0c8057ad9c7845f200da4119d975cb4d456b96d1bef22bc484d156c7a6`
- Report: `benchmarks/reports/005-overcompression-regression.html`

| Language | Hidden success | First public pass | Median checks | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 1/6 | 2.0 | 95,558.0 | 46.3064 | 7 |
| Python | 6/6 | 5/6 | 1.0 | 43,094.0 | 19.7339 | 1 |
| Rust | 6/6 | 5/6 | 1.0 | 36,383.5 | 23.4845 | 1 |

### Gate result

The sub-3k core **failed** the directional and strict gates. Hidden
correctness remained 100%, but Parley passed only one first public check and
used 121.7% more median tokens than Python and 162.6% more than Rust. Median
elapsed time was 134.7% above Python.

### Diagnosed omissions

- Both bracket sessions used `true`/`false` because the compact core no longer
  stated Parley's `yes`/`no` literals.
- One compact session used `stop` outside a loop after the break-only wording
  was shortened; another used unsupported `is equal to` / `is not equal to`
  spellings after the exact comparison list was removed.
- One inventory session twice malformed conversion as
  `number from text quantity_text` / `number from text_quantity` before
  reaching the accepted `number from quantity_text` form.
- The iteration-003 reserved-name, spaced-function-name, changing-call, and
  expression-call mistakes did not recur.

### Next experiment

Restore only the four missing guardrails above, assert them in the skill
regression test, and run a new immutable pilot. Treat 2,998 characters as
below the demonstrated reliability floor for this task family.

## Engineering changes after 005

### 2026-07-29 — Parley 0.3.143 reliability-floor recovery

- Restored `yes`/`no`, the exact comparison spellings, loop-only `stop`, and
  the unambiguous `number from quantity_text` form identified by iteration
  005, producing a 3,283-character core.
- Kept the core 24.4% smaller than iteration 004's 4,340-character version;
  metered task prompts are 4,730–4,774 characters versus 5,787–5,831 there.
- Added P201 replacements from `true`/`false` to `yes`/`no` and exact P101
  hints for `is equal to` / `is not equal to` and malformed
  `number from text variable` conversions.
- Expanded hard regression coverage for every newly observed omission. The
  next immutable pilot must recover first-pass success before any conclusion
  about the smaller prompt's efficiency is accepted.
