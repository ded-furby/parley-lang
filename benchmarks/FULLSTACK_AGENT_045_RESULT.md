# Full-stack agent study 045 result: invalid gate, complete evidence

Iteration 045 completed all 96 preregistered fresh sessions exactly once. Its
strict result is **invalid / gate failed**, not a language win.

The parent evaluator preserved 96 unique thread results, 99 public attempts,
480 hidden case executions, 96 cleanup records, and all external journals and
attempt files. Every hidden assignment passed semantically. During the live
run, however, all 96 cells failed one frozen evidence-integrity check because
application response-header pairs were Python tuples in memory and JSON arrays
after persistence. The contents match, but strict Python equality does not.
That failure propagated to workspace integrity and exact-root eligibility.
Iteration 045 cannot be selectively rerun or repaired.

## Frozen gate

| Condition | Result | Evidence |
| --- | --- | --- |
| Execution integrity | FAIL | tuple/JSON-array representation mismatch affected 96/96 live records |
| Correctness | PASS | 96/96 hidden assignments and 480/480 hidden cases passed |
| First check | FAIL | Parley 23/24; Python and TypeScript 24/24 |
| Tokens | FAIL | Parley median 62,296.5; Python 61,697.0 |
| Elapsed | FAIL | Parley median 35.8317s; Python 30.71725s |
| Maintainability | FAIL | frozen eligibility requires workspace integrity, which was false |

Only one of six frozen conditions passed, so the overall gate failed.

## Descriptive results

These observations do not rehabilitate the invalid primary gate.

| Language | Hidden | First check | Median tokens | Median elapsed | Structural exact roots* |
| --- | ---: | ---: | ---: | ---: | ---: |
| Parley | 24/24 | 23/24 | 62,296.5 | 35.8317s | 12/12 |
| Python | 24/24 | 24/24 | 61,697.0 | 30.71725s | 1/12 |
| TypeScript | 24/24 | 24/24 | 81,360.5 | 56.1295s | 2/12 |
| Rust | 24/24 | 22/24 | 108,884.0 | 84.41045s | 12/12 |

\* Structural changed-file equality recomputed outside the primary gate. The
frozen exact-root metric remains zero because it requires valid workspace
integrity.

Relative to Python, Parley used 0.9717% more median session tokens and 16.6501%
more median elapsed time. Median final Parley source used 3.6028% fewer
`o200k_base` tokens than Python and 31.2313% fewer than Rust, but 3.0452% more
than TypeScript. Source size is descriptive and never substitutes for complete
session tokens.

The three public repairs were retained: one Parley compile repair and two Rust
semantic repairs. All final hidden outcomes passed. All 293 exact-build hash
checks were stable; 292 commands succeeded and the one failed Parley build was
the recorded first public attempt. Scratch capacity and all 96 evidence-gated
cleanups passed with no retained workspace bytes.

## Next independent phase

The next iteration must use a new corpus. Before that freeze it should:

1. represent header pairs as JSON-native two-item lists at creation time;
2. test live-to-persisted round trips with empty, custom, and duplicate header
   pairs so equality is proven before any measured session;
3. shorten and clarify the Parley response-web card, especially invalid
   compound comparisons such as `is not at least`;
4. target the measured Python gaps in both token cost and elapsed time without
   changing iteration-045 tasks, thresholds, or evidence.

This study covers four synthetic response-control contracts and two model
configurations. It does not establish that any language is universally best.
