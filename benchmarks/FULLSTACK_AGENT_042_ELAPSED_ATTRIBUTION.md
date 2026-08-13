# Iteration 042 elapsed attribution

This post-study analysis uses all 24 matched Parley/Python cells from the
immutable iteration-042 raw result, including all 12 terra-medium pairs and the
repaired Python cell. It is descriptive only: it does not change the frozen
gate, exclude a row, or authorize a 042 rerun.

## The Terra miss is a marginal-median crossing

The registered elapsed rule compares the separate medians for each language.
Terra Parley therefore fails at 27.41515 seconds versus Python's 25.183, an
8.8637% gap. The matched observations are more heterogeneous than that one
comparison suggests:

- Parley was faster in 7 of 12 Terra matched pairs.
- The median paired Parley-minus-Python difference was **−1.3807 seconds**.
- Parley's marginal median is the mean of central observations 27.1342 and
  27.6961; Python's is the mean of 24.6064 and 25.7596.
- Terra implementation medians favored Parley, 27.8661 versus 34.21425
  seconds. Maintenance medians favored Python, 25.4379 versus 24.1174.
- Radio Archive and Bakery Batch task medians favored Parley; Theatre
  Turnaround and Subsea Relay favored Python.

Thus, the failure is real under the frozen rule, but it is not a consistent
Parley loss across every Terra task or matched pair. It arises where the center
of two crossing, mixed-task distributions lands.

## The systematic cost is the public build phase

| Measure | Parley median | Python median | Paired Parley − Python median |
|---|---:|---:|---:|
| Overall elapsed | 28.05485 s | 30.63845 s | −2.3704 s |
| Overall public check | 5.4733 s | 1.5364 s | +3.8709 s |
| Overall build phase | 4.0229 s | 0.0629 s | +3.96095 s |
| Overall agent phase excluding public check | 21.8657 s | 29.1521 s | −6.1922 s |
| Terra elapsed | 27.41515 s | 25.183 s | −1.3807 s paired |
| Terra public check | 5.73085 s | 1.54965 s | +4.0394 s |
| Terra build phase | 4.1778 s | 0.0641 s | +4.1111 s |
| Terra agent phase excluding public check | 20.05115 s | 23.17735 s | −4.8015 s |

The frozen Parley build phase was slower in **24/24 matched pairs**. Its paired
delta ranged from +3.5618 to +5.6935 seconds. The remaining agent phase was
usually faster and Parley already passed the complete-session token gate.
Subtracting observed build time would put the Terra marginal medians at
22.07895 seconds for Parley and 25.11775 for Python, but that subtraction is a
component diagnostic—not an alternate experiment or a gate pass.

## Decision

The next generic target is cold `parley web build` latency under exact,
protected-input builds. Preserve the token-winning v0.5.3 context and avoid
model-specific prompting changes. Profile and regression-test the build path on
non-042 programs, freeze any product change before a successor corpus exists,
and measure it only on a new disjoint population.

Canonical data: `fullstack_agent_042_elapsed_attribution.json`; raw SHA-256:
`13f54a40b75ff55934c62a4e44400b0fbbae713392188979fce1f6c59aa3a889`.
