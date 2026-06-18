# Parley specification (v0.3)

This document defines the language precisely enough to reimplement it.
For learning, read [TUTORIAL.md](TUTORIAL.md); for daily use,
[REFERENCE.md](REFERENCE.md).

## 1. Design goals

1. **Agents are the primary authors.** The grammar favours patterns language
   models already know deeply: English phrases, Python-style indentation,
   one canonical way to write each construct.
2. **Rust-grade output.** Compilation is a total function onto a memory-safe
   subset of Rust; rustc provides memory safety and native code generation.
3. **No prose-parsing.** Every tool surface (checker, build errors, runtime
   failures) is available as structured JSON with stable codes.
4. **Determinism.** Same program, same behaviour: map iteration is sorted,
   integer overflow and division by zero are defined (they stop the program),
   there is no undefined behaviour.

## 2. Lexical structure

* Source is UTF-8; string contents may be any text.
* Blocks are indentation-delimited (Python rules; 4 spaces conventional,
  tabs count as 8). Newlines end statements. Inside parentheses, newlines
  are insignificant.
* Comments run from `note:` or `#` to end of line.
* Multi-word phrases (`is more than`, `a list of`, `to the power of`, …) are
  single lexical tokens, matched with one-or-more spaces between words and a
  word boundary at the end. This is what makes English LALR(1)-parsable.
* Keyword tokens are matched contextually: a word like `length` may name a
  variable because `length of` only forms a token where an expression is
  expected. Words that are complete tokens by themselves (`is`, `of`, `item`,
  `a`, `sorted`, …) are reserved; the checker rejects them as names (P209).
* Literals: `INT /\d+/`, `FLOAT /\d+\.\d+/`, strings
  `"(\\.|[^"\\\n])*"` with escapes `\n \t \r \" \\` and `{expr}`
  interpolation (`{{`/`}}` for literal braces).

## 3. Grammar

The complete grammar is [`parley/grammar.lark`](../parley/grammar.lark)
(Lark dialect, LALR(1) + indentation post-lexer). It is normative; the
parse-relevant highlights:

* **rhs rule.** List literals (`a list of 1, 2`), empty containers, and record
  constructions appear only (a) directly after `be`, `to`, or `give back`, or
  (b) inside parentheses. This keeps their commas unambiguous against
  argument and field commas with one token of lookahead.
* **Calls.** Statement calls are bare: `f with a, b`. Expression calls are
  parenthesised: `(f with a, b)`. Zero-parameter functions are called by
  bare name.
* **repeat counts** are atoms (`repeat n times:`); parenthesise anything
  bigger: `repeat (n plus 1) times:` — this disambiguates against the
  `times` multiplication operator.

## 4. Static semantics

* **Types** as in REFERENCE.md. No implicit conversions except
  number → decimal promotion (at assignment, argument, return and mixed
  arithmetic positions). Division always yields decimal.
* **Scopes.** One namespace for variables; functions, record names, enum
  names and variants are global. A `let` binds until the end of its block;
  redeclaration and shadowing are errors (P209). `set` requires an existing
  binding (P211).
* **Map keys** are `number` or `text` (P309) so iteration can be sorted.
* **`when`** over an enum must be exhaustive or carry `otherwise:` (P208);
  over yesno, covering `yes` and `no` counts as exhaustive; over numbers and
  text, `otherwise:` is mandatory. An arm may list several patterns
  (`is 1, 2 or 3:`) and, when the subject is numeric, inclusive ranges
  (`is 10 to 20:`); range ends are literals of the subject's type, smaller
  first (P312).
* **Function values.** `the function f` is a value of type
  `(function taking …  giving …)`, represented as a cloneable Rust
  `Rc<dyn Fn...>`. Only plain defined functions qualify: not `main` and not
  functions with `changing` parameters (P313). A variable holding a function
  value is called with the ordinary call forms. Function values cannot be
  compared, converted to text, or said (P301).
* **Anonymous functions.** `a function taking x as number giving number:`
  creates a function value. Its indented body follows the same statement rules
  as a named function body. Outside variables read by the body are captured by
  value at creation time; later changes to the original variable do not affect
  the closure. Captured values cannot be changed inside the closure (P314).
* **Functions** with `giving T` must give back on every path (P304).
  `changing` parameters require a plain variable argument of exactly the
  parameter's type (P305).
* **`attempt`** bodies may not `give back`, and may not `stop`/`skip` loops
  that started outside the attempt (P310).
* The checker is total: any program it accepts must compile under rustc.
  A rustc rejection is a Parley bug, surfaced as P901 with the source line.

## 5. Dynamic semantics

* **Value model.** Parley exposes value semantics: assignment, construction,
  return, and `for each` iteration copy heap values. In generated Rust,
  read-only non-`changing` heap parameters are borrowed and are cloned only if
  the callee stores or mutates its local parameter. The only user-visible
  aliasing is `changing` parameters, which are exclusive mutable borrows for
  the call.
* **Numbers** are 64-bit (`i64`/`f64`). Integer overflow stops the program in
  debug builds (`parley run`); release builds (`parley build`) wrap.
  `a divided by b` is IEEE-754 division after promotion, with `b = 0`
  stopping the program.
* **Failures.** These stop the program with an English message and exit
  code 1: division/remainder by zero, out-of-range `item`, `value of`
  nothing, smallest/largest of an empty list, negative `square root of`,
  negative integer powers, overflowing powers, file write failures, reading
  input past end-of-file. An enclosing `attempt:` catches them; `the error`
  then holds the message.
* **I/O.** `say` writes a line to stdout. `ask` prompts on stdout and reads
  one line from stdin. File operations are whole-file. `a random number` is
  a non-cryptographic xorshift seeded from the clock.

## 6. Compilation model

```
program.par ──parse──▶ AST ──check──▶ typed AST ──emit──▶ main.rs ──cargo──▶ native binary
                │            │                                  │
                ▼            ▼                                  ▼
              P1xx         P2xx/P3xx                 P9xx (mapped back by line)
```

* The emitter writes a single `main.rs`: a fixed helper prelude (≈200 lines,
  zero external crates), one item per Parley declaration, and a `fn main`
  that installs an English panic handler around the program.
* A line map (rust line → parley file/line) accompanies emission; any
  residual rustc diagnostic is translated through it.
* `include "x"` is textual. It first resolves `x` relative to the including
  file, then as `parley_modules/x`, then through `PARLEY_PATH` roots. Package
  directories load `main.par`.
* Build directory: `.parley-build/<program>/` with a shared cargo target dir
  in `.parley-build/target/`.

## 7. Stability

v0.3 is an experiment. Syntax may change; error codes are append-only.
Known limits: no generics for user functions, no methods, single-threaded,
and no versioned package manager. Function values exist for named functions
without `changing` parameters and anonymous functions with value captures. See
the README roadmap.
