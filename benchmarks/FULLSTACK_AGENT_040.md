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
four prior fresh-agent corpora. No 040 scaffold, protocol, validation artifact,
execution journal, or measured session exists.
