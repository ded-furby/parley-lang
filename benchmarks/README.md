# Benchmarks

This directory turns the research plan in `docs/RESEARCH.md` into a runnable
starting point. It is intentionally small: it measures equivalent Parley,
Python, and Rust reference sources and verifies that every Parley seed task
passes `parley check --json`.

Run from the repository root:

```bash
python3 benchmarks/measure.py
```

The default report is written to:

```text
benchmarks/results/parley_seed_metrics.json
```

For automation:

```bash
python3 benchmarks/measure.py --format json --output /tmp/parley_seed_metrics.json
python3 benchmarks/measure.py --no-check
python3 benchmarks/measure.py --languages parley,rust
```

For model-token counts, install the optional research dependency and choose a
`tiktoken` encoding:

```bash
python3 -m pip install -e ".[research]"
python3 benchmarks/measure.py --llm-tokenizer cl100k_base
```

To capture generated attempts from an agent run:

```bash
python3 benchmarks/runlog.py append \
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
python3 benchmarks/runlog.py summarize \
  --log benchmarks/results/runs.jsonl \
  --format json
```

## What this proves

- The Phase 1 task list is explicit in `benchmarks/tasks.json`.
- Each task has Parley, Python, and Rust reference sources.
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
