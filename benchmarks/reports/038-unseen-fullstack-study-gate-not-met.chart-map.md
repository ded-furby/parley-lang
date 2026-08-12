# Chart map — iteration 038

## Hidden assignment success rate

- Segment: final-artifact correctness evidence.
- Question: which language arms passed all five withheld cases plus the derived
  browser/server agreement check?
- Takeaway: all four language arms pass 24/24, yielding 96/96 hidden-correct
  assignments after the frozen public-feedback workflow.
- Family/type: comparison and ranking / single-series bar.
- Fields: language and hidden success rate; tooltips retain cohort, first-check,
  token, time, and final-source context.
- Sufficiency: four frozen language categories with 24 sessions each and no
  exclusions.
- Palette: single-root blue with direct values; labels provide non-color
  identity.
- Scale: absolute fractional rate beginning at zero.
- Caveat: correctness is one of six frozen conditions and cannot establish the
  strict claim by itself.
- Surface: full-width native artifact chart in the stakeholder report.

## First public check success rate

- Segment: first-pass implementation reliability.
- Question: did Parley match the best baseline before any repair turn?
- Takeaway: Parley passes 18/24 first checks while every baseline passes 24/24;
  all six misses are archive implementation build failures.
- Family/type: comparison and ranking / single-series bar.
- Fields: language, first-check success rate, and repair-turn count.
- Sufficiency: four language rates over every frozen session.
- Palette: single-root blue with direct values.
- Scale: absolute fractional rate beginning at zero.
- Caveat: one Python cell voluntarily ran a second passing check, so eight
  repair turns correspond to six first-check failures.
- Surface: full-width native artifact chart.

## Median complete session tokens

- Segment: frozen token-efficiency gate.
- Question: did Parley use no more input-plus-output tokens than the cheapest
  baseline overall?
- Takeaway: Parley beats TypeScript and Rust but is 11.79% above Python; the
  gap repeats in both model strata.
- Family/type: comparison and ranking / sorted single-series bar.
- Fields: language and median complete tokens; tooltips retain correctness,
  first-check, elapsed, and source-size context.
- Sufficiency: four medians over 24 complete sessions each, including repairs.
- Palette: single-root blue with direct values.
- Scale: absolute magnitude beginning at zero; ascending order.
- Caveat: this is complete Codex input plus output, not source text size.
- Surface: full-width native artifact chart.

## Median fresh-session elapsed time

- Segment: frozen elapsed-efficiency gate.
- Question: did Parley complete no slower than the fastest baseline?
- Takeaway: Parley's 29.669-second median is 29.70% above TypeScript's
  22.876-second median; TypeScript is also fastest in both model strata.
- Family/type: comparison and ranking / sorted single-series bar.
- Fields: language and median elapsed seconds.
- Sufficiency: four medians over 24 sessions each.
- Palette: single-root blue with direct values.
- Scale: absolute magnitude beginning at zero; ascending order.
- Caveat: timing is local to the frozen machine, tools, models, and checker.
- Surface: full-width native artifact chart.

## Median final editable-source tokens

- Segment: secondary representation-compactness evidence.
- Question: did Parley retain compact application sources despite higher total
  session cost than Python?
- Takeaway: Parley's 681.5-token median is 32.49% below Python, 17.79% below
  TypeScript, and 49.33% below Rust.
- Family/type: comparison and ranking / sorted single-series bar.
- Fields: language and median final `o200k_base` token count.
- Sufficiency: four medians over 24 final editable-source snapshots.
- Palette: single-root blue with direct values.
- Scale: absolute magnitude beginning at zero; ascending order.
- Caveat: compact representation does not substitute for complete agent cost.
- Surface: full-width native artifact chart.

No trend chart is used because iteration 038 is a balanced categorical
experiment, not a time series. Exact gate, model, language, integrity, and
failure-class values remain in tables because audit lookup matters more than
visual shape for those sections. Repeated bars are intentional: the four
primary comparisons share the same four-category magnitude question and
benefit from consistent scales and reading order.
