# Full-stack agent study 047 attribution

This post-result decomposition preserves the valid 047 result and its failed
token and elapsed-time conditions. It analyzes all eight matched Parley/Python
task/replicate pairs and does not revise the frozen gate.

## Token result

Parley's marginal median was 60,757 complete-session tokens versus Python's
60,551.5, a difference of 205.5 tokens or 0.3394%. Across matched pairs, the
median Parley-minus-Python difference was 384.5 tokens: 142.5 input tokens and
214 output tokens. Parley used fewer total tokens in three pairs and more in
five; the 95% bootstrap interval for the paired median was -88 to +771 tokens,
and the exact two-sided sign-test p-value was 0.726562.

The frozen Parley prompt is exactly 161 `o200k_base` tokens larger than the
Python prompt for every task. Parley used more reasoning-output tokens in all
eight matched pairs and more output tokens in seven. This small pilot therefore
does not isolate syntax, source size, or the 176-token context as a generic
cause of the primary 0.3394% token loss.

## Elapsed result

Parley's marginal elapsed median was 3.4404 seconds (11.4461%) above Python.
The marginal public-check difference was 1.0589 seconds, of which 0.9926
seconds was application build time. In all eight matched pairs, the Parley
public build took longer. The paired complete-session difference had a 4.4578-
second median, a -2.9256 to +12.6811 second bootstrap interval, and a 0.289062
two-sided sign-test p-value. Cells were scheduled separately, so the non-check
component cannot be treated as a controlled compiler effect.

## Redundant-check sensitivity

One Parley implementation cell ran four successful public checks while its
matched Python cell ran one. This produced the extreme +107,620-token and
+93.0058-second pair. Excluding that entire matched pair leaves seven-session
medians of 60,515 tokens for Parley and 60,551 for Python, while Parley remains
0.6557 seconds slower. This is sensitivity analysis only: the cell remains in
the valid frozen result, and the gate remains failed.

## Decision

Preserve v0.5.7 and its compact context. The token gap is too small and the
sample too variable to justify benchmark-specific language or instruction
tuning. The stable roughly one-second public-build difference is a separate
compiler-cost target. The next product work should add independently useful
coverage, followed by a larger disjoint evaluation capable of distinguishing
small token effects from interaction variance.

This analysis cannot attribute all elapsed or token differences causally,
authorize a same-corpus rerun, or establish universal language superiority.

Frozen evidence:

- source raw SHA-256: `f04515b84abfbb2a3fe0477c7d0d5c5de9eba8a6f4de3eba2cf062886e779d28`
- attribution SHA-256: `a9ee9b9961c408cef70ccd6bec6bfa23995abdea5fdf761080988c957f420865`
