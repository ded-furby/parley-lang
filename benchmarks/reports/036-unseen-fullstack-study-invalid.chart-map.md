# Chart map — iteration 036

## Hidden assignment success rate

- Segment: hidden-correctness evidence.
- Question: which language arms produced applications that passed all five
  withheld cases plus browser/server agreement?
- Takeaway: Parley, TypeScript, and Rust pass 24/24; Python passes 12/24, split
  between 0/12 implementations and 12/12 repairs.
- Family/type: comparison and ranking / single-series bar.
- Fields: language, hidden success rate; tooltip retains session count,
  implementation successes, repair successes, and source size.
- Sufficiency: four frozen language categories with 24 sessions each.
- Palette: single-root blue plus neutral axes; axis labels supply non-color
  identity and no redundant legend is used.
- Scale: absolute fractional rate beginning at zero.
- Caveat: valid parent-run hidden judgment, but the intended agent-visible
  public semantic feedback was blocked.
- Surface: full-width native artifact chart in the portable technical report.

## Median complete session tokens

- Segment: frozen token-efficiency gate.
- Question: did Parley use no more input-plus-output tokens than the cheapest
  baseline overall?
- Takeaway: Parley beats TypeScript and Rust but is 11.93% above Python, so the
  preregistered best-baseline threshold fails.
- Family/type: comparison and ranking / sorted single-series bar.
- Fields: language, median total tokens; tooltip retains cohort and outcome
  context.
- Sufficiency: four language medians over 24 complete sessions each, with no
  exclusions or correctness-conditioned filtering.
- Palette: single-root blue plus neutral axes and direct values.
- Scale: absolute magnitude beginning at zero; ascending order.
- Caveat: sessions include repeated public builds whose loopback runtime checks
  could not execute.
- Surface: full-width native artifact chart.

## Median fresh-session elapsed time

- Segment: frozen elapsed-efficiency gate.
- Question: did Parley complete no slower than the fastest baseline?
- Takeaway: Parley's 38.442-second median is 3.84% above TypeScript's 37.021
  seconds, and the ordering repeats within both model configurations.
- Family/type: comparison and ranking / sorted single-series bar.
- Fields: language, median elapsed seconds; tooltip retains session and outcome
  context.
- Sufficiency: four language medians over 24 sessions each.
- Palette: single-root blue plus neutral axes and direct values.
- Scale: absolute magnitude beginning at zero; ascending order.
- Caveat: this is timing of the failed execution protocol, not clean productive
  work with functioning public feedback.
- Surface: full-width native artifact chart.

## Median final editable-source tokens

- Segment: secondary representation-compactness evidence.
- Question: did Parley retain the application-source compactness observed in
  iteration 035?
- Takeaway: Parley's 501.5-token median is below TypeScript 801, Python 854, and
  Rust 1,252.5, while the primary complete-session token gate still fails.
- Family/type: comparison and ranking / sorted single-series bar.
- Fields: language, median final o200k_base tokens; tooltip retains session and
  task-outcome context.
- Sufficiency: four language medians over 24 final editable source snapshots.
- Palette: single-root blue plus neutral axes and direct values.
- Scale: absolute magnitude beginning at zero; ascending order.
- Caveat: source representation and complete agent effort are distinct metrics.
- Surface: full-width native artifact chart.

No trend chart is used because iteration 036 is a balanced categorical
experiment, not a time series. Exact gate, model-stratified, language, and
integrity values remain in tables because audit lookup matters more than visual
shape for those sections.
