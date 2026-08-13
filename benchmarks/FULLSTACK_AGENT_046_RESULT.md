# Full-stack agent study 046 result

## Verdict: valid / strict gate failed

Iteration 046 completed all 96 frozen sessions exactly once. The independent
audit verified 96 unique cell IDs, 96 unique thread IDs, 96 start/finish journal
pairs, 96 cleanup records, and 101 parent-owned public-attempt files. All live
attempt collections equal their durable JSON records; the evidence defect that
invalidated iteration 045 did not recur.

Parley passed execution integrity, correctness, first-check, complete-session
token, and maintainability conditions. It failed the elapsed-time condition, so
the preregistered six-part gate failed overall.

| Language | Hidden assignments | First checks | Median total tokens | Median elapsed | Exact maintenance root |
| --- | ---: | ---: | ---: | ---: | ---: |
| Parley | 24/24 | 24/24 | **61,992.5** | 33.6522s | 12/12 |
| Python | 24/24 | 24/24 | 62,235.5 | **28.8755s** | 6/12 |
| TypeScript | 24/24 | 21/24 | 82,714.0 | 61.8548s | 3/12 |
| Rust | 24/24 | 22/24 | 109,422.5 | 77.7707s | 12/12 |

All languages passed all 24 hidden assignments and all 480 named hidden cases.
Parley and Python passed every first public check. TypeScript repaired three
cells and Rust repaired two; one repair followed a failed build and four
followed semantic response mismatches. No hidden semantic failure occurred.

## Frozen gate

| Condition | Result | Evidence |
| --- | --- | --- |
| Execution integrity | Pass | 96/96 attempt/workspace integrity, 96 cleanups, zero runner errors |
| Correctness | Pass | Parley 24/24 assignments and 120/120 hidden cases; all baselines equal |
| First check | Pass | Parley 24/24 overall and 12/12 within both task kinds |
| Tokens | Pass | Parley has the lowest overall median and beats the best baseline in both model configurations |
| Elapsed | **Fail** | Parley 33.6522s versus Python 28.8755s overall; Terra also loses to Python |
| Maintainability | Pass | Parley 12/12 exact roots, tied with Rust and above Python/TypeScript |

Overall, Parley used 0.3905% fewer median complete session tokens than Python,
45.5948% less elapsed time than TypeScript, and 43.3457% fewer tokens than Rust.
It was 16.5424% slower than Python. By model configuration, Parley used 0.2338%
fewer tokens than Python under Sol and 0.2245% fewer under Terra. Its elapsed
time was 8.1219% lower than Python under Sol but 22.3943% higher under Terra;
the frozen condition required success overall and within every configuration.

## Context optimization observation

The pre-corpus Parley response card fell from 313 to 124 `o200k_base` tokens
(60.3834%), and the measured Parley prompt delta versus Python fell from 298 to
109 tokens (63.4228%). Parley's overall median complete session total was
61,992.5 tokens, compared with 62,296.5 in iteration 045, but the corpora and
measured sessions are disjoint. This is descriptive evidence, not a causal
estimate of the compact card's effect and not permission to revise iteration
045.

## Evidence integrity and resource control

The pre-measurement smoke proved exact live-to-persisted equality for empty,
custom, and duplicate JSON-native response-header pair lists. During measurement
all 96 cells passed attempt-record and workspace-integrity checks. The external
audit reread all 101 attempt files and matched them to raw evidence.

There were 294 exact build commands: 293 succeeded, while one failed public
Rust build was retained and repaired. All 294 immediate protected/read-only hash
checks were stable. All 93 scratch capacity checks passed; 96 workspaces were
cleaned with zero failures, peak per-cell usage was 161,200,764 bytes, and no
workspace bytes remained after cleanup. Repository commit, tree, branch, and
clean status were identical before and after measurement.

## Source and scope

Median final source size was 1,223.5 `o200k_base` tokens for Parley, 1,324.5 for
Python, 1,214.0 for TypeScript, and 1,772.0 for Rust. Source size is secondary;
complete session tokens are the frozen cost metric.

This valid result supports a narrow claim: on these four synthetic response
control plus browser assignments, with these two model configurations and this
toolchain, Parley matched hidden correctness, achieved the lowest overall
median complete-session token count, and tied the best exact-root maintenance
rate, while remaining slower than Python. It does not establish that Parley—or
any language—is universally best. The failed strict gate is final for this
corpus; selective reruns and same-corpus tuning remain forbidden.

Frozen evidence:

- raw SHA-256: `0117effbc633affb6d79d14e8f1b713634ca3c5c263537e1ba2207b7ccaf2d07`
- audit SHA-256: `5251e814218fc7b502e9e05c2fc6a13da6d3cdabe41906a9eb024e1b0e3ccbad`
- measurement commit: `28ecbc95ff787752c9a203803a4403f04f9e086e`
