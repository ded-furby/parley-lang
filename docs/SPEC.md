# Parley specification (v0.4)

This document defines the language precisely enough to reimplement it.
For learning, read [TUTORIAL.md](TUTORIAL.md); for daily use,
[REFERENCE.md](REFERENCE.md).

## 1. Design goals

1. **Agents are the primary authors.** The grammar favours patterns language
   models already know deeply: English phrases, Python-style indentation,
   one canonical way to write each construct.
2. **Rust-grade output.** Compilation is a total function onto a memory-safe
   subset of Rust; rustc provides memory safety and native code generation.
3. **No prose-parsing.** Every tool surface (checker, build errors, runtime
   failures) is available as structured JSON with stable codes.
4. **Determinism.** Same program, same behaviour: map key/value iteration is
   sorted by key, printing a map orders it by key too, integer overflow and
   division by zero are defined (they stop the program), there is no
   undefined behaviour.

## 2. Lexical structure

* Source is UTF-8; string contents may be any text.
* Blocks are indentation-delimited (Python rules; 4 spaces conventional,
  tabs count as 8). Newlines end statements. Inside parentheses, newlines
  are insignificant.
* Comments run from `note:` or `#` to end of line.
* Multi-word phrases (`is more than`, `a list of`, `to the power of`, …) are
  single lexical tokens, matched with one-or-more spaces between words and a
  word boundary at the end. This is what makes English LALR(1)-parsable.
* Keyword tokens are matched contextually: words such as `length`, `position`,
  and `number` may name values because operators and type annotations are
  recognized only in their grammatical contexts. Thus `number as number`
  means a parameter named `number` whose type is `number`. The word remains
  reserved as a record, kind, or variant name because a user-defined type with
  that spelling could not be referenced unambiguously. In the inherently
  ambiguous `item position of values`, `position` is the item index; use
  parentheses when the index itself is a search expression: `item (position
  of needle in text) of values`. Words that are complete tokens by themselves
  (`is`, `of`, `item`, `a`, `sorted`, …) are reserved; the checker rejects
  them as names (P209). Operators added after v0.4 are therefore multi-word
  phrases (`the setting`, `the current time`, `files in`, `maybe item`): a
  single new keyword would silently break any existing program that already
  uses that word as a variable name.
* Literals: `INT /\d+/`, `FLOAT /\d+\.\d+/`, strings
  `"(\\.|[^"\\\n])*"` with escapes `\n \t \r \" \\` and `{expr}`
  interpolation (`{{`/`}}` for literal braces). An interpolated expression may
  contain text literals, written with escaped quotes:
  `"{name otherwise \"none\"}"`. An unescaped quote closes the string, so the
  error then lands on whatever followed it.

## 3. Grammar

The complete grammar is [`parley/grammar.lark`](../parley/grammar.lark)
(Lark dialect, LALR(1) + indentation post-lexer). It is normative; the
parse-relevant highlights:

* **rhs rule.** List literals (`a list of 1, 2`), empty containers, and record
  constructions appear only (a) directly after `be`, `to`, or `give back`, or
  (b) inside parentheses. This keeps their commas unambiguous against
  argument and field commas with one token of lookahead.
* **Calls.** Statement calls are bare: `f with a, b`. Expression calls are
  parenthesised: `(f with a, b)`. Zero-parameter functions are called by
  bare name. Multi-argument calls may use `and`; an `and` expression is split
  into arguments only when the named callee's arity proves the split.
* **repeat counts** accept addition/subtraction directly
  (`repeat n minus 1 times:`); parenthesise expressions containing
  multiplication or other operators to disambiguate the delimiter `times`.

## 4. Static semantics

The normal command target requires one parameterless, non-returning `main`
function (P210). The typed web target checks a module without requiring
`main`; its manifest-selected route and browser entry functions are separately
validated under the P710–P724 boundary rules in [WEB.md](WEB.md).

