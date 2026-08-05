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

## Shipped in v0.3.157

- `parley workflow test` with isolated, exact-output fixture comparison.
- schema-2 manifests with ordered named inputs and declared test cases.
- validation for missing, duplicate, and unknown inputs, plus output identity
  protection across every named input.
- schema-1 run compatibility and generated fixtures for every starter.

## Shipped in v0.3.158

- Release Steward combines named test, metadata, checklist, and package inputs
  into one Markdown `READY` or `BLOCKED` decision.
- repository dogfood evidence records a truthful blocked release and the exact
  open checklist items.
- three wheel-bundled products install by catalog name into readable local
  source, with semantic versions and whole-tree SHA-256 lock records.
- `parley workflow verify` detects missing or modified installed products.

## Shipped beside Workflows in v0.3.159

- `parley data compare`, `pack`, `check`, and `unpack` provide a platform-level
  agent-context translation layer around the JSON data model.
- automatic mode uses TOON only after exact round-trip verification and a
  strictly-lower measured token count; unsupported shapes retain compact JSON.
- no workflow contract or Parley language syntax changed, so this does not
  manufacture product evidence for structured values inside programs.

## Next product loop

1. Record where users edit installed source, where they get stuck, and how long
   the first successful run takes.
2. Add a helper or platform capability only when it recurs across unrelated
   workflows and has a coherent safety model.
3. Seek independent maintainers before calling the first-party catalog an
   ecosystem.

Near-term workflow/runtime candidates are structured JSON/CSV values inside a
Parley program, explicit directory enumeration, and HTTP requests. The
v0.3.159 CLI packer does not satisfy that separate need. None should become
syntax merely because one benchmark or starter wants it; each needs a general
API, deterministic tests, clear failure behavior, and a maintainable
implementation.

The v0.3.158 review in [`CAPABILITY_EVIDENCE.md`](CAPABILITY_EVIDENCE.md)
deferred JSON and CSV: only one of three products needed flat key-value reads,
and zero needed CSV. Reconsider only after the documented recurrence gate.

## Adoption gates

- A new user can scaffold, check, and run a workflow in under ten minutes.
- Re-running with identical input produces identical output.
- Unsafe replacement is opt-in and visible.
- At least three real workflows are maintained by someone other than their
  original author before claiming ecosystem traction.
- Language/compiler changes must demonstrate cross-workflow usefulness rather
  than optimize one transcript or token score.
