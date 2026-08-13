# Response-web context optimization 004

## Status

Preregistered on 2026-08-13 after iteration 045 was published and before the
optimized card, iteration-046 corpus, scaffolds, protocol, or model output.

## Evidence and boundary

Iteration 045 used the frozen 313-token
`scaffolded-response-web-v0.5.6.md` card. Its Parley prompt was 298
`o200k_base` tokens larger than the Python prompt. Parley retained 100% hidden
semantic correctness but used 0.9717% more median complete session tokens and
16.6501% more median elapsed time than Python. One Parley first attempt also
compiled the unsupported compound comparison `is not at least`, then repaired
it after a diagnostic.

Those observations motivate a general context reduction; they do not permit a
same-corpus rerun or a claim that context alone caused the measured gaps.
Iteration 045 and its historical card remain byte-identical.

## Frozen requirements

The new response-web card must:

1. contain at most 128 `o200k_base` tokens and at most 550 UTF-8 bytes;
2. say that the printed scaffold is authoritative and the smallest owning file
   should be edited;
3. state the exact typed status/headers/body response-record requirement;
4. show the existing header-map creation, request-header lookup, and
   response-header assignment forms;
5. forbid server framing and hop-by-hop response headers;
6. list supported comparison phrases and explicitly forbid combining `not`
   with another comparator;
7. retain truncating `number from (a divided by b)` guidance;
8. add no task vocabulary, expected value, route, field, formula, model hint,
   or benchmark-specific repair.

Future Parley response-control scaffolds must serialize their JSON manifest in
canonical compact form. The compact form must parse to the identical object,
end with one newline, use no insignificant spaces, and use at most 135
`o200k_base` tokens for each future study manifest.

## Evaluation rule

Freeze the card bytes and token count before selecting any iteration-046 task
semantics. A later independent corpus may measure complete session tokens and
elapsed time. Passing this artifact target is not evidence that either primary
metric will improve, and no iteration-045 output may be replaced or rerun.
