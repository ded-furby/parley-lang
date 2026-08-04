# Iteration 022 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does Parley match the better Python/Rust baseline on the
  frozen broad corpus under an independent model?
- Decision-useful answer: final correctness ties at 72/72 per language, but
  Parley uses 3.20× Python's and 1.80× Rust's median reported tokens per task.
  It passes 39/72 first checks and only the correctness gate condition.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Effort | Did Parley match reported token cost? | Category comparison / bar | language, median_tokens_task | Parley is 3.20× Python and 1.80× Rust | Relaxed three-category language palette |
| Reliability | Did Parley match first-check success? | Category comparison / bar | language, first_rate | Hidden correctness ties; first-check reliability does not | Relaxed three-category language palette |
| Session distribution | Was the aggregate driven by one outlier? | Discrete comparison / grouped bar | replicate, language, tokens_task | Every Parley replicate exceeds Python; five exceed Rust | Relaxed three-category language palette |
| Task failures | Where did Parley repair? | Ranked comparison / horizontal bar | task, first_failures | Failures concentrate in map and optional-accumulator tasks | Single-root bars |
| Failure signatures | Which causes recur independently? | Ranked comparison / horizontal bar | signature, events | `contains key` produces 15 events across three tasks and five sessions | Single-root bars |
| Source size | Is generated Parley source longer than Rust? | Category comparison / bar | language, source_tokens_task | Parley source stays one-third shorter than Rust despite higher agent effort | Relaxed three-category language palette |

The report records the recurring `contains key` phrase as an evidence candidate,
not an accepted language change. This corpus is reused under the preregistered
model split, its post-output stop rule forbids learning ergonomics from it, and
membership already has canonical `key is in map` syntax. `repeat while`, bare
`nothing`, unwrapped input, unparenthesized prefix expressions, decimal list
positions, and one incorrect algorithm are likewise rejected as compiler work.
