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
2. **A useful product layer.** Parley Workflows must prove the language on
   real, repeatable automation: inspectable source, safe execution, native
   output, and an adoption loop driven by unrelated user tasks.
3. **A landing page** (one page, scrolling, Three.js, cursor-controlled 3D,
   unique, craft level above igloo.inc without copying it).
4. **The research angle.** Formalise token efficiency as a language-design
   metric; benchmark agent error rates across Python/Rust/Zero/Parley;
   publish on arXiv with a USYD professor. (Arjun's long-term goal.)

## Where things stand (2026-08-05)

### Done and verified

- **Language v0.3 / toolchain v0.3.158** — full pipeline (Lark LALR parse → checker → Rust emit
  → cargo). The latest local suite has 362 tests, including e2e tests that
  compile every feature to a native binary and assert stdout. Eleven examples in
  `examples/`. Docs: `docs/TUTORIAL.md`, `REFERENCE.md`, `SPEC.md`,
  `ERRORS.md` (generated from `parley/diagnostics.py` — regenerate it if
  you add a P-code; `tests/test_diagnostics.py` enforces coverage).
- **v0.3.156 Parley Workflows:** `parley workflow list/new/run` ships the first
  product layer over the language. Three bundled starters cover text cleanup,
  log summaries, and Markdown checklist reports; normal Parley source can
  `include "std/workflow"` for reusable deterministic helpers. The runner
  requires a real input file, refuses an existing output without `--force`,
  rejects input/output identity including hard links, validates schema-1
  manifests, and compiles through the existing Rust backend. Focused tests pass
  10/10, the full suite passes 355/355, and a built v0.3.156 wheel contains all
  three templates plus `std/workflow`. Product history and adoption gates live
  in `workflows/`; future helpers require recurring real-workflow evidence.
- **v0.3.157 repeatable workflow contracts:** new scaffolds use schema-2
  manifests with ordered named inputs and exact-output fixture cases. `parley
  workflow test` compiles once and checks every fixture in an isolated output
  directory. Runs reject missing, duplicate, and unknown input names and guard
  every input against output identity; schema-1 workflows remain compatible.
  Focused tests pass 10/10 and the full suite passes 358/358.
- **v0.3.158 flagship workflow products:** Release Steward accepts named test
  results, release metadata, a Markdown checklist, and package information and
  produces one deterministic `READY`/`BLOCKED` report. Its ready and blocked
  golden fixtures pass, and the repository dogfood run truthfully records its
  remaining release blockers. Release Steward, Log Summary, and Checklist
  Report now ship as wheel resources and install by catalog name into readable
  `parley_workflows/` source. `parley.workflows.lock.json` records semantic
  versions and whole-tree SHA-256; `parley workflow verify` detects drift. A
  fresh-wheel smoke installed all three and verified all checksums; the full
  suite passes 360/360.
- **Structured-input decision:** `workflows/CAPABILITY_EVIDENCE.md` records the
  v0.3.158 review. JSON is a low-pressure need in one of three products and CSV
  in zero, so both are deliberately deferred. No compiler, skill, or benchmark
  instruction changed. Reconsider only when two unrelated maintained workflows
  need genuinely structured values or repeated typed records.
- **Independent deeper corpus checkpoint (iteration 032):** four new
  five-module projects cover quoted environment normalization, Retry-After
  precedence, raw webhook-body verification, and stable pagination ordering.
  The manifest SHA is
  `49df28a27ce00ac58d898a386fcee1cae46fd15fd02c38ec82272b39a326bb1f`;
  isolated root fixes pass 60/60 cross-language case groups. The corpus is
  independent of report 031 outcomes and changes no compiler, skill,
  instruction, runner, or metric. Corpus commit `d435ecd` precedes protocol
  commit `0919607` and every measured session.
- **Iteration 032 preregistration:** protocol SHA
  `d702c3401af57092196e9056ef51057b63700a70fa56212511c2927a758e588c`
  freezes six complete four-project bundles per language: 18 fresh sessions,
  72 assignments, seed `320260805`, Parley v0.3.158, and the unchanged
  1,519-character skill. The strict 4-part efficiency/reliability gate and
  24/24 exact-root condition are unchanged from 031. All cells were run once
  with no exclusions or reruns; no outcome triggered same-corpus tuning.
- **Independent deeper-project result (iteration 032):** all 18 fresh sessions
  and 72 assignments pass first check, hidden judgment, command protocol, and
  integrity with zero repairs. Parley records 15,704.50 median tokens/repo and
  8.4545 seconds versus Python's 15,033.00/7.5247 and Rust's
  15,451.38/9.3756. The frozen primary gate is 2/4: correctness and first-check
  pass; tokens and faster-baseline elapsed fail. Parley trails Python by 4.47%
  tokens and 12.36% elapsed, trails Rust by 1.64% tokens, and beats Rust by
  9.82% elapsed. Exact-root maintainability improves to 24/24, so the overall
  five-condition result is 3/5. Preserve raw SHA
  `0600ca9e65c3413387641b3c227db27f6c212e00d9b56802cd1111769610b4f5`
  and report SHA
  `5c309fa0a2c9a81281a90e9b921600c67b46fc2f3b59f38daac3d48369ce75db`.
  This clean negative confirmation changes no compiler, syntax, prompt,
  instruction, runner, task, or metric; continue product adoption work.
- **Committed progress archive:** `progress/index.html` is a responsive,
  searchable visual timeline over all 32 preserved benchmark HTML reports.
  `progress/manifest.json` records source/archive paths, sizes, and SHA-256;
  all 32 copies verify byte-for-byte, including explicitly preserved report
  013. Refresh it with `python3 scripts/sync_progress_reports.py` after a new
  report is added.
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
- **v0.3.136 text case-fold helper:** `std/text` adds `case_folded`,
  lowercasing text and folding `ß` to `ss` so common case-insensitive
  comparisons can use plain equality over normalized text.
- **v0.3.137 list unique helpers:** `std/list` adds `unique_number`,
  `unique_text`, `unique_decimal`, and `unique_yesno`, matching common
  Python-style deduplication workflows while preserving first-seen order.
- **v0.3.138 number range helpers:** `std/list` adds `range_number`,
  `range_number_from`, and `range_number_step`, materializing Python-style
  stop-exclusive number ranges with positive and negative steps.
- **v0.3.139 borrow-safe item mutation:** list/map set and remove operations
  evaluate their indexes, keys, and values before taking the target's mutable
  borrow, so accepted expressions such as `remove item (length of xs) of xs`
  compile instead of surfacing P901 from rustc.
- **v0.3.140 compact agent skill:** the default skill is a 7,168-character
  task-facing core with explicit first-pass syntax for typed empty lists,
  promptless input, literal braces, expression calls, maybes, and map lookup.
  The prior exhaustive stdlib/package/LSP/research material remains available
  on demand in `skill/parley/references/extended-reference.md`.
- **v0.3.141 benchmark-driven agent pass:** the default skill is now a
  4,340-character safe-forms sheet with explicit rules for reserved
  `position`, single-token snake_case names, expression-call parentheses,
  and declaration-only `changing`. P101 now gives exact repair hints for the
  four parse patterns seen in the 90-session confirmation run; the full
  reference remains preserved on demand.
- **v0.3.142 sub-3k agent core:** the always-injected safe-forms sheet is
  2,998 characters, with the iteration-004 zero-repair rules retained. The
  three benchmark prompts are 4,445–4,489 characters; all detailed language
  and tooling material remains in the unchanged on-demand reference.
- **v0.3.143 reliability-floor recovery:** after the sub-3k core regressed to
  one first pass in six, the core restores exact `yes`/`no`, comparison,
  loop-only `stop`, and numeric-conversion forms at 3,283 characters. P101
  and P201 now give direct repairs for the corresponding agent mistakes.
- **v0.3.144 returning-function guardrail:** the 3,280-character core includes
  canonical `giving TYPE` / `give back value`, and P101 directly repairs
  common `returns`, `return`, and bare `give` substitutions observed in
  protocol-v2 iteration 007 without increasing prompt size.
- **v0.3.145 progressive-disclosure core:** the always-loaded contract is
  1,557 characters and retains every empirically observed first-pass trap.
  The proven 3,280-character v0.3.144 core is preserved byte-for-byte at
  `skill/parley/references/core-v0.3.144.md` for on-demand fallback.
- **v0.3.146 transcript-backed natural aliases:** the parser/runtime accepts
  the recurring iteration-009 drafts (`set` creation, `print`, `return`,
  maybe-value phrases, arithmetic repeat counts, `sort`, empty-text character
  splitting, and `stop` to leave `main`). A 1,371-character core restores a
  concrete safe-form program; the failed v0.3.145 core is also preserved.
- **v0.3.147 conversion/output recovery:** `text_expr as number` is a checked
  parse-and-unwrap, and text `plus` any scalar formats like interpolation.
  These cover both repeated inventory failures from pilot 010. The core also
  states that numeric input is typed and `say` emits one complete line.
- **v0.3.148 symmetric text output:** `expr as text` aliases `text from expr`,
  and adding a scalar to `list of text` formats it using interpolation rules.
  All six pilot-011 first sources now type-check unchanged; the 1,519-character
  skill is intentionally unchanged to isolate compiler ergonomics.
- **v0.3.149 natural helpers:** parameter declarations accept natural `and`
  separators, and calls flatten `and` expressions only when the callee's arity
  proves they are arguments. An `and`-separated signature infers `changing`
  for a list/map parameter directly mutated by its body; comma-separated
  signatures retain established value semantics. The exact pilot-012 first
  source now checks unchanged, and the full 284-test suite passes.
- **v0.3.150 one-shot instruction compression:** after pilot 013 reached 6/6
  first-pass with zero Parley repairs, the always-loaded skill was reduced
  once from 1,519 to 343 characters using only general entry-point, state,
  I/O, and diagnostic-loop guidance. The redundant benchmark-only wrapper was
  removed. The proven 0.3.149 core is preserved byte-for-byte; compiler
  semantics and protocol constraints are unchanged.
- **v0.3.151 evidence-backed rollback:** pilot 014 fell to 0/6 first-pass and
  69 Parley repair turns across all three tasks. The exact 1,519-character
  reliability core and the original metered wrapper are restored. No further
  instruction compression is planned; compiler semantics remain frozen.
- **v0.3.152 contextual `position`:** iteration 017 rejected this common
  variable name across four unrelated tasks. It is now accepted uniformly,
  including `item position of values`, while the existing `position of needle
  in text` operator is preserved. All five untouched failing first sources
  pass their public and hidden cases, and the full 294-test suite passes. The
  skill is unchanged and `modulo` was deliberately not added.
- **v0.3.153 contextual `modulo`:** iteration 019 supplied anti-primed
  recurrence across clock, parity, and weekday task families. Infix `a modulo
  b` now reuses the exact existing whole-number `%` AST/checker/emitter/runtime
  path, including the zero guard and Rust-style negative rule. All five saved
  018 rotation failures pass public and hidden replay; unrelated 019 problems
  remain rejected. The full 301-test suite passes and the skill is unchanged.
- **v0.3.154 mutable loop bindings:** the Rust emitter now marks range and
  collection loop variables mutable exactly when their bodies change them.
  This closes the iteration-020 P901 totality defect without adding syntax;
  assignment remains local to the current iteration and does not alter the
  source collection, range bounds, or next value. Checker, emitter, native,
  docs, and regression coverage are included. The untouched failing 020 source
  now compiles and passes its public case plus all five hidden cases; the skill
  remains unchanged.
- **v0.3.155 contextual `number`:** iteration 021 produced ten P209 failures
  across five unrelated task families. `number` is now valid uniformly as a
  value-level field, function, parameter, variable, or loop binding while
  remaining the built-in type in type positions and reserved for user-defined
  record/kind/variant names. No grammar, AST, runtime, or skill change is
  required; parser, checker, emitter, native, and documentation coverage are
  included. The 309-test suite passes, and all ten untouched P209 sources now
  compile and pass their 50 combined public/hidden cases.
- **Size-eight confirmation result (iteration 020):** 30 fresh sessions and
  240 task assignments passed protocol/integrity checks, but the strict gate
  failed 0/4 conditions. Parley reached 79/80 hidden and 74/80 first-check
  tasks at 8,252.19 tokens/task, versus Python's perfect 80/80 and 5,806.25
  tokens/task. Five repair-free Parley bundles had a 6,129.88 median—1.37%
  above Rust and 5.57% above Python—but that post-hoc subset is not parity.
  Preserve report 020. Reject redundant `repeat while` and one-task
  containment aliases. The next compiler work is only the general P901 fix
  for mutation of an accepted range-loop variable; then move to a genuinely
  new broad corpus or model split with the skill unchanged.
- **New broad-corpus result (iteration 021):** all 216 task assignments passed
  hidden cases and all 18 fresh sessions passed protocol/integrity checks.
  Strict parity still failed 1/4: Parley reached 51/72 first checks and
  8,367.13 tokens/task versus Python's 72/72 and 4,057.08. Ten P209 failures
  across five unrelated tasks rejected ordinary identifier `number`; this
  uniquely passes cross-task, general-usefulness, semantic, and maintenance
  review. Preserve report 021, implement only contextual `number`, keep the
  skill unchanged, replay the ten exact sources, and use a new corpus or model
  split rather than tuning these twelve tasks. Reject `repeat while`, postfix
  `sorted`, multiword function declarations, and all isolated forms.
- **Independent-model preregistration (iteration 022):** the model-split path
  authorized by 021 is frozen with `gpt-5.6-terra`, Parley 0.3.155, the same
  validated twelve tasks, and six complete-bundle replicates per language.
  The skill and four-condition gate are unchanged. Compare languages only
  within this model; do not attribute cross-iteration movement separately to
  contextual `number` or the model, and make no ergonomics change from the
  reused corpus after output.
- **Independent-model result (iteration 022):** all 216 assignments passed
  hidden cases and all 18 fresh sessions passed integrity/protocol checks, but
  strict parity failed 1/4. Parley reached 39/72 first checks, 15 repairs, and
  13,040.79 median tokens/task versus Python's 72/72, zero, and 4,079.00 and
  Rust's 64/72, six, and 7,265.04. The contextual-`number` P209 signature was
  zero, without causal attribution because both model and compiler changed.
  A redundant literal `key` in map membership recurred 15 times across three
  tasks and five sessions, but canonical membership already exists and the
  reused-corpus stop rule prohibits tuning. Preserve raw SHA
  `8594f5e8cceb31866002f25e7c3a6e49e00dc98124d70a519b37129d846e60ee`
  and report 022. Make no compiler or skill change; move to previously unseen
  application-style work and retain the general-usefulness, semantic,
  maintainability, and independent-new-task gates.
- **Application-corpus preregistration (iteration 023):** eight previously
  unused application workflows are frozen under `gpt-5.6-sol`, Parley 0.3.155,
  six complete-bundle replicates per language, seed `20260809`, and the
  unchanged 1,519-character skill. The general benchmark harness now supports
  safe relative expected-file contracts; the file-backed task deletes and
  exactly rejudges its output for each case. All 40 oracles were independently
  recomputed and the corrected full test command passed 313/313. The task
  manifest SHA is `f64d441628bd21ea8c6b5fbe3dda51f4d5c52f75607cdceed0616b76ad4d6dc4`;
  protocol SHA is `0a424ac66bbbc01e6f9020fc643462c3353ac4d69065a500613688ba96c423f8`.
  Preserve every result; no same-corpus syntax tuning is allowed.
- **Application-corpus result (iteration 023):** all 144 assignments passed
  hidden cases; all 18 fresh sessions passed integrity/protocol checks; and
  all 72 exact hidden file judgments matched. Strict parity still failed 1/4.
  Parley reached 33/48 first checks, nine repairs, and 13,461.56 median
  tokens/task versus Python's 48/48, zero, and 6,242.00 and Rust's 48/48,
  zero, and 6,584.69. Parley source was 43.58% shorter than Rust. Five
  descending-range expectations were one task; four join-precedence failures
  were one session; six file drafts were one task. No signature crossed both
  task and session independence, so no compiler or skill change follows.
  Preserve raw SHA
  `fbe356681089cd59c3616a845adf29a8fbfceee10476fac7312780cc07275342`
  and report 023. Move toward general discoverability or real-repository work,
  not same-corpus aliases.
- **Seeded-maintenance design (iteration 024):** the next test changes work
  mode rather than language semantics. Four language-specific, hidden-correct
  application solutions preserved from raw iteration 023 are reproduced in
  each prompt and written to the fresh workspace; agents must edit them in
  place to add new aggregation, wildcard-policy, cancellation, and exact-file
  behavior. Six complete-bundle replicates per language produce 18 sessions
  and 72 hidden-judged assignments. All 12 seeds match raw 023 byte-for-byte,
  compile under the current toolchain, and fail the new public requirements;
  an independent oracle matches all 20 new public/hidden contracts. The
  backward-compatible harness records seed size and rough-token edit size.
  Benchmark tests pass 42/42 and the pre-protocol full suite passes 318/318. Preregister
  protocol 024 before running. Protocol 024 is now frozen at SHA
  `d69506b3b7c3c50707534ddecc6ff1fcba8cf3a9651b53c93356dd652a929b93`
  against harness/corpus commit `cb4e3d4`; run all 18 sessions once without
  selective reruns. This related-source corpus is strictly a
  maintenance-efficiency test and may not justify compiler or syntax changes.
- **Seeded-maintenance result (iteration 024):** all 72 assignments passed
  hidden cases and all 18 fresh sessions passed integrity/protocol checks, but
  strict parity failed 1/4. Parley reached 17/24 first checks, six repairs, and
  20,547.88 median tokens/task versus Python's 24/24, zero, and 11,142.88 and
  Rust's 24/24, zero, and 11,654.50. Every Parley session repaired once. Six
  invoice failures in six sessions assigned decimal division to a whole-number
  result, but they remain one task family; one file-read maybe failure was
  isolated. No language or skill change follows from this related-source
  corpus. Parley final source was 41.50% shorter than Rust and its edit 23.22%
  smaller, without lower agent effort. Preserve raw SHA
  `ca3d24d96ef63242aa35ae8970df617df275d2e3cd552b740c4b15d3f67963e1`
  and report 024. Next freeze a real multi-file repository-maintenance corpus,
  with existing/hidden tests and changed-file scope, rather than tuning invoice
  syntax.
- **Repository-maintenance design (iteration 025):** four new two-file
  repositories cover delivery pricing, inventory reservation, incident
  routing, and exact filtered-file reporting. Each session must run the
  protected `./sources` command once as its first shell action; it prints only
  the eight editable files, and every later shell command must be `./check`.
  The backward-compatible harness records seed/final files, rough-token edit
  size, and changed-file count. All 12 repositories pass their frozen old
  contracts and fail each new public requirement unmodified; an independent
  oracle matches all 20 new public/hidden contracts. The full suite passes
  324/324. Harness/corpus commit `814a05b` is pushed. Protocol 025 is frozen at
  SHA `26f51b2c2753e1b9661296d77e42d80a5e9c099fc40df0e1f63fd6b4ecf57364`;
  run all 18 sessions once with Parley v0.3.155 and the unchanged skill. Do not
  learn syntax from 024 or selectively rerun 025 cells.
- **Repository-maintenance result (iteration 025):** all 72 assignments passed
  hidden tests and the first public check with zero repairs. All 18 sessions
  ran one protected `./sources` command first, then one successful `./check`;
  every repository changed both files and all 72 hidden file cases matched.
  Strict parity improved to 2/4: Parley used 15,812.00 median tokens/repo and
  13.5096 seconds versus Python's 14,932.25 and 10.2835 and Rust's 15,611.63
  and 13.1285. The remaining gaps to Rust are only 1.28% tokens and 2.90%
  elapsed. There are no failure signatures and no language/skill change.
  Preserve raw SHA
  `bfbbbe59624696ed722b7928a8bd5e3fd4334229d529aa691f2061e7e61a923d`
  and report 025. Next add four unrelated repositories and preregister a
  size-eight workload under the exact same source protocol to test fixed-context
  amortization; require a larger confirmation if it passes.
- **Eight-repository expansion design (iteration 026):** preserve the four 025
  repository objects exactly and add support-SLA, feature-rollout, ledger, and
  exact priority-digest repositories. The deterministic combined manifest has
  SHA `6dadf527fd966c93fcf034074e397c69050f6dfa9ca16e6df722fc796459157f`.
  Independent oracles match all 20 new public/hidden contracts; all 12 new
  language-specific seeds pass their old contracts and compile while failing
  their new public requirements. The complete pre-protocol suite passes
  328/328. Freeze a six-replicate size-eight matrix only after committing this
  corpus. Keep Parley v0.3.155, the 1,519-character skill, source protocol, and
  four-condition gate unchanged; preserve all output and require a larger
  confirmation if the expansion passes.
- **Eight-repository expansion preregistration (iteration 026):** the corpus
  commit `74c0f67c3531719c491da4e7613a5f2c9e8f8e4e` is pushed. Protocol 026 is
  frozen at SHA
  `aca80f25160e8b7b0eed88a1ca1ab062ad158c3a86723c7786464e400e953e2a`:
  six complete size-eight replicates per language, 18 fresh sessions and 144
  assignments, seed `20260815`. Run it once without selective reruns. Require
  `./sources` exactly once and first, only `./check` later, and preserve all
  session/token/file evidence. No compiler or instruction change is allowed
  from iteration 025 output; a passing expansion requires a larger
  confirmation before any parity claim.
- **Eight-repository expansion result (iteration 026):** all 144 assignments
  pass hidden cases, all 144 hidden exact-file judgments match, all sessions
  preserve source-order/integrity/protocol rules, and every assignment changes
  both files. Parley reaches 8,945.13 median tokens/repo and 9.5669 seconds,
  beating Rust's 9,079.38 and 10.4539 by 1.48% and 8.48%, respectively. Strict
  parity still fails 1/4 because Python is lower (8,394.69 tokens, 7.6526
  seconds) and one Parley session first-checks 6/8 before one repair; Parley is
  46/48 first-check overall versus 48/48 for both baselines. Its two failures
  use `repetition count` in analogous file workflows within the same session,
  so they do not justify a language/skill change. Preserve raw SHA
  `e071acdf35461f28a6cad5fb927a237a5d075156c231068e5102c7705637c55d`
  and report 026. Next add a second independent repository set and preregister
  a size-sixteen pilot under the unchanged protocol; require a larger
  confirmation if that broader pilot passes.
- **Second repository expansion design (iteration 027):** preserve all eight
  026 task objects exactly and add shipping-manifest, account-lockout,
  sensor-band, tag-dedup, timesheet-pay, score-band, delivery-batch, and
  path-sanitizer repositories. The deterministic sixteen-task manifest has SHA
  `4d48c171c217cd7be4bc12fb7880c89f0b829470c5e68717fac810f1aace7312`.
  Independent oracles match all 40 new public/hidden cases; all 24 new
  language-specific seeds pass their old contracts and compile while failing
  their new requirements. The complete pre-protocol suite passes 332/332.
  Commit this corpus before freezing a six-replicate size-sixteen pilot. Keep
  v0.3.155, the skill, source protocol, and strict gate unchanged; a pass still
  requires larger confirmation.
- **Sixteen-repository preregistration (iteration 027):** the corpus commit
  `6d10ee11961f6bffc9f6208e763637ed8c3e5b1c` is pushed. Protocol 027 is frozen
  at SHA `c9d06a379af53a86bb80fb30797f3421c0b3f9c103a93438496aa9f0463893b4`:
  six complete size-sixteen replicates per language, 18 fresh sessions and 288
  assignments, seed `20260817`. Run once without selective reruns under the
  exact source protocol. Preserve all evidence; do not change the compiler or
  instruction. Even a passing result requires larger confirmation.
- **Sixteen-repository result (iteration 027):** all 288 assignments pass
  hidden cases; Parley and Rust are 96/96 first-check clean, while Python is
  95/96 before one indentation repair. Strict parity fails 2/4. Parley uses
  7,675.56 median tokens/repo versus Python's 5,046.25 and Rust's 5,650.28;
  its 8.0127 seconds remains below Rust's 8.5897 but above Python's 5.8393.
  Three one-edit-action Parley runs cluster near 7.00k while three two-action
  runs cluster near 8.34k; even the one-action subset remains above both
  baselines. There is no Parley failure signature and no language/skill change.
  All 144 exact-file cases pass; 270/288 assignments change two files, while
  every language correctly leaves the already-sufficient tag helper unchanged.
  Preserve raw SHA
  `9955e67c36d7d3e3ea236644d731a6e4f9054da801b097cf41a7d64ceb64ce7c`
  and report 027. Stop scaling the synthetic bundle further; next use real
  repository maintenance episodes, or confirm size-eight only for the narrower
  Rust-parity claim.
- **Read-only repository evidence harness (iteration 028 preflight):** the
  bundle harness now supports safe per-language `context_files`, printed by
  `./sources` with `[read-only]` labels and included in integrity hashes.
  Context cannot overlap editable files; its characters/lines/rough tokens are
  recorded separately. Tasks may hide prompt-level public examples so agents
  diagnose from visible issue/test evidence while protected cases remain
  frozen. Tasks without context preserve prior prompt and source-output wording.
  Full suite passes 338/338. This is language-neutral harness work only; commit
  it before building the 028 project-style regression corpus.
- **Project-style diagnostic corpus (iteration 028 design):** four unrelated
  regressions cover an invoice boundary, after-hours routing, normalized tag
  identity, and deferred-capacity state. Every language receives three
  editable files plus the same two read-only issue/test artifacts; public
  examples are protected but omitted from the prompt. Independent oracles
  match all 20 cases, all 12 seeds compile, and every seed fails its intended
  regression. Manifest SHA is
  `49147f96ce0f50239314719f4fce76bd979bea2829f5eb629d4cdb0c7097013e`;
  the full suite passes 341/341. One pre-freeze seed transcription used
  unsupported `div` and was corrected to established Parley division syntax;
  no measured output or language/skill change resulted. Commit the corpus,
  then freeze and run the six-replicate 18-session protocol once without
  selective reruns or same-corpus optimization.
- **Project-style diagnostic preregistration (iteration 028):** corpus/harness
  commit `2cf86bf` is pushed. Protocol 028 freezes four complete regression
  repositories per session, six replicates per language, 18 fresh sessions,
  72 assignments, seed `20260819`, v0.3.155, and the unchanged 1,519-character
  skill. Every session sees 12 editable plus eight byte-identical read-only
  files through `./sources` exactly once first, then only `./check`; prompt
  examples stay hidden. Protocol SHA is
  `96916b4731801f0758eda1fdc5bd2bd007b7734052bb0a4a4f3d5b1356502af0`.
  Run once without selective reruns. A pass still requires larger confirmation;
  a failure cannot trigger same-corpus compiler or instruction tuning.
- **Project-style diagnostic result (iteration 028):** all 72 assignments pass
  their first check and hidden cases with zero repairs; every session preserves
  source order, command protocol, checker/context integrity, and read-only
  evidence. Strict parity is 2/4. Parley uses 15,020.88 median tokens/repo and
  7.0073 seconds versus Python's 14,390.75/6.5723 and Rust's
  14,801.63/7.0672: Parley is only 1.48% above Rust tokens and 0.85% faster,
  but remains 4.38% above Python tokens and 6.62% slower. Parley and Python
  change the seeded root-defect file 24/24 times; Rust is 22/24 because one
  session adds two caller-side compensations. Preserve raw SHA
  `a11d59d33756b13a4f27efb04389840b8de997991d6dd1031964846b271568ee`
  and report 028 SHA
  `9eb3a59c3b75e7ec95ed1dbcc590337c774e8b76932137c386570161b3ca4c65`.
  No language/skill change follows. Next use independently sourced project
  regressions with ambiguity, dependency navigation, test changes, and an
  explicit root-cause score; a positive pilot still needs larger confirmation.
- **Historically grounded expansion (iteration 029 design):** preserve the
  four 028 task objects exactly and add four deterministic, no-source-copy
  adaptations of public issue mechanisms: invalid-config fallback, aliased
  cache identity, FSM termination rollback, and cancellation lock loss. The
  combined manifest SHA is
  `50e55b985b959c96175632530cbb142b424453b4e815a731d2067a3432895b07`.
  Independent oracles match all 20 new cases; all 12 new seeds compile and
  fail their intended regression; evidence and prompts are symmetric; full
  suite passes 346/346. Every task/language now has a predeclared root-defect
  file, and all 48 Parley assignments must modify it as a fifth maintainability
  gate. Commit the corpus, then freeze six size-eight replicates/language with
  v0.3.155 and the unchanged skill. Preserve all output; do not tune from 028.
- **Historically grounded preregistration (iteration 029):** corpus commit
  `9c03ef56a718d0cff9dca6a29492440d77224fb6` is pushed. Protocol 029 freezes
  six complete size-eight replicates per language, 18 fresh sessions, 144
  assignments, seed `20260821`, v0.3.155, and the unchanged skill. Each session
  sees 24 editable plus 16 byte-identical read-only files. The strict four
  parity conditions remain; a fifth condition requires 48/48 Parley patches
  to touch their predeclared root-defect file. Protocol SHA is
  `3c4c4416f8bcac678a1bee3fbe001e87f7188fad80948695f2d19917674f3b25`.
  Run once with no selective reruns. A five-condition pass still
  requires larger confirmation; failure cannot trigger same-corpus tuning.
- **Historically grounded result (iteration 029):** all 144 assignments pass
  first check, hidden cases, and root-defect location with zero repairs. Every
  session preserves source order, command protocol, and checker/context
  integrity. Parley uses 8,408.56 median tokens/repo and 4.5455 seconds versus
  Python's 8,034.69/3.9298 and Rust's 8,489.06/5.0027. It beats Rust by 0.95%
  tokens and 9.14% elapsed but remains 4.65%/15.67% above Python, so primary
  strict parity is 2/4 and overall five-condition status is 3/5. Disclose that
  protocol context characters/lines sum raw files (3,614/47), while the runner
  meters join newlines too (3,622/55); rough tokens remain 710 and symmetry is
  unaffected. Preserve raw SHA
  `dd4fd41e8967c0b3f25e0957cd1b1793e79fb78fda65653fe63a9bacf8bcdc65`
  and report SHA
  `aef4caaf828caf4ff8c7083b96b6960bc460cc221cfea0cb372eea3093e6712b`.
  No language/skill change follows. Size-eight Rust parity is now replicated;
  Python-and-Rust parity is not. Next either confirm the Rust claim over 90
  sessions or use genuinely deeper project episodes for the strict claim.
- **Post-029 causal audit:** every language/session uses four messages, one
  completed file-change action, one source dump, and one check. Parley prompt
  and editable source are 5,860 and 7,978 characters/session versus Python's
  4,173 and 5,718–5,743; equal read-only context is 3,622. Its output tokens
  are slightly lower, so the remaining Python gap is input context/source, not
  repair or action variance. Repeated safe numeric-input unwrapping is
  semantically intentional and does not justify syntax. Next freeze a
  90-session size 1/2/4/8 curve on exact corpus 029 before deciding whether
  deeper repositories can move the strict gate.
- **Ninety-session scale preregistration (iteration 030):** protocol SHA
  `1eae4604ea8a9c0a4fbce404e1f177af74a06afbf8a93409781c1961a6e09b9f`
  freezes exact corpus 029 at sizes 1/2/4/8, two complete replicates, seed
  `20260823`: 90 fresh sessions and 192 assignments. Every task appears twice
  per language/scale; size eight remains the directional primary gate, and all
  64 Parley assignments must touch their frozen root file. Commit the protocol
  before output, then run every cell once. Report reciprocal-size token fits
  descriptively; do not treat two size-eight cells as confirmation or tune any
  task/language/instruction from the result.
- **Ninety-session scaling result (iteration 030):** all 90 fresh sessions and
  192 assignments pass first check, hidden cases, root-defect location,
  integrity, and command protocol with zero repairs. Size-eight Parley records
  8,344.00 tokens/repo and 4.5740 seconds versus Python's 8,059.56/4.0855 and
  Rust's 8,508.31/5.1263. It beats Rust by 1.93% tokens and 10.77% elapsed but
  trails Python by 3.53%/11.96%, so the strict gate is 2/4 and root quality is
  64/64. A reciprocal-size fit (R² > 0.99999 for all languages) estimates the
  Parley/Python gap as +2,009.535 fixed tokens/session plus +74.358 residual
  tokens/task; versus Rust it is +1,677.022 fixed and −287.745 residual, with a
  descriptive crossover near 5.83 tasks/session. Preserve raw SHA
  `ab49ad72652fc686e703aef2b7f5f9bd691d217ce4455237598bcca5d0b07adc`
  and report SHA
  `7f03cdc214a302e3b3236433111c4e579fc90f25cc80faa856c3fbd3dfc2e9bd`.
  No compiler or instruction change follows. Rust parity is confirmed for
  diagnosis bundles around six or more tasks; Python parity is not. Next use
  preregistered deeper project episodes, not same-corpus tuning.
- **Deeper project corpus checkpoint (iteration 031):** manifest SHA
  `7f81e6e6f62303d0f83c1e3451a1374c61c2fdf10a35a62fc6c89642178f46b2`
  freezes four independently sourced five-module tasks over redirect
  credentials, empty-collection configuration, forwarded OAuth origin, and
  terminal liveness. Every task/language has three equal read-only evidence
  files and one predeclared root. All 12 buggy seeds compile and fail at least
  two case groups; isolated root fixes pass 60/60 cases. Full benchmark tests
  pass 71/71 with pinned Parley and Cargo on `PATH`. Commit the corpus before
  protocol 031. Do not change the language/instruction or choose tasks from
  measured output.
- **Deeper project preregistration (iteration 031):** protocol SHA
  `4ede556b6010d2c011c0f109e83cf9502893536affed10b1e17973a1e2bbf19e`
  freezes six complete four-task bundles per language: 18 fresh sessions and
  72 assignments, seed `20260825`, v0.3.155, and the unchanged skill. The
  strict four-condition gate remains, plus 24/24 exact Parley root-file fixes.
  Run all cells once with no exclusion or rerun; a failure cannot trigger
  same-corpus language/instruction/task tuning.
- **Deeper project result (iteration 031):** all 72 assignments are hidden
  correct. Parley records 15,937.00 median tokens/repo and 7.3906 seconds versus
  Python's 23,668.38/9.2024 and Rust's 24,475.75/10.2195, with 22/24 first
  success versus 20/24 for both baselines. Strict efficiency/reliability passes
  4/4; weighted and repair-free sensitivities also favor Parley. All ten
  repairs are the same shared empty-state interpretation (Parley 2, Python 4,
  Rust 4). Every patch touches its frozen root, but one run per language also
  leaves a harmless count-helper edit, so exact-root quality is 23/24 and the
  overall five-condition result is 4/5. Preserve raw SHA
  `e6415531460770e6d8c05f45f01aa35628ee41081980fb3bb4e059352c5481b8`
  and report SHA
  `00d7a6c4d20e0b322a1f401cbe1f007eac5b054f0750516869af88c19fa844ef`.
  No language/instruction change follows. Next use an independent deeper
  confirmation with new mechanisms and the same gates; do not tune 031.
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
- **Fresh-agent benchmark protocol v2:** the language-neutral prompt forbids
  listing or reading workspace/checker files, requires the solution as the
  first tool action, and permits only exact `./check` shell commands. Each run
  records compliance and violations, eliminating the exploration variance
  observed in iteration 006.
- **90-session confirmation (iteration 015):** all 90 fresh sessions passed
  hidden cases and complied with protocol. Parley finished at 44,809 median
  tokens, 20.1131 seconds, and 25/30 first-pass versus Python at 43,031,
  17.4409, and 23/30, and Rust at 43,366.5, 20.1867, and 29/30. Parley is
  competitive and more reliable than Python on this matrix, but the
  predeclared strict best-baseline parity gate was not met. Compiler and skill
  are frozen; the next benchmark work is a broader predeclared task corpus,
  not transcript-level tuning.
- **Broad-corpus result (iteration 016):** all 48 fresh sessions across eight
  new tasks passed hidden cases and complied with protocol. Parley finished at
  43,455 median tokens, 20.0663 seconds, and 13/16 first-pass versus Python at
  41,832.5, 16.5347, and 15/16, and Rust at 42,020.5, 17.1042, and 16/16.
  Seven of eight Parley repair turns were isolated to word rotation; excluding
  that task leaves a similar 3.81% token gap to Python. No compiler change is
  justified. Require cross-task evidence plus general usefulness, semantic
  consistency, and maintainability for future proposals.
- **Workload-scale result (iteration 017):** all 192 task-solutions across 90
  fresh sessions passed hidden cases, checker integrity, and protocol checks.
  Fixed prompt overhead amortized as intended, but repair loops made size-eight
  Parley consume 19,273.88 median tokens/task versus Python's 5,716.75 (3.37×),
  so the strict gate failed tokens, time, and first-check reliability. A
  cross-task audit found ordinary identifier `position` rejected in four
  unrelated tasks, while unsupported `modulo` remained confined to rotation.
  The only justified compiler candidate is contextual `position`; preserve
  `benchmarks/reports/017-workload-scale-parity-failed.html`, keep the
  1,519-character skill frozen, and rerun the same workload as iteration 018.
- **Contextual-identifier replication result (iteration 018):** all 192 task
  solutions passed hidden cases and all 90 sessions preserved integrity and
  protocol compliance. The prior `position` failure family fell from five
  events across four tasks to zero. Size-eight Parley improved 22.94% to
  14,853.31 tokens/task and 13/16 first-check tasks, but remained 2.55× Python
  and failed three gate conditions. Five of six first-check failures were
  `modulo` in rotation; the other was a one-task `does` phrasing error. Make no
  compiler change yet. Preserve report 018, keep the skill frozen, and next
  test natural remainder vocabulary across unrelated arithmetic task families.
- **Arithmetic-vocabulary preregistration (iteration 019):** six new,
  independently worded task families and a 36-session three-language matrix
  are frozen in `benchmarks/vocabulary_protocol_019.json`. Agent-visible text
  avoids all candidate operator spellings. At least two unrelated Parley task
  families must independently use `modulo` in their first-check source before
  an alias is even eligible; eligibility still requires semantic consistency,
  maintainability, full tests, and broad confirmation.
- **Arithmetic-vocabulary result (iteration 019):** the eligibility gate
  passed without spelling priming: five first-check sources across clock,
  parity, and weekday task families independently used `modulo`. Parley
  finished 5/12 first-check and 11/12 hidden with 26 repairs; Python and Rust
  were 12/12 on both. The only eligible design is a maintainable infix alias
  for the existing guarded whole-number remainder path, with explicit
  Rust-style negative semantics. Preserve report 019, implement/test v0.3.153
  without changing the skill, replay saved failures, then freeze broad
  confirmation before any parity claim.
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

### Next work (in suggested order)

1. **Independent adoption evidence.** Record first-run/edit friction with
   maintainers other than the original author before claiming ecosystem use.
2. **Real Release Steward operation.** Use the installed workflow on each
   actual release candidate, preserve its report, and promote JSON only if
   structured-input friction recurs across at least two maintained products.
3. **Mature-repository validation.** If another benchmark is justified, use a
   real repository or release operation with history and dependency search;
   preregister it and do not tune from reports 031 or 032.
4. **Package publishing workflow** — checksum installs, publish-entry
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
- Run `python3 -m pytest tests/` (e2e needs cargo; runtime varies with Cargo cache).
- Keep diagnostics stable: never renumber existing P-codes.

## Conventions

- Version lives in `pyproject.toml` and `parley/__init__.py` (now 0.3.158).
- Examples must run clean; e2e tests assert their exact stdout.
- The skill (`skill/parley/SKILL.md`) is the agent-facing contract —
  treat it as part of the language release, not an afterthought.
