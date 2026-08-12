# Parent-owned public checker transport

Iteration 036 showed that `sandbox_workspace_write.network_access=false` also
prevents a process inside the agent sandbox from binding a loopback server. Its
public checker could compile applications but could not exercise their HTTP or
browser behavior. Iteration 037 therefore uses a parent-owned checker boundary.

## Protocol

1. Before the agent starts, the parent creates two mode-`0600` POSIX FIFOs,
   `.benchmark_check_request` and `.benchmark_check_response`, plus a generated
   client and `./check` wrapper in the fresh workspace.
2. The agent remains under `network_access=false`. Running `./check` writes a
   nonce and request ID to the request FIFO, then waits on the response FIFO.
3. The already-running parent broker receives the request and invokes the
   public evaluator outside the network-denied sandbox. That evaluator builds
   the candidate, starts its service on an allocated loopback port, runs the
   frozen public HTTP cases, and drives real headless Chromium for public
   browser cases.
4. The parent atomically preserves the complete attempt record outside the
   agent workspace and returns only bounded public stdout, stderr, status, and
   request ID through the response FIFO.
5. Final integrity compares both FIFO identities (device, inode, file type,
   mode, and owner) and hashes the generated client, wrapper, source printer,
   visible read-only files, and frozen configuration.

The broker serves sequential requests, caps request and response sizes, limits
attempt count, records evaluator exceptions as failed attempts, and rejects
bad request authentication. Hidden cases use a separate parent evaluation
after the session and never enter this channel.

## Threat boundary

This is a measurement-integrity mechanism for a command-constrained coding
agent, not an isolation boundary against an intentionally hostile model. The
generated nonce is readable from the client, and the workspace process can
open its FIFOs. Command-event validation, attempt limits, protected-file
hashes, unexpected-file checks, and the outer Codex sandbox jointly enforce
the preregistered protocol. A protocol violation invalidates the cell; it is
never repaired or silently excluded.

No TCP socket crosses the sandbox boundary. Only the parent evaluator binds
loopback, so outbound network access stays disabled for the complete agent
session.

## Pre-measurement evidence

`smoke_agent_check_transport.py` exercises the full boundary in a fresh
network-denied Codex session. The model may run exactly `./sources` followed by
`./check` and may not edit files. The parent evaluator compiles a fixture,
verifies `GET /status`, loads the page in real Chromium, imports `/app.js`, and
observes the rendered value `42`.

Both frozen model strata passed independently:

| Artifact | Model | Result | Parent evaluation |
| --- | --- | --- | --- |
| `agent_check_transport_smoke.json` | `gpt-5.6-terra`, medium | pass | HTTP 200 plus Chromium title/text |
| `agent_check_transport_smoke_sol.json` | `gpt-5.6-sol`, medium | pass | HTTP 200 plus Chromium title/text |

Each artifact includes the complete Codex event stream, usage, exact command
events, parent attempt, and integrity result. These are execution-mechanism
preflights only. They contain no iteration 037 task semantics and are not
language measurements.

Run the unit boundary tests with:

```bash
pytest -q tests/test_benchmarks.py -k parent_check
```

Run a fresh smoke only before a new protocol is frozen, never as a selective
rerun of a measured cell:

```bash
python3 benchmarks/smoke_agent_check_transport.py \
  --model gpt-5.6-sol \
  --workspace /private/tmp/parley-agent-check-transport-smoke \
  --output /private/tmp/parley-agent-check-transport-smoke.json
```
