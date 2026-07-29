# Versioned agent benchmark reports

These reports are immutable snapshots. Never replace or delete an existing
numbered HTML file; create the next number with its canonical artifact, SQL
transformation, and chart-map notes.

| Version | Compiler | Result | Report |
| --- | --- | --- | --- |
| 001 | Parley 0.3.138 | Correctness tied; Parley missed efficiency parity | [HTML](001-pilot-baseline.html) |
| 002 | Parley 0.3.140 | Pilot-level correctness and efficiency parity reached | [HTML](002-efficiency-parity.html) |

The decision record, input hashes, exact metrics, and next experiment are in
`../EXPERIMENT_LOG.md`. Full per-session JSON remains under
`benchmarks/results/` and is intentionally ignored because it contains large
agent transcripts; each log entry records its SHA-256.
