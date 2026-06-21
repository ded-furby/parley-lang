# Parley language reference

Complete, in one page. Every Parley construct maps to exactly one Rust
construct — the right column is literally what `parley rust program.par`
prints (minus mechanical details like `i64` suffixes and helper plumbing).

## Program shape

A program is records, kinds (enums) and functions at the top level, with
indentation-based blocks (4 spaces). Execution starts at `to main:`.
Comments: `note: …` or `# …` to end of line.

## Types

| Parley | Rust | notes |
|---|---|---|
| `number` | `i64` | whole numbers |
| `decimal` | `f64` | |
| `text` | `String` | UTF-8; `length of` counts characters |
| `yesno` | `bool` | literals `yes` / `no` |
| `list of T` | `Vec<T>` | items count from 1 |
| `map from K to V` | `HashMap<K, V>` | K is `number` or `text`; `keys of` and `values of` are sorted by key |
| `maybe T` | `Option<T>` | `some x` or `nothing`; unwrap with `value of` |
| record | `struct` (derive Clone, Debug, PartialEq) | |
| kind | `enum` (derive Clone, Copy, Debug, PartialEq) | |
| `(function taking A, B giving R)` | `Rc<dyn Fn(A, B) -> R>` | a cloneable function value; both clauses optional |

**Value semantics:** storing text/lists/maps/records copies them. Function
calls keep the same behaviour, but generated Rust borrows read-only heap
parameters and clones inside the callee only when that parameter is stored or
mutated. Mutation crosses a function boundary only through `changing`
parameters (`&mut T`).

## Declarations

| Parley | Rust |
|---|---|
| `a point has x as number, y as number` | `struct Point { x: i64, y: i64 }` |
| `a mood is one of happy, grumpy` | `enum Mood { Happy, Grumpy }` |
| `to f with a as number giving number:` | `fn f(a: i64) -> i64 {` |
| `to f with xs as list of number:` | `fn f(xs: &Vec<i64>) {` |
| `to f with changing xs as list of number:` | `fn f(xs: &mut Vec<i64>) {` |

Variant names share one global namespace (so `happy` alone is unambiguous).

## Statements

| Parley | Rust |
|---|---|
| `let x be 5` | `let mut x: i64 = 5;` |
| `set x to 6` | `x = 6;` |
| `set p's x to 6` | `p.x = 6;` |
| `say expr` | `println!(…)` (yesno prints `yes`/`no`, maybe prints `nothing` or the value) |
| `if c:` / `otherwise if c:` / `otherwise:` | `if c { } else if c { } else { }` |
| `when x:` with `is v:` arms | `match` (enums) / `if`-chain (numbers, text, yesno) |
| `is 1, 2 or 3:` (multi-value arm) | `1 \| 2 \| 3 =>` / chained `\|\|` |
| `is 10 to 20:` (range arm, numeric `when`) | `x >= 10 && x <= 20` (inclusive) |
| `while c:` | `while c { }` |
| `repeat n times:` | `for _ in 0..n { }` |
| `for each x in xs:` | `for x in xs.clone() { }` (iterates a copy) |
| `for each i from 1 to 10:` | `for i in 1..=10 { }` (inclusive) |
| `stop` / `skip` | `break;` / `continue;` |
| `give back expr` | `return expr;` |
| `assert condition` / `assert condition, message` | catchable runtime check |
| `fail "message"` | catchable runtime failure |
| `add x to xs` | `xs.push(x);` |
| `remove item i of xs` / `remove item k of m` | bounds-checked list removal or silent map-key removal |
| `set item i of xs to v` | bounds-checked `xs[i-1] = v` |
| `set item k of m to v` | `m.insert(k, v);` |
| `write t to file p` / `append t to file p` | `std::fs` (failure stops the program; catchable) |
| `attempt:` / `if it failed:` | `catch_unwind` — see Errors below |
| `include "lib.par"` | splices the file before parsing; resolves relative paths, `parley_modules`, then `PARLEY_PATH` |
| `f with a, b` (statement call) | `f(a, b);` |

## Expressions

Precedence, loosest to tightest: `or` · `and` · `not` · comparisons ·
`split by`/`joined with`/`replacing … with …` · `plus minus` · `times divided-by %` ·
`to the power of` · prefix operations · `'s` field access.

| Parley | Rust | type |
|---|---|---|
| `a plus b` | `a + b` (texts: `format!`) | number/decimal/text/list |
| `a minus b`, `a times b` | `a - b`, `a * b` | numeric |
| `a divided by b` | guarded `a / b` | **always decimal**; ÷0 stops the program |
| `remainder of a divided by b` | guarded `a % b` | number |
| `a to the power of b` | `a.pow(b)` / `a.powf(b)` | |
| `x is y` / `x is not y` | `==` / `!=` | yesno |
| `is more than / less than / at least / at most` | `> < >= <=` | yesno |
| `xs contains x` | `.contains(…)` (list, map key, or substring) | yesno |
| `t starts with p` / `t ends with p` | `.starts_with` / `.ends_with` | yesno |
| `t split by ","` | `.split(…).collect()` | list of text |
| `xs joined with ", "` | `.join(…)` (list of text) | text |
| `t replacing old with new` | `.replace(old, new)` | text |
| `position of needle in t` | UTF-8-safe substring search | maybe number |
| `count of needle in t` | non-overlapping substring count | number |
| `"{x} and {y}"` | `format!("{} and {}", x, y)` | text |
| `(f with a, b)` | `f(a, b)` — calls in expressions take parens | |
| `bob's name` | `bob.name` | field type |
| `item i of xs` / `item i of t` / `item k of m` | bounds/presence-checked access (1-based) | element/text/value |
| `a list of 1, 2, 3` | `vec![1, 2, 3]` | directly after be/to/give back, or in parens |
| `an empty list of text` | `Vec::<String>::new()` | |
| `a map from text to number` | `HashMap::new()` | |
| `a point with x 1, y 2` | `Point { x: 1, y: 2 }` | all fields required |
| `nothing` | `None` | |
| `some x` | `Some(x)` | maybe of x's type |
| `value of m` | checked unwrap | inner type |
| `the error` | last runtime error text | text |
| `the function f` | `Rc::new(move |…| f(…))` | a named function value (no `changing` params) |
| `a function taking x as number giving number: ...` | `Rc::new(move |x: i64| -> i64 { ... })` | anonymous closure with captured values |