* **Program body.** Statements at the top level of a file are collected, in
  source order, into a synthesized `main`. A file that has top-level statements
  cannot also define `to main:` (P212), so a program has exactly one entry
  point either way. Includes are spliced textually before parsing, so an
  included file may contain only functions, records, and enums; top-level
  statements in an included file are rejected against that file and line
  (P213).

* **Variable introduction.** `let name be value` always creates a variable.
  `set name to value` creates it when absent and mutates it when present;
  field targets still require an existing base variable.
* **Natural statement aliases.** `print` is `say`, `return` is `give back`,
  and `sort xs` replaces an existing list with its sorted copy.
  `sorted xs by field` orders a `list of R` for a record `R` by one of its
  fields, which must be number, decimal, text, or yesno (P316); an unknown
  field is P204. The sort is stable and ascending, so equal keys keep source
  order and `reversed` gives the descending order. `sort xs by field` is the
  statement spelling of the same operation.
  `stop` outside a loop is valid only in `main`, where it returns from the
  program.
* **Types** as in REFERENCE.md. No implicit conversions except
  number → decimal promotion (at assignment, argument, return and mixed
  arithmetic positions). Division always yields decimal.
* **Whole-number remainder** has three equivalent spellings: `a % b`, `a
  modulo b`, and `remainder of a divided by b`. All use the same guarded
  operation and reject a zero divisor at runtime. Negative operands follow
  Rust remainder semantics: the result has the dividend's sign, so `-5 modulo
  3` is `-2`. `modulo` has the same precedence as multiplication and division.
* **Scopes.** One namespace for variables; functions, record names, enum
  names and variants are global. A `let` binds until the end of its block;
  redeclaration and shadowing are errors (P209). `set` requires an existing
  binding (P211).
* **Map keys** are `number` or `text` (P309) so iteration can be sorted.
  `keys of m` returns sorted keys; `values of m` returns values in sorted-key
  order. `remove item key of m` removes a map entry if it exists and leaves
  the map unchanged when it does not. Item indexes, keys, and replacement
  values are evaluated before the collection is mutably borrowed, so they may
  read the same list or map being changed.
* **`when`** over an enum must be exhaustive or carry `otherwise:` (P208);
  over yesno, covering `yes` and `no` counts as exhaustive; over numbers and
  text, `otherwise:` is mandatory. An arm may list several patterns
  (`is 1, 2 or 3:`) and, when the subject is numeric, inclusive ranges
  (`is 10 to 20:`); range ends are literals of the subject's type, smaller
  first (P312).
* **Function values.** `the function f` is a value of type
  `(function taking …  giving …)`, represented as a cloneable Rust
  `Rc<dyn Fn...>`. Only plain defined functions qualify: not `main` and not
  functions with `changing` parameters (P313). A variable holding a function
  value is called with the ordinary call forms. Function values cannot be
  compared, converted to text, or said (P301).
* **Anonymous functions.** `a function taking x as number giving number:`
  creates a function value. Its indented body follows the same statement rules
  as a named function body. Outside variables read by the body are captured by
  value at creation time; later changes to the original variable do not affect
  the closure. Captured values cannot be changed inside the closure (P314).
* **Functions** with `giving T` must give back on every path (P304). A `fail`
  statement is terminal and therefore satisfies a returning path.
  `changing` parameters require a plain variable argument of exactly the
  parameter's type (P305). Parameter declarations may be comma-separated or
  `and`-separated. In the natural `and` form, a list/map parameter directly
  mutated by the body is inferred as `changing`; comma-separated declarations
  retain value semantics unless `changing` is explicit.
* **Maybe values.** `nothing` is assignable to any `maybe T`; `some expr`
  constructs a `maybe` containing `expr`'s type. `value of` unwraps a maybe
  and is a checked runtime operation. `expr otherwise fallback` requires
  `expr` to be `maybe T` (P315) and `fallback` to be assignable to `T`; it
  gives `T`, never stops the program, and evaluates `fallback` only when
  `expr` is nothing. It binds tighter than comparison and looser than
  arithmetic, so `x otherwise 0 is more than 5` groups as
  `(x otherwise 0) is more than 5`. `has no value` aliases `is nothing`;
  `has value` and `has a value` alias `is not nothing`.
  For text, `expr as number` is exactly the checked composition
  `value of (number from expr)` and therefore stops on invalid input.
  `expr as text` is exactly `text from expr`.
* **`assert condition`** requires `condition` to be yesno. Its optional
  message form, `assert condition, expr`, requires `expr` to be text. A failed
  assertion is a catchable runtime failure.
* **`fail expr`** requires `expr` to be text. It stops the current execution
  with that message and can be caught by an enclosing `attempt:`.
* **`attempt`** bodies may not `give back`, and may not `stop`/`skip` loops
  that started outside the attempt (P310).
* The checker is total: any program it accepts must compile under rustc.
  A rustc rejection is a Parley bug, surfaced as P901 with the source line.

## 5. Dynamic semantics

* **Value model.** Parley exposes value semantics: assignment, construction,
  return, and `for each` iteration copy heap values. In generated Rust,
  read-only non-`changing` heap parameters are borrowed and are cloned only if
  the callee stores or mutates its local parameter. The only user-visible
  aliasing is `changing` parameters, which are exclusive mutable borrows for
  the call. A loop variable may be assigned inside its body; the assignment is
  local to that iteration and does not change the source collection, range
  bounds, or next iteration value.
* **Text joining.** `plus` with text on either side formats the other value
  using the same rules as interpolation and returns text. Adding a non-text
  value to a `list of text` applies the same destination-aware formatting.
* **Numbers** are 64-bit (`i64`/`f64`). Integer overflow stops the program with
  an English runtime failure, in every build: the generated release profile
  sets `overflow-checks = true`, so `parley build` and `parley run` agree and
  release binaries never wrap. When the operands are literals, rustc proves the
  overflow up front and it is reported as P317 before the binary exists.
  `a divided by b` is IEEE-754 division after promotion, with `b = 0`
  stopping the program.
  Bundled `std/math` includes `factorial`, returning `1` for `0`, multiplying
  whole numbers through `n`, and failing with English text for negative input.
  `greatest_common_divisor` and `least_common_multiple` normalize negative
  inputs to positive whole-number results; their zero behavior follows
  Python's `math.gcd` and `math.lcm` conventions.
  `combination_count` and `permutation_count` return exact whole-number
  counts, return `0` when the chosen count is larger than the total, and fail
  with English text for negative inputs.
  `integer_square_root` returns the floor of the square root for non-negative
  whole numbers and fails with English text for negative input;
  `is_perfect_square` returns no for negative inputs.
  `is_close` checks decimal closeness using explicit relative and absolute
  tolerances and fails with English text when either tolerance is negative.
  `hypotenuse` returns the decimal square root of `x*x + y*y`.
  `distance_2d` and `distance_3d` return Euclidean decimal distances between
  two typed coordinate points.
  `copy_sign` returns the absolute magnitude with the sign of another decimal
  source, treating zero sign sources as non-negative.
  `pi_value`, `tau_value`, and `e_value` expose common decimal math constants
  as zero-parameter helpers.
  `radians_from_degrees` and `degrees_from_radians` convert decimal angles
  using the usual pi-based relationship between degrees and radians.
* **Text operations** such as `split by`, `joined with`, `item i of text`,
  `starts with`, `ends with`, `contains`, `replacing old with new`,
  `position of needle in text`, and `count of needle in text` are
  deterministic UTF-8 string operations.
  Splitting by empty text returns a list of Unicode characters.
  `item i of text` uses 1-based character indexing and returns a one-character
  text value.
  Bundled `std/text` helpers such as `maybe_character` and `text_slice` use
  the same 1-based UTF-8 character indexing.
  `reversed_text` reverses by those same UTF-8 characters and leaves empty
  text empty.
  `partition_text` returns a three-item `list of text`: text before the first
  separator match, the separator, and text after it. Missing or empty
  separators produce the stable absent shape `[t, "", ""]`.
  `rpartition_text` uses the same three-item shape for the last separator
  match. Missing or empty separators produce the right-absent shape
  `["", "", t]`.
  `split_text` splits at most `max_splits` separator matches from the left,
  returns left-side pieces followed by the unsplit right side in original
  order, and returns `[t]` for empty separators or non-positive split counts.
  `rsplit_text` splits at most `max_splits` separator matches from the right,
  returns the unsplit left side followed by right-side pieces in original
  order, and returns `[t]` for empty separators or non-positive split counts.
  `replaced_text` replaces at most `max_replacements` non-overlapping matches
  of `old` with `new`, returns the original text for empty `old` or
  non-positive counts, and uses the same UTF-8 character semantics as other
  text helpers.
  `last_position` returns `some n` for the last 1-based UTF-8 character
  position of a needle, supports overlapping matches, returns `nothing` for
  an absent needle, and returns the final text boundary for an empty needle.
  `position_or_zero` and `last_position_or_zero` unwrap search positions to a
  number, returning `0` when the needle is absent.
  Replacement returns a new text value and does not mutate the original text.
  `without_prefix` and `without_suffix` return the original text unchanged
  when the requested edge text is empty or absent. `left_trimmed_of`,
  `right_trimmed_of`, and `trimmed_of` remove any leading/trailing UTF-8
  character that appears in an explicit character-set text, and leave the
  original text unchanged for an empty character set.
  `has_prefix` and `has_suffix` return yes for matching text edges and also
  for empty prefix or suffix checks. `has_any_prefix` and `has_any_suffix`
  scan a list of candidate edges, return yes on the first match, return no
  for an empty candidate list, and keep the same empty-edge match behavior as
  the single-edge helpers.
  `lines_of` returns an empty list for empty text, otherwise the raw
  newline-separated lines including blank middle lines and trailing empty
  lines.
  `split_lines` returns an empty list for empty text, splits on `\n`, `\r`,
  and `\r\n` line boundaries, preserves blank middle lines, and omits the
  synthetic final empty item for terminal line breaks. `split_lines_kept`
  uses the same line boundaries but retains the matched newline text on each
  returned line.
  `word_count` and `words_of` split on space, tab, newline, and carriage
  return boundaries, collapse repeated whitespace, ignore leading and trailing
  whitespace, and return `0` or an empty list for all-whitespace text.
  `is_whitespace`, `left_trimmed`, and `right_trimmed` treat space, tab,
  newline, and carriage return as whitespace characters.
  `is_space` is a non-empty whole-text predicate over those same whitespace
  characters.
  `capitalized` returns empty text unchanged, uppercases the first UTF-8
  character, and lowercases the rest of the text.
  `case_folded` lowercases the text and folds `ß` to `ss`, so common
  case-insensitive comparisons can use equality on the folded values.
  `is_digit`, `is_alpha`, `is_alphanumeric`, `is_identifier`, `is_lowercase`, and
  `is_uppercase` are non-empty whole-text predicates over ASCII digits and
  letters. Identifier checks require a first ASCII letter or underscore and
  then ASCII letters, digits, or underscores. Lowercase and uppercase
  predicates accept only letters of that case. `is_ascii` accepts empty text,
  tab, newline, carriage return, and printable ASCII characters from space
  through `~`.
  `is_printable` accepts empty text, spaces, ordinary printable text, and
  non-ASCII printable characters, and rejects tab, newline, and carriage
  return controls.
  `swap_case` swaps ASCII lowercase and uppercase letters and leaves
  digits, spaces, punctuation, and non-ASCII characters unchanged.
  `title_cased` uppercases the first character of each whitespace-delimited
  word, lowercases the rest of each word, preserves the original whitespace,
  and returns empty text unchanged.
  `is_titlecase` returns yes when non-empty text contains at least one ASCII
  letter and is already equal to its `title_cased` form.
  `padded_left`, `padded_right`, and `padded_center` repeat a non-empty fill
  text enough times to reach the requested width, leaving text unchanged when
  already wide enough or when the fill text is empty. Center padding alternates
  right then left, so an odd gap places the extra fill on the right.
  `zero_filled` pads with zeroes to the requested width and preserves an
  initial `+` or `-` before inserted zeroes.
  `tabs_expanded` replaces tabs with spaces up to the next tab stop, counts
  UTF-8 characters as columns, resets the column after newline or carriage
  return, and removes tabs when the requested tab size is non-positive.
  Position returns `some n` with a 1-based character position, or `nothing`
  when the needle is absent. Count returns the number of non-overlapping
  matches; an empty needle counts the character boundaries, so it returns
  `length of text plus 1`.
* **Bundled list helpers** in `std/list`, including `list_slice_number`,
  `list_slice_text`, `list_slice_decimal`, and `list_slice_yesno`, use
  1-based inclusive indexes. Slice helpers clamp bounds to the list and give
  an empty list for reversed or out-of-range requests. Stepped slice helpers
  use the same bounds but include every `step`th item and fail for
  non-positive steps. Count-based take helpers return the first `count` items,
  with non-positive counts returning an empty list; count-based drop helpers
  return everything after the first `count` items, with non-positive counts
  returning a fresh copy. Tail take helpers return the last `count` items,
  with non-positive counts returning an empty list; tail drop helpers return
  everything before the last `count` items, with non-positive counts returning
  a fresh copy. List prefix/suffix predicates compare typed values in order,
  return yes for empty candidate lists, and return no when the candidate is
  longer than the source list. Enumerate helpers return fresh number-key maps from 1-based
  indexes, or from a caller-provided starting key in the `_from` variants, to
  the corresponding typed list values. Copy helpers return a
  fresh number, text, decimal, or yes/no list with the same items. Yes/no edge
  helpers mirror the number, text, and decimal first/last helpers, including
  maybe-returning empty-list variants. Extend, clear, insert, pop, remove,
  sort, and reverse helpers take a `changing` list parameter and mutate the
  caller's list. Chain helpers return fresh typed lists containing all values
  from the left input followed by all values from the right input, without
  mutating either input. Unique helpers return fresh typed lists with duplicate
  values removed while preserving first-seen order. Number range helpers return
  fresh number lists with Python-style stop-exclusive bounds, including
  positive and negative stepped ranges; a step of `0` fails with English text.
  Repeat helpers return fresh typed lists containing a
  requested number of copies of one value, or an empty list for non-positive
  counts. Cycle helpers return fresh typed lists by repeatedly walking a
  source list until the requested count is reached, with empty output for
  empty source lists or non-positive counts. Insert helpers clamp the target
  index: 1 or below inserts at the front, and an index past the end appends.
  Pop helpers return `maybe`
  values, removing a valid 1-based item and returning `nothing` without
  mutation for out-of-range indexes. Remove helpers delete the first matching
  value and return yes/no for whether anything changed. Filter helpers accept
  a first-class predicate function, return a fresh list, and preserve the
  original order of values where the predicate returns yes. Map helpers accept
  a first-class same-type transform function, return a fresh list, and
  preserve item order. Predicate any/all helpers accept first-class predicate
  functions, short-circuit over list items, and return no/yes respectively for
  empty lists. Fold helpers accept first-class two-argument same-type
  accumulator functions, scan left to right, and return the explicit initial
  value for empty lists. Maybe-find helpers accept first-class predicate
  functions, return `some value` for the first matching item, and return `nothing` for
  empty lists or no-match scans. Predicate-count helpers accept first-class
  predicate functions and return the number of matching items, with `0` for
  empty lists. Predicate-index helpers return `some index` with a 1-based
  position for the first matching item, or `nothing` for empty lists/no-match
  scans. Predicate all-index helpers return fresh `list of number` values with
  every 1-based position where the predicate matches, or an empty list for
  empty/no-match scans. Take/drop-while helpers accept first-class predicate functions,
  split the leading matching prefix from the remaining suffix, and return
  fresh lists. Reject helpers accept first-class predicate functions and return
  fresh lists of values where the predicate returns `no`. Compress helpers
  accept a parallel `list of yesno` selector list, scan by 1-based position
  until either list ends, and return a fresh typed list of values whose
  selector is yes. Count, index, and
  membership helpers work
  over number, text, decimal, and yes/no items.
  Sort helpers reorder
  number, text, decimal, and yes/no caller lists in place, with yes/no sorting
  placing `no` before `yes`. Reverse helpers reorder number, text, decimal,
  and yes/no caller lists in place. Sum helpers wrap the built-in list sum for
  number and decimal lists and return the additive identity for empty lists.
  Accumulated-sum and accumulated-product helpers scan number or decimal lists
  left to right and return a fresh list containing each running total or
  running product. Accumulated-minimum and accumulated-maximum helpers scan
  ordered number, decimal, or text lists left to right and return a fresh list
  containing each running minimum or running maximum. All accumulated helpers
  return an empty list for empty inputs.
  Product helpers multiply every number or decimal item and return the
  multiplicative identity for empty lists.
  Sum-product helpers multiply matching number or decimal items pairwise,
  add the products, return the additive identity for two empty lists, and fail
  with English text when the list lengths differ.
  Median helpers sort a fresh number or decimal copy, return the middle value
  or the average of the two middle values as a decimal, fail with English text
  on empty lists, and also have maybe-returning empty-list-safe variants.
  Median-low and median-high helpers return the lower or upper middle value
  from that sorted copy, preserving the original number or decimal item type,
  and also have maybe-returning empty-list-safe variants.
  Mode helpers for number, text, decimal, and yes/no lists scan the original
  list, return the most common value, keep the first value seen when counts
  tie, fail with English text on empty lists, and also have maybe-returning
  empty-list-safe variants.
  Plural mode helpers return every value tied for the highest count in
  first-seen order, suppress duplicates, and return an empty typed list for an
  empty input list.
  Population variance helpers for number and decimal lists return the mean of
  squared distances from the list average as a decimal, using the full list
  length as the denominator. Population standard-deviation helpers return the
  square root of that variance. Empty population-statistics inputs fail with
  English text, and maybe-returning variants return `nothing` instead.
  Sample variance helpers use the same squared-distance total but divide by
  `length minus 1`, matching the usual unbiased sample estimate. Sample
  standard-deviation helpers return the square root of that sample variance.
  Inputs shorter than two items fail with English text, and maybe-returning
  variants return `nothing` instead.
  Geometric mean helpers for number and decimal lists multiply non-negative
  values and raise the product to `1 divided by length`, returning `0.0` when
  any value is zero. Harmonic mean helpers divide the list length by the sum
  of reciprocal values, returning `0.0` when any value is zero. Empty inputs
  and negative values fail with English text; maybe-returning variants return
  `nothing` for those invalid inputs.
  Quantile helpers for number and decimal lists sort a fresh copy and return
  `groups minus 1` decimal cut points. `quantiles_*` uses the exclusive rank
  `i times (length plus 1) divided by groups`; `inclusive_quantiles_*` uses the
  inclusive rank `1 plus i times (length minus 1) divided by groups`.
  `groups` must be at least `1`, `groups` of `1` returns an empty list,
  singleton inputs repeat the only value, and empty inputs fail with English
  text. Maybe-returning variants return `nothing` for invalid groups or empty
  inputs.
  Covariance helpers for number and decimal list pairs return sample
  covariance as a decimal, requiring equal-length inputs with at least two
  items. Correlation helpers return Pearson correlation by dividing the shared
  deviation total by the square root of the two individual deviation totals;
  equal-length inputs with at least two items are required, and constant input
  lists fail with English text. Maybe-returning variants return `nothing` for
  invalid lengths, too-short inputs, or constant correlation inputs.
  Linear-regression helpers for number and decimal list pairs return a
  two-item `list of decimal`: slope first, intercept second. Ordinary
  regression uses the same centered deviation totals as covariance, requires
  equal-length inputs with at least two items, and fails when the x input is
  constant. Proportional regression forces the intercept to `0.0`, computes
  slope as `sum(x times y) divided by sum(x times x)`, and fails when all
  x values are zero. Maybe-returning variants return `nothing` for invalid
  shapes or unusable x inputs.
* **Bundled map helpers** in `std/map` provide key membership checks, value
  membership checks, maybe lookup, fallback lookup, fallback insertion,
  counted increments, copy helpers, update helpers, take helpers,
  take-with-fallback helpers, and clear helpers for text-key and number-key
  maps. Value membership helpers scan map values and return yes when any value
  is equal to the requested value. Ensure helpers use a `changing`
  target map, return the present value when the key exists, otherwise insert
  the fallback and return it. Copy helpers return fresh maps with the same
  entries. Update helpers use a `changing` target map and copy every entry
  from the second map into it, overwriting matching keys and inserting missing
  ones. Take and clear helpers use `changing` map parameters: maybe take
  helpers return `some value` and remove a present key, or return `nothing`
  without mutation when the key is absent; take-with-fallback helpers remove
  and return a present value, or return the fallback when the key is absent;
  clear helpers remove every entry.
* **Failures.** These stop the program with an English message and exit
  code 1: failed `assert`, `fail`, division/remainder by zero, out-of-range
  `item`, `value of` nothing, smallest/largest of an empty list, negative
  `square root of`, negative integer powers, overflowing powers, file write
  failures, reading input past end-of-file. An enclosing `attempt:` catches
  them; `the error` then holds the message.
* **I/O.** `say` writes a line to stdout. `ask` prompts on stdout and reads
  one line from stdin. File operations are whole-file. `a random number` is
  a non-cryptographic xorshift seeded from the clock.
* **Program inputs.** `the arguments` is the `list of text` of command-line
  words after the program name; `parley run file.par ARG…` forwards its
  trailing arguments unchanged, flags included. `the input` is the `list of
  text` of every line of standard input, with a trailing newline and any `\r`
  removed and empty input giving an empty list. Both name values, not streams:
  `the input` drains stdin at most once and every later mention sees the same
  lines. A program should therefore use `the input` or `ask`, not both.
* **JSON.** `a R from json t` decodes text into record `R`, giving `maybe R`:
  `nothing` for malformed JSON, a missing required field, a wrong field type,
  or an unknown field — the same `deny_unknown_fields` strictness the typed web
  layer applies. A `maybe T` field is the one exception: an absent key decodes
  as `nothing`, which is what `maybe` already means. `x as json` encodes any
  JSON-safe value as text. Both directions accept exactly the types the web
  layer accepts: number, decimal, text, yesno, kinds, lists, text-keyed maps,
  and records of those; anything else is P317. Maps encode in key order, so the
  same value always produces the same bytes. A program that never mentions JSON
  builds with no dependencies at all; one that does adds serde and about 68 KiB
  to the binary.
* **Environment and clock.** `the setting "NAME"` gives `maybe text` for an
  environment variable. `the current time` gives whole seconds since the Unix
  epoch; like `a random number` it is a deliberate exception to design goal 4,
  and a program that wants reproducible output must not print it directly.
* **Directory listing.** `files in path` gives `maybe list of text`: the
  sorted paths of the regular files directly in that directory, excluding
  subdirectories, or `nothing` when the directory cannot be read. Sorting is
  what makes a program that walks a directory produce the same output twice.
* **Non-failing access.** `maybe item i of x` is `item i of x` with the failure
  turned into `nothing`: it gives `maybe T` for a `list of T`, `maybe text` for
  text, and `maybe V` for a `map from K to V`, and never stops the program.
  With `otherwise` it is the one-line safe-access form for every container.
* **Decimal rendering.** A `decimal` renders with Rust's shortest
  round-tripping `f64` Display, so `1.0` and `7 divided by 7` both print `1`
  with no fractional part, and `0.1 plus 0.2` prints `0.30000000000000004`.
  Output therefore does not distinguish a whole-valued `decimal` from a
  `number`; use `"{d}"` with an explicit format of your own if a program needs
  the distinction on stdout.
* **Rendering.** A said or interpolated value renders by its static type, and
  the rendering is total and deterministic. Text and numbers print bare at the
  top level and quoted/Debug-shaped inside a container. A `yesno` prints
  `yes`/`no` at every depth — inside lists, maps, records, and maybes, not only
  as a bare value. A `maybe` prints `nothing` or its inner value. A map prints
  its entries in sorted-key order, so a program's output never depends on hash
  iteration order. Lists keep source order; records print `Name { field: value,
  … }` in declaration order.

## 6. Compilation model

```
program.par ──parse──▶ AST ──check──▶ typed AST ──emit──▶ main.rs ──cargo──▶ native binary
                │            │                                  │
                ▼            ▼                                  ▼
              P1xx         P2xx/P3xx                 P9xx (mapped back by line)
