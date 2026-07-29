# Iteration 004 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: did Parley 0.3.141 remove the iteration-003 first-pass failures
  and clear the strict efficiency gate in a new two-replicate pilot?
- Decision-useful answer: all first checks and hidden checks passed, but the
  token and elapsed medians still miss Python.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley beats Rust but trails Python | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Python leads; Parley and Rust are close | Single-root, axis labels carry identity |
| Task sensitivity | How does the pilot vary by task? | Grouped comparison / bar | task, language, median_total_tokens | Parley leads compact ranges but not every task | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | All three languages passed 6/6 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | All three languages used zero | Single-root, zero baseline |

No uncertainty chart is shown. Two replicates per task-language cell are
directional only, and the report does not make an inferential or universal
language-ranking claim.
