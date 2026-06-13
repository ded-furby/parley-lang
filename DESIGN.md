# Design

## Visual Theme

A forge at night. Near-black surface; a single ember-red brand color that
glows where the work happens; near-white ink. The WebGL particle scene is
the page's imagery: scattered English glyph-dust condensing, as you
scroll, into a dense faceted monolith (the native binary). Dark is forced
by the scene, not by fashion: emissive particles need a deep field to
read.

## Color Palette (OKLCH)

- `--bg`: oklch(0.13 0.012 29) — near-black, faint iron warmth
- `--surface`: oklch(0.17 0.014 29) — raised panels (code blocks)
- `--ink`: oklch(0.96 0.005 29) — near-white text
- `--ink-dim`: oklch(0.72 0.012 29) — secondary text (AA on bg)
- `--ember`: oklch(0.62 0.19 29.2) — brand red, links, highlights, particle glow
- `--ember-deep`: oklch(0.45 0.17 29.2) — pressed/hover, scene shadow tones
- Strategy: **Committed** — black surface, ember carries identity (30%+ of
  perceived surface via the scene). No second hue.

## Typography

- Display & body: **Zodiak** (Fontshare) — literary serif with machined
  edges; carries the "it's English" half of the brand. Weights 400/700.
- Code & labels: **Fragment Mono** (Google Fonts) — the "machine code"
  half. Used only where text IS code or compiler output, never as costume.
- Scale: fluid clamp(), display max 5.5rem, ratio ≥1.25 between steps.
- Letter-spacing on display: -0.02em. Body line-height 1.6, max 70ch.

## Components

- Code panes: solid `--surface`, 1px border oklch(0.28 0.02 29), radius
  10px, Fragment Mono 0.9rem, no shadows.
- Install command: single-line mono strip with copy button (verb label
  "Copy command").
- Links: ink underlined; hover shifts to ember. Buttons: ember fill, black
  text, radius 8px.

## Motion

- Scene: scroll-driven particle morph (glyph dust → monolith), cursor
  repulsion field, slow idle drift. Ease-out-quint everywhere; no bounce.
- DOM: content sections fade/rise 12px once, on first reveal only;
  visible-by-default (reveal enhances, never gates).
- `prefers-reduced-motion`: static mid-morph scene frame, no cursor force,
  no DOM entrance motion.

## Layout

- Fixed full-viewport canvas behind; DOM sections scroll over it.
- Single column, max 880px for prose; hero and finale full-bleed.
- Five beats: hero → what it looks like (code) → the loop (JSON repair) →
  how it works (pipeline) → install/footer.
