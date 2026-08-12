# Chart map — iteration 039

## Hidden assignment success rate

- Question: which language arms passed the complete withheld judgment?
- Takeaway: Parley, Python, and TypeScript pass 24/24; Rust passes 23/24.
- Type: single-series categorical bar over all 24 sessions per language.
- Caveat: final correctness is one of six frozen conditions.

## First public check success rate

- Question: did Parley match the best baseline before any repair?
- Takeaway: Parley passes 21/24 versus 24/24 for each baseline.
- Type: single-series categorical bar with an absolute zero baseline.
- Caveat: all three Parley misses are one model/task shape and later recover.

## Median complete session tokens

- Question: did Parley match the cheapest complete-session baseline?
- Takeaway: Parley is 5.88% above Python, while below TypeScript and Rust.
- Type: ascending single-series magnitude bar over 24 sessions per language.
- Caveat: this measures complete Codex input plus output, not source size.

## Median fresh-session elapsed time

- Question: did Parley match the fastest complete-session baseline?
- Takeaway: Parley is 24.94% above TypeScript.
- Type: ascending single-series magnitude bar over 24 sessions per language.
- Caveat: timing is local to the frozen machine, toolchain, models, and checker.

## Median final editable-source tokens

- Question: did Parley retain a compact source representation?
- Takeaway: Parley is 21.88–51.73% smaller than the three baselines.
- Type: ascending single-series magnitude bar using `o200k_base` counts.
- Caveat: compact output does not substitute for complete agent cost.

All plots use direct values and labels, with language providing non-color identity.
There is no trend chart because this is a balanced categorical experiment, not a
time series. Gate, model, integrity, and failure details remain tables because
precise audit lookup matters more than visual shape for those sections.
