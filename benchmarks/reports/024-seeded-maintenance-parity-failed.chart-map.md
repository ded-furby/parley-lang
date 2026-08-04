# Iteration 024 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does Parley match Python and Rust when agents maintain
  existing hidden-correct application programs rather than generate from an
  empty file?
- Decision-useful answer: final correctness ties at 24/24 per language, but
  every Parley session repairs; its median effort is 1.84× Python and 1.76×
  Rust, so only the correctness gate passes.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Effort | Did seeded maintenance close reported token cost? | Category comparison / bar | language, median_tokens_task | Parley remains above both baselines | Relaxed three-category language palette |
| Session distribution | Is the aggregate driven by one outlier? | Discrete comparison / grouped bar | replicate, language, tokens_task | Every Parley replicate exceeds every Python/Rust replicate | Relaxed three-category language palette |
| Reliability | Did Parley match first-check success? | Category comparison / bar | language, first_rate | All final results tie; Parley first-check reliability is 70.83% | Relaxed three-category language palette |
| Task failures | Where did Parley repair? | Ranked comparison / horizontal bar | task, first_failures | Invoice division accounts for six of seven failed task checks | Single-root bars |
| Source size | How compact are seed and final programs? | Grouped comparison / bar | language, stage, rough_tokens_task | Parley final source is 41.50% shorter than Rust | Hard two-root stage palette |
| Edit size | How large was the seed-to-final change? | Category comparison / bar | language, edit_tokens_task | Parley edits are smaller than Rust but larger than Python | Relaxed three-category language palette |

Only two failure signatures exist, so a chart would overstate a sparse exact
lookup. The report uses an audit table instead. Whole-number division produced
six errors across six independent sessions but only one invoice task; the
maybe-read error appears once in one file task. Because the sources are reused
from iteration 023, iteration 024 cannot independently support any language
change even if a signature recurs by session.
