# Parley language reference

Complete, in one page. Every Parley construct maps to exactly one Rust
construct — the right column is literally what `parley rust program.par`
prints (minus mechanical details like `i64` suffixes and helper plumbing).

## Program shape

A program is records, kinds (enums) and functions at the top level, with
indentation-based blocks (4 spaces). Execution starts at `to main:`.
Comments: `note: …` or `# …` to end of line.

## Types

| Parley | Rust | notes |
|---|---|---|
| `number` | `i64` | whole numbers |
| `decimal` | `f64` | |
| `text` | `String` | UTF-8; `length of` counts characters |
| `yesno` | `bool` | literals `yes` / `no` |
| `list of T` | `Vec<T>` | items count from 1 |
| `map from K to V` | `HashMap<K, V>` | K is `number` or `text`; `keys of` and `values of` are sorted by key |
| `maybe T` | `Option<T>` | `some x` or `nothing`; unwrap with `value of` |
| record | `struct` (derive Clone, Debug, PartialEq) | |
| kind | `enum` (derive Clone, Copy, Debug, PartialEq) | |
| `(function taking A, B giving R)` | `Rc<dyn Fn(A, B) -> R>` | a cloneable function value; both clauses optional |

**Value semantics:** storing text/lists/maps/records copies them. Function
calls keep the same behaviour, but generated Rust borrows read-only heap
parameters and clones inside the callee only when that parameter is stored or
mutated. Mutation crosses a function boundary only through `changing`
parameters (`&mut T`).

## Declarations

| Parley | Rust |
|---|---|
| `a point has x as number, y as number` | `struct Point { x: i64, y: i64 }` |
| `a mood is one of happy, grumpy` | `enum Mood { Happy, Grumpy }` |
| `to f with a as number giving number:` | `fn f(a: i64) -> i64 {` |
| `to f with xs as list of number:` | `fn f(xs: &Vec<i64>) {` |
| `to f with changing xs as list of number:` | `fn f(xs: &mut Vec<i64>) {` |

Variant names share one global namespace (so `happy` alone is unambiguous).

## Statements

| Parley | Rust |
|---|---|
| `let x be 5` | `let mut x: i64 = 5;` |
| `set x to 6` | `x = 6;` |
| `set p's x to 6` | `p.x = 6;` |
| `say expr` | `println!(…)` (yesno prints `yes`/`no`, maybe prints `nothing` or the value) |
| `if c:` / `otherwise if c:` / `otherwise:` | `if c { } else if c { } else { }` |
| `when x:` with `is v:` arms | `match` (enums) / `if`-chain (numbers, text, yesno) |
| `is 1, 2 or 3:` (multi-value arm) | `1 \| 2 \| 3 =>` / chained `\|\|` |
| `is 10 to 20:` (range arm, numeric `when`) | `x >= 10 && x <= 20` (inclusive) |
| `while c:` | `while c { }` |
| `repeat n times:` | `for _ in 0..n { }` |
| `for each x in xs:` | `for x in xs.clone() { }` (iterates a copy) |
| `for each i from 1 to 10:` | `for i in 1..=10 { }` (inclusive) |
| `stop` / `skip` | `break;` / `continue;` |
| `give back expr` | `return expr;` |
| `assert condition` / `assert condition, message` | catchable runtime check |
| `fail "message"` | catchable runtime failure |
| `add x to xs` | `xs.push(x);` |
| `remove item i of xs` | bounds-checked `xs.remove(i-1)` |
| `set item i of xs to v` | bounds-checked `xs[i-1] = v` |
| `set item k of m to v` | `m.insert(k, v);` |
| `write t to file p` / `append t to file p` | `std::fs` (failure stops the program; catchable) |
| `attempt:` / `if it failed:` | `catch_unwind` — see Errors below |
| `include "lib.par"` | splices the file before parsing; resolves relative paths, `parley_modules`, then `PARLEY_PATH` |
| `f with a, b` (statement call) | `f(a, b);` |

