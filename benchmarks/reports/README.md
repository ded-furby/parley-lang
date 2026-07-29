# Versioned agent benchmark reports

These reports are immutable snapshots. Never replace or delete an existing
numbered HTML file; create the next number with its canonical artifact, SQL
transformation, and chart-map notes.

| Version | Compiler | Result | Report |
| --- | --- | --- | --- |
| 001 | Parley 0.3.138 | Correctness tied; Parley missed efficiency parity | [HTML](001-pilot-baseline.html) |
| 002 | Parley 0.3.140 | Pilot-level correctness and efficiency parity reached | [HTML](002-efficiency-parity.html) |
| 003 | Parley 0.3.140 | Ten-replicate run preserved correctness but missed strict Python parity | [HTML](003-confirmation-gap.html) |
| 004 | Parley 0.3.141 | First-pass pilot recovered; clean-run medians still missed Python | [HTML](004-first-pass-pilot.html) |
| 005 | Parley 0.3.142 | Sub-3k core preserved final correctness but regressed first-pass efficiency | [HTML](005-overcompression-regression.html) |
| 006 | Parley 0.3.143 | Reliability recovered; optional workspace exploration kept efficiency below gate | [HTML](006-reliable-exploration-gap.html) |
| 007 | Parley 0.3.143 | Protocol v2 reached near parity; returning-function repair kept gate open | [HTML](007-protocol-v2-near-parity.html) |

The decision record, input hashes, exact metrics, and next experiment are in
`../EXPERIMENT_LOG.md`. Full per-session JSON remains under
`benchmarks/results/` and is intentionally ignored because it contains large
agent transcripts; each log entry records its SHA-256.
