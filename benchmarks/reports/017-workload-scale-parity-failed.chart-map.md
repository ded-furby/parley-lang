# Iteration 017 report notes

- Audience: technical
- Delivery: self-contained HTML from one canonical report artifact
- Question: does Parley's fixed fresh-session instruction cost amortize enough
  to match or beat Python and Rust when a session solves more unrelated tasks?
- Decision-useful answer: prompt characters per task amortized almost exactly
  as designed, but both size-eight Parley sessions incurred repairs and failed
  strict parity. A reserved-identifier failure recurred across unrelated tasks
  and supports one general compiler change; the rotation-only `modulo` failure
  does not.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Efficiency curve | How did tokens per task change with bundle size? | Discrete comparison / grouped bar | bundle_label, language, median_tokens_task | Clean scales amortized, but size-eight Parley repair loops reversed the curve | Relaxed three-category language palette |
| Cold-start mechanism | Did fixed prompt overhead amortize? | Discrete comparison / grouped bar | bundle_label, language, median_prompt_chars_task | Parley prompt gap to Python fell from 1,681 to 212 chars/task | Relaxed three-category language palette |
| Reliability | How often did tasks pass the first bundle check? | Discrete comparison / grouped bar | bundle_label, language, first_public_task_success_rate | Parley fell to 11/16 at size eight; both baselines stayed perfect | Relaxed three-category language palette |
| Time efficiency | Did elapsed time per task reach parity? | Discrete comparison / grouped bar | bundle_label, language, median_seconds_task | Parley missed Python at every size and missed both baselines at size eight | Relaxed three-category language palette |
| Failure concentration | Which Parley tasks failed first checks? | Ranked comparison / horizontal bar | task, first_failures | Rotation failed 6/8; three additional task families exposed the reserved `position` issue | Single-root, axis labels carry identity |

Grouped bars are repeated because all four scale sections compare the same
four discrete workload sizes across the same three languages; a four-point
line would imply a stronger continuous trend than the design supports. Exact
session counts, denominators, session totals, and weighted values remain in
the audit table and source data.