## Expressions

Precedence, loosest to tightest: `or` · `and` · `not` · comparisons ·
`split by`/`joined with`/`replacing … with …` · `plus minus` · `times divided-by %` ·
`to the power of` · prefix operations · `'s` field access.

| Parley | Rust | type |
|---|---|---|
| `a plus b` | `a + b` (texts: `format!`) | number/decimal/text/list |
| `a minus b`, `a times b` | `a - b`, `a * b` | numeric |
| `a divided by b` | guarded `a / b` | **always decimal**; ÷0 stops the program |
| `remainder of a divided by b` | guarded `a % b` | number |
| `a to the power of b` | `a.pow(b)` / `a.powf(b)` | |
| `x is y` / `x is not y` | `==` / `!=` | yesno |
| `is more than / less than / at least / at most` | `> < >= <=` | yesno |
| `xs contains x` | `.contains(…)` (list, map key, or substring) | yesno |
| `t starts with p` / `t ends with p` | `.starts_with` / `.ends_with` | yesno |
| `t split by ","` | `.split(…).collect()` | list of text |
| `xs joined with ", "` | `.join(…)` (list of text) | text |
| `t replacing old with new` | `.replace(old, new)` | text |
| `position of needle in t` | UTF-8-safe substring search | maybe number |
| `count of needle in t` | non-overlapping substring count | number |
| `"{x} and {y}"` | `format!("{} and {}", x, y)` | text |
| `(f with a, b)` | `f(a, b)` — calls in expressions take parens | |
| `bob's name` | `bob.name` | field type |
| `item i of xs` / `item i of t` / `item k of m` | bounds/presence-checked access (1-based) | element/text/value |
| `a list of 1, 2, 3` | `vec![1, 2, 3]` | directly after be/to/give back, or in parens |
| `an empty list of text` | `Vec::<String>::new()` | |
| `a map from text to number` | `HashMap::new()` | |
| `a point with x 1, y 2` | `Point { x: 1, y: 2 }` | all fields required |
| `nothing` | `None` | |
| `some x` | `Some(x)` | maybe of x's type |
| `value of m` | checked unwrap | inner type |
| `the error` | last runtime error text | text |
| `the function f` | `Rc::new(move |…| f(…))` | a named function value (no `changing` params) |
| `a function taking x as number giving number: ...` | `Rc::new(move |x: i64| -> i64 { ... })` | anonymous closure with captured values |

A variable holding a function value is called exactly like a function:
`(f with x)` in expressions, `f with x` as a statement. Function values
cannot be compared, turned into text, or said.

Anonymous functions capture outside variables by value when they are created.
Changing the original variable later does not change the captured value.
Closures can read captured values, but cannot `set` them; give back a changed
value and assign it outside if you need that flow.

### Built-in operations

| Parley | works on | gives |
|---|---|---|
| `length of x` | text, list, map | number |
| `sum of xs` | list of number/decimal | same |
| `smallest of xs` / `largest of xs` | list of number/decimal/text | element |
| `sorted xs` / `reversed xs` | list (reversed also text) | same |
| `uppercase of t` / `lowercase of t` / `trimmed t` | text | text |
| `absolute of n` | number/decimal | same |
| `rounded x` / `floor of x` / `ceiling of x` | decimal (number passes through) | number |
| `square root of x` | number/decimal | decimal |
| `keys of m` | map | sorted list of keys |
| `values of m` | map | list of values in sorted-key order |
| `text from x` | anything | text |
| `number from x` | text → **maybe** number; decimal → number | |
| `decimal from x` | text → **maybe** decimal; number → decimal | |
| `ask "prompt"` | — | text (end of input stops the program) |
| `ask for a number "prompt"` | — | maybe number |
| `read file "p"` | — | maybe text |
| `a random number from 1 to 6` | — | number (inclusive) |

## Errors

