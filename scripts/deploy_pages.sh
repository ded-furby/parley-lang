#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/parley-pages.XXXXXX")"

cleanup() {
  rm -rf "$tmp"
}
trap cleanup EXIT

cp "$root/site/index.html" "$tmp/index.html"
cp "$root/site/404.html" "$tmp/404.html"
cp "$root/site/style.css" "$tmp/style.css"
cp "$root/site/main.js" "$tmp/main.js"
cp "$root/site/registry.json" "$tmp/registry.json"
cp -R "$root/site/packages" "$tmp/packages"
touch "$tmp/.nojekyll"

git -C "$tmp" init
git -C "$tmp" branch -m gh-pages
git -C "$tmp" add .nojekyll index.html 404.html style.css main.js registry.json packages
git -C "$tmp" commit -m "Deploy landing page"
git -C "$tmp" remote add origin https://github.com/ded-furby/parley-lang.git
git -C "$tmp" fetch origin gh-pages
git -C "$tmp" push --force-with-lease origin gh-pages

echo "Published https://ded-furby.github.io/parley-lang/"
