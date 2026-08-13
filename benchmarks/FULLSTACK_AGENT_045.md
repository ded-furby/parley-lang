# Full-stack agent study 045: semantics-only corpus freeze

Iteration 045 starts from the committed v0.5.6 product and context freeze at
`6b39eef`. Only after that checkpoint were these task semantics and cases
selected. This commit contains no stack scaffold, reference implementation,
comparison protocol, threshold, prompt, or model output.

## Frozen population

The four new workflows exercise request-dependent response semantics rather
than another status-200 scoring surface:

1. `artifact_accession_build`: authenticated creation with 401 challenge, 422
   domain validation, 201 location, application state header, and browser score.
2. `microgrid_bid_build`: API-key authorization, 422 validation, 409 duplicate
   conflict, 202 asynchronous acceptance, location/retry headers, and browser score.
3. `trail_permit_repair`: a predeclared route-handler defect reverses bearer
   authorization polarity while the business rule and browser path remain intact.
4. `cold_chain_booking_repair`: a predeclared route-handler defect substitutes
   server-owned `content-length` for `location`, turning correct creation into a
   deterministic 500 response-header failure.

All domains, task/case IDs, request/response fields, v9 routes, exports,
formulas, response branches, header sets, fixtures, and defects are disjoint
from iterations 036--044. The two maintenance faults are exposed by public
cases and name `route_handler` as the only accepted root role before scaffolds
exist.

## Frozen cases

Each task has four public and five hidden cases: one public status request, one
public typed workflow result, one public transport/schema failure, one public
browser judgment, two hidden workflow branches, one hidden unknown-field
failure, and two hidden browser judgments. Across 36 cases the population
covers status 200, 201, 202, 400, 401, 409, 415, and 422 plus `location`,
`www-authenticate`, `retry-after`, validation/conflict, and application state
headers. Typed decoding precedes authorization, matching the frozen runtime.

- Tasks: `fullstack_agent_045_tasks.json`
- Tasks SHA-256:
  `39c76f1a4a5e02d5afde27b8e010bc9fb5f75ea670a04c89063eb1cdb160aebb`
- Cases: `fullstack_agent_045_cases.json`
- Cases SHA-256:
  `99d255b2e49153a99900775ac3d947336abf7fb415ffb4186dc1c7b8710e755b`
- Product artifact SHA-256:
  `49e1ee43ce014e3888a193442e426269f7bdf19b0403ab29a2b3a40505596216`

The deterministic builder regenerates both JSON files, and independent tests
verify the 36-case visibility split, prior-study disjointness, response-control
coverage, exact expected outcomes, maintenance observability, and selected
formula anchors.

## Claim boundary and next step

This freezes a broader capability population; it reports no language result.
It cannot establish reliability, efficiency, framework parity, or universal
superiority. Next, commit this corpus, then preregister the balanced language /
model / replicate matrix and six-condition gate before any scaffold or
reference implementation is authored.
