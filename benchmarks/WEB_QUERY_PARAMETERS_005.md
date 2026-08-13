# Typed web query-parameter protocol 005

This product protocol is frozen after the valid study-047 result and its
post-result attribution, before any query-map checker, runtime, metadata,
documentation, agent-context, or v0.5.8 implementation. Its baseline is Parley
v0.5.7 at commit `7d21f51d35cb271c15873a0c417a1bfe89c9eefd` and tree
`13206bc2194d8f1de64aca3c3831c09fc28bd09b`. It does not reuse or modify a
measured agent task, and no study-047 outcome may be rerun or rejudged.

Baseline product hashes:

- `parley/web.py`: `3ccc181a93f47356da04ce6f624062d2e7584b1ce5db58bd0a4f79bb9857cdfd`
- `parley/cli.py`: `e8c3faf4973a1f59967eca61d3cf1cf1560cfad63363e5d70bb73c62be7d5f28`
- `parley/diagnostics.py`: `ce639286cd3582b2d34293f9f451e8d988adf592b37addaa44bc9f5691b5117f`
- `docs/WEB_PATH_PARAMETERS.md`: `bc01befe0f6cf7739c000674c115da9e13b22e69867fc3e162ce16573609e2cd`
- `skill/parley/references/web-v0.5.7.md`: `b98288c8a5e237c4dba8dfefb9c8291f766f9edc03290c4dd04fc5645ea90b11`

## Product need

`web_request.query` preserves the raw query string, but every application must
currently implement its own splitting, repeated-key handling, percent decoding,
UTF-8 validation, and error policy. This is unsafe duplication at an HTTP trust
boundary. The next generic capability is one deterministic parsed query map,
using existing Parley map/list access rather than new core-language syntax.

## Frozen checked handler contract

The existing five-field legacy record and six-field path-aware record remain
valid with unchanged behavior. A query-aware handler uses this exact seven-field
record:

```parley
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text, path_parameters as map from text to text, query_parameters as map from text to list of text
```

- `path_parameters` remains sixth; `query_parameters` is seventh and final.
- The seven-field shape works for exact and parameterized routes. Exact routes
  receive an empty path map.
- A query-aware handler may still take one typed JSON body after `web_request`.
- Every other field order or type remains P714. Its hint must name all three
  supported shapes clearly.
- `query_parameters` is a map from decoded names to lists of decoded values.
  Existing safe map/list expressions access it; no grammar or core type changes.

`parley web check --json` and `parley.build.json` expose a boolean
`query_parameters` field per route. It is true exactly when that handler uses
the seven-field request record. Existing ordered `path_parameters` metadata is
unchanged.

## Frozen decoding contract

Parsing occurs only after a query-aware route matches and before its handler or
typed body decoder runs.

- An absent or empty query produces an empty map.
- Split the raw query on `&`; split each non-empty pair at its first `=`.
  A name without `=` has an empty value. Empty pairs are ignored, but an empty
  decoded name is invalid.
- Percent-decode names and values exactly once as UTF-8. `+` decodes to a space;
  a literal plus must be `%2B`. Percent-decoded `&` and `=` remain data because
  structural splitting happens first.
- Repeated names append values in arrival order. The generated Rust map is
  key-ordered, matching Parley's deterministic map semantics.
- Malformed/truncated escapes, invalid UTF-8, NUL, ASCII control bytes, or DEL
  in a decoded name or value return status 400 with JSON error code
  `invalid_query_parameter` before the handler or typed body decoder runs.
- More than 128 non-empty query pairs returns the same 400 error. The existing
  request-target byte limit remains authoritative for total encoded size.
- Path routing and path-capture validation happen before query parsing. Thus a
  malformed path capture retains `invalid_path_parameter` precedence.
- Legacy and six-field handlers keep receiving the unchanged raw `query` text;
  their requests are not rejected by the new parser.

## Preregistered verification gate

The v0.5.8 change is accepted only if all of these pass:

1. Checker tests prove the five-, six-, and seven-field records are accepted in
   their declared route contexts; wrong field order/type and query-only
   six-field shapes retain P714 with the updated stable explanation.
2. Generated-contract and build-metadata tests prove every route reports the
   correct `query_parameters` boolean while preserving ordered path captures.
3. Native tests cover absent/empty queries, bare names, blank values, repeated
   names in arrival order, multiple names, `+` spaces, literal `%2B`, decoded
   Unicode, decoded `&`/`=`, exact routes, parameterized routes, `HEAD`, and a
   typed JSON body after query parsing.
4. Native negative tests cover empty decoded names, malformed/truncated escapes,
   invalid UTF-8, NUL, control/DEL bytes, and the 129-pair bound. They must prove
   `invalid_query_parameter` and no handler/body execution.
5. Precedence tests prove invalid path captures win before query errors, while
   legacy and path-only handlers preserve raw-query behavior even for strings
   the new query parser would reject.
6. Dynamic response control and both generated JSON backends compose with the
   seven-field record. Exact build hashes remain stable after every command.
7. Dedicated tests, the complete repository suite before and after version
   advance, historical frozen references, and a v0.5.8 wheel all pass. The
   accepted implementation receives a new user reference and compact agent
   reference rather than rewriting v0.5.7 evidence.

Passing this protocol would establish one bounded HTTP input capability and its
safety properties. It would not establish mature-framework parity, production
security, lower agent cost, or universal language superiority. The stable
study-047 build-cost observation remains a separate target.

Next: commit this zero-implementation protocol, then implement the checker,
runtime, metadata, documentation, and native verification without changing the
frozen semantics or gate.
