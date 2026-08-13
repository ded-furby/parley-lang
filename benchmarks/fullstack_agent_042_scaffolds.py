"""Generate frozen language workspaces for full-stack agent study 042."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .fullstack_agent_036_scaffolds import (
        PYTHON_APP_TEMPLATE as BASE_PYTHON_APP_TEMPLATE,
        RUST_MAIN_TEMPLATE as BASE_RUST_MAIN_TEMPLATE,
        TS_SERVER_TEMPLATE as BASE_TS_SERVER_TEMPLATE,
        ScaffoldFile,
        _clean,
        _replace,
    )
    from .fullstack_agent_042_logic import (
        PARLEY_LOGIC,
        PARLEY_MAIN,
        PYTHON_BROWSER,
        PYTHON_BROWSER_EXPORT,
        PYTHON_LOGIC,
        RUST_LIB,
        RUST_WASM,
        TS_SCHEMA,
        TYPESCRIPT_LOGIC,
    )
except ImportError:
    from fullstack_agent_036_scaffolds import (
        PYTHON_APP_TEMPLATE as BASE_PYTHON_APP_TEMPLATE,
        RUST_MAIN_TEMPLATE as BASE_RUST_MAIN_TEMPLATE,
        TS_SERVER_TEMPLATE as BASE_TS_SERVER_TEMPLATE,
        ScaffoldFile,
        _clean,
        _replace,
    )
    from fullstack_agent_042_logic import (
        PARLEY_LOGIC,
        PARLEY_MAIN,
        PYTHON_BROWSER,
        PYTHON_BROWSER_EXPORT,
        PYTHON_LOGIC,
        RUST_LIB,
        RUST_WASM,
        TS_SCHEMA,
        TYPESCRIPT_LOGIC,
    )


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS_PATH = BENCHMARKS / "fullstack_agent_042_tasks.json"
LANGUAGES = ("parley", "python", "typescript", "rust")


def load_task_map() -> dict[str, dict[str, Any]]:
    payload = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    return {task["id"]: task for task in payload["tasks"]}


def _contract(task: dict[str, Any]) -> str:
    request = "\n".join(
        f"- `{name}`: {kind}" for name, kind in task["request_fields"].items()
    )
    response = "\n".join(
        f"- `{name}`: {kind}" for name, kind in task["response_fields"].items()
    )
    return _clean(
        f"""
        # {task['title']}

        {task['statement']}

        ## HTTP

        - `GET {task['status_route']}` returns `{{"service":"{task['service']}","ready":true}}`.
        - `POST {task['post_route']}` accepts strict JSON and returns strict JSON.
        - A number is a nonnegative JSON integer and never a boolean.
        - Unknown, missing, wrongly typed, or out-of-domain fields return
          status 400 with error `invalid_json`.
        - A non-JSON POST returns 415 with error `json_content_type_required`.
        - A body over 16384 bytes returns 413 with error `body_too_large`.

        Request fields:

        {request}

        Response fields:

        {response}

        ## Browser

        Export `{task['browser_export']}` with request fields in the order listed
        above. It returns the same value as response field
        `{task['shared_result_field']}` for equivalent inputs.
        """
    ).replace("        ", "")


PUBLIC_INDEX = _clean(
    """
    <!doctype html>
    <meta charset="utf-8">
    <title>Full-stack agent study 042</title>
    <main>Full-stack agent study 042 browser target</main>
    """
).replace("    ", "")


PYTHON_APP_TEMPLATE = BASE_PYTHON_APP_TEMPLATE.replace(
    '@app.get("/api/status")', '@app.get("@@STATUS_ROUTE@@")'
)

TS_SERVER_TEMPLATE = BASE_TS_SERVER_TEMPLATE.replace(
    'app.get("/api/status"', 'app.get("@@STATUS_ROUTE@@"'
).replace("FULLSTACK_036", "FULLSTACK_042")

RUST_MAIN_TEMPLATE = BASE_RUST_MAIN_TEMPLATE.replace(
    "fullstack_agent_036", "fullstack_agent_042"
).replace("FULLSTACK_036", "FULLSTACK_042").replace(
    'route("/api/status"', 'route("@@STATUS_ROUTE@@"'
).replace(
    "Ok(value) => json_response(handle(value), StatusCode::OK)",
    'Ok(value) if value.valid() => json_response(handle(value), StatusCode::OK), Ok(_) => error("invalid_json", StatusCode::BAD_REQUEST, "numeric value outside contract")',
)


def _parley_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    manifest = {
        "schema_version": 1,
        "name": task["id"],
        "entrypoint": "main.par",
        "static_dir": "public",
        "routes": [
            {"method": "GET", "path": task["status_route"], "handler": "project_status"},
            {"method": "POST", "path": task["post_route"], "handler": "handle_request"},
        ],
        "browser": {
            "entrypoint": "main.par",
            "exports": [{"name": task["browser_export"]}],
        },
        "server": {"host": "127.0.0.1", "port": 8787, "max_body_bytes": 16384},
    }
    return {
        "logic.par": ScaffoldFile(_clean(PARLEY_LOGIC[task["id"]][variant]), True),
        "main.par": ScaffoldFile(_clean(PARLEY_MAIN[task["id"]]), True),
        "parley.web.json": ScaffoldFile(json.dumps(manifest, indent=2) + "\n", True),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _python_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    export_name, js_name = PYTHON_BROWSER_EXPORT[task["id"]]
    browser = _clean(
        PYTHON_BROWSER[task["id"]][variant]
        + f"\nexport async function loadParley() {{ return {{ {export_name}: {js_name} }}; }}"
    )
    app = _replace(
        PYTHON_APP_TEMPLATE,
        service=task["service"],
        route=task["post_route"],
        status_route=task["status_route"],
    )
    return {
        "logic.py": ScaffoldFile(_clean(PYTHON_LOGIC[task["id"]][variant]), True),
        "browser.js": ScaffoldFile(browser, True),
        "app.py": ScaffoldFile(app, True),
        "requirements.txt": ScaffoldFile(
            (BENCHMARKS / "fullstack_035/python/requirements.txt").read_text(), False
        ),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _typescript_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    server = _replace(
        TS_SERVER_TEMPLATE,
        schema=TS_SCHEMA[task["id"]],
        service=task["service"],
        route=task["post_route"],
        status_route=task["status_route"],
    )
    return {
        "src/logic.ts": ScaffoldFile(_clean(TYPESCRIPT_LOGIC[task["id"]][variant]), True),
        "src/server.ts": ScaffoldFile(server, True),
        "package.json": ScaffoldFile(
            (BENCHMARKS / "fullstack_035/typescript/package.json").read_text(), False
        ),
        "package-lock.json": ScaffoldFile(
            (BENCHMARKS / "fullstack_035/typescript/package-lock.json").read_text(), False
        ),
        "tsconfig.json": ScaffoldFile(
            (BENCHMARKS / "fullstack_035/typescript/tsconfig.json").read_text(), False
        ),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def _rust_browser(task: dict[str, Any]) -> str:
    symbol, args = RUST_WASM[task["id"]]
    names = [chr(ord("a") + index) for index in range(len(args))]
    converted = ", ".join(
        f"asI64({value}, '{names[index]}')" if "?" not in value else value
        for index, value in enumerate(args)
    )
    return _clean(
        f"""
