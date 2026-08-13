# Typed web query parameters (v0.5.8)

Parley can decode a matched route's query into a deterministic repeated-value
map. Opt in with the seven-field request record:

```parley
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text, path_parameters as map from text to text, query_parameters as map from text to list of text

a search_result has terms as map from text to list of text

to search with request as web_request giving search_result:
    give back a search_result with terms request's query_parameters
```

The original five-field record and v0.5.7 six-field path record remain valid.
`path_parameters` is always sixth and `query_parameters` is seventh and final.
Exact routes receive an empty path map. A typed JSON body may follow the request
record as before.

`parley web check --json` and `parley.build.json` report `query_parameters: true`
for handlers using this shape. Ordered path-capture metadata is unchanged.

## Decoding

For `/search?q=red+fox&q=swift&literal=%2B`, the map contains:

```json
{"literal":["+"],"q":["red fox","swift"]}
```

- Names and values are percent-decoded exactly once as UTF-8.
- `+` becomes a space; `%2B` is a literal plus.
- Repeated values retain arrival order; map keys retain deterministic ordering.
- Bare names and `name=` both have an empty value.
- Empty `&&` pairs are ignored. Empty decoded names are invalid.
- Decoded `&` and `=` are data, not separators.
- At most 128 non-empty pairs are accepted.

Malformed escapes, invalid UTF-8, NUL, control, or DEL bytes return status 400
with `invalid_query_parameter` before handler or typed-body execution. Path
matching and capture validation happen first, so `invalid_path_parameter`
retains precedence. Query parsing is opt-in: older request shapes continue to
receive the unchanged raw `request.query`, even when it contains malformed
percent escapes.

This is a bounded native HTTP input facility. It does not provide a complete
URL-standard implementation, typed scalar coercion, middleware, or a mature
framework's full request model.
