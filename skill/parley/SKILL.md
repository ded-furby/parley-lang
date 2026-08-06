---
name: parley
description: Write and test Parley (.par), an English-like compiled language. Use for Parley programs or plain-English compiled code.
---

# Parley

Write `solution.par` with 4-space blocks. Use only `./check`; follow hints.

```parley
to valid with line as text giving yesno:
    give back length of line is more than 0

let count be ask for a number "" otherwise 0
repeat count times:
    let line be ask ""
    if (valid with line):
        say line
```

- Top-level statements are the program body; never also write `to main:`.
  Included files hold only functions, records, and enums.
- `let x be value` creates; `set x to value` mutates or creates. `say`,
  `give back`/`return`, and `is nothing`/`has no value` work.
- A `maybe` (`ask for a number`, `number from t`, `read file`, `files in d`,
  `maybe item i of x`) unwraps as `m otherwise default`; use `is nothing` only
  when missing needs other code. Text conversion can use `x as number`.
- `the arguments` and `the input` are `list of text`: command-line words and
  every stdin line. Use `the input` or `ask`, never both.
- `say` emits one full line; assemble pieces in a list and join them first.
  Escape quotes inside `{…}`: `"{name otherwise \"none\"}"`.
- Lists/text are 1-based: `an empty list of text`, `add x to xs`,
  `item i of xs`, `remove item i of xs`, `line split by ""`,
  `parts joined with ","`, `sorted xs by field` for records.
- Maps: `a map from text to number`; `map contains key`;
  `set item key of map to value`; `item key of map`; sorted `keys of map`.
- JSON is typed: declare a record, then `a config from json t` (maybe config,
  strict about unknown/missing fields) and `x as json` (text).
- Stdlib: `include "std/text"` (padding, `fixed_decimal`), `std/time`
  (`timestamp_text with the current time`), `std/list`, `std/map`, `std/math`.
- Use `yesno`/`yes`/`no`; comparisons use `is [not/less than/at most/more
  than/at least]`. Literal braces are `"{{"` / `"}}"`.
- `for each i from 1 to length of xs` is inclusive. Names are `snake_case`.
  Parenthesize expression calls and complex repeat counts.

Full proven fallback: `references/core-v0.3.144.md`.
