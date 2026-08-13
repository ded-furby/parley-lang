# Parley typed response-control quick reference

Read the frozen `web-v0.5.2.md` reference for typed route and browser basics.
For a route whose status or headers vary by request, add this manifest member:

```json
"response": {"status_field": "status", "headers_field": "headers", "body_field": "body"}
```

Return exactly the configured record shape:

```parley
a web_response has status as number, headers as map from text to text, body as response_body
```

Only `body` becomes JSON. Status is 200--599. Use application headers such as
`www-authenticate`, `location`, `set-cookie`, and `x-*`; framing, hop-by-hop,
invalid, duplicate, control-bearing, or oversized headers are rejected. A
route may declare `success_status` or `response`, not both. `HEAD` follows GET
and bodyless status semantics are enforced.
