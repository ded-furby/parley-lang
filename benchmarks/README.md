# Benchmarks

This directory turns the research plan in `docs/RESEARCH.md` into a runnable
starting point. It is intentionally small: it measures equivalent Parley,
Python, and Rust reference sources and verifies that every Parley seed task
passes `parley check --json`. The manifest in `tasks.json` records the Parley,
Python, and Rust source path for every task.

Run from the repository root:

```bash
parley benchmark measure
```

The default report is written to:

```text
benchmarks/results/parley_seed_metrics.json
```

For automation:

```bash
parley benchmark prompt --task hello --language parley
parley benchmark prompt --language python --format json --output /tmp/python_prompts.json
parley benchmark measure --format json --output /tmp/parley_seed_metrics.json
parley benchmark measure --no-check
parley benchmark measure --languages parley,rust
```

For model-token counts, install the optional research dependency and choose a
`tiktoken` encoding:

```bash
python3 -m pip install -e ".[research]"
parley benchmark measure --llm-tokenizer cl100k_base
```

To capture generated attempts from an agent run:

```bash
parley benchmark append \
  --log benchmarks/results/runs.jsonl \
  --task hello \
  --language parley \
  --model my-agent \
  --attempt 1 \
  --status first_run_success \
  --prompt-file /tmp/prompt.md \
  --source-file /tmp/answer.par \
  --diagnostics-file /tmp/check.json \
  --stdout-file /tmp/stdout.txt \
  --stderr-file /tmp/stderr.txt
```

To summarize a run log by task/language/model:

```bash
parley benchmark summarize \
  --log benchmarks/results/runs.jsonl \
  --format json
```

The underlying scripts (`benchmarks/measure.py` and `benchmarks/runlog.py`)
remain executable directly, but the `parley benchmark ...` command is the
documented interface from the source checkout.

## What this proves

- The Phase 1 task list and reference source paths are explicit in
  `benchmarks/tasks.json`.
- Each task has Parley, Python, and Rust reference sources.
- Language-neutral prompts are reproducible from the same manifest.
- Source-size metrics are reproducible inside the repo for all three
  languages.
- LLM-token counts can be produced with a named `tiktoken` encoding.
- Generated attempts, diagnostics, stdout/stderr, prompts, and patches can be
  captured in a JSONL run log.
- Run logs can be summarized into first-run success, eventual success, elapsed
  time, and repair-turn counts by task/language/model.
- The Parley side of the corpus can be verified without a Rust build.

## What this does not prove yet

- `rough_tokens` is a regex count; use `--llm-tokenizer` for model-token
  counts.
- It does not run agents by itself or decide semantic correctness beyond the
  status labels recorded by the runner.
- It does not make a publishable claim about Parley outperforming another
  language.

Those are the next steps before an arXiv paper can make results claims.

## Fresh-context coding-agent pilot

`agent_runner.py` runs a small end-to-end pilot with new ephemeral Codex
sessions. Its tasks live in `agent_tasks.json`, separate from the seed corpus.
Each session receives one task, one public example, a uniform `./check`
command, and no hidden cases. The parent runner judges the final source after
the session exits and records the complete transcript, source, compiler
attempts, token usage, and hidden-case output.

Protocol v2 also forbids listing or reading any existing workspace file. The
first tool action must create the solution, and the only permitted shell
command is exactly `./check`. Every result records command-protocol compliance
and the exact violating commands, if any.

Build or install the exact Parley revision being measured, then run:

```bash
python3 benchmarks/agent_runner.py \
  --replicates 2 \
  --model gpt-5.6-sol \
  --reasoning medium \
  --parley-command /absolute/path/to/parley \
  --output benchmarks/results/agent_pilot.json
```

The default matrix is three held-out tasks by Parley, Python, and Rust. Every
cell uses a fresh temporary directory and ephemeral agent session. Parley gets
the current `skill/parley/SKILL.md`, and its prompt tokens are included in the
reported cost. Agent tool access has no internet, and hidden cases are not
written into its workspace. Runs with a command-protocol violation are not
valid acceptance evidence even if their final source passes.

The separately frozen `agent_tasks_broad.json` manifest expands coverage to
eight tasks across text processing, numeric streams, stateful aggregation,
and sequence transformation. It also records the predeclared 48-session
matrix, outcomes, reporting policy, and change rule. Run it without altering
the compiler or skill after the manifest is committed:

```bash
python3 benchmarks/agent_runner.py \
  --tasks-file benchmarks/agent_tasks_broad.json \
  --replicates 2 \
  --seed 20260730 \
  --model gpt-5.6-sol \
  --reasoning medium \
  --parley-command /absolute/path/to/parley \
  --output benchmarks/results/agent_broad_corpus.json
```

The broad corpus is diagnostic. A failure or efficiency difference isolated
to one task is not a reason to add syntax. Future language changes must be
useful across unrelated programs and must preserve semantic consistency and
maintainability.

## Workload-scale bundle benchmark

`bundle_runner.py` measures whether the fixed cost of fresh-session language
instructions amortizes when one agent session completes several unrelated
programs. Its complete iteration-017 configuration and parity gate live in
`bundle_protocol_017.json`; the runner takes model, tasks, bundle sizes,
replicates, seed, timeout, and concurrency from that file rather than mutable
command-line flags.

