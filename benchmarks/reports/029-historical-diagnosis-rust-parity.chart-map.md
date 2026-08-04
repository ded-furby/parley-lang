# Iteration 029 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does a historically grounded size-eight diagnosis corpus
  preserve correctness, root-cause quality, and Python/Rust efficiency parity?
- Decision-useful answer: Parley is perfect and beats Rust on tokens/time, but
  remains above the lower Python baseline.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Tokens | How close is reported agent effort? | Category comparison / bar | language, median_tokens_task | Parley is 0.95% below Rust and 4.65% above Python | Relaxed three-category language palette |
| Sessions | Is the aggregate robust? | Discrete comparison / grouped bar | replicate, language, tokens_task | Every language forms a tight repair-free cluster | Relaxed three-category language palette |
| Elapsed | Did Parley match wall-clock time? | Category comparison / bar | language, median_seconds_task | Parley is 9.14% faster than Rust | Relaxed three-category language palette |
| Source size | How compact is editable source? | Grouped comparison / bar | language, stage, rough_tokens_task | Parley final source is 40.53% shorter than Rust | Hard two-root stage palette |
| Edit size | How large were root repairs? | Category comparison / bar | language, edit_tokens_task | Parley edits are 7.89% smaller than Rust | Relaxed three-category language palette |

Reliability, equal evidence, root-cause location, patch consistency, and
command integrity remain exact metrics/tables rather than redundant charts.
