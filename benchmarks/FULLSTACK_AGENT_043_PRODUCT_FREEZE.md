# Full-stack iteration 043 product freeze

Parley v0.5.4 is frozen at commit `bf0f85a` before any iteration-043 task,
case, scaffold, formula, route, defect, prompt, or model output exists. The
freeze retains the 222-token v0.5.3 scaffold-aware context that passed the 042
complete-session token gate and adds only the independently measured cold web
build improvement.

## Bound product

- Version: v0.5.4
- Commit: `bf0f85aa33dbd6d52c17260d85a04155d11518c2`
- Tree: `9f3149e3f742167982e8c48212ac26830870e4bb`
- Context: `skill/parley/references/scaffolded-web-v0.5.3.md`
- Context SHA-256:
  `f40a1030de6b3ed75f47183dee41d1ac3185dd87b747f779dab8835d4d63e8c4`
- Context budget: 892 bytes / 222 `o200k_base` tokens

The common typed-route path now emits strict Serde traits directly and avoids
the proc-macro dependency stack. Programs with explicit core JSON expressions
retain derives. Strict unknown, duplicate, missing, wrong-type, optional-field,
and enum behavior is unchanged.

## Evidence boundary

The frozen non-042 build study completed 12 baseline and 12 candidate builds.
Its median of fixture medians fell from 3.855847 to 2.63777 seconds, a 31.5904%
improvement. WASM sizes were unchanged, maximum native-size growth was 0.0036%,
and the final repository suite passed 585/585 tests.

The deterministic product artifact is `fullstack_agent_043_product.json`, with
SHA-256
`1ca7bb4fe501eda55991af61cabb715c5c5c53e202df976ef051809576635ed0`.
It hash-binds the exact Git product blobs, context, baseline, candidate, and
analysis from the evidence commit so later language versions cannot rewrite
this boundary.

## Claim boundary

This is a product and local build-latency result, not a comparative agent
outcome. It does not change iteration 042, predict the 043 gate, prove
production suitability, or establish universal superiority. A successor study
must use a new disjoint population and preserve the six-condition all-strata
gate, external execution evidence, exact-build checks, scratch lifecycle, and
no-rerun rule.
