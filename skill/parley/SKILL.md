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
For research runs from the source checkout, use `parley benchmark prompt
--task hello --language parley` for language-neutral prompts, `parley benchmark
measure --format json` for seed-corpus metrics, and `parley benchmark
summarize --log runs.jsonl --format json` for attempt summaries.

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
    say item 1 of "text"
    for each x in sorted xs:
        say x times 10
    let m be a map from text to number         # keys: number or text only
    set item "a" of m to 1
    say keys of m joined with ", "             # sorted by key
    say sum of values of m                     # values also follow key order
    remove item "a" of m                       # maps can delete keys

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
`t split by ","`, `xs joined with ", "`, `t replacing old with new`,
`position of needle in t`, `count of needle in t`, `item i of t`.

Builtins: `length of · sum of · smallest of · largest of · sorted · reversed ·
uppercase of · lowercase of · trimmed · absolute of · rounded · floor of ·
ceiling of · square root of · keys of · values of · text from · number from ·
decimal from · some · value of · ask · ask for a number · read file ·
write … to file … · append … to file … · a random number from 1 to 6 ·
assert · fail · the error`.

Multi-file code uses `include "helpers.par"`. Reusable local packages can live
at `parley_modules/package_name/main.par` and be loaded with
`include "package_name"`. Shared package roots can be listed in `PARLEY_PATH`.
Bundled packages are available as `include "std/math"` (`clamped`,
`clamped_decimal`, `between`, `between_decimal`, `percent_of`,
`percent_of_decimal`), `include "std/text"` (`is_blank`, `repeated_text`,
`surrounded_with`, `capitalized`, `line_count`, `nonempty_line_count`, `nonempty_lines`,
`word_count`, `words_of`, `maybe_character`, `text_slice`, `without_prefix`,
`without_suffix`, `is_whitespace`, `left_trimmed`, `right_trimmed`,
`is_digit`, `is_alpha`, `is_alphanumeric`, `padded_left`, `padded_right`,
`padded_center`),
`include "std/list"` (`first_number`, `last_number`, `count_number`,
`index_number`, `average_number`, `maybe_first_number`, `maybe_last_number`,
`maybe_item_number`, `list_slice_number`, `extend_number`, `clear_number`, `insert_number`, `pop_number`, `remove_number`, `sort_number`, `reverse_number`, `maybe_smallest_number`, `maybe_largest_number`, `maybe_average_number`,
`first_text`, `last_text`, `count_text`, `index_text`, `maybe_first_text`,
`maybe_last_text`, `maybe_item_text`, `list_slice_text`, `extend_text`, `clear_text`, `insert_text`, `pop_text`, `remove_text`, `sort_text`, `reverse_text`, `maybe_smallest_text`, `maybe_largest_text`,
`first_decimal`, `last_decimal`, `count_decimal`, `index_decimal`,
`average_decimal`, `maybe_first_decimal`, `maybe_last_decimal`,
`maybe_item_decimal`, `list_slice_decimal`, `extend_decimal`, `clear_decimal`, `insert_decimal`, `pop_decimal`, `remove_decimal`, `sort_decimal`, `reverse_decimal`, `maybe_smallest_decimal`, `maybe_largest_decimal`,
`maybe_average_decimal`, `all_yes`, `any_yes`, `maybe_item_yesno`, `list_slice_yesno`, `extend_yesno`, `clear_yesno`, `insert_yesno`, `pop_yesno`, `remove_yesno`, `reverse_yesno`, `count_yes`,
`count_no`, `index_yes`, `index_no`),
and `include "std/map"` (`number_at`,
`take_number_at`, `number_or`, `add_count`, `text_at`, `take_text_at`,
`text_or`, `decimal_at`, `take_decimal_at`, `decimal_or`, `yesno_at`,
`take_yesno_at`, `yesno_or`, `clear_number_map`, `clear_text_map`,
`clear_decimal_map`, `clear_yesno_map`, `number_key_number_at`,
`take_number_key_number_at`, `number_key_number_or`, `add_number_key_count`,
`number_key_text_at`, `take_number_key_text_at`, `number_key_text_or`,
`number_key_decimal_at`, `take_number_key_decimal_at`,
`number_key_decimal_or`, `number_key_yesno_at`,
`take_number_key_yesno_at`, `number_key_yesno_or`,
`clear_number_key_number_map`, `clear_number_key_text_map`,
`clear_number_key_decimal_map`, `clear_number_key_yesno_map`).
Use `parley package new name` to create a local package skeleton, then
`parley package install name path --version 1.0.0` to vendor it into
`parley_modules/name/`; names may contain letters, numbers, dashes,
underscores, and dots. Package versions must use semantic `X.Y.Z` form, with
optional prerelease/build suffixes. `parley package list` reads
`parley.lock.json`.
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
"Name <https://example.com>"` to print a registry-ready entry. Add
`--signing-key release-2026 --signing-secret SECRET` to attach an HMAC-SHA256
release signature.
Use `parley package review name path --version 1.0.0 --description "helpers"
--license MIT --maintainer "Name <https://example.com>"` before submitting a
package; it validates metadata, parses package `.par` files, computes the
digest, and prints the registry entry that would be submitted. It accepts the
same signing options as `publish`.
Use `parley package check-registry registry.json` before hosting a registry.
Use `--require-signatures --signing-secret SECRET` when the registry should
reject unsigned or tampered signed-release entries.
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
   rounded contains replacing position times changing plus minus yes no
   nothing not and or` and statement keywords cannot be names — P209 tells
   you and suggests one.
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
* `parley benchmark prompt`, `parley benchmark measure`, and
  `parley benchmark summarize` expose the research harness from the source
  checkout.
* `parley package search --registry registry.json` and `parley package install
  name --registry registry.json` use schema-1 package registries. Prefer
  registry entries with `sha256`; installs reject mismatches before overwriting
  `parley_modules/name`. Package versions must be semantic `X.Y.Z` strings.
* `parley package verify` checks installed package digests against
  `parley.lock.json`; run it after package installs or before release.
* `parley package check-registry registry.json` validates package names,
  required version, description, license, maintainer, and source metadata,
  semantic versions, readable sources, SHA-256 matches, and optional required
  HMAC-SHA256 release signatures before a registry is hosted.
* `parley package publish name path --version X --description "..." --license
  MIT --maintainer "Name <https://example.com>"` prints the registry entry for
  a local package, including the deterministic SHA-256. Add `--signing-key`
  and `--signing-secret` to include a release signature.
* `parley package review name path --version X --description "..." --license
  MIT --maintainer "Name <https://example.com>"` dry-runs a package submission
  by validating metadata, parsing package `.par` files, and printing the
  registry entry that would be submitted.
* The hosted starter package index is
  `https://ded-furby.github.io/parley-lang/registry.json`.
