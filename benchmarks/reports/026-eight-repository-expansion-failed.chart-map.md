# Iteration 026 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does Parley match Python and Rust when eight repositories
  amortize fixed context under the unchanged maintenance protocol?
- Decision-useful answer: Parley beats Rust on median tokens and elapsed time,
  but strict parity fails against Python and on one repaired first-check session.

## Required-structure mapping

Scope and metric definitions precede visual evidence. Technical summary,
findings, method, limitations/robustness, recommended next step, and further
questions retain the technical-report order.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Tokens | How close is reported agent effort? | Category comparison / bar | language, median_tokens_task | Parley is 1.48% below Rust and 6.56% above Python | Relaxed three-category language palette |
| Session distribution | Is the aggregate robust? | Discrete comparison / grouped bar | replicate, language, tokens_task | Five Parley runs cluster; one repair is the outlier | Relaxed three-category language palette |
| Elapsed | Did Parley match wall-clock time? | Category comparison / bar | language, median_seconds_task | Parley is 8.48% faster than Rust, 25.02% slower than Python | Relaxed three-category language palette |
| Source size | How compact are seed and final repositories? | Grouped comparison / bar | language, stage, rough_tokens_task | Parley final source is 38.03% shorter than Rust | Hard two-root stage palette |
| Edit size | How large were cross-file patches? | Category comparison / bar | language, edit_tokens_task | Parley edits are 21.63% smaller than Rust | Relaxed three-category language palette |

Reliability remains a metric/table because the meaningful difference is two
exact failures rather than a distribution. Failure classification, command
order, changed-file scope, and exact-file judgments remain tables.
