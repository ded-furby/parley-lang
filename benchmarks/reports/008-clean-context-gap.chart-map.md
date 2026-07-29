# Iteration 008 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: after perfect Parley first-pass recovery, does protocol v2 meet
  the strict efficiency gate?
- Decision-useful answer: no; reliability is perfect, but the clean Parley
  cluster remains 6–7% above token baselines and 7–16% above time baselines.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley is 6.9% above Python | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley has the highest median | Single-root, axis labels carry identity |
| Task sensitivity | Is the clean gap consistent by task? | Grouped comparison / bar | task, language, median_total_tokens | Parley is ~2.8k–3.1k above the lower baseline per cell | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley and Rust 6/6; Python 4/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley and Rust zero; Python two | Single-root, zero baseline |

The detail table includes 100% command-protocol compliance for all languages.
No uncertainty chart is shown because two replicates per cell remain a
directional pilot and the strict point gate is not met.
