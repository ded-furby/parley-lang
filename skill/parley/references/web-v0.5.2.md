# Parley typed-web quick reference

Project: source, `parley.web.json`, static files. Check:
`parley web check PROJECT --json`; build: `parley web build PROJECT`.

Division gives `decimal`; `number from (a divided by b)` truncates and is total,
so never add `otherwise`. Multiplication is `times` or `multiplied by`.

Schema 1 names exact routes and exports:

```json
{
  "schema_version": 1,
  "name": "app-name",
  "entrypoint": "main.par",
  "static_dir": "public",
  "routes": [
    {"method": "GET", "path": "/api/status", "handler": "status"},
    {"method": "POST", "path": "/api/update", "handler": "update"}
  ],
  "browser": {
    "entrypoint": "main.par",
    "exports": [{"name": "score"}]
  },
  "server": {"host": "127.0.0.1", "port": 8787, "max_body_bytes": 16384}
}
```

Handlers:

```parley
to status giving status_response:
    ...
to create with body as create_request giving create_response:
    ...
to inspect with request as web_request giving inspect_response:
    ...
to update with request as web_request, body as update_request giving update_response:
    ...
```

Request metadata, if used, is exactly:

```parley
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text
```

Records define strict JSON and reject unknown or missing required fields.
Supported values: `number`, `decimal`, `text`, `yesno`, `maybe`, lists,
text-keyed maps, records, kinds. Body routes expect JSON; handlers return a
supported value and cannot have `changing` parameters.

Keep each rule in one pure included function; handlers and thin browser wrappers
call it. During repairs, do not edit correct callers.

Browser exports are deterministic scalar functions using only `number`,
`decimal`, or `yesno` parameters/returns, without `changing`. Reachable code
cannot use I/O, files, randomness, attempts, closures, or dynamic functions.
JavaScript maps the types to `bigint`, `number`, `boolean`:

```js
import { loadParley } from "./parley.js";
const parley = await loadParley();
const result = parley.score(10n, 4n);
```
