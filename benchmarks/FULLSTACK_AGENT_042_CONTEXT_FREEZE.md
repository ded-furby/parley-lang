# Iteration 042 pre-corpus context freeze

Version 0.5.3 introduces one specialized context for agents working inside an
already-printed Parley typed-web scaffold:
`skill/parley/references/scaffolded-web-v0.5.3.md`.

The card is frozen before any iteration-042 task semantics, cases, scaffolds,
reference implementation, protocol threshold, or model output exists. That
ordering prevents the next population from being written around a context that
has already seen it.

## Evidence and budget

- Evidence commit: `c18f282da0d358165477daa093844d5ebb4adcda`
- Context SHA-256:
  `f40a1030de6b3ed75f47183dee41d1ac3185dd87b747f779dab8835d4d63e8c4`
- Context size: 892 bytes / 222 `o200k_base` tokens
- v0.5.2 core+web baseline: 4,350 bytes / 1,164 tokens
- Static reduction: 3,458 bytes / 942 tokens / 80.9278%
- Freeze manifest: `benchmarks/fullstack_agent_042_context.json`
- Manifest SHA-256:
  `2fb41ea35931df100ff71ec3b8c2137fd89f93b5a95c5fb22474aa9465217f97`

The 041 matched-pair attribution found a +3,309 median input-token difference,
despite Parley using fewer output tokens and smaller source edits in all 24
pairs. The fixed v0.5.2 rendered context contributed 1,154 more prompt tokens
than Python on every task. That makes repeated context the next generic product
target; it does not turn the attribution's arithmetic diagnostics into measured
results.

## Retained contract

The card retains the scaffold-authority and repair-locality rules, pure shared
logic for HTTP/browser agreement, four-space function syntax, multiplication,
total truncating division, deterministic browser scalars, and the Parley-to-JS
scalar mapping. It omits full manifests, handler and record boilerplate, loader
examples, and general CLI/collection/stdlib syntax because the task's printed
scaffold already supplies those forms.

The card is used alone for this narrow surface. The general Parley skill and all
historical versioned contexts remain available and unchanged for non-scaffolded
or broader tasks.

## Claim boundary and next step

This checkpoint establishes only a deterministic context artifact and its
static budget. It does not establish retained agent reliability, comparative
token parity, or language superiority, and iteration 041 remains gate-not-met.
Next, freeze a new disjoint task/case population, preregister reliability and
efficiency gates, build the harness after that freeze, and execute without
same-population tuning or reruns.
