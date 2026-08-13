# Cold web-build backend study 003

This product benchmark is frozen after full-stack study 046's elapsed
decomposition and before any v0.5.7 compiler, runtime, dependency, linker, or
build-backend change. It does not reuse a 046 task, route, field, formula,
fixture, model output, or workspace.

## Frozen population

Four deterministic v0.5.6 projects exercise the remaining cold-build boundary:

1. `harbor_admission`: a POST route with request-dependent status and headers,
   custom response-envelope field names, and no browser export.
2. `forest_inventory`: a dynamic-response POST route and scalar browser/WASM
   export.
3. `glacier_manifest`: static GET and POST routes plus a scalar browser/WASM export.
4. `manual_json_control`: an explicit Parley `as json` expression that retains
   the dependency-backed implementation as a non-primary regression control.

The exact fixture hashes are:

- `harbor_admission`:
  `7def72af37b813a90f9b993980c32da66ec44e0012571ad24a0d98806a914069`
- `forest_inventory`:
  `216405e22242bfb1283b2ccd1ee3bd826caaaf08fae1daf4f71ca4ac308c96ce`
- `glacier_manifest`:
  `55a604460f741037ad3e7dfefa994a1841928211bc09c6d1c6a4af6f619d7819`
- `manual_json_control`:
  `ae6f86bfdc28ed1ee7fb30175fbb1bd3a70a1c052d7457abf53a8c3d32b6d365`

All identifiers and routes are absent from studies 036--046.

## Measurement protocol

Every cell starts in a new temporary directory with no `.parley-build` target.
Installed dependency sources, the Rust toolchain, and ordinary process and
filesystem caches may remain warm, matching study 046's prepared-toolchain
rule. One complete `forest_inventory` build is an unmeasured warmup. The
benchmark then runs four sequential replicates per fixture and times the full
`parley web build` command from CLI startup through checking, Rust generation,
native/WASM compilation, and bundle copying.

Before each timed command, `parley web check --json` must pass. Every cell must
retain successful command status; native/static/build-manifest artifacts;
declared browser artifacts; response modes; sizes; and hashes. A failed or slow
cell may not be excluded or rerun. The untouched v0.5.6 baseline must be
measured and committed before product implementation begins.

## Preregistered acceptance gate

A candidate is accepted only when all of the following hold:

- The complete existing test suite passes.
- All 16 candidate cells pass without exclusion or rerun.
- The median of the three primary fixture medians improves by at least 20%
  against the frozen v0.5.6 baseline.
- No individual fixture median, including `manual_json_control`, regresses by
  more than 5%.
- Median native-server or WASM size does not increase by more than 25% without
  a separately documented product decision.
- Dynamic statuses/headers, static typed routes, explicit JSON, native serving,
  and browser/WASM behavior retain dedicated regression coverage.

The study measures prepared-toolchain, fresh-target local build latency. It
does not measure model latency, server throughput, ecosystem breadth, or
universal language superiority, and it cannot revise study 046. An accepted
change may inform a later agent study only after the product and evidence are
committed and a new disjoint corpus is frozen.

Next: commit this zero-measurement protocol and harness, then execute and
publish the untouched v0.5.6 baseline exactly once.

## Frozen v0.5.6 baseline

The 16 measured builds at protocol commit
`d04acec70ffbed84381cb555652ca6e6eac2926d` all passed. The primary fixture
medians were 0.696614 seconds for `harbor_admission`, 0.877070 for
`forest_inventory`, and 0.811446 for `glacier_manifest`; their preregistered
median was **0.811446 seconds**. The dependency-backed `manual_json_control`
median was 3.715876 seconds. Its retained first cell took 9.573492 seconds; it
was not excluded or rerun.

Median native-server sizes ranged from 440,704 to 493,888 bytes. The two WASM
artifacts were 1,181 and 1,306 bytes. Dynamic and static response modes were
present in every build manifest exactly as frozen.

Canonical baseline: `web_build_backend_003_baseline.json`; SHA-256:
`5588e490c22c74d5a9e9be8751438ea645341433d264b723b39594acc1dfb9f0`.
This fixes the candidate's 20% target at **0.649157 seconds or lower** for the
median of primary fixture medians, in addition to the per-fixture regression,
correctness, and size gates.

Next: commit this immutable baseline, then profile the generic build backend
without changing the frozen fixture population or acceptance rule.

## Rejected direct-rustc candidate

The candidate compiled dependency-free generated native and browser artifacts
directly with `rustc`, while preserving Cargo and pinned Serde for explicit
language-level JSON. It also extended direct compiler diagnostics to retain
Parley's generated-to-source line mapping. The exact candidate passed the
complete 705-test suite and all 16 measured cells.

| Fixture | Baseline median | Candidate median | Change |
| --- | ---: | ---: | ---: |
| `harbor_admission` | 0.696614s | 0.675405s | -3.0446% |
| `forest_inventory` | 0.877070s | 0.839149s | -4.3236% |
| `glacier_manifest` | 0.811446s | 0.775853s | -4.3864% |
| `manual_json_control` | 3.715876s | 3.772513s | +1.5242% |

The primary median of fixture medians improved only **4.3864%**, from 0.811446
to 0.775853 seconds, below the preregistered 20% requirement. The maximum
fixture regression was 1.5242%; native size did not increase; and the maximum
WASM size increase was 4.4030%, so every non-latency condition passed.

The candidate is rejected and v0.5.7 is not released. Its implementation and
exact verification files are retained in Git history, then the product returns
to v0.5.6. There will be no same-population retuning or second candidate run.

Canonical candidate: `web_build_backend_003_candidate.json`; SHA-256:
`ac161529241f770fed935b455da466f4f24b49e88e68b82ee109ea7011d8602b`.
Canonical analysis: `web_build_backend_003_analysis.json`; SHA-256:
`25a163c74dc646d56d4dd30b16f5bcf0eac0363adcf70be034b5dafd58c36f27`.

This rejection narrows the mechanism: Cargo orchestration contributes a real
but small fraction of the remaining prepared-toolchain build time. It does not
explain study 046's variable end-to-end elapsed difference and does not support
a language-superiority claim.
