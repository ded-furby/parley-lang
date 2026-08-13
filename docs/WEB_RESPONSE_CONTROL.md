# Typed web response control

Parley routes normally return one inferred JSON value with status 200, or the
static 2xx `success_status` declared in `parley.web.json`. A route that needs
request-dependent status and application headers can instead opt into a typed
response envelope:

```json
{
  "method": "POST",
  "path": "/api/items",
  "handler": "create_item",
  "response": {
    "status_field": "status",
    "headers_field": "headers",
    "body_field": "body"
  }
}
```

The handler must return a record with exactly the three configured fields:

```parley
a item_body has message as text, accepted as yesno
a item_response has status as number, headers as map from text to text, body as item_body

to create_item with request as create_request giving item_response:
    let headers be a map from text to text
    if request's count is at most 0:
        set item "x-validation" of headers to "count"
        give back an item_response with status 422, headers headers, body (an item_body with message "count must be positive", accepted no)
    set item "location" of headers to "/api/items/{request's name}"
    give back an item_response with status 201, headers headers, body (an item_body with message request's name, accepted yes)
```

The names may differ from `status`, `headers`, and `body`, but they must be
valid, distinct Parley names and match the record exactly. Status is `number`,
headers is `map from text to text`, and body may be any supported JSON-safe
type. Only the body field is JSON-encoded. `response` and `success_status` are
mutually exclusive. `parley web check --json` reports the selected contract.

## Runtime safety

Dynamic statuses may be 200 through 599. Invalid values become a structured
500 `invalid_response_status` error. Status 204, 205, and 304 follow bodyless
HTTP semantics. `HEAD` executes the corresponding GET contract, keeps its
status and headers, and omits its body.

Response names are normalized to lowercase and must be ASCII HTTP tokens.
Values may not contain control bytes. Names must be unique ignoring case, with
at most 100 fields and 32,768 encoded bytes. The generated server rejects
framing, hop-by-hop, and server-owned fields including `content-length`,
`content-type`, `connection`, `transfer-encoding`, and
`x-content-type-options`. It permits application fields such as `location`,
`set-cookie`, `www-authenticate`, and `x-*`. Any violation becomes a structured
500 `invalid_response_headers` error without forwarding the supplied headers.

This provides typed primitives for authentication decisions, creation,
validation, and redirects. It does not provide an identity provider,
authorization policy, session/cookie framework, TLS termination, or proxy.
