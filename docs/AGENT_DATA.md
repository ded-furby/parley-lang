# Agent data: fewer context tokens without changing meaning

Parley treats source code and structured context as two different optimization
problems. The language makes programs easier for agents to write and repair.
The `parley data` commands make existing JSON cheaper to place in an agent's
context when, and only when, a verified compact encoding is actually smaller.

This is a translation layer around the JSON data model. It is not new Parley
syntax, a storage format, a public API contract, or a reason to make agents
generate unfamiliar output.

## The safety contract

`parley data pack INPUT.json` follows five rules:

1. Parse strict UTF-8 JSON and reject `NaN` and infinity.
2. Build both compact JSON and a conservative TOON candidate.
3. Decode the TOON candidate and compare the complete ordered JSON data model.
4. Select TOON only when it is supported, round-trips exactly, and uses
   strictly fewer measured tokens. Otherwise select compact JSON.
5. Refuse silent replacement and optionally write a SHA-256 measurement report.

The semantic contract therefore remains JSON even when the delivered bytes are
TOON. `--format toon` can require TOON, but it fails instead of approximating an
unsupported value. `--format json` always produces compact JSON.

```bash
# Inspect the decision without writing anything.
parley data compare context.json

# Let Parley choose and preserve an auditable measurement.
parley data pack context.json \
  --output context.agent \
  --report context.measurement.json

# Validate or restore the compact representation.
parley data check context.agent --json
parley data unpack context.agent --output restored.json --pretty
```

The default `rough` tokenizer is a deterministic regex intended for local
comparison, not a claim about a particular model. Install the `research` extra
and pass a known tiktoken encoding for model-token measurements:

```bash
pip install 'parley-lang[research]'
parley data compare context.json --tokenizer cl100k_base
```

## Supported TOON profile

The current `parley-safe-subset-v1` encoder targets TOON 4.1 forms that have a
simple lossless interpretation:

- JSON primitives;
- root and nested objects with ordered text keys;
- arrays of primitives;
- uniform arrays of non-empty, flat objects with the same ordered keys.

Mixed arrays, nested arrays, non-uniform object rows, empty-object table rows,
and other ambiguous shapes fall back to JSON in automatic mode. The decoder is
strict about indentation, declared array lengths, table widths, duplicate keys,
quoted escapes, finite numbers, and trailing whitespace. No third-party TOON
runtime is needed.

This conservative boundary follows the official [TOON 4.1 working-draft
specification](https://toonformat.dev/reference/spec), which presents TOON as a
translation of the JSON data model and says tabular arrays are its strongest
case. The specification also cautions that deeply nested or non-uniform data,
storage, and public interchange APIs may be better served by JSON.

## Why automatic instead of TOON everywhere

Token count alone does not prove better agent performance. The 2026 paper
[Notation Matters: How Data Format Choice Impacts LLM
Performance](https://arxiv.org/abs/2605.29676) reports task- and model-dependent
tradeoffs: TOON can reduce prompt tokens, but unfamiliar output notation can
also reduce accuracy or trigger costly parse-repair cascades.

Parley therefore separates two questions:

- **Input compression:** Does a representation save real model tokens while
  preserving the exact JSON value? `parley data` can answer this deterministically.
- **Agent comprehension:** Does the model still answer or code correctly from
  that representation? Only a blinded, repeated task evaluation can answer this.

Until the second gate is demonstrated broadly, Parley's tools and diagnostics
continue to emit JSON for agents. TOON is an optional read-only context
optimization, never a benchmark-shaped language feature.

## Measurement report

The report records the tokenizer, input SHA-256, candidate byte/character/token
counts, round-trip status, selection reason, requested and delivered formats,
savings relative to compact JSON, and output SHA-256. A consumer should retain
the JSON source or generated report alongside a packed artifact; packed output
is a derived context asset rather than the source of truth.

## Thesis gates

Parley should claim an agent-data win only when all of these hold on a frozen,
public corpus:

1. Every selected compact artifact round-trips to the exact JSON data model.
2. Selection produces positive token savings under the model's real tokenizer.
3. Read-only comprehension or coding accuracy is non-inferior to JSON across
   multiple task families and models.
4. Total session tokens, including format errors and repairs, are lower.
5. The implementation remains small, deterministic, and independent of one
   benchmark transcript.

Source-language claims remain separate: Parley must still beat Python and Rust
on hidden correctness, first-check success, repair turns, and total session
cost. Combining those scores would hide which part of the system actually
helped.
