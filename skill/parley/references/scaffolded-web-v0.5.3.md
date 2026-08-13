# Parley scaffolded-web repair card

The printed scaffold is authoritative. Preserve its manifest, HTTP handlers,
entrypoint, and wrappers. Implement or repair the smallest owning included
logic function; keep it pure so HTTP and browser paths call one rule.

Follow the scaffold's signatures and four-space blocks. `let x be value`
creates; `set x to value` mutates; return with `give back`. Use
`yesno`/`yes`/`no`; compare with `is` plus `not`, `less than`, `at most`, `more
than`, or `at least`. Multiplication is `times` or `multiplied by`.

Division yields `decimal`; `number from (a divided by b)` truncates and is
total—never add `otherwise`.

Browser exports must stay deterministic scalars. Parley `number`, `decimal`,
and `yesno` map to JavaScript `bigint`, `number`, and `boolean`. Do not add I/O,
state, dependencies, or duplicate business logic. Run only the supplied
checker.
