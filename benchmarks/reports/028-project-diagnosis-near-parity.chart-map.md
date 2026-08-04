# Iteration 028 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does Parley match Python and Rust when agents diagnose
  multi-file regressions from read-only project evidence?
- Decision-useful answer: all languages are perfectly first-check and hidden
  correct; Parley nearly matches Rust but remains above Python.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Tokens | How close is reported agent effort? | Category comparison / bar | language, median_tokens_task | Parley is 1.48% above Rust and 4.38% above Python | Relaxed three-category language palette |
| Sessions | Is the aggregate robust? | Discrete comparison / grouped bar | replicate, language, tokens_task | Every language forms a tight repair-free cluster | Relaxed three-category language palette |
| Elapsed | Did Parley match wall-clock time? | Category comparison / bar | language, median_seconds_task | Parley is 0.85% faster than Rust | Relaxed three-category language palette |
| Source size | How compact is editable source? | Grouped comparison / bar | language, stage, rough_tokens_task | Parley final source is 40.74% shorter than Rust | Hard two-root stage palette |
| Edit size | How large were regression repairs? | Category comparison / bar | language, edit_tokens_task | Every assignment changes one file | Relaxed three-category language palette |

Reliability stays in exact metrics/tables. Equal read-only context, command
order, root-cause location, and compensating fixes remain tables and prose.
