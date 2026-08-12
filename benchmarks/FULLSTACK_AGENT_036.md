# Fresh-agent full-stack study 036

Iteration 036 is the preregistered fresh-agent follow-up required by product
comparison 035. It asks whether agents can implement and repair new
server-plus-browser application contracts in Parley, Python, TypeScript, and
Rust with comparable correctness and lower complete-session cost.

This study is deliberately separate from Release Radar. None of its product
names, fields, formulas, defects, fixtures, or expected repairs are reused.
The language remains frozen at Parley v0.5.0; no transcript from this corpus
may be used to tune the compiler, skill, task, checker, or metric.

## Frozen task population

The corpus has four assignments:

1. Build a shipping-quote service and browser total function from a contract.
2. Build a capacity-planning service and browser accepted-jobs function from a
   contract.
3. Repair quota calculations that diverge when carryover capacity is present.
4. Repair a tenant cache token that aliases equal resource IDs across tenants.

The first two start from stack scaffolds with blank application logic. The
last two start from complete applications with one predeclared defect in the
shared application-logic module. Every assignment has one typed JSON route,
one deterministic scalar browser export, a status route, public cases, and
withheld cases. HTTP and browser results must agree on the shared scalar rule.

The maintenance mechanisms are independent of report 035. Quota surface
disagreement is historically grounded in openai/codex issue 23192, but the
fixture, formula, source, and expected repair are new synthetic adaptations.
The tenant cache-key task is a synthetic multi-tenant isolation defect. No
upstream code or test is copied.

## Freeze order

The task descriptions and cases are committed before any four-language
scaffold, reference implementation, runner result, or agent session. The
protocol records their byte hashes in a later commit. Stack scaffolds and
reference implementations may then be built only to make the already-frozen
contracts executable; they may not alter a case or gate.

## Agent-visible boundary

Each fresh session receives exactly one language/task workspace. `./sources`
prints all editable source and visibly read-only contract/scaffold files once;
after that, the only permitted shell command is `./check`. The public checker
builds the real service and browser target and runs public HTTP/browser cases.
Hidden cases stay in the parent runner. Internet, plugins, apps, browser-use,
computer-use, multi-agent delegation, user config, and repository rules are
disabled.

Framework and compiler infrastructure is frozen and supplied equally as
language-appropriate stack scaffolding. Its source is preserved and its prompt
cost is measured, but the primary authored-change metric covers every editable
application file. Complete Codex input and output tokens remain the primary
efficiency measure.

## Claim boundary

A positive result can support only this statement: under the frozen models,
stacks, tasks, and session protocol, Parley agents implemented and repaired
these new cross-target contracts with the reported reliability and session
cost. It cannot prove universal language superiority, production framework
parity, or performance superiority.

The complete matrix is published whether positive, mixed, or negative. No
cell may be selectively rerun, removed, replaced, or tuned.

## Execution amendment

Before the first measured cell, an execution-integrity audit found provenance,
workspace-integrity, metric-capture, aggregation, and interruption-recovery
omissions in the initial runner. Protocol revision 2 freezes an execution-only
correction; no task, case, model, metric definition, threshold, or gate changed.
See `FULLSTACK_AGENT_036_AMENDMENT.md` for the preserved checkpoints, exact
changes, and zero-session boundary.

## Result

Iteration 036 completed all 96 frozen cells exactly once at committed checkpoint
`42bb923`. The strict overall gate failed and the execution is not valid for the
intended public-feedback claim.

The parent-run hidden judgment is still complete descriptive evidence: Parley,
TypeScript, and Rust each passed 24/24 assignments; Python passed 12/24, split
between 0/12 implementations and 12/12 repairs. Parley changed exactly its
predeclared root in all 12 hidden-correct maintenance rows. Its 82,903 median
complete-session tokens nevertheless exceeded Python's 74,064.5, and its
38.442-second median exceeded TypeScript's 37.021 seconds.

Two execution defects make the strict run invalid:

1. The network-disabled Codex sandbox also denied loopback socket binding.
   All 179 public checks built, then failed with `Operation not permitted`
   before running an HTTP or browser case. First-check, final-public, and
   repair-feedback metrics are therefore uninterpretable.
2. Cargo deterministically rewrote the reused `release-radar-035` root package
   entry in every Rust `Cargo.lock` to the actual `fullstack-agent-036` package,
   failing read-only integrity in all 24 Rust cells.

The no-rerun rule remains binding. The raw result is preserved at
`benchmarks/results/fullstack_agent_036_raw.json`; the canonical technical
report source is
`benchmarks/reports/036-unseen-fullstack-study-invalid.artifact.json`. A newly
frozen iteration 037 must use new tasks and a loopback-safe checker architecture.
