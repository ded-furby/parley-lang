# Parley in 15 minutes

Parley reads like English and compiles to a native binary. This walkthrough
covers the whole language. Every snippet is a complete program — copy it into
a file and `parley run file.par`. Run `parley doctor` once after install to
check that Rust, the bundled stdlib, and local package support are available.

## 1. Say hello

```parley
to main:
    say "Hello!"
```

Every program starts at `to main:`. Blocks are indentation (4 spaces), exactly
like Python. `say` prints anything.

## 2. Variables

```parley
to main:
    let count be 10
    set count to count plus 5
    say count
```

`let` creates a variable, `set` changes it. A variable lives until the end of
the block it was created in, and its type never changes.

The basic types:

| type | examples |
|---|---|
| `number` | `42`, `-3` (whole numbers) |
| `decimal` | `2.5`, `0.1` |
| `text` | `"hello"` |
| `yesno` | `yes`, `no` |

## 3. Talking values: interpolation

```parley
to main:
    let who be "world"
    say "Hello, {who}! Two plus two is {2 plus 2}."
```

Anything inside `{…}` in a string is a normal expression. Use `{{` and `}}`
for literal braces.

## 4. Math, in words or symbols

```parley
to main:
    say 7 plus 3 times 2          # 13 — times binds tighter
    say 10 divided by 4           # 2.5 — division always gives a decimal
    say remainder of 10 divided by 3
    say 2 to the power of 8
    say square root of 144
    say rounded 2.5
```

`+ - * / %` work too. `rounded`, `floor of`, `ceiling of` turn decimals into
whole numbers.

## 5. Deciding

```parley
to main:
    let score be 75
    if score is at least 90:
        say "brilliant"
    otherwise if score is more than 50:
        say "solid"
    otherwise:
        say "keep going"
```

Comparisons: `is`, `is not`, `is more than`, `is less than`, `is at least`,
`is at most`. Combine with `and`, `or`, `not`.

## 6. Repeating

```parley
to main:
    repeat 3 times:
        say "hi"
    for each i from 1 to 5:
        say i
    let n be 0
    while n is less than 3:
        set n to n plus 1
```

`stop` ends a loop early; `skip` jumps to the next turn.

## 7. Lists

```parley
to main:
    let primes be a list of 2, 3, 5, 7
    add 11 to primes
    say item 1 of primes          # items count from 1
    say length of primes
    say sum of primes
    for each p in sorted primes:
        say p
```

Also: `remove item 2 of primes`, `set item 1 of primes to 13`,
`primes contains 7`, `smallest of`, `largest of`, `reversed`.
An empty start: `let names be an empty list of text`.

## 8. Maps

```parley
to main:
    let ages be a map from text to number
    set item "ada" of ages to 36
    let ada be item "ada" of ages
    say ada
    for each name in keys of ages:
        say name
```

Keys are `number` or `text`. `keys of` always comes back sorted, so programs
behave the same every run.

## 9. Text tools

```parley
to main:
    let line be "milk, eggs, flour"
    let parts be line split by ", "
    say length of parts
    say parts joined with " + "
    say uppercase of "quiet"
    if line starts with "milk":
        say "dairy first"
```

Also: `lowercase of`, `trimmed`, `contains`, `ends with`, `reversed`.

## 10. Records

```parley
a point has x as number, y as number

to main:
    let home be a point with x 3, y 4
    say home's x
    set home's y to 10
    say home
```

A record bundles named fields. Read fields with `'s`. Records are **copied**
when stored. Function calls preserve value semantics too: the generated Rust
borrows read-only records and clones only if the callee mutates its local copy.

## 11. Kinds (enums) and `when`

```parley
a mood is one of happy, neutral, grumpy

to main:
    let today be grumpy
    when today:
        is happy:
            say "pet the cat"
        is neutral:
            say "observe the cat"
        is grumpy:
            say "feed the cat"
```

A `when` over a kind must cover every variant (or end with `otherwise:`).
`when` also works on numbers and text — then `otherwise:` is required.

One arm can check several values, and numeric `when`s can check ranges
(both ends included):

```parley
to main:
    let score be 95
    when score:
        is 90 to 100:
            say "A"
        is 1, 2 or 3:
            say "tiny"
        otherwise:
            say "keep going"
```

## 12. Functions

```parley
to greet with name as text:
    say "Hello, {name}!"

to double with n as number giving number:
    give back n times 2

to main:
    greet with "Ada"
    say (double with 21)
```

`to name with parameters giving type:` defines; `give back` returns. As a
statement, call plainly: `greet with "Ada"`. Inside an expression, wrap the
call in parentheses: `(double with 21)`. A function with no parameters is
called by its bare name: `let d be roll`.

To let a function **change** the caller's variable, mark the parameter
`changing`:

```parley
to bump with changing n as number:
    set n to n plus 1

to main:
    let count be 0
    bump with count
    say count            # 1
```

Functions are also values. `the function name` picks one up, and a
`(function …)` type declares a parameter that accepts one — so behaviour
can be passed around like any other value:

```parley
to double with x as number giving number:
    give back x times 2

to apply_twice with f as (function taking number giving number), x as number giving number:
    give back (f with (f with x))

to main:
    let d be the function double
    say (apply_twice with d, 5)    # 20
```

This works for any function without `changing` parameters. See
[examples/higher_order.par](../examples/higher_order.par).

You can also make an anonymous function right where you need it. It captures
outside values when it is created:

