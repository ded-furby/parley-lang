# Full-stack agent study 047 result

## Verdict: valid / strict gate failed

Iteration 047 completed all 32 frozen sessions exactly once. The independent
audit verified 32 unique cell IDs, 32 unique thread IDs, 32 start/finish journal
pairs, 32 cleanup records, and 35 parent-owned public-attempt files. All live
attempt collections equal their durable JSON records, and all request-path,
path-parameter, and application-header evidence remained JSON-native.

Parley passed execution integrity, correctness, first-check, and maintainability
conditions. It failed the token and elapsed-time conditions, so the
preregistered six-part gate failed overall.

| Language | Hidden assignments | First checks | Median total tokens | Median elapsed | Exact maintenance root |
| --- | ---: | ---: | ---: | ---: | ---: |
| Parley | 8/8 | 8/8 | 60,757.0 | 33.4983s | **4/4** |
| Python | 8/8 | 8/8 | **60,551.5** | **30.0579s** | 2/4 |
| TypeScript | 8/8 | 8/8 | 77,828.5 | 34.4154s | 0/4 |
| Rust | 8/8 | 8/8 | 101,209.5 | 51.6613s | **4/4** |

All languages passed all eight hidden assignments, all 160 named hidden cases,
and every first public check. One Parley implementation session invoked three
additional checks after its first successful check; all 35 public attempts
passed, so these are counted as three redundant check turns rather than
repaired failures. No public build, public semantic, or hidden semantic failure
occurred.

## Frozen gate

| Condition | Result | Evidence |
| --- | --- | --- |
| Execution integrity | Pass | 32/32 attempt/workspace integrity, 32 cleanups, zero runner errors |
| Correctness | Pass | Parley 8/8 assignments and 40/40 hidden cases; all baselines equal |
| First check | Pass | Parley 8/8 overall and 4/4 within both task kinds; all baselines equal |
| Tokens | **Fail** | Parley median 60,757.0 versus Python 60,551.5 |
| Elapsed | **Fail** | Parley median 33.4983s versus Python 30.0579s |
| Maintainability | Pass | Parley 4/4 exact roots, tied with Rust and above Python/TypeScript |

Parley used 0.3394% more median complete-session tokens and 11.4461% more
elapsed time than Python. It used 21.9348% fewer tokens than TypeScript and
39.9691% fewer than Rust; it was 2.6647% faster than TypeScript and 35.1578%
faster than Rust. The frozen token condition requires Parley to match or beat
the best baseline, so the small Python difference is still a failure rather
than a tie or rounding adjustment.

## Path-routing evidence

The audit reconstructed all 236 HTTP judgments: 140 public and 96 hidden. Every
HTTP record retained the exact request path and JSON-native application-header
pairs. All 140 public HTTP judgments retained path-parameter maps; 64 hidden
judgments retained maps after application routing, while 32 unsafe encoded
paths were rejected before capture. The hidden population exercised 64
percent-encoded paths, including valid once-decoded decimal values and frozen
malformed UTF-8, separator-smuggling, and invalid-escape cases. All judgments
passed without selective reruns.

## Evidence integrity and resource control

There were 99 exact build commands, all successful, and all 99 immediate
protected/read-only hash checks were stable. All 29 renewed scratch-capacity
checks passed; 32 workspaces were cleaned with zero failures, peak per-cell
usage was 160,816,251 bytes, and no workspace bytes remained after cleanup.
Repository commit, tree, branch, and clean status were identical before and
after measurement.

The 176-token Parley context produced a frozen 161-token prompt delta versus
Python. Median final source size was 743.0 `o200k_base` tokens for Parley,
944.5 for Python, 741.5 for TypeScript, and 1,284.0 for Rust. Source size and
prompt deltas are descriptive secondary measures; complete session tokens are
the preregistered cost metric.

## Scope

This valid pilot supports a bounded claim: on these four synthetic typed
path-routing plus browser assignments, with one model configuration and two
replicates, Parley matched perfect hidden and first-check correctness, tied the
best exact-root maintenance rate, and used substantially fewer tokens than
TypeScript and Rust. Python remained slightly lower-token and faster. This does not
establish that Parley—or any language—is universally best. The failed
strict gate is final for this corpus; selective reruns and same-corpus tuning
remain forbidden.

Frozen evidence:

- raw SHA-256: `f04515b84abfbb2a3fe0477c7d0d5c5de9eba8a6f4de3eba2cf062886e779d28`
- audit SHA-256: `0fc04897b4ba3a5e24c35b1b7d6235f1cde5835c005004a1f5a0fb2053182f5a`
- measurement commit: `38151ffe40f7908801a4621ca4d7c00ac9f12d18`