A variable holding a function value is called exactly like a function:
`(f with x)` in expressions, `f with x` as a statement. Function values
cannot be compared, turned into text, or said.

Anonymous functions capture outside variables by value when they are created.
Changing the original variable later does not change the captured value.
Closures can read captured values, but cannot `set` them; give back a changed
value and assign it outside if you need that flow.

### Built-in operations

| Parley | works on | gives |
|---|---|---|
| `length of x` | text, list, map | number |
| `sum of xs` | list of number/decimal | same |
| `smallest of xs` / `largest of xs` | list of number/decimal/text | element |
| `sorted xs` / `reversed xs` | list (reversed also text) | same |
| `uppercase of t` / `lowercase of t` / `trimmed t` | text | text |
| `absolute of n` | number/decimal | same |
| `rounded x` / `floor of x` / `ceiling of x` | decimal (number passes through) | number |
| `square root of x` | number/decimal | decimal |
| `keys of m` | map | sorted list of keys |
| `values of m` | map | list of values in sorted-key order |
| `text from x` | anything | text |
| `number from x` | text → **maybe** number; decimal → number | |
| `decimal from x` | text → **maybe** decimal; number → decimal | |
| `ask "prompt"` | — | text (end of input stops the program) |
| `ask for a number "prompt"` | — | maybe number |
| `read file "p"` | — | maybe text |
| `a random number from 1 to 6` | — | number (inclusive) |

## Errors

Runtime failures (`assert`, `fail`, divide by zero, item out of range,
`value of` nothing, file write trouble, end of input) **stop the program**
with a one-line English message on stderr and exit code 1 — unless wrapped:

```parley
attempt:
    assert score is at least 0, "score cannot be negative"
if it failed:
    say the error
```

`assert` needs a yes/no condition, and its optional message must be text.
`fail` needs a text expression. `give back`, `stop`, and `skip` cannot jump
out of an `attempt:` block.

## Scoping and naming rules

* A `let` lives until the end of its block; no shadowing, no redeclaring.
* `set` only changes existing variables.
* Names are letters/digits/underscores and cannot be Parley vocabulary words
  (`is`, `item`, `of`, `to`, `a`, `sorted`, …) — the checker lists the exact
  conflict and suggests alternatives (P209).
* Multi-word phrases are part of the grammar: write them with spaces
  (`is more than`), any number of spaces between the words.

## The agent contract

`parley check program.par --json` emits:

```json
{"ok": false, "diagnostics": [{"code": "P204", "message": "…", "file": "…",
  "line": 4, "col": 9, "hint": "Did you mean \"score\"?",
  "replacement": null, "severity": "error"}]}
```

Codes are stable (see [ERRORS.md](ERRORS.md)); `parley explain P204` prints
the catalog entry. The intended loop: **check → apply hint → re-check → run.**

## Setup doctor

`parley doctor` checks the installed Parley version, Python version, Rust
`cargo` backend, bundled standard packages, and local package state. Use
`parley doctor --json` in scripts or agent setup checks; it returns a
machine-readable report with an `ok` field and one entry per check.

## Benchmark research

From a source checkout, `parley benchmark prompt --task hello --language parley`
renders the language-neutral prompt for one seed task. Omit `--task` to render
all prompts, or use `--format json` for automation. `parley benchmark measure`
runs the Phase 1 seed corpus metrics for Parley, Python, and Rust references.
It forwards the same options as `benchmarks/measure.py`, including
`--format json`, `--no-check`, `--languages`, `--output`, and
`--llm-tokenizer`. Use `parley benchmark append` to record one generated
attempt row in JSONL, and `parley benchmark summarize --log runs.jsonl` to
aggregate attempts by task/language/model.

## Editor integration

`parley-lsp` starts a stdio Language Server Protocol server. It publishes the
same parser/checker diagnostics and stable P-codes as `parley check --json` for
open `.par` documents. The initial server supports `initialize`,
`textDocument/didOpen`, `textDocument/didChange`, `textDocument/didClose`, and
`shutdown`.

## Bundled packages

Use `include "std/math"` for small numeric helpers:

| Function | Gives |
|---|---|
| `clamped with n, low, high` | `n` limited to the inclusive range |
| `clamped_decimal with n, low, high` | decimal `n` limited to the inclusive range |
| `between with n, low, high` | yes/no range check |
| `between_decimal with n, low, high` | yes/no decimal range check |
| `percent_of with part, whole` | decimal percentage |
| `percent_of_decimal with part, whole` | decimal percentage from decimal inputs |
| `pi_value` / `tau_value` / `e_value` | decimal math constants |
| `factorial with n` | whole-number factorial; negative input fails with an English message |
| `greatest_common_divisor with left, right` | non-negative greatest common divisor; negatives are normalized |
| `least_common_multiple with left, right` | non-negative least common multiple; returns `0` when either input is `0` |
| `combination_count with total, chosen` | count unordered choices; returns `0` when `chosen` is greater than `total`; negative inputs fail |
| `permutation_count with total, chosen` | count ordered arrangements; returns `0` when `chosen` is greater than `total`; negative inputs fail |
| `integer_square_root with n` | floor of the square root for non-negative whole numbers; negative input fails |
| `is_perfect_square with n` | yes when a whole number is a perfect square; negative input gives no |
| `is_close with left, right, relative_tolerance, absolute_tolerance` | yes when two decimals are close within the larger tolerance; negative tolerances fail |
| `hypotenuse with x, y` | decimal square root of `x*x + y*y` |
| `distance_2d with x1, y1, x2, y2` / `distance_3d with x1, y1, z1, x2, y2, z2` | decimal Euclidean point distance |
| `copy_sign with magnitude, sign_source` | decimal magnitude with the sign of `sign_source`; zero sign sources count as non-negative |
| `radians_from_degrees with angle` / `degrees_from_radians with angle` | decimal angle conversion helpers |

