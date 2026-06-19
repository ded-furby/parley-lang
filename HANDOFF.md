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

## Where things stand (2026-06-20)

### Done and verified

- **Language v0.3 / toolchain v0.3.36** — full pipeline (Lark LALR parse → checker → Rust emit
  → cargo). The latest local suite has 203 tests, including e2e tests that
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
- **Claude Code skill** in `skill/parley/` — kept in sync with the
  language; update it whenever syntax changes.
- **Landing page** in `site/` — self-contained static site (index.html,
  style.css, main.js, 404.html; Three.js via CDN import map). The hero headline
  "speak plainly." is ~15k ember particles that respond to the cursor;
  scrolling shreds it to dust and condenses it into a black monolith (the
  native binary) behind the install command. A 2026-06-18 readiness pass
  added GSAP-powered DOM reveals/copy affordance, a skip link, and mobile
  overflow fixes. Verified with Playwright at desktop and mobile widths:
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

- Version lives in `pyproject.toml` and `parley/__init__.py` (now 0.3.36).
- Examples must run clean; e2e tests assert their exact stdout.
- The skill (`skill/parley/SKILL.md`) is the agent-facing contract —
  treat it as part of the language release, not an afterthought.
