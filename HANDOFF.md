# Parley — agent handoff

Read this first. It is the single source of truth for what this project is
trying to achieve, what is already done, and exactly where to pick up.
Update it whenever you finish or start a work item.

## The goals (in priority order)

1. **A complete programming language.** English-like syntax easier than
   Python, Rust-level speed and safety (it transpiles to Rust and ships
   native binaries). A user must be able to write, `parley check`,
   `parley run`, and `parley build` any reasonable program. AI agents are
   the primary authors: one canonical way to write each construct, and
   every compiler error is a JSON repair instruction with a stable P-code.
2. **A landing page** (one page, scrolling, Three.js, cursor-controlled 3D,
   unique, craft level above igloo.inc without copying it).
3. **The research angle.** Formalise token efficiency as a language-design
   metric; benchmark agent error rates across Python/Rust/Zero/Parley;
   publish on arXiv with a USYD professor. (Arjun's long-term goal.)

## Where things stand (2026-06-22)

### Done and verified

- **Language v0.3 / toolchain v0.3.135** — full pipeline (Lark LALR parse → checker → Rust emit
  → cargo). The latest local suite has 251 tests, including e2e tests that
  compile every feature to a native binary and assert stdout. Eleven examples in
  `examples/`. Docs: `docs/TUTORIAL.md`, `REFERENCE.md`, `SPEC.md`,
  `ERRORS.md` (generated from `parley/diagnostics.py` — regenerate it if
  you add a P-code; `tests/test_diagnostics.py` enforces coverage).
- **v0.2 features just added:** richer `when` patterns (multi-value arms
  `is 1, 2 or 3:`, inclusive numeric ranges `is 10 to 20:`, new P312) and
  first-class function values (`the function f`, type
  `(function taking A giving R)`, now represented as cloneable `Rc<dyn Fn>`,
  new P313). Also fixed a latent bug: `when` over a decimal with an integer
  arm used to emit Rust that did not compile (now typed literals, see
  `_pattern_num`).
- **v0.3 closure feature:** anonymous function literals
  (`a function taking x as number giving number:`) capture outside values at
  creation time, can be passed anywhere a `(function ...)` value is expected,
  and add P314 for attempts to mutate captured values.
- **v0.3 backend optimisation:** non-`changing` heap parameters are borrowed
  in generated Rust; a callee clones its local parameter only if it stores or
  mutates that parameter, preserving Parley value semantics without cloning
  every read-only call argument.
- **v0.3.1 editor tooling:** `parley-lsp` is a stdio Language Server Protocol
  server that publishes the same parser/checker P-code diagnostics as
  `parley check --json` for open `.par` documents.
- **v0.3.2 package includes:** `include "name"` can resolve packages from
  `parley_modules/name/main.par` and from package roots listed in
  `PARLEY_PATH`, while preserving source maps and P105 include diagnostics.
- **v0.3.3 bundled stdlib:** `include "std/math"` provides `clamped`,
  `between`, and `percent_of`; `include "std/text"` provides `is_blank`,
  `repeated_text`, and `surrounded_with`. These `.par` files are packaged in
  the wheel under `parley/stdlib/`.
- **v0.3.4 local package workflow:** `parley package install name source
  --version X` vendors a local package into `parley_modules/name/` and records
  it in `parley.lock.json`; `parley package list` prints the lockfile.
- **v0.3.5 bundled list helpers:** `include "std/list"` provides first/last,
  count, index, and average helpers for number and text lists.
- **v0.3.6 maybe constructor:** `some expr` constructs a present `maybe`
  value, so functions can directly `give back some index` alongside
  `give back nothing`.
- **v0.3.7 bundled map helpers:** `include "std/map"` provides maybe lookups,
  fallback lookups, and a text-key count helper for common map workflows.
- **v0.3.8 package skeletons:** `parley package new name` creates an
  installable local package directory with `main.par`.
- **v0.3.9 setup doctor:** `parley doctor` and `parley doctor --json` verify
  the local Parley version, Python version, Rust `cargo`, bundled stdlib, and
  local package state.
- **v0.3.10 custom runtime failures:** `fail "message"` stops execution with
  a user-provided English message, is catchable by `attempt:`, and counts as a
  terminal path for returning functions.
- **v0.3.11 runtime assertions:** `assert condition, "message"` checks
  invariants with a yes/no condition, optional text message, and catchable
  runtime failure semantics.
- **v0.3.12 benchmark CLI:** `parley benchmark measure`, `parley benchmark
  append`, and `parley benchmark summarize` expose the research harness from
  the installed command when run inside a source checkout.
- **v0.3.13 registry-backed packages:** `parley package search --registry`
  reads a schema-1 package manifest, and `parley package install name
  --registry registry.json` vendors a listed package while preserving the
  lockfile workflow.
- **v0.3.14 hosted starter package index:** GitHub Pages now serves
  `/registry.json` plus starter `mathkit` and `textkit` packages under
  `/packages/`, and the deploy script publishes those assets.
- **v0.3.15 package integrity:** registry entries can carry `sha256`,
  installs verify the package before replacing an existing vendor directory,
  `parley.lock.json` records the installed digest, and `parley package
  publish` prints a registry-ready JSON entry for local package sources.
- **v0.3.16 package lock verification:** `parley package verify` recomputes
  vendored package digests from `parley.lock.json`, reports missing or legacy
  unchecked entries, and fails if a local package has been modified.
- **v0.3.17 registry validation:** `parley package check-registry registry.json`
  validates public package manifests before hosting: package names, required
  version/description/source fields, mandatory `sha256`, readable sources, and
  digest matches.
- **v0.3.18 package ownership metadata:** public registry entries now carry
  required `license` and `maintainer` fields, `parley package publish` requires
  them when printing a registry entry, and `parley package check-registry`
  rejects hosted manifests that omit either field.
- **v0.3.19 package version governance:** package install, publish, and
  registry validation now require semantic package versions in `X.Y.Z` form
  with optional prerelease/build suffixes.
- **v0.3.20 benchmark reference manifest:** `benchmarks/tasks.json` now records
  the Parley, Python, and Rust source path for every seed task, and tests verify
  that those declared references exist.
- **v0.3.21 package submission review:** `parley package review` dry-runs a
  package submission by validating metadata, computing the deterministic
  SHA-256, parsing package `.par` files, and printing the registry entry that
  would be submitted.
- **v0.3.22 signed package releases:** `parley package publish` and `review`
  can attach HMAC-SHA256 release signatures, and `parley package
  check-registry --require-signatures --signing-secret ...` rejects unsigned or
  tampered registry entries before hosting.
- **v0.3.23 benchmark prompts:** `parley benchmark prompt` renders
  language-neutral prompts from `benchmarks/tasks.json`, so repeated agent
  runs can use the same task wording without exposing reference sources.
- **v0.3.24 stdlib coverage:** `std/text` adds `line_count`,
  `nonempty_line_count`, and `word_count`; `std/list` now has decimal
  first/last/count/index/average helpers to match the existing number and text
  helpers.
- **v0.3.25 number-key map helpers:** `std/map` now has maybe lookup,
  fallback lookup, and count-increment helpers for `map from number to number`,
  plus maybe/fallback lookup helpers for `map from number to text`.
- **v0.3.26 safe list edge helpers:** `std/list` adds maybe-returning
  first/last helpers for number, text, and decimal lists so empty-list cases
  can stay explicit instead of becoming runtime failures.
- **v0.3.27 safe list aggregates:** `std/list` adds maybe-returning
  smallest/largest helpers for number, text, and decimal lists, plus
  maybe-returning average helpers for number and decimal lists.
- **v0.3.28 yes/no list helpers:** `std/list` adds `all_yes`, `any_yes`,
  `count_yes`, `count_no`, `index_yes`, and `index_no` for boolean-list
  workflows.
- **v0.3.29 decimal and yes/no map helpers:** `std/map` adds maybe and
  fallback lookups for decimal and yes/no values under both text and number
  keys. Present `maybe yesno` values now print as `yes`/`no` instead of Rust's
  raw `true`/`false`.
- **v0.3.30 safe list indexing:** `std/list` adds `maybe_item_number`,
  `maybe_item_text`, `maybe_item_decimal`, and `maybe_item_yesno`, returning
  `nothing` for non-positive and out-of-range indexes.
- **v0.3.31 decimal math helpers:** `std/math` adds `clamped_decimal`,
  `between_decimal`, and `percent_of_decimal`, matching the existing number
  helper workflows for decimal values.
- **v0.3.32 text extraction helpers:** `std/text` adds `words_of` and
  `nonempty_lines`, returning cleaned `list of text` values for common
  text-processing workflows.
- **v0.3.33 text replacement operator:** text expressions support
  `text replacing old with new`, type-checking all operands as `text` and
  compiling to Rust's string replacement.
- **v0.3.34 text search positions:** text expressions support
  `position of needle in text`, returning `maybe number` with 1-based
  character positions so absent matches stay explicit.
- **v0.3.35 text occurrence counts:** text expressions support
  `count of needle in text`, returning non-overlapping occurrence counts with
  UTF-8 character semantics for empty needles.
- **v0.3.36 text item access:** `item i of text` now returns the 1-based
  UTF-8 character at position `i` as text, with English runtime failures for
  out-of-range positions.
- **v0.3.37 safe text character helper:** `std/text` adds
  `maybe_character`, returning `maybe text` for 1-based UTF-8 character lookup
  without runtime failure on non-positive or out-of-range indexes.
- **v0.3.38 UTF-8 text slice helper:** `std/text` adds `text_slice`, returning
  clamped 1-based inclusive character slices and empty text for reversed or
  out-of-range requests.
- **v0.3.39 clamped list slice helpers:** `std/list` adds
  `list_slice_number`, `list_slice_text`, `list_slice_decimal`, and
  `list_slice_yesno`, returning list slices with clamped 1-based inclusive
  bounds.
- **v0.3.40 list mutation helpers:** `std/list` adds `extend_number`,
  `extend_text`, `extend_decimal`, `extend_yesno`, and matching `clear_*`
  helpers, using `changing` parameters to mutate caller lists.
- **v0.3.41 deterministic map values:** `values of m` returns a list of map
  values in sorted-key order, mirroring `keys of m` for predictable map
  workflows.
- **v0.3.42 list insertion helpers:** `std/list` adds `insert_number`,
  `insert_text`, `insert_decimal`, and `insert_yesno`, using 1-based clamped
  insertion that mutates caller lists through `changing` parameters.
- **v0.3.43 list pop helpers:** `std/list` adds `pop_number`, `pop_text`,
  `pop_decimal`, and `pop_yesno`, returning `maybe` values while removing
  valid 1-based items from caller lists.
- **v0.3.44 list remove helpers:** `std/list` adds `remove_number`,
  `remove_text`, `remove_decimal`, and `remove_yesno`, removing the first
  matching item from caller lists and returning yes/no for whether a value was
  removed.
- **v0.3.45 map take helpers:** `std/map` adds take-and-remove helpers for
  text-key and number-key maps across number, text, decimal, and yes/no
  values, returning `maybe` values while deleting present keys from caller
  maps.
- **v0.3.46 map clear helpers:** `std/map` adds clear helpers for text-key
  and number-key maps across number, text, decimal, and yes/no values,
  removing every entry from caller maps through `changing` parameters.
- **v0.3.47 list ordering helpers:** `std/list` adds `sort_number`,
  `reverse_number`, `sort_text`, `reverse_text`, `sort_decimal`, and
  `reverse_decimal`, mutating ordered caller lists through `changing`
  parameters.
- **v0.3.48 text edge removal helpers:** `std/text` adds `without_prefix`
  and `without_suffix`, returning text with a matching prefix or suffix
  removed while leaving absent or empty edge text unchanged.
- **v0.3.49 one-sided text trimming:** `std/text` adds `is_whitespace`,
  `left_trimmed`, and `right_trimmed`, covering space, tab, newline, and
  carriage-return edge cleanup without removing content on the opposite side.
- **v0.3.50 text padding helpers:** `std/text` adds `padded_left` and
  `padded_right`, repeating non-empty fill text to align strings to a requested
  width while leaving already-wide text unchanged.
- **v0.3.51 centered text padding:** `std/text` adds `padded_center`,
  centering text to a requested width with repeated fill text and placing the
  extra fill on the right when the gap is odd.
- **v0.3.52 ASCII text classification:** `std/text` adds `is_digit`,
  `is_alpha`, and `is_alphanumeric` for non-empty whole-text checks over
  ASCII digits and letters.
- **v0.3.53 text capitalization:** `std/text` adds `capitalized`, uppercasing
  the first UTF-8 character and lowercasing the rest while preserving empty
  text.
- **v0.3.54 yes/no list reversal:** `std/list` adds `reverse_yesno`,
  mutating `list of yesno` values in place and no-oping cleanly on empty lists.
- **v0.3.55 yes/no list sorting:** `std/list` adds `sort_yesno`, mutating
  `list of yesno` values in place with `no` ordered before `yes`.
- **v0.3.56 list copy helpers:** `std/list` adds `copy_number`, `copy_text`,
  `copy_decimal`, and `copy_yesno`, returning fresh lists that preserve the
  original items while staying independent of later source-list mutation.
- **v0.3.57 yes/no list edge helpers:** `std/list` adds `first_yesno`,
  `last_yesno`, `maybe_first_yesno`, and `maybe_last_yesno`, bringing yes/no
  lists in line with the number, text, and decimal edge helper families.
- **v0.3.58 ASCII text case predicates:** `std/text` adds `is_lowercase` and
  `is_uppercase`, non-empty whole-text checks for ASCII lowercase and uppercase
  letters.
- **v0.3.59 text case swapping:** `std/text` adds `swap_case`, swapping ASCII
  lowercase and uppercase letters while leaving digits, spaces, punctuation,
  and non-ASCII characters unchanged.
- **v0.3.60 text title casing:** `std/text` adds `title_cased`, uppercasing
  the first character of each whitespace-delimited word, lowercasing the rest,
  and preserving original spacing.
- **v0.3.61 text title-case predicate:** `std/text` adds `is_titlecase`,
  checking whether text with at least one ASCII letter is already in
  `title_cased` form.
- **v0.3.62 ASCII text predicate:** `std/text` adds `is_ascii`, matching
  Python's empty-text-friendly ASCII check for printable ASCII plus tab,
  newline, and carriage return.
- **v0.3.63 printable text predicate:** `std/text` adds `is_printable`,
  returning no for tab, newline, and carriage return controls while accepting
  spaces, ordinary text, non-ASCII printable characters, and empty text.
- **v0.3.64 whole-text whitespace predicate:** `std/text` adds `is_space`,
  returning yes only when non-empty text contains only space, tab, newline,
  or carriage return characters.
- **v0.3.65 raw line-list helper:** `std/text` adds `lines_of`, returning
  every newline-separated line, including blank and trailing lines, while
  keeping empty text as an empty list.
- **v0.3.66 prefix/suffix predicates:** `std/text` adds `has_prefix` and
  `has_suffix`, including Python-like yes results for empty prefix/suffix
  checks.
- **v0.3.67 UTF-8 text reversal helper:** `std/text` adds `reversed_text`,
  reversing by Parley characters rather than raw bytes and preserving empty
  text as empty text.
- **v0.3.68 text partition helper:** `std/text` adds `partition_text`,
  returning a three-text list of before/separator/after for the first
  separator match, or text/empty/empty when absent.
- **v0.3.69 right-side text partition helper:** `std/text` adds
  `rpartition_text`, returning before/separator/after for the last separator
  match, or empty/empty/text when absent.
- **v0.3.70 last text position helper:** `std/text` adds `last_position`,
  returning a `maybe number` for the last 1-based UTF-8 character position of
  a needle, including overlapping matches and the final boundary for an empty
  needle.
- **v0.3.71 zero-fill text padding helper:** `std/text` adds `zero_filled`,
  padding text on the left with zeroes to a target width while preserving a
  leading `+` or `-` before the inserted zeroes.
- **v0.3.72 tab expansion helper:** `std/text` adds `tabs_expanded`,
  replacing tabs with spaces up to the next tab stop, resetting columns after
  newline/carriage return, and removing tabs when the tab size is non-positive.
- **v0.3.73 universal newline split helper:** `std/text` adds `split_lines`,
  returning Python-style line lists over `\n`, `\r`, and `\r\n` boundaries,
  preserving blank middle lines and omitting the synthetic final empty line
  for terminal line breaks.
- **v0.3.74 right-side split helper:** `std/text` adds `rsplit_text`,
  splitting text at most `max_splits` times from the right while preserving
  the unsplit left side, matching Python's common `rsplit(separator, n)`
  workflow with deterministic no-op behavior for empty separators or
  non-positive split counts.
- **v0.3.75 bounded split helper:** `std/text` adds `split_text`, splitting
  text at most `max_splits` times from the left while preserving the unsplit
  right side, matching Python's common `split(separator, n)` workflow with
  deterministic no-op behavior for empty separators or non-positive counts.
- **v0.3.76 whitespace word extraction:** `std/text` updates `word_count` and
  `words_of` to split on space, tab, newline, and carriage-return boundaries,
  collapsing repeated whitespace and ignoring leading/trailing whitespace.
- **v0.3.77 bounded text replacement helper:** `std/text` adds `replaced_text`,
  replacing at most `max_replacements` non-overlapping matches while leaving
  empty needles and non-positive counts unchanged.
- **v0.3.78 factorial math helper:** `std/math` adds `factorial`, returning
  whole-number factorials with `0! = 1` and a catchable English failure for
  negative input.
- **v0.3.79 integer GCD/LCM helpers:** `std/math` adds
  `greatest_common_divisor` and `least_common_multiple`, normalizing negative
  inputs to non-negative results and returning `0` for zero LCM inputs.
- **v0.3.80 combinatorics math helpers:** `std/math` adds
  `combination_count` and `permutation_count`, matching Python-style zero
  results when `chosen` exceeds `total` and catchable English failures for
  negative inputs.
- **v0.3.81 square-root math helpers:** `std/math` adds
  `integer_square_root` and `is_perfect_square`, covering Python-style integer
  root workflows with catchable English failures for negative roots.
- **v0.3.82 list product helpers:** `std/list` adds `product_number` and
  `product_decimal`, matching Python-style multiplicative identity behavior
  for empty number and decimal lists.
- **v0.3.83 list membership helpers:** `std/list` adds `contains_number`,
  `contains_text`, `contains_decimal`, and `contains_yesno`, giving direct
  yes/no membership checks across bundled list families.
- **v0.3.84 map key membership helpers:** `std/map` adds text-key and
  number-key `*_has_key` helpers across number, text, decimal, and yes/no
  map values.
- **v0.3.85 explicit list sums and map copy helpers:** `std/list` adds
  `sum_number` and `sum_decimal` helpers, and `std/map` adds fresh-copy
  helpers for text-key and number-key maps across number, text, decimal, and
  yes/no values.
- **v0.3.86 yes/no list count/index parity:** `std/list` adds
  `count_yesno` and `index_yesno`, matching the value-parameter count/index
  helper shape used by number, text, and decimal lists.
- **v0.3.87 map update helpers:** `std/map` adds `update_*_map` helpers for
  text-key and number-key maps across number, text, decimal, and yes/no
  values; each helper mutates the first map by overwriting matching keys and
  inserting missing keys from the second map.
- **v0.3.88 map ensure helpers:** `std/map` adds `ensure_*_at` helpers for
  text-key and number-key maps across number, text, decimal, and yes/no
  values; each helper returns the present value when the key exists, otherwise
  inserts the fallback and returns it.
- **v0.3.89 map take-or-fallback helpers:** `std/map` adds `take_*_or`
  helpers for text-key and number-key maps across number, text, decimal, and
  yes/no values; each helper removes and returns a present value, otherwise
  returns the fallback without mutating the map.
- **v0.3.90 map value membership helpers:** `std/map` adds `*_has_value`
  helpers for text-key and number-key maps across number, text, decimal, and
  yes/no values; each helper scans map values and returns yes when a matching
  value is present.
- **v0.3.91 list filter helpers:** `std/list` adds `filter_number`,
  `filter_text`, `filter_decimal`, and `filter_yesno`. Each helper accepts a
  first-class predicate function and returns a fresh list containing only the
  values where the predicate returns yes, preserving input order.
- **v0.3.92 list map helpers:** `std/list` adds `map_number`, `map_text`,
  `map_decimal`, and `map_yesno`. Each helper accepts a first-class
  same-type transform function and returns a fresh list in input order.
- **v0.3.93 list predicate any/all helpers:** `std/list` adds `any_*` and
  `all_*` predicate helpers for number, text, decimal, and yes/no lists.
  Helpers accept first-class predicate functions; empty lists give no for
  `any_*` and yes for `all_*`, matching Python's any/all convention.
- **v0.3.94 text any-edge helpers:** `std/text` adds `has_any_prefix` and
  `has_any_suffix`, matching Python's tuple-style startswith/endswith
  workflow over a list of candidate edges. Empty candidate lists give no;
  empty candidate text still matches, consistent with `has_prefix` and
  `has_suffix`.
- **v0.3.95 list maybe-find helpers:** `std/list` adds `maybe_find_number`,
  `maybe_find_text`, `maybe_find_decimal`, and `maybe_find_yesno`, matching
  Python's first-match generator workflow with typed `maybe` results. Empty
  lists and no-match scans return `nothing`.
- **v0.3.96 list predicate-count helpers:** `std/list` adds
  `count_where_number`, `count_where_text`, `count_where_decimal`, and
  `count_where_yesno`, matching Python's `sum(1 for x in xs if predicate(x))`
  workflow over typed lists. Empty lists and no-match scans return `0`.
- **v0.3.97 list fold helpers:** `std/list` adds `fold_number`,
  `fold_text`, `fold_decimal`, and `fold_yesno`, matching Python's
  `functools.reduce` workflow with an explicit initial accumulator so empty
  lists deterministically return the initial value.
- **v0.3.98 list take/drop-while helpers:** `std/list` adds `take_while_*`
  and `drop_while_*` helpers for number, text, decimal, and yes/no lists,
  matching Python's `itertools.takewhile` and `dropwhile` workflows while
  returning fresh typed lists.
- **v0.3.99 list reject helpers:** `std/list` adds `reject_*` helpers for
  number, text, decimal, and yes/no lists, matching Python's
  `itertools.filterfalse` workflow by returning fresh typed lists of values
  where the predicate returns `no`.
- **v0.3.100 list predicate-index helpers:** `std/list` adds
  `maybe_find_index_*` helpers for number, text, decimal, and yes/no lists,
  returning the first 1-based index where a predicate returns `yes` or
  `nothing` for empty/no-match scans.
- **v0.3.101 list predicate-index collection helpers:** `std/list` adds
  `indexes_where_*` helpers for number, text, decimal, and yes/no lists,
  returning fresh `list of number` values with every 1-based index where a
  predicate returns `yes`.
- **v0.3.102 text search fallback helpers:** `std/text` adds
  `position_or_zero` and `last_position_or_zero`, mirroring maybe-returning
  search helpers but returning `0` for no match so simple agent code can avoid
  explicit maybe unwrapping.
- **v0.3.103 text character-trim helpers:** `std/text` adds `trimmed_of`,
  `left_trimmed_of`, and `right_trimmed_of`, mirroring Python
  `strip(chars)`, `lstrip(chars)`, and `rstrip(chars)` for explicit character
  sets while leaving text unchanged for an empty character set.
- **v0.3.104 kept line-split helper:** `std/text` adds `split_lines_kept`,
  mirroring Python `splitlines(keepends=True)` by splitting on `\n`, `\r`,
  and `\r\n` while retaining the matched line boundary on each returned line
  and avoiding a synthetic final empty item.
- **v0.3.105 text identifier predicate:** `std/text` adds `is_identifier`,
  checking non-empty ASCII/Parley identifier text whose first character is a
  letter or underscore and whose remaining characters are letters, digits, or
  underscores.
- **v0.3.106 decimal closeness helper:** `std/math` adds `is_close`, matching
  Python's `math.isclose` workflow with explicit relative and absolute
  tolerances and a catchable failure for negative tolerances.
- **v0.3.107 decimal hypotenuse helper:** `std/math` adds `hypotenuse`,
  matching Python's common two-argument `math.hypot` workflow for decimal
  right-triangle distance calculations.
- **v0.3.108 decimal sign-copy helper:** `std/math` adds `copy_sign`,
  matching Python's common `math.copysign` workflow by returning a decimal
  magnitude with the sign of a second decimal source.
- **v0.3.109 decimal angle conversion helpers:** `std/math` adds
  `radians_from_degrees` and `degrees_from_radians`, matching Python's
  common `math.radians` and `math.degrees` workflows for decimal angles.
- **v0.3.110 decimal math constants:** `std/math` adds `pi_value`,
  `tau_value`, and `e_value`, matching Python's common `math.pi`, `math.tau`,
  and `math.e` workflows through zero-parameter helpers.
- **v0.3.111 decimal point-distance helpers:** `std/math` adds `distance_2d`
  and `distance_3d`, matching Python's common `math.dist` workflow for fixed
  2D and 3D decimal coordinate points.
- **v0.3.112 list sum-product helpers:** `std/list` adds
  `sum_product_number` and `sum_product_decimal`, matching Python's
  `math.sumprod` workflow over typed lists with catchable failures for length
  mismatches.
- **v0.3.113 list median helpers:** `std/list` adds `median_number`,
  `median_decimal`, `maybe_median_number`, and `maybe_median_decimal`,
  matching Python's statistics median workflow over typed lists with catchable
  failures or explicit `nothing` results for empty lists.
- **v0.3.114 list median-low/high helpers:** `std/list` adds
  `median_low_number`, `median_high_number`, `median_low_decimal`,
  `median_high_decimal`, and maybe-returning variants, matching Python's
  `statistics.median_low` and `statistics.median_high` workflows over typed
  lists.
- **v0.3.115 list mode helpers:** `std/list` adds mode and maybe-mode helpers
  for number, text, decimal, and yes/no lists, matching Python's
  `statistics.mode` tie behavior by returning the first value seen among
  equally common values.
- **v0.3.116 list plural-mode helpers:** `std/list` adds `modes_number`,
  `modes_text`, `modes_decimal`, and `modes_yesno`, matching Python's
  `statistics.multimode` workflow by returning all tied modes in first-seen
  order and returning an empty list for empty input.
- **v0.3.117 list population statistics helpers:** `std/list` adds
  `population_variance_number`, `population_standard_deviation_number`,
  `population_variance_decimal`, `population_standard_deviation_decimal`, and
  maybe-returning variants, matching Python's population variance/stdev
  workflow over typed numeric lists with catchable empty-list failures.
- **v0.3.118 list sample statistics helpers:** `std/list` adds
  `sample_variance_number`, `sample_standard_deviation_number`,
  `sample_variance_decimal`, `sample_standard_deviation_decimal`, and
  maybe-returning variants, matching Python's sample variance/stdev workflow
  with catchable failures for inputs shorter than two items.
- **v0.3.119 list mean-family helpers:** `std/list` adds
  `geometric_mean_number`, `harmonic_mean_number`, `geometric_mean_decimal`,
  `harmonic_mean_decimal`, and maybe-returning variants, covering the common
  Python statistics mean-family workflows with catchable empty/negative input
  failures and zero-aware harmonic means.
- **v0.3.120 list quantile helpers:** `std/list` adds
  `quantiles_number`, `inclusive_quantiles_number`, `quantiles_decimal`,
  `inclusive_quantiles_decimal`, and maybe-returning variants, matching
  Python's exclusive/default and inclusive `statistics.quantiles` workflows
  with catchable empty input and invalid group failures.
- **v0.3.121 list covariance/correlation helpers:** `std/list` adds
  `covariance_number`, `correlation_number`, `covariance_decimal`,
  `correlation_decimal`, and maybe-returning variants, matching Python's
  sample covariance and Pearson correlation workflows with catchable
  length, short-input, and constant-input failures.
- **v0.3.122 list linear-regression helpers:** `std/list` adds
  `linear_regression_number`, `proportional_linear_regression_number`,
  `linear_regression_decimal`, `proportional_linear_regression_decimal`, and
  maybe-returning variants, matching Python's `statistics.linear_regression`
  workflows by returning `[slope, intercept]` decimal lists.
- **v0.3.123 list accumulated-sum helpers:** `std/list` adds
  `accumulated_sum_number` and `accumulated_sum_decimal`, matching Python's
  default `itertools.accumulate` running-total workflow with fresh typed lists
  and empty-list identity behavior.
- **v0.3.124 list accumulated-product helpers:** `std/list` adds
  `accumulated_product_number` and `accumulated_product_decimal`, extending
  Python-style `itertools.accumulate` workflows to running products with fresh
  typed lists and empty-list identity behavior.
- **v0.3.125 list accumulated-extrema helpers:** `std/list` adds
  `accumulated_minimum_number`, `accumulated_maximum_number`,
  `accumulated_minimum_decimal`, and `accumulated_maximum_decimal`, extending
  Python-style `itertools.accumulate` workflows to running extrema over typed
  numeric lists.
- **v0.3.126 list text accumulated-extrema helpers:** `std/list` adds
  `accumulated_minimum_text` and `accumulated_maximum_text`, extending
  Python-style `itertools.accumulate` extrema workflows to text lists using
  Parley's lexical text ordering.
- **v0.3.127 list selector-compression helpers:** `std/list` adds
  `compress_number`, `compress_text`, `compress_decimal`, and
  `compress_yesno`, matching Python's `itertools.compress` workflow with
  parallel yes/no selectors and shortest-input stopping behavior.
- **v0.3.128 list chain helpers:** `std/list` adds `chain_number`,
  `chain_text`, `chain_decimal`, and `chain_yesno`, matching Python's
  `itertools.chain` workflow by returning fresh typed lists that contain the
  left input followed by the right input without mutating either.
- **v0.3.129 list bounded-repeat helpers:** `std/list` adds `repeat_number`,
  `repeat_text`, `repeat_decimal`, and `repeat_yesno`, matching Python's
  bounded `itertools.repeat(value, count)` workflow with fresh typed lists and
  empty results for non-positive counts.
- **v0.3.130 list bounded-cycle helpers:** `std/list` adds `cycle_number`,
  `cycle_text`, `cycle_decimal`, and `cycle_yesno`, matching bounded
  consumption of Python's `itertools.cycle` workflow with fresh typed lists and
  empty results for empty inputs or non-positive counts.
- **v0.3.131 list stepped-slice helpers:** `std/list` adds
  `list_slice_step_number`, `list_slice_step_text`, `list_slice_step_decimal`,
  and `list_slice_step_yesno`, matching Python-style positive-step slice and
  `itertools.islice` workflows over Parley's clamped 1-based list bounds.
- **v0.3.132 list count-based take/drop helpers:** `std/list` adds
  `take_number`, `drop_number`, `take_text`, `drop_text`, `take_decimal`,
  `drop_decimal`, `take_yesno`, and `drop_yesno`, matching common
  Python-style first-N and drop-N list workflows with fresh typed lists.
- **v0.3.133 list enumeration helpers:** `std/list` adds `enumerate_number`,
  `enumerate_number_from`, `enumerate_text`, `enumerate_text_from`,
  `enumerate_decimal`, `enumerate_decimal_from`, `enumerate_yesno`, and
  `enumerate_yesno_from`, matching Python-style indexed enumeration by
  returning fresh number-key maps from list indexes to typed values.
- **v0.3.134 list tail take/drop helpers:** `std/list` adds
  `take_last_number`, `drop_last_number`, `take_last_text`, `drop_last_text`,
  `take_last_decimal`, `drop_last_decimal`, `take_last_yesno`, and
  `drop_last_yesno`, matching Python-style tail slicing workflows with fresh
  typed lists.
- **v0.3.135 list prefix/suffix predicates:** `std/list` adds
  `has_prefix_number`, `has_suffix_number`, `has_prefix_text`,
  `has_suffix_text`, `has_prefix_decimal`, `has_suffix_decimal`,
  `has_prefix_yesno`, and `has_suffix_yesno`, matching Python-style sequence
  edge checks over typed Parley lists.
- **Claude Code skill** in `skill/parley/` — kept in sync with the
  language; update it whenever syntax changes.
- **Landing page** in `site/` — self-contained static site (index.html,
  style.css, main.js, 404.html; Three.js via CDN import map). The hero headline
  "speak plainly." is ~15k ember particles that respond to the cursor;
  scrolling shreds it to dust and condenses it into a black monolith (the
  native binary) behind the install command. A 2026-06-18 readiness pass
  added GSAP-powered DOM reveals/copy affordance, a skip link, and mobile
  overflow fixes. A 2026-06-21 fallback pass keeps the text hero visible when
  CDN-loaded Three.js/GSAP assets are unavailable. Verified with Playwright at desktop and mobile widths:
  no horizontal overflow; WebGL scene reaches `scene-ok`; no runtime errors
  beyond headless Chromium WebGL performance warnings. Design context in
  `PRODUCT.md` / `DESIGN.md` (PRODUCT.md was synthesised from the repo and
  Arjun's brief, not a user interview — confirm with him before redesigns).
- **Release/research docs** — `docs/RESEARCH.md` now defines the publishable
  benchmark plan, `benchmarks/` contains a Phase-1 Parley/Python/Rust seed
  metrics harness with explicit source references, optional `tiktoken` counts
  plus JSONL attempt logging, run-log summaries, exposed through `parley benchmark`, and
  `docs/RELEASE.md` records the GitHub/Pages/PyPI
  readiness checklist. `docs/SPEC.md` now correctly says v0.3 and no longer
  claims higher-order functions are missing. `docs/DOMAINS.md` records
  checked domain candidates; current recommendation is `parleylang.com`.
- Repo: https://github.com/ded-furby/parley-lang (GitHub account
  `ded-furby`). It is public as of 2026-06-18. Live website:
  https://ded-furby.github.io/parley-lang/ served by GitHub Pages from
  the `gh-pages` branch.

### Blocked (needs Arjun, not an agent)

- **CI push.** The commit "Add CI workflow" is kept as the LOCAL TIP of
  main, deliberately unpushed: the gh OAuth token lacks the `workflow`
  scope, and any push containing that commit is rejected. Fix:
  `gh auth refresh -h github.com -s workflow`, then `git push`.
  Attempted again on 2026-06-18; GitHub required device-code browser auth,
  so the token still only has `gist`, `read:org`, and `repo`.
  If you commit new work, commit it, then rebase it BELOW the CI commit
  (or cherry-pick the CI commit back on top) and push with
  `git push origin HEAD~1:main` so the CI commit stays the unpushed tip.
- **PyPI.** The name `parley-lang` is unverified/unpublished. The documented
  install path uses `pip install git+https://github.com/ded-furby/parley-lang`,
  which works before a PyPI release.

### Not started (the remaining roadmap, in suggested order)

1. **Run the benchmark study** (goal 3). `parley benchmark prompt` now renders
   language-neutral task prompts, `parley benchmark measure` measures
   Parley/Python/Rust seed references, supports optional `tiktoken` token
   counts, checks Parley with JSON diagnostics, and captures generated attempts
   to JSONL with `parley benchmark append` and summary analysis through
   `parley benchmark summarize`. Still needed: repeated agent error-rate runs
   and a result write-up.
2. **Package publishing workflow** — checksum installs, publish-entry
   generation, lock verification, registry validation, ownership metadata,
   semantic version governance, submission review, and HMAC release-signature
   verification exist. Still needed later: PyPI reservation/upload and a
   long-term public package trust policy if Parley grows past the starter
   registry.

## Working on the compiler: the contract

- Pipeline files: `parley/grammar.lark` → `parser.py` → `checker.py` →
  `emit_rust.py`; CLI in `cli.py`; P-codes in `diagnostics.py`.
- The checker must be total: any program it accepts must compile under
  rustc. A rustc rejection is a Parley bug (surfaced as P901).
- Every new feature needs: grammar + AST + checker (with P-coded errors
  and hints) + emitter + tests at all four levels (parser/checker/emit/
  e2e) + docs (TUTORIAL, REFERENCE, SPEC, skill) + an example if user-facing.
- Run `python3 -m pytest tests/` (e2e needs cargo; ~20 s warm).
- Keep diagnostics stable: never renumber existing P-codes.

## Conventions

- Version lives in `pyproject.toml` and `parley/__init__.py` (now 0.3.135).
- Examples must run clean; e2e tests assert their exact stdout.
- The skill (`skill/parley/SKILL.md`) is the agent-facing contract —
  treat it as part of the language release, not an afterthought.
