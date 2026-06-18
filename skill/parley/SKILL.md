---
name: parley
description: Write, check, and run Parley programs (.par files) — an English-like language that compiles to native binaries through Rust. Use when the user asks for Parley code, mentions .par files, or wants plain-English programs with compiled performance.
---

# Writing Parley

Parley is an English-like compiled language. You write plain sentences; the
toolchain transpiles to Rust and ships a native binary. Programs live in
`.par` files and start at `to main:`. Blocks are indentation (4 spaces),
comments are `note: …` or `# …`.

## The loop you must follow

1. Write the program.
2. `parley check program.par --json` — structured diagnostics, no build.
3. Apply the `hint` of each diagnostic (codes are stable; `parley explain P204`).
4. Re-check until `"ok": true`, then `parley run program.par`.
5. Ship a binary with `parley build program.par -o name`.

Never guess at fixes when a hint is present — hints name the exact repair.
If `parley` is missing: `pip install git+https://github.com/ded-furby/parley-lang`
(needs Rust: https://rustup.rs).

## The whole language on one screen

```parley
note: declarations live at the top level

a mood is one of happy, neutral, grumpy        # enum (variants are global)

a cat has name as text, lives as number        # record

to feed with c as cat giving text:             # function with return
    give back "{c's name} purrs"

to bump with changing n as number:             # mutates the caller's variable
    set n to n plus 1

to main:
    let felix be a cat with name "Felix", lives 9
    say (feed with felix)                      # expression calls take parens
    bump with felix's lives                    # ✗ changing needs a variable
    let count be 0
    bump with count                            # ✓ statement calls are bare
    say "count is {count}"                     # interpolation in any string

    let xs be a list of 3, 1, 2                # list (1-based items)
    add 9 to xs
    say item 1 of xs
    for each x in sorted xs:
        say x times 10
    let m be a map from text to number         # keys: number or text only
    set item "a" of m to 1
    say keys of m joined with ", "             # keys of is always sorted

    let maybe_n be ask for a number "n? "      # maybe number
    if maybe_n is nothing:
        say "not a number"
    otherwise:
        say value of maybe_n                   # unwrap AFTER checking

    when felix's lives:                        # when over numbers/text needs otherwise
        is 9:
            say "all nine"
        is 1, 2 or 3:                          # several values in one arm
            say "few"
        is 4 to 8:                             # inclusive range (numeric when only)
            say "some"
        otherwise:
            say "fewer"

    let f be the function feed                 # a function as a value
    say (f with felix)                         # call it like any function
    let add_lives be a function taking n as number giving number:
        give back n plus felix's lives         # closure captures current value

    attempt:                                   # catches runtime failures
        say 1 divided by 0
    if it failed:
        say the error

    while count is less than 3:
        set count to count plus 1
        if count is 2:
            skip                               # continue; `stop` = break
    repeat 2 times:
        say "hi"
    for each i from 1 to 3:
        say i
```

Types: `number` (i64) · `decimal` (f64) · `text` · `yesno` (yes/no) ·
`list of T` · `map from K to V` · `maybe T` · records · kinds ·
`(function taking A, B giving R)` (function value; both clauses optional —
parameter example: `to apply with f as (function taking number giving number):`).
Anonymous function values use
`a function taking x as number giving number:` followed by an indented body.

Operators: `plus minus times divided by` (or `+ - * / %`),
`remainder of a divided by b`, `a to the power of b`,
`is / is not / is more than / is less than / is at least / is at most`,
`and or not`, `contains`, `starts with`, `ends with`,
`t split by ","`, `xs joined with ", "`.

Builtins: `length of · sum of · smallest of · largest of · sorted · reversed ·
uppercase of · lowercase of · trimmed · absolute of · rounded · floor of ·
ceiling of · square root of · keys of · text from · number from ·
decimal from · value of · ask · ask for a number · read file ·
write … to file … · append … to file … · a random number from 1 to 6 ·
the error`.

## Rules that catch agents out

1. **Commas belong to arguments.** A list literal or record construction goes
   directly after `be` / `to` / `give back`, or inside parens anywhere else:
   `greet with (a list of 1, 2), 5`.
2. **Division always gives a decimal.** Convert back with `rounded x`,
   `floor of x`, `ceiling of x`.
3. **Value semantics.** `let b be a_list` copies; mutating `b` never changes
   `a_list`. Cross-function mutation only via `changing` parameters, whose
   arguments must be plain variables.
4. **`let` is block-scoped, no shadowing.** Create before the `if`/loop if
   you need it after. `set` changes; `let` creates.
5. **Reserved vocabulary.** `a an is of to item ask sorted reversed trimmed
   rounded contains times changing plus minus yes no nothing not and or` and
   statement keywords cannot be names — P209 tells you and suggests one.
6. **maybes must be checked.** `value of` on nothing stops the program.
7. **`repeat` counts are atoms**: `repeat (n plus 1) times:`.
8. **No early exit from `attempt:`** (`give back`/`stop`/`skip` can't cross it).
9. **Text joins via interpolation**, not `plus`: `"total: {n}"`.
10. **`when` needs `otherwise:`** unless it covers a whole enum (or yes and no).
11. **Function values are made with `the function name`** (not the bare name)
    or with `a function taking ...:` closures. Named function values only work
    for functions without `changing` parameters. Function values cannot be
    compared, said, or turned into text.
12. **Closures capture by value.** They can read outside variables as they
    were when the closure was created, but cannot `set` captured variables.

## Reading failures

* Compile-time: every diagnostic has `code`, `line`, `message`, `hint` — the
  hint is the fix. P2xx = names, P3xx = types, P1xx = syntax.
* Run-time: the process prints `The program stopped: <English reason>` on
  stderr and exits 1. Wrap the risky statement in `attempt:` /
  `if it failed:` to handle it in-program (`the error` holds the message).
* `parley rust program.par` prints the generated Rust if you need to inspect
  the backend; `P901` means the checker missed something — simplify the line
  and report it.
