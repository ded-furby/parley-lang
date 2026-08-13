# Full-stack agent study 046 execution freeze

Protocol revision 2 freezes the complete validated execution graph before the
first measured session. The revision-1 protocol commit is
`47448a84b3663ff2aef1d17cf92cca26bc4d7891`; the validated harness commit is
`3f716d448cd5f64f0ce008d03a5a27e24eef1f63` with tree
`4fa77808aeaa2f33f2e35307c0ce0653ba135efe`.

Clean-room validation passed all 16 task/language reference applications and
all 144 named cases. All 16 seeds built, none passed publicly, and all eight
maintenance language/root boundaries were exact. Peak per-cell workspace use
was 161,226,830 bytes, giving 13.320 times headroom inside the frozen 2 GiB
per-worker allowance.

The orchestration smoke passed the protected source/check command path, parent
FIFO transport, exact Python builds, public and hidden HTTP/Chromium execution,
custom-header judgment, and workspace integrity. Most importantly, it proved
that live empty, custom, and duplicate response-header pairs are JSON-native
lists and remain exactly equal after durable persistence. The public broker
attempt also matched its durable JSON record exactly.

The frozen Parley response-web card is 124 `o200k_base` tokens. Its task prompt
is 109 tokens larger than the corresponding Python prompt, versus 298 in
iteration 045. Canonical compact Parley manifests range from 124 to 132 tokens,
below the preregistered 135-token ceiling. These are artifact measurements, not
complete-session performance results.

No task, case, status, header, formula, context byte, model, threshold, metric,
or gate changed during validation. There are zero measured iteration-046
sessions at this freeze. The study must run all 96 cells exactly once and
publish the complete result even if the strict gate fails or execution is
invalid.
