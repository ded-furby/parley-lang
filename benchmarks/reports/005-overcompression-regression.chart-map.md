# Iteration 005 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: can a sub-3k injected core reduce clean-run overhead without
  losing Parley's iteration-004 first-pass reliability?
- Decision-useful answer: no; final correctness remained intact, but five of
  six Parley sessions needed repairs and both efficiency metrics regressed.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley trails both baselines | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley has the highest median | Single-root, axis labels carry identity |
| Task sensitivity | Is the regression isolated to one task? | Grouped comparison / bar | task, language, median_total_tokens | Parley trails on all three task cells | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley 1/6; Python and Rust 5/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley seven; Python and Rust one | Single-root, zero baseline |

No uncertainty chart is shown. Two replicates per cell are directional, but
the predeclared pilot gate fails directly and a confidence interval cannot
turn the recorded point result into an acceptance pass.
