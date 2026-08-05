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
| 020 | Parley 0.3.153 | The size-eight confirmation reached 79/80 hidden tasks but failed all four strict parity conditions | [HTML](020-size-eight-confirmation-failed.html) |
| 021 | Parley 0.3.154 | New-corpus correctness tied at 72/72; first-check repairs left agent effort at 2.06× Python | [HTML](021-new-broad-corpus-parity-failed.html) |
| 022 | Parley 0.3.155 | Independent-model correctness tied, but Parley used 3.20× Python's token effort and passed only 39/72 first checks | [HTML](022-independent-model-parity-failed.html) |
| 023 | Parley 0.3.155 | Application correctness and exact file output tied; repairs left agent effort above 2× both baselines | [HTML](023-application-corpus-parity-failed.html) |
| 024 | Parley 0.3.155 | Seeded maintenance correctness tied; one repair in every Parley session left effort at 1.84× Python | [HTML](024-seeded-maintenance-parity-failed.html) |
| 025 | Parley 0.3.155 | Multi-file maintenance reached perfect first-check reliability and came within 1.28% of Rust's token effort | [HTML](025-repository-maintenance-near-parity.html) |
| 026 | Parley 0.3.155 | Eight-repository expansion preserved Rust-level efficiency but missed Python and the strict gate | [HTML](026-eight-repository-expansion-failed.html) |
| 027 | Parley 0.3.155 | Sixteen-repository scaling regressed through context growth and did not justify language tuning | [HTML](027-sixteen-repository-scale-regression.html) |
| 028 | Parley 0.3.155 | Project diagnosis restored near parity with exact root-cause evidence | [HTML](028-project-diagnosis-near-parity.html) |
| 029 | Parley 0.3.155 | Historically grounded diagnosis reproduced Rust parity while still trailing Python | [HTML](029-historical-diagnosis-rust-parity.html) |
| 030 | Parley 0.3.155 | Ninety sessions isolated a real amortization crossover near six diagnosis tasks | [HTML](030-ninety-session-scaling-mechanism.html) |
| 031 | Parley 0.3.155 | Deeper projects passed the four-part efficiency/reliability gate; exact-root quality was 23/24 | [HTML](031-deeper-project-efficiency-win.html) |
| 032 | Parley 0.3.158 | Independent confirmation preserved perfect reliability but missed strict token/time parity | [HTML](032-independent-confirmation-strict-parity-not-met.html) |
| 033 | Parley 0.3.159 | Adaptive agent-data packing was lossless but missed the frozen 5% aggregate gate | [HTML](033-adaptive-agent-data-gate-not-met.html) |
| 034 | Parley 0.3.159 | Paired 90-session confirmation saved tokens in all 45 pairs without accuracy loss | [HTML](034-verified-toon-context-efficiency-win.html) |
| 035 | Parley 0.4.0 | Release Radar passed 60/60 cross-language checks and used 40.37% fewer authored tokens than the nearest baseline | [HTML](035-release-radar-fullstack-compactness-proof.html) |

The decision record, input hashes, exact metrics, and next experiment are in
`../EXPERIMENT_LOG.md`. Full per-session JSON remains under
`benchmarks/results/`; completed numbered studies force-add their exact raw
JSON snapshots so later reports can be reproduced, and each log entry records
the snapshot SHA-256.
