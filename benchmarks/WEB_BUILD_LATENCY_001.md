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
