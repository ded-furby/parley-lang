# Parley typed path-parameter quick reference

Read `web-v0.5.2.md` for typed routes/browser basics and `web-v0.5.6.md` for
dynamic response envelopes. A route may capture whole path segments:

```json
{"method":"GET","path":"/api/items/{item_id}","handler":"show_item"}
```

Parameterized handlers take extended metadata with `path_parameters` last:

```parley
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text, path_parameters as map from text to text

let item_id be (maybe item "item_id" of request's path_parameters) otherwise ""
```

Names are ordered, unique whole-segment Parley identifiers. Exact routes win;
overlapping same-method templates are rejected. Captures are decoded once as
UTF-8. Invalid escapes or decoded separators/control bytes return 400 before
the handler. `web check --json` reports `path_parameters` for each route.