Runtime failures (`assert`, `fail`, divide by zero, item out of range,
`value of` nothing, file write trouble, end of input) **stop the program**
with a one-line English message on stderr and exit code 1 — unless wrapped:

```parley
attempt:
    assert score is at least 0, "score cannot be negative"
if it failed:
    say the error
```

`assert` needs a yes/no condition, and its optional message must be text.
`fail` needs a text expression. `give back`, `stop`, and `skip` cannot jump
out of an `attempt:` block.

## Scoping and naming rules

* A `let` lives until the end of its block; no shadowing, no redeclaring.
* `set` only changes existing variables.
* Names are letters/digits/underscores and cannot be Parley vocabulary words
  (`is`, `item`, `of`, `to`, `a`, `sorted`, …) — the checker lists the exact
  conflict and suggests alternatives (P209).
* Multi-word phrases are part of the grammar: write them with spaces
  (`is more than`), any number of spaces between the words.

## The agent contract

`parley check program.par --json` emits:

```json
{"ok": false, "diagnostics": [{"code": "P204", "message": "…", "file": "…",
  "line": 4, "col": 9, "hint": "Did you mean \"score\"?",
  "replacement": null, "severity": "error"}]}
```

Codes are stable (see [ERRORS.md](ERRORS.md)); `parley explain P204` prints
the catalog entry. The intended loop: **check → apply hint → re-check → run.**

## Setup doctor

`parley doctor` checks the installed Parley version, Python version, Rust
`cargo` backend, bundled standard packages, and local package state. Use
`parley doctor --json` in scripts or agent setup checks; it returns a
machine-readable report with an `ok` field and one entry per check.

## Benchmark research

From a source checkout, `parley benchmark prompt --task hello --language parley`
renders the language-neutral prompt for one seed task. Omit `--task` to render
all prompts, or use `--format json` for automation. `parley benchmark measure`
runs the Phase 1 seed corpus metrics for Parley, Python, and Rust references.
It forwards the same options as `benchmarks/measure.py`, including
`--format json`, `--no-check`, `--languages`, `--output`, and
`--llm-tokenizer`. Use `parley benchmark append` to record one generated
attempt row in JSONL, and `parley benchmark summarize --log runs.jsonl` to
aggregate attempts by task/language/model.

## Editor integration

`parley-lsp` starts a stdio Language Server Protocol server. It publishes the
same parser/checker diagnostics and stable P-codes as `parley check --json` for
open `.par` documents. The initial server supports `initialize`,
`textDocument/didOpen`, `textDocument/didChange`, `textDocument/didClose`, and
`shutdown`.

## Bundled packages

Use `include "std/math"` for small numeric helpers:

| Function | Gives |
|---|---|
| `clamped with n, low, high` | `n` limited to the inclusive range |
| `clamped_decimal with n, low, high` | decimal `n` limited to the inclusive range |
| `between with n, low, high` | yes/no range check |
| `between_decimal with n, low, high` | yes/no decimal range check |
| `percent_of with part, whole` | decimal percentage |
| `percent_of_decimal with part, whole` | decimal percentage from decimal inputs |

Use `include "std/text"` for small text helpers:

| Function | Gives |
|---|---|
| `is_blank with t` | yes when `trimmed t` is empty |
| `maybe_character with t, index` | maybe one-character text at a 1-based UTF-8 character index |
| `text_slice with t, first, last` | text from clamped 1-based inclusive UTF-8 character bounds, or empty text for reversed/empty ranges |
| `repeated_text with t, count` | text repeated `count` times |
| `surrounded_with with t, wrapper` | wrapper + text + wrapper |
| `line_count with t` | number of newline-separated lines, or 0 for empty text |
| `nonempty_line_count with t` | number of lines whose trimmed text is not empty |
| `nonempty_lines with t` | list of trimmed, non-blank lines |
| `word_count with t` | number of non-blank space-separated words |
| `words_of with t` | list of non-blank space-separated words |

