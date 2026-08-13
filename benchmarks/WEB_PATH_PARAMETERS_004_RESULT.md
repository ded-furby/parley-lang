# Typed web path-parameter result 004

## Verdict: accepted as Parley v0.5.7

The implementation passed all six conditions in the immutable protocol at
`benchmarks/WEB_PATH_PARAMETERS_004.md` (SHA-256
`d27d2f3ab39dd4ec3578f362ee7a3d4cf347526cc5039d7ac0159f29b398a531`).

Twenty-one dedicated tests cover one/multiple captures, exact priority, method
separation, template ambiguity, every declared manifest error, legacy and
extended metadata shapes, P714/P725 diagnostics, raw path/query preservation,
UTF-8 decoding, encoded separator and raw backslash rejection, malformed
escapes, invalid UTF-8, NUL, control/DEL bytes, 404 fallback, typed-body
precedence, parameterized `HEAD`, ordered check/build metadata, dynamic
response control, and both JSON backends. Raw `/` remains the segment delimiter
rather than a captured byte; an encoded slash is rejected before the handler.

The complete repository suite passed **727/727** in 205.22 seconds before the
version advanced, **727/727** in 206.22 seconds afterward, and **727/727** in
209.00 seconds on the exact final source tree. Historical
`docs/WEB.md` and other frozen references remained byte-for-byte unchanged;
the new user and agent references are `docs/WEB_PATH_PARAMETERS.md` and
`skill/parley/references/web-v0.5.7.md`.

The v0.5.7 wheel built successfully at 145,278 bytes with SHA-256
`553bfb8ffe003edb9e38d057c6617f7f9abbb634bdb1838a4402c18776daa7e1`.
This accepts one bounded typed-routing capability and safety contract. It is
not an agent-comparison result, production-framework parity, or evidence of
universal language superiority.

Accepted product file hashes before commit:

- `parley/web.py`:
  `3ccc181a93f47356da04ce6f624062d2e7584b1ce5db58bd0a4f79bb9857cdfd`
- `parley/cli.py`:
  `e8c3faf4973a1f59967eca61d3cf1cf1560cfad63363e5d70bb73c62be7d5f28`
- `parley/diagnostics.py`:
  `ce639286cd3582b2d34293f9f451e8d988adf592b37addaa44bc9f5691b5117f`
- `docs/WEB_PATH_PARAMETERS.md`:
  `bc01befe0f6cf7739c000674c115da9e13b22e69867fc3e162ce16573609e2cd`
- `skill/parley/references/web-v0.5.7.md`:
  `b98288c8a5e237c4dba8dfefb9c8291f766f9edc03290c4dd04fc5645ea90b11`
- `tests/test_web_path_parameters_004.py`:
  `8fb5fe57979bcfdd261fb6e64b0fac8b433e893fcc5e8bf7ba98cb95a3001097`
