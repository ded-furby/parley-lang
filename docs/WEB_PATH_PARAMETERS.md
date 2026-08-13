# Typed web path parameters (v0.5.7)

Parley web routes can capture named whole path segments without adding routing
syntax to the language:

```json
{
  "method": "GET",
  "path": "/api/items/{item_id}",
  "handler": "show_item"
}
```

Each `{name}` occupies a complete, non-empty segment and must be a Parley field
name. A name may appear only once in one route. Exact routes take priority over
templates, so `/api/items/current` and `/api/items/{item_id}` can safely
coexist. Two same-method templates are rejected if one request could match
both; routes for different methods remain independent.

## Handler contract

A parameterized route receives the extended HTTP metadata record:

```parley
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text, path_parameters as map from text to text

a item_result has item_id as text, state as text

to show_item with request as web_request giving item_result:
    let item_id be (maybe item "item_id" of request's path_parameters) otherwise ""
    give back an item_result with item_id item_id, state "found"
```

`path_parameters` must be the sixth and final field. A typed JSON body may
follow `web_request` exactly as for an exact route. Exact routes may keep using
the original five-field record, or use the extended record and receive an
empty parameter map. Other record shapes produce P714; a parameterized route
without the extended record produces P725.

`parley web check --json` and `parley.build.json` report an ordered
`path_parameters` list for every route.

## Matching and decoding

Matching uses the path before `?`. Existing `request.path` and `request.query`
values remain raw; only captured values are percent-decoded. Captures decode
exactly once as UTF-8, so `caf%C3%A9` becomes `café`. Literal template segments
are exact: `%63urrent` does not alias the literal `current` route.

Malformed escapes, invalid UTF-8, and captured slash, backslash, NUL, control,
or DEL bytes return status 400 with `invalid_path_parameter` before handler or
typed-body execution. Captures never participate in static filesystem lookup.
`HEAD` follows parameterized `GET` exactly and omits the body.

This is typed routing for bounded native web applications. It does not provide
middleware, authorization policy, reverse-proxy normalization, or a mature
framework's complete URL/router feature set.
