# Iteration 003 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: does Parley 0.3.140 maintain correctness and reach the strict
  efficiency gate with 10 replicates per task-language cell?
- Decision-useful answer: correctness holds and Parley beats Rust on median
  tokens, but strict parity fails against Python on tokens and time.
- Frozen design: no compiler, skill, task, model, reasoning, seed, or hidden
  oracle change was made after the first confirmation outcome was observed.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley beats Rust but trails Python | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley is slower than both baselines | Single-root, axis labels carry identity |
| Task sensitivity | Which task breaks aggregate parity? | Grouped comparison / bar | task, language, median_total_tokens | Compact ranges is the Parley bottleneck | Relaxed categorical because language is a real second dimension |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley 23/30, Python 24/30, Rust 30/30 | Single-root, exact values in table |
| Repair burden | Which language used repair turns? | Comparison / horizontal bar | language, repair_turns | Parley used 11, Python six, Rust zero | Single-root, zero baseline |

No uncertainty chart is shown. The predeclared acceptance rule is a direct
point-estimate gate, which iteration 003 misses; a confidence interval cannot
reverse that recorded outcome. The report avoids inferential or universal
language-ranking claims.
