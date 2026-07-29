---
name: parley
description: Write, check, and run Parley programs (.par files), an English-like language that compiles through Rust to native binaries. Use for Parley code, .par files, or plain-English compiled programs.
---

# Parley

Write `.par` with 4-space indentation and `to main:`. If the workspace has
`./check`, use it exclusively. Do not search for or invoke another compiler.
Otherwise run `parley check program.par --json`. Follow hints until
`"ok": true`.

## First-pass rules

- Names are a `snake_case` identifier, never spaced words. Never name a
  variable `position`; use `index` or `cursor`. Avoid command words such as
  `item`, `ask`, `add`, `set`, `remove`, and `say`.
- Calls used as expressions require parentheses: `if (is_valid with line):`
  or `say (double with 21)`. A standalone call is bare.
- Write `changing` only in a parameter declaration; pass the plain variable
  at the call site.
- Use typed empty collections: `an empty list of text` or
  `a map from text to number`.
- Use `ask ""` for line input without a prompt. `ask for a number ""` and
  `number from text` give `maybe number`; check `is nothing` before `value of`.
- Literal braces in strings are doubled (`"{{"`, `"}}"`); interpolation uses
  single braces (`"total: {count}"`).
- In long conditions, bind calls or repeated `item ... of ...` expressions to
  temporary names first.

## Safe forms

```parley
to record_label with label as text, changing labels as list of text:
    add label to labels

to main:
    let maybe_count be ask for a number ""
    if maybe_count is nothing:
        fail "expected a number"
    let count be value of maybe_count

    let labels be an empty list of text
    record_label with "count={count}", labels

    let values be an empty list of number
    add count to values
    let first_value be item 1 of values
    set item 1 of values to first_value plus 1

    let totals be a map from text to number
    set item "all" of totals to count
    if totals contains "all":
        say item "all" of totals
```

Lists/text are 1-based. Common forms: `length of values`,
`item index of values`, `remove item index of values`, `sorted values`,
`item index of line`, `line split by " "`, `parts joined with ","`,
`trimmed line`, `keys of totals`. Direct map lookup gives the value, not a
maybe; guard missing keys with `map contains key`.

Control flow (`otherwise if` is valid):

```parley
while cursor is at most length of values:
    set cursor to cursor plus 1

repeat count times:
    say count

for each index from 1 to length of values:
    say item index of values
```

Range endpoints are inclusive. Use `stop`/`skip`. Create variables before a
block if needed after it. `let` creates; `set` mutates. Operators include
`plus`, `minus`, `times`, `%`, comparisons, `and`, `or`, and `not`.

Read `references/extended-reference.md` only for records, enums, closures,
files, includes, packages, editors, or research tooling. Repository docs are
authoritative.
