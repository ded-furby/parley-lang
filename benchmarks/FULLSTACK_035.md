# Full-stack comparison 035

Iteration 035 asks one deliberately bounded question: how compactly can Parley
v0.4.0 express and ship the verified Release Radar contract compared with
idiomatic Python, TypeScript, and Rust implementations?

The product was frozen first at commit
`e5470b6f844f1586a7aedef814e20c39ce9746c6`. The exact HTTP failures, successful
responses, browser flow, counting rules, tool stacks, repetitions, gates, and
claim boundaries are now frozen in:

- `benchmarks/fullstack_035_protocol.json`
- `benchmarks/fullstack_035_cases.json`

## Why this is separate from the agent benchmark series

Reports 001–034 measured fresh coding-agent sessions. Iteration 035 first measures
the product itself: exact correctness, application-authored source tokens, build
time, startup, sequential local request rate, artifact size, browser execution,
and server/browser rule reuse. Source tokens are a useful, reproducible measure
of how much code an agent must represent, but they are **not** Codex session
tokens. A later unseen-task fresh-session study is required for that stronger
claim.

## Fairness boundary

The same checked-in HTML, CSS, and form JavaScript are served by all four
implementations and excluded from every authored-source count. Language-owned
API code, scoring code, browser adapters, manifests, dependency declarations,
and compiler configuration count. Generated files, lockfiles, dependencies,
runtimes, compiler internals, the harness, and this protocol do not.

Python is allowed a counted JavaScript scoring supplement. TypeScript can share
one TypeScript scoring module between server and browser. Rust and Parley can
compile a shared rule to native code and WebAssembly. Browser technology is
reported, but only identical behavior is a correctness requirement.

## Frozen claim

The strongest possible positive conclusion is “Parley is the smallest fully
correct authored implementation of this Release Radar contract under the frozen
o200k token rule, while reusing one checked scoring definition across native and
browser targets.” It is not “Parley beats every language,” and it is not yet “AI
agents always use fewer tokens with Parley.”

No Parley product or compiler code may change from the frozen commit based on
this comparison. Complete results will be preserved as report 035.
