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

## Where things stand (2026-06-18)

### Done and verified

- **Language v0.2** — full pipeline (Lark LALR parse → checker → Rust emit
  → cargo). **114 tests pass**, including e2e tests that compile every
  feature to a native binary and assert stdout. Ten examples in
  `examples/`. Docs: `docs/TUTORIAL.md`, `REFERENCE.md`, `SPEC.md`,
  `ERRORS.md` (generated from `parley/diagnostics.py` — regenerate it if
  you add a P-code; `tests/test_diagnostics.py` enforces coverage).
- **v0.2 features just added:** richer `when` patterns (multi-value arms
  `is 1, 2 or 3:`, inclusive numeric ranges `is 10 to 20:`, new P312) and
  first-class function values (`the function f`, type
  `(function taking A giving R)`, Rust fn pointers, new P313). Also fixed
  a latent bug: `when` over a decimal with an integer arm used to emit
  Rust that did not compile (now typed literals, see `_pattern_num`).
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
  metrics harness, and `docs/RELEASE.md` records the GitHub/Pages/PyPI
  readiness checklist. `docs/SPEC.md` now correctly says v0.2 and no longer
  claims higher-order functions are missing. `docs/DOMAINS.md` records checked
  domain candidates; current recommendation is `parleylang.com`.
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

1. **Anonymous closures with captured variables.** Today only named,
   non-`changing` functions can be values. Design sketch: a closure
   expression in English (e.g. `a function taking x as number giving
   number: x times 2` — syntax undecided), emitted as `Rc<dyn Fn(...)>`
   with clone-on-capture to preserve value semantics. This is the largest
   remaining language gap.
2. **Complete the benchmark runner** (goal 3). `benchmarks/` now measures
   Parley/Python/Rust seed references and checks Parley with JSON diagnostics.
   Still needed: LLM-tokenizer counts, generated-source capture, repair-turn
   logging, and repeated agent error-rate runs.
3. **Borrow-based passing for big values** — perf optimisation in
   `emit_rust.py` (pass `&T` for non-changing heap params, clone only on
   store). Touches the whole emitter; do it with the e2e suite green.
4. **LSP server**, **packages beyond `include`** — later.

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

- Version lives in `pyproject.toml` and `parley/__init__.py` (now 0.2.0).
- Examples must run clean; e2e tests assert their exact stdout.
- The skill (`skill/parley/SKILL.md`) is the agent-facing contract —
  treat it as part of the language release, not an afterthought.
