# Iteration 016 report notes

- Audience: technical
- Delivery: self-contained HTML from the canonical report artifact
- Question: how does frozen Parley behave on eight independently declared
  tasks outside the three-task optimization corpus?
- Decision-useful answer: all languages were correct, but Parley retained a
  small aggregate token/time gap and lower first-pass reliability. Seven of
  eight Parley repairs were isolated to one rotation task, which is evidence
  for more general testing rather than a task-specific language change.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate efficiency | Which language used the fewest reported tokens? | Comparison / horizontal bar | language, median_total_tokens; input/output in tooltip | Parley was 3.88% above Python | Single-root, axis labels carry identity |
| Aggregate efficiency | Which language finished fastest? | Comparison / horizontal bar | language, median_elapsed_seconds | Parley was 21.36% above Python | Single-root, axis labels carry identity |
| First-pass reliability | Which language passed the first public check? | Comparison / horizontal bar | language, first_public_check_success_rate | Parley 13/16; Python 15/16; Rust 16/16 | Single-root, exact values in table |
| Task sensitivity | Is the token gap broad or task-local? | Comparison / horizontal bar | task, parley_vs_best_gap | Six tasks clustered near 3–4%; deduplication and rotation were larger | Single-root, ordered task labels |
| Repair concentration | Where did Parley spend repairs? | Comparison / horizontal bar | task, parley_repairs | Rotation used seven of eight Parley repair turns | Single-root, zero baseline |

The wide task table reports first-pass successes, median tokens, and repair
turns for every one of the 24 task-language cells. Hidden success was 2/2 in
all cells. With two replicates per cell, task-level rates are diagnostic and
must not be treated as precise population estimates.
