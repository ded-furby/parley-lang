# Full-stack agent study 046

## Status

Protocol revision 1 is frozen after the independent product, compact-context,
corpus, and cross-language scaffold commits, and before dependency preparation,
clean-room evidence, any model session, or measurement. Revision 2 must bind
the complete validated execution graph before the first measured session.

## Question

On a new, disjoint response-control corpus, can Parley 0.5.6 match Python,
TypeScript, and Rust on correctness and maintainability while using no more
complete session tokens or elapsed time than the best baseline? The compact
Parley response-web card is 124 `o200k_base` tokens, down from 313 in the
invalid iteration 045; this study does not assume that artifact reduction will
cause a complete-session improvement.

## Frozen design

The matrix contains four tasks, four languages, two model configurations, and
three replicates: 96 fresh sessions. Each assignment has four public and five
hidden cases spanning exact HTTP status, JSON, custom response headers, and
real-Chromium behavior. Two tasks are implementations and two contain
predeclared route-handler defects.

The primary gate is unchanged in shape from iteration 045: execution integrity,
hidden correctness, first-check success, complete input-plus-output tokens,
elapsed time, and exact-root maintenance must all pass. Parley token and elapsed
medians must be no higher than the best baseline, including the frozen
configuration-level comparisons.

The evidence mechanism must represent live response-header pairs as JSON-native
lists before persistence and prove exact live-to-durable equality for empty,
custom, and duplicate pairs. This closes the mechanism class that invalidated
iteration 045 without changing or rerunning its corpus.

## Boundaries

No result can establish that Parley is the best language for every task. A
passing gate supports only this frozen synthetic comparison; a failed or
invalid gate is preserved and published. Selective reruns, same-corpus tuning,
and post-result threshold changes are forbidden.
