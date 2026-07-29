# Iteration 009 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: can a 1,557-character progressive-disclosure core retain the
  iteration-008 reliability result and clear the strict efficiency gate?
- Decision-useful answer: no; correctness survived, but first-pass reliability
  collapsed to 0/6 and 19 Parley repairs drove median effort to 3.77× Python.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley used 3.77× Python's median tokens | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley took 4.52× Python's median time | Single-root, axis labels carry identity |
| Task sensitivity | Does the regression occur across tasks? | Grouped comparison / bar | task, language, median_total_tokens | Every Parley task cell exceeded 111k median tokens | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley 0/6; Python 5/6; Rust 6/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley used 19; Python one; Rust zero | Single-root, zero baseline |

The detail table includes 100% hidden success and command-protocol compliance
for all languages. No uncertainty chart is shown because two replicates per
cell remain a directional pilot and the supporting reliability gate fails.
