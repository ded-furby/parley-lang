# Chart map — iteration 040

## Raw hidden assignment success rate

- Question: what outcome did the frozen runner record for each language arm?
- Takeaway: TypeScript records 24/24; Python and Rust 23/24; Parley 22/24.
- Type: single-series categorical bar over all 24 sessions per language.
- Caveat: four raw misses had no hidden semantic execution because of the host
  disk incident; this is not a semantic failure-rate comparison.

## First public check success rate

- Question: what first-check outcome did the frozen runner retain?
- Takeaway: Parley records 23/24 and TypeScript 24/24; the strict condition is
  false even though one Parley miss was infrastructure-caused.
- Type: single-series categorical bar with an absolute zero baseline.
- Caveat: interrupted and ENOSPC-affected cells remain failures by protocol.

## Median complete session tokens

- Question: did Parley match the cheapest raw complete-session baseline?
- Takeaway: Parley is 4.8113% above Python, while below TypeScript and Rust.
- Type: ascending single-series magnitude bar over 24 rows per language.
- Caveat: two interrupted rows retain zero tokens, and the strict study is
  invalidated; these values are descriptive, not confirmatory.

## Median fresh-session elapsed time

- Question: did Parley match the fastest raw complete-session baseline?
- Takeaway: Parley is 22.1262% above TypeScript.
- Type: ascending single-series magnitude bar over 24 rows per language.
- Caveat: timing is local, includes incident effects, and cannot support a
  valid comparative claim from this run.

## Median final editable-source tokens

- Question: did Parley retain a compact source representation?
- Takeaway: Parley is 24.0636–56.2459% smaller than the three baselines.
- Type: ascending single-series magnitude bar using `o200k_base` counts.
- Caveat: compact source does not substitute for complete agent cost or
  restore the invalidated primary gate.

All plots use direct values and labels, with language providing non-color
identity. The repeated bar family is deliberate: every visual is the same
balanced four-category comparison, while gate, incident, model, and integrity
details remain tables because exact audit lookup matters more than shape.
