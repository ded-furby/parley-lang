# Parley scaffolded response-web card

The printed scaffold is authoritative. Preserve its files, manifest, route
paths, field names, handler signatures, and wrappers. Make the smallest owning
change; keep shared rules pure. Use four-space blocks, `let` to create, `set`
to mutate, and `give back` to return.

A dynamic route declares:

```json
"response":{"status_field":"status","headers_field":"headers","body_field":"body"}
```

Its handler returns exactly a record with `status as number`, `headers as map
from text to text`, and the scaffold's JSON-safe `body`. Create headers with
`let headers be a map from text to text`; write one with
`set item "location" of headers to value`; read request headers with
`(maybe item "authorization" of request's headers) otherwise ""`.
Use status 200--599. Never set server-owned framing or hop-by-hop headers.

Use `yesno`/`yes`/`no`; comparisons use `is` plus `not`, `at most`, `more
than`, or `at least`. Multiplication is `times`; division yields `decimal`, and
`number from (a divided by b)` truncates without `otherwise`.

Browser exports stay deterministic scalars: `number`, `decimal`, `yesno` map
to JavaScript `bigint`, `number`, `boolean`. Do not add I/O, state,
dependencies, duplicate business logic, or extra checker runs.
