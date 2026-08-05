# Chart map — iteration 035

## Application-authored tokens by language

- Section: authored-source compactness.
- Question: which fully correct implementation has the smallest author-owned
  application surface?
- Takeaway: Parley uses 684 o200k tokens, 40.37% below the nearest baseline.
- Family/type: comparison and ranking / single-series bar.
- Fields: language, o200k tokens; tooltips retain cl100k, bytes, lines, and
  correctness.
- Sufficiency: four deliberately important, directly labeled language arms.
- Palette: single-root sequential blue plus neutral scaffolding; category labels
  provide the non-color distinction.
- Scale: absolute magnitude starting at zero; sorted ascending.
- Surface: full-width native artifact chart in the portable technical report.

## Sequential local request rate by language

- Section: descriptive runtime evidence.
- Question: does the compact generated Parley server remain locally competitive
  on the frozen typed route?
- Takeaway: Parley trails Rust by 5.87% and exceeds TypeScript/Python in this one
  sequential localhost test.
- Family/type: comparison and ranking / single-series bar.
- Fields: language, median requests/second; tooltips retain five-round minimum,
  maximum, and median startup.
- Sufficiency: four directly labeled language medians, each derived from five
  rounds of 500 measured requests after 25 warmups.
- Palette: single-root sequential blue plus neutral scaffolding; direct language
  labels preserve grayscale readability.
- Scale: absolute magnitude starting at zero; sorted descending.
- Surface: full-width native artifact chart with an adjacent limitation paragraph
  and exact audit table.

No trend line is used: five rounds measure spread and rotation, not a meaningful
time series. Exact build/startup/load ranges and artifact sizes remain in the
table because a mixed-unit chart would obscure rather than clarify them.
