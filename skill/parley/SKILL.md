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
Use `parley doctor --json` to verify a fresh install before starting a larger
program or debugging an environment problem.
For editor diagnostics, run `parley-lsp` as a stdio Language Server Protocol
server; it emits the same P-code diagnostics as `parley check --json`.
For research runs from the source checkout, use `parley benchmark measure
--format json` for seed-corpus metrics and `parley benchmark summarize --log
runs.jsonl --format json` for attempt summaries.

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

    assert count is at least 0, "count cannot be negative"
    attempt:                                   # catches runtime failures
        assert no, "custom assertion"
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
decimal from · some · value of · ask · ask for a number · read file ·
write … to file … · append … to file … · a random number from 1 to 6 ·
assert · fail · the error`.

Multi-file code uses `include "helpers.par"`. Reusable local packages can live
at `parley_modules/package_name/main.par` and be loaded with
`include "package_name"`. Shared package roots can be listed in `PARLEY_PATH`.
Bundled packages are available as `include "std/math"` (`clamped`, `between`,
`percent_of`), `include "std/text"` (`is_blank`, `repeated_text`,
`surrounded_with`), `include "std/list"` (`first_number`, `last_number`,
`count_number`, `index_number`, `average_number`, `first_text`, `last_text`,
`count_text`, `index_text`), and `include "std/map"` (`number_at`,
`number_or`, `add_count`, `text_at`, `text_or`).
Use `parley package new name` to create a local package skeleton, then
`parley package install name path --version 1.0.0` to vendor it into
`parley_modules/name/`; names may contain letters, numbers, dashes,
underscores, and dots. `parley package list` reads `parley.lock.json`.
Registry manifests use `{"schema_version": 1, "packages": {"name":
{"version": "1.0.0", "source": "path-or-url", "description": "...",
"license": "MIT", "maintainer": "Name <https://example.com>",
"sha256": "..."}}}`. Search with
`parley package search --registry registry.json`, then install with
`parley package install name --registry registry.json`. When `sha256` is
present, install verifies it before replacing an existing package and records
the digest in `parley.lock.json`. Run `parley package verify` to check that
vendored packages still match the lockfile. Use `parley package publish name
path --version 1.0.0 --description "helpers" --license MIT --maintainer
"Name <https://example.com>"` to print a registry-ready entry.
Use `parley package check-registry registry.json` before hosting a registry.
The hosted starter index is
`https://ded-furby.github.io/parley-lang/registry.json`.

## Rules that catch agents out

1. **Commas belong to arguments.** A list literal or record construction goes
   directly after `be` / `to` / `give back`, or inside parens anywhere else:
   `greet with (a list of 1, 2), 5`.
2. **Division always gives a decimal.** Convert back with `rounded x`,
   `floor of x`, `ceiling of x`.
3. **Value semantics.** `let b be a_list` copies; mutating `b` never changes
   `a_list`. Normal function calls preserve that behaviour even though the
   backend borrows read-only heap parameters. Cross-function mutation only via
   `changing` parameters, whose arguments must be plain variables.
4. **`let` is block-scoped, no shadowing.** Create before the `if`/loop if
   you need it after. `set` changes; `let` creates.
5. **Reserved vocabulary.** `a an is of to item ask sorted reversed trimmed
   rounded contains times changing plus minus yes no nothing not and or` and
   statement keywords cannot be names — P209 tells you and suggests one.
6. **maybes must be checked.** Use `some x` to construct a present maybe value;
   `value of` on nothing stops the program.
7. **`repeat` counts are atoms**: `repeat (n plus 1) times:`.
8. **Use `assert condition, "message"` for invariants.** The condition must
   be yes/no, the optional message must be text, and failures are catchable.
9. **Use `fail "message"` for custom runtime errors.** The message must be text
   and can be caught by `attempt:` / `if it failed:`.
10. **No early exit from `attempt:`** (`give back`/`stop`/`skip` can't cross it).
11. **Text joins via interpolation**, not `plus`: `"total: {n}"`.
12. **`when` needs `otherwise:`** unless it covers a whole enum (or yes and no).
13. **Function values are made with `the function name`** (not the bare name)
    or with `a function taking ...:` closures. Named function values only work
    for functions without `changing` parameters. Function values cannot be
    compared, said, or turned into text.
14. **Closures capture by value.** They can read outside variables as they
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
* `parley-lsp` publishes diagnostics for open `.par` files in editors that can
  launch a stdio LSP server.
* `parley doctor --json` reports Parley, Python, cargo, bundled stdlib, and
  local package readiness.
* `parley benchmark measure` and `parley benchmark summarize` expose the
  research harness from the source checkout.
* `parley package search --registry registry.json` and `parley package install
  name --registry registry.json` use schema-1 package registries. Prefer
  registry entries with `sha256`; installs reject mismatches before overwriting
  `parley_modules/name`.
* `parley package verify` checks installed package digests against
  `parley.lock.json`; run it after package installs or before release.
* `parley package check-registry registry.json` validates package names,
  required version, description, license, maintainer, and source metadata,
  readable sources, and SHA-256 matches before a registry is hosted.
* `parley package publish name path --version X --description "..." --license
  MIT --maintainer "Name <https://example.com>"` prints the registry entry for
  a local package, including the deterministic SHA-256.
* The hosted starter package index is
  `https://ded-furby.github.io/parley-lang/registry.json`.
