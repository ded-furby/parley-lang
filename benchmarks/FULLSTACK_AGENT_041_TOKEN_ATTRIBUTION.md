# Iteration 041 complete-token attribution

This post-study analysis uses all 24 matched Parley/Python cells from the
immutable iteration-041 raw result. It is descriptive only: it does not change
the frozen gate, exclude the repaired Python cell, or authorize a 041 rerun.

## Observed decomposition

| Measure | Parley median | Python median | Paired Parley − Python median |
|---|---:|---:|---:|
| Complete tokens | 63,565.5 | 60,591 | +3,028.5 |
| Input tokens | 63,057 | 59,807.5 | +3,309 |
| Cached input | 47,104 | 49,152 | +640 |
| Uncached input | 15,634 | 12,198 | +1,998.5 |
| Output tokens | 580.5 | 840 | −254 |
| Reasoning output | 78 | 127 | −44.5 |
| Prompt characters | 7,548 | 3,278 | +4,270 |
| Rough edit tokens | 47 | 138 | −73.5 |

Parley produced fewer output tokens and smaller edits in every one of the 24
pairs. Its complete-token deficit is therefore an input-context deficit, not a
larger generated solution or repair burden.

The frozen renderer adds exactly 4,270 characters and 1,154 `o200k_base`
tokens to every Parley prompt relative to Python. The referenced core+web
context itself is 4,350 bytes / 1,164 tokens. The typical Parley session has
three agent message items around `./sources`, the edit, `./check`, and the final
response, so the same fixed prefix can contribute repeatedly to billed input.

## Counterfactual diagnostic

Subtracting the 1,154-token fixed prompt delta three times from each Parley row
would produce a descriptive median of 60,103.5 tokens, 0.8046% below Python.
Using each row's agent-message count as the repetition proxy produces 59,892,
1.1536% below Python. These are arithmetic scenarios, not measured alternate
outcomes: caching and orchestration accounting are not a randomized context
ablation, and neither number passes the frozen gate.

## Decision

The highest-priority generic target is a scaffold-aware Parley web reference
that preserves total numeric conversion, pure shared logic, smallest-owner
repair, and browser scalar constraints while omitting syntax already printed by
the supplied source scaffold. It must be committed before any successor task
population exists, validated for syntax/coverage, and tested on a new disjoint
population. Iteration 041 remains unchanged and gate-not-met.

Canonical data:
`fullstack_agent_041_token_attribution.json`; raw SHA-256:
`37c27539e9003a7a28bc82b58bdc70fd9f0538a1dd5dc0ab6aa5ff6a6ffff65d`.
