# Fresh-agent full-stack study 040

Iteration 040 is the independent successor to study 039. This first checkpoint
contains task and case semantics only. Parley v0.5.2, its contextual P315
diagnostic, and the versioned 1,164-token core/web context were committed before
these names, formulas, routes, fixtures, or defect mechanisms were selected.

## Frozen task population

The corpus has four assignments:

1. Build a museum rotation planner with permanent and borrowed pieces, late
   opening time, tour blocks, labels, and exhibit modes.
2. Build a harbor signal planner with fog-reduced beacons, vessel coverage,
   crew load, and congestion states.
3. Repair rooftop battery discharge that consumes protected reserve energy.
4. Repair bookmobile loading that subtracts lift assistance instead of adding
   it to deck slots.

Each assignment has a unique typed POST route, a status route, a deterministic
scalar ES-module export, four public cases, and five hidden cases. Both
visibility sets include real-browser judgment. The field named by
`shared_result_field` must agree with the browser result for equivalent input.

## Independence boundary

Task IDs, case IDs, request fields, response fields, POST routes, and browser
exports are disjoint from iterations 036–039. The product domains, formulas,
fixtures, reserve-depletion defect, and lift-polarity defect are new. No 040
scaffold, reference implementation, agent prompt, model output, threshold, or
protocol exists at this checkpoint.

The population deliberately mixes ceiling division, multiplication, guarded
subtraction, minimum/maximum clamps, boolean adjustments, ordered reserve
allocation, and three-way states. Only the museum task uses quotient batching,
so 040 is not a disguised replay of 039's conversion failure.

Task and case files must be committed alone before any stack implementation or
comparison protocol. A later protocol must bind that commit and the exact file
hashes. Execution code may make these contracts runnable but may not change
their semantics or expected values.

## Claim boundary

A positive result could support only the frozen models, stacks, tasks, and
session protocol later preregistered for 040. Four synthetic assignments cannot
prove universal superiority, production-framework parity, or performance in
unmeasured domains. Every cell and failure must be published without selective
reruns or correctness-conditioned efficiency filtering.

## Current state

The semantics are ready for their standalone corpus commit with these exact
SHA-256 values:

- tasks: `8f1f56a7f59f6080b239634df1c469f0b83e37432af9d966b94779ec8022e211`
- cases: `f21a5f863ba79d13513e9a6bda934cad6ab8358e57f678598840c6046d3c4806`

An independent oracle verifies every successful HTTP and browser fixture, the
4/5 public/hidden split, browser coverage, metadata, and disjointness from all
four prior fresh-agent corpora. The strict comparison is preregistered in
`fullstack_agent_040_protocol.json` with SHA-256
`cfac96ea73fb24a273b05e7376bb28eb8008b4e3ffff80cd33942370cb54a075`.
It binds Parley v0.5.2, the versioned 1,164-token context, four languages, two
medium-reasoning model configurations, three replicates, and the unchanged
six-condition gate. That statement records the corpus/protocol checkpoint;
later commits built and froze the harness without changing task semantics.

## Execution and result

The final protocol revision has SHA-256
`3f0dc69b18b5f2dcad5a21eaddcefd498a2ebfd81694a7f2cd516e5b6875ed83`.
Before measurement, 16/16 reference stack/task cells passed all nine cases,
16/16 broken maintenance seeds built and failed public semantics, 8/8 repair
root boundaries passed, and orchestration smoke coverage passed. The final
execution boundary is commit `2820f4eb3bc44578bdc60237559782c07a2511df`.

The 96-row raw result has SHA-256
`37b631af1ca17033ea30fe433699c52e90f7175b42454ac819e7bd2d3ff50914`.
Host disk exhaustion affected five frozen cells. Two started cells were
permanently interrupted under the preregistered resume rule; three other cells
recorded explicit ENOSPC effects. No affected cell was selectively rerun.

The independent audit has SHA-256
`feffa77e5e9840d9a65bc0d34fb251b280c4dbbab37932cf9ad2fd23b3322904`.
It verifies all 96 journal pairs, 94 external attempt files, and 280/280 stable
post-build hashes. All 460 hidden named cases that actually executed passed,
but four assignments had no hidden semantic execution. The primary gate is
therefore invalidated and false: execution integrity, correctness, first
check, tokens, and elapsed time fail; maintainability alone passes.

The canonical report is
`reports/040-independent-fullstack-study-invalidated.artifact.json`. Iteration
040 is closed unchanged. Any successor must first add generic scratch-capacity
protection, then freeze an independent corpus; it must not rerun or tune on
these tasks.