Use `include "std/text"` for small text helpers:

| Function | Gives |
|---|---|
| `is_blank with t` | yes when `trimmed t` is empty |
| `maybe_character with t, index` | maybe one-character text at a 1-based UTF-8 character index |
| `text_slice with t, first, last` | text from clamped 1-based inclusive UTF-8 character bounds, or empty text for reversed/empty ranges |
| `reversed_text with t` | text reversed by UTF-8 characters; empty text gives empty text |
| `partition_text with t, separator` | three-item list: before first separator, separator, after; absent separator gives `t`, `""`, `""` |
| `rpartition_text with t, separator` | three-item list: before last separator, separator, after; absent separator gives `""`, `""`, `t` |
| `replaced_text with t, old, new, max_replacements` | text with at most `max_replacements` non-overlapping replacements; empty `old` or non-positive count leaves `t` unchanged |
| `split_text with t, separator, max_splits` | list split at most `max_splits` times from the left; empty separator or non-positive count gives `[t]` |
| `rsplit_text with t, separator, max_splits` | list split at most `max_splits` times from the right; empty separator or non-positive count gives `[t]` |
| `position_or_zero with needle, t` | first 1-based UTF-8 character position, or `0` when missing |
| `last_position with needle, t` | maybe 1-based UTF-8 character position of the last match; empty needle gives `length of t plus 1` |
| `last_position_or_zero with needle, t` | last 1-based UTF-8 character position, or `0` when missing |
| `repeated_text with t, count` | text repeated `count` times |
| `surrounded_with with t, wrapper` | wrapper + text + wrapper |
| `capitalized with t` | text with the first character uppercased and the rest lowercased |
| `title_cased with t` | whitespace-delimited words title-cased while preserving original whitespace |
| `is_titlecase with t` | yes when text has at least one ASCII letter and is already title-cased |
| `line_count with t` | number of newline-separated lines, or 0 for empty text |
| `nonempty_line_count with t` | number of lines whose trimmed text is not empty |
| `nonempty_lines with t` | list of trimmed, non-blank lines |
| `lines_of with t` | list of newline-separated lines, preserving blank and trailing lines; empty text gives an empty list |
| `split_lines with t` | list of lines split on `\n`, `\r`, and `\r\n`, preserving blank middle lines but not a synthetic final empty line |
| `split_lines_kept with t` | list of universal newline-split lines with each matched line boundary retained |
| `word_count with t` | number of whitespace-delimited words |
| `words_of with t` | list of whitespace-delimited words, splitting on space, tab, newline, and carriage return |
| `without_prefix with t, prefix` | text with `prefix` removed when present |
| `without_suffix with t, suffix` | text with `suffix` removed when present |
| `has_prefix with t, prefix` | yes when text starts with `prefix`; empty prefix gives yes |
| `has_suffix with t, suffix` | yes when text ends with `suffix`; empty suffix gives yes |
| `has_any_prefix with t, prefixes` | yes when text starts with any candidate prefix; empty candidate lists give no |
| `has_any_suffix with t, suffixes` | yes when text ends with any candidate suffix; empty candidate lists give no |
| `is_whitespace with c` | yes for a space, tab, newline, or carriage return character |
| `is_space with t` | yes when non-empty text contains only space, tab, newline, or carriage return characters |
| `is_digit with t` | yes when non-empty `t` contains only ASCII digits |
| `is_alpha with t` | yes when non-empty `t` contains only ASCII letters |
| `is_alphanumeric with t` | yes when non-empty `t` contains only ASCII letters and digits |
| `is_identifier with t` | yes when non-empty `t` is an ASCII/Parley identifier-like name |
| `is_ascii with t` | yes when every character is tab, newline, carriage return, or printable ASCII; empty text gives yes |
| `is_printable with t` | yes when text has no tab, newline, or carriage return controls; empty text gives yes |
| `is_lowercase with t` | yes when non-empty `t` contains only ASCII lowercase letters |
| `is_uppercase with t` | yes when non-empty `t` contains only ASCII uppercase letters |
| `swap_case with t` | text with ASCII lowercase and uppercase letters swapped |
| `left_trimmed with t` / `right_trimmed with t` | text with leading or trailing whitespace removed |
| `left_trimmed_of with t, chars` / `right_trimmed_of with t, chars` / `trimmed_of with t, chars` | text with explicit leading/trailing characters removed; empty `chars` leaves text unchanged |
| `padded_left with t, width, fill` / `padded_right with t, width, fill` | text padded to at least `width` characters with repeated `fill` |
| `zero_filled with t, width` | text padded on the left with `0`, preserving an initial `+` or `-` before the zeroes |
| `tabs_expanded with t, tab_size` | text with tabs replaced by spaces up to the next tab stop; non-positive tab size removes tabs |
| `padded_center with t, width, fill` | text centered to at least `width` characters with repeated `fill`; odd gaps place the extra fill on the right |

Use `include "std/list"` for common list helpers:

