# Iteration 020 report notes

- Audience: technical
- Delivery: self-contained HTML from one canonical report artifact
- Question: after the evidence-backed modulo alias, does Parley match the best
  Python/Rust baseline over ten complete size-eight workload replicates?
- Decision-useful answer: no. Five repair-free Parley bundles isolate a clean
  6.13k-token regime only 1.37% above Rust but 5.57% above Python; five other
  bundles repaired, and one clean bundle failed a hidden rotation case.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Session distribution | How variable were tokens/task across ten replicates? | Discrete comparison / grouped bar | replicate, language, tokens_task | Baselines are tight; Parley splits into clean and repaired regimes | Relaxed three-category language palette |
| Reliability | Did Parley match hidden and first-check rates? | Category comparison / bar | language, first_rate / hidden_rate | Parley reached 74/80 first and 79/80 hidden; baselines were 80/80 | Outcome palette per chart |
| Time | Did elapsed time reach the better baseline? | Category comparison / bar | language, median_seconds_task | Parley median 7.55 sec/task missed Python and Rust | Relaxed three-category language palette |
| Task failures | Which task families failed first checks? | Ranked comparison / horizontal bar | task, first_failures | Failures concentrate in dedup, prefix, and one rotation source | Single-root, labels carry identity |
| Repair burden | Which Parley replicates repaired? | Discrete comparison / bar | replicate, repair_turns | Exactly five of ten Parley bundles were repair-free | Single-root |

Exact session totals, clean sensitivity, failure signatures, and hidden
outcomes remain in audit tables. The report rejects redundant `repeat while`
syntax despite recurrence because canonical `while` already covers it.
