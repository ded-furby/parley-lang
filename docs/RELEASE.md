# Release and hosting checklist

This page is the operational checklist for making Parley usable by someone who
arrives from GitHub or the website.

## Local verification

Run from the repository root:

```bash
python3 -m pytest tests/
python3 -m pytest tests/test_lsp.py
python3 -m pip install -e ".[dev]"
parley check examples/higher_order.par --json
python3 -m pytest tests/test_parser.py::test_include_bundled_std_package tests/test_e2e.py::test_bundled_std_packages_run tests/test_e2e.py::test_bundled_std_list_package_runs tests/test_e2e.py::test_bundled_std_map_package_runs
python3 -m pytest tests/test_packages.py
tmp="$(mktemp -d)" && (cd "$tmp" && parley package new demo_package)
tmp="$(mktemp -d)" && mkdir "$tmp/demo_pkg" && printf 'to ready giving yesno:\n    give back yes\n' > "$tmp/demo_pkg/main.par" && parley package publish demo_pkg "$tmp/demo_pkg" --version 1.0.0 --description "demo package" --license MIT --maintainer "Demo Maintainer <https://example.com>"
tmp="$(mktemp -d)" && mkdir "$tmp/demo_pkg" && printf 'to ready giving yesno:\n    give back yes\n' > "$tmp/demo_pkg/main.par" && hash="$(python3 -c 'import hashlib, pathlib, sys; p=pathlib.Path(sys.argv[1]); print(hashlib.sha256(b"main.par\0"+(p/"main.par").read_bytes()).hexdigest())' "$tmp/demo_pkg")" && printf '{"schema_version":1,"packages":{"demo_pkg":{"version":"1.0.0","source":"demo_pkg","description":"demo package","license":"MIT","maintainer":"Demo Maintainer <https://example.com>","sha256":"%s"}}}\n' "$hash" > "$tmp/registry.json" && (cd "$tmp" && parley package check-registry registry.json && parley package search --registry registry.json && parley package install demo_pkg --registry registry.json && parley package verify)
parley doctor --json
parley --version
parley benchmark measure --no-check --format json --output /tmp/parley_seed_metrics.json
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
- Keep `parley-lsp` wired in `pyproject.toml`; it is the editor integration
  entry point and publishes the same P-code diagnostics as `parley check`.
- Keep bundled `.par` packages under `parley/stdlib/` listed in
  `tool.setuptools.package-data`.
- Keep `parley doctor --json` passing; it is the quick setup proof for
  installed users and automation.
- Keep `parley package search --registry` and registry-backed install covered;
  this is the first public package-index surface. Registry entries may include
  `sha256`; installs must verify it and record the digest in
  `parley.lock.json`.
- Keep `parley package publish` covered; it prints a registry-ready entry for
  local package sources with license, maintainer, and the deterministic package
  SHA-256, and it must reject non-semantic versions.
- Keep `parley package verify` covered; it must fail for modified packages and
  old lock entries that lack a digest.
- Keep `parley package check-registry` covered; it must reject missing
  checksums, missing license/maintainer metadata, and package sources whose
  content no longer matches the registry. It must also reject non-semantic
  package versions.
- Keep `site/registry.json` and `site/packages/` deployed through
  `scripts/deploy_pages.sh`; the hosted starter index lives at
  `https://ded-furby.github.io/parley-lang/registry.json`.
- Keep `parley benchmark measure --format json` working from a source
  checkout; it is the research readiness proof for the seed corpus, whose
  manifest records the Parley, Python, and Rust reference sources.

## CI

The CI workflow runs the Python test suite on Ubuntu with Rust installed:

```text
.github/workflows/ci.yml
```

If GitHub rejects pushes that add or modify workflow files, refresh the GitHub
CLI/OAuth token with the `workflow` scope before pushing.

Current status: the workflow commit is still local-only until the account is
reauthorized through GitHub's device flow with the `workflow` scope.

## Website

The landing page is a static site in `site/`:

```text
site/index.html
site/style.css
site/main.js
```

It has no build step. Any static host can serve the directory directly.

The current production deployment is GitHub Pages from the `gh-pages` branch,
with the static site files at the branch root. Publish site updates with:

```bash
scripts/deploy_pages.sh
```

### GitHub Pages source

1. Keep source files in `site/` on `main`.
2. Run `scripts/deploy_pages.sh` to copy them to the root of `gh-pages`.
3. GitHub Pages serves `gh-pages` at `https://ded-furby.github.io/parley-lang/`.
4. Verify the canvas, copy button, nav links, custom 404, reduced-motion
   behavior, and mobile layout after every deploy.

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

Release build commands:

```bash
python3 -m pip install -e ".[dev,publish]"
python3 -m build
python3 -m twine check dist/*
```

## Pre-release audit

- `python3 -m pytest tests/` passes.
- All examples run through e2e tests.
- The website renders without console errors.
- `/404.html` renders as a branded error page.
- The README install path is true.
- The skill file matches the current syntax.
- The benchmark CLI can measure the seed corpus, whose manifest records the
  Parley/Python/Rust reference sources, and summarize a run log.
- The package CLI can search a schema-1 registry, install a listed package,
  reject a bad checksum, verify a locked install, validate a registry manifest,
  and print a publish entry with license and maintainer metadata for a local
  package. Package install, publish, and registry validation reject
  non-semantic versions.
- The hosted registry URL serves JSON with license, maintainer, SHA-256
  metadata, and the listed package source files.
- The GitHub branch is pushed and visible publicly.
- The website URL is live and linked from the repository description.
