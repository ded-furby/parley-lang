# Web build backend in v0.5.7

Parley web builds select the smallest Rust build backend that preserves the
program's dependency contract.

Generated server and browser code with no external Rust dependencies compiles
directly with `rustc`. The direct commands preserve the corresponding Cargo
profile's overflow checks, release optimization and symbol stripping, plus the
browser profile's size optimization, link-time optimization, and aborting panic
behavior. Direct `rustc` JSON diagnostics retain Parley's generated-to-source
line mapping.

A program that uses an explicit language-level `from json` or `as json`
expression still builds its native server through Cargo because it depends on
the pinned Serde backend. Backend selection is automatic. It does not change
the checked manifest, native HTTP behavior, generated browser API, or bundle
layout.

This is a local build-path optimization. Its preregistered evidence and scope
are recorded in [`WEB_BUILD_BACKEND_003.md`](../benchmarks/WEB_BUILD_BACKEND_003.md).
It is not a server-throughput result or evidence of universal language
superiority.
