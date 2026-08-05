# Parley Workflows roadmap

## Product thesis

Parley should earn adoption by making useful automation easier to understand,
safer to run, and cheaper for agents to maintain. Workflows is the first place
to prove that outside a benchmark harness.

## Shipped in v0.3.156

- `parley workflow list`, `new`, and `run`.
- `clean-text`, `log-summary`, and `checklist-report` starters.
- bundled `std/workflow` helpers for required file reads, normalized lines,
  line filtering/counting, Markdown formatting, and output writes.
- overwrite protection, input/output identity protection, schema-1 workflow
  manifests, native end-to-end tests, and wheel resource verification.

## Next product loop

1. Dogfood the three starters on real repository and operations work.
2. Record where users edit generated source, where they get stuck, and how long
   the first successful run takes.
3. Add a helper or platform capability only when it recurs across unrelated
   workflows and has a coherent safety model.
4. Publish a small community workflow catalog after at least three independent
   workflows can be installed, inspected, and rerun deterministically.

Near-term candidates are structured JSON/CSV input, explicit directory
enumeration, and HTTP requests. None should become syntax merely because one
benchmark or starter wants it; each needs a general API, deterministic tests,
clear failure behavior, and a maintainable implementation.

## Adoption gates

- A new user can scaffold, check, and run a workflow in under ten minutes.
- Re-running with identical input produces identical output.
- Unsafe replacement is opt-in and visible.
- At least three real workflows are maintained by someone other than their
  original author before claiming ecosystem traction.
- Language/compiler changes must demonstrate cross-workflow usefulness rather
  than optimize one transcript or token score.