Use `include "std/list"` for common list helpers:

| Function | Gives |
|---|---|
| `first_number with xs` / `last_number with xs` | first or last number |
| `maybe_first_number with xs` / `maybe_last_number with xs` | maybe first or last number |
| `maybe_item_number with xs, index` | maybe number at a 1-based index |
| `list_slice_number with xs, first, last` | list of number from clamped 1-based inclusive bounds |
| `extend_number with changing xs, more` | append every number from `more` to `xs` |
| `clear_number with changing xs` | remove every item from `xs` |
| `insert_number with changing xs, index, value` | insert `value` before the 1-based index, clamped to front/end |
| `count_number with xs, n` | occurrences of `n` |
| `index_number with xs, n` | maybe 1-based index of `n` |
| `average_number with xs` | decimal average |
| `maybe_smallest_number with xs` / `maybe_largest_number with xs` | maybe smallest or largest number |
| `maybe_average_number with xs` | maybe decimal average |
| `first_text with xs` / `last_text with xs` | first or last text |
| `maybe_first_text with xs` / `maybe_last_text with xs` | maybe first or last text |
| `maybe_item_text with xs, index` | maybe text at a 1-based index |
| `list_slice_text with xs, first, last` | list of text from clamped 1-based inclusive bounds |
| `extend_text with changing xs, more` | append every text value from `more` to `xs` |
| `clear_text with changing xs` | remove every item from `xs` |
| `insert_text with changing xs, index, value` | insert `value` before the 1-based index, clamped to front/end |
| `count_text with xs, t` | occurrences of `t` |
| `index_text with xs, t` | maybe 1-based index of `t` |
| `maybe_smallest_text with xs` / `maybe_largest_text with xs` | maybe smallest or largest text |
| `first_decimal with xs` / `last_decimal with xs` | first or last decimal |
| `maybe_first_decimal with xs` / `maybe_last_decimal with xs` | maybe first or last decimal |
| `maybe_item_decimal with xs, index` | maybe decimal at a 1-based index |
| `list_slice_decimal with xs, first, last` | list of decimal from clamped 1-based inclusive bounds |
| `extend_decimal with changing xs, more` | append every decimal from `more` to `xs` |
| `clear_decimal with changing xs` | remove every item from `xs` |
| `insert_decimal with changing xs, index, value` | insert `value` before the 1-based index, clamped to front/end |
| `count_decimal with xs, d` | occurrences of `d` |
| `index_decimal with xs, d` | maybe 1-based index of `d` |
| `average_decimal with xs` | decimal average |
| `maybe_smallest_decimal with xs` / `maybe_largest_decimal with xs` | maybe smallest or largest decimal |
| `maybe_average_decimal with xs` | maybe decimal average |
| `all_yes with xs` / `any_yes with xs` | yes/no aggregate over a `list of yesno`; empty lists give yes for `all_yes` and no for `any_yes` |
| `maybe_item_yesno with xs, index` | maybe yes/no value at a 1-based index |
| `list_slice_yesno with xs, first, last` | list of yes/no from clamped 1-based inclusive bounds |
| `extend_yesno with changing xs, more` | append every yes/no value from `more` to `xs` |
| `clear_yesno with changing xs` | remove every item from `xs` |
| `insert_yesno with changing xs, index, value` | insert `value` before the 1-based index, clamped to front/end |
| `count_yes with xs` / `count_no with xs` | count yes or no values |
| `index_yes with xs` / `index_no with xs` | maybe 1-based index of the first yes or no |

Use `include "std/map"` for common map helpers:

