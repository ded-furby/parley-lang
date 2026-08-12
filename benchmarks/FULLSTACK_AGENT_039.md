# Fresh-agent full-stack study 039

Iteration 039 is the prospective successor to study 038. Its first checkpoint
contains only task and case semantics. Parley v0.5.1 and its compact typed-web
reference were committed before these names, formulas, routes, fixtures, or
defect mechanisms were frozen.

## Frozen task population

The corpus has four assignments:

1. Build a festival power planner with speaker, lighting, weather, and
   connection-point components.
2. Build a clinic queue pressure service with urgent capacity and
   five-patient waiting groups.
3. Repair prepaid event credit that is incorrectly capped before weekend fees.
4. Repair seedling dispatch calculations that ignore chilled-capacity loss.

Each assignment has a status route, typed JSON route, deterministic scalar ES
module export, four public cases, and five hidden cases. Public and hidden sets
both include real-browser judgments. The response field named by
`shared_result_field` must agree with the browser result for equivalent input.

## Independence boundary

The 039 IDs, request fields, response fields, POST routes, browser exports, and
case IDs are disjoint from 036–038. Product domains, formulas, fixtures, and the
two repair mechanisms are new. No earlier transcript or solution informed the
semantics.

Only one assignment requires quotient batching. The population also covers
plain multiplication, branching, minimum/maximum clamps, credit ordering, and
capacity propagation, preventing the successor from becoming a replay of
038's archive arithmetic failure.

Task and case files must be committed as their own freeze checkpoint before
any 039 scaffold, reference implementation, comparison protocol, threshold,
or measured session. A later protocol must record that commit and both exact
file hashes. Execution code may make these contracts runnable but may not
change their semantics or expected values.

## Claim boundary

A positive result can support only the frozen models, stacks, tasks, and
session protocol. Four synthetic assignments cannot prove universal language
superiority, production-framework parity, or quality in unmeasured domains.
Every cell and failure must be published without selective reruns or
correctness-conditioned efficiency filtering.

## Measured result

Task and case semantics are frozen at commit `1db9d08`, and the strict
96-cell protocol is preregistered in `fullstack_agent_039_protocol.json`.
Parley v0.5.1 and its 1,168-token combined skill/web context are frozen before
measurement; the context is 48.3% smaller than iteration 038's.

The zero-session harness is preserved at commit `a93a8cc`. Clean-room
validation passed all 16 task/language references across 144 cases. All 16
intentionally wrong seeds built without passing public semantics, all eight
maintenance root boundaries held, and all 48 reference/seed exact build
commands preserved protected inputs. The FIFO orchestration smoke also passed
public and hidden HTTP/browser execution and final integrity.

Protocol revision 2 and `FULLSTACK_AGENT_039_EXECUTION_FREEZE.md` bind all 18
transitive execution files. The final preflight artifacts have SHA-256 values:

- validation: `24ecb9b640b380f644a69d14d602b662ddc86ad2f5b8acca603951f6637d230b`
- orchestration smoke: `e13d33fa1f33f330bf7591c86db5542d66f8a6c31a5c9c66a990a27a1b31b6d4`
- protocol: `e827e55f99af7161931cd0c6c320895afe749217584c87fe2668a36b8170a95b`

The frozen matrix then ran exactly once at measurement commit
`11f41b06dc0e6e72aee39c324735749d91a39682`. All 96 cells completed with
unique cell and thread IDs, 96 immutable journal pairs, 99 retained public
attempt files, and no reruns. The independent audit verified every external
record and all 291 immediate post-build frozen-input hashes.

- raw result: `results/fullstack_agent_039_raw.json`
- raw SHA-256: `28ecc96591b4f0bc3561f302e271f392c30439767d220c5a9e5ba73f0b47a3c3`
- independent audit: `fullstack_agent_039_audit.json`
- audit SHA-256: `bf2270b79cc238d58dc864a6241a3ed982b31dc5f6ccf632bac72be9d71a1fd6`
- canonical report:
  `reports/039-independent-fullstack-study-gate-not-met.artifact.json`
- report SHA-256: `99eec038542242ea3b7a382098e03e8c16e1ca8b78d747f04ef174ed23c91c1d`

The strict gate is false:

| Condition | Result | Evidence |
| --- | --- | --- |
| Execution integrity | Pass | 96/96 once-run cells; 291/291 stable build-hash boundaries |
| Hidden correctness | Pass | Parley/Python/TypeScript 24/24; Rust 23/24; Parley perfect by model and kind |
| First check | Fail | Parley 21/24 versus every baseline 24/24; implementation 9/12 versus 12/12 |
| Complete session tokens | Fail | Parley median 63,301 versus Python 59,784.5; Parley higher in both model strata |
| Elapsed | Fail | Parley median 28.073 s versus TypeScript 22.469 s; Parley higher in both model strata |
| Maintainability | Fail | Parley 6/12 exact roots versus Python/TypeScript 12/12 and Rust 11/11 hidden-correct |

All three Parley first-check misses were sol-medium clinic implementations
that added `otherwise 0` after the total `number from decimal` conversion.
Each recovered in one repair turn and passed hidden judgment. The decimal
return mismatch and unsupported multiplication wording seen in 038 did not
recur, providing independent evidence that the v0.5.1 changes closed those
specific failure classes.

All six Parley event-credit repairs changed exactly their declared defect
root. All six seedling-dispatch repairs were hidden-correct but also edited
`main.par`, so the preregistered locality condition failed. The one hidden
baseline failure was a Rust event-credit repair that mishandled an overpayment
clamp in two withheld HTTP/browser cases.

Parley's median final editable source was 669.5 `o200k_base` tokens: 31.47%
smaller than Python, 21.88% smaller than TypeScript, and 51.73% smaller than
Rust. Its complete token gap to Python fell from 11.79% in 038 to 5.88% in
039, but best-baseline parity remains unmet. Preserve this population and its
negative verdict unchanged; the next phase must use only task-independent
diagnostic, locality, and context-cost improvements before a new corpus is
frozen.