| Function | Gives |
|---|---|
| `first_number with xs` / `last_number with xs` | first or last number |
| `maybe_first_number with xs` / `maybe_last_number with xs` | maybe first or last number |
| `maybe_item_number with xs, index` | maybe number at a 1-based index |
| `list_slice_number with xs, first, last` | list of number from clamped 1-based inclusive bounds |
| `list_slice_step_number with xs, first, last, step` | stepped list of number from clamped 1-based inclusive bounds; non-positive steps fail |
| `take_number with xs, count` / `drop_number with xs, count` | fresh number list containing the first `count` items or everything after them |
| `copy_number with xs` | fresh list of number with the same items |
| `chain_number with left, right` | fresh number list containing `left` followed by `right`; inputs are not mutated |
| `repeat_number with value, count` | fresh number list containing `count` copies of `value`; non-positive counts give an empty list |
| `cycle_number with xs, count` | fresh number list cycling through `xs` until `count` items are produced; empty input or non-positive counts give an empty list |
| `filter_number with xs, keep` | fresh list of numbers where `keep` returns yes |
| `reject_number with xs, test` | fresh list of numbers where `test` returns no |
| `compress_number with xs, selectors` | fresh list of numbers whose parallel yes/no selector is yes; stops when either list ends |
| `map_number with xs, transform` | fresh list of numbers after applying `transform` to each item |
| `fold_number with xs, initial, combine` | left fold with a number accumulator; empty lists give `initial` |
| `any_number with xs, test` / `all_number with xs, test` | predicate any/all over numbers; empty lists give no/yes |
| `maybe_find_number with xs, test` | maybe first number where `test` returns yes |
| `maybe_find_index_number with xs, test` | maybe 1-based index of first number where `test` returns yes |
| `indexes_where_number with xs, test` | fresh number list of every 1-based index where `test` returns yes |
| `count_where_number with xs, test` | number of values where `test` returns yes |
| `take_while_number with xs, test` / `drop_while_number with xs, test` | leading matching prefix or remaining suffix |
| `extend_number with changing xs, more` | append every number from `more` to `xs` |
| `clear_number with changing xs` | remove every item from `xs` |
| `insert_number with changing xs, index, value` | insert `value` before the 1-based index, clamped to front/end |
| `pop_number with changing xs, index` | maybe removed number at a 1-based index |
| `remove_number with changing xs, value` | remove the first matching number; yes if one was removed |
| `sort_number with changing xs` | sort a number list in place |
| `reverse_number with changing xs` | reverse a number list in place |
| `count_number with xs, n` | occurrences of `n` |
| `contains_number with xs, n` | yes when `n` is present |
| `index_number with xs, n` | maybe 1-based index of `n` |
| `average_number with xs` | decimal average |
| `geometric_mean_number with xs` | decimal geometric mean; empty lists or negative items fail |
| `harmonic_mean_number with xs` | decimal harmonic mean; empty lists or negative items fail; zero items give `0.0` |
| `quantiles_number with xs, groups` | decimal exclusive quantile cut points; `groups` must be at least `1`; empty lists fail |
| `inclusive_quantiles_number with xs, groups` | decimal inclusive quantile cut points; `groups` of `1` gives an empty list; empty lists fail |
| `median_number with xs` | decimal median of a sorted copy; empty lists fail |
| `median_low_number with xs` / `median_high_number with xs` | lower or upper middle number from a sorted copy; empty lists fail |
| `mode_number with xs` | most common number; ties keep the first value seen; empty lists fail |
| `modes_number with xs` | fresh number list of all tied modes in first-seen order; empty lists give an empty list |
| `population_variance_number with xs` | decimal population variance; empty lists fail |
| `population_standard_deviation_number with xs` | decimal population standard deviation; empty lists fail |
| `sample_variance_number with xs` | decimal sample variance; lists shorter than two items fail |
| `sample_standard_deviation_number with xs` | decimal sample standard deviation; lists shorter than two items fail |
| `covariance_number with xs, ys` | decimal sample covariance; lists must have the same length and at least two items |
| `correlation_number with xs, ys` | decimal Pearson correlation; lists must have the same length, at least two items, and non-constant inputs |
| `linear_regression_number with xs, ys` | two-decimal list `[slope, intercept]`; lists must have the same length, at least two items, and non-constant x values |
| `proportional_linear_regression_number with xs, ys` | two-decimal list `[slope, 0.0]`; lists must have the same length, at least two items, and non-zero x values |
| `product_number with xs` | product of all numbers; empty list gives `1` |
| `sum_number with xs` | sum of all numbers; empty list gives `0` |
| `accumulated_sum_number with xs` | fresh number list of running totals; empty list gives an empty list |
| `accumulated_product_number with xs` | fresh number list of running products; empty list gives an empty list |
| `accumulated_minimum_number with xs` / `accumulated_maximum_number with xs` | fresh number list of running minimum or maximum values; empty list gives an empty list |
| `sum_product_number with left, right` | sum of pairwise products; empty lists give `0`; length mismatch fails |
| `maybe_smallest_number with xs` / `maybe_largest_number with xs` | maybe smallest or largest number |
| `maybe_average_number with xs` | maybe decimal average |
| `maybe_geometric_mean_number with xs` | maybe decimal geometric mean |
| `maybe_harmonic_mean_number with xs` | maybe decimal harmonic mean |
| `maybe_quantiles_number with xs, groups` / `maybe_inclusive_quantiles_number with xs, groups` | maybe decimal quantile cut points |
| `maybe_median_number with xs` | maybe decimal median |
| `maybe_median_low_number with xs` / `maybe_median_high_number with xs` | maybe lower or upper middle number |
| `maybe_mode_number with xs` | maybe most common number |
| `maybe_population_variance_number with xs` | maybe decimal population variance |
| `maybe_population_standard_deviation_number with xs` | maybe decimal population standard deviation |
| `maybe_sample_variance_number with xs` | maybe decimal sample variance |
| `maybe_sample_standard_deviation_number with xs` | maybe decimal sample standard deviation |
| `maybe_covariance_number with xs, ys` / `maybe_correlation_number with xs, ys` | maybe decimal covariance or correlation |
| `maybe_linear_regression_number with xs, ys` / `maybe_proportional_linear_regression_number with xs, ys` | maybe two-decimal regression result |
| `first_text with xs` / `last_text with xs` | first or last text |
| `maybe_first_text with xs` / `maybe_last_text with xs` | maybe first or last text |
| `maybe_item_text with xs, index` | maybe text at a 1-based index |
| `list_slice_text with xs, first, last` | list of text from clamped 1-based inclusive bounds |
| `list_slice_step_text with xs, first, last, step` | stepped list of text from clamped 1-based inclusive bounds; non-positive steps fail |
| `take_text with xs, count` / `drop_text with xs, count` | fresh text list containing the first `count` items or everything after them |
| `copy_text with xs` | fresh list of text with the same items |
| `chain_text with left, right` | fresh text list containing `left` followed by `right`; inputs are not mutated |
| `repeat_text with value, count` | fresh text list containing `count` copies of `value`; non-positive counts give an empty list |
| `cycle_text with xs, count` | fresh text list cycling through `xs` until `count` items are produced; empty input or non-positive counts give an empty list |
| `filter_text with xs, keep` | fresh list of text values where `keep` returns yes |
| `reject_text with xs, test` | fresh list of text values where `test` returns no |
| `compress_text with xs, selectors` | fresh list of text values whose parallel yes/no selector is yes; stops when either list ends |
| `map_text with xs, transform` | fresh list of text values after applying `transform` to each item |
| `fold_text with xs, initial, combine` | left fold with a text accumulator; empty lists give `initial` |
| `any_text with xs, test` / `all_text with xs, test` | predicate any/all over text values; empty lists give no/yes |
| `maybe_find_text with xs, test` | maybe first text value where `test` returns yes |
| `maybe_find_index_text with xs, test` | maybe 1-based index of first text value where `test` returns yes |
| `indexes_where_text with xs, test` | fresh number list of every 1-based text index where `test` returns yes |
| `count_where_text with xs, test` | number of text values where `test` returns yes |
| `take_while_text with xs, test` / `drop_while_text with xs, test` | leading matching prefix or remaining suffix |
| `extend_text with changing xs, more` | append every text value from `more` to `xs` |
| `clear_text with changing xs` | remove every item from `xs` |
| `insert_text with changing xs, index, value` | insert `value` before the 1-based index, clamped to front/end |
| `pop_text with changing xs, index` | maybe removed text at a 1-based index |
| `remove_text with changing xs, value` | remove the first matching text; yes if one was removed |
| `sort_text with changing xs` | sort a text list in place |
| `reverse_text with changing xs` | reverse a text list in place |
| `accumulated_minimum_text with xs` / `accumulated_maximum_text with xs` | fresh text list of running minimum or maximum values; empty list gives an empty list |
| `count_text with xs, t` | occurrences of `t` |
| `contains_text with xs, t` | yes when `t` is present |
| `index_text with xs, t` | maybe 1-based index of `t` |
| `mode_text with xs` | most common text; ties keep the first value seen; empty lists fail |
| `modes_text with xs` | fresh text list of all tied modes in first-seen order; empty lists give an empty list |
| `maybe_mode_text with xs` | maybe most common text |
| `maybe_smallest_text with xs` / `maybe_largest_text with xs` | maybe smallest or largest text |
| `first_decimal with xs` / `last_decimal with xs` | first or last decimal |
| `maybe_first_decimal with xs` / `maybe_last_decimal with xs` | maybe first or last decimal |
| `maybe_item_decimal with xs, index` | maybe decimal at a 1-based index |
| `list_slice_decimal with xs, first, last` | list of decimal from clamped 1-based inclusive bounds |
| `list_slice_step_decimal with xs, first, last, step` | stepped list of decimal from clamped 1-based inclusive bounds; non-positive steps fail |
| `take_decimal with xs, count` / `drop_decimal with xs, count` | fresh decimal list containing the first `count` items or everything after them |
| `copy_decimal with xs` | fresh list of decimal with the same items |
| `chain_decimal with left, right` | fresh decimal list containing `left` followed by `right`; inputs are not mutated |
| `repeat_decimal with value, count` | fresh decimal list containing `count` copies of `value`; non-positive counts give an empty list |
| `cycle_decimal with xs, count` | fresh decimal list cycling through `xs` until `count` items are produced; empty input or non-positive counts give an empty list |
| `filter_decimal with xs, keep` | fresh list of decimals where `keep` returns yes |
| `reject_decimal with xs, test` | fresh list of decimals where `test` returns no |
| `compress_decimal with xs, selectors` | fresh list of decimals whose parallel yes/no selector is yes; stops when either list ends |
| `map_decimal with xs, transform` | fresh list of decimals after applying `transform` to each item |
| `fold_decimal with xs, initial, combine` | left fold with a decimal accumulator; empty lists give `initial` |
| `any_decimal with xs, test` / `all_decimal with xs, test` | predicate any/all over decimals; empty lists give no/yes |
| `maybe_find_decimal with xs, test` | maybe first decimal where `test` returns yes |
| `maybe_find_index_decimal with xs, test` | maybe 1-based index of first decimal where `test` returns yes |
| `indexes_where_decimal with xs, test` | fresh number list of every 1-based decimal index where `test` returns yes |
| `count_where_decimal with xs, test` | number of decimals where `test` returns yes |
| `take_while_decimal with xs, test` / `drop_while_decimal with xs, test` | leading matching prefix or remaining suffix |
| `extend_decimal with changing xs, more` | append every decimal from `more` to `xs` |
| `clear_decimal with changing xs` | remove every item from `xs` |
| `insert_decimal with changing xs, index, value` | insert `value` before the 1-based index, clamped to front/end |
| `pop_decimal with changing xs, index` | maybe removed decimal at a 1-based index |
| `remove_decimal with changing xs, value` | remove the first matching decimal; yes if one was removed |
| `sort_decimal with changing xs` | sort a decimal list in place |
| `reverse_decimal with changing xs` | reverse a decimal list in place |
| `count_decimal with xs, d` | occurrences of `d` |
| `contains_decimal with xs, d` | yes when `d` is present |
| `index_decimal with xs, d` | maybe 1-based index of `d` |
| `average_decimal with xs` | decimal average |
| `geometric_mean_decimal with xs` | decimal geometric mean; empty lists or negative items fail |
| `harmonic_mean_decimal with xs` | decimal harmonic mean; empty lists or negative items fail; zero items give `0.0` |
| `quantiles_decimal with xs, groups` | decimal exclusive quantile cut points; `groups` must be at least `1`; empty lists fail |
| `inclusive_quantiles_decimal with xs, groups` | decimal inclusive quantile cut points; `groups` of `1` gives an empty list; empty lists fail |
| `median_decimal with xs` | median of a sorted copy; empty lists fail |
| `median_low_decimal with xs` / `median_high_decimal with xs` | lower or upper middle decimal from a sorted copy; empty lists fail |
| `mode_decimal with xs` | most common decimal; ties keep the first value seen; empty lists fail |
| `modes_decimal with xs` | fresh decimal list of all tied modes in first-seen order; empty lists give an empty list |
| `population_variance_decimal with xs` | decimal population variance; empty lists fail |
| `population_standard_deviation_decimal with xs` | decimal population standard deviation; empty lists fail |
| `sample_variance_decimal with xs` | decimal sample variance; lists shorter than two items fail |
| `sample_standard_deviation_decimal with xs` | decimal sample standard deviation; lists shorter than two items fail |
| `covariance_decimal with xs, ys` | decimal sample covariance; lists must have the same length and at least two items |
| `correlation_decimal with xs, ys` | decimal Pearson correlation; lists must have the same length, at least two items, and non-constant inputs |
| `linear_regression_decimal with xs, ys` | two-decimal list `[slope, intercept]`; lists must have the same length, at least two items, and non-constant x values |
| `proportional_linear_regression_decimal with xs, ys` | two-decimal list `[slope, 0.0]`; lists must have the same length, at least two items, and non-zero x values |
| `product_decimal with xs` | product of all decimals; empty list gives `1.0` |
| `sum_decimal with xs` | sum of all decimals; empty list gives `0.0` |
| `accumulated_sum_decimal with xs` | fresh decimal list of running totals; empty list gives an empty list |
| `accumulated_product_decimal with xs` | fresh decimal list of running products; empty list gives an empty list |
| `accumulated_minimum_decimal with xs` / `accumulated_maximum_decimal with xs` | fresh decimal list of running minimum or maximum values; empty list gives an empty list |
| `sum_product_decimal with left, right` | sum of pairwise products; empty lists give `0.0`; length mismatch fails |
| `maybe_smallest_decimal with xs` / `maybe_largest_decimal with xs` | maybe smallest or largest decimal |
| `maybe_average_decimal with xs` | maybe decimal average |
| `maybe_geometric_mean_decimal with xs` | maybe decimal geometric mean |
| `maybe_harmonic_mean_decimal with xs` | maybe decimal harmonic mean |
| `maybe_quantiles_decimal with xs, groups` / `maybe_inclusive_quantiles_decimal with xs, groups` | maybe decimal quantile cut points |
| `maybe_median_decimal with xs` | maybe decimal median |
| `maybe_median_low_decimal with xs` / `maybe_median_high_decimal with xs` | maybe lower or upper middle decimal |
| `maybe_mode_decimal with xs` | maybe most common decimal |
| `maybe_population_variance_decimal with xs` | maybe decimal population variance |
| `maybe_population_standard_deviation_decimal with xs` | maybe decimal population standard deviation |
| `maybe_sample_variance_decimal with xs` | maybe decimal sample variance |
| `maybe_sample_standard_deviation_decimal with xs` | maybe decimal sample standard deviation |
| `maybe_covariance_decimal with xs, ys` / `maybe_correlation_decimal with xs, ys` | maybe decimal covariance or correlation |
| `maybe_linear_regression_decimal with xs, ys` / `maybe_proportional_linear_regression_decimal with xs, ys` | maybe two-decimal regression result |
| `first_yesno with xs` / `last_yesno with xs` | first or last yes/no value |
| `maybe_first_yesno with xs` / `maybe_last_yesno with xs` | maybe first or last yes/no value |
| `all_yes with xs` / `any_yes with xs` | yes/no aggregate over a `list of yesno`; empty lists give yes for `all_yes` and no for `any_yes` |
| `maybe_item_yesno with xs, index` | maybe yes/no value at a 1-based index |
| `list_slice_yesno with xs, first, last` | list of yes/no from clamped 1-based inclusive bounds |
| `list_slice_step_yesno with xs, first, last, step` | stepped list of yes/no from clamped 1-based inclusive bounds; non-positive steps fail |
| `take_yesno with xs, count` / `drop_yesno with xs, count` | fresh yes/no list containing the first `count` items or everything after them |
| `copy_yesno with xs` | fresh list of yes/no with the same items |
| `chain_yesno with left, right` | fresh yes/no list containing `left` followed by `right`; inputs are not mutated |
| `repeat_yesno with value, count` | fresh yes/no list containing `count` copies of `value`; non-positive counts give an empty list |
| `cycle_yesno with xs, count` | fresh yes/no list cycling through `xs` until `count` items are produced; empty input or non-positive counts give an empty list |
| `filter_yesno with xs, keep` | fresh list of yes/no values where `keep` returns yes |
| `reject_yesno with xs, test` | fresh list of yes/no values where `test` returns no |
| `compress_yesno with xs, selectors` | fresh list of yes/no values whose parallel yes/no selector is yes; stops when either list ends |
| `map_yesno with xs, transform` | fresh list of yes/no values after applying `transform` to each item |
| `fold_yesno with xs, initial, combine` | left fold with a yes/no accumulator; empty lists give `initial` |
| `any_yesno with xs, test` / `all_yesno with xs, test` | predicate any/all over yes/no values; empty lists give no/yes |
| `maybe_find_yesno with xs, test` | maybe first yes/no value where `test` returns yes |
| `maybe_find_index_yesno with xs, test` | maybe 1-based index of first yes/no value where `test` returns yes |
| `indexes_where_yesno with xs, test` | fresh number list of every 1-based yes/no index where `test` returns yes |
| `count_where_yesno with xs, test` | number of yes/no values where `test` returns yes |
| `take_while_yesno with xs, test` / `drop_while_yesno with xs, test` | leading matching prefix or remaining suffix |
| `extend_yesno with changing xs, more` | append every yes/no value from `more` to `xs` |
| `clear_yesno with changing xs` | remove every item from `xs` |
| `insert_yesno with changing xs, index, value` | insert `value` before the 1-based index, clamped to front/end |
| `pop_yesno with changing xs, index` | maybe removed yes/no at a 1-based index |
| `remove_yesno with changing xs, value` | remove the first matching yes/no value; yes if one was removed |
| `sort_yesno with changing xs` | sort a yes/no list in place, with `no` before `yes` |
| `reverse_yesno with changing xs` | reverse a yes/no list in place |
| `count_yes with xs` / `count_no with xs` | count yes or no values |
| `count_yesno with xs, value` | occurrences of a yes/no value |
| `contains_yesno with xs, value` | yes when a yes/no value is present |
| `index_yes with xs` / `index_no with xs` | maybe 1-based index of the first yes or no |
| `index_yesno with xs, value` | maybe 1-based index of a yes/no value |
| `mode_yesno with xs` | most common yes/no value; ties keep the first value seen; empty lists fail |
| `modes_yesno with xs` | fresh yes/no list of all tied modes in first-seen order; empty lists give an empty list |
| `maybe_mode_yesno with xs` | maybe most common yes/no value |