| Function | Gives |
|---|---|
| `number_at with m, key` | maybe number from a `map from text to number` |
| `number_or with m, key, fallback` | number or fallback |
| `add_count with changing m, key` | increments a text-key count in place |
| `text_at with m, key` | maybe text from a `map from text to text` |
| `text_or with m, key, fallback` | text or fallback |
| `decimal_at with m, key` | maybe decimal from a `map from text to decimal` |
| `decimal_or with m, key, fallback` | decimal or fallback |
| `yesno_at with m, key` | maybe yes/no from a `map from text to yesno` |
| `yesno_or with m, key, fallback` | yes/no or fallback |
| `number_key_number_at with m, key` | maybe number from a `map from number to number` |
| `number_key_number_or with m, key, fallback` | number or fallback |
| `add_number_key_count with changing m, key` | increments a number-key count in place |
| `number_key_text_at with m, key` | maybe text from a `map from number to text` |
| `number_key_text_or with m, key, fallback` | text or fallback |
| `number_key_decimal_at with m, key` | maybe decimal from a `map from number to decimal` |
| `number_key_decimal_or with m, key, fallback` | decimal or fallback |
| `number_key_yesno_at with m, key` | maybe yes/no from a `map from number to yesno` |
| `number_key_yesno_or with m, key, fallback` | yes/no or fallback |

## Local packages

`parley package new name` creates `name/main.par`, a starter local package
that can be installed into a project.

`parley package install name source --version 1.0.0` copies a local package
directory or `.par` file into `parley_modules/name/`. Package names may contain
letters, numbers, dashes, underscores, and dots, and must start with a letter or
number. Package versions must use semantic `X.Y.Z` form, with optional
prerelease/build suffixes such as `1.2.3-beta.1+build.5`. Directory packages
need a `main.par`. Installs are recorded in `parley.lock.json` with the
package SHA-256, and `parley package list` prints the locked package names,
versions, and vendored paths.

Registry manifests use JSON:

```json
{"schema_version": 1, "packages": {"mathkit": {
  "version": "1.0.0", "source": "../mathkit", "description": "math helpers",
  "license": "MIT", "maintainer": "Your Name <https://example.com>",
  "sha256": "..."
}}}
```

`parley package search --registry registry.json` lists available packages, and
`parley package install mathkit --registry registry.json` vendors the package
named by the registry. Relative registry sources resolve from the manifest's
directory. A source may be a package directory, a single `.par` file, `file://`
URL, or an `http(s)` URL pointing at a `.par` file. When the registry entry has
`sha256`, install verifies the package before replacing an existing vendored
copy and writes the digest to `parley.lock.json`.

Use `parley package publish mathkit path --version 1.0.0 --description
"math helpers" --license MIT --maintainer "Your Name <https://example.com>"
--source packages/mathkit/main.par` to print a registry-ready JSON entry with
license, maintainer, and the deterministic package SHA-256. Directory packages
hash every file by relative path and content; single-file packages hash the
installed `main.par` layout. Add `--signing-key release-2026 --signing-secret
SECRET` to include an HMAC-SHA256 release signature in the entry.

Use `parley package review mathkit path --version 1.0.0 --description
"math helpers" --license MIT --maintainer "Your Name <https://example.com>"`
before submitting a package to a registry. It validates required metadata,
computes the deterministic SHA-256, parses every package `.par` file, and
prints the registry entry that would be submitted. It accepts the same
`--signing-key` / `--signing-secret` options as `publish`.

Use `parley package verify` after checkout, install, or before release. It
reads `parley.lock.json`, recomputes each vendored package digest, prints `OK`
for packages that still match, and exits non-zero if a package is missing, has
no recorded `sha256`, or has been modified locally.

Use `parley package check-registry registry.json` before hosting a registry.
It validates package names, required `version`, `description`, `license`,
`maintainer`, `source`, and `sha256` fields, resolves each source from the
registry location, recomputes the package digest, and exits non-zero if any
entry is incomplete, has a non-semantic version, or has changed.
Add `--require-signatures --signing-secret SECRET` to reject unsigned or
tampered package entries before hosting a signed registry.

The public starter index is hosted with the website at
`https://ded-furby.github.io/parley-lang/registry.json`.
