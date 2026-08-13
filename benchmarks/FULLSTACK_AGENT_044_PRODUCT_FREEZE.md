# Full-stack iteration 044 product freeze

Parley v0.5.5 is frozen at commit `a098996` before any iteration-044 task,
case, scaffold, formula, route, defect, prompt, or model output exists. The
freeze retains the 222-token v0.5.3 scaffold-aware context that passed the 042
and 043 complete-session token gates and adds only the independently measured
second cold web-build improvement.

## Bound product

- Version: v0.5.5
- Commit: `a098996847927c4eb622e2af8d0b7ebee81011c6`
- Tree: `be8be51158157fc33b6b0e00e5ce62e6478d94fe`
- Context: `skill/parley/references/scaffolded-web-v0.5.3.md`
- Context SHA-256:
  `f40a1030de6b3ed75f47183dee41d1ac3185dd87b747f779dab8835d4d63e8c4`
- Context budget: 892 bytes / 222 `o200k_base` tokens

The common typed-route path now emits a strict standard-library JSON parser,
encoder, and type codecs, avoiding all third-party native Cargo dependencies.
Programs with explicit core JSON expressions retain the Serde derive backend.
Strict nested, Unicode, unknown, duplicate, missing, wrong-type,
optional-field, collection, decimal, and enum behavior is covered.

## Evidence boundary

The frozen non-043 build study completed 16 baseline and 16 candidate builds.
Its primary median of fixture medians fell from 2.725720 to 0.802735 seconds, a
70.5496% improvement. Every fixture improved, native servers became smaller,
WASM sizes were unchanged, and the final repository suite passed 609/609
tests.

The deterministic product artifact is `fullstack_agent_044_product.json`, with
SHA-256
`181e26d1204765f3e14a1a24dfe9d82a545d271b3da900785716e509e1551e89`.
It hash-binds the exact Git product blobs, context, baseline, candidate, and
analysis from the evidence commit so later language versions cannot rewrite
this boundary.

## Claim boundary

This is a product and local build-latency result, not a comparative agent
outcome. It does not change iteration 043, predict the 044 gate, prove
production suitability, or establish universal superiority. A successor study
must use a new disjoint population and preserve the six-condition all-strata
gate, external execution evidence, exact-build checks, scratch lifecycle, and
no-rerun rule.