Use `include "std/map"` for common map helpers:

| Function | Gives |
|---|---|
| `number_has_key with m, key` | yes when a text key is present in a number map |
| `number_has_value with m, value` | yes when a number value is present in a text-key number map |
| `number_at with m, key` | maybe number from a `map from text to number` |
| `take_number_at with changing m, key` | maybe number from a text-key map, removed when present |
| `take_number_or with changing m, key, fallback` | remove and return a text-key number value, or fallback when absent |
| `number_or with m, key, fallback` | number or fallback |
| `ensure_number_at with changing m, key, fallback` | existing number for `key`, or insert and return `fallback` |
| `add_count with changing m, key` | increments a text-key count in place |
| `copy_number_map with m` | fresh copy of a `map from text to number` |
| `update_number_map with changing m, more` | copy entries from `more` into a text-key number map, overwriting matching keys |
| `clear_number_map with changing m` | remove every entry from a `map from text to number` |
| `text_has_key with m, key` | yes when a text key is present in a text map |
| `text_has_value with m, value` | yes when a text value is present in a text-key text map |
| `text_at with m, key` | maybe text from a `map from text to text` |
| `take_text_at with changing m, key` | maybe text from a text-key map, removed when present |
| `take_text_or with changing m, key, fallback` | remove and return a text-key text value, or fallback when absent |
| `text_or with m, key, fallback` | text or fallback |
| `ensure_text_at with changing m, key, fallback` | existing text for `key`, or insert and return `fallback` |
| `copy_text_map with m` | fresh copy of a `map from text to text` |
| `update_text_map with changing m, more` | copy entries from `more` into a text-key text map, overwriting matching keys |
| `clear_text_map with changing m` | remove every entry from a `map from text to text` |
| `decimal_has_key with m, key` | yes when a text key is present in a decimal map |
| `decimal_has_value with m, value` | yes when a decimal value is present in a text-key decimal map |
| `decimal_at with m, key` | maybe decimal from a `map from text to decimal` |
| `take_decimal_at with changing m, key` | maybe decimal from a text-key map, removed when present |
| `take_decimal_or with changing m, key, fallback` | remove and return a text-key decimal value, or fallback when absent |
| `decimal_or with m, key, fallback` | decimal or fallback |
| `ensure_decimal_at with changing m, key, fallback` | existing decimal for `key`, or insert and return `fallback` |
| `copy_decimal_map with m` | fresh copy of a `map from text to decimal` |
| `update_decimal_map with changing m, more` | copy entries from `more` into a text-key decimal map, overwriting matching keys |
| `clear_decimal_map with changing m` | remove every entry from a `map from text to decimal` |
| `yesno_has_key with m, key` | yes when a text key is present in a yes/no map |
| `yesno_has_value with m, value` | yes when a yes/no value is present in a text-key yes/no map |
| `yesno_at with m, key` | maybe yes/no from a `map from text to yesno` |
| `take_yesno_at with changing m, key` | maybe yes/no from a text-key map, removed when present |
| `take_yesno_or with changing m, key, fallback` | remove and return a text-key yes/no value, or fallback when absent |
| `yesno_or with m, key, fallback` | yes/no or fallback |
| `ensure_yesno_at with changing m, key, fallback` | existing yes/no for `key`, or insert and return `fallback` |
| `copy_yesno_map with m` | fresh copy of a `map from text to yesno` |
| `update_yesno_map with changing m, more` | copy entries from `more` into a text-key yes/no map, overwriting matching keys |
| `clear_yesno_map with changing m` | remove every entry from a `map from text to yesno` |
| `number_key_number_has_key with m, key` | yes when a number key is present in a number-key number map |
| `number_key_number_has_value with m, value` | yes when a number value is present in a number-key number map |
| `number_key_number_at with m, key` | maybe number from a `map from number to number` |
| `take_number_key_number_at with changing m, key` | maybe number from a number-key map, removed when present |
| `take_number_key_number_or with changing m, key, fallback` | remove and return a number-key number value, or fallback when absent |
| `number_key_number_or with m, key, fallback` | number or fallback |
| `ensure_number_key_number_at with changing m, key, fallback` | existing number for `key`, or insert and return `fallback` |
| `add_number_key_count with changing m, key` | increments a number-key count in place |
| `copy_number_key_number_map with m` | fresh copy of a `map from number to number` |
| `update_number_key_number_map with changing m, more` | copy entries from `more` into a number-key number map, overwriting matching keys |
| `clear_number_key_number_map with changing m` | remove every entry from a `map from number to number` |
| `number_key_text_has_key with m, key` | yes when a number key is present in a number-key text map |
| `number_key_text_has_value with m, value` | yes when a text value is present in a number-key text map |
| `number_key_text_at with m, key` | maybe text from a `map from number to text` |
| `take_number_key_text_at with changing m, key` | maybe text from a number-key map, removed when present |
| `take_number_key_text_or with changing m, key, fallback` | remove and return a number-key text value, or fallback when absent |
| `number_key_text_or with m, key, fallback` | text or fallback |
| `ensure_number_key_text_at with changing m, key, fallback` | existing text for `key`, or insert and return `fallback` |
| `copy_number_key_text_map with m` | fresh copy of a `map from number to text` |
| `update_number_key_text_map with changing m, more` | copy entries from `more` into a number-key text map, overwriting matching keys |
| `clear_number_key_text_map with changing m` | remove every entry from a `map from number to text` |
| `number_key_decimal_has_key with m, key` | yes when a number key is present in a number-key decimal map |
| `number_key_decimal_has_value with m, value` | yes when a decimal value is present in a number-key decimal map |
| `number_key_decimal_at with m, key` | maybe decimal from a `map from number to decimal` |
| `take_number_key_decimal_at with changing m, key` | maybe decimal from a number-key map, removed when present |
| `take_number_key_decimal_or with changing m, key, fallback` | remove and return a number-key decimal value, or fallback when absent |
| `number_key_decimal_or with m, key, fallback` | decimal or fallback |
| `ensure_number_key_decimal_at with changing m, key, fallback` | existing decimal for `key`, or insert and return `fallback` |
| `copy_number_key_decimal_map with m` | fresh copy of a `map from number to decimal` |
| `update_number_key_decimal_map with changing m, more` | copy entries from `more` into a number-key decimal map, overwriting matching keys |
| `clear_number_key_decimal_map with changing m` | remove every entry from a `map from number to decimal` |
| `number_key_yesno_has_key with m, key` | yes when a number key is present in a number-key yes/no map |
| `number_key_yesno_has_value with m, value` | yes when a yes/no value is present in a number-key yes/no map |
| `number_key_yesno_at with m, key` | maybe yes/no from a `map from number to yesno` |
| `take_number_key_yesno_at with changing m, key` | maybe yes/no from a number-key map, removed when present |
| `take_number_key_yesno_or with changing m, key, fallback` | remove and return a number-key yes/no value, or fallback when absent |
| `number_key_yesno_or with m, key, fallback` | yes/no or fallback |
| `ensure_number_key_yesno_at with changing m, key, fallback` | existing yes/no for `key`, or insert and return `fallback` |
| `copy_number_key_yesno_map with m` | fresh copy of a `map from number to yesno` |
| `update_number_key_yesno_map with changing m, more` | copy entries from `more` into a number-key yes/no map, overwriting matching keys |
| `clear_number_key_yesno_map with changing m` | remove every entry from a `map from number to yesno` |

