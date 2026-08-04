# Iteration 018 report notes

- Audience: technical
- Delivery: self-contained HTML from one canonical report artifact
- Question: did the one cross-task contextual-identifier change remove the
  iteration-017 failure family and produce strict workload parity?
- Decision-useful answer: the exact `position` failure family disappeared and
  size-eight Parley tokens/task improved 22.94%, but rotation-only `modulo`
  failures kept both size-eight bundles in repair and strict parity still
  failed.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Current scale | What is the 018 token curve? | Discrete comparison / grouped bar | bundle_label, language, median_tokens_task | Clean scales retain a small gap; repaired size eight remains 2.55× Python | Relaxed three-category language palette |
| Replication delta | Did v0.3.152 improve Parley? | Discrete comparison / grouped bar | bundle_label, iteration, median_tokens_task | Size-eight tokens/task fell 22.94%; small-scale medians moved only 1.4–1.5% | Relaxed two-category iteration palette |
| Reliability | Which language passes tasks on the first check? | Discrete comparison / grouped bar | bundle_label, language, first_public_task_success_rate | Parley improved size eight to 13/16; both baselines stayed 16/16 | Relaxed three-category language palette |
| Time | Did elapsed workload cost reach parity? | Discrete comparison / grouped bar | bundle_label, language, median_seconds_task | Size-eight Parley improved to 10.91 sec/task but remained 2.15× Python | Relaxed three-category language palette |
| Failure concentration | Which Parley tasks still fail first checks? | Ranked comparison / horizontal bar | task, first_failures | Five of six failures were rotation; seven tasks were at least 7/8 | Single-root, axis labels carry identity |

Grouped bars are used because sizes 1, 2, 4, and 8 are discrete experimental
conditions, not a continuous time series. Exact session totals, denominators,
weighted token values, clean-session sensitivity, and failure signatures stay
in the audit tables.
