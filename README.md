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
division, powers, roots · a text toolbox (`split by`, `joined with`,
`replacing … with …`, `position of … in …`, `count of … in …`,
`item i of text`, safe character lookup and slicing, `uppercase of`,
`contains`, line/word counts, word/line extraction, capitalization, ASCII digit/letter checks, prefix/suffix removal, one-sided trimming, left/right/center padding, …) · number/text/decimal list
helpers with safe maybe first/last/index/pop, clamped slicing, extend/clear/insert/pop/remove/sort/reverse mutation, and aggregate variants, plus yes/no list predicates and reversal · text-key and number-key map helpers for number, text, decimal, and yes/no values, including maybe lookup, fallback, counted increment, take-and-remove, and clear variants

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
- [ ] a formal token-efficiency benchmark vs Python/Rust/Zero (seed corpus,
      optional tokenizer counts, CLI, and run logging exist; agent runs still planned)

## Development

```bash
git clone https://github.com/ded-furby/parley-lang && cd parley-lang
pip install -e ".[dev]"
pytest            # 207 tests; e2e compiles real binaries (needs cargo)
```

MIT licensed. Built by [Arjun Avtani](https://github.com/ded-furby) with
Claude.
