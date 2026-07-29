# Iteration 012 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: do symmetric text conversion and destination-aware formatting
  restore first-pass reliability and strict efficiency parity?
- Decision-useful answer: first-pass reliability rose from 2/6 to 5/6 and
  tied both baselines, but Parley still used 4.77% more median tokens than
  Python and took 8.78% longer than Rust.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley was within 4.77% of Python's median | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley remained 8.78% above Rust and 24.54% above Python | Single-root, axis labels carry identity |
| Task sensitivity | Where is the remaining repair outlier? | Grouped comparison / bar | task, language, median_total_tokens | Five Parley runs clustered tightly; one compact-ranges run needed two repairs | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | All three languages passed 5/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley and Rust used two; Python used one | Single-root, zero baseline |

The detail table includes 100% hidden success and command-protocol compliance
for all languages. No uncertainty chart is shown because two replicates per
cell remain directional and the strict efficiency gate still fails.
