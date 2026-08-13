# Full-stack iteration 045 product freeze

Parley v0.5.6 is frozen before any iteration-045 task, case, scaffold,
formula, route, field, defect, comparison threshold, prompt, or model output is
selected. The product evidence and compact response-web context are separate
committed boundaries.

## Bound product

- Version: v0.5.6
- Product commit: `6bae1149d101d5a483f31f55905083e0a939c1da`
- Product tree: `525b23b0191cb5f16a9cc4b5281d9b9af912898c`
- Context commit: `1a73fc7ea7d60f5235d5cd3173eba858a6a384b7`
- Context tree: `b704aff898c299d0d15f549f30078753ae35e7b9`
- Context: `skill/parley/references/scaffolded-response-web-v0.5.6.md`
- Context SHA-256:
  `58e1066e2c313c35617d96c5f8829e4ca14f6a77a60fdba0d8af7b19a2fab2b8`
- Context budget: 1,281 bytes / 313 `o200k_base` tokens

Opted-in typed routes can now return request-dependent status, bounded
application headers, and a separately encoded JSON body. The checker verifies
the configured record contract. The runtime rejects invalid statuses, header
injection, duplicates ignoring case, server-owned framing/hop-by-hop fields,
and count/byte limit violations. Static routes and both strict JSON backends
remain supported.

## Evidence boundary

Fourteen dedicated cases passed across static checking, both generated JSON
backends, compiled 401 authentication challenges, 201 creation, 422 validation,
malformed-request precedence, adversarial status/header inputs, bodyless
statuses, and `HEAD`. The complete suite passed 643/643 both before and after
the version advance. A 143,349-byte v0.5.6 wheel built successfully with
SHA-256
`f3fa31b3fb7ff23faa5f13b54d32c3f26a8cc65daed28cdbb21458263314a458`.

The deterministic artifact `fullstack_agent_045_product.json` binds product,
verification, documentation, context, and evidence blobs from their exact Git
commits so later development cannot rewrite this boundary. Its SHA-256 is
`49e1ee43ce014e3888a193442e426269f7bdf19b0403ab29a2b3a40505596216`.

## Claim boundary

This is an accepted capability and static-context result, not a comparative
agent outcome. It does not reinterpret 044, prove mature-framework parity, or
establish universal superiority. A successor study must use a disjoint unseen
population, separately frozen after this checkpoint, and retain correctness,
first-check, complete-token, elapsed, maintainability, all-strata, external
evidence, scratch-lifecycle, and no-rerun controls.
