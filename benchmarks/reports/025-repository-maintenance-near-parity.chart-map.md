# Iteration 025 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does Parley match Python and Rust when agents inspect and
  change two-file repositories under public and hidden tests?
- Decision-useful answer: all languages are 24/24 hidden and first-check clean.
  Parley misses strict parity only on efficiency: 5.89% above Python and 1.28%
  above Rust in median reported tokens, and 2.90% above Rust in elapsed time.

## Required-structure mapping

Scope and metric definitions appear before visual evidence because the report
contract requires denominators before comparison. Technical summary, findings,
method, limitations/robustness, recommended next step, and further questions
retain the technical-report order otherwise.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Tokens | How close is reported agent effort? | Category comparison / bar | language, median_tokens_task | Parley is 1.28% above Rust and 5.89% above Python | Relaxed three-category language palette |
| Session distribution | Is the near-parity aggregate robust? | Discrete comparison / grouped bar | replicate, language, tokens_task | Four Parley sessions cluster near Rust; two raise the weighted mean | Relaxed three-category language palette |
| Elapsed | Did Parley match wall-clock task time? | Category comparison / bar | language, median_seconds_task | Parley is 2.90% above Rust and 31.37% above Python | Relaxed three-category language palette |
| Source size | How compact are seed and final repositories? | Grouped comparison / bar | language, stage, rough_tokens_task | Parley final source is 39.48% shorter than Rust | Hard two-root stage palette |
| Edit size | How large were cross-file patches? | Category comparison / bar | language, edit_tokens_task | Parley edits are 25.60% smaller than Rust but 23.41% larger than Python | Relaxed three-category language palette |

A reliability chart is omitted because all three values are exactly 100%; the
metric strip and exact table are more honest. Failure charts are omitted
because there are no first-check or hidden failures. Command order, changed-file
scope, and file judgment are exact lookups and remain tables.
