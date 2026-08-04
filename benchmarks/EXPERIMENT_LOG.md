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

## 006 — Reliability-floor recovery pilot

- Date: 2026-07-29
- Compiler: Parley 0.3.143, commit `e6227a558b7d90ee1ddbfb21370fdc426ff0987a`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `9b33b71ab9d2313b0a4b5e2e08e6e610872d0c89d45838c51777808dbd0ade1a`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `0fc414fed62ef5118cdc4c6edac9d646c89f7887609ba2154d22f1871418d686`
- Report: `benchmarks/reports/006-reliable-exploration-gap.html`

| Language | Hidden success | First public pass | Median checks | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 6/6 | 1.0 | 63,997.5 | 28.1329 | 0 |
| Python | 6/6 | 5/6 | 1.0 | 51,180.5 | 18.8539 | 1 |
| Rust | 6/6 | 5/6 | 1.0 | 43,190.5 | 18.7361 | 1 |

### Gate result

The reliability recovery passed: all six Parley sessions passed first check
and the hidden cases. Strict efficiency still **failed**. Parley used 25.0%
more median tokens than Python, 48.2% more than Rust, and about 50% more median
time than either baseline.

### Protocol diagnosis

Every Parley session ran an extra pre-solution command (`ls`, `rg --files`, or
`sed` over public checker/config files) before its successful `./check`.
Baseline sessions did this inconsistently. The prompt prohibited modifying
checker files but did not prohibit reading them, creating avoidable tool and
context variance despite identical task information already being present in
the prompt.

### Next experiment

Freeze Parley 0.3.143. Amend the language-neutral prompt to prohibit listing
or reading workspace files and require creating the solution immediately,
then running only `./check`. Record the protocol flag, test the rendered
prompt, and rerun all three languages as iteration 007.

## Engineering changes after 006

### 2026-07-29 — Fresh-agent benchmark protocol v2

- The language-neutral prompt now prohibits listing, reading, or inspecting
  existing workspace files and says all required information is already in
  the prompt.
- The first tool action must create the solution; after edits, the only
  permitted shell command is exactly `./check` for every language.
- Each run records `command_protocol_compliant` and the exact violating
  commands. Language summaries record compliance counts and rates.
- Added regression coverage for the prompt contract and command classifier.
- Parley 0.3.143, its skill, tasks, model, reasoning, seed, public cases, and
  hidden oracle remain frozen for iteration 007. This is an explicit protocol
  revision, so its metrics are reported separately rather than silently
  spliced into the earlier series.

## 007 — Exact-check-only protocol-v2 pilot

- Date: 2026-07-29
- Compiler: Parley 0.3.143, benchmark commit `339d854bdc38e41e8aa72c3ccb31d66898d7ebda`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `14dfef712901eac42983b1f9d36fe1bfdd9aadae39b82d0edcc1af58ed145d20`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `0fc414fed62ef5118cdc4c6edac9d646c89f7887609ba2154d22f1871418d686`
- Report: `benchmarks/reports/007-protocol-v2-near-parity.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 5/6 | 6/6 | 45,947.5 | 20.4253 | 3 |
| Python | 6/6 | 4/6 | 6/6 | 43,047.5 | 20.8073 | 2 |
| Rust | 6/6 | 6/6 | 6/6 | 43,604.5 | 19.6029 | 0 |

### Gate result

All 18 sessions complied with protocol v2 and passed hidden cases. Strict
parity still **failed**, but the gap narrowed sharply: Parley used 6.7% more
median tokens than Python and 5.4% more than Rust; it was 1.8% faster than
Python but 4.2% slower than Rust. Its 5/6 first-pass rate was below Rust's 6/6.

### Diagnosed concentration

Five Parley runs passed first check and clustered between 45,680 and 46,726
tokens. The remaining bracket run wrote `returns yesno`, `return valid`, then
`give valid`; generic P101 hints led to three repair turns before the agent
inlined the helper. Canonical `giving yesno` / `give back valid` had been
removed from the compact core during earlier compression.

### Next experiment

Add the canonical returning-function form while removing at least the same
number of lower-value core bytes. Add exact parse hints for `returns`,
`return value`, and `give value`, then rerun the unchanged protocol-v2 pilot.

## Engineering changes after 007

### 2026-07-29 — Parley 0.3.144 returning-function guardrail

- Added canonical `giving TYPE` and `give back value` forms to the core and
  explicitly rejected common `returns`, `return value`, and `give value`
  substitutions.
- Added exact P101 repair hints for each of those three observed parse forms.
- Removed lower-value reference prose so the core is 3,280 characters, three
  bytes smaller than 0.3.143; protocol-v2 task prompts remain
  4,884–4,928 characters.
- Added three parser regression cases reproducing the iteration-007 repair
  sequence. Iteration 008 keeps protocol v2, tasks, model, reasoning, seed,
  public cases, and hidden oracle unchanged.

## 008 — Clean-context gap pilot

- Date: 2026-07-29
- Compiler: Parley 0.3.144, commit `504d93d38ff07a532ff79ac765fddf899de3cd6d`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `7dcd3e6e42fc8c5097f6d901741eb47f0da61c5d6fc4e91c42707f40903903db`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `f2683bdc7e78e98b55f101d38f42ee32646d423e7e51ac4370f952e1c0430284`
- Report: `benchmarks/reports/008-clean-context-gap.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 6/6 | 6/6 | 46,040.5 | 20.6735 | 0 |
| Python | 6/6 | 4/6 | 6/6 | 43,081.5 | 17.8991 | 2 |
| Rust | 6/6 | 6/6 | 6/6 | 43,476.5 | 19.3878 | 0 |

### Gate result

Parley satisfied hidden correctness, first-pass reliability, and protocol
compliance, but strict efficiency still **failed**. Its median tokens were
6.9% above Python and 5.9% above Rust; median elapsed time was 15.5% above
Python and 6.6% above Rust.

### Isolated residual

All six Parley runs passed first check and clustered from 45,602 to 46,377
tokens. Median input was 2,864.5 tokens above Python while median output was
only 94.5 higher. Per-task gaps to the lower baseline were also consistent:
3,115 on inventory, 2,943.5 on compact ranges, and 2,833.5 on bracket report.
With repair and command variance removed, always-loaded language context is
the remaining measured gap.

### Next experiment

Preserve the 3,280-character core as a fallback. Build a much smaller
always-injected contract that retains every empirically observed trap and
routes detailed syntax to the existing on-demand reference. Run a new
protocol-v2 pilot; do not proceed to confirmation unless it preserves the
iteration-008 reliability result and clears both efficiency medians.

## Engineering changes after 008

### 2026-07-29 — Parley 0.3.145 progressive-disclosure core

- Preserved the proven 3,280-character v0.3.144 skill byte-for-byte at
  `skill/parley/references/core-v0.3.144.md` (SHA-256
  `f2683bdc7e78e98b55f101d38f42ee32646d423e7e51ac4370f952e1c0430284`).
- Replaced the always-loaded contract with a 1,557-character core that keeps
  every first-pass trap isolated by iterations 003–008: reserved names,
  snake-case identifiers, booleans, exact comparisons, numeric conversion,
  collection mutation and lookup, literal braces, expression calls,
  declaration-only `changing`, returning functions, loop-only control, block
  scope, and temporary bindings for complex conditions.
- Reduced the median rendered Parley task prompt from 4,913 to 3,190
  characters (35.1%) while retaining the on-demand exhaustive reference.
- Added a regression test pinning the fallback's byte length and SHA-256 so a
  future compression pass cannot silently destroy the last proven core.

## 009 — Progressive-disclosure regression

- Date: 2026-07-29
- Compiler: Parley 0.3.145, commit `075fdb94a12468e4fd7537f9f1c3fbfd1454d440`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `a44f50f6fd88f18e43858d1a4eca5448031a39be95bf9beaefd62cf6c71f96ee`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `d8ca4eaf0889c200b4b14427756c884cc648702a58331cfb1fe17b5d7b2634b1`
- Report: `benchmarks/reports/009-progressive-disclosure-regression.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 0/6 | 6/6 | 162,504.0 | 69.6042 | 19 |
| Python | 6/6 | 5/6 | 6/6 | 43,086.5 | 15.4107 | 1 |
| Rust | 6/6 | 6/6 | 6/6 | 43,408.0 | 23.0070 | 0 |

### Gate result

Final correctness and command compliance remained perfect, but first-pass
reliability and strict efficiency both **failed**. Parley's median tokens were
277.2% above Python and 274.4% above Rust; median elapsed time was 351.7%
above Python and 202.5% above Rust. Do not run the 90-session confirmation for
this candidate.

### Diagnosed regression

The shorter prompt itself was not enough: its 3,190-character rendered median
was 35.1% below iteration 008, yet all six Parley sessions needed 3–5 checks.
Five initial solutions used `set x to` to introduce variables, four used
`has no value`, and the set also tried `print`, `return`, bare `give back`,
empty-text splitting, unsupported collection iteration, and `sort`. The tiny
core retained isolated traps but removed the concrete safe-form backbone and
the explicit rule that `let` creates while `set` mutates.

### Next experiment

Keep the v0.3.144 fallback immutable. Restore a compact executable safe-form
example and the missing foundational forms—`let`, `set`, `is nothing`, `say`,
1-based indexing/text traversal, and branching to leave `main`—while staying
materially below 3,280 core characters. Add direct parser diagnostics for the
predictable natural aliases, then run protocol-v2 pilot 010.

## Engineering changes after 009

### 2026-07-29 — Parley 0.3.146 transcript-backed natural aliases

- Preserved the failed 1,557-character v0.3.145 core byte-for-byte at
  `skill/parley/references/core-v0.3.145.md` (SHA-256
  `d8ca4eaf0889c200b4b14427756c884cc648702a58331cfb1fe17b5d7b2634b1`).
- Added compiler support for the exact natural drafts repeated in iteration
  009: `set name to value` can introduce a missing variable; `print` aliases
  `say`; `return` aliases `give back`; `has no value` / `has [a] value` alias
  maybe comparisons; `sort xs` mutates to a sorted copy; repeat counts accept
  direct addition/subtraction; splitting by empty text yields Unicode
  characters; and loop-free `stop` leaves `main`.
- Rechecked all six recorded iteration-009 first sources against the new
  compiler. Four now type-check unchanged; both remaining bracket sources are
  rejected only for safely using a `maybe number` as a repeat count.
- Replaced the abstract micro-core with a 1,371-character contract containing
  one executable safe-form example, including the required maybe-number
  check and unwrap. Rendered task prompts are 2,975–3,019 characters, versus
  4,884–4,928 for the proven v0.3.144 core.

## 010 — Natural-alias partial recovery

- Date: 2026-07-29
- Compiler: Parley 0.3.146, commit `4ace8070c653af34fdcdadcb2d2adac452b48dbd`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `499e9de14c2c96de2af049c7dd574d879eec947ddaff42b59446ecd6d106fc8b`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `c49d14eb2702981a9c1641f79a38239b59916e671392193bcff47424d3511e1f`
- Report: `benchmarks/reports/010-natural-alias-partial-recovery.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 2/6 | 6/6 | 78,314.0 | 44.3483 | 9 |
| Python | 6/6 | 5/6 | 6/6 | 43,009.5 | 17.4465 | 1 |
| Rust | 6/6 | 6/6 | 6/6 | 43,394.5 | 18.6566 | 0 |

### Gate result

Correctness and protocol compliance remained perfect. First-pass reliability
improved from 0/6 to 2/6, and repair turns fell from 19 to 9, but reliability
and strict efficiency still **failed**. Parley's median tokens were 82.1%
above Python and 80.5% above Rust; median elapsed time was 154.2% above Python
and 137.7% above Rust.

### Isolated remaining failures

Both bracket sessions passed first check at a 44,920-token task median, close
to Rust's 43,535.5. Both inventory sessions independently wrote
`item 2 of parts as number` and joined text to numbers with `plus`; resolving
those two missing natural forms dominated their 3–4 repair turns. Compact
ranges needed one repair in each run: one emitted fragments with newline
printing, and one read numeric inputs as text before trying `value of`.

### Next experiment

Add checked `expr as number` conversion and scalar-aware text joining, then
state explicitly that `say` emits one complete line and numeric input uses
`ask for a number`. Preserve the current core, keep the task/protocol frozen,
and run pilot 011 before any confirmation.

## Engineering changes after 010

### 2026-07-29 — Parley 0.3.147 conversion/output recovery

- Preserved the 1,371-character v0.3.146 partial-recovery core byte-for-byte
  at `skill/parley/references/core-v0.3.146.md` (SHA-256
  `c49d14eb2702981a9c1641f79a38239b59916e671392193bcff47424d3511e1f`).
- Added postfix `text_expr as number` as a checked composition of
  `number from` and `value of`; invalid numeric text still stops safely.
- Made text `plus` non-text values format with the same rules as string
  interpolation, accepting both independently repeated inventory drafts.
- Added two concise core sentences: numeric input uses `ask for a number`,
  and `say` emits one complete line, so fragments should be assembled before
  output. The resulting core is 1,519 characters.
- Rechecked all six pilot-010 first sources. Five now type-check unchanged;
  only the compact-range source that treated plain text as a maybe remains
  rejected, exactly where the new core gives the corrective form.

