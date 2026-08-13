# Typed web path-parameter protocol 004

This product protocol is frozen after study 046 and rejected build-backend
study 003, before any path-template parser, checker, runtime, documentation, or
v0.5.7 implementation. Its baseline is Parley v0.5.6 at commit `bed8fde` and
tree `6e3b0c94227d25d3a4c47e5015270a4a4de52d75`. It does not reuse or modify a
measured agent task.

## Product need

Typed routes currently match only exact paths. Applications can inspect the
raw path through `web_request`, but they cannot declare, validate, or receive a
dynamic resource identifier without implementing routing themselves. The next
generic capability is therefore checked whole-segment path templates.

## Frozen manifest contract

Schema-1 route paths may contain named whole-segment captures:

```json
{"method": "GET", "path": "/api/items/{item_id}", "handler": "show_item"}
```

- A capture occupies one complete non-empty segment and uses a Parley field
  name matching `[A-Za-z_][A-Za-z0-9_]*`.
- Braces outside a whole capture, empty capture names, repeated names in one
  route, empty template segments, and trailing template slashes are rejected.
- Existing exact paths retain their current accepted syntax and behavior.
- Exact routes take priority over a matching template regardless of declaration
  order. Thus `/api/items/current` may coexist with `/api/items/{item_id}`.
- Two templates for the same method are rejected when any request path could
  match both. Methods remain independent. Existing duplicate exact-route
  rejection remains unchanged.
- `HEAD` continues to dispatch through `GET`, including parameterized GET
  routes, and sends no body.

`parley web check --json` and `parley.build.json` expose an ordered
`path_parameters` list for every route; exact routes expose an empty list.

## Frozen checked handler contract

The legacy metadata record remains valid for exact routes:

```parley
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text
```

Any route may instead use the extended record, whose sixth and final field is:

```parley
path_parameters as map from text to text
```

A parameterized route must take extended `web_request` as its first parameter,
optionally followed by one existing typed JSON body. Otherwise `web check`
emits stable diagnostic P725 before Rust runs. Exact routes populate an empty
map when they use the extended record. The existing P714 diagnostic continues
to reject every other `web_request` shape.

The handler reads a declared capture with the existing safe map expression,
for example `(maybe item "item_id" of request's path_parameters) otherwise
""`. No new core-language syntax is added.

## Frozen runtime and safety contract

- Matching uses the request path before `?`; `web_request.path` and
  `web_request.query` preserve their existing raw strings.
- Each captured segment is percent-decoded exactly once as UTF-8. Literal
  template segments are matched exactly and are not decoded aliases.
- A malformed escape, invalid UTF-8, decoded slash, backslash, NUL, ASCII
  control byte, or DEL in a captured value produces status 400 with JSON error
  code `invalid_path_parameter` before the handler or typed body decoder runs.
- A non-matching template continues to the next route, static fallback, or the
  existing structured 404. Captures never influence filesystem path lookup.
- Parameter maps contain exactly the template's names and decoded values.
  Values may be empty only if a future contract explicitly permits empty path
  segments; this protocol does not.

## Preregistered verification gate

The v0.5.7 change is accepted only if all of these pass:

1. Manifest tests cover valid one/multiple-capture templates; exact/template
   coexistence; invalid braces, names, repeats, empty segments, trailing slash;
   duplicate exact routes; and every ambiguous-template overlap class.
2. Checker tests prove parameterized routes require the extended metadata
   record, exact routes accept both legacy and extended records, wrong extended
   shapes retain P714, and the missing dynamic contract emits P725.
3. Native tests cover exact-route priority, single and multiple captures,
   method separation, raw path/query compatibility, Unicode percent decoding,
   404 behavior, JSON body decoding after routing, and parameterized `HEAD`.
4. Native negative tests cover malformed/truncated escapes, invalid UTF-8,
   encoded and raw slash/backslash, NUL, control bytes, and DEL, all returning
   `invalid_path_parameter` without invoking handler logic.
5. `web check --json` and `parley.build.json` report ordered parameter names;
   existing exact-route metadata and response-control behavior remain stable.
6. The complete existing suite passes before and after the version advance,
   historical frozen references remain byte-for-byte unchanged, and a v0.5.7
   wheel builds successfully.

Passing this protocol would establish one bounded typed-routing capability and
its safety properties. It would not establish mature-framework parity,
production security, lower agent cost, or universal language superiority. Any
later comparative study must freeze unseen tasks only after the product and
evidence are committed.

Next: commit this protocol with zero implementation, then build the manifest,
checker, runtime, metadata, and native verification against the frozen gate.

