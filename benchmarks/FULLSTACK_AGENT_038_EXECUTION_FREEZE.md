# Iteration 038 pre-measurement execution freeze

Status: frozen before measured execution. Zero iteration-038 task cells have
started.

The preserved checkpoints are:

- exact-build mechanism: `6e50439dd2f47cae4c7bb4d5356bae7cf5dd0937`
- corpus freeze: `b08401e6972822ed211cf33e089b9a59602ea23d`
- protocol preregistration: `26083489bb8319567813642c508e7dc8a5fae122`
- validated executable harness: `0cc6426afe6755896395bbfd251f60d5b60affc9`

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
all languages, and executes public HTTP and real-Chromium cases. Only bounded
public feedback returns through the FIFO; complete attempt JSON is written
atomically outside the agent workspace.

The numeric-domain guard rejects negative integer inputs before proxying all
other traffic byte-for-byte. It is identical for all four stacks and disclosed
as infrastructure behavior, not authored-source correctness. After the agent
exits, a separate parent evaluation rebuilds the final sources and executes the
five hidden cases. Hidden inputs and expected values never enter the workspace,
prompt, public attempt directory, or feedback transport.

## Exact-build and integrity controls

- Before and immediately after each exact build command, the runner snapshots
  every protected and visibly read-only regular file. Any content, size, mode,
  missing-file, or symlink change fails the build and the cell.
- Parley uses its measured web build; Python runs bytecode compilation and
  browser syntax validation; TypeScript uses the pinned compiler; Rust runs
  native and WASM release builds with `--locked --offline`.
- The canonical 038 Cargo lock was generated from the final manifest and is
  checked after both Rust commands. This closes the lock-reordering defect that
  invalidated iteration 037.
- The runner validates every transitive harness, task-logic module, template,
  adapter, validator, dependency manifest, and lockfile against the protocol's
  SHA-256 list.
- Exact v0.5.0 source/install provenance, dependency trees, toolchains,
  Playwright/Chromium, host platform, and Codex executable are recorded and
  revalidated before and after execution.
- Editable files must remain regular files. The TypeScript dependency symlink
  has one exact target. Added paths outside declared generated directories,
  FIFO replacement, broker protocol errors, or mismatched external attempt
  records invalidate the cell.
- Every successful public build runs exactly three HTTP and one browser case,
  plus derived HTTP/browser agreement. A build-only response cannot satisfy
  execution integrity.
- Each cell has one immutable start and finish journal. An interrupted started
  cell is a permanent failure; only never-started cells may run after resume.
- Fresh execution refuses an existing output, non-empty journal or attempt
  root, dirty repository, or mismatched provenance.

## Pre-measurement evidence

The task-free exact-build mechanism first proved both a canonical positive
control and the 037-style noncanonical-lock negative control. After protocol
preregistration and the committed harness checkpoint:

- 16/16 reference task/language cells built and passed;
- 144/144 named public and hidden HTTP/browser cases passed;
- 16/16 derived HTTP/browser equality checks passed;
- 16/16 intentionally incorrect seeds built with stable frozen inputs;
- 0/16 seeds incorrectly passed their public semantics;
- 8/8 maintenance pairs changed only their predeclared root set;
- all 24 reference build commands and 24 seed build commands preserved every
  protected/read-only input; and
- a non-model smoke exercised source printing, FIFO checking, four public and
  five hidden cases, browser judgments, derived agreement, and final integrity.

The reference and orchestration artifacts must be regenerated after this
revision is committed so they record the final protocol hash. The complete
repository suite must pass and the repository must be clean before the first
measured cell.

## Measurement command

After the final preflight artifacts are committed, run the matrix once:

```bash
python3 benchmarks/run_fullstack_agent_038.py run \
  --parley-command /private/tmp/parley-fullstack-038-parley/bin/parley \
  --provenance /private/tmp/parley-fullstack-038-provenance.json \
  --work-root /private/tmp/parley-fullstack-038-work \
  --journal-root /private/tmp/parley-fullstack-038-journal \
  --attempt-root /private/tmp/parley-fullstack-038-attempts \
  --output benchmarks/results/fullstack_agent_038_raw.json
```

Every frozen cell runs exactly once. There are no task-informed model smoke
sessions, selective reruns, exclusions, or same-corpus fixes after measurement
begins.
