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

## What this proves

- The Phase 1 task list is explicit in `benchmarks/tasks.json`.
- Each task has Parley, Python, and Rust reference sources.
- Source-size metrics are reproducible inside the repo for all three
  languages.
- The Parley side of the corpus can be verified without a Rust build.

## What this does not prove yet

- `rough_tokens` is a regex count, not an LLM tokenizer count.
- It does not run agents, collect repair turns, or measure generated patches.
- It does not make a publishable claim about Parley outperforming another
  language.

Those are the next steps before an arXiv paper can make results claims.
