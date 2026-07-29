# Iteration 014 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: can a 343-character general quickstart retain reliability while
  closing the fixed-context gap?
- Decision-useful answer: no. Hidden correctness eventually survived, but
  Parley fell to 0/6 first-pass, 69 repair turns, and 10.37× Python's tokens.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | How severe was the compression regression? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley used 10.37× Python's median tokens | Single-root, axis labels carry identity |
| Aggregate efficiency | How much wall time did repair loops add? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley took 8.73× Python's median time | Single-root, axis labels carry identity |
| Task sensitivity | Did the regression affect every task? | Grouped comparison / bar | task, language, median_total_tokens | All three Parley task families regressed | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley 0/6; Python 5/6; Rust 6/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley used 69; Python one; Rust zero | Single-root, zero baseline |

The detail table preserves 100% eventual hidden success and protocol compliance
for all languages. The cross-task replication makes rollback decisive; no
additional instruction-compression pilot is warranted.
