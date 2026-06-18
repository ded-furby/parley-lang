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
```

```
$ parley run cats.par
Felix has 9 lives left
naps today: 4

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

For the research harness, run `parley benchmark measure --format json` from a
source checkout to produce the Parley/Python/Rust seed-corpus metrics, and
`parley benchmark summarize --log runs.jsonl --format json` to review recorded
agent attempts.

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
(sorted iteration), `maybe` options (`some x`, `nothing`, `value of`) · functions with `changing` (mutable)
parameters and recursion · string interpolation `"{x}"` ·
custom runtime failures with `fail "message"` ·
runtime assertions with `assert condition, "message"` ·
`attempt:`/`if it failed:` error handling with `the error` · file I/O ·
stdin `ask` · random numbers · bundled `std/math`, `std/text`, `std/list`, and `std/map`
packages · multi-file programs via `include`, `parley_modules`, and `PARLEY_PATH` package roots ·
local package vendoring with `parley package` and `parley.lock.json` ·
setup checks with `parley doctor` ·
`stop`/`skip`/`give back` · whole-number and decimal math with guarded
division, powers, roots · a text toolbox (`split by`, `joined with`,
`uppercase of`, `contains`, …)

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
- [ ] a formal token-efficiency benchmark vs Python/Rust/Zero (seed corpus,
      optional tokenizer counts, CLI, and run logging exist; agent runs still planned)
- [ ] remote package registry

## Development

```bash
git clone https://github.com/ded-furby/parley-lang && cd parley-lang
pip install -e ".[dev]"
pytest            # 158 tests; e2e compiles real binaries (needs cargo)
```

MIT licensed. Built by [Arjun Avtani](https://github.com/ded-furby) with
Claude.
