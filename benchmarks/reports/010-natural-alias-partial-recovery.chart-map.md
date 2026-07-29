# Iteration 010 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: do transcript-backed syntax aliases restore first-pass efficiency
  with the 1,371-character executable core?
- Decision-useful answer: partly; bracket reporting reached 2/2 clean runs,
  but task-specific conversion/output mistakes kept aggregate Parley at 2/6
  first-pass and 1.82× Python's median tokens.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley used 1.82× Python's median tokens | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley took 2.54× Python's median time | Single-root, axis labels carry identity |
| Task sensitivity | Where did aliases work? | Grouped comparison / bar | task, language, median_total_tokens | Bracket reached a clean 44.9k; inventory remained 157.6k | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley 2/6; Python 5/6; Rust 6/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley used nine; Python one; Rust zero | Single-root, zero baseline |

The detail table includes 100% hidden success and command-protocol compliance
for all languages. No uncertainty chart is shown because two replicates per
cell remain a directional pilot and the supporting reliability gate fails.
