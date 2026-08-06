# Parley

**Speak plainly, ship native binaries.** An English-like programming language
where AI agents are the primary authors — compiled to real machine code
through Rust.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Website: [ded-furby.github.io/parley-lang](https://ded-furby.github.io/parley-lang/)

```parley
a cat has name as text, lives as number

to describe with c as cat giving text:
    give back "{c's name} has {c's lives} lives left"

let felix be a cat with name "Felix", lives 9
say (describe with felix)

let tally be a map from text to number
set item "naps today" of tally to 4
for each key in keys of tally:
    say "{key}: {item key of tally}"
say "total: {sum of values of tally}"
```

```
$ parley run cats.par
Felix has 9 lives left
naps today: 4
total: 4

$ parley build cats.par -o cats     # → a ~350 KiB native binary, no runtime
```

## Why

Every language asks its author to remember things compilers should handle:
Python forgets your types until 2 a.m., Rust makes you negotiate with a
borrow checker. Both were designed for *humans* — and now most new code is
written by agents, whose strengths (English, patterns, fast retries on good
feedback) and weaknesses (hallucinated APIs, off-by-one symbol soup) are
completely different.

Parley is designed around that author:

* **The syntax is English.** `set count to count plus 1` · `if guess is more
  than secret:` · `bob's name`. There is one canonical way to write each
  construct — nothing to misremember.
* **The safety is Rust's.** Parley transpiles to a memory-safe subset of
  Rust; rustc compiles the binary. Static types, no nulls (`maybe` is
  explicit), no data races, no GC, deterministic behavior — without one
  lifetime annotation in your source.
* **Every error is a repair instruction.** The checker catches mistakes
  *before* Rust ever sees them and answers in JSON with stable codes and
  exact fixes — `Did you mean "score"?` — so an agent converges in one
  retry instead of five. Runtime failures are one-line English sentences.
* **The language ships as a skill.** Drop [`skill/parley`](skill/parley)
  into any Claude Code setup and the agent is fluent — the whole language
  fits on one screen.

## Quickstart

```bash
# 1. Rust provides the backend (one-time)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 2. Install parley
pip install git+https://github.com/ded-furby/parley-lang
#    (or: pipx install git+https://github.com/ded-furby/parley-lang)

# 3. Check the local toolchain, then go
parley doctor
parley new hello && parley run hello/main.par
```

## Write an actual command-line tool

A program's two inputs are plain `list of text`, so a real filter is a few
lines and the same source behaves identically under `run` and `build`:

```parley
let top_n be (number from ((maybe item 1 of the arguments) otherwise "5")) otherwise 5

for each line in the input:
    say "{top_n}: {uppercase of line}"
```

```bash
$ echo "hello" | parley run tool.par 3
3: HELLO
```

`the arguments` is the command-line words after the program name (and
`parley run file.par ARG…` forwards them, flags included); `the input` is every
line of stdin, read once. `maybe item i of x` is non-failing access for lists,
text, and maps, so `… otherwise default` is the one-line safe read. See
[`examples/wordcount.par`](examples/wordcount.par) for a complete tool.

## Read and write JSON, typed

JSON crosses into Parley as a record you already declared. There is no untyped
"any" value to pick apart later, and no schema to keep in sync by hand:

```parley
a author has name as text, email as maybe text
a post has title as text, tags as list of text, writer as author

let loaded be a post from json ((read file "post.json") otherwise "")
if loaded has no value:
    fail "post.json is not a post"

let p be value of loaded
say "{p's title} by {p's writer's name}"
write p as json to file "copy.json"
```

`a R from json t` gives `maybe R` — `nothing` for malformed JSON, a missing
field, a wrong type, or an unknown field, the same strictness the typed web
layer applies to request bodies. An absent `maybe` field simply decodes as
`nothing`. `x as json` goes the other way for any JSON-safe value; anything
that has no JSON form is refused at check time (P317).

Maps encode in key order, so the same value always produces the same bytes —
Parley maps are `BTreeMap`, and iteration, printing, and JSON all agree. A
program that never mentions JSON still builds with no dependencies; one that
does adds serde and about 68 KiB. See
[`examples/jsonreport.par`](examples/jsonreport.par).

## Build something real: Parley Workflows

Parley Workflows is the first product layer on top of the language: small,
deterministic file transformations that a person can inspect, an agent can
modify, and Rust can compile to a native binary.

```bash
parley workflow list
parley workflow install release-steward
parley workflow test release-steward
parley workflow new release-report --template checklist-report
parley workflow test release-report
parley workflow run release-report \
  --input source=release-report/input.txt \
  --output report.md
```

The wheel-bundled catalog installs Release Steward, Log Summary, and Checklist
Report with semantic versions and whole-tree SHA-256 lock records. Release
Steward combines test results, release metadata, a checklist, and package
information into one readiness decision, and is dogfooded on this repository.
Every workflow is ordinary `main.par` source and can use
`include "std/workflow"` for reusable file, matching, normalization, and report
helpers. Schema-2 manifests declare ordered named inputs and exact-output test
fixtures. The runner requires every input, refuses to overwrite output unless
`--force` is explicit, and never permits an input and output to be the same
file. `parley workflow verify` detects local changes to installed products. See
[`workflows/`](workflows) for the product contract and roadmap.

## Pack agent context safely

Parley can also make structured context smaller without changing its meaning.
`parley data` treats JSON as the semantic source of truth, tries a conservative
TOON 4.1 encoding, decodes it back, and selects it only when the complete JSON
value survives and the requested tokenizer measures strictly fewer tokens.
Unsupported or unhelpful shapes stay compact JSON automatically.

```bash
parley data compare context.json
parley data pack context.json \
  --output context.agent \
  --report context.measurement.json
parley data unpack context.agent --output restored.json --pretty
```

This is an optional input-context translation layer, not Parley syntax or a
claim that agents should emit TOON. The strict safe subset, failure behavior,
tokenizer options, research boundary, and falsifiable thesis gates are in
[`docs/AGENT_DATA.md`](docs/AGENT_DATA.md).

## Build a typed full-stack product

Parley web projects bind ordinary checked functions to exact HTTP routes. The
compiler infers each JSON request and response contract from Parley records,
rejects unknown request fields, and builds a native server. Deterministic
scalar functions can also compile to browser WebAssembly with generated
JavaScript wrappers and TypeScript declarations—without adding web-only syntax
to the language.

```bash
parley web check examples/release-radar --json
parley web build examples/release-radar
parley web serve examples/release-radar
```

Release Radar is the dogfood application: one Parley readiness rule produces a
live WASM score in the browser and the confirmed typed assessment on the native
JSON backend. The generated server bounds headers and bodies, rejects ambiguous
lengths and unsupported transfer encoding, canonicalizes static paths, and
serves `.wasm` with the streaming MIME type. The present HTTP/1.1 and scalar
WASM limits are explicit in [`docs/WEB.md`](docs/WEB.md); this is a foundation,
not yet a claim of mature-framework parity.

The preregistered [four-language Release Radar
comparison](benchmarks/reports/035-release-radar-fullstack-compactness-proof.html)
then reproduced all 14 HTTP cases and a real browser flow in Parley, Python,
TypeScript, and Rust: **60/60 checks passed**. Parley's counted application
surface is **684 o200k tokens**, 40.37% below Python (the smallest correct
baseline), 49.93% below TypeScript, and 64.91% below Rust; `cl100k_base` keeps
the same ordering. Parley also reuses one checked scoring definition across
native code and WASM. This proves compactness for this bounded product—not
general language superiority or lower fresh-agent session tokens.

## The agent loop

```bash
$ parley check game.par --json
{
  "ok": false,
  "diagnostics": [{
    "code": "P204", "file": "game.par", "line": 12, "col": 9,
    "message": "\"scor\" is not a field of player.",
    "hint": "Did you mean \"score\"?", "severity": "error"
  }]
}
```

`check` is parse + type-check only — milliseconds, no Rust build — so the
write → check → fix loop is instant. `parley explain P204` documents any
code. `parley doctor --json` reports whether the local install can build
native binaries and whether the bundled stdlib is present. Humans get the
same diagnostics with source carets and colors.

For the research harness, run `parley benchmark prompt --task hello --language
parley` to render a language-neutral agent prompt, `parley benchmark measure
--format json` from a source checkout to produce the Parley/Python/Rust
seed-corpus metrics, and `parley benchmark summarize --log runs.jsonl --format
json` to review recorded agent attempts. The preserved
[90-session scaling report](benchmarks/reports/030-ninety-session-scaling-mechanism.html)
found a clear amortization mechanism and confirmed Rust parity around six or
more diagnosis tasks per session, while still trailing Python. The independent
[deeper-project report](benchmarks/reports/031-deeper-project-efficiency-win.html)
then passed all four predeclared efficiency/reliability conditions: Parley used
15,937 median tokens per repository and 7.3906 seconds versus Python's
23,668.38/9.2024 and Rust's 24,475.75/10.2195. Exact-root patch quality was
23/24. The independently sourced
[confirmation](benchmarks/reports/032-independent-confirmation-strict-parity-not-met.html)
then reproduced perfect reliability and improved Parley to 24/24 exact-root
patches, but did not reproduce strict efficiency parity: the frozen gate was
2/4, with Parley 4.47% above Python and 1.64% above Rust on median tokens. That
is strong, honest evidence to build on—not a claim that the language is
finished or a reason to tune syntax to one corpus. Browse the complete,
checksum-backed visual history in
[`progress/index.html`](progress/index.html).

The preregistered [adaptive agent-data
diagnostic](benchmarks/reports/033-adaptive-agent-data-gate-not-met.html) then
tested 12 JSON documents with rough, `cl100k_base`, and `o200k_base` tokenizers.
Every supported TOON candidate round-tripped exactly and automatic mode never
increased tokens. Three record-heavy cases selected TOON under both primary
tokenizers, saving 4.5682% and 4.5673% in aggregate—useful, but below the frozen
5% gate. The result is preserved as a failed 4/5, with no same-corpus tuning.

The separately committed [90-session agent
confirmation](benchmarks/reports/034-verified-toon-context-efficiency-win.html)
then tested only the record-heavy shapes where Stage A said TOON helps. JSON
and TOON both achieved 45/45 exact answers and valid JSON responses across
sol-low, sol-medium, and terra-medium. TOON used fewer tokens in all 45 matched
pairs, saving 6,392 input tokens (1.1083%) and 6,422 total session tokens
(1.1066%); the frozen gate passed 5/5. This validates adaptive read-only input
packing on this corpus, not universal TOON output or a general Parley/Python/Rust
victory.

For editor integration, start the stdio language server from your editor:

```bash
parley-lsp
```

It publishes the same stable P-code diagnostics as `parley check --json` for
open `.par` documents.

Install the skill so your agent already knows all of this:

```bash
cp -r skill/parley ~/.claude/skills/
```

## What the language has

records · enums with exhaustive `when` (multi-value arms, numeric ranges) ·
function values (`the function f`) and anonymous closures with captured values · lists, maps
(`keys of` and `values of` sorted by key), `maybe` options (`some x`, `nothing`, `value of`) · functions with `changing` (mutable)
parameters and recursion · string interpolation `"{x}"` ·
custom runtime failures with `fail "message"` ·
runtime assertions with `assert condition, "message"` ·
`attempt:`/`if it failed:` error handling with `the error` · file I/O ·
stdin `ask` · random numbers · bundled `std/math`, `std/text`, `std/list`, `std/map`, and `std/workflow`
packages · multi-file programs via `include`, `parley_modules`, and `PARLEY_PATH` package roots ·
local and registry-backed package vendoring with SHA-256 lock metadata and
`parley package verify`, plus registry validation with
`parley package check-registry` and dry-run submission review with
`parley package review`, and optional HMAC-SHA256 release signatures, via
`parley package` and `parley.lock.json` ·
setup checks with `parley doctor` ·
typed HTTP/JSON projects with checked route signatures, strict record decoding,
native static serving, bounded requests, and browser/WASM scalar exports with
generated JavaScript and TypeScript bindings via `parley web` ·
safe workflow scaffolding, fixture testing, named-input execution, checksummed
catalog installation, and drift verification with `parley workflow` ·
`stop`/`skip`/`give back` · whole-number and decimal math helpers with guarded
division, powers, roots, math constants, integer square roots, perfect-square checks, factorials, GCD/LCM, combinations/permutations, decimal closeness, hypotenuse, point-distance helpers, sign-copy checks, and angle conversions · a text toolbox (`split by`, `joined with`,
`replacing … with …`, bounded replacement, `position of … in …`, `count of … in …`,
`item i of text`, safe character lookup and slicing, `uppercase of`,
`contains`, first and last search positions, numeric search fallbacks, line/word counts, raw, universal, keep-end, and non-empty line extraction, whitespace word extraction, tab expansion, left and right partitioning, bounded left/right splitting, capitalization, case folding, title casing and title-case checks, ASCII, printable, identifier, and whitespace checks, ASCII digit/letter/case checks, reversal, case swapping, prefix/suffix checks and removal, any-prefix/any-suffix checks, whitespace and explicit-character trimming, left/right/center/zero padding, …) · number/text/decimal list
helpers with safe maybe first/last/index/pop, copying, fresh chaining, first-seen uniqueness, number-only stop-exclusive range generation, bounded repetition, bounded cycling, stepped slicing, count-based take/drop, tail take/drop, prefix/suffix predicates, indexed enumeration maps, function-value filtering, rejecting/filterfalse, selector compression, mapping, folding, predicate any/all, maybe-find, predicate first/all indexes, predicate counts, and take/drop-while, clamped slicing, membership predicates, explicit sum/product, cumulative sums/products/extrema, sum-product, arithmetic/geometric/harmonic means, covariance/correlation/regression, exclusive/inclusive quantiles, median, median-low/high, mode, plural-mode, population/sample variance, and population/sample standard-deviation helpers, extend/clear/insert/pop/remove/sort/reverse mutation, and aggregate variants, plus text-list cumulative extrema, yes/no list edge helpers, predicates, value-parameter count/index helpers, copying, fresh chaining, first-seen uniqueness, bounded repetition, bounded cycling, stepped slicing, count-based take/drop, tail take/drop, prefix/suffix predicates, indexed enumeration maps, filtering, rejecting/filterfalse, selector compression, mapping, folding, predicate any/all, maybe-find, predicate first/all indexes, predicate counts, take/drop-while, sorting, mode helpers, plural-mode helpers, and reversal · text-key and number-key map helpers for number, text, decimal, and yes/no values, including key membership, value membership, maybe lookup, fallback, fallback insertion, counted increment, copying, update merging, take-and-remove, take-with-fallback, and clear variants

Learn it in 15 minutes: [docs/TUTORIAL.md](docs/TUTORIAL.md). Every
construct and its Rust mapping: [docs/REFERENCE.md](docs/REFERENCE.md).
Formal details: [docs/SPEC.md](docs/SPEC.md). All error codes:
[docs/ERRORS.md](docs/ERRORS.md). Research plan:
[docs/RESEARCH.md](docs/RESEARCH.md). Release and hosting checklist:
[docs/RELEASE.md](docs/RELEASE.md). Typed web projects:
[docs/WEB.md](docs/WEB.md). Domain options:
[docs/DOMAINS.md](docs/DOMAINS.md). Seed benchmark harness:
[benchmarks/](benchmarks). Browseable evidence archive: [progress/](progress).
Eleven working programs: [examples/](examples).

## How it works

```
program.par ──parse──▶ AST ──check──▶ typed AST ──emit──▶ main.rs ──cargo──▶ native binary
                          (English diagnostics, JSON)        (zero crates, ~200-line prelude)
```

The compiler is ~2,500 lines of Python (Lark LALR grammar — yes, English is
LALR(1) if multi-word phrases are tokens). Every Parley construct maps to
exactly one Rust construct; heap values clone when stored, while read-only
heap parameters are borrowed in generated Rust so ownership never leaks into
the syntax; a line map points any residual rustc message back at your `.par`
line. `parley rust program.par` shows the generated code.

| | Python | Rust | **Parley** |
|---|---|---|---|
| an agent can write it without docs | ✓ | partly | ✓ (it's English) |
| catches type errors before running | ✗ | ✓ | ✓ |
| memory safety without GC | ✗ | ✓ | ✓ (via Rust) |
| native single-file binary | ✗ | ✓ | ✓ |
| machine-readable compiler errors | ✗ | ✓ (JSON) | ✓ (JSON + stable hints) |
| borrow checker in your face | — | yes | never (value semantics) |

## Status & roadmap

v0.3 is a working experiment — the full pipeline is real (all examples
compile and run; the test suite builds every feature as a native binary),
but the language is young and the syntax may still move. Known limits and
the plan:

- [x] richer `when` patterns (ranges, multiple values per arm) — v0.2
- [x] function values (`the function f`, `Rc<dyn Fn>` backed) — v0.2/v0.3
- [x] anonymous closures with captured values — v0.3
- [x] borrow-based passing for big values — v0.3
- [x] LSP diagnostics server (`parley-lsp`) — v0.3.1
- [x] package include roots (`parley_modules`, `PARLEY_PATH`) — v0.3.2
- [x] bundled standard packages (`std/math`, `std/text`) — v0.3.3
- [x] local package vendoring and lockfile (`parley package`) — v0.3.4
- [x] bundled list helpers (`std/list`) — v0.3.5
- [x] present maybe values (`some x`) — v0.3.6
- [x] bundled map helpers (`std/map`) — v0.3.7
- [x] local package skeletons (`parley package new`) — v0.3.8
- [x] setup doctor (`parley doctor --json`) — v0.3.9
- [x] custom runtime failures (`fail "message"`) — v0.3.10
- [x] runtime assertions (`assert condition, "message"`) — v0.3.11
- [x] benchmark CLI (`parley benchmark measure` / `summarize`) — v0.3.12
- [x] registry-backed packages (`parley package search --registry`) — v0.3.13
- [x] hosted starter package index (`/registry.json`) — v0.3.14
- [x] checksum-verified package installs and publish entries — v0.3.15
- [x] local package lock verification (`parley package verify`) — v0.3.16
- [x] package registry validation (`parley package check-registry`) — v0.3.17
- [x] package license and maintainer metadata for public registries — v0.3.18
- [x] package semantic-version governance — v0.3.19
- [x] benchmark manifest with Parley/Python/Rust reference sources — v0.3.20
- [x] package submission review (`parley package review`) — v0.3.21
- [x] signed package release entries (`--require-signatures`) — v0.3.22
- [x] language-neutral benchmark prompts (`parley benchmark prompt`) — v0.3.23
- [x] expanded stdlib helpers for text counting and decimal lists — v0.3.24
- [x] number-key helpers for bundled `std/map` — v0.3.25
- [x] maybe-returning first/last helpers for bundled `std/list` — v0.3.26
- [x] maybe-returning aggregate helpers for bundled `std/list` — v0.3.27
- [x] yes/no list predicates for bundled `std/list` — v0.3.28
- [x] decimal and yes/no value helpers for bundled `std/map` — v0.3.29
- [x] safe indexed lookup helpers for bundled `std/list` — v0.3.30
- [x] decimal helper variants for bundled `std/math` — v0.3.31
- [x] word and non-empty line extraction helpers for bundled `std/text` — v0.3.32
- [x] text replacement expression (`text replacing old with new`) — v0.3.33
- [x] text search position expression (`position of needle in text`) — v0.3.34
- [x] text occurrence count expression (`count of needle in text`) — v0.3.35
- [x] text character indexing (`item i of text`) — v0.3.36
- [x] safe text character helper (`maybe_character`) — v0.3.37
- [x] UTF-8 text slice helper (`text_slice`) — v0.3.38
- [x] clamped list slice helpers for bundled `std/list` — v0.3.39
- [x] extend/clear mutation helpers for bundled `std/list` — v0.3.40
- [x] deterministic map values expression (`values of m`) — v0.3.41
- [x] insert mutation helpers for bundled `std/list` — v0.3.42
- [x] maybe-returning pop helpers for bundled `std/list` — v0.3.43
- [x] first-match remove helpers for bundled `std/list` — v0.3.44
- [x] take-and-remove helpers for bundled `std/map` — v0.3.45
- [x] clear helpers for bundled `std/map` — v0.3.46
- [x] sort/reverse mutation helpers for bundled `std/list` — v0.3.47
- [x] prefix/suffix removal helpers for bundled `std/text` — v0.3.48
- [x] one-sided trim helpers for bundled `std/text` — v0.3.49
- [x] text padding helpers for bundled `std/text` — v0.3.50
- [x] centered text padding helper for bundled `std/text` — v0.3.51
- [x] ASCII text classification helpers for bundled `std/text` — v0.3.52
- [x] capitalization helper for bundled `std/text` — v0.3.53
- [x] yes/no list reverse helper for bundled `std/list` — v0.3.54
- [x] yes/no list sort helper for bundled `std/list` — v0.3.55
- [x] list copy helpers for bundled `std/list` — v0.3.56
- [x] yes/no list edge helpers for bundled `std/list` — v0.3.57
- [x] ASCII text case predicates for bundled `std/text` — v0.3.58
- [x] text case swapping for bundled `std/text` — v0.3.59
- [x] text title casing for bundled `std/text` — v0.3.60
- [x] text title-case predicate for bundled `std/text` — v0.3.61
- [x] ASCII text predicate for bundled `std/text` — v0.3.62
- [x] printable text predicate for bundled `std/text` — v0.3.63
- [x] whole-text whitespace predicate for bundled `std/text` — v0.3.64
- [x] raw line-list helper for bundled `std/text` — v0.3.65
- [x] prefix/suffix predicates for bundled `std/text` — v0.3.66
- [x] UTF-8 text reversal helper for bundled `std/text` — v0.3.67
- [x] text partition helper for bundled `std/text` — v0.3.68
- [x] right-side text partition helper for bundled `std/text` — v0.3.69
- [x] last text position helper for bundled `std/text` — v0.3.70
- [x] zero-fill text padding helper for bundled `std/text` — v0.3.71
- [x] tab expansion helper for bundled `std/text` — v0.3.72
- [x] universal newline split helper for bundled `std/text` — v0.3.73
- [x] right-side split helper for bundled `std/text` — v0.3.74
- [x] bounded split helper for bundled `std/text` — v0.3.75
- [x] whitespace-delimited word extraction for bundled `std/text` — v0.3.76
- [x] bounded replacement helper for bundled `std/text` — v0.3.77
- [x] numeric fallback text search helpers for bundled `std/text` — v0.3.102
- [x] explicit character-set trim helpers for bundled `std/text` — v0.3.103
- [x] kept line-split helper for bundled `std/text` — v0.3.104
- [x] identifier predicate for bundled `std/text` — v0.3.105
- [x] factorial helper for bundled `std/math` — v0.3.78
- [x] greatest-common-divisor and least-common-multiple helpers for bundled `std/math` — v0.3.79
- [x] combination and permutation count helpers for bundled `std/math` — v0.3.80
- [x] integer square root and perfect-square helpers for bundled `std/math` — v0.3.81
- [x] decimal closeness helper for bundled `std/math` — v0.3.106
- [x] decimal hypotenuse helper for bundled `std/math` — v0.3.107
- [x] decimal sign-copy helper for bundled `std/math` — v0.3.108
- [x] decimal angle conversion helpers for bundled `std/math` — v0.3.109
- [x] decimal math constant helpers for bundled `std/math` — v0.3.110
- [x] decimal point-distance helpers for bundled `std/math` — v0.3.111
- [x] product helpers for bundled number and decimal lists — v0.3.82
- [x] sum-product helpers for bundled number and decimal lists — v0.3.112
- [x] median helpers for bundled number and decimal lists — v0.3.113
- [x] median-low/high helpers for bundled number and decimal lists — v0.3.114
- [x] mode helpers for bundled number, text, decimal, and yes/no lists — v0.3.115
- [x] plural-mode helpers for bundled number, text, decimal, and yes/no lists — v0.3.116
- [x] population variance and standard-deviation helpers for bundled number and decimal lists — v0.3.117
- [x] sample variance and standard-deviation helpers for bundled number and decimal lists — v0.3.118
- [x] geometric and harmonic mean helpers for bundled number and decimal lists — v0.3.119
- [x] exclusive and inclusive quantile helpers for bundled number and decimal lists — v0.3.120
- [x] covariance and correlation helpers for bundled number and decimal lists — v0.3.121
- [x] linear regression helpers for bundled number and decimal lists — v0.3.122
- [x] cumulative sum helpers for bundled number and decimal lists — v0.3.123
- [x] cumulative product helpers for bundled number and decimal lists — v0.3.124
- [x] cumulative minimum/maximum helpers for bundled number and decimal lists — v0.3.125
- [x] cumulative minimum/maximum helpers for bundled text lists — v0.3.126
- [x] selector compression helpers for bundled lists — v0.3.127
- [x] fresh chain helpers for bundled lists — v0.3.128
- [x] bounded repeat helpers for bundled lists — v0.3.129
- [x] bounded cycle helpers for bundled lists — v0.3.130
- [x] stepped slice helpers for bundled lists — v0.3.131
- [x] count-based take/drop helpers for bundled lists — v0.3.132
- [x] indexed enumeration map helpers for bundled lists — v0.3.133
- [x] tail take/drop helpers for bundled lists — v0.3.134
- [x] list prefix/suffix predicates for bundled lists — v0.3.135
- [x] text case-fold helper for bundled `std/text` — v0.3.136
- [x] first-seen unique helpers for bundled lists — v0.3.137
- [x] stop-exclusive range helpers for bundled number lists — v0.3.138
- [x] borrow-safe evaluation of list/map mutation arguments — v0.3.139
- [x] progressive-disclosure agent skill with compact core — v0.3.140
- [x] benchmark-driven first-pass skill and parser hints — v0.3.141
- [x] sub-3k always-injected safe-forms skill — v0.3.142
- [x] benchmark-proven skill guardrails and literal diagnostics — v0.3.143
- [x] returning-function first-pass guardrail and diagnostics — v0.3.144
- [x] 1.6k progressive-disclosure agent core with preserved fallback — v0.3.145
- [x] transcript-backed natural aliases and executable 1.4k agent core — v0.3.146
- [x] checked postfix number conversion and scalar text joining — v0.3.147
- [x] postfix text conversion and destination-aware text-list insertion — v0.3.148
- [x] natural `and` helper signatures/calls with inferred list/map mutation — v0.3.149
- [x] one-shot general agent-instruction compression — v0.3.150
- [x] evidence-backed rollback to the proven reliability core — v0.3.151
- [x] contextual `position` identifiers from cross-task evidence — v0.3.152
- [x] contextual `modulo` alias from anti-primed cross-task evidence — v0.3.153
- [x] mutable range/list loop bindings preserve checker-to-Rust totality — v0.3.154
- [x] contextual value identifier `number` from five unrelated task families — v0.3.155
- [x] safe workflow library, starters, and file-to-file runner — v0.3.156
- [x] workflow fixtures and schema-2 named inputs — v0.3.157
- [x] Release Steward and checksummed three-product workflow catalog — v0.3.158
- [x] verified adaptive JSON/TOON agent-context packing — v0.3.159
- [x] typed HTTP/JSON and deterministic browser/WASM full-stack foundation — v0.4.0
- [x] measured token cuts: top-level program body and `otherwise` maybe fallback — v0.4.1
- [x] record sorting, generic `reversed`, and deterministic yes/no-aware printing — v0.4.2
- [x] real command-line programs: arguments, stdin, `maybe item`, `files in`,
      `the setting`, `the current time`, `fixed_decimal` — v0.4.3
- [x] typed JSON in the core language and key-ordered maps end to end — v0.4.4
- [x] membership helpers for bundled lists — v0.3.83
- [x] key membership helpers for bundled maps — v0.3.84
- [x] explicit list sum helpers and map copy helpers — v0.3.85
- [x] value-parameter count/index helpers for bundled yes/no lists — v0.3.86
- [x] update helpers for bundled maps — v0.3.87
- [x] fallback-insert helpers for bundled maps — v0.3.88
- [x] take-with-fallback helpers for bundled maps — v0.3.89
- [x] value membership helpers for bundled maps — v0.3.90
- [x] higher-order filter helpers for bundled lists — v0.3.91
- [x] higher-order map helpers for bundled lists — v0.3.92
- [x] higher-order any/all predicate helpers for bundled lists — v0.3.93
- [x] any-prefix and any-suffix helpers for bundled text — v0.3.94
- [x] predicate maybe-find helpers for bundled lists — v0.3.95
- [x] predicate count helpers for bundled lists — v0.3.96
- [x] same-type fold helpers for bundled lists — v0.3.97
- [x] take/drop-while helpers for bundled lists — v0.3.98
- [x] reject/filterfalse helpers for bundled lists — v0.3.99
- [x] predicate maybe-find-index helpers for bundled lists — v0.3.100
- [x] predicate all-index helpers for bundled lists — v0.3.101
- [ ] confirm token-efficiency parity vs Python/Rust at 10 replicates per cell
      (fresh-session harness and immutable HTML reports exist; optimization continues)

## Development

```bash
git clone https://github.com/ded-furby/parley-lang && cd parley-lang
pip install -e ".[dev]"
python3 -m pytest # e2e compiles real native and web binaries (needs cargo)
```

MIT licensed. Built by [Arjun Avtani](https://github.com/ded-furby) with
Claude.
