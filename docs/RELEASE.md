# Release and hosting checklist

This page is the operational checklist for making Parley usable by someone who
arrives from GitHub or the website.

## Local verification

Run from the repository root:

```bash
python3 -m pytest tests/
python3 -m pip install -e ".[dev]"
parley check examples/higher_order.par --json
parley run examples/hello.par
```

The e2e tests require Rust and `cargo`.

## GitHub repository

- The public repository is `https://github.com/ded-furby/parley-lang`.
- The live website is `https://ded-furby.github.io/parley-lang/`.
- `main` should contain the compiler, docs, examples, skill, website, and CI.
- Keep `README.md` as the entry point for developers.
- Keep `docs/SPEC.md`, `docs/REFERENCE.md`, `docs/TUTORIAL.md`,
  `docs/ERRORS.md`, and `skill/parley/SKILL.md` in sync for every language
  change.

## CI

The CI workflow runs the Python test suite on Ubuntu with Rust installed:

```text
.github/workflows/ci.yml
```

If GitHub rejects pushes that add or modify workflow files, refresh the GitHub
CLI/OAuth token with the `workflow` scope before pushing.

## Website

The landing page is a static site in `site/`:

```text
site/index.html
site/style.css
site/main.js
```

It has no build step. Any static host can serve the directory directly.

The current production deployment is GitHub Pages from the `gh-pages` branch,
with the static site files at the branch root.

### GitHub Pages option

1. Push `main`.
2. In repository settings, enable Pages.
3. Set the source to the `main` branch and `/site` folder, or use a Pages
   deployment workflow after workflow-scope authentication is fixed.
4. Visit the generated Pages URL and verify the canvas, copy button, nav links,
   reduced-motion behavior, and mobile layout.

### Custom domain option

1. Pick the domain after checking current availability. Current candidates are
   tracked in [DOMAINS.md](DOMAINS.md).
2. Add the domain in GitHub Pages settings.
3. Add a `site/CNAME` file containing the chosen domain.
4. Configure DNS records as GitHub Pages instructs.
5. Recheck HTTPS after the certificate is issued.

## Package publishing

The Git install path works today:

```bash
pip install git+https://github.com/ded-furby/parley-lang
```

PyPI publishing is not complete until the package name is reserved and an
authenticated release is uploaded. Do not claim `pip install parley-lang`
until that is verified.

## Pre-release audit

- `python3 -m pytest tests/` passes.
- All examples run through e2e tests.
- The website renders without console errors.
- The README install path is true.
- The skill file matches the current syntax.
- The GitHub branch is pushed and visible publicly.
- The website URL is live and linked from the repository description.
