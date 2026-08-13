# Cold web-build latency study 001

This product benchmark is frozen after iteration 042's elapsed attribution and
before any compiler/build-path change. It does not reuse an iteration-042 task,
formula, route, field, fixture, model output, or workspace.

## Frozen population

Three deterministic Parley projects exercise distinct build surfaces:

1. `status_only`: a native typed GET service without a browser export.
2. `browser_score`: a typed GET service plus a scalar browser/WASM export.
3. `typed_post`: a typed POST request/response service plus a scalar
   browser/WASM export.

Every measured cell starts in a new temporary directory with no
`.parley-build` target. Dependency sources and the installed Rust toolchain may
remain warm, matching the prepared-toolchain rule used by the full-stack
studies. One complete browser fixture is built as an unmeasured process and OS
warmup. The benchmark then runs four sequential replicates per fixture. It
times the complete `parley web build` command, including CLI startup, checking,
Rust generation, native/WASM compilation, and bundle copying.

## Integrity and acceptance

- `parley web check --json` must pass before every timed build.
- Every command must exit zero.
- Every bundle must contain its native server, static index, build manifest,
  and the declared browser artifacts.
- No failed cell may be excluded or rerun.
- The candidate is accepted only if all existing tests pass, every benchmark
  cell passes, and the median of the three fixture medians improves by at least
  20% against the frozen baseline.
- Median native-server or WASM size may not increase by more than 25% without a
  separately justified product decision.

The benchmark measures local cold build latency, not server throughput,
browser runtime speed, application quality, or universal language superiority.
Any accepted change must be committed before a new independent full-stack
corpus is designed.

## Frozen v0.5.3 baseline

The 12 measured builds at commit `42c464a` all passed. The fixture medians were
3.543877 seconds for `status_only`, 3.855847 for `browser_score`, and 3.933453
for `typed_post`; the median of those medians was **3.855847 seconds**. Median
native-server sizes were 441,216 bytes for the two GET fixtures and 493,696
bytes for the typed POST fixture. The browser artifacts were 1,103 and 1,442
bytes.

Canonical baseline: `web_build_latency_001_baseline.json`; SHA-256:
`ba295fc3395491f83dfa5e93ad6ca9fac28407dbfa0f5097ff370817010ee05b`.

## Accepted v0.5.4 candidate

Version 0.5.4 emits ordinary strict Serde trait implementations for records and
enums used only at typed route boundaries. This removes Serde's
syn/quote/proc-macro2 derive stack from the common cold native build. Programs
that explicitly use `from json` or `as json` retain the derive backend.

All 12 candidate cells passed. The fixture medians fell to 2.475271 seconds for
`status_only`, 2.63777 for `browser_score`, and 2.806763 for `typed_post`. The
median of fixture medians improved from 3.855847 to **2.63777 seconds**, a
**31.5904% reduction** that clears the frozen 20% threshold. Each fixture
improved by 28.6438–31.5904%. WASM sizes were unchanged; the largest native
size increase was 0.0036%. The complete suite passed 585/585 tests, including
strict unknown, duplicate, missing, wrong-type, optional-field, enum, internal
JSON, native server, and browser/WASM paths.

Canonical candidate: `web_build_latency_001_candidate.json`; SHA-256:
`2fca8256642b5e6e06f72b61c4b7f839b18fc13c657c6781015a4b507c726848`.
Canonical analysis: `web_build_latency_001_analysis.json`; SHA-256:
`380c2309102acf570eebd94140d2106bdacebea87ebbebadf2d0c103fc80ee22`.

The candidate was measured from the exact v0.5.4 product-file hashes recorded
in the analysis; the result's Git field identifies their clean v0.5.3 base
because the accepted product diff had not yet been committed. This local
product result does not alter iteration 042 or predict a future agent outcome.
