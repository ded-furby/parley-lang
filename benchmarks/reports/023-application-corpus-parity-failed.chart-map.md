# Iteration 023 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does Parley match Python and Rust on new, richer
  application workflows including exact file output?
- Decision-useful answer: final correctness ties at 48/48 per language, but
  Parley uses 2.16× Python's and 2.04× Rust's median reported tokens per task,
  reaches 33/48 first checks, and passes only the correctness gate condition.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Effort | Did Parley match reported token cost? | Category comparison / bar | language, median_tokens_task | Parley remains above both baselines | Relaxed three-category language palette |
| Reliability | Did Parley match first-check success? | Category comparison / bar | language, first_rate | Hidden correctness ties; first-check reliability does not | Relaxed three-category language palette |
| Session distribution | Was the aggregate driven by one outlier? | Discrete comparison / grouped bar | replicate, language, tokens_task | Every Parley replicate exceeds both baseline medians | Relaxed three-category language palette |
| Task failures | Where did Parley repair? | Ranked comparison / horizontal bar | task, first_failures | File and ticket workflows account for 11/15 failures | Single-root bars |
| Failure signatures | Which causes recur independently? | Ranked comparison / horizontal bar | signature, events | No cause spans unrelated tasks and independent sessions | Single-root bars |
| Source size | Is generated Parley source longer than Rust? | Category comparison / bar | language, source_tokens_task | Parley source is 43.58% shorter than Rust despite higher effort | Relaxed three-category language palette |

The report treats descending-range expectation as a one-task behavior question,
not a syntax mandate. File-task failures are missing rare-feature knowledge
within one family, and the four cross-task join failures all came from one
session. No signature clears both task-family and independent-session gates;
the frozen stop rule therefore admits no compiler or skill change from 023.
