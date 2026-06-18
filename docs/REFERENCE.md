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
| `map from K to V` | `HashMap<K, V>` | K is `number` or `text`; `keys of` is sorted |
| `maybe T` | `Option<T>` | literal `nothing`; unwrap with `value of` |
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
`split by`/`joined with` · `plus minus` · `times divided-by %` ·
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
| `"{x} and {y}"` | `format!("{} and {}", x, y)` | text |
| `(f with a, b)` | `f(a, b)` — calls in expressions take parens | |
| `bob's name` | `bob.name` | field type |
| `item i of xs` / `item k of m` | bounds/presence-checked access (1-based) | element |
| `a list of 1, 2, 3` | `vec![1, 2, 3]` | directly after be/to/give back, or in parens |
| `an empty list of text` | `Vec::<String>::new()` | |
| `a map from text to number` | `HashMap::new()` | |
| `a point with x 1, y 2` | `Point { x: 1, y: 2 }` | all fields required |
| `nothing` | `None` | |
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
| `text from x` | anything | text |
| `number from x` | text → **maybe** number; decimal → number | |
| `decimal from x` | text → **maybe** decimal; number → decimal | |
| `ask "prompt"` | — | text (end of input stops the program) |
| `ask for a number "prompt"` | — | maybe number |
| `read file "p"` | — | maybe text |
| `a random number from 1 to 6` | — | number (inclusive) |

## Errors

Runtime failures (divide by zero, item out of range, `value of` nothing,
file write trouble, end of input) **stop the program** with a one-line English
message on stderr and exit code 1 — unless wrapped:

```parley
attempt:
    risky stuff
if it failed:
    say the error
```

`give back`, `stop`, and `skip` cannot jump out of an `attempt:` block.

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
| `between with n, low, high` | yes/no range check |
| `percent_of with part, whole` | decimal percentage |

Use `include "std/text"` for small text helpers:

| Function | Gives |
|---|---|
| `is_blank with t` | yes when `trimmed t` is empty |
| `repeated_text with t, count` | text repeated `count` times |
| `surrounded_with with t, wrapper` | wrapper + text + wrapper |

## Local packages

`parley package install name source --version 1.0.0` copies a local package
directory or `.par` file into `parley_modules/name/`. Package names may contain
letters, numbers, dashes, underscores, and dots, and must start with a letter or
number. Directory packages need a `main.par`. Installs are recorded in
`parley.lock.json`, and `parley package list` prints the locked package names,
versions, and vendored paths.
