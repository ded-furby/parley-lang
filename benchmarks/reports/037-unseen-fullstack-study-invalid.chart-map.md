# Chart map — iteration 037

## Hidden assignment success rate

- Segment: final-artifact correctness evidence.
- Question: which language arms passed all five withheld cases plus the derived
  browser/server agreement check?
- Takeaway: Parley, Python, and TypeScript pass 24/24; Rust passes 22/24 after
  two independent Terra orchard implementations misuse signed
  `saturating_sub` as a clamp to zero.
- Family/type: comparison and ranking / single-series bar.
- Fields: language and hidden success rate; tooltips retain cohort, task-kind,
  first-check, and source-size context.
- Sufficiency: four frozen language categories with 24 sessions each and no
  exclusions.
- Palette: single-root blue with direct values; labels provide non-color
  identity.
- Scale: absolute fractional rate beginning at zero.
- Caveat: valid parent-run hidden judgment; the overall experiment is still
  invalid because the Rust read-only freeze was noncanonical.
- Surface: full-width native artifact chart in the technical report.

## First public check success rate

- Segment: agent-visible feedback reliability.
- Question: did Parley match the best baseline before any repair turn?
- Takeaway: Parley passes 18/24 first checks versus Python 23/24 and
  TypeScript/Rust 24/24; all six Parley misses are orchard build attempts.
- Family/type: comparison and ranking / single-series bar.
- Fields: language, first-check success rate, and repair-turn count.
- Sufficiency: four language rates over every frozen session; the parent-owned
  transport made the metric interpretable in 037.
- Palette: single-root blue with direct values.
- Scale: absolute fractional rate beginning at zero.
- Caveat: one Python cell voluntarily ran a second passing check after its
  first passing attempt, so aggregate repair turns (eight) exceed first-check
  failures (seven).
- Surface: full-width native artifact chart.

## Median complete session tokens

- Segment: frozen token-efficiency gate.
- Question: did Parley use no more input-plus-output tokens than the cheapest
  baseline overall?
- Takeaway: Parley beats TypeScript and Rust but is 11.88% above Python; the
  gap repeats in both model strata.
- Family/type: comparison and ranking / sorted single-series bar.
- Fields: language and median complete tokens; tooltips retain outcome and
  source-size context.
- Sufficiency: four medians over 24 complete sessions each, including failures.
- Palette: single-root blue with direct values.
- Scale: absolute magnitude beginning at zero; ascending order.
- Caveat: the session metric includes all public checks and repair turns, as
  preregistered.
- Surface: full-width native artifact chart.

## Median fresh-session elapsed time

- Segment: frozen elapsed-efficiency gate.
- Question: did Parley complete no slower than the fastest baseline?
- Takeaway: Parley's 30.799-second median is 28.92% above TypeScript's
  23.890-second median; TypeScript is also fastest in both model strata.
- Family/type: comparison and ranking / sorted single-series bar.
- Fields: language and median elapsed seconds.
- Sufficiency: four medians over 24 sessions each.
- Palette: single-root blue with direct values.
- Scale: absolute magnitude beginning at zero; ascending order.
- Caveat: timing is local to the frozen machine, tools, model configurations,
  and parent-owned checker protocol.
- Surface: full-width native artifact chart.

## Median final editable-source tokens

- Segment: secondary representation-compactness evidence.
- Question: did Parley retain compact application sources despite higher total
  session cost than Python?
- Takeaway: Parley's 552-token median is 40.39% below Python, 34.21% below
  TypeScript, and 59.20% below Rust.
- Family/type: comparison and ranking / sorted single-series bar.
- Fields: language and median final `o200k_base` token count.
- Sufficiency: four medians over 24 final editable-source snapshots.
- Palette: single-root blue with direct values.
- Scale: absolute magnitude beginning at zero; ascending order.
- Caveat: source representation and complete agent effort are distinct
  metrics; this secondary measure does not rescue the failed primary gate.
- Surface: full-width native artifact chart.

No trend chart is used because iteration 037 is a balanced categorical
experiment, not a time series. Exact gate, configuration, language, integrity,
and hidden-failure values remain in tables because audit lookup matters more
than visual shape for those sections.
