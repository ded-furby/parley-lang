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
written into its workspace.

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

## Versioned benchmark reports

Completed experiment reports live in `benchmarks/reports/`. Report filenames
start with a monotonically increasing experiment number and are immutable;
new results create a new HTML file instead of replacing an earlier one. The
decision log, acceptance target, input hashes, and next experiment are kept in
`benchmarks/EXPERIMENT_LOG.md`.
