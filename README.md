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

to main:
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
json` to review recorded agent attempts.

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
stdin `ask` · random numbers · bundled `std/math`, `std/text`, `std/list`, and `std/map`
packages · multi-file programs via `include`, `parley_modules`, and `PARLEY_PATH` package roots ·
local and registry-backed package vendoring with SHA-256 lock metadata and
`parley package verify`, plus registry validation with
`parley package check-registry` and dry-run submission review with
`parley package review`, and optional HMAC-SHA256 release signatures, via
`parley package` and `parley.lock.json` ·
setup checks with `parley doctor` ·
`stop`/`skip`/`give back` · whole-number and decimal math helpers with guarded
division, powers, roots, math constants, integer square roots, perfect-square checks, factorials, GCD/LCM, combinations/permutations, decimal closeness, hypotenuse, point-distance helpers, sign-copy checks, and angle conversions · a text toolbox (`split by`, `joined with`,
`replacing … with …`, bounded replacement, `position of … in …`, `count of … in …`,
`item i of text`, safe character lookup and slicing, `uppercase of`,
`contains`, first and last search positions, numeric search fallbacks, line/word counts, raw, universal, keep-end, and non-empty line extraction, whitespace word extraction, tab expansion, left and right partitioning, bounded left/right splitting, capitalization, title casing and title-case checks, ASCII, printable, identifier, and whitespace checks, ASCII digit/letter/case checks, reversal, case swapping, prefix/suffix checks and removal, any-prefix/any-suffix checks, whitespace and explicit-character trimming, left/right/center/zero padding, …) · number/text/decimal list
helpers with safe maybe first/last/index/pop, copying, function-value filtering, rejecting/filterfalse, mapping, folding, predicate any/all, maybe-find, predicate first/all indexes, predicate counts, and take/drop-while, clamped slicing, membership predicates, explicit sum/product, sum-product, and median helpers, extend/clear/insert/pop/remove/sort/reverse mutation, and aggregate variants, plus yes/no list edge helpers, predicates, value-parameter count/index helpers, copying, filtering, rejecting/filterfalse, mapping, folding, predicate any/all, maybe-find, predicate first/all indexes, predicate counts, take/drop-while, sorting, and reversal · text-key and number-key map helpers for number, text, decimal, and yes/no values, including key membership, value membership, maybe lookup, fallback, fallback insertion, counted increment, copying, update merging, take-and-remove, take-with-fallback, and clear variants

Learn it in 15 minutes: [docs/TUTORIAL.md](docs/TUTORIAL.md). Every
construct and its Rust mapping: [docs/REFERENCE.md](docs/REFERENCE.md).
Formal details: [docs/SPEC.md](docs/SPEC.md). All error codes:
[docs/ERRORS.md](docs/ERRORS.md). Research plan:
[docs/RESEARCH.md](docs/RESEARCH.md). Release and hosting checklist:
[docs/RELEASE.md](docs/RELEASE.md). Domain options:
[docs/DOMAINS.md](docs/DOMAINS.md). Seed benchmark harness:
[benchmarks/](benchmarks). Eleven working programs: [examples/](examples).

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
- [ ] a formal token-efficiency benchmark vs Python/Rust/Zero (seed corpus,
      optional tokenizer counts, CLI, and run logging exist; agent runs still planned)

## Development

```bash
git clone https://github.com/ded-furby/parley-lang && cd parley-lang
pip install -e ".[dev]"
pytest            # 229 tests; e2e compiles real binaries (needs cargo)
```

MIT licensed. Built by [Arjun Avtani](https://github.com/ded-furby) with
Claude.
