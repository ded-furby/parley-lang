---
name: parley
description: Write and test Parley (.par), an English-like compiled language. Use for Parley programs or plain-English compiled code.
---

# Parley

Write `solution.par` with 4-space blocks. Use only `./check`; follow hints.

```parley
to valid with line as text giving yesno:
    give back length of line is more than 0

to main:
    let count_input be ask for a number ""
    if count_input is nothing:
        say ""
    otherwise:
        let count be value of count_input
        repeat count times:
            let line be ask ""
            if (valid with line):
                say line
```

- `let x be value` creates; `set x to value` mutates or creates. `say`,
  `give back`/`return`, and `is nothing`/`has no value` work.
- Numeric input uses `ask for a number`; text conversion can use `x as number`.
  `say` emits one full line; assemble pieces in a list and join them first.
- Lists/text are 1-based. Use `an empty list of text`, `add x to xs`,
  `item i of xs`, `remove item i of xs`, `line split by ""`, and
  `parts joined with ","`.
- Maps: `a map from text to number`; `map contains key`;
  `set item key of map to value`; `item key of map`; sorted `keys of map`.
- Use `yesno`/`yes`/`no`; comparisons use `is [not/less than/at most/more
  than/at least]`. Literal braces are `"{{"` / `"}}"`.
- `for each i from 1 to length of xs` is inclusive. Names are `snake_case`.
  Parenthesize expression calls and complex repeat counts.

Full proven fallback: `references/core-v0.3.144.md`.
