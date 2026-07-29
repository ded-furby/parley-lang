# Iteration 007 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: does exact-check-only protocol v2 close Parley's efficiency gap?
- Decision-useful answer: it removes most of the gap and all runs comply, but
  Parley remains 5–7% above the token baselines and 4% above the fastest time.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley is within 6.7% but still highest | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley beats Python but trails Rust | Single-root, axis labels carry identity |
| Task sensitivity | Where did repair tails occur? | Grouped comparison / bar | task, language, median_total_tokens | One Parley bracket run dominates that cell | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley 5/6, Python 4/6, Rust 6/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley three, Python two, Rust zero | Single-root, zero baseline |

The detail table includes command-protocol compliance; all languages are at
100%. No uncertainty chart is shown because two replicates per cell remain a
directional pilot and the point acceptance gate is not met.
