# Parley typed-web quick reference

A project has Parley source, `parley.web.json`, and static files.
Check: `parley web check PROJECT --json`; build: `parley web build PROJECT`.

Division gives `decimal`; use `number from (a divided by b)` to truncate.
Multiplication is `times` or `multiplied by`.

Manifest schema 1 names exact routes and browser exports:

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

Route handlers use one of four signatures:

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

If used, request metadata has exactly this record definition:

```parley
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text
```

Records define request/response JSON. Values may be `number`, `decimal`, `text`,
`yesno`, `maybe`, lists, text-keyed maps, records, or kinds. Records reject
unknown or missing required fields. Body routes expect JSON. Handlers must
return a supported value and cannot have `changing` parameters.

Browser exports are deterministic scalar functions using only `number`,
`decimal`, or `yesno` parameters/returns, with no `changing`. Browser-reachable
code cannot use I/O, files, randomness, attempts, closures, or dynamic
functions. JavaScript maps those types to `bigint`, `number`, and `boolean`:

```js
import { loadParley } from "./parley.js";
const parley = await loadParley();
const result = parley.score(10n, 4n);
```
