# Product

## Register

brand

## Users

Two audiences, one page. First: developers who land here from GitHub or a
tweet, late in the evening, skeptical, deciding in thirty seconds whether
"an English-like language for AI agents" is a real compiler or a toy.
Second: people who run coding agents and want to know whether pointing
their agent at Parley actually reduces error loops. Both arrive on a
laptop, both have seen a hundred dev-tool landing pages this month.

## Product Purpose

Parley is an English-like programming language where AI agents are the
primary authors. Source reads as plain English; the compiler transpiles to
a memory-safe subset of Rust and ships a ~350 KiB native binary. Errors
come back as JSON repair instructions with stable codes so an agent
converges in one retry. The landing page exists to make one promise
physical: you speak plainly, and something solid comes out the other end.
Success: the visitor scrolls once, understands the promise, and runs the
install command or stars the repo.

## Brand Personality

Plain-spoken, machined, quietly confident. The voice of a well-built tool:
no exclamation marks, no superlatives, sentences that read like the
language itself ("set count to count plus 1"). The duality IS the brand:
literary English in, machine code out. Emotionally: the calm of watching
metal being poured into a mold.

## Anti-references

- igloo.inc is the craft benchmark, not a template: do not copy its
  voxel/ice aesthetic, its sci-fi terminal styling, or its structure.
- The 2026 dev-tool default: dark page, grotesk + mono, purple/green
  gradient glow, bento grid of feature cards. Parley must not look like a
  YC launch page.
- The editorial-magazine lane: italic display serif, ruled three-column
  layouts, monochrome restraint. Parley shows a scene, not a specimen.
- No mascots, no 3D blobs, no floating rounded cubes with soft shadows.

## Design Principles

1. **The scene is the argument.** The WebGL scene must literally enact the
   product: English words condense into a solid machined object. If the 3D
   were removed, the page should feel like the proof went missing.
2. **Practice what you preach.** The language's whole pitch is plainness.
   Every line of page copy must pass the same bar: one canonical way to
   say it, no jargon, no marketing verbs.
3. **Show real artifacts.** Real Parley source, real compiler JSON, real
   binary sizes. Nothing invented for the page.
4. **One idea per fold.** Long scroll, deliberate pacing, minimal detail.
   The user asked for one page that scrolls and not too much else.
5. **Cursor as conversation.** The pointer perturbs the scene and the
   scene answers. Interaction should feel like the parley the name
   promises.

## Accessibility & Inclusion

WCAG AA contrast on all text (≥4.5:1 body, ≥3:1 large). Full
`prefers-reduced-motion` path: scene renders a static composed state, no
scroll morph, no cursor force. Page must remain readable with WebGL
unavailable (content lives in DOM, canvas is decoration). Keyboard
navigation for all links and the copy-install affordance.
