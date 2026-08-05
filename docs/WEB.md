# Typed web projects

Parley web projects turn ordinary checked records and functions into a native
HTTP/JSON server and, optionally, a browser WebAssembly module. The web layer
uses a manifest instead of adding framework-specific syntax to the language.

## Start and run

```bash
parley web new status-board
parley web check status-board --json
parley web build status-board
parley web serve status-board
```

`web check` does no Rust build. It parses and type-checks the entrypoint, then
checks every route and browser ABI declaration. `web build` produces a
dedicated bundle containing:

```text
dist/
  server                 native executable
  parley.build.json      exact build contract
  public/                copied static files
    parley.wasm          optional generated browser module
    parley.js            optional JavaScript loader and typed wrappers
    parley.d.ts          optional TypeScript declarations
```

Run the bundle from its own directory. The server reads `PARLEY_WEB_HOST` and
`PARLEY_WEB_PORT` as optional deployment overrides. The manifest values remain
the defaults.

## Manifest

`parley.web.json` schema 1 binds exact HTTP routes to Parley functions:

```json
{
  "schema_version": 1,
  "name": "release-radar",
  "entrypoint": "main.par",
  "static_dir": "public",
  "routes": [
    {"method": "GET", "path": "/api/status", "handler": "project_status"},
    {"method": "POST", "path": "/api/assess", "handler": "assess_release"}
  ],
  "browser": {
    "entrypoint": "main.par",
    "exports": [{"name": "readiness_score"}]
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8787,
    "max_body_bytes": 16384
  }
}
```

Entrypoints and static directories must stay within the project. Routes are
exact method/path pairs in this first contract; dynamic parameters and
middleware are deliberately not implied.

## Typed JSON routes

A route handler may have one of four checked signatures:

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

The optional metadata record has one exact definition:

```parley
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text
```

The compiler infers the request JSON type and response JSON type from the
function. Supported JSON values are `number`, `decimal`, `text`, `yesno`,
`maybe`, lists, text-keyed maps, records, and kinds. Records reject unknown JSON
fields, so a misspelled agent-generated key is a 400 response instead of
silently disappearing. Body routes require `application/json` or a `+json`
media type. Invalid request JSON returns a structured error; response encoding
failure and handler failure return 500.

This is generated static typing, not runtime schema guessing: a manifest that
names a missing handler, a non-returning handler, a changing parameter, a
number-keyed JSON map, or an unsupported signature fails `parley web check`
with stable P710–P715 diagnostics before Rust runs.

## Browser/WASM exports

The browser target currently exposes deterministic scalar functions. Exported
parameters and returns may be `number`, `decimal`, or `yesno`; parameters may
not be `changing`. The checker walks the export call graph and rejects terminal
I/O, files, randomness, runtime-failure handling, closures, and dynamic
function values with P720–P723 diagnostics.

```parley
to readiness_score with passed as number, total as number, package_ready as yesno giving number:
    ...
```

```js
import { loadParley } from "./parley.js";

const parley = await loadParley();
const score = parley.readiness_score(385, 385, true); // bigint
```

Parley `number` is a signed 64-bit value, so the JavaScript boundary accepts a
safe integer or `bigint` and returns `bigint` without precision loss. `decimal`
maps to JavaScript `number`; `yesno` maps to `boolean`. The generated
declaration file records that API. The server serves `.wasm` as
`application/wasm`, allowing browsers to use streaming instantiation.

Install the Rust target once before a browser build:

```bash
rustup target add wasm32-unknown-unknown
```

## HTTP and static-file behavior

The generated server uses Rust's standard `TcpListener` and one isolated
thread per connection. It applies read/write timeouts, a 64 KiB header limit,
the manifest body limit, exact `Content-Length`, UTF-8 typed bodies, conflicting
length rejection, and no chunked-request support. Responses set their own
length, close the connection, and include `X-Content-Type-Options: nosniff`.

Static paths are canonicalized and must remain within the copied `public/`
root. `/` maps to `index.html`; missing or unsafe paths fall through to a JSON
404. The build never serves the Parley source tree.

## Honest boundary

This is a usable typed full-stack foundation, not yet a replacement for mature
web frameworks. It does not yet provide TLS termination, HTTP/2 or HTTP/3,
streaming/chunked request bodies, WebSockets, dynamic path parameters,
middleware composition, database drivers, authentication, structured response
headers, browser text/list ABIs, or an async connection runtime. Put the native
server behind a production reverse proxy and treat the browser scalar ABI as
the first stable slice.

The flagship proof is [`examples/release-radar`](../examples/release-radar):
the same Parley readiness function runs locally through WASM and inside a typed
native JSON handler. Future additions should come from recurring application
needs in this product and unrelated adopters—not from benchmark transcripts.
