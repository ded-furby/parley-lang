# Cold web-build latency study 002

This product benchmark is frozen after iteration 043's complete elapsed
attribution and before any v0.5.5 compiler, runtime, dependency, or build-cache
change. It does not reuse an iteration-043 task, formula, route, field,
fixture, model output, or workspace.

## Frozen population

Four deterministic Parley projects exercise new build surfaces:

1. `depot_overview`: a typed GET route with an enum and optional response
   field, without a browser export.
2. `orchard_batch`: a typed POST route plus a scalar browser/WASM export.
3. `weather_dispatch`: combined typed GET and POST routes plus a scalar
   browser/WASM export, matching the broad product shape implicated by 043
   without reusing its semantics.
4. `explicit_json_control`: a typed POST route whose handler also uses an
   explicit Parley `as json` expression, retaining the derive-backed path as a
   regression control rather than a primary optimization target.

The exact fixture hashes are:

- `depot_overview`:
  `88620befb8e6070919c7f49403e59c082f605305605d82dd864be3211a4e43ae`
- `orchard_batch`:
  `933d950cb7b24ff426c5cbd2eadb51bb30962142eb3f9792f3ef6eafcc12b345`
- `weather_dispatch`:
  `9b462bda84cfee3f655e1bb6e650e7281abc045f27a67a19be7483881eddbf9c`
- `explicit_json_control`:
  `480a72e05ecea8a15f94a680c733b46acac9863de9ed502e901eb5db6558ff10`

## Measurement protocol

Every measured cell starts in a new temporary directory with no
`.parley-build` target. Installed dependency sources, the Rust toolchain, and
ordinary process/filesystem caches may remain warm, matching the prepared-
toolchain rule used by the full-stack studies. One complete
`weather_dispatch` build is an unmeasured process and OS warmup. The benchmark
then runs four sequential replicates per fixture, timing the complete
`parley web build` command from CLI startup through checking, Rust generation,
native/WASM compilation, and bundle copying.

Before each timed build, `parley web check --json` must pass. Every command,
required native/static/browser artifact, and fixture hash is retained in the
result. No failed or slow cell may be excluded or rerun. The baseline must be
measured from this committed protocol before product implementation begins.

## Preregistered acceptance gate

A v0.5.5 candidate is accepted only when all of the following hold:

- The complete existing test suite passes.
- All 16 frozen candidate cells pass without exclusion or rerun.
- The median of the three primary fixture medians improves by at least 20%
  against the frozen v0.5.4 baseline.
- No individual fixture median, including `explicit_json_control`, regresses
  by more than 5%.
- Median native-server or WASM size does not increase by more than 25% without
  a separately documented product decision.
- Strict typed-route JSON behavior, explicit core JSON expressions, native
  serving, and browser/WASM behavior retain dedicated regression coverage.

The benchmark measures local fresh-target web-build latency only. It does not
measure server throughput, browser runtime speed, application quality,
ecosystem breadth, or universal language superiority. An accepted change may
inform a later successor study only after the product and its evidence are
committed and a new agent corpus is independently frozen.

Next: commit this protocol and harness, measure and publish the v0.5.4 baseline
unchanged, then diagnose or implement only generic mechanisms outside 043.

## Frozen v0.5.4 baseline

The 16 measured builds at protocol commit `3772eaa` all passed. The primary
fixture medians were 2.512234 seconds for `depot_overview`, 2.725720 for
`orchard_batch`, and 2.739210 for `weather_dispatch`; their preregistered median
was **2.725720 seconds**. The derive-backed `explicit_json_control` median was
3.869316 seconds. Median native-server sizes ranged from 441,232 to 510,384
bytes, while the two WASM artifacts were 1,417 and 1,436 bytes.

Canonical baseline: `web_build_latency_002_baseline.json`; SHA-256:
`b6c951d84f1754f0d7fa640379accbdf1e2dccf2a3af6c333a354d0080e8f62b`.
This result fixes the candidate's 20% target at **2.180576 seconds or lower**
for the median of primary fixture medians, in addition to the per-fixture
regression, correctness, and size gates above.

## Accepted v0.5.5 candidate

Version 0.5.5 generates a strict standard-library JSON parser, encoder, and
typed codecs for programs that use JSON only at web route boundaries. Their
native Cargo project therefore has no third-party dependency graph. Programs
that explicitly use Parley `from json` or `as json` expressions retain the
existing Serde derive backend unchanged.

All 16 candidate cells passed. The primary fixture medians fell to 0.621875
seconds for `depot_overview`, 0.802735 for `orchard_batch`, and 0.826261 for
`weather_dispatch`. Their median improved from 2.725720 to **0.802735
seconds**, a **70.5496% reduction** that clears the frozen 20% threshold. The
derive-backed control also improved 5.5866%, so no fixture regressed. Native
servers became 3.2321–14.0639% smaller and WASM sizes were unchanged.

The complete suite passed 609/609 tests. Dedicated native execution covers
strict unknown, duplicate, missing, wrong-type, optional, enum, nested record,
list, text-keyed map, decimal, Unicode, escape, surrogate, malformed-number,
and trailing-input behavior. The previous v0.5.4 analysis remains
byte-for-byte reproducible after the product advanced.

Canonical candidate: `web_build_latency_002_candidate.json`; SHA-256:
`25efbcc80906060c3403c0e00852ff43ff8f7c0dcd4440c672613dbff9fdb9f7`.
Canonical analysis: `web_build_latency_002_analysis.json`; SHA-256:
`fc00677316db8969dee86460899fb8d84ad0e5fb4cda9fafe3275305f2c19c40`.

This accepts a generic local build-path improvement. It does not alter 043,
predict an agent-study result, or establish universal language superiority.
The v0.5.5 product and evidence must be committed before any successor agent
task population is selected.
