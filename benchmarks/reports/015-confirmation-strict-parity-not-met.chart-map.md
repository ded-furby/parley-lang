# Iteration 015 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: does the frozen proven Parley configuration satisfy the
  predeclared gates at 10 replicates per task-language cell?
- Decision-useful answer: correctness held across all 90 sessions and Parley
  beat Python on first-pass reliability, but strict token, elapsed, and
  best-baseline first-pass parity were not met.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley was 4.13% above Python | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley was 15.32% above Python but 0.36% below Rust | Single-root, axis labels carry identity |
| Task sensitivity | Does aggregate efficiency hold across tasks? | Grouped comparison / bar | task, language, median_total_tokens | Parley led Python on bracket but trailed the best baseline in every task | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley 25/30; Python 23/30; Rust 29/30 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley six; Python seven; Rust one | Single-root, zero baseline |

The table reports 30 fresh sessions per language and ten replicates per cell.
This is confirmation evidence for the declared three-task matrix, not a claim
about all programming work; the next study should broaden the task corpus.
