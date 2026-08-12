# Iteration 036 pre-measurement execution amendment

Status: frozen before measured execution. Zero iteration-036 task cells had been
started when this amendment was made.

The original corpus and harness checkpoints remain preserved in Git:

- corpus freeze: `0d26bb9fdf492846bea6b4edf7f329c967c39571`
- protocol preregistration: `64741b3d1bd85578a89429be401a44d3c859481f`
- first executable harness: `7d96094d43fc5d792e8aff23c8f51aa1909d2570`
- launch-ready documentation: `1720c1d1d7299134394487a0bd9aa5cb7a8776a8`

No task, case, expected value, scaffold semantics, compiler behavior, skill,
web reference, model, reasoning setting, replicate count, metric definition,
threshold, or primary gate changed. The frozen task, case, skill, and web
reference hashes in the protocol are unchanged.

## Why an amendment was required

An execution-integrity audit found objective harness omissions before the
irreversible 96-cell run:

1. The runner accepted an arbitrary `parley` command and did not prove that it
   came from the frozen v0.5.0 product checkpoint.
2. Final integrity covered checker/config files but not visibly read-only
   scaffold files, dependency symlinks, or unexpected added files.
3. Generated Parley build state could survive between public and hidden
   builds.
4. The runner promised o200k source counts and rough edit size but captured
   only final rough source tokens.
5. Exact-root aggregation used every maintenance row rather than the
   preregistered population of hidden-correct maintenance rows.
6. A parent-process interruption could lose completed cells and tempt a rerun.
7. The Codex invocation did not use strict configuration validation or an
   explicit workspace-network denial.

Leaving these omissions in place would weaken provenance, permit undetected
workspace expansion, misreport a preregistered metric, and make the no-rerun
rule fragile.

## Execution-only corrections

Protocol revision 2 therefore freezes these execution controls:

- Build Parley in a clean isolated environment from Git commit
  `02cd809f35dfa9f93468e59cfc8a38d97abb41ee` and tree
  `d36495b9d868ef5ef485c58b30e80a1a06e2328a`.
- Record and revalidate the source archive, extracted tree, installed Parley
  package and site-packages trees, executable, dependency locks/trees,
  runtimes, browser binary, platform, and Codex executable.
- Hash protected and read-only workspace files, verify the TypeScript
  dependency symlink, reject unexpected files, and clear generated Parley
  build state before every build.
- Capture seed and final UTF-8 bytes, lines, rough tokens, o200k_base tokens,
  hashes, changed files, and rough token edit size.
- Compute exact-root rate only among hidden-correct maintenance assignments,
  exactly as the frozen primary gate states.
- Write immutable per-cell start and finish journal records. On resume, a cell
  with a start record but no finish record becomes a preserved interruption
  failure and is never rerun; only cells never started may run.
- Require `--strict-config` and
  `sandbox_workspace_write.network_access=false` for every measured session.
- Refuse a fresh run with an existing output or non-empty journal, require a
  clean committed repository, and invalidate execution integrity if the
  repository or frozen environment changes during the matrix.

These changes affect only whether the already-frozen experiment is executed
and recorded faithfully. They do not make any outcome easier for Parley or a
baseline.

## Pre-measurement validation

Before the execution freeze, both frozen model IDs accepted the exact strict,
network-disabled invocation using an unrelated one-line smoke prompt. No
benchmark source, task, case, scaffold, or expected value was exposed.

The amended clean-room toolchain then passed the complete reference boundary:

- 16/16 language/task reference cells passed;
- 128/128 exact public and hidden HTTP/browser cases passed;
- 16/16 seeded applications built;
- 0/16 seeded applications incorrectly passed their public cases; and
- 8/8 maintenance root-file boundaries matched the preregistration.

The final reference artifact is regenerated after the execution hashes are
committed and before the first measured cell starts.
