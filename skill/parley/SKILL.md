---
name: parley
description: Write, check, and run Parley programs (.par files), an English-like language that compiles through Rust to native binaries. Use for Parley code, .par files, or plain-English compiled programs.
---

# Parley

Use this core reference for normal programs. Read
`references/extended-reference.md` only when a task needs the exhaustive
standard-library catalog, packages/registries, LSP setup, or research tooling.

Parley files use 4-space indentation, begin execution at `to main:`, and use
`note: ...` or `# ...` comments. There is one preferred write/check loop:

1. Write the `.par` file.
2. If the workspace provides `./check`, use that command exclusively.
   Otherwise run `parley check program.par --json`.
3. Apply each diagnostic's `hint`, then re-check until `"ok": true`.
4. Run with `parley run program.par`; build with
   `parley build program.par -o name`.

Do not search for another compiler when `./check` exists. P1xx diagnostics are
syntax, P2xx names, P3xx types, and P901 is a compiler bug; simplify only if a
P901 hint asks you to.

## Core syntax

```parley
to double with n as number giving number:
    give back n times 2

to main:
    let name be ask ""                      # text input; empty prompt prints nothing
    let maybe_count be ask for a number ""  # gives maybe number
    if maybe_count is nothing:
        fail "expected a whole number"
    let count be value of maybe_count        # unwrap only after checking

    let values be an empty list of number    # typed empty list
    add count to values
    set item 1 of values to count plus 1
    remove item (length of values) of values # list positions are 1-based

    let totals be a map from text to number
    if totals contains name:
        let current be item name of totals
        set item name of totals to current plus count
    otherwise:
        set item name of totals to count

    for each key in keys of totals:          # map keys/values are key-sorted
        say "{key} {item key of totals}"

    say (double with count)                  # expression calls need parentheses
```

Statement calls are bare (`double with count`); calls used as expressions are
parenthesized (`say (double with count)`). `let` creates a block-scoped name;
`set` changes an existing name. Do not shadow a name with another `let`.

Types are `number` (i64), `decimal` (f64), `text`, `yesno` (`yes`/`no`),
`list of T`, `map from K to V` (number/text keys), `maybe T`, records, enums,
and function values. Assignment has value semantics: lists, maps, text, and
records are copied when stored. Cross-function mutation requires a `changing`
parameter and a plain variable argument.

## Input, text, lists, and maps

- `ask "prompt"` returns text. Use `ask ""` for line-oriented input without
  extra output.
- `ask for a number ""` and `number from text` return `maybe number`.
  Check `is nothing` / `is not nothing`, then use `value of`.
- Text operations: `line split by " "`, `parts joined with ","`,
  `length of line`, `item i of line`, `trimmed line`, `uppercase of line`,
  `lowercase of line`, `line contains "x"`, `line starts with "x"`,
  `line ends with "x"`, `line replacing old with new`, and
  `position of needle in line` (a maybe number).
- Text interpolation is `"total: {count}"`; text does not concatenate with
  `plus`.
- Literal braces inside a Parley string must be doubled: `"{{"` is one `{`
  and `"}}"` is one `}`. This matters when processing bracket characters.
- Lists: `a list of 1, 2`, `an empty list of text`, `add x to xs`,
  `item i of xs`, `set item i of xs to x`, `remove item i of xs`,
  `length of xs`, `sorted xs`, `reversed xs`, `sum of xs`.
- Map lookup (`item key of map`) returns the map's value type and stops at
  runtime if the key is absent. Guard with `map contains key` first. Do not
  treat a direct map lookup as a maybe.
- `keys of map` and `values of map` are deterministic and sorted by key.

## Expressions and control flow

Arithmetic: `plus`, `minus`, `times`, `divided by`, `%`,
`remainder of a divided by b`, `a to the power of b`. Division returns a
decimal; use `rounded`, `floor of`, or `ceiling of` when a number is required.

Comparisons: `is`, `is not`, `is more than`, `is less than`, `is at least`,
`is at most`, combined with `and`, `or`, `not`.

```parley
if condition:
    say "yes"
otherwise if other_condition:
    say "other"
otherwise:
    say "no"

while count is less than 10:
    set count to count plus 1

repeat count times:
    say count

for each item in values:
    say item

for each index from 1 to length of values:   # inclusive endpoints
    say item index of values
```

Use `stop` for break and `skip` for continue. A computed repeat count may need
parentheses: `repeat (count plus 1) times:`.

`when value:` supports `is value:`, `is 1, 2 or 3:`, inclusive numeric
`is 4 to 8:`, and `otherwise:`. Non-enum `when` blocks need `otherwise:`.

## Functions, records, enums, and failures

```parley
a mood is one of happy, neutral, grumpy
a cat has name as text, lives as number

to rename with changing text_value as text, new_value as text:
    set text_value to new_value

to main:
    let cat_value be a cat with name "Milo", lives 9
    say cat_value's name
    let operation be the function double
    say (operation with 21)

    assert cat_value's lives is at least 0, "lives cannot be negative"
    attempt:
        fail "example failure"
    if it failed:
        say the error
```

Returning functions use `giving TYPE` and `give back value`. Function values
use `the function name` or an anonymous `a function taking ... giving ...:`
block. Closures capture outside values by value and cannot mutate captures.

`assert condition, "message"` and `fail "message"` create English runtime
failures. Catch them with `attempt:` / `if it failed:`; `the error` contains
the message. `give back`, `stop`, and `skip` cannot jump out of an attempt.

## Includes and deeper references

Use `include "helpers.par"` for another file, `include "package_name"` for a
local package, and `include "std/math"`, `"std/text"`, `"std/list"`, or
`"std/map"` for bundled helpers. Standard helpers follow typed names such as
`maybe_first_number`, `median_decimal`, `filter_text`, and `number_at`.

Read `references/extended-reference.md` before relying on a less-common helper
name or doing package publishing, registry validation, editor/LSP integration,
or benchmark tooling. The repository's `docs/TUTORIAL.md`,
`docs/REFERENCE.md`, `docs/SPEC.md`, and `docs/ERRORS.md` are authoritative
when available.

## Common repair rules

1. Follow diagnostic hints exactly; codes are stable.
2. Write typed empty lists (`an empty list of text`), never an untyped empty
   literal.
3. Double literal string braces (`{{` and `}}`).
4. Parenthesize function calls inside expressions.
5. Check and unwrap values returned by input conversion; do not unwrap direct
   list/map item access.
6. Create variables before an `if` or loop if they are needed afterwards.
7. Use interpolation for mixed text/value output.
8. Reserved English vocabulary cannot be used as names; use the P209
   suggestion.