## Local packages

`parley package new name` creates `name/main.par`, a starter local package
that can be installed into a project.

`parley package install name source --version 1.0.0` copies a local package
directory or `.par` file into `parley_modules/name/`. Package names may contain
letters, numbers, dashes, underscores, and dots, and must start with a letter or
number. Package versions must use semantic `X.Y.Z` form, with optional
prerelease/build suffixes such as `1.2.3-beta.1+build.5`. Directory packages
need a `main.par`. Installs are recorded in `parley.lock.json` with the
package SHA-256, and `parley package list` prints the locked package names,
versions, and vendored paths.

Registry manifests use JSON:

```json
{"schema_version": 1, "packages": {"mathkit": {
  "version": "1.0.0", "source": "../mathkit", "description": "math helpers",
  "license": "MIT", "maintainer": "Your Name <https://example.com>",
  "sha256": "..."
}}}
```

`parley package search --registry registry.json` lists available packages, and
`parley package install mathkit --registry registry.json` vendors the package
named by the registry. Relative registry sources resolve from the manifest's
directory. A source may be a package directory, a single `.par` file, `file://`
URL, or an `http(s)` URL pointing at a `.par` file. When the registry entry has
`sha256`, install verifies the package before replacing an existing vendored
copy and writes the digest to `parley.lock.json`.

