---
name: parley
description: Write and test Parley (.par), an English-like compiled language. Use for Parley programs or plain-English compiled code.
---

# Parley

Write `solution.par`; indent blocks 4 spaces. Use only `./check`; follow hints.

```parley
to valid with line as text giving yesno:
    give back length of line is more than 0

let count be ask for a number "" otherwise 0
repeat count times:
    let line be ask ""
    if (valid with line):
        say line
```

- Top-level statements are the program body; never add `to main:` too.
  Included files contain only functions, records, and enums.
- `let x be value` creates; `set x to value` mutates/creates. `say`, `give back`
  /`return`, and `is nothing`/`has no value` work.
- Maybes from `ask for a number`, `number from text`, `read file`, `files in d`,
  or `maybe item i of x` unwrap as `m otherwise default`. `number from decimal`
  is a plain truncated number—never add `otherwise`. Text can use `x as number`.
- `the arguments` and `the input` are `list of text` (argv and stdin lines).
  Use `the input` or `ask`, never both.
- `say` emits one line. Escape quotes inside `{…}` as
  `"{name otherwise \"none\"}"`; Literal braces are `"{{"` / `"}}"`.
- Lists/text are 1-based: `an empty list of text`, `add x to xs`, `item i of xs`,
  `remove item i of xs`, `line split by ""`, `parts joined with ","`, and
  record `sorted xs by field`.
- Maps: `a map from text to number`; `map contains key`; set/get with
  `set item key of map to value` / `item key of map`; sorted `keys of map`.
- JSON is typed: declare a record; `a config from json t` gives maybe config,
  rejecting unknown/missing fields; `x as json` gives text.
- `any name` is a type variable, e.g. `to head_or with xs as list of any item,
  d as any item giving any item:`.
- Stdlib: `include "std/text"`, `std/time`, `std/list`, `std/map`, `std/math`.
- Use `yesno`/`yes`/`no`; compare with `is` plus `not`, `less than`, `at most`,
  `more than`, or `at least`. Loops `for each i from 1 to length of xs` include
  both ends. Names are `snake_case`. Parenthesize expression calls/repeat counts.
- Repairs: edit the smallest owning module; leave correct callers/entrypoints.

Full proven fallback: `references/core-v0.3.144.md`.
