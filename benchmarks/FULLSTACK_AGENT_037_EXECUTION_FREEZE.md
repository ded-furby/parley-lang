# Iteration 037 pre-measurement execution freeze

Status: frozen before measured execution. Zero iteration-037 task cells have
started.

The preserved checkpoints are:

- checker transport: `c833b5fec002fdbedf6fdf5c3e65361afaf4675a`
- corpus freeze: `b3ddad835758ee077a35ec318322b5149a25b88f`
- protocol preregistration: `6ef336a7cb79b914f4791a266120523ac20bdc38`
- first executable harness: `c28d064a09f5a8cb1d6c8c61c455871ada0a2f21`
- final integrity hardening: `10664d592d2655bd528374c7f77c4d3226b0d1b7`

Protocol revision 2 adds only the exact execution-file hashes and controls
described here. It does not change a task, case, expected value, model,
reasoning setting, replicate, metric, threshold, gate, compiler, skill, web
reference, or language stack version.

## Frozen execution architecture

Each fresh workspace contains task sources, visibly read-only stack context,
one source printer, and a generated checker client. The Codex process runs with
network access disabled. Its `./check` command communicates through two
mode-0600 POSIX FIFOs with a parent broker. The parent builds the candidate,
starts it on an inner loopback port, applies the same numeric-domain guard to
all languages, and exposes a second parent-owned loopback endpoint to public
HTTP and real-Chromium cases. Only bounded public feedback returns through the
FIFO; complete attempt JSON is written atomically outside the agent workspace.

The numeric-domain guard is frozen shared infrastructure. It rejects negative
integer inputs and the timeline task's zero bucket width before proxying all
other traffic byte-for-byte to the candidate service. This is required because
the frozen Parley v0.5.0 typed server validates JSON shape and types but has no
custom status hook for positive-only fields. The guard is identical for all
four stacks and is disclosed as infrastructure behavior, not authored-source
correctness.

After the agent exits, a separate parent evaluation rebuilds the final sources
and executes the five hidden cases. Hidden inputs and expected values never
enter the workspace, prompt, public attempt directory, or feedback transport.

## Integrity and interruption controls

- The runner validates every transitive harness, template, adapter, dependency
  manifest, and lockfile against the protocol's SHA-256 list.
- The exact v0.5.0 source archive, source tree, installed package tree,
  executable, Python environment, TypeScript tree, Rust toolchain/lock,
  Playwright package, Chromium binary, platform, and Codex executable are
  recorded and revalidated.
- Protected and visibly read-only files must remain regular files with exact
  hashes. Editable files must remain regular files. The TypeScript dependency
  symlink has one exact target.
- Added files, symlinks, and directories outside declared generated paths are
  rejected. Both FIFO identities include device, inode, file type, mode, and
  owner; any protocol error invalidates the cell.
- Every successful build attempt must execute exactly the three public HTTP
  cases and one public Chromium case. A cell must execute at least one complete
  public semantic set; build-only feedback cannot satisfy integrity.
- Parent attempt files are compared to the in-memory records when the cell
  ends and again while aggregating a resumed or completed run.
- Each cell has one immutable start record and one immutable finish record. A
  started cell interrupted before its finish record becomes a permanent
  failure. Only never-started cells may execute after resume.
- Fresh execution refuses an existing output, non-empty journal, non-empty
  attempt root, dirty repository, or mismatched provenance. Repository and
  provenance are checked again before the result is written.

## Pre-measurement evidence

Both frozen model strata passed the unrelated constant-42 network-denied
transport smoke before task design. After protocol preregistration:

- 16/16 reference task/language cells built and passed;
- 144/144 named public and hidden HTTP/browser cases passed;
- 16/16 derived HTTP/browser equality checks passed;
- 16/16 seeded applications built;
- 0/16 seeded applications incorrectly passed the public cases;
- 8/8 maintenance task/language pairs changed only their predeclared root set;
- all 16 Rust reference/seed builds preserved the matching 037 lockfile; and
- a non-model end-to-end cell exercised source printing, the FIFO check,
  external attempt persistence, public HTTP/Chromium evaluation, hidden
  rebuilding, and final integrity without showing the corpus to a model.

The canonical reference artifact is regenerated after this revision is
committed so it records the final protocol SHA. The complete repository suite
must pass and the repository must be clean before the first measured cell.

## Measurement command

After the final preflight artifact is committed, run the matrix once:

```bash
python3 benchmarks/run_fullstack_agent_037.py run \
  --parley-command /private/tmp/parley-fullstack-037-parley/bin/parley \
  --provenance /private/tmp/parley-fullstack-037-provenance.json \
  --work-root /private/tmp/parley-fullstack-037-work \
  --journal-root /private/tmp/parley-fullstack-037-journal \
  --attempt-root /private/tmp/parley-fullstack-037-attempts \
  --output benchmarks/results/fullstack_agent_037_raw.json
```

Every frozen cell runs exactly once. There are no task-informed smoke sessions,
selective reruns, exclusions, or same-corpus fixes after measurement begins.