```parley
to main:
    let offset be 7
    let add_offset be a function taking x as number giving number:
        give back x plus offset
    set offset to 100
    say (add_offset with 5)      # 12
```

The closure reads the original `offset` value. It cannot `set offset` inside
the closure; give back a new value if you want to change something outside.

## 13. Maybe: values that might be missing

Some operations can fail honestly — they give back a `maybe`:

```parley
to main:
    let answer be ask for a number "how many cats? "
    if answer is nothing:
        say "that was not a number"
    otherwise:
        say "{value of answer} cats!"

    let fallback be some 3
    if fallback is not nothing:
        say value of fallback
```

`ask for a number`, `number from text`, `decimal from text`, and `read file`
all give maybes. Check `is nothing` / `is not nothing`, then unwrap with
`value of`. Use `some value` when your own function needs to give back a
present maybe value. (Unwrapping nothing stops the program — check first.)

## 14. When things go wrong: assert, fail, and attempt

Runtime problems (divide by zero, item out of range, a failed
`assert condition, "message"`, `fail "message"`, …) stop the program with a
plain-English message — unless you catch them:

```parley
to main:
    attempt:
        assert no, "custom assertion"
    if it failed:
        say "oops: {the error}"
    say "still going"
```

Use `assert` for invariants that should already be true. The condition must
give yes or no; the optional message must be text.

Use `fail` when your own code or a small helper package needs to reject an
invalid state. The message must be text.

## 15. Files, input, randomness

```parley
to main:
    write "first line" to file "notes.txt"
    append "\nsecond line" to file "notes.txt"
    let content be read file "notes.txt"
    if content is not nothing:
        say value of content
    let name be ask "your name: "
    let roll be a random number from 1 to 6
    say "{name} rolled {roll}"
```

## 16. Many files

```parley
include "helpers.par"

to main:
    say (helper_from_other_file)
```

`include` splices another file in — errors still point at the right file and
line. For reusable local packages, put `main.par` under
`parley_modules/package_name/` and write `include "package_name"`. Shared
package roots can also be listed in `PARLEY_PATH` using your operating system's
path separator.

Bundled standard packages are available without extra files:

```parley
include "std/math"
include "std/text"
include "std/list"
include "std/map"

to main:
    say (clamped with 12, 1, 10)
    say (repeated_text with "ha", 3)
    say (word_count with "one two three")
    let numbers be a list of 4, 2, 4, 8
    say (average_number with numbers)
    say (index_number with numbers, 8)
    let empty_numbers be an empty list of number
    say (maybe_first_number with empty_numbers)
    say (maybe_item_number with numbers, 2)
    say (maybe_average_number with empty_numbers)
    let prices be a list of 1.5, 2.5, 2.0
    say (average_decimal with prices)
    say (maybe_largest_decimal with prices)
    let flags be a list of yes, no, yes
    say (all_yes with flags)
    say (index_no with flags)
    let counts be a map from text to number
    add_count with counts, "agent"
    say (number_or with counts, "agent", 0)
    let flags be a map from text to yesno
    set item "ready" of flags to yes
    say (yesno_at with flags, "ready")
    let seats be a map from number to number
    add_number_key_count with seats, 7
    say (number_key_number_or with seats, 7, 0)
```

To vendor a local package into a project:

```bash
parley package new mathkit
parley package install mathkit ../mathkit --version 1.0.0
parley package list
parley package verify
parley package review mathkit ../mathkit --version 1.0.0 --description "math helpers" --license MIT --maintainer "Your Name <https://example.com>"
parley package publish mathkit ../mathkit --version 1.0.0 --description "math helpers" --license MIT --maintainer "Your Name <https://example.com>" --signing-key release-2026 --signing-secret "$PARLEY_PACKAGE_SIGNING_SECRET"
parley package check-registry registry.json --require-signatures --signing-secret "$PARLEY_PACKAGE_SIGNING_SECRET"
```

`package new` creates a starter `main.par`; `package install` copies the
package to `parley_modules/mathkit/` and records it in `parley.lock.json`.
The lockfile includes the installed package SHA-256. `package verify` checks
that vendored files still match the lockfile. `package publish` prints a
registry-ready JSON entry with license, maintainer, and the same digest.
`package review` dry-runs that registry submission, validates metadata, and
parses package `.par` files before you submit it. `package check-registry`
validates registry ownership metadata before you host it. Signed registries add
`--signing-key` / `--signing-secret` when publishing and
`--require-signatures` when checking. Keep the signing secret out of the
registry file. Package versions must use semantic `X.Y.Z` form, such as
`1.0.0` or `1.0.0-beta.1`.

For a registry manifest, use `parley package search --registry registry.json`
and `parley package install mathkit --registry registry.json`. If the registry
entry includes `sha256`, install verifies the package before replacing anything
under `parley_modules/`.
The hosted starter index is:

```bash
parley package search --registry https://ded-furby.github.io/parley-lang/registry.json
parley package install mathkit --registry https://ded-furby.github.io/parley-lang/registry.json
```

## That's the whole language

Next steps:

* [REFERENCE.md](REFERENCE.md) — every construct with the Rust it becomes
* [ERRORS.md](ERRORS.md) — every error code with its fix
* `parley benchmark prompt --task hello --language parley` — a reusable agent prompt
* `parley benchmark measure --format json` — the seed research corpus metrics
* `examples/` — eleven programs from hello to closures and a todo app
