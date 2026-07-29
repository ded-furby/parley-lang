---
name: parley
description: Write, check, and run Parley programs (.par files), an English-like language that compiles through Rust to native binaries. Use for Parley code, .par files, or plain-English compiled programs.
---

# Parley

Write `.par` files with 4-space indentation and a `to main:` entry point.
Use this loop:

1. Write the program.
2. If the workspace has `./check`, run `./check` exclusively. Do not search
   for or invoke another compiler. Otherwise use
   `parley check program.par --json`.
3. Apply diagnostic hints and re-check until `"ok": true`.

Run with `parley run program.par`; build with
`parley build program.par -o name`.

## First-pass rules

- Names are one `snake_case` identifier, never space-separated words.
- Do not use reserved vocabulary as a name. In particular, never name a
  variable `position`; use `index` or `cursor`. Avoid command words such as
  `item`, `ask`, `add`, `set`, `remove`, `say`, `read`, and `write` as names.
- Calls used as expressions require parentheses: `if (is_valid with line):`
  and `say (double with 21)`. A standalone call is bare:
  `record_label with label, labels`.
- Write `changing` only in a parameter declaration. At the call site pass the
  plain variable, without `changing`.
- Use `an empty list of text`, not an untyped empty list.
- Use `ask ""` for line input without printing a prompt.
- Literal braces in strings are doubled: `"{{"` and `"}}"`. Interpolation
  uses single braces: `"total: {count}"`.
- For a long condition containing calls or several `item ... of ...`
  expressions, bind those expressions to temporary names first. This avoids
  English-phrase ambiguity and makes diagnostics local.

## Safe core example

```parley
to double with value as number giving number:
    give back value times 2

to record_label with label as text, changing labels as list of text:
    add label to labels

to main:
    let maybe_count be ask for a number ""
    if maybe_count is nothing:
        fail "expected a whole number"
    let count be value of maybe_count

    let labels be an empty list of text
    record_label with "count={count}", labels

    let values be an empty list of number
    add count to values
    let first_value be item 1 of values
    set item 1 of values to first_value plus 1

    say (double with count)
    say (labels joined with ",")
```

`number from text` and `ask for a number ""` return `maybe number`. Check
`is nothing` or `is not nothing` before `value of`.

## Common forms

Types: `number` (i64), `decimal` (f64), `text`, `yesno` (`yes`/`no`),
`list of T`, `map from K to V`, and `maybe T`.

- Variables: `let count be 0`; mutate with `set count to count plus 1`.
- Text: `length of line`, `item index of line`, `line split by " "`,
  `parts joined with ","`, `trimmed line`, `line contains "x"`.
- Lists are 1-based: `add value to values`, `item index of values`,
  `set item index of values to value`, `remove item index of values`,
  `length of values`, `sorted values`.
- Maps: `a map from text to number`, `totals contains key`,
  `item key of totals`, `set item key of totals to value`, `keys of totals`.
  Direct map lookup gives the value, not a maybe; guard a missing key first.
- Arithmetic: `plus`, `minus`, `times`, `divided by`, `%`.
- Comparison: `is`, `is not`, `is less than`, `is at most`, `is more than`,
  `is at least`, plus `and`, `or`, `not`.

```parley
if condition:
    say "yes"
otherwise if other_condition:
    say "other"
otherwise:
    say "no"

while cursor is at most length of values:
    let current_value be item cursor of values
    say current_value
    set cursor to cursor plus 1

repeat count times:
    say count

for each index from 1 to length of values:
    say item index of values

for each key in keys of totals:
    say "{key} {item key of totals}"
```

Range endpoints are inclusive. Use `stop` for break and `skip` for continue.
Variables created inside an `if` or loop do not exist outside it; initialize
outside when later code needs them. `let` creates a name and `set` mutates it.

Read `references/extended-reference.md` only for records, enums, function
values, closures, attempts, files, includes, standard-library/package names,
LSP/editor setup, or research tooling. Repository `docs/REFERENCE.md` and
`docs/SPEC.md` are authoritative when available.
