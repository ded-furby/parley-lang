# Iteration 006 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: does Parley 0.3.143 restore first-pass reliability and clear the
  pilot efficiency gate?
- Decision-useful answer: reliability recovered to 6/6, but efficiency still
  failed while every Parley session performed extra workspace inspection.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley has the highest median | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley has the highest median | Single-root, axis labels carry identity |
| Task sensitivity | Is the gap consistent by task? | Grouped comparison / bar | task, language, median_total_tokens | Parley clusters near 64k across tasks | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley 6/6; Python and Rust 5/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley zero; Python and Rust one | Single-root, zero baseline |

No uncertainty chart is shown. Two replicates per cell are directional, and
the next run changes the prompt protocol to prohibit optional workspace
inspection for all languages.
