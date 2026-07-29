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