const asI64 = (value, name) => {{ if (typeof value === "bigint") return value; if (!Number.isSafeInteger(value)) throw new TypeError(`${{name}} must be a safe whole number`); return BigInt(value); }};
export async function loadParley() {{
  const response = await fetch(new URL("/fullstack_agent_042.wasm", import.meta.url));
  const result = await WebAssembly.instantiateStreaming(response);
  const wasm = result.instance.exports;
  return {{ {task['browser_export']}: ({', '.join(names)}) => wasm.{symbol}({converted}) }};
}}
"""
    )


def _rust_files(task: dict[str, Any], variant: str) -> dict[str, ScaffoldFile]:
    main = _replace(
        RUST_MAIN_TEMPLATE,
        browser=_rust_browser(task).rstrip("\n"),
        service=task["service"],
        route=task["post_route"],
        status_route=task["status_route"],
    )
    return {
        "src/lib.rs": ScaffoldFile(_clean(RUST_LIB[task["id"]][variant]), True),
        "src/main.rs": ScaffoldFile(main, True),
        "Cargo.toml": ScaffoldFile(
            (BENCHMARKS / "fullstack_042/rust/Cargo.toml").read_text(), False
        ),
        "Cargo.lock": ScaffoldFile(
            (BENCHMARKS / "fullstack_042/rust/Cargo.lock").read_text(), False
        ),
        "public/index.html": ScaffoldFile(PUBLIC_INDEX, False),
    }


def scaffold_files(
    task: dict[str, Any], language: str, variant: str = "seed"
) -> dict[str, ScaffoldFile]:
    if language not in LANGUAGES:
        raise ValueError(f"unsupported language: {language}")
    if variant not in {"seed", "reference"}:
        raise ValueError(f"unsupported scaffold variant: {variant}")
    builders = {
        "parley": _parley_files,
        "python": _python_files,
        "typescript": _typescript_files,
        "rust": _rust_files,
    }
    files = builders[language](task, variant)
    files["CONTRACT.md"] = ScaffoldFile(_contract(task), False)
    return files


ROOT_FILES: dict[str, tuple[str, ...]] = {
    "parley": ("logic.par",),
    "python": ("browser.js", "logic.py"),
    "typescript": ("src/logic.ts",),
    "rust": ("src/lib.rs",),
}
