# Parley scaffolded HTTP

Trust the scaffold; edit the smallest owner. Dynamic handlers return the exact typed status/headers/body record. Create headers with `let headers be a map from text to text`; read with `(maybe item "authorization" of request's headers) otherwise ""`; write with `set item "location" of headers to value`. Never set framing/hop headers.

For `{name}` routes, keep `path_parameters` sixth; read `(maybe item "name" of request's path_parameters) otherwise ""`. Query-aware `web_request` keeps `query_parameters as map from text to list of text` seventh/last. Read values with `(maybe item "q" of request's query_parameters) otherwise a list of text`, then `(maybe item 1 of values) otherwise ""`. Captures/query values are decoded.

Use `is less than`, `is more than`, `is at most`, `is at least`, or `is not`; never combine `not` with another comparator. `number from (a divided by b)` truncates.
