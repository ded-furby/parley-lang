---
name: parley
description: Write, check, and run Parley programs (.par files), an English-like language that compiles through Rust to native binaries. Use for Parley code, .par files, or plain-English compiled programs.
---

# Parley

Use 4-space blocks and `to main:`. When present, use only `./check`; follow
hints to `"ok": true`.

- Names are one `snake_case` token. `position`/commands are reserved; use
  `index` or `cursor`.
- Booleans: `yesno`, `yes`, `no` (not `true`/`false`). Comparisons: `is`,
  `is not`, `is less than`, `is at most`, `is more than`, `is at least`.
- Input: `ask ""`; number: `ask for a number ""` or
  `number from quantity_text`; check the maybe, then `value of`.
- Collections: `an empty list of text`; `a map from text to number`;
  `add x to xs`; `item i of xs`; `remove item i of xs`; `map contains key`;
  `set item key of map to value`; `keys of map`. Item lookup gives the value,
  not a maybe.
- Text: `line split by " "`; `parts joined with ","`; interpolation
  `"{value}"`; literal braces `"{{"` / `"}}"`.
- Return with `giving TYPE` / `give back value`. Parenthesize expression calls:
  `if (valid with line):`. Statement calls are bare.
- `changing` appears only in parameter declarations; calls pass plain vars.
- Control: `if`/`otherwise`, `while`, `repeat n times`, `for each index from 1
  to length of xs` (inclusive). `stop`/`skip` only inside loops. Block names
  stay in their block.
- Bind complex calls/items to temporary names before long conditions.

For more, read `references/core-v0.3.144.md`.
