# Research plan

Parley's publishable research angle is not "English syntax is nicer" or
"another notation has fewer characters." The work now has two deliberately
separate tracks: whether an agent-oriented language reduces the cost of getting
correct programs, and whether verified context packing reduces input tokens
without reducing agent comprehension.

## Claim

**Track A — coding language.** Structured language design can improve AI
coding-agent reliability. Parley combines one canonical English-like syntax,
static checks, and JSON repair diagnostics. It must be compared with Python and
Rust on hidden correctness, first-check success, repair loops, elapsed time,
and complete session-token cost.

**Track B — agent context.** A shape-aware translation of the JSON data model
can reduce model-input tokens without changing meaning. It must compare compact
JSON with automatically selected, round-trip-verified TOON on both token count
and downstream task accuracy. This layer is documented in
[`AGENT_DATA.md`](AGENT_DATA.md) and is not Parley language syntax.

## Questions

1. Do agents produce valid programs in fewer attempts when targeting Parley?
2. Does `parley check --json` reduce the number of model/tool turns needed
   after an initial compiler error?
3. How much source-token overhead does Parley introduce relative to Python and
   Rust for the same small programs?
4. Which error classes remain hard for agents even with structured hints?
5. Which structured-data shapes produce real savings under each model's
   tokenizer after exact round-trip verification?
6. Does read-only TOON context preserve answer and coding accuracy relative to
   JSON, including all format-repair tokens?

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

Each task now has equivalent reference implementations in Parley, Python, and
Rust, and `benchmarks/tasks.json` records the source path for all three. Keep
prompts language-neutral: describe the behavior, inputs, outputs, and
constraints, then ask the agent to implement in the assigned language.

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

For agent-data experiments, freeze the JSON corpus, tokenizer, model, prompts,
randomization, scoring code, repetitions, non-inferiority margin, and fallback
policy before measuring outcomes. Report input compression separately from
task accuracy. Keep requested model output in JSON so an output-format failure
cannot be mistaken for a source-language or comprehension failure.

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
harness now exists in [`benchmarks/`](../benchmarks/) and is exposed through
`parley benchmark`: it renders language-neutral task prompts with
`parley benchmark prompt`, records source-size metrics for equivalent Parley,
Python, and Rust references across the ten example tasks, with source paths
declared in `benchmarks/tasks.json`; it can add `tiktoken` model-token counts
with `--llm-tokenizer`, verifies each Parley source with `parley check --json`,
and can append generated attempts plus diagnostics/stdout/stderr to a JSONL run
log with `parley benchmark append`. The same run log can be summarized with
`parley benchmark summarize` into first-run success, eventual success, elapsed
time, and repair-turn counts by task/language/model.

The independent deeper-project confirmation in report 032 froze 18 sessions
and 72 language assignments. All 72 were hidden-correct and first-check-correct
with no repairs, and all 24 Parley cases found the exact defect root. The strict
efficiency gate nevertheless finished only 2/4: Parley's 15,704.5 median
tokens exceeded Python's 15,033 and Rust's 15,451.375, while its 8.4545-second
median was between Python's 7.5247 and Rust's 9.3756. That is repeated evidence
for reliability and diagnosis, not proof that Parley is universally cheaper.

The next agent-data stage starts from an adaptive JSON/TOON implementation and
a frozen shape-diverse repository corpus. Iteration 033 retained all 12 cases,
verified every supported round trip, and selected TOON for three cases under
both primary tokenizers. Savings were 4.5682% (`cl100k_base`) and 4.5673%
(`o200k_base`), narrowly below the frozen 5% threshold, so Stage A is preserved
as a failed 4/5 with no profile tuning. Static compression can establish only
losslessness and conditional token savings. The preregistered 90-session paired
study is still required before claiming that the representation works better
for agents. Track A likewise still needs mature external projects, more models,
and independent replication before any "best language" claim.

Iteration 034 freezes that next study at 90 fresh cells: five exact-answer task
families, JSON/TOON pairs, sol-low/sol-medium/terra-medium configurations, and
three repetitions. It spans two model IDs rather than the three proposed in the
Stage B outline because only those two are available in the established Codex
runner; that constraint is recorded before output and limits generalization.

The complete 90-session result passes all five frozen conditions: 90 unique
tool-free sessions, 90/90 exact answers, 90/90 valid JSON responses, and lower
input plus total tokens in every one of 45 matched pairs. TOON saves 1.1083% of
summed input tokens and 1.1066% of complete input-plus-output tokens after the
large fixed Codex context is included. This confirms non-inferior adaptive input
packing for the selected record-heavy tasks. It does not test model-generated
TOON, heterogeneous shapes, external model families, or Parley source against
Python/Rust.
