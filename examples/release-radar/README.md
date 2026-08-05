# Release Radar

Release Radar is the first Parley full-stack dogfood application. Its ordinary
Parley records are the JSON request and response contracts for two native HTTP
routes. The `readiness_score` function is also compiled to browser WebAssembly,
and generated JavaScript/TypeScript bindings expose the same checked rule to the
page.

```bash
parley web check examples/release-radar --json
parley web build examples/release-radar
parley web serve examples/release-radar
```

Open `http://127.0.0.1:8787`. The browser computes a local preview through
WASM; submitting the form sends typed JSON to the native Parley server and
renders the returned `release_assessment`.