## 011 — Conversion/output gap

- Date: 2026-07-29
- Compiler: Parley 0.3.147, commit `d1ffece41d46784365d6c2c23480a7c93cb1407e`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `c1b82867234f2aaadaf3b382b9b0ff8eeea98d3dec3114632f77f84861311435`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Report: `benchmarks/reports/011-conversion-output-gap.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 2/6 | 6/6 | 74,819.0 | 24.8918 | 5 |
| Python | 6/6 | 4/6 | 6/6 | 43,048.0 | 19.4613 | 2 |
| Rust | 6/6 | 6/6 | 6/6 | 43,395.5 | 19.3580 | 0 |

### Gate result

Correctness and protocol compliance remained perfect. Parley stayed at 2/6
first-pass, but repairs fell from nine to five and median elapsed time nearly
halved. Strict efficiency still **failed**: median tokens were 73.8% above
Python and 72.4% above Rust; elapsed time was 27.9% above Python and 28.6%
above the slightly faster Rust median.

### Isolated remaining failures

Both compact-range sessions independently wrote `number as text`; both
inventory sessions independently added a numeric total directly to a
`list of text`. Bracket reporting remained 2/2 first-pass. The repeated
pairing supports two narrow language affordances: postfix `as text`, and
destination-aware formatting when a scalar is added to a text list.

### Next experiment

Add those two mechanical forms without increasing the compact skill, confirm
all six pilot-011 first sources type-check unchanged, then run pilot 012.

## Engineering changes after 011

### 2026-07-29 — Parley 0.3.148 symmetric text output

- Preserved the 1,519-character v0.3.147 core byte-for-byte at
  `skill/parley/references/core-v0.3.147.md` (SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`).
- Added postfix `expr as text` as an exact alias for `text from expr`.
- Made `add value to text_list` format non-text values using the same rules as
  interpolation and text `plus`, while retaining type errors for unit and
  function values.
- Left the always-loaded skill unchanged at 1,519 characters, isolating this
  experiment to compiler ergonomics.
- All six pilot-011 first sources now parse and type-check unchanged.

## 012 — Near parity, single outlier

- Date: 2026-07-29
- Compiler: Parley 0.3.148, commit `ba725eb6d5f767875c344df75f09e30575e5c1ce`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `b1f978100df5b6693b6db1df61275becb3500760d52d1f9979620ef8805b50f4`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Report: `benchmarks/reports/012-near-parity-single-outlier.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 5/6 | 6/6 | 45,060.0 | 21.9441 | 2 |
| Python | 6/6 | 5/6 | 6/6 | 43,008.5 | 17.6208 | 1 |
| Rust | 6/6 | 5/6 | 6/6 | 43,395.5 | 20.1728 | 2 |

### Gate result

Correctness and protocol compliance remained perfect. Parley improved from
2/6 to 5/6 first public checks, tying both baselines, while median tokens fell
39.8% and elapsed time fell 11.8% from iteration 011. Strict efficiency still
**failed**: median tokens were 4.77% above Python and 3.84% above Rust;
elapsed time was 24.54% above Python and 8.78% above Rust.

### Isolated remaining failure

Five Parley sessions passed first check in a tight 44,288–45,335-token band.
The sole outlier defined a helper with natural `and`-separated parameters and
calls, then mutated a list parameter without the explicit `changing` marker.
The first repair changed separators to commas; the second inlined the helper
after value semantics produced blank output. That run consumed 109,005 tokens.

### Next experiment

Accept natural `and` separators for parameter lists and multi-argument calls,
and infer reference passing for a parameter demonstrably mutated by its
function body. Preserve the compact skill, recheck the saved source unchanged,
and run pilot 013. After first-pass reliability is complete, reduce the fixed
Parley prompt overhead that remains visible in the clean-run cluster.

## Engineering changes after 012

### 2026-07-29 — Parley 0.3.149 natural helper actions

- Added `and` as a parameter separator and arity-directed call-argument
  separator; one-argument boolean expressions retain their existing meaning.
- For an `and`-separated signature only, directly mutating a list/map
  parameter infers `changing`. Comma-separated signatures preserve the
  existing value-semantics contract.
- Rechecked the exact pilot-012 first source: zero diagnostics, with only its
  `parts` parameter inferred changing and both three-argument calls recovered.
- Kept the 1,519-character always-loaded skill byte-for-byte unchanged to
  isolate compiler ergonomics.
- Verification: 284 tests passed, including native output and the prior
  non-changing heap-parameter clone regression.

## 013 — Reliability restored, fixed-context gap

- Date: 2026-07-29
- Compiler: Parley 0.3.149, commit `dab87c7f29d582a3e8bed92a50d7ba19b9119c5d`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `340921143168951af65e743ca994cb4071e90058dfb4ab20a621f90847c39597`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Report: `benchmarks/reports/013-reliability-restored-context-gap.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 6/6 | 6/6 | 45,018.5 | 22.5310 | 0 |
| Python | 6/6 | 5/6 | 6/6 | 43,061.0 | 17.6641 | 1 |
| Rust | 6/6 | 6/6 | 6/6 | 43,437.0 | 20.4717 | 0 |

### Gate result

Correctness and protocol compliance remained perfect. Parley reached 6/6
first-public-check success with zero repairs, exceeding Python and tying Rust.
The strict efficiency gate still **failed**: median tokens were 4.55% above
Python and 3.64% above Rust; elapsed time was 27.55% above Python and 10.06%
above Rust.

### Isolated remaining gap

All six Parley sessions passed immediately in a narrow 44,483–45,503-token
band. The 3,152-character Parley prompt remained 1,683 characters larger than
Python and 1,672 larger than Rust. Median Parley input exceeded Python by
1,770 tokens while output exceeded it by 187.5, consistent with fixed context
being replayed across a clean multi-turn tool interaction.

### Next experiment

Preserve the proven 1,519-character core, then reduce the always-loaded skill
to the smallest executable contract that retains the exact six clean source
families. Keep compiler 0.3.149 and protocol v2 frozen; run pilot 014 before
starting the 90-session confirmation.

## Engineering changes after 013

### 2026-07-29 — Parley 0.3.150 one-shot general instruction compression

