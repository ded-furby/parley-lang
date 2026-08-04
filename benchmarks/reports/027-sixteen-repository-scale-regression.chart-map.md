# Iteration 027 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does a second independent expansion preserve Rust parity
  and close the Python gap at size sixteen?
- Decision-useful answer: reliability remains perfect and Parley stays faster
  than Rust, but token effort regresses above both baselines.

## Required-structure mapping

Scope and metric definitions precede visual evidence. Technical summary,
findings, method, limitations/robustness, recommended next step, and further
questions retain the technical-report order.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Tokens | How close is reported agent effort? | Category comparison / bar | language, median_tokens_task | Parley is 35.84% above Rust and 52.10% above Python | Relaxed three-category language palette |
| Session distribution | Is the aggregate robust? | Discrete comparison / grouped bar | replicate, language, tokens_task | Parley splits by one versus two edit actions | Relaxed three-category language palette |
| Elapsed | Did Parley match wall-clock time? | Category comparison / bar | language, median_seconds_task | Parley is 6.72% faster than Rust, 37.22% slower than Python | Relaxed three-category language palette |
| Source size | How compact are seed and final repositories? | Grouped comparison / bar | language, stage, rough_tokens_task | Parley final source is 39.38% shorter than Rust | Hard two-root stage palette |
| Edit size | How large were maintenance patches? | Category comparison / bar | language, edit_tokens_task | Parley edits are 21.39% smaller than Rust | Relaxed three-category language palette |

Reliability stays in metrics/tables because differences are exact counts.
Failure classification, command order, changed-file scope, and exact-file
judgments remain tables.
