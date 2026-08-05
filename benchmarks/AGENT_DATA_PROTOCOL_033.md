# Iteration 033 — adaptive agent-data preregistration

Status: **frozen before the broad-corpus measurement**  
Date: 2026-08-05  
Parley version: 0.3.159  
Corpus: `benchmarks/agent_data_corpus.json`  
Manifest SHA-256: `8dd47b32a3b5103cb22153d9a390ff8a4b7669e7fead3cea9a397ece2c19e08b`

## Motivation and disclosed pilot

The official TOON 4.1 working draft describes a JSON-model translation that is
particularly compact for uniform object arrays and less suitable for deeply
nested or non-uniform structures. External research also reports that token
savings do not guarantee model accuracy. Parley therefore implements adaptive
selection with an exact round-trip gate instead of adopting TOON as syntax.

Before freezing this corpus, one implementation smoke test inspected
`site/registry.json`: the deterministic rough counter selected TOON and measured
37.234% fewer tokens. That file remains in the broad corpus, but this known
pilot must not be described as confirmatory evidence.

No other corpus aggregate, per-case eligibility count, real-tokenizer result,
or comprehension outcome will be inspected before this protocol is committed.

## Stage A: representation diagnostic

The frozen manifest contains 12 JSON documents from compiler diagnostics,
tests, configuration, event streams, package metadata, workflow manifests,
benchmark protocols, patch catalogs, and portable reports. Seven are existing
repository artifacts and five are synthetic instances of documented repository
contracts. Cases cover uniform records, nested objects, primitive arrays,
non-uniform records, mixed/nested arrays, and large heterogeneous documents.

Run exactly once with:

```bash
python3 benchmarks/measure_agent_data.py \
  --tokenizer rough \
  --tokenizer cl100k_base \
  --tokenizer o200k_base \
  --output benchmarks/results/agent_data_033.json
```

The rough tokenizer is a deterministic diagnostic. The two tiktoken encodings
are the primary token-count views. No case may be removed because it falls back
to JSON or worsens the desired aggregate.

### Frozen Stage A gates

Stage A passes only if all are true:

1. All 12 files parse as strict UTF-8 JSON.
2. Every supported TOON candidate decodes to the exact ordered JSON data model.
3. Automatic selection never increases tokens for any case or tokenizer.
4. At least three cases select TOON and at least three fall back to JSON under
   each primary tokenizer, demonstrating that selection is genuinely adaptive.
5. Aggregate adaptive tokens are at least 5% below compact JSON under both
   `cl100k_base` and `o200k_base`.

Failure is a valid result. It must be preserved, and it triggers no same-corpus
encoder, syntax, corpus, tokenizer, or threshold change. A success proves only
lossless conditional compression on these documents—not model comprehension,
coding quality, or superiority over another programming language.

## Stage B: planned 90-session agent confirmation

Stage B will be run only after Stage A is preserved and a separate immutable
task/prompt manifest is committed. The design is 90 fresh sessions:

- 5 task families: exact lookup, filtering, aggregation, cross-record
  reasoning, and context-grounded code modification;
- 2 input representations: compact JSON and the verified adaptive artifact;
- 3 independently frozen model IDs;
- 3 repetitions per task/representation/model cell.

Representation labels and file extensions will be neutralized where practical,
cell order will be seeded and randomized, and every session will start without
benchmark-history context. Prompts, JSON data model, allowed tools, and scoring
must be identical across representations. Models will answer in JSON in both
arms; asking them to generate TOON would test output notation rather than input
comprehension.

Before any Stage B session, its manifest must freeze the exact model IDs,
temperature/reasoning settings, seed, task inputs, prompts, expected answers,
timeouts, retry policy, parser, hidden scorer, and hashes. Primary outcomes are
hidden exact correctness and total session tokens including parse or repair
turns. Secondary outcomes are first-response parse success, elapsed time, and
error taxonomy. No failed or inconvenient cell may be silently rerun or
excluded.

The non-inferiority and savings margins will be frozen in that Stage B manifest
after Stage A establishes the actual token effect but before model output is
seen. Until all 90 sessions are preserved, Parley may claim only deterministic
round-trip behavior and the measured Stage A representation savings.

## Change policy

- Do not add Parley syntax because a corpus case is awkward.
- Do not tune the TOON profile from Stage A or Stage B outcomes and re-score the
  same data as confirmation.
- Any implementation repair discovered before measurement requires updating
  the version, manifest/protocol hashes, and this status before a fresh run.
- Preserve report 013, report 032, raw Stage A JSON, the generated HTML, and
  every future Stage B transcript in the progress archive.
- Judge follow-up work by general usefulness, semantic consistency, security,
  and maintainability—not token savings alone.
