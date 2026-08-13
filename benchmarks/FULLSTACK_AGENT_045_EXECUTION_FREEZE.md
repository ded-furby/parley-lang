# Full-stack agent study 045 execution freeze

Study 045 is permitted to execute only from protocol revision 2. The revision
freezes the validated response-control harness after protocol revision 1 and
before any measured model session.

## Adaptation boundary

- Product code: `6bae1149d101d5a483f31f55905083e0a939c1da`
- Corpus code: `3f3a5943532cd63a151ec8221715f75ab352a931`
- Protocol revision 1: `4aebf5f`
- Validated harness: `58aaf262bffa97a28a0a23cb310de45c9fd59719`
- Measured sessions before this freeze: `0`

No task, case, expected status, expected JSON value, expected application
header, browser value, model, reasoning setting, replicate count, threshold,
or primary gate changed during harness construction.

## Validation gate

The clean-room validator built a reference and seed workspace for every task
and language combination:

- 16 of 16 reference cells passed all nine named cases (144 case executions);
- 16 of 16 seed cells built successfully and 0 of 16 passed the public suite;
- all eight maintenance task/language boundaries changed exactly the declared
  route-handler root;
- every build preserved all protected and read-only inputs;
- peak validation workspace use was 161,230,321 bytes, giving 13.319x headroom
  inside the frozen 2 GiB per-worker allowance.

The HTTP judge forwards candidate request headers, lets typed handlers decide
negative-domain 422 responses, and compares the complete normalized set of
application response-header pairs. Server-owned and hop-by-hop headers are
excluded; duplicate application headers cannot collapse into a passing map.

The parent-owned orchestration smoke proved the FIFO source/check path, one
bounded public attempt, exact-build preservation, HTTP and Chromium execution,
a failing missing-header seed case, and a passing `www-authenticate` case.

Revision-1 evidence is retained in
`benchmarks/fullstack_agent_045_validation.json` and
`benchmarks/fullstack_agent_045_orchestration_smoke.json`. Revision 2 requires
those checks to be rerun so their protocol identity advances before measured
execution.

## Execution integrity

The runner refuses measured output while the protocol revision is not exactly
2. Revision 2 binds every transitive runner, scaffold, logic, proxy, transport,
exact-build, scratch, dependency-lock, and preparation input by SHA-256.

All 96 cells remain fresh, randomized, once-run sessions. Durable start,
finish, parent-attempt, and cleanup evidence precedes bounded reclamation.
Only never-started cells may execute after resume; a started unfinished cell is
a permanent interruption failure. Any repository, toolchain, FIFO, protected
file, build, cleanup, or scratch-capacity failure remains visible and cannot
authorize a selective rerun.

The strict six-condition gate remains unchanged. It is evidence for this
frozen comparison only and does not imply universal language superiority.