Each replicate assigns the same eight broad tasks exactly once per language at
bundle sizes 1, 2, 4, and 8. The parent process retains all hidden cases. One
workspace checker compiles and runs every public program in the bundle, while
the result preserves task-level source, first-check status, hidden judgments,
session usage, and protocol integrity.

```bash
python3 benchmarks/bundle_runner.py \
  --protocol-file benchmarks/bundle_protocol_017.json \
  --parley-command /absolute/path/to/parley \
  --output benchmarks/results/agent_bundle_017_protocol_v1_v0.3.151.json
```

Per-task values always divide one session's complete token or elapsed total by
the number of assigned tasks; session totals remain in the same report. The
predeclared strict gate applies at bundle size eight and requires Parley to
match the better baseline on correctness, tokens per task, elapsed time per
task, and first-check task success.

If an objective hidden-test oracle error is found, saved sources can be
rejudged without changing or rerunning agent attempts:

```bash
python3 benchmarks/agent_runner.py \
  --rejudge-report benchmarks/results/agent_pilot.json \
  --rejudge-note "Describe the oracle correction" \
  --parley-command /absolute/path/to/parley \
  --output benchmarks/results/agent_pilot.json
```

This is a protocol and smoke-scale pilot, not a publishable sample. A serious
comparison needs more held-out tasks, more repetitions, multiple models, a
predeclared analysis, and an execution sandbox that prevents reads outside
the per-run workspace rather than relying on the benchmark instruction.

## Unseen full-stack fresh-agent study 036

Iteration 036 is the preregistered fresh-session follow-up to product comparison
035. It leaves the historical three-language CLI runners untouched and adds a
separate Parley/Python/TypeScript/Rust harness for four new typed-HTTP plus
browser assignments. The 96-cell matrix spans two implementation tasks, two
maintenance tasks, sol-medium, terra-medium, and three repetitions.

Prepare the pinned offline dependency stores, verify every reference/seed
boundary, then run the matrix from the committed checkpoint:

```bash
python3 benchmarks/prepare_fullstack_agent_036.py
python3 benchmarks/run_fullstack_agent_036.py validate-corpus
python3 benchmarks/run_fullstack_agent_036.py validate-references \
  --parley-command /private/tmp/parley-fullstack-036-parley/bin/parley \
  --provenance /private/tmp/parley-fullstack-036-provenance.json \
  --output benchmarks/fullstack_agent_036_validation.json
python3 benchmarks/run_fullstack_agent_036.py run \
  --parley-command /private/tmp/parley-fullstack-036-parley/bin/parley \
  --provenance /private/tmp/parley-fullstack-036-provenance.json \
  --work-root /private/tmp/parley-fullstack-036-work \
  --journal-root /private/tmp/parley-fullstack-036-journal \
  --output benchmarks/results/fullstack_agent_036_raw.json
```

`./sources` is allowed exactly once in every agent cell; all later shell
activity must be exactly `./check`. The public checker builds and runs the real
HTTP/browser application. Hidden cases remain in the parent runner. The frozen
six-condition gate and no-rerun rule are in
`fullstack_agent_036_protocol.json`.

The 96-cell matrix has now run exactly once. Its strict gate failed, and a
post-run audit classified the execution as invalid for the intended public
feedback loop: sandbox network denial also blocked localhost in all 179 public
checks, while Cargo rewrote the stale root package entry in all 24 Rust
lockfiles. Do not rerun or tune iteration 036. Preserve its raw result and use
new tasks in iteration 037 after a complete in-sandbox public HTTP/browser
smoke passes. See `FULLSTACK_AGENT_036.md` and the canonical report artifact in
`benchmarks/reports/036-unseen-fullstack-study-invalid.artifact.json`.

## Parent-owned public checker for iteration 037

The replacement checker transport is implemented in
`agent_check_transport.py`. The agent keeps outbound and loopback networking
disabled; its protected `./check` wrapper sends a bounded request over POSIX
FIFOs to the parent runner, which performs public HTTP and real-Chromium checks
outside the sandbox and returns only public feedback. Complete attempts are
written atomically outside the agent workspace, and FIFO identity plus client
hashes are checked for every cell.

Before any 037 task semantics were frozen, independent terra-medium and
sol-medium Codex smokes both passed the full compile, HTTP, JavaScript-module,
and browser-render path with exactly `./sources` then `./check`. See
`AGENT_CHECK_TRANSPORT.md` and the two
`agent_check_transport_smoke*.json` evidence artifacts. These smokes validate
the execution mechanism only; they are not language results.

The independent 037 corpus is now frozen in
`fullstack_agent_037_tasks.json` and `fullstack_agent_037_cases.json`: two new
implementations, two new repairs, four public cases per task, and five hidden
cases per task. Every task has an explicit public Chromium case, and automated
oracles verify all success fixtures. No 037 scaffold, reference implementation,
protocol threshold, or measured session existed at the corpus checkpoint. See
`FULLSTACK_AGENT_037.md` for the freeze and claim boundaries.

## Versioned benchmark reports

Completed experiment reports live in `benchmarks/reports/`. Report filenames
start with a monotonically increasing experiment number and are immutable;
new results create a new HTML file instead of replacing an earlier one. The
decision log, acceptance target, input hashes, and next experiment are kept in
`benchmarks/EXPERIMENT_LOG.md`.
