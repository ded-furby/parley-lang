# Iteration 030 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does balanced workload scaling reveal whether Parley's
  remaining Python gap is fixed session overhead or per-task language cost?
- Decision-useful answer: the dominant gap is fixed, but a small positive
  residual versus Python remains; Parley crosses Rust near size six.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Scaling | How does workload size change effort? | Grouped scale comparison / bar | bundle_size, language, median_tokens_task | All languages amortize fixed context steeply | Relaxed three-language palette |
| Gaps | Does Parley close the absolute gap? | Diverging grouped comparison / bar | bundle_size, baseline, token_gap | Python gap shrinks; Rust crosses below zero at size eight | Hard two-baseline palette |
| Fit | Which fitted component differs? | Grouped component comparison / bar | baseline, component, token_gap | Extra fixed context dominates; residual is +74 vs Python and -288 vs Rust | Hard two-component palette |
| Elapsed | Does time follow token amortization? | Grouped scale comparison / bar | bundle_size, language, median_seconds_task | Parley is between Python and Rust at size eight | Relaxed three-language palette |
| Source | How compact is editable code? | Grouped stage comparison / bar | language, stage, rough_tokens_task | Parley is shorter than Rust and longer than Python | Hard two-stage palette |

Exact reliability, root-cause, action-order, task-balance, fit-coefficient, and
session values remain in metrics/tables. A line chart was intentionally omitted:
four logarithmically spaced scales are clearer as discrete preregistered groups,
and the direct-gap panel preserves the small size-eight differences hidden by
the common steep scale.
