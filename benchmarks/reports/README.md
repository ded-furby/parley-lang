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
| 008 | Parley 0.3.144 | Perfect first-pass reliability isolated a 6–7% clean context gap | [HTML](008-clean-context-gap.html) |
| 009 | Parley 0.3.145 | 1.6k core preserved correctness but collapsed first-pass efficiency | [HTML](009-progressive-disclosure-regression.html) |
| 010 | Parley 0.3.146 | Natural aliases recovered bracket first-pass but two task families still repaired | [HTML](010-natural-alias-partial-recovery.html) |
| 011 | Parley 0.3.147 | Repairs fell to five; paired text-conversion/output gaps remained | [HTML](011-conversion-output-gap.html) |
| 012 | Parley 0.3.148 | All languages tied at 5/6 first-pass; strict token and elapsed parity still missed | [HTML](012-near-parity-single-outlier.html) |
| 013 | Parley 0.3.149 | Parley reached 6/6 first-pass; fixed context left a 4.55% token gap | [HTML](013-reliability-restored-context-gap.html) |
| 014 | Parley 0.3.150 | One-shot instruction compression regressed every task family and was rejected | [HTML](014-overcompression-rejected.html) |
| 015 | Parley 0.3.151 | 90-session confirmation preserved correctness but did not meet strict parity | [HTML](015-confirmation-strict-parity-not-met.html) |
| 016 | Parley 0.3.151 | Broad out-of-sample correctness held; a 3.88% token gap and rotation repairs remained | [HTML](016-broad-corpus-diagnostic.html) |
| 017 | Parley 0.3.151 | Cold-start cost amortized, but repaired size-eight bundles missed strict parity | [HTML](017-workload-scale-parity-failed.html) |
| 018 | Parley 0.3.152 | Contextual `position` removed its cross-task failures; rotation repairs still blocked parity | [HTML](018-contextual-identifier-replication-failed.html) |
| 019 | Parley 0.3.152 | Anti-primed `modulo` use recurred across three task families; alias eligibility gate passed | [HTML](019-arithmetic-vocabulary-gate-passed.html) |

The decision record, input hashes, exact metrics, and next experiment are in
`../EXPERIMENT_LOG.md`. Full per-session JSON remains under
`benchmarks/results/`; completed numbered studies force-add their exact raw
JSON snapshots so later reports can be reproduced, and each log entry records
the snapshot SHA-256.
