# Parley Workflows

Parley Workflows is the first product layer built on the language: small,
deterministic file transformations that are readable by a person, easy for an
agent to modify, and compiled to native binaries through Rust.

## Start a workflow

```bash
parley workflow list
parley workflow new my-cleaner --template clean-text
parley workflow run my-cleaner --input my-cleaner/input.txt --output result.txt
```

The runner validates the input, refuses to replace an existing output unless
`--force` is explicit, and never allows the output to be the input file. Every
starter is normal Parley source in `main.par`; use `parley check` while editing
it and include `std/workflow` for the reusable helpers.

## Included starters

- `clean-text` trims lines and removes blanks.
- `log-summary` counts `ERROR`, `WARN`, and `INFO` rows and produces Markdown.
- `checklist-report` summarizes open and completed Markdown checklist items.

## Product rule

New workflow helpers must solve a repeated real task, compose with existing
functions, and preserve deterministic behavior. A helper should not be added
only because one benchmark transcript happened to use it.

