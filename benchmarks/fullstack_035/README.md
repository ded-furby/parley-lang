# Release Radar baselines

These are the implementation sources for the frozen comparison in
`../FULLSTACK_035.md`. All four servers expose the same 14 HTTP cases and the
same real-browser flow from `../fullstack_035_cases.json`.

The shared UI remains in `examples/release-radar/public`; the harness points
each server there at runtime. Language-owned browser modules are generated from
Parley/TypeScript, handwritten and counted for Python, and embedded in counted
Rust source while loading Rust WebAssembly.

Run the complete protocol from the repository root after installing the pinned
dependencies:

```bash
FULLSTACK_035_PYTHON=/path/to/benchmark-venv/bin/python \
  /path/to/benchmark-venv/bin/python benchmarks/run_fullstack_035.py \
  --output benchmarks/results/fullstack_035_v0.4.0.json
```

`requirements.lock.txt`, `package-lock.json`, and `Cargo.lock` preserve resolved
dependency evidence. Lockfiles, generated outputs, shared UI, dependencies, and
the harness are excluded by the preregistered authored-source rule.