- Preserved the 1,519-character reliability core byte-for-byte at
  `skill/parley/references/core-v0.3.149.md` (SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`).
- Replaced it with a 343-character general quickstart covering only entry
  point, indentation, state, output, text input, safe numeric input, and the
  compiler-diagnostic repair loop. It contains no benchmark-task hints.
- Removed redundant Parley-only explanatory wrapper prose from the runner;
  workspace restrictions, exact-command protocol, tasks, and check loop are
  unchanged.
- Froze compiler semantics at the 0.3.149 behavior; 0.3.150 is an
  instruction-only release. This is the sole compression experiment before a
  broader corpus or the predeclared 90-session confirmation.

## 014 — One-shot instruction compression rejected

- Date: 2026-07-29
- Toolchain: Parley 0.3.150, commit `a573dca29296cd7e75b013450c855e6f2ea6ca42`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 2 replicates = 18 fresh sessions
- Result JSON SHA-256: `3517b51ec7288317a61624d4074b436bb2647f358d543448147045a407234939`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `3ea14e8165ec10dbe6f087bf02fc5641df50439fd0894c3523d76755f9d8d3ea`
- Report: `benchmarks/reports/014-overcompression-rejected.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 6/6 | 0/6 | 6/6 | 446,534.5 | 161.0150 | 69 |
| Python | 6/6 | 5/6 | 6/6 | 43,065.5 | 18.4376 | 1 |
| Rust | 6/6 | 6/6 | 6/6 | 43,329.0 | 18.7325 | 0 |

### Gate result

The compression hypothesis decisively **failed**. All Parley sessions
eventually passed hidden cases and obeyed protocol, but none passed its first
public check. Median checks rose to 12.5, median tokens to 10.37× Python, and
median elapsed time to 8.73× Python.

### Cross-task evidence

The failure replicated across every task: bracket sessions used 8 and 20
checks; compact ranges used 4 and 3; inventory totals used 23 and 17. This is
not an isolated syntax miss. Removing the executable contract transferred a
large language-discovery burden into repeated compiler repair loops.

### Decision

Reject the 343-character core and restore the proven 1,519-character 0.3.149
core. Do not run another compression experiment. Freeze instructions and
compiler semantics, then proceed to a broader corpus or the predeclared
90-session confirmation. Future changes require general usefulness, semantic
consistency, and maintainability—not improvement on one transcript.

## Engineering changes after 014

### 2026-07-29 — Parley 0.3.151 proven-core rollback

- Restored `skill/parley/SKILL.md` byte-for-byte from the preserved 0.3.149
  core (1,519 characters; SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`).
- Restored the original metered Parley wrapper in `agent_runner.py` so future
  confirmation results remain comparable to pilot 013.
- Made no compiler or language change. No further instruction-compression
  experiment is permitted in this optimization cycle.
- Next evidence is distributional: a broader task corpus or the predeclared
  10-replicate-per-cell confirmation, not another three-task tuning pass.

### 2026-08-04 — Parley 0.3.152 contextual `position`

- Iteration 017 found the ordinary name `position` rejected in five
  first-check events spanning four unrelated tasks. This met the predeclared
  cross-task rule and independently exposed a vocabulary-design problem: a
  common domain name was globally reserved only because Parley also has the
  `position of needle in text` operator.
- `position` is now a contextual identifier. `item position of values` reads
  the variable as its index, while `position of "x" in text` retains its
  search meaning. If a search expression itself is an item index, explicit
  parentheses resolve the inherent phrase boundary.
- The implementation factors item-index parsing into one documented grammar
  rule shared by reads, sets, and removals. It removes the obsolete reserved
  name and diagnostic special case; it does not add a new operator or weaken
  checker semantics.
- All five untouched 017 first-attempt sources that failed on `position` now
  pass their original public and hidden cases. The full suite passes 294/294,
  including parser, checker, Rust emission, and native execution coverage.
- The 1,519-character skill remains byte-for-byte unchanged. Unsupported
  `modulo` remains unchanged because its evidence is still confined to one
  task. Iteration 018 must be frozen separately before measuring 0.3.152.

### 2026-08-05 — Parley 0.3.153 contextual `modulo`

- Iteration 019's anti-primed first sources independently used infix `modulo`
  across clock, parity, and weekday task families, satisfying the cross-task
  evidence rule. The alias is also independently useful as standard arithmetic
  vocabulary.
- `_MOD` now accepts the word `modulo` contextually alongside `%`. Both feed
  the existing `%` binary AST, whole-number checker, guarded `parley_rem`
  emitter path, and Rust remainder runtime semantics. No new AST node,
  checker branch, runtime function, or mathematical-modulo behavior was added.
- `modulo` remains available as an ordinary identifier where an operator is
  not grammatically expected. Decimal operands still receive P302; a zero
  divisor still raises the existing English runtime failure. Docs and tests
  explicitly define the result's sign for negative operands (`-5 modulo 3`
  is `-2`) and standard multiplicative precedence.
- All five untouched iteration-018 rotation first sources that began with
  unsupported `modulo` now pass their original public and hidden cases. The
  broader 019 replay intentionally still rejects unrelated reserved-name,
  malformed-phrase, and decimal-division issues rather than weakening them.
- The full suite passes 301/301 across parser, checker, emitter, diagnostics,
  benchmark protocols, and native execution. The 1,519-character skill remains
  byte-for-byte unchanged pending broad confirmation.

## Pre-registration for 020 — Ten-replicate size-eight confirmation

- Date frozen: 2026-08-06
- Compiler: Parley 0.3.153, commit
  `736a474c9752050bb82942565ac5bd09cd3662e4`
- Instruction core: proven 1,519-character core, byte-for-byte unchanged
- Task population: the eight broad-corpus tasks from iterations 016–018
- Workload size: all eight programs in every fresh session
- Matrix: 10 complete bundles × 3 languages = 30 fresh sessions and 240
  hidden-judged task-solutions
- Seed: `20260806`
- Protocol: `benchmarks/bundle_protocol_020.json`

### Why this confirmation is concentrated

Iterations 017 and 018 already measured the complete size 1/2/4/8 curve. The
unresolved claim is specifically size-eight parity, previously represented by
only two sessions per language. Iteration 020 spends the same 30-session
per-language budget on ten complete size-eight replicates, strengthening the
primary comparison while avoiding 60 more small-scale sessions that cannot
answer the blocking question.

### Frozen gate and decision rule

Parley must preserve 100% hidden-task correctness and match or beat the better
Python/Rust baseline on median reported tokens/task, median elapsed
seconds/task, and first-check task success. All four conditions are required.
Report repair-free sensitivity and every failure signature. Do not respond to
a residual token gap with syntax: any later proposal again needs recurrence
across unrelated tasks plus independent general usefulness, semantic
consistency, and maintainability. No instruction compression is permitted.

## 015 — 90-session confirmation: strict parity not met

- Date: 2026-07-29
- Toolchain: Parley 0.3.151, commit `db39bda61dca9619dce72293ea2ba6ded5c81c2c`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 3 tasks × 3 languages × 10 replicates = 90 fresh sessions
- Result JSON SHA-256: `8fbe1639ba293915467b5ec142f8561f4d498f00fe76a20d9f2c0eef01a3ac24`
- Task manifest SHA-256: `63820d71c388bdbb22aea49f47b7a9c2113c9fd37fd9209b3ecdc7f2dd0ca20e`
- Parley skill SHA-256: `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Report: `benchmarks/reports/015-confirmation-strict-parity-not-met.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 30/30 | 25/30 | 30/30 | 44,809.0 | 20.1131 | 6 |
| Python | 30/30 | 23/30 | 30/30 | 43,031.0 | 17.4409 | 7 |
| Rust | 30/30 | 29/30 | 30/30 | 43,366.5 | 20.1867 | 1 |

### Gate result

Hidden correctness and command-protocol compliance were perfect for all 90
sessions. Parley exceeded Python on first-pass reliability and used fewer
repairs, while nearly tying Rust on elapsed time. The predeclared strict gate
nevertheless **failed**: Parley median tokens were 4.13% above Python and
3.33% above Rust; elapsed time was 15.32% above Python (though 0.36% below
Rust); first-pass reliability was below Rust's 96.67%.

### Task-level result

- Bracket report: Parley 44,991.5 tokens and 7/10 first-pass; Python 72,550
  and 3/10; Rust 43,675 and 9/10.
- Compact ranges: Parley 44,969.5 and 9/10; Python 43,033.5 and 10/10; Rust
  43,622.5 and 10/10.
- Inventory totals: Parley 44,668.5 and 9/10; Python 42,800 and 10/10; Rust
  43,111 and 10/10.

### Decision

Do not optimize against individual confirmation transcripts. Freeze the
current compiler and instruction core. The next useful evidence is a broader,
predeclared task corpus spanning additional algorithms and programming
constructs. Any future language change must be justified independently by
generality, semantic consistency, and maintainability.

## Pre-registration for 016 — Broad out-of-sample corpus

- Date frozen: 2026-07-30
- Compiler: Parley 0.3.151, semantics unchanged from iteration 015
- Instruction core: restored 1,519-character reliability core, unchanged
- Matrix: 8 new tasks × 3 languages × 2 replicates = 48 fresh sessions
- Seed: `20260730`
- Manifest: `benchmarks/agent_tasks_broad.json`
- Domains: text processing, numeric streams, stateful aggregation, and
  sequence transformation, with two tasks in each domain
- Primary outcomes: hidden success, first-public-check success,
  command-protocol compliance, median total tokens, and median elapsed time

### Analysis and change rule

Report the complete corpus and every task-language cell, including failures
and outliers. This experiment is out-of-sample diagnostic evidence, not a new
tuning loop or a publishable language ranking. Do not change the compiler or
language because of one task or transcript. A future proposal must address an
issue recurring across at least two unrelated tasks and independently satisfy
general usefulness, semantic consistency, and maintainability.

## 016 — Broad corpus: correctness holds, parity not met

- Date: 2026-07-30
- Toolchain: Parley 0.3.151, commit `632eb46dace340b9f65f7e34935224b5dbf2e062`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.142.5
- Matrix: 8 tasks × 3 languages × 2 replicates = 48 fresh sessions
- Result JSON SHA-256: `8529aff77c008edda63295f5d6d5f79e68e9a93e7e80be72eac4ce9fa69bdaa5`
- Task manifest SHA-256: `cc8a0795b62c58c04056d097b4ff1af698dc8a9cc57865ab3fd874af618c50c3`
- Parley skill SHA-256: `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Report: `benchmarks/reports/016-broad-corpus-diagnostic.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Repair turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 16/16 | 13/16 | 16/16 | 43,455.0 | 20.0663 | 8 |
| Python | 16/16 | 15/16 | 16/16 | 41,832.5 | 16.5347 | 1 |
| Rust | 16/16 | 16/16 | 16/16 | 42,020.5 | 17.1042 | 0 |

### Result

All 48 fresh sessions passed every hidden case, preserved checker integrity,
and complied with protocol v2. Strict efficiency parity was **not met**:
Parley median tokens were 3.88% above Python and 3.41% above Rust; median
elapsed time was 21.36% above Python and 17.32% above Rust. Parley first-pass
reliability was also below both baselines.

### Cross-task evidence

Six task medians placed Parley 3.0–4.24% above the best baseline with both
Parley replicates passing their first public checks. Stable word
deduplication had one repaired Parley run and a 38.49% token gap. Rotate words
left had two repaired Parley runs, seven repair turns, and a 266.87% gap.
Excluding rotation leaves Parley at 43,436 median tokens versus Python at
41,843, a similar 3.81% gap; the aggregate median result is therefore not an
artifact of the large rotation outlier.

### Decision

Make no compiler or syntax change from this experiment alone. Rotation
repeated within one task but did not recur across unrelated tasks. The broad
small token gap is consistent with fixed instruction/context overhead and
does not identify a semantically justified language feature. Keep compiler
and skill frozen. Any future proposal requires evidence across at least two
unrelated tasks plus an independent case for general usefulness, semantic
consistency, and maintainability.

## Pre-registration for 017 — Workload-scale cold-start amortization

- Date frozen: 2026-08-04
- Compiler: Parley 0.3.151, semantics unchanged from iterations 015–016
- Instruction core: proven 1,519-character core, byte-for-byte unchanged
- Task population: the eight predeclared broad-corpus tasks from iteration 016
- Bundle sizes: 1, 2, 4, and 8 tasks per fresh session
- Matrix: 90 fresh sessions; 192 independently hidden-judged task-solutions
- Replicates: 2 complete task partitions per bundle size and language
- Seed: `20260804`
- Protocol: `benchmarks/bundle_protocol_017.json`

### Primary gate

At bundle size eight, Parley must preserve 100% hidden-task correctness and
match or beat the better Python/Rust baseline on median reported tokens per
assigned task, median elapsed seconds per assigned task, and first-check task
success. All four conditions are required for strict workload parity.

### Interpretation and change rule

This experiment tests whether the fixed cold-start instruction cost amortizes
on a realistic multi-program workload. Report session totals beside every
amortized value. Do not compress the instruction core again. Do not change
syntax or compiler semantics from one workload, task, or transcript; require
the same issue across at least two unrelated tasks plus an independent case
for general usefulness, semantic consistency, and maintainability.

## 017 — Workload scale: amortization works, strict parity fails

- Date: 2026-08-04
- Toolchain: Parley 0.3.151, preregistration commit
  `2d0a4360f32126324e14155b5f641d7ec5c5fbc5`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.146.0
- Matrix: bundle sizes 1, 2, 4, and 8; 90 fresh sessions; 192 independently
  judged task-solutions
- Result JSON SHA-256: `309022cb61a1cc208586c42ecf411227a537781a1ee3f6896b94815b5db2804d`
- Frozen protocol SHA-256: `d7768b0d7aef0f0f04606429fbe3a322f9f321dace4048eba4a4cf342622fca1`
- Parley skill SHA-256: `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Report: `benchmarks/reports/017-workload-scale-parity-failed.html`

| Bundle size | Language | Hidden tasks | First-check tasks | Median tokens/task | Median seconds/task | Repair turns |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Parley | 16/16 | 13/16 | 40,793.50 | 19.8440 | 7 |
| 1 | Python | 16/16 | 16/16 | 39,278.00 | 17.5571 | 0 |
| 1 | Rust | 16/16 | 16/16 | 39,546.50 | 19.9184 | 0 |
| 2 | Parley | 16/16 | 15/16 | 21,065.75 | 12.9838 | 1 |
| 2 | Python | 16/16 | 16/16 | 20,120.25 | 10.7401 | 0 |
| 2 | Rust | 16/16 | 16/16 | 20,374.25 | 12.6012 | 0 |
| 4 | Parley | 16/16 | 15/16 | 11,076.13 | 9.1367 | 2 |
| 4 | Python | 16/16 | 16/16 | 10,555.00 | 6.5878 | 0 |
| 4 | Rust | 16/16 | 16/16 | 10,783.88 | 9.2004 | 0 |
| 8 | Parley | 16/16 | 11/16 | 19,273.88 | 13.4129 | 6 |
| 8 | Python | 16/16 | 16/16 | 5,716.75 | 4.6577 | 0 |
| 8 | Rust | 16/16 | 16/16 | 5,965.38 | 6.8335 | 0 |

### Gate result

All 192 task-solutions passed hidden cases, and all 90 sessions preserved
checker integrity and protocol compliance. The size-eight strict gate
nevertheless **failed three of four conditions**: correctness passed, while
Parley missed tokens/task, seconds/task, and first-check task success. Its
19,273.88 median tokens/task were 3.37× Python's 5,716.75.

### Mechanism and cross-task audit

The intended fixed-cost amortization did occur: Parley's prompt-character gap
to Python fell from 1,681 per task at size one to 211.88 at size eight, and
clean-session token use fell through size four. Repairs then dominated the
size-eight result; neither Parley session was repair-free.

Every language passed every hidden task. Parley's ten first-check task
failures were compile-time P101 diagnostics. Five failure events used
`position` as an ordinary variable across four unrelated tasks; five used the
unsupported word `modulo`, all in word rotation alone. Rotation finished 2/8
on its first check, while the next weakest task finished 6/8.

### Decision

The recurring `position` collision satisfies the predeclared cross-task rule
and has an independent language-design case: position is a common identifier,
and allowing it contextually can preserve the existing `position of ... in
...` operator without adding a new concept. Implement and test that one
general compiler change. Do not add `modulo` from this evidence: it remains
confined to one task. Keep the 1,519-character instruction core frozen, then
rerun the same workload under a separately preserved iteration 018 protocol.

## Pre-registration for 018 — Contextual-identifier replication

- Date frozen: 2026-08-04
- Compiler: Parley 0.3.152, commit
  `b94964ab64d85e099bf65f23280331cd3398af01`
- Instruction core: proven 1,519-character core, byte-for-byte unchanged
- Protocol: `benchmarks/bundle_protocol_018.json`
- Matrix: exact iteration-017 replication—bundle sizes 1, 2, 4, and 8;
  90 fresh sessions; 192 hidden-judged task-solutions; seed `20260804`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.146.0

### Frozen difference and gate

The only compiler difference from iteration 017 is the generally useful,
cross-task-supported contextual interpretation of the existing word
`position`. Unsupported `modulo` is intentionally unchanged. The task
population, deterministic partitions, prompts, skill, runner behavior,
replicate count, three languages, and four-part size-eight strict parity gate
are unchanged. All four conditions—hidden correctness, tokens/task,
seconds/task, and first-check task success—must pass.

### Analysis rule

Preserve all results, including stochastic baseline movement and failures.
Compare the complete scale curve with iteration 017, but do not attribute
Python/Rust movement to the Parley compiler. Make no further compiler change
unless the new evidence again crosses unrelated tasks and independently meets
general usefulness, semantic consistency, and maintainability.

## 018 — Contextual identifier works; strict parity still fails

- Date: 2026-08-04
- Toolchain: Parley 0.3.152, preregistration commit
  `7b1c441e13c754af7dee68678bcbb8dc8bce2f63`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.146.0
- Matrix: exact 017 replication—90 fresh sessions; 192 hidden-judged tasks
- Result JSON SHA-256: `67b2afcba283539c033efe630022bb994cf0e73a7e73aad4023d484059f709d8`
- Frozen protocol SHA-256: `bd79ecf56c2559b34bcaf9e78de7d0e999c9c932ef677863f3600c443711050d`
- Parley skill SHA-256: `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Report: `benchmarks/reports/018-contextual-identifier-replication-failed.html`

| Bundle size | Language | Hidden tasks | First-check tasks | Median tokens/task | Median seconds/task | Repair turns |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Parley | 16/16 | 15/16 | 41,394.50 | 18.8773 | 5 |
| 1 | Python | 16/16 | 15/16 | 39,911.00 | 16.9915 | 1 |
| 1 | Rust | 16/16 | 16/16 | 40,170.00 | 21.7918 | 0 |
| 2 | Parley | 16/16 | 15/16 | 21,361.75 | 12.3799 | 2 |
| 2 | Python | 16/16 | 16/16 | 20,455.75 | 10.5582 | 0 |
| 2 | Rust | 16/16 | 16/16 | 20,686.25 | 11.7004 | 0 |
| 4 | Parley | 16/16 | 15/16 | 11,245.75 | 8.5983 | 4 |
| 4 | Python | 16/16 | 16/16 | 10,664.38 | 7.1571 | 0 |
| 4 | Rust | 16/16 | 16/16 | 10,968.00 | 9.1520 | 0 |
| 8 | Parley | 16/16 | 13/16 | 14,853.31 | 10.9088 | 4 |
| 8 | Python | 16/16 | 16/16 | 5,817.56 | 5.0686 | 0 |
| 8 | Rust | 16/16 | 16/16 | 6,038.00 | 6.9591 | 0 |

### Gate and replication result

All 192 task-solutions passed hidden cases; all 90 sessions preserved checker
integrity and protocol compliance, with 90 unique threads, no timeouts, and no
agent failures. The size-eight strict gate again passed correctness only.
Parley improved from 19,273.88 to 14,853.31 median tokens/task (−22.94%) and
from 11/16 to 13/16 first-check tasks, but still used 2.55× Python's tokens
and 2.15× its elapsed time.

The exact `position` failure family fell from five events across four tasks to
zero; every previously affected task reached 8/8 first-check success. This
confirms the general compiler change solved the evidenced problem. All five
untouched 017 first sources also pass their original public and hidden cases
under 0.3.152.

### Remaining failure audit and decision

Five of six Parley first-check task failures were rotation programs using
unsupported `modulo`; the sixth was a one-off `does` phrasing failure in
stable deduplication. Rotation then accumulated further `mod`/invalid `div`
repair attempts, for fifteen failed public-check task events overall. Neither
initial signature affects two unrelated tasks, so make **no compiler change**
from 018.

The next justified experiment is a separately preregistered, independent
arithmetic-vocabulary corpus spanning unrelated parity, wraparound, clock,
checksum, and cyclic-index problems without suggesting an operator spelling.
Only cross-task recurrence plus an independent semantic/maintenance case can
justify an alias for the remainder operation. Keep the skill unchanged.

## Pre-registration for 019 — Independent arithmetic vocabulary

- Date frozen: 2026-08-05
- Compiler: Parley 0.3.152, semantics unchanged after iteration 018
- Instruction core: proven 1,519-character core, byte-for-byte unchanged
- Task manifest: `benchmarks/agent_tasks_arithmetic_vocabulary.json`
- Protocol: `benchmarks/vocabulary_protocol_019.json`
- Matrix: 6 unrelated tasks × 3 languages × 2 replicates = 36 fresh sessions
- Domains: number classification, time arithmetic, checksum arithmetic,
  cyclic indexing, calendar arithmetic, and stream divisibility
- Seed: `20260805`

### Anti-priming and primary evidence gate

No agent-visible task title, statement, example, prompt, or skill text names
or shows `modulo`, `remainder`, `percent`, or `%`. The primary unit is an
unrelated Parley task family whose source at the **first public check** uses
the standalone word `modulo`. At least two task families must independently
do so before an alias proposal is eligible.

Eligibility is not adoption. A compiler change would still require an
independent case for general usefulness, exact semantic consistency with the
existing integer remainder operation, one maintainable canonical meaning,
full pipeline coverage, and a subsequent broad-workload confirmation. Report
all 36 sessions, including every spelling, failure, repair, hidden judgment,
token count, and elapsed time.

## 019 — Arithmetic vocabulary gate passes across three families

- Date: 2026-08-05
- Toolchain: Parley 0.3.152, preregistration commit
  `18d513933e855057f46ee3ce8a283eab1f658352`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.146.0
- Matrix: 6 tasks × 3 languages × 2 replicates = 36 fresh sessions
- Result JSON SHA-256: `641a9af72b5d995662b1b6efe7ec5c595c4bfac4da6569a90f2d1873256aeafe`
- Task manifest SHA-256: `35edff11458c985c05c092d02560ffe1d4a1777c2f34012d1c85142dfd2eb348`
- Frozen protocol SHA-256: `49132da0f7c183844b9789be915b69d3a95433391a202e3247056f72278fb018`
- Report: `benchmarks/reports/019-arithmetic-vocabulary-gate-passed.html`

| Language | Hidden success | First public pass | Protocol compliant | Median tokens | Median seconds | Median checks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 11/12 | 5/12 | 12/12 | 84,553.5 | 33.2747 | 2.5 |
| Python | 12/12 | 12/12 | 12/12 | 39,285.0 | 14.4360 | 1.0 |
| Rust | 12/12 | 12/12 | 12/12 | 39,646.5 | 17.8915 | 1.0 |

### Primary evidence gate

The untouched first-check Parley source used standalone `modulo` in five
sessions across **three unrelated task families**: both clock sessions, both
parity sessions, and one weekday session. No agent-visible title, statement,
case, prompt, or skill text contained candidate arithmetic spellings. The
predeclared threshold was at least two task families, so the eligibility gate
**passes**.

The established `remainder of a divided by b` phrase appeared in three first
sources across divisibility and checksum tasks; two passed immediately, while
one failed only because it declared reserved variable `number`. One checksum
source used malformed `total remainder 10`. Three sources used subtraction or
loops instead of a direct operator.

### Correctness and burden

All 36 sessions preserved checker integrity and protocol compliance with 36
unique threads, no timeouts, and no agent failures. Parley accumulated 26
repair turns. Its one hidden failure was a first-check-clean weekday program
that subtracted seven exactly seven times; the 100-day hidden case produced 55
instead of 6. That bounded workaround is a real algorithmic failure and stays
in the result.

### Semantic and maintenance decision

One alias is now eligible and independently justified:

- **General usefulness:** anti-primed recurrence spans clocks, parity, and
  calendars, beyond rotation.
- **Semantic consistency:** Parley already has whole-number `%` and
  `remainder of a divided by b`, both emitted through the guarded
  `parley_rem` runtime helper. `a modulo b` must map to exactly that behavior.
- **Maintainability:** add one lexical spelling to the existing multiplicative
  operator; do not create a new AST node, checker path, or runtime operation.
- **Precision:** document and test that negative operands follow the existing
  Rust-style remainder rule (result has the dividend's sign), avoiding an
  undeclared Euclidean-modulo semantic change.

Implement v0.3.153 with parser/checker/emitter/native and zero-divisor,
precedence, and negative-number tests. Keep the instruction core unchanged for
the first confirmation. Replay the saved first sources, then freeze and rerun
the broad workload before claiming parity.

## Pre-registration for 020 — Size-eight confirmation

- Date frozen: 2026-08-05
- Compiler: Parley 0.3.153 at `736a474c9752050bb82942565ac5bd09cd3662e4`
- Instruction core: proven 1,519-character core, byte-for-byte unchanged
- Protocol: `benchmarks/bundle_protocol_020.json`
- Matrix: 10 size-eight replicates × 3 languages = 30 fresh sessions and
  240 hidden-judged task assignments
- Seed: `20260805`
- Preregistration commit: `ead3369`

The exact eight-task workload from iterations 017–018 is retained because it
was the predeclared confirmation target after the evidence-backed `modulo`
change. All four strict conditions must independently match the better
Python/Rust baseline: hidden correctness, median tokens per task, median
elapsed seconds per task, and first-check task success. The instruction,
prompts, task order, hidden cases, runner, and checker are frozen before any
session output.

## 020 — Size-eight confirmation fails all strict parity conditions

- Date: 2026-08-05
- Toolchain: Parley 0.3.153, preregistration commit `ead3369`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.146.0
- Matrix: 10 complete size-eight replicates per language; 30 fresh sessions;
  240 task assignments
- Result JSON SHA-256: `842b3408b9220a81e17ccc43a6523bfee20de2b3b8ca62baef3b58b6529d2cdf`
- Frozen protocol SHA-256: `31da622d09ba6dce88f0a6c8073bd2874ccdbf4451d86c42ac3df84e97f3d327`
- Parley skill SHA-256: `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Report: `benchmarks/reports/020-size-eight-confirmation-failed.html`

| Language | Hidden tasks | First-check tasks | Repair turns | Median tokens/task | Median seconds/task | Prompt chars/task |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 79/80 | 74/80 | 6 | 8,252.19 | 7.5476 | 867.5 |
| Python | 80/80 | 80/80 | 0 | 5,806.25 | 4.8133 | 655.625 |
| Rust | 80/80 | 80/80 | 0 | 6,047.25 | 6.8861 | 658.125 |

### Gate result and sensitivity

All 30 sessions used unique threads, complied with the protocol, and passed
checker-integrity validation, with no timeouts, runner errors, or nonzero
agent exits. The strict gate passed **0/4** conditions. Parley reached 98.75%
hidden correctness and 92.5% first-check correctness, but the baselines were
perfect. Its median token cost was 1.42× Python's and its median elapsed time
was 56.8% higher.

Five Parley sessions were repair-free. Their post-hoc median was 6,129.88
tokens/task and 6.5342 seconds/task, 5.57% above Python's token median and
1.37% above Rust's. They passed 40/40 first checks and 39/40 hidden tasks; the
hidden miss was a bounded rotation workaround. This clean subset diagnoses a
near-baseline regime but does not replace the frozen primary result.

### Failure audit and decision

The `modulo` alias eliminated the repeated rotation parse signature. The six
remaining first-check failures were: two `repeat while` sources across two
tasks, two `does not contain` sources in stable deduplication, one `contains
... is no` source in the same task, and one P901 Rust-backend failure after
the checker accepted mutation of a range-loop variable.

Do **not** add `repeat while`: it duplicates canonical `while` and would make
the surface less coherent for the sake of two transcripts. Do not add either
containment phrasing from one task family. Fix the mutable loop-variable P901
because checker totality is a language contract and the correction is broadly
useful regardless of tokens. Keep the instruction unchanged and perform no
second compression experiment. After that correctness fix, use a genuinely
new broad corpus or model split; do not continue tuning against these eight
tasks.

## Post-020 compiler correction — v0.3.154 mutable loop bindings

- Trigger: iteration-020 P901 after the checker accepted `set index to limit`
  inside `for each index from 1 to limit:`
- Design: no grammar, AST, checker, diagnostic, or runtime change
- Emission: range and collection loop bindings gain Rust `mut` exactly when
  existing recursive mutation analysis finds that their body changes the loop
  variable; unchanged bindings remain immutable
- Semantics: assignment changes only the current iteration value, never the
  source collection, frozen range bounds, or next iteration value
- Instruction: unchanged; no compression or syntax addition
- Verification: 305 tests passed in 94.42 seconds, including checker, emitter,
  and native range/list mutation regressions
- Exact replay: the untouched iteration-020 first source that previously
  raised P901 compiled and produced the expected output for the public case
  and all five hidden longest-common-prefix cases

This is a checker-totality repair, not evidence that the failed iteration-020
parity result changed. Do not rerun that same corpus as an optimization target.
The next measurement must use a newly frozen broad corpus or model split.

## Pre-registration for 021 — New twelve-task broad corpus

- Date frozen: 2026-08-05
- Compiler: Parley 0.3.154 at
  `574709bc0e3eeb78326937b67513c667b992d98b`
- Instruction core: proven 1,519-character core, byte-for-byte unchanged
- Task manifest: `benchmarks/agent_tasks_broad_021.json`
- Task manifest SHA-256:
  `45f6387fbe8fef2e3c59b59781b967b81302494b6f09533df81bead27f20f781`
- Protocol: `benchmarks/bundle_protocol_021.json`
- Matrix: 12 new tasks × 3 languages × 6 complete-bundle replicates = 18
  fresh sessions and 216 hidden-judged task assignments
- Seed: `20260807`

The corpus has zero task overlap with every earlier seed, pilot,
arithmetic-vocabulary, and broad workload. It spans sets/order, two distinct
stack problems, flat matrix indexing, two map workflows, search, ASCII text
transformation, polynomial evaluation, calendar rules, and numeric distance.
Each language receives the same task statements, public cases, withheld cases,
session structure, and six order permutations.

The unchanged four-condition gate requires Parley to match the better baseline
on hidden correctness, median tokens/task, median seconds/task, and first-check
success. Report and preserve every failure. No syntax may be added from one
transcript. Cross-task recurrence is only an eligibility signal; any change
must also be generally useful, semantically consistent, and maintainable. The
single instruction-compression experiment remains closed.

## 021 — New-corpus correctness ties; strict parity still fails

- Date: 2026-08-05
- Toolchain: Parley 0.3.154, preregistration commit `bbba5e1`
- Agent: `gpt-5.6-sol`, medium reasoning, Codex CLI 0.146.0
- Matrix: 12 new tasks × 3 languages × 6 complete-bundle replicates = 18
  fresh sessions and 216 task assignments
- Result JSON SHA-256: `07fe050ef2a9e5c963a1cb6df2d59c5cc582fc7c383143f2e5a337f2f5656c2e`
- Task manifest SHA-256: `45f6387fbe8fef2e3c59b59781b967b81302494b6f09533df81bead27f20f781`
- Frozen protocol SHA-256: `e21d1045235b8028d8dd140840af634fd541e6df4717b26bab2d82946d1b13f6`
- Parley skill SHA-256: `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Report: `benchmarks/reports/021-new-broad-corpus-parity-failed.html`

| Language | Hidden tasks | First-check tasks | Repair turns | Median tokens/task | Median seconds/task | Source tokens/task |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 72/72 | 51/72 | 8 | 8,367.13 | 8.3810 | 134.83 |
| Python | 72/72 | 72/72 | 0 | 4,057.08 | 4.0737 | 109.50 |
| Rust | 72/72 | 72/72 | 0 | 4,319.75 | 5.9032 | 211.79 |

### Gate and integrity result

The strict gate passed hidden correctness only: **1/4** conditions. All 216
final programs passed every hidden case. Parley used 2.06× Python's median
reported tokens/task and 2.06× its elapsed time, and no Parley bundle passed
all twelve tasks on the first check. Every Python and Rust bundle did.

All 18 sessions used unique threads and passed checker-integrity and command-
protocol validation. There were no timeouts, runner errors, nonzero agent
exits, or hidden failures. Every Parley session repaired; the six token rates
ranged from 7,490.92 to 12,180.92 per task, so no repair-free sensitivity
subset exists.

Parley's generated programs remained materially shorter than Rust: 134.83
versus 211.79 median rough source tokens/task (−36.34%). The agent-effort gap
therefore cannot be explained by Rust-sized Parley source. Parley's median
prompt was 737.83 characters/task versus Python's 595.92; the fixed skill is
unchanged and no compression experiment is permitted.

### Complete first-failure audit

All 21 failed first task checks were compile/check failures; repairs recovered
72/72 hidden correctness.

| Signature | Events | Unrelated task families | Decision |
| --- | ---: | ---: | --- |
| Ordinary identifier `number` rejected by P209 | 10 | 5 | Eligible; passes design review |
| Multiword function declaration | 3 | 3, all in one session | Reject; canonical snake_case and precise P101 |
| `repeat while` | 3 | 2 | Reject; duplicates canonical `while` |
| Postfix `numbers sorted` | 2 | 2 | Reject; duplicates `sorted numbers` and `sort numbers` |
| Undefined local before declaration | 2 | 1 | Reject; authoring errors |
| Unparenthesized call with natural `and` | 1 | 1 | Reject; isolated call-shape error |

`number` independently clears the language-design gate. It is an ordinary,
generally useful name across sorted uniqueness, matrix diagonal difference,
nearest-pair gap, sorted-list search, and sparse dot product. The parser already
accepted these identifier positions and the checker deliberately emitted P209.
Type positions remain unambiguous: `number` still means the built-in type
there, while identifier positions resolve to the local declaration. The
maintainable change is therefore to remove only `number` from the unconditional
reserved-name set, with uniform declaration/loop/parameter/function/call tests.

Preserve 021 unchanged. Implement contextual `number` as a separate compiler
version, keep the instruction unchanged, and replay all ten exact P209 sources.
Do not rerun this corpus as a tuning target; the next measurement must be a new
corpus or model split.

## Post-021 compiler change — v0.3.155 contextual `number`

- Evidence: 10 P209 events across five unrelated iteration-021 task families
- General scope: value-level field, function, parameter, variable, and loop
  binding names
- Semantic boundary: built-in `number` type syntax is unchanged; user-defined
  record, kind, and variant names `number` remain rejected because such a type
  could not be referenced unambiguously
- Implementation: the contextual lexer and grammar already distinguish the
  observed positions; the checker now permits `number` only for the five
  value-name categories
- Pipeline: parser, checker, Rust emitter, native execution, reference,
  tutorial, and specification coverage
- Verification: 309 tests passed in 97.13 seconds; strengthened emitter/native
  callable-name checks also passed
- Frozen-source replay: all 10 untouched P209 sources compiled and passed all
  50 combined public and hidden cases under v0.3.155
- Instruction: byte-for-byte unchanged, SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`

No `repeat while`, postfix `sorted`, insert phrase, multiword function syntax,
or other iteration-021 draft is accepted. The exact-source replay is a
regression check, not a revised benchmark result. The next efficiency evidence
must come from a newly frozen corpus or model split.

## Pre-registration for 022 — Independent-model split

- Date frozen: 2026-08-05
- Compiler: Parley 0.3.155 at
  `5b407e7f1f263db4cc73aa9a77de1c87c2b862e4`
- Model: `gpt-5.6-terra`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged
- Task manifest: frozen iteration-021 twelve-task corpus, SHA-256
  `45f6387fbe8fef2e3c59b59781b967b81302494b6f09533df81bead27f20f781`
- Protocol: `benchmarks/bundle_protocol_022.json`, SHA-256
  `8aea92b1001a28d1137a2af55af10c2e36ce4baa85e38fb14ba43da92c015edd`
- Matrix: 12 tasks × 3 languages × 6 complete-bundle replicates = 18 fresh
  sessions and 216 hidden-judged task assignments
- Seed: `20260808`

This is the model split explicitly allowed by iteration 021's stop rule. The
primary result compares Parley, Python, and Rust only within `gpt-5.6-terra`.
Iteration 021 used both a different model and Parley 0.3.154, so descriptive
movement across iterations cannot separately identify model or compiler
effects. Audit disappearance of the frozen contextual-`number` signature, but
do not make a counterfactual token claim.

The strict four-condition gate, skill, prompts, cases, runner, and protocol are
otherwise unchanged. Preserve every result. No post-output ergonomics change
may be learned from this reused corpus; future evidence must use new tasks.

## 022 — Independent-model correctness ties; strict parity still fails

- Completed: 2026-08-05
- Compiler: Parley 0.3.155
- Model: `gpt-5.6-terra`, medium reasoning
- Matrix: 12 tasks × 3 languages × 6 complete-bundle replicates = 18 fresh
  sessions and 216 hidden-judged task assignments
- Raw result:
  `benchmarks/results/agent_model_split_022_protocol_v1_v0.3.155.json`
- Raw SHA-256:
  `8594f5e8cceb31866002f25e7c3a6e49e00dc98124d70a519b37129d846e60ee`
- Report: `benchmarks/reports/022-independent-model-parity-failed.html`
- Report inputs:
  `benchmarks/reports/022-independent-model-parity-failed.artifact.json`,
  `.sql`, and `.chart-map.md`
- Integrity: 18 unique thread IDs; 18/18 fresh-session, checker-integrity,
  and command-protocol checks passed; no timeout, runner error, or nonzero
  agent exit

| Language | Hidden tasks | First-check tasks | Repairs | Median tokens/task | Median seconds/task |
| --- | ---: | ---: | ---: | ---: | ---: |
| Parley | 72/72 | 39/72 | 15 | 13,040.79 | 9.5024 |
| Python | 72/72 | 72/72 | 0 | 4,079.00 | 3.6720 |
| Rust | 72/72 | 64/72 | 6 | 7,265.04 | 6.2378 |

The strict gate failed 1/4. Correctness passed. Parley missed the token,
elapsed, and first-check conditions. Its median reported token effort was
3.20× Python and 1.80× Rust; elapsed time was 2.59× and 1.52× respectively.
No Parley session was repair-free, so the preregistered clean-session
sensitivity analysis is unavailable.

The 33 Parley first-task failures classify as follows:

| Signature | Events | Task families | Independent sessions |
| --- | ---: | ---: | ---: |
| Redundant literal `key` in map membership | 15 | 3 | 5 |
| Unwrapped numeric input | 7 | 7 | 1 |
| Bare `nothing` accumulator | 4 | 1 | 4 |
| `repeat while` phrasing | 3 | 3 | 1 |
| Unparenthesized prefix/value phrase | 2 | 2 | 1 |
| Decimal midpoint used as list position | 1 | 1 | 1 |
| Incorrect polynomial computation | 1 | 1 | 1 |

The map signature used sources such as `balances contains key name`; canonical
Parley already writes the same membership operation as `balances contains
name`. Although the redundant word recurred across three unrelated map tasks
and five sessions, this exact corpus was reused for the preregistered model
split. The frozen stop rule therefore forbids a post-output compiler change,
and duplicating an already complete operator merely to accept these transcripts
would fail the maintainability gate. `repeat while` is likewise redundant.
Unwrapped input is one session's habit; bare `nothing` is one task; the rest
are isolated. **No compiler, grammar, runtime, prompt, or skill change follows
from iteration 022.**

The contextual-`number` P209 signature is 0/33 after ten events in iteration
021. This is consistent with v0.3.155, and its ten frozen sources already pass
50/50 replay cases, but iteration 022 changes both model and compiler and
cannot attribute performance movement to either. Descriptively, the same model
also moved Rust from 72/72 first checks and 4,319.75 tokens/task in 021 to
64/72 and 7,265.04 here, while Python remained 72/72 and about 4.08k.

Preserve 022 unchanged. The next benchmark must use previously unseen,
application-style work that expands coverage beyond compact stdin/stdout
algorithms—modules, records, file operations, packaged helpers, and
multi-function programs—while keeping the proven instruction unchanged.
Any future compiler proposal still requires recurrence on new unrelated tasks,
general usefulness, semantic consistency, and maintainability.

## Pre-registration for 023 — New application-style broad corpus

- Date frozen: 2026-08-05
- Compiler: Parley 0.3.155 at
  `8f4a66885f3e0837f1595d72cf38ada5b8112f97`
- Model: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged, SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Task manifest: `benchmarks/agent_tasks_application_023.json`, SHA-256
  `f64d441628bd21ea8c6b5fbe3dda51f4d5c52f75607cdceed0616b76ad4d6dc4`
- Protocol: `benchmarks/bundle_protocol_023.json`, SHA-256
  `0a424ac66bbbc01e6f9020fc643462c3353ac4d69065a500613688ba96c423f8`
- Matrix: eight tasks × three languages × six complete-bundle replicates =
  18 fresh sessions and 144 hidden-judged task assignments
- Seed: `20260809`

The eight IDs and statements are unused in iterations 001-022. The workload
moves beyond small algorithm exercises into invoice aggregation, mutable ticket
workflows, configuration overlays, access-policy evaluation, scheduling,
shipment state transitions, contact merging, and a file-backed notes program.
Each task combines multiple entities or operations. The file task is materially
judged: before every case the harness deletes `file_backed_notes.txt`, then
requires exact UTF-8 contents in addition to exact stdout. Expected-file paths
are validated as safe relative paths.

All 40 public/hidden oracle cases and expected file contents were independently
recomputed before freezing. Four targeted harness tests passed. The first full
suite invocation omitted the repository from subprocess `PYTHONPATH`, producing
119 identical import-environment failures and 194 passes; the corrected command
`PYTHONPATH=/Users/arjun/Desktop/parley-lang python3 -m pytest -q` passed all
313 tests in 101.55 seconds. This operational failure and its correction are
retained here for history.

The primary gate is the same four-condition within-model comparison used by
the broad studies: hidden correctness, reported tokens per task, elapsed time
per task, and first-check task success. Cross-iteration movement is descriptive
only because the task population changed. Preserve all output. If parity
passes, require a larger preregistered confirmation. If it fails, do not tune
syntax on this corpus; only independently recurring defects may enter separate
general-usefulness, semantic-consistency, and maintainability review.

## 023 — Application correctness ties; strict parity still fails

- Completed: 2026-08-05
- Compiler: Parley 0.3.155
- Model: `gpt-5.6-sol`, medium reasoning
- Matrix: eight tasks × three languages × six complete-bundle replicates =
  18 fresh sessions and 144 hidden-judged task assignments
- Raw result:
  `benchmarks/results/agent_application_023_protocol_v1_v0.3.155.json`
- Raw SHA-256:
  `fbe356681089cd59c3616a845adf29a8fbfceee10476fac7312780cc07275342`
- Report: `benchmarks/reports/023-application-corpus-parity-failed.html`
- Report inputs:
  `benchmarks/reports/023-application-corpus-parity-failed.artifact.json`,
  `.sql`, and `.chart-map.md`
- Integrity: 18 unique thread IDs; 18/18 fresh-session, checker-integrity,
  and command-protocol checks passed; no timeout, nonzero agent exit, or
  runner error

| Language | Hidden tasks | First-check tasks | Repairs | Median tokens/task | Median seconds/task | Source tokens/task |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 48/48 | 33/48 | 9 | 13,461.56 | 11.4346 | 206.44 |
| Python | 48/48 | 48/48 | 0 | 6,242.00 | 6.6633 | 200.25 |
| Rust | 48/48 | 48/48 | 0 | 6,584.69 | 9.4315 | 365.88 |

The strict gate failed 1/4. Correctness passed; tokens, elapsed, and first
check failed. Parley used 2.16× Python's and 2.04× Rust's median reported
tokens per task. It took 1.72× Python's and 1.21× Rust's elapsed time. No
Parley session was repair-free, so the preregistered clean-session sensitivity
analysis is unavailable.

Exact file judgment worked as designed. The harness deleted the expected file
before every case and checked exact UTF-8 contents afterward. Python and Rust
passed `file_backed_notes` initially in all six sessions. Parley repaired it in
all six, then passed all 6/6 hidden task judgments and 24/24 hidden file cases.
Across languages all 72 exact file cases passed.

The 15 Parley first-task failures classify as follows:

| Signature | Events | Task families | Independent sessions |
| --- | ---: | ---: | ---: |
| Descending range assumed for ticket ordering | 5 | 1 | 5 |
| Unparenthesized join plus suffix | 4 | 4 | 1 |
| Indexed `repeat` form | 3 | 1 | 3 |
| `newline` pseudo-identifier | 2 | 1 | 2 |
| Unwrapped read-file maybe | 1 | 1 | 1 |

Five independent sessions assumed `for each priority from 5 to 1` descends,
but all five events belong to one ordering task. Adding descending-range
semantics would require a deliberate general design for endpoints and step
behavior, not adoption from that transcript. Four join failures crossed four
tasks but came from one session's repeated precedence habit. The remaining
six failures all belong to the one file task and use either redundant indexed
repeat syntax, a nonexistent value, or an intentionally unchecked maybe.
No signature crosses both unrelated tasks and independent sessions. **No
compiler, grammar, runtime, prompt, or skill change follows from 023.**

Parley source was close to Python-sized and far shorter than Rust: 206.44 rough
tokens/task versus 200.25 and 365.88. Parley is 43.58% shorter than Rust while
using more than twice the reported agent tokens. This again locates the gap in
first-check discoverability and repair context, not emitted source verbosity.

Preserve 023 unchanged. Further work should target general discoverability of
existing semantics on new tasks or a broader real-repository benchmark, not
add aliases from these transcripts. Any future compiler change still requires
new unrelated-task recurrence, general usefulness, semantic consistency, and
maintainability.

## Design and preflight for 024 — Seeded maintenance corpus

- Prepared: 2026-08-05
- Compiler: Parley 0.3.155, unchanged from iteration 023
- Model planned: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged
- Work mode: modify four existing programs in place rather than generate them
  from empty files
- Planned matrix: four tasks × three languages × six complete-bundle
  replicates = 18 fresh sessions and 72 hidden-judged assignments
- Seed: `20260811`

Iteration 023 tied final correctness while Parley source was 43.58% shorter
than Rust and only 3.09% longer than Python, yet Parley used more than twice
their reported agent tokens. Iteration 024 therefore changes the unit of work,
not the language: an agent receives an already correct application program and
must implement a new requirement. The four maintenance families add an invoice
discount/net total, wildcard policy matching, shipment cancellation, and a
second exact notes index file.

Every seed is the shortest hidden-correct iteration-023 final source for its
language/task by rough-token count. Provenance records the exact source task and
replicate. A preflight test confirms all 12 seed strings are byte-identical to
the preserved raw 023 result and were hidden-correct there. Under v0.3.155 all
12 compile, while all four seeds per language fail their new public case as
intended. A separate Python oracle recomputes all 20 new public/hidden stdout
and file contracts exactly.

The general benchmark harness now accepts optional `seed_sources`, writes them
outside the protected checker-integrity set, reproduces them in the prompt,
requires editing as the first action, and records seed size plus a deterministic
rough-token edit count. Cold-start manifests and prompts remain backward
compatible. The benchmark module passed 41/41 tests, and the corrected full
suite command `PYTHONPATH=/Users/arjun/Desktop/parley-lang python3 -m pytest -q`
passed 318/318 in 102.74 seconds.

This related-source corpus is a performance-methodology test, not independent
language-design evidence. No syntax, compiler, grammar, AST, checker, runtime,
prompt skill, or diagnostic is changed. No 024 transcript may justify a
language change; future proposals still need recurrence across unrelated new
tasks and independent sessions, then general-usefulness, semantic-consistency,
and maintainability review.

## Pre-registration for 024 — Seeded application maintenance

- Date frozen: 2026-08-05
- Compiler: Parley 0.3.155; last language change commit
  `8f4a66885f3e0837f1595d72cf38ada5b8112f97`
- Frozen harness/corpus commit:
  `cb4e3d4b5f3dd1a7ffc788622d93dcb5e1fffee8`
- Model: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged, SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Task manifest: `benchmarks/agent_tasks_maintenance_024.json`, SHA-256
  `2d6b248f11781ca6d2039e5fdf5023ce43a679fd92c733fed0e6ce15cedddbc0`
- Protocol: `benchmarks/bundle_protocol_024.json`, SHA-256
  `d69506b3b7c3c50707534ddecc6ff1fcba8cf3a9651b53c93356dd652a929b93`
- Matrix: four tasks × three languages × six complete-bundle replicates =
  18 fresh sessions and 72 hidden-judged assignments
- Seed: `20260811`

The same strict four-condition gate is frozen at bundle size four: hidden
correctness, reported tokens per assigned task, elapsed time per assigned task,
and first-check task success. Each agent sees the exact language-specific seed
in both its measured prompt and workspace. The runner records prompt effort,
seed/final source size, and deterministic inserted/deleted rough-token edit
size. Expected output files are removed independently before each public and
hidden case and compared byte-for-byte as UTF-8 text.

Preserve every session without selective reruns. A pass requires a broader
real-repository confirmation before any general parity claim. A failure cannot
trigger a language or instruction change from this related-source corpus; the
next evidence source must be selected for external validity, not transcript
syntax.

## 024 — Seeded maintenance correctness ties; strict parity still fails

- Completed: 2026-08-05
- Compiler: Parley 0.3.155
- Model: `gpt-5.6-sol`, medium reasoning
- Matrix: four tasks × three languages × six complete-bundle replicates =
  18 fresh sessions and 72 hidden-judged assignments
- Raw result:
  `benchmarks/results/agent_maintenance_024_protocol_v1_v0.3.155.json`
- Raw SHA-256:
  `ca3d24d96ef63242aa35ae8970df617df275d2e3cd552b740c4b15d3f67963e1`
- Report: `benchmarks/reports/024-seeded-maintenance-parity-failed.html`
- Report SHA-256:
  `72e2fb1dec296ece26a45d7a833e9f0938f4b497583a4619816fe9d2b16027a5`
- Report inputs:
  `benchmarks/reports/024-seeded-maintenance-parity-failed.artifact.json`,
  `.sql`, and `.chart-map.md`
- Integrity: 18 unique thread IDs; 18/18 fresh-session, checker-integrity,
  and command-protocol checks passed; no timeout, nonzero agent exit, or
  runner error

The first launcher invocation stopped before creating a model session because
the Homebrew `parley` entry point could not import the checkout under the
isolated environment (`ModuleNotFoundError`). No raw output file or benchmark
cell existed. The exact frozen command then used a temporary executable pinned
to this checkout and Python 3.14. No protocol, task, prompt, harness, result
cell, or gate changed.

| Language | Hidden tasks | First-check tasks | Repairs | Median tokens/task | Median seconds/task | Seed tokens/task | Final source tokens/task | Edit tokens/task |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 24/24 | 17/24 | 6 | 20,547.88 | 12.6944 | 186.75 | 243.38 | 67.38 |
| Python | 24/24 | 24/24 | 0 | 11,142.88 | 6.1056 | 167.00 | 206.25 | 40.25 |
| Rust | 24/24 | 24/24 | 0 | 11,654.50 | 7.2065 | 339.25 | 416.00 | 87.75 |

The strict gate failed 1/4. Correctness passed; tokens, elapsed time, and first
check failed. Parley used 1.84× Python's and 1.76× Rust's median reported
tokens per task. It took 2.08× Python's and 1.76× Rust's median elapsed time.
Every Parley session required exactly one repair and used more tokens than
every Python or Rust session, so the preregistered repair-free sensitivity is
unavailable and the aggregate is not driven by one outlier.

Exact two-file judgment worked. The harness removed both expected files before
every case. Parley passed the notes-index task initially in five of six
sessions, then passed 6/6 hidden task judgments and 24/24 hidden file cases.
Python and Rust were first-check clean. Across languages all 72 hidden file
cases matched stdout and both exact UTF-8 files.

The seven Parley first-task failures classify as follows:

| Signature | Events | Task families | Independent sessions |
| --- | ---: | ---: | ---: |
| Whole-number division produced decimal | 6 | 1 | 6 |
| Unwrapped read-file maybe | 1 | 1 | 1 |

All six invoice drafts assigned `/` or `divided by` to a whole-number
discount. Parley correctly typed the result as decimal and emitted P301 with a
direct `rounded`, `floor of`, or `ceiling of` repair hint. Every session used
`floor of` on the next attempt. Repetition across sessions is strong evidence
that this one requirement is surprising, but it is still one task family and
does not settle general whole-number-division syntax or semantics. The file
draft split a `maybe text` without unwrapping once and repaired with the
existing `value of` operation.

Source compactness did not predict agent effort. Parley's final source was
41.50% shorter than Rust and its median edit was 23.22% smaller, yet Parley
used 76% more reported agent tokens. Relative to Python, Parley's final source
was 18.00% larger and its edit was 67.39% larger. The measured Parley prompt
also included the frozen skill. Descriptively, the maintenance token ratio
narrowed from iteration 023's 2.16× Python and 2.04× Rust to 1.84× and 1.76×,
but the task count, source context, and unit of work changed, so this is not a
causal improvement estimate.

The canonical report builder passed validation, packaging, source-dialog
interaction, and responsive browser checks at 1440 and 390 pixels. A first
successful build was followed by a report self-audit that added an adjacent
interpretation paragraph for each secondary chart; the final corrected build
again passed every stage with 35 rendered blocks, six charts, seven metrics,
and six tables.

**No compiler, grammar, AST, checker, runtime, diagnostic, prompt, or skill
change follows from iteration 024.** The corpus deliberately reuses source
from 023 and cannot count as independent language-design recurrence. Preserve
024 unchanged. The next defensible evidence is a preregistered real multi-file
repository-maintenance corpus with existing and hidden tests, equivalent
seeded repositories, changed-file scope, and patch-size measurement. Reopen a
language design only after recurrence across unrelated new domains plus
general-usefulness, semantic-consistency, and maintainability review.

## Design and preflight for 025 — Multi-file repository maintenance

- Prepared: 2026-08-05
- Compiler: Parley 0.3.155, unchanged
- Model planned: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged
- Planned matrix: four repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 72 hidden-judged assignments
- Seed: `20260813`

Iteration 024 showed that inline seeded source narrowed the descriptive token
ratio but left every Parley session repairing. Iteration 025 increases external
validity without mining its transcripts: each task is a new two-file repository
whose requirement crosses an entrypoint/helper boundary. The domains are
delivery pricing, inventory reservation, incident routing, and filtered exact
file reporting. None reuses 024 source or changes Parley semantics.

The language-neutral harness now supports safe relative `seed_files` and one
declared entrypoint per language. A protected `./sources` command prints only
the eight editable source files in the session. The first shell command must be
exactly `./sources`, exactly once; afterward the only shell command is
`./check`. Checker, source-printer, and configuration hashes remain protected.
This allows controlled repository inspection while preventing arbitrary
reconnaissance. The runner records all seed/final files, rough-token edit size,
and changed-file count. Existing cold-start and inline-seed protocols retain
their exact `./check`-only prompt sentence and behavior.

All 12 language-specific repositories compile and pass two frozen seed cases
per task (24 seed cases per language). Every unmodified seed compiles but fails
its new public case. An independent Python oracle reproduces all 20 new
public/hidden stdout and expected-file contracts. Unsafe repository paths are
rejected. Targeted repository tests and the complete corrected suite passed;
`PYTHONPATH=/Users/arjun/Desktop/parley-lang python3 -m pytest -q` finished
324/324 in 112.02 seconds.

No compiler, grammar, AST, checker, runtime, diagnostic, prompt skill, or
instruction-compression change is part of this work. Preserve the harness and
corpus in a commit, then freeze protocol 025 before any model session.

## Pre-registration for 025 — Multi-file repository maintenance

- Date frozen: 2026-08-05
- Compiler: Parley 0.3.155; last language change commit
  `8f4a66885f3e0837f1595d72cf38ada5b8112f97`
- Frozen harness/corpus commit:
  `814a05b63a9bdd9e8f3d9e5ff85cb016a3f1531d`
- Model: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged, SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Task manifest: `benchmarks/agent_tasks_repositories_025.json`, SHA-256
  `36d5a42d46e35921decd9d2c4af6c5fc9cbaf1f8301cc29922f4bdb522425e95`
- Protocol: `benchmarks/bundle_protocol_025.json`, SHA-256
  `26f51b2c2753e1b9661296d77e42d80a5e9c099fc40df0e1f63fd6b4ecf57364`
- Matrix: four repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 72 hidden-judged assignments
- Seed: `20260813`

The strict four-condition gate remains hidden correctness, reported tokens per
repository, elapsed time per repository, and first-check repository success.
Each session must run `./sources` exactly once as its first shell command; only
`./check` may follow. Source-printer output is therefore measured model context
without inline prompt duplication. The four repositories expose eight editable
files per session. Changed-file count, seed/final rough tokens, and edit rough
tokens are frozen secondary maintenance measures.

Preserve every session without selective reruns. If parity passes, require a
larger confirmation. If it fails, no same-corpus syntax or instruction change
is allowed. Only recurrence across unrelated new repositories and independent
sessions may enter separate general-usefulness, semantic-consistency, and
maintainability review.

## 025 — Perfect repository reliability; strict efficiency parity narrowly fails

- Completed: 2026-08-05
- Compiler: Parley 0.3.155
- Model: `gpt-5.6-sol`, medium reasoning
- Matrix: four repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 72 hidden-judged assignments
- Raw result:
  `benchmarks/results/agent_repositories_025_protocol_v1_v0.3.155.json`
- Raw SHA-256:
  `bfbbbe59624696ed722b7928a8bd5e3fd4334229d529aa691f2061e7e61a923d`
- Report: `benchmarks/reports/025-repository-maintenance-near-parity.html`
- Report SHA-256:
  `591e495fd6d33af2b781f527613aca90352f029a1f8011428337ddabdebc327c`
- Report inputs:
  `benchmarks/reports/025-repository-maintenance-near-parity.artifact.json`,
  `.sql`, and `.chart-map.md`
- Integrity: 18 unique thread IDs; 18/18 fresh-session, source-order,
  checker-integrity, and command-protocol checks passed; no timeout, nonzero
  agent exit, or runner error

| Language | Hidden repos | First-check repos | Repairs | Median tokens/repo | Median seconds/repo | Seed tokens/repo | Final source tokens/repo | Edit tokens/repo | Changed files/repo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 24/24 | 24/24 | 0 | 15,812.00 | 13.5096 | 105.50 | 186.25 | 92.25 | 2.00 |
| Python | 24/24 | 24/24 | 0 | 14,932.25 | 10.2835 | 89.00 | 155.25 | 74.75 | 2.00 |
| Rust | 24/24 | 24/24 | 0 | 15,611.63 | 13.1285 | 211.25 | 307.75 | 124.00 | 2.00 |

The strict gate failed 2/4. Correctness and first-check reliability passed;
tokens and elapsed time failed. Parley is 5.89% above Python and only **1.28%
above Rust** in median reported tokens per repository. It is 31.37% above
Python and **2.90% above Rust** in median elapsed time. All six Parley sessions
are repair-free, so the preregistered clean-session sensitivity is the entire
primary sample rather than a selected subset.

The source protocol worked exactly. All 18 sessions ran `./sources` once as
their first shell command and then one successful `./check`. The source
printer exposed only the eight editable seed files. Every one of the 72
repository assignments changed both its entrypoint and helper; checker and
source-printer hashes held. The filtered-report repository passed on the first
check in all 18 sessions, and all 72 hidden file cases matched exact UTF-8
output.

There are no first-check failures, hidden failures, diagnostics, or failure
signatures to classify. **No compiler, syntax, diagnostic, prompt, or skill
change follows from iteration 025.** The reliability improvement comes from
consistent existing patterns across a helper boundary, not a new alias.

Four Parley sessions cluster tightly between 15,762.25 and 15,823.25 reported
tokens per repository, near all six Rust runs. Replicates 2 and 5 use 20,656.00
and 19,761.00 without extra commands or repairs, lifting Parley's weighted mean
to 17,261.13. The median near-parity result is therefore supported by most
sessions, while clean-session context variance remains material. Parley's
median input tokens are 1.48% above Rust and its output tokens 6.14% below;
combined total still misses by 1.28%.

Parley final source is 39.48% shorter than Rust and its median edit is 25.60%
smaller. Relative to Python, Parley final source is 19.97% larger and its edit
is 23.41% larger. The unchanged skill makes Parley's agent prompt about 416
characters per repository larger than Rust's, consistent with—but not causal
proof of—the remaining fixed-context gap.

The canonical report builder passed validation, packaging, source-dialog
interaction, and responsive browser checks at 1440 and 390 pixels. The final
reader contains 33 rendered blocks, five charts, eight metrics, and five
tables; artifact metrics match the raw summary exactly.

Preserve 025 unchanged as the strongest broad result so far. The next
defensible experiment is a size-eight repository workload with four additional
unrelated repositories under the same source protocol, skill, model, and gate.
That tests whether general workload amortization closes the remaining 1.28%
Rust token gap without tuning the current tasks. If it passes, run the planned
larger confirmation before claiming general parity.

## Design and preflight for 026 — Eight-repository expansion

- Prepared: 2026-08-05
- Compiler: Parley 0.3.155, unchanged
- Model planned: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged
- Planned matrix: eight repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 144 hidden-judged assignments
- Seed: `20260815`
- Combined manifest SHA-256:
  `6dadf527fd966c93fcf034074e397c69050f6dfa9ca16e6df722fc796459157f`
- Four-task additions SHA-256:
  `972730ddc781dfad2d589737c6ba0577d2482dbdb0c454a2c0151ad18d028c91`

Iteration 026 is the prerecommended independent scale expansion, not a replay
or repair of 025. The first four repository objects are preserved exactly from
025. Four unrelated two-file repositories add support-SLA policy, feature
rollout eligibility, tolerance-aware ledger reconciliation, and exact
priority-filtered file output. Their requirements cross entrypoint/helper
boundaries but introduce no Parley-specific vocabulary or transcript-derived
syntax.

The corpus is reproducibly assembled by
`benchmarks/build_repository_corpus_026.py` from the preserved 025 manifest and
the separately reviewable 026 additions. An independent oracle reproduces all
20 new public/hidden stdout and exact-file contracts. All 12 new
language-specific seeded repositories compile and pass their old contracts;
every unmodified seed compiles but fails its new public requirement. Tests
also prove that the combined manifest contains eight unique task IDs, with the
first four task objects equal to 025 and the final four equal to the additions.
The complete pre-protocol suite passed 328/328 in 124.13 seconds.

No compiler, grammar, AST, checker, runtime, diagnostic, prompt skill, source
protocol, or instruction-compression change is part of this work. Commit and
push the reviewed corpus before freezing protocol 026. Preserve every later
session without selective reruns. A passing pilot still requires a larger
confirmation before any general parity claim.

## Pre-registration for 026 — Eight-repository expansion

- Date frozen: 2026-08-05
- Compiler: Parley 0.3.155; last language change commit
  `8f4a66885f3e0837f1595d72cf38ada5b8112f97`
- Frozen harness/corpus commit:
  `74c0f67c3531719c491da4e7613a5f2c9e8f8e4e`
- Model: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged, SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Task manifest: `benchmarks/agent_tasks_repositories_026.json`, SHA-256
  `6dadf527fd966c93fcf034074e397c69050f6dfa9ca16e6df722fc796459157f`
- Protocol: `benchmarks/bundle_protocol_026.json`, SHA-256
  `aca80f25160e8b7b0eed88a1ca1ab062ad158c3a86723c7786464e400e953e2a`
- Matrix: eight repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 144 hidden-judged assignments
- Seed: `20260815`

The primary scale is eight. The strict gate is unchanged: Parley must preserve
100% hidden-repository success, match the better baseline's first-check rate,
and use no more median reported tokens or median elapsed time per repository
than the lower baseline. Each session exposes sixteen editable source files by
running `./sources` exactly once as its first shell command; only `./check` may
follow. There are 48 public, 192 hidden, and 48 exact hidden-file judgments per
language.

Run the complete 18-session matrix once and preserve every session, including
infrastructure failures, without selective reruns. Report per-session and
per-repository evidence, file-scope edits, exact-file results, repairs, and
integrity/protocol status. If the strict gate passes, preregister a larger
confirmation before claiming parity. If it fails, do not tune this corpus or
change syntax/instructions from a same-corpus signature.

## 026 — Rust efficiency parity reached; strict best-baseline gate fails

- Completed: 2026-08-05
- Compiler: Parley 0.3.155
- Model: `gpt-5.6-sol`, medium reasoning
- Matrix: eight repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 144 hidden-judged assignments
- Raw result:
  `benchmarks/results/agent_repositories_026_protocol_v1_v0.3.155.json`
- Raw SHA-256:
  `e071acdf35461f28a6cad5fb927a237a5d075156c231068e5102c7705637c55d`
- Report: `benchmarks/reports/026-eight-repository-expansion-failed.html`
- Report SHA-256:
  `1944cce88cda70e28d12d1942c2b06d587b6a0bbe42b9289441b9dacb0da9232`
- Report inputs: matching `.artifact.json`, `.sql`, `.chart-map.md`, and
  reproducible `build_026_report.py`
- Integrity: 18 unique thread IDs; 18/18 fresh-session, source-order,
  checker-integrity, and command-protocol checks passed; no timeout, nonzero
  agent exit, or runner error

| Language | Hidden repos | First-check repos | Repairs | Median tokens/repo | Median seconds/repo | Seed tokens/repo | Final source tokens/repo | Edit tokens/repo | Changed files/repo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 48/48 | 46/48 | 1 | 8,945.13 | 9.5669 | 100.38 | 191.06 | 107.81 | 2.00 |
| Python | 48/48 | 48/48 | 0 | 8,394.69 | 7.6526 | 86.00 | 161.19 | 90.44 | 2.00 |
| Rust | 48/48 | 48/48 | 0 | 9,079.38 | 10.4539 | 207.50 | 308.31 | 137.56 | 2.00 |

Parley now **beats Rust on both efficiency conditions**: 1.48% fewer median
reported tokens per repository and 8.48% lower median elapsed time. That
reverses iteration 025's 1.28% token and 2.90% elapsed deficits under a corpus
expanded with four unrelated repositories frozen before output. It remains
6.56% above Python in tokens and 25.02% above Python in elapsed time.

The strict better-baseline gate therefore fails 1/4. All 144 assignments pass
hidden cases, but Parley first-checks 46/48 versus both baselines' 48/48; token
and elapsed gates compare against lower Python and also fail. Five repair-free
Parley sessions cluster between 8,908.25 and 8,979.63 tokens per repository.
Their preregistered sensitivity median is 8,928.88, still 1.66% below Rust and
6.36% above Python. One repaired run reaches 14,192.75 and lifts Parley's
weighted mean to 9,814.42.

The repaired session used unsupported `repetition count` in both exact-file
workflows. Both programs failed P101 at `count`, then passed after adding an
explicit one-based counter. These are two analogous tasks in one session, not
independent cross-domain/session recurrence; the other five Parley sessions
avoid the phrase. **No compiler, syntax, diagnostic, prompt, or skill change
follows from iteration 026.**

All 144 hidden exact-file cases pass: 48 per language across filtered-report
and priority-digest workflows. All 144 assignments change both files. Every
session runs `/bin/zsh -lc ./sources` exactly once first, followed only by one
or two `/bin/zsh -lc ./check` commands. The 1,519-character skill and Parley
v0.3.155 are unchanged.

The canonical report builder passes validation, packaging, source-dialog
interaction, and responsive browser checks at 1440 and 390 pixels. The final
reader contains 35 rendered blocks, five charts, eight metrics, and six tables;
artifact headline and language metrics match the raw summary exactly. An
in-app-browser attempt to navigate automatically from report 016 to the local
`file://` output was blocked by the browser URL policy and was not bypassed;
the existing user tab was left untouched.

Preserve 026 unchanged. It is positive evidence that Parley can beat Rust on
repository-shaped agent effort, but it is not Python-and-Rust parity and not a
general claim. The next defensible experiment is a second independent set of
unrelated repositories and a preregistered size-sixteen pilot under the same
source protocol. Do not tune any current task. A passing broader pilot still
requires the planned larger confirmation.

## Design and preflight for 027 — Second independent repository expansion

- Prepared: 2026-08-05
- Compiler: Parley 0.3.155, unchanged
- Model planned: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged
- Planned matrix: sixteen repositories × three languages × six
  complete-bundle replicates = 18 fresh sessions and 288 hidden-judged
  assignments
- Seed: `20260817`
- Combined manifest SHA-256:
  `4d48c171c217cd7be4bc12fb7880c89f0b829470c5e68717fac810f1aace7312`
- Eight-task additions SHA-256:
  `804a0d2aa20b7a570e6e1313a1922e707c6519297fe685a367a32c65a8fe6476`

Iteration 027 follows the preserved 026 recommendation without changing or
tuning any current task. The first eight repository objects are exactly equal
to the 026 corpus. Eight separately reviewable additions cover shipping
manifests, role-aware lockouts, configurable sensor bands, normalized tag
deduplication, overtime payroll, assessment score bands, running-capacity
batching, and path sanitization. Each remains a two-file maintenance change
crossing an entrypoint/helper boundary; none derives syntax from a failure
transcript.

`benchmarks/build_repository_corpus_027.py` reproducibly combines the preserved
026 manifest and new additions. An independent oracle reproduces all 40 new
public/hidden contracts. All 24 new language-specific seeded repositories
compile and pass their two old-contract cases; every unmodified seed compiles
but fails its new public requirement. Tests prove the first eight combined
objects are equal to 026, the final eight equal the additions, and all sixteen
IDs are unique. The complete pre-protocol suite passed 332/332 in 147.11
seconds.

No compiler, grammar, AST, checker, runtime, diagnostic, prompt skill, source
protocol, or instruction-compression change is included. Commit and push the
reviewed corpus before freezing protocol 027. Preserve every later session
without selective reruns. Even a passing size-sixteen pilot requires the
planned larger confirmation before a general parity claim.

## Pre-registration for 027 — Sixteen-repository expansion

- Date frozen: 2026-08-05
- Compiler: Parley 0.3.155; last language change commit
  `8f4a66885f3e0837f1595d72cf38ada5b8112f97`
- Frozen harness/corpus commit:
  `6d10ee11961f6bffc9f6208e763637ed8c3e5b1c`
- Model: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged, SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Task manifest: `benchmarks/agent_tasks_repositories_027.json`, SHA-256
  `4d48c171c217cd7be4bc12fb7880c89f0b829470c5e68717fac810f1aace7312`
- Protocol: `benchmarks/bundle_protocol_027.json`, SHA-256
  `c9d06a379af53a86bb80fb30797f3421c0b3f9c103a93438496aa9f0463893b4`
- Matrix: sixteen repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 288 hidden-judged assignments
- Seed: `20260817`

The strict four-condition gate is unchanged at primary scale sixteen. Parley
must finish 100% hidden-correct, match the better first-check baseline, and use
no more median reported tokens or elapsed time per repository than the lower
Python/Rust median. Each session exposes thirty-two editable files through one
protected `./sources` command first; only `./check` may follow. Each language
receives 96 public, 384 hidden, and 48 exact hidden-file judgments.

Run all 18 sessions once, preserve every result without selective reruns, and
report full per-session/per-repository/token/file evidence. If strict parity
passes, this remains a six-replicate pilot: preregister the larger confirmation
before claiming parity. If it fails, do not tune the corpus or change syntax or
instructions from same-corpus evidence.

## 027 — Perfect Parley reliability; size-sixteen token efficiency regresses

- Completed: 2026-08-05
- Compiler: Parley 0.3.155
- Model: `gpt-5.6-sol`, medium reasoning
- Matrix: sixteen repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 288 hidden-judged assignments
- Raw result:
  `benchmarks/results/agent_repositories_027_protocol_v1_v0.3.155.json`
- Raw SHA-256:
  `9955e67c36d7d3e3ea236644d731a6e4f9054da801b097cf41a7d64ceb64ce7c`
- Report: `benchmarks/reports/027-sixteen-repository-scale-regression.html`
- Report SHA-256:
  `dd49899d2c066c4556d8734e8a2c99c9533cc00df123db1e38fb0e659297c5d5`
- Report inputs: matching `.artifact.json`, `.sql`, `.chart-map.md`, and
  reproducible `build_027_report.py`
- Integrity: 18 unique thread IDs; 18/18 fresh-session, source-order,
  checker-integrity, and command-protocol checks passed; no timeout, nonzero
  agent exit, or runner error

| Language | Hidden repos | First-check repos | Repairs | Median tokens/repo | Median seconds/repo | Seed tokens/repo | Final source tokens/repo | Edit tokens/repo | Changed files/repo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 96/96 | 96/96 | 0 | 7,675.56 | 8.0127 | 87.25 | 179.75 | 106.38 | 1.9375 |
| Python | 96/96 | 95/96 | 1 | 5,046.25 | 5.8393 | 71.94 | 147.91 | 92.22 | 1.9375 |
| Rust | 96/96 | 96/96 | 0 | 5,650.28 | 8.5897 | 187.25 | 296.50 | 135.31 | 1.9375 |

The strict gate fails 2/4. Parley alone is 96/96 first-check clean, so hidden
correctness and first-check reliability pass. Its median tokens per repository
are 52.10% above Python and 35.84% above Rust. Its elapsed time remains 6.72%
below Rust but 37.22% above Python, so the better-baseline token and elapsed
conditions fail.

Size sixteen does not preserve iteration 026's Rust token advantage. The
mechanism is visible in the complete event stream: Parley replicates 2, 5, and
6 apply all 31 changed files in one file-change action and cluster at
6,980.81–7,031.13 tokens per repository. Replicates 1, 3, and 4 split the same
31 files across two file-change actions and cluster at 8,320.00–8,386.06. All
six run one source command, one successful check, and zero repairs. Even the
one-action median, 7,000.56, remains about 24% above Rust's primary median and
39% above Python's, so batching is only a partial explanation.

Python replicate 1 is the only first-check failure: an unexpected indent in
the ledger entrypoint. It repairs once and passes all hidden cases. No Parley
parse, type, runtime, hidden, or draft-signature failure occurs across 96
assignments. **No compiler, syntax, diagnostic, prompt, or skill change follows
from iteration 027.** Mandating one patch action would alter agent workflow and
benchmark instructions rather than improve general language semantics.

All 144 hidden exact-file cases pass. Of 288 assignments, 270 change both
files. All 18 tag-dedup assignments change only the entrypoint in every
language because the existing helper already provides the required lowercase
normalization; this is semantically appropriate shared scope, not a shortcut.

Parley final source remains 39.38% shorter than Rust and its edit 21.39%
smaller, while both are roughly 22% and 15% above Python. This confirms that
source compactness does not by itself predict reported agent context at large
bundle size.

The canonical report builder passes validation, packaging, source-dialog
interaction, and responsive browser checks at 1440 and 390 pixels. The final
reader contains 35 rendered blocks, five charts, eight metrics, and six tables;
artifact headline and language metrics match the raw summary exactly.

Preserve 027 unchanged and stop increasing synthetic bundle size: the
direction is worse despite perfect Parley reliability. Keep 026 as positive
size-eight Rust-efficiency evidence without generalizing it. The next useful
study should use independently sourced real repository maintenance episodes
with test changes and dependency navigation. A larger size-eight confirmation
is justified only if the narrower Rust-parity claim, rather than strict
Python-and-Rust parity, becomes the decision target.

## Harness preflight for 028 — Read-only repository evidence

- Prepared: 2026-08-05
- Compiler: Parley 0.3.155, unchanged
- Instruction: proven 1,519-character core, byte-for-byte unchanged
- Complete compatibility suite: 338/338 passed in 148.68 seconds

Iteration 027 shows that larger explicit rewrite bundles are not a defensible
route to token parity. Iteration 028 therefore changes the task shape, not the
language: agents will diagnose project-style regressions from visible issue and
test evidence rather than receiving every public input/output pair inline.

The language-neutral harness now accepts per-language `context_files` only for
repository tasks. `./sources` prints editable files with the historical format
and labels declared context as `[read-only]`. Context paths use the same safe
relative-path rules as seeded code, cannot overlap editable files, are written
inside the task repository, and join checker/source-printer/config files in the
integrity hash set. The result record measures context characters, lines, and
rough tokens separately from seed/final/edit source metrics.

Tasks may set `show_public_examples` to false. Their public and hidden cases
remain frozen in the protected checker, but the prompt supplies only the issue
statement and directs the agent to inspect declared read-only repository
evidence. The default remains true, and tasks without context preserve the
prior source dump and repository prompt wording. Targeted tests cover visible
context ordering/labels, editability lists, integrity tampering, prompt
behavior, unsafe/overlapping paths, and backward compatibility.

No compiler, syntax, grammar, AST, checker, runtime, diagnostic, Parley skill,
or instruction-compression change is included. Commit and push this harness
checkpoint before authoring and freezing the 028 diagnostic corpus.

## Design and preflight for 028 — Project-style regression diagnosis

- Prepared: 2026-08-05
- Compiler: Parley 0.3.155, unchanged
- Model planned: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged, SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Planned matrix: four repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 72 hidden-judged assignments
- Seed: `20260819`
- Manifest: `benchmarks/agent_tasks_diagnostic_028.json`, SHA-256
  `49147f96ce0f50239314719f4fce76bd979bea2829f5eb629d4cdb0c7097013e`

The corpus changes task shape after iteration 027 instead of increasing the
synthetic rewrite bundle again. Its unrelated regression families are an
invoice boundary, after-hours routing, normalized identity, and state updates
after deferred capacity requests. Every repository has three editable files
and two read-only artifacts (`ISSUE.md` and `tests/regression.txt`). The
read-only contents are byte-identical across Parley, Python, and Rust, and
prompt-level public examples are disabled.

An independent oracle matches all 20 public/hidden cases. All 12
language-specific seeds compile, while every seeded repository fails its one
intended public regression before agent work. Tests also freeze task/file/case
counts, language-symmetric evidence, prompt omission, and integrity coverage
for all context files. The complete pre-protocol suite passes 341/341 in
155.87 seconds.

During fixture authoring, the first local Parley preflight exposed unsupported
`subtotal div 10`; it was corrected to the already-supported whole-number
expression `floor of (subtotal divided by 10)` before the corpus was frozen.
This was a seed transcription correction, produced no measured session, and
does not change the language, skill, or task semantics. The subsequent
preflight compiled all twelve seeds and observed exactly four failing
regressions per language.

Commit and push this reviewed corpus before freezing protocol 028. Then run
all 18 sessions once, preserve every result without selective reruns, and
report diagnosis behavior, complete correctness, first-check repairs, agent
tokens/time, source/context/edit sizes, changed-file scope, integrity, and
command protocol. No same-corpus syntax or instruction change is permitted.

## Pre-registration for 028 — Project-style regression diagnosis

- Date frozen: 2026-08-05
- Compiler: Parley 0.3.155; last language change commit
  `8f4a66885f3e0837f1595d72cf38ada5b8112f97`
- Frozen harness/corpus commit:
  `2cf86bf`
- Model: `gpt-5.6-sol`, medium reasoning
- Instruction: proven 1,519-character core, byte-for-byte unchanged, SHA-256
  `6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c`
- Task manifest: `benchmarks/agent_tasks_diagnostic_028.json`, SHA-256
  `49147f96ce0f50239314719f4fce76bd979bea2829f5eb629d4cdb0c7097013e`
- Protocol: `benchmarks/bundle_protocol_028.json`, SHA-256
  `96916b4731801f0758eda1fdc5bd2bd007b7734052bb0a4a4f3d5b1356502af0`
- Matrix: four repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 72 hidden-judged assignments
- Seed: `20260819`

The strict four-condition gate applies at primary scale four. Parley must
finish 100% hidden-correct, match the better first-check baseline, and use no
more median reported tokens or elapsed time per repository than the lower
Python/Rust median. Every session receives twelve editable and eight read-only
files through exactly one protected `./sources` command first; only `./check`
may follow. Each language receives 24 public and 96 hidden judgments.

Run all 18 sessions once and preserve every result without selective reruns.
Report the complete event stream and context/source/edit accounting. If strict
parity passes, this remains a six-replicate pilot and requires a larger
confirmation before a general claim. If it fails, do not tune the corpus or
change syntax or instructions from same-corpus evidence.

## 028 — Project diagnosis reaches clean near-Rust efficiency

- Completed: 2026-08-05
- Compiler: pinned Parley 0.3.155 binary; language unchanged
- Model: `gpt-5.6-sol`, medium reasoning; Codex CLI 0.146.0
- Matrix: four repositories × three languages × six complete-bundle
  replicates = 18 fresh sessions and 72 hidden-judged assignments
- Raw result:
  `benchmarks/results/agent_diagnostic_028_protocol_v1_v0.3.155.json`
- Raw SHA-256:
  `a11d59d33756b13a4f27efb04389840b8de997991d6dd1031964846b271568ee`
- Report: `benchmarks/reports/028-project-diagnosis-near-parity.html`
- Report SHA-256:
  `9eb3a59c3b75e7ec95ed1dbcc590337c774e8b76932137c386570161b3ca4c65`
- Report inputs: matching `.artifact.json`, `.sql`, `.chart-map.md`, and
  reproducible `build_028_report.py`
- Integrity: 18 unique thread IDs; 18/18 fresh-session, source-order,
  checker/context-integrity, and command-protocol checks passed; no timeout,
  nonzero agent exit, runner error, or selective rerun

| Language | Hidden repos | First-check repos | Repairs | Median tokens/repo | Median seconds/repo | Context tokens/repo | Final source tokens/repo | Edit tokens/repo | Changed files/repo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Parley | 24/24 | 24/24 | 0 | 15,020.88 | 7.0073 | 80.25 | 168.00 | 8.00 | 1.00 |
| Python | 24/24 | 24/24 | 0 | 14,390.75 | 6.5723 | 80.25 | 147.00 | 6.00 | 1.00 |
| Rust | 24/24 | 24/24 | 0 | 14,801.63 | 7.0672 | 80.25 | 283.50 | 7.25 | 1.00 |

The strict better-baseline gate fails 2/4. All three languages are 24/24 on
the first check and hidden cases, so correctness and first-check conditions
pass. Parley is 1.48% above Rust and 4.38% above Python in median reported
tokens per repository. Its median elapsed time is 0.85% below Rust but 6.62%
above Python. Token and elapsed conditions compare against lower Python and
therefore fail.

The result is unusually stable: every completed session uses one source dump,
one successful check, and zero repairs. Per-repository token ranges are
14,996.75–15,109.50 for Parley, 14,378.00–14,468.25 for Python, and
14,786.50–14,828.25 for Rust. There is no failure outlier or repair loop to
remove. Parley final source remains 40.74% shorter than Rust and 14.29% larger
than Python; compact source again does not predict model-token effort directly.

Every language receives exactly 1,531 characters, 27 lines, and 321 rough
tokens of read-only evidence per session. All 144 context-file exposures
remain integrity-clean. Prompt-level public examples remain withheld. The
Parley prompt is 1,090.75 characters per repository versus 670.00 for Python
and 675.00 for Rust because the unchanged skill is included once per session.

The preregistered secondary patch-location audit finds that Parley and Python
change the seeded defect file in all 24 assignments. Rust does so in 22/24.
Rust replicate 6 instead adds caller-side special cases for invoice subtotal
2000 and high-severity after-hours routing, leaving `pricing.rs` and
`routing.rs` incorrect for other callers. Both patches pass every frozen
hidden case, so primary correctness remains 100%; the report labels them as
maintainability-relevant compensations rather than retroactively changing the
gate.

There is no Parley syntax, compiler, diagnostic, semantic, runtime, or draft
failure across the 24 assignments. **No compiler, prompt, or skill change
follows from iteration 028.** The residual gap is model context/workflow, not
evidence for narrow syntax. The one allowed instruction-compression experiment
remains closed.

The canonical report builder passes validation, packaging, source-dialog
interaction, and responsive browser checks at 1440 and 390 pixels. The final
reader contains 35 blocks, five charts, eight metrics, and six tables; artifact
headline/language metrics match the raw summary exactly.

Preserve 028 unchanged. It is strong evidence of perfect Parley diagnosis and
near-Rust efficiency under equal project evidence, but it is not strict
Python-and-Rust parity. The next useful corpus should use independently sourced
project regressions with ambiguous symptoms, dependency navigation, and test
changes, and should score root-cause repair explicitly. A positive broader
pilot still requires the planned larger confirmation before a general claim.