```

* The emitter writes a single `main.rs`: a fixed helper prelude (≈200 lines,
  zero external crates), one item per Parley declaration, and a `fn main`
  that installs an English panic handler around the program.
* A line map (rust line → parley file/line) accompanies emission; any
  residual rustc diagnostic is translated through it.
* `include "x"` is textual. It first resolves `x` relative to the including
  file, then as `parley_modules/x`, then through bundled standard packages,
  then through `PARLEY_PATH` roots. Package directories load `main.par`.
* `parley package install name source --version X` vendors a local package
  directory or `.par` file into `parley_modules/name/` and records it in
  `parley.lock.json` with the deterministic package SHA-256. Package versions
  must use semantic `X.Y.Z` form, with optional prerelease/build suffixes.
  Registry entries may include `sha256`; when present, install verifies it
  before replacing an existing vendored package. `parley package publish name
  source --version X` requires license and maintainer metadata, then prints a
  registry-ready entry with those fields and that digest. With
  `--signing-key KEY --signing-secret SECRET`, `publish` and `review` also
  attach an HMAC-SHA256 release signature over the canonical registry fields.
  `parley package review name source --version X` validates submission
  metadata, computes the same digest, parses package `.par` files, and prints
  the registry entry that would be submitted. `parley package verify`
  recomputes vendored package digests from the lockfile and fails if a package
  is missing, unchecked, or modified. `parley package check-registry registry`
  validates a public registry manifest before hosting by checking package
  names, required version, description, license, maintainer, and source
  metadata, readable sources, digest matches, and, when
  `--require-signatures --signing-secret SECRET` is used, release signatures.
* `parley doctor` verifies the installed toolchain: Parley version, Python
  version, Rust `cargo`, bundled standard packages, and local package state.
* Build directory: `.parley-build/<program>/` with a shared cargo target dir
  in `.parley-build/target/`.

## 7. Stability

v0.3 is an experiment. Syntax may change; error codes are append-only.
Known limits: no generics for user functions, no methods, single-threaded, and
no decentralized public-key package trust network. Function values exist for
named functions without `changing` parameters and anonymous functions with
value captures. See the README roadmap.
