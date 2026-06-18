# Research plan

Parley's publishable research angle is not "English syntax is nicer." The
paper should test whether an agent-oriented language surface reduces the cost
of getting correct compiled programs from coding agents.

## Claim

Structured language design can improve AI coding-agent reliability. Parley
combines one canonical English-like syntax, static checks, and JSON repair
diagnostics. The expected result is fewer repair loops and less token spend
than comparable Python or Rust tasks.

## Questions

1. Do agents produce valid programs in fewer attempts when targeting Parley?
2. Does `parley check --json` reduce the number of model/tool turns needed
   after an initial compiler error?
3. How much source-token overhead does Parley introduce relative to Python and
   Rust for the same small programs?
4. Which error classes remain hard for agents even with structured hints?

## Phase 1 benchmark

Use the existing examples as the seed corpus:

- hello
- fizzbuzz
- records
- enums and match-like branching
- lists and maps
- higher-order function values
- file statistics
- calculator with recoverable runtime errors
- guessing game with input
- todo list

For each task, prepare equivalent reference implementations in Parley, Python,
and Rust. Keep prompts language-neutral: describe the behavior, inputs,
outputs, and constraints, then ask the agent to implement in the assigned
language.

## Metrics

- **First-check success:** program parses and type-checks on the first attempt.
- **First-run success:** program runs and matches expected output on the first
  attempt.
- **Repair turns:** number of check/run/fix cycles until success.
- **Diagnostic use:** whether the next patch follows the emitted P-code hint.
- **Token cost:** prompt, source, diagnostic, and repair tokens.
- **Wall time:** optional, measured separately from token count.

## Protocol

1. Freeze the language version and benchmark tasks.
2. Run each language/task/model combination multiple times with fresh context.
3. Allow only documented compiler/runtime output as feedback.
4. Record every generated source file, diagnostic JSON payload, stdout/stderr,
   and patch attempt.
5. Judge success with executable tests, not manual inspection.

## Baselines

- Python: concise dynamic baseline with broad model familiarity.
- Rust: safe native-code baseline with strong compiler diagnostics.
- Parley: agent-oriented syntax plus Parley P-code diagnostics.

Zero or other experimental agent-facing languages can be added later, but the
first paper should stay small enough to run and audit.

## Paper shape

1. Motivation: coding agents are now a language-design target.
2. Design: canonical syntax, total checker, JSON repair contract, Rust backend.
3. Implementation: compact compiler pipeline and test suite.
4. Evaluation: benchmark protocol, results, and error taxonomy.
5. Discussion: where English-like syntax helps, where it hurts, and what
   language features agents still need.

## Current status

The compiler and documentation are ready for a pilot study. A Phase 1 seed
harness now exists in [`benchmarks/`](../benchmarks/): it records source-size
metrics for equivalent Parley, Python, and Rust references across the ten
example tasks, can add `tiktoken` model-token counts with
`--llm-tokenizer`, verifies each Parley source with `parley check --json`,
and can append generated attempts plus diagnostics/stdout/stderr to a JSONL
run log with `benchmarks/runlog.py`. The same run log can be summarized into
first-run success, eventual success, elapsed time, and repair-turn counts by
task/language/model.

This is not yet a paper result. Repeated agent runs and success judgments
across fresh samples still need to be run before any comparative claims should
be made.
