use std::{env, path::PathBuf};

use axum::{
    Router,
    body::{Body, to_bytes},
    extract::Request,
    http::{StatusCode, header},
    response::{IntoResponse, Response},
    routing::{any, get, post},
};
use release_radar_035::{ReleaseInput, assess_release};
use serde::Serialize;
use serde_json::json;
use tower_http::services::{ServeDir, ServeFile};

const MAX_BODY_BYTES: usize = 16_384;
const BROWSER_MODULE: &str = r#"const asI64 = (value, name) => {
  if (typeof value === "bigint") return value;
  if (!Number.isSafeInteger(value)) throw new TypeError(`${name} must be a safe whole number`);
  return BigInt(value);
};
export async function loadParley() {
  const response = await fetch(new URL("/release_radar_035.wasm", import.meta.url));
  if (!response.ok) throw new Error(`Could not load Rust WASM: ${response.status}`);
  const result = await WebAssembly.instantiateStreaming(response);
  const wasm = result.instance.exports;
  return { readiness_score: (a, b, c, d, ready) => wasm.parley_readiness_score(
    asI64(a, "testsPassed"), asI64(b, "testsTotal"),
    asI64(c, "checklistDone"), asI64(d, "checklistTotal"), ready ? 1 : 0,
  ) };
}
"#;

fn json_response(value: impl Serialize, status: StatusCode) -> Response {
    let mut response = (status, serde_json::to_vec(&value).unwrap()).into_response();
    response.headers_mut().insert(
        header::CONTENT_TYPE,
        header::HeaderValue::from_static("application/json"),
    );
    response
}

fn error(code: &str, status: StatusCode, detail: impl Into<String>) -> Response {
    json_response(json!({"error": code, "detail": detail.into()}), status)
}

async fn status() -> Response {
    json_response(
        json!({
            "service": "Release Radar",
            "milestone": "typed-http-json-plus-browser-wasm",
            "typed_routes": 2,
            "browser_exports": 1,
            "ready": true
        }),
        StatusCode::OK,
    )
}

async fn assess(request: Request) -> Response {
    let media_type = request
        .headers()
        .get(header::CONTENT_TYPE)
        .and_then(|value| value.to_str().ok())
        .unwrap_or("")
        .split(';')
        .next()
        .unwrap_or("")
        .trim()
        .to_ascii_lowercase();
    if media_type != "application/json" && !media_type.ends_with("+json") {
        return error(
            "json_content_type_required",
            StatusCode::UNSUPPORTED_MEDIA_TYPE,
            "expected application/json",
        );
    }
    if let Some(length) = request.headers().get(header::CONTENT_LENGTH) {
        let declared = length
            .to_str()
            .ok()
            .and_then(|value| value.parse::<usize>().ok());
        if declared.is_none_or(|value| value > MAX_BODY_BYTES) {
            return error(
                "body_too_large",
                StatusCode::PAYLOAD_TOO_LARGE,
                "request body exceeds 16384 bytes",
            );
        }
    }
    let body = match to_bytes(request.into_body(), MAX_BODY_BYTES).await {
        Ok(body) => body,
        Err(_) => {
            return error(
                "body_too_large",
                StatusCode::PAYLOAD_TOO_LARGE,
                "request body exceeds 16384 bytes",
            );
        }
    };
    match serde_json::from_slice::<ReleaseInput>(&body) {
        Ok(release) => json_response(assess_release(release), StatusCode::OK),
        Err(reason) => error("invalid_json", StatusCode::BAD_REQUEST, reason.to_string()),
    }
}

async fn missing_api(request: Request<Body>) -> Response {
    error(
        "not_found",
        StatusCode::NOT_FOUND,
        format!("no API route {}", request.uri().path()),
    )
}

async fn browser_module() -> Response {
    let mut response = BROWSER_MODULE.into_response();
    response.headers_mut().insert(
        header::CONTENT_TYPE,
        header::HeaderValue::from_static("text/javascript; charset=utf-8"),
    );
    response
}

#[tokio::main]
async fn main() {
    let public = env::var_os("RELEASE_RADAR_PUBLIC")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("../../../examples/release-radar/public"));
    let wasm = env::var_os("RELEASE_RADAR_WASM")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            PathBuf::from("target/wasm32-unknown-unknown/release/release_radar_035.wasm")
        });
    let app = Router::new()
        .route("/api/status", get(status))
        .route("/api/assess", post(assess))
        .route("/api/{*rest}", any(missing_api))
        .route("/parley.js", get(browser_module))
        .route_service("/release_radar_035.wasm", ServeFile::new(wasm))
        .fallback_service(ServeDir::new(public).append_index_html_on_directories(true));
    let port = env::var("PARLEY_WEB_PORT")
        .ok()
        .and_then(|value| value.parse::<u16>().ok())
        .unwrap_or(8787);
    let listener = tokio::net::TcpListener::bind(("127.0.0.1", port))
        .await
        .unwrap();
    axum::serve(listener, app).await.unwrap();
}
