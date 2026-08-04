# Iteration 021 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does Parley match the better Python/Rust baseline on a
  twelve-task corpus with zero overlap with earlier benchmark tasks?
- Decision-useful answer: correctness ties at 72/72, but Parley uses 2.06×
  Python's reported tokens and passes only 51/72 first checks. Ten failures
  across five unrelated tasks reject ordinary identifier `number`.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Effort | Did Parley match reported token cost? | Category comparison / bar | language, median_tokens_task | Parley is 2.06× Python and 1.94× Rust | Relaxed three-category language palette |
| Reliability | Did Parley match first-check success? | Category comparison / bar | language, first_rate | Hidden correctness ties; first-check reliability does not | Relaxed three-category language palette |
| Session distribution | Was the result driven by one outlier? | Discrete comparison / grouped bar | replicate, language, tokens_task | Every Parley replicate is above both baselines | Relaxed three-category language palette |
| Task failures | Where did Parley repair? | Ranked comparison / horizontal bar | task, first_failures | Failures affect seven tasks and concentrate in sorted unique numbers | Single-root bars |
| Failure signatures | Which causes cross task boundaries? | Ranked comparison / horizontal bar | signature, events | Reserved `number` produces 10 events across five tasks | Single-root bars |
| Source size | Is generated Parley source longer than Rust? | Category comparison / bar | language, source_tokens_task | Parley source is much shorter than Rust despite higher agent effort | Relaxed three-category language palette |

The report treats `number` as eligible for contextual-identifier review because
the signal crosses five unrelated tasks and the word is generally useful. It
rejects postfix `sorted`, `repeat while`, insert phrasing, and multiword
function declarations as redundant or insufficiently evidenced.
