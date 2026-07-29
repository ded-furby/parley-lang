# Iteration 013 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: do natural helper actions eliminate the last Parley repair while
  preserving correctness and clean-run efficiency?
- Decision-useful answer: yes on reliability—Parley reached 6/6 first-pass
  with zero repairs—but fixed context left median tokens 4.55% above Python
  and elapsed time 10.06% above Rust.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley was within 4.55% of Python's median | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley remained 10.06% above Rust | Single-root, axis labels carry identity |
| Task sensitivity | Is the remaining gap consistent across tasks? | Grouped comparison / bar | task, language, median_total_tokens | Every Parley task was clean; compact and inventory retained small baseline gaps | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley and Rust passed 6/6; Python passed 5/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley and Rust used zero; Python used one | Single-root, zero baseline |

The detail table includes 100% hidden success and command-protocol compliance
for all languages. No uncertainty chart is shown because two replicates per
cell remain directional and strict token/time parity still fails.
