# Typed web query-parameter result 005

## Verdict: accepted as Parley v0.5.8

The implementation passed all seven conditions in the immutable protocol at
`benchmarks/WEB_QUERY_PARAMETERS_005.md` (SHA-256
`8c4d96512af3759d635d410b4b7372e268e80af5d90a94a00b895c6c9c1a64c3`).

Nine dedicated pytest cases cover the legacy, path-aware, and query-aware
request shapes; P714 diagnostics; check/build metadata; exact and parameterized
routes; absent, empty, bare, blank, repeated, Unicode, plus, escaped-plus, and
escaped-delimiter values; deterministic maps and arrival-ordered lists; `HEAD`;
typed JSON bodies; all declared malformed/control/limit failures; path/query/
body precedence; legacy raw-query compatibility; dynamic response control; and
both generated JSON backends.

The complete repository suite passed **767/767** in 225.23 seconds before the
version advanced and **767/767** in 219.19 seconds afterward. The final source
tree also passed **767/767**. Focused query/path/response/base-web verification
passed 56/56 after version advance.

The v0.5.8 wheel built successfully at 145,793 bytes. Its SHA-256 is
`044af3f790226b1bef82709c0f7c6d84121180476d96da1539eee2e69d141a67`;
embedded package metadata and `parley.__version__` both report 0.5.8.

Historical v0.5.7 references remained byte-for-byte unchanged:

- `docs/WEB_PATH_PARAMETERS.md`:
  `bc01befe0f6cf7739c000674c115da9e13b22e69867fc3e162ce16573609e2cd`
- `skill/parley/references/web-v0.5.7.md`:
  `b98288c8a5e237c4dba8dfefb9c8291f766f9edc03290c4dd04fc5645ea90b11`

Accepted product file hashes before commit:

- `parley/web.py`:
  `d0bbe5cfcf774c7bb79ab7949a2705dd9df52fa408b7fb370ab3cf4af16ddf29`
- `parley/cli.py`:
  `ce53c588510924c847b812f6115973fdb9dadbaff291fe2465dd4ed10f438872`
- `parley/diagnostics.py`:
  `506f91ce3b8c9207ea3022edab49f99677aed196efabb714674e42ec384ee5d0`
- `docs/WEB_QUERY_PARAMETERS.md`:
  `16da1feffc852af5c60bddf29377f435cd51f8ff31d61e6d9dd017181128c0b3`
- `skill/parley/references/web-v0.5.8.md`:
  `9b05892f00cffa11bc84f7eff18ec7dedfd7c9c42b41ca1ae0cdbd799f49670e`
- `tests/test_web_query_parameters_005.py`:
  `20567ef654be3ee081af5ca43b33869d630eede2d1c8373bee5c8490e2734fb0`

This accepts one bounded HTTP input capability and its safety contract. It is
not agent-comparison evidence, complete URL/framework parity, production
security certification, or evidence of universal language superiority. Study
047 and its failed gate remain immutable.
