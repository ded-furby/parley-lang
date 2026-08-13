# Parley typed query-parameter quick reference

Read `web-v0.5.7.md` for path captures. To receive a decoded query map, use the
seven-field request record with both maps last:

```parley
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text, path_parameters as map from text to text, query_parameters as map from text to list of text

let values be (maybe item "q" of request's query_parameters) otherwise a list of text
let first be (maybe item 1 of values) otherwise ""
```

Repeated values keep arrival order. Names/values decode once as UTF-8; `+` is a
space and `%2B` is plus. Invalid escapes, UTF-8, empty names, control bytes, or
more than 128 pairs return 400 before the handler/body. Path errors win first.
Five- and six-field request records retain raw-query behavior.
