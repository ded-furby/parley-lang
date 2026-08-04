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
