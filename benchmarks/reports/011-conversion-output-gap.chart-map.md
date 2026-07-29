# Iteration 011 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: do checked numeric conversion and scalar text joining clear the
  remaining task-family failures?
- Decision-useful answer: they cut repairs from nine to five and elapsed time
  nearly in half, but paired missing text-conversion forms kept Parley at 2/6
  first-pass and 1.74× Python's median tokens.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley used 1.74× Python's median tokens | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley remained 28.6% above the faster Rust median | Single-root, axis labels carry identity |
| Task sensitivity | Where do repairs remain? | Grouped comparison / bar | task, language, median_total_tokens | Bracket stayed clean; compact and inventory paired by failure family | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley 2/6; Python 4/6; Rust 6/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley used five; Python two; Rust zero | Single-root, zero baseline |

The detail table includes 100% hidden success and command-protocol compliance
for all languages. No uncertainty chart is shown because two replicates per
cell remain a directional pilot and the supporting reliability gate fails.
