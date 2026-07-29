# Iteration 002 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: did the compact skill and borrow-safe mutation change bring Parley
  to at least Python/Rust agent-efficiency parity without losing correctness?
- Decision-useful answer: yes at pilot scale; confirm with 10 replicates per
  task-language cell before treating the result as robust.
- Baseline: immutable iteration 001, same task manifest, model, reasoning,
  seed, hidden cases, language matrix, and replicate count.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley has the lowest iteration-002 median | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley has the lowest iteration-002 elapsed median | Single-root, axis labels carry identity |
| Task sensitivity | Does parity hold on every task? | Grouped comparison / bar | task, language, median_total_tokens | Result varies by task; inventory remains a Parley deficit | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley and Rust are 6/6; Python is 4/6 | Single-root, exact rate in tooltip/table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley and Rust used zero; Python used two | Single-root, zero baseline |

No uncertainty chart is included because two replicates per task-language cell
cannot support a meaningful interval estimate. The limitation is stated next
to the task-level finding and in the robustness section. Exact values remain in
the language table and canonical snapshot.
