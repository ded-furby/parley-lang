# Benchmarks

This directory turns the research plan in `docs/RESEARCH.md` into a runnable
starting point. It is intentionally small: it measures the existing Parley
examples and verifies that every seed task passes `parley check --json`.

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
```

## What this proves

- The Phase 1 Parley task list is explicit in `benchmarks/tasks.json`.
- Each task points at a real checked example in `examples/`.
- Source-size metrics are reproducible inside the repo.
- The Parley side of the corpus can be verified without a Rust build.

## What this does not prove yet

- It does not include equivalent Python or Rust implementations.
- `rough_tokens` is a regex count, not an LLM tokenizer count.
- It does not run agents, collect repair turns, or measure generated patches.
- It does not make a publishable claim about Parley outperforming another
  language.

Those are the next steps before an arXiv paper can make results claims.