Use `parley package publish mathkit path --version 1.0.0 --description
"math helpers" --license MIT --maintainer "Your Name <https://example.com>"
--source packages/mathkit/main.par` to print a registry-ready JSON entry with
license, maintainer, and the deterministic package SHA-256. Directory packages
hash every file by relative path and content; single-file packages hash the
installed `main.par` layout. Add `--signing-key release-2026 --signing-secret
SECRET` to include an HMAC-SHA256 release signature in the entry.

Use `parley package review mathkit path --version 1.0.0 --description
"math helpers" --license MIT --maintainer "Your Name <https://example.com>"`
before submitting a package to a registry. It validates required metadata,
computes the deterministic SHA-256, parses every package `.par` file, and
prints the registry entry that would be submitted. It accepts the same
`--signing-key` / `--signing-secret` options as `publish`.

Use `parley package verify` after checkout, install, or before release. It
reads `parley.lock.json`, recomputes each vendored package digest, prints `OK`
for packages that still match, and exits non-zero if a package is missing, has
no recorded `sha256`, or has been modified locally.

Use `parley package check-registry registry.json` before hosting a registry.
It validates package names, required `version`, `description`, `license`,
`maintainer`, `source`, and `sha256` fields, resolves each source from the
registry location, recomputes the package digest, and exits non-zero if any
entry is incomplete, has a non-semantic version, or has changed.
Add `--require-signatures --signing-secret SECRET` to reject unsigned or
tampered package entries before hosting a signed registry.

The public starter index is hosted with the website at
`https://ded-furby.github.io/parley-lang/registry.json`.
