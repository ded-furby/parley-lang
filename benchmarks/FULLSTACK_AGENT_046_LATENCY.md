# Full-stack agent study 046 latency decomposition

## Result

This post-result secondary analysis preserves study 046's valid / strict-gate-
failed verdict. It explains the elapsed observation. It does not revise the frozen gate,
rerun a cell, or make the original comparison causal.

Parley's marginal median complete-session time was 33.6522 seconds versus
Python's 28.8755 seconds, a 4.7767-second or 16.5424% disadvantage. Only
0.8259 seconds of that marginal median difference appeared in parent-recorded
public checks, including a 0.9100-second build difference. Marginal medians of
non-check session time differed by 2.8132 seconds. These component medians do
not add to the elapsed median because each component can have a different
median cell.

## Matched Parley/Python cells

Matching on task, model configuration, and replicate gives 24 descriptive
pairs:

| Measure | Median difference | Mean difference | Range |
| --- | ---: | ---: | ---: |
| Complete session | -0.5204s | +3.2510s | -53.4758s to +69.3897s |
| Public checks | +0.8120s | +0.9360s | -0.2435s to +2.7659s |
| Application builds | +0.9042s | +1.0144s | +0.8160s to +1.8078s |
| Non-check session | -1.0202s | +2.3150s | -54.2759s to +68.3718s |
| Complete-session tokens | -138.5 | -132.5 | -800 to +428 |

Parley was faster in 13 pairs and Python in 11. The deterministic 50,000-draw
bootstrap interval for the paired median elapsed difference is -10.2032 to
+2.3991 seconds; the exact two-sided sign-test p-value is 0.838820. Parley used
no more complete-session tokens in 15 of 24 pairs.

The stable matched build difference identifies a concrete product cost, but the
much wider non-check range means the study cannot attribute the complete-session
elapsed gate failure to compilation alone. The paired sessions shared frozen
task, model configuration, and replicate labels, but were scheduled separately
rather than simultaneously.

## Configuration detail

Under Sol, Parley's marginal non-check median was 29.2608 seconds versus
Python's 32.5506 seconds. Under Terra it was 30.3112 seconds versus 26.0396
seconds. Public-check medians were consistently higher for Parley: 2.3625
versus 1.5169 seconds under Sol and 2.4372 versus 1.6323 seconds under Terra.

This split reinforces the boundary: study 046 demonstrates a local cold-build
cost worth optimizing and substantial service/agent timing variance. It does
not estimate how much a compiler optimization would improve end-to-end agent
latency, and it does not establish universal language superiority.

## Reproduction

Run:

```sh
python3 benchmarks/analyze_fullstack_agent_046_latency.py
```

The analyzer asserts the frozen raw SHA-256 before reading the measurements,
uses seed `460260814` for 50,000 bootstrap draws, and writes
`benchmarks/fullstack_agent_046_latency.json` deterministically.

Frozen inputs and output:

- raw evidence SHA-256: `0117effbc633affb6d79d14e8f1b713634ca3c5c263537e1ba2207b7ccaf2d07`
- latency artifact SHA-256: `d02880e5982248bc82f5a9bec845525bd8bbdee257cef3a369586b08e8f47a04`
