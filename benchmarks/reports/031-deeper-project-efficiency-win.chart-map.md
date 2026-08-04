# Iteration 031 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: do deeper multi-file diagnosis episodes let Parley match or
  beat Python and Rust without language or instruction tuning?
- Decision-useful answer: strict efficiency/reliability passes 4/4, while the
  separate exact-root maintainability condition finishes 23/24.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Tokens | Did Parley beat both baselines? | Category comparison / bar | language, median_tokens_task | Parley is 32.67% below Python and 34.89% below Rust | Relaxed three-language palette |
| Distribution | Does the win survive full session disclosure? | Grouped discrete comparison / bar | replicate, language, tokens_task | Repair frequency creates high-cost baseline clusters | Relaxed three-language palette |
| Elapsed | Did wall time also pass? | Category comparison / bar | language, median_seconds_task | Parley is faster than both baselines | Relaxed three-language palette |
| Reliability | Which language succeeds first? | Category comparison / bar | language, first_rate_percent | Parley is 22/24 versus 20/24 | Relaxed three-language palette |
| Source | Is the win just shorter code? | Grouped stage comparison / bar | language, stage, rough_tokens_task | Parley is longer than Python but shorter than Rust | Hard two-stage palette |

Exact root scope, repairs, task cuts, action protocol, and all session values
remain in metrics and audit tables. Five charts answer distinct decisions; none
duplicates the exact lookup tables.
