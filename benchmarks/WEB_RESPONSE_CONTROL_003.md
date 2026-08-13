# Typed web response-control protocol 003

This product protocol is frozen after independent full-stack study 044 and
before any response-control implementation. Its baseline is Parley v0.5.5 at
commit `e71e8ad` and tree `837c0b7ab80c0d38fda9683d7bf0781c980d70e6`.
It does not reuse or modify a measured 044 task.

## Product need

Typed routes can already read request headers and declare one static 2xx
`success_status`. They cannot express a request-dependent authentication
failure, validation failure, redirect/location, challenge, or response header.
The next generic capability is therefore an opt-in typed response envelope.

## Frozen manifest and type contract

A route opts in with this schema-1 manifest member:

```json
"response": {
  "status_field": "status",
  "headers_field": "headers",
  "body_field": "body"
}
```

The three configured names must be distinct Parley field names. An opted-in
route may not also declare `success_status`. Its handler must return a record
with exactly those three fields:

- status: `number`
- headers: `map from text to text`
- body: any existing JSON-safe boundary type

Routes without `response` retain their current checked return type and static
`success_status` behavior. The checker reports stable P716--P719 diagnostics
for a non-record envelope, wrong field set, wrong status type, wrong headers
type, or unsafe body. `web check --json` and `parley.build.json` expose whether
each route uses a static or dynamic response contract.

## Frozen runtime contract

For an opted-in route, the generated server serializes only the configured
body field and uses the status and headers from the same typed return value.
It accepts status 200 through 599. Other values produce status 500 with JSON
error code `invalid_response_status`.

Response header names are normalized to lowercase and must be non-empty ASCII
HTTP token names. Names must be unique ignoring case. Values may not contain
CR, LF, NUL, another ASCII control byte, or DEL. At most 100 custom fields and
32,768 encoded header bytes (`name + ": " + value + CRLF`) are accepted.
Violations produce status 500 with JSON error code
`invalid_response_headers` and no supplied custom headers.

The server owns and rejects these names case-insensitively:
`connection`, `content-length`, `content-type`, `date`, `keep-alive`,
`proxy-authenticate`, `proxy-authorization`, `server`, `te`, `trailer`,
`transfer-encoding`, `upgrade`, and `x-content-type-options`. Application
headers such as `location`, `set-cookie`, `www-authenticate`, and `x-*` remain
available.

All responses retain the generated JSON content type, exact framing,
connection close, and `nosniff`. Status 204, 205, and 304 sends no body;
204 and 304 omit `Content-Length`, while 205 sends `Content-Length: 0`.
`HEAD` preserves the corresponding GET status, custom headers, and GET content
length while omitting the body.

## Preregistered verification gate

The change is accepted only if all of these pass:

1. Manifest and static checker tests cover valid custom field names, every
   rejected contract shape, and coexistence rejection with `success_status`.
2. A native authentication route returns 401 plus `www-authenticate` when a
   request header is missing and 200 plus an application header when present.
3. A native creation route returns 201 plus `location`, and a typed validation
   branch returns 422, while malformed request JSON still fails before the
   handler with 400.
4. Native tests cover invalid status, invalid/control-bearing/duplicate/
   reserved headers, header count and byte limits, bodyless statuses, and
   dynamic `HEAD` behavior.
5. Existing static-response route behavior and the dependency-free route-only
   Cargo path remain unchanged; the explicit-JSON backend also passes.
6. The complete test suite passes before the product version is advanced and
   the implementation is committed.

This protocol evaluates a missing typed-web capability and its safety
properties. Passing it would not establish production-framework parity or
universal language superiority. Any later agent comparison must freeze unseen
tasks only after this product change and its evidence are committed.

## Accepted v0.5.6 product

The implementation passed all six frozen conditions. Fourteen dedicated tests
cover manifest parsing, custom field names, P716--P719 static checks, both JSON
backends, compiled authentication and creation/validation routes, malformed
request precedence, invalid statuses, every declared header rejection class,
both header limits, bodyless statuses, and dynamic `HEAD`. Existing static
routes retain their success status and dependency-free Cargo path.

The complete repository suite passed **643/643** in 199.70 seconds before the
version advanced and **643/643** again in 199.47 seconds afterward. Historical
benchmark references were kept byte-for-byte at
their frozen hashes; the new user and agent references live in
`docs/WEB_RESPONSE_CONTROL.md` and `skill/parley/references/web-v0.5.6.md`.
The v0.5.6 wheel also built successfully from the release tree.
This accepts the generic capability and safety contract only. No post-v0.5.5
agent comparison has yet been run.
