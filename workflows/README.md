# Parley Workflows

Parley Workflows is the first product layer built on the language: small,
deterministic file transformations that are readable by a person, easy for an
agent to modify, and compiled to native binaries through Rust.

## Start a workflow

```bash
parley workflow list
parley workflow new my-cleaner --template clean-text
parley workflow test my-cleaner
parley workflow run my-cleaner \
  --input source=my-cleaner/input.txt \
  --output result.txt
```

The schema-2 manifest declares ordered named inputs and exact-output fixtures.
`parley workflow test` compiles once, runs each case into an isolated temporary
output, and compares bytes exactly. The runner validates every named input,
refuses to replace an existing output unless `--force` is explicit, and never
allows the output to be any input file. Schema-1 single-input workflows remain
compatible. Every starter is normal Parley source in `main.par`; use `parley
check` while editing it and include `std/workflow` for reusable helpers.

Multiple inputs repeat `--input NAME=PATH`; their CLI order does not matter:

```bash
parley workflow run release-steward \
  --input package_info=package.txt \
  --input test_results=tests.txt \
  --output readiness.md
```

The program receives paths in the manifest's declared order, with the output
path last. Missing, duplicate, and unknown input names fail before compilation.

## Included starters

- `clean-text` trims lines and removes blanks.
- `log-summary` counts `ERROR`, `WARN`, and `INFO` rows and produces Markdown.
- `checklist-report` summarizes open and completed Markdown checklist items.

## Install a maintained workflow

```bash
parley workflow install release-steward
parley workflow install log-summary
parley workflow install checklist-report
parley workflow verify
```

The three first-party products ship inside the Python wheel. Installation
copies readable source and fixtures into `parley_workflows/` and records the
semantic version, source, path, and whole-tree SHA-256 in
`parley.workflows.lock.json`. Run or test an installed workflow by name. An
existing install is preserved unless `--force` is explicit, and `verify`
reports missing or locally changed files.

## Product rule

New workflow helpers must solve a repeated real task, compose with existing
functions, and preserve deterministic behavior. A helper should not be added
only because one benchmark transcript happened to use it.
