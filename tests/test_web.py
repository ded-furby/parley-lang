import json
from pathlib import Path
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request

import pytest

from conftest import REPO, run_cli
from parley.cli import _safe_bundle_target
from parley.diagnostics import ParleyError
from parley.web import (
    WebProjectError,
    check_browser,
    check_web,
    load_project,
    render_browser,
    render_server,
)


SOURCE = """\
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text
a request_body has name as text, count as number
a response_body has message as text, accepted as yesno

to hello with request as web_request, body as request_body giving response_body:
    give back a response_body with message "hello {body's name}", accepted body's count is more than 0

to health giving response_body:
    give back a response_body with message "ready", accepted yes

to score with passed as number, ready as yesno giving number:
    if ready:
        give back passed plus 10
    give back passed
"""


def write_project(root: Path, *, browser=True) -> Path:
    root.mkdir()
    (root / "main.par").write_text(SOURCE)
    public = root / "public"
    public.mkdir()
    (public / "index.html").write_text("<!doctype html><title>fixture</title>")
    manifest = {
        "schema_version": 1,
        "name": "web-fixture",
        "entrypoint": "main.par",
        "static_dir": "public",
        "routes": [
            {"method": "GET", "path": "/api/health", "handler": "health"},
            {"method": "POST", "path": "/api/hello", "handler": "hello",
             "success_status": 201},
        ],
        "server": {"port": 18787, "max_body_bytes": 4096},
    }
    if browser:
        manifest["browser"] = {"exports": [{"name": "score"}]}
    (root / "parley.web.json").write_text(json.dumps(manifest))
    return root


def test_web_contract_infers_typed_json_and_request_metadata(tmp_path):
    project = load_project(write_project(tmp_path / "app"))
    checked = check_web(project)

    assert [(route.route.method, route.route.path) for route in checked.routes] == [
        ("GET", "/api/health"),
        ("POST", "/api/hello"),
    ]
    assert checked.routes[0].body_param is None
    assert checked.routes[1].has_request is True
    assert str(checked.routes[1].body_param.type) == "request_body"
    assert str(checked.routes[1].function.ret) == "response_body"


def test_server_generation_has_strict_json_and_bounded_http(tmp_path):
    checked = check_web(load_project(write_project(tmp_path / "app")))
    rust, _ = render_server(checked)

    assert "serde::Deserialize" in rust
    assert "#[serde(deny_unknown_fields)]" in rust
    assert 'content_type != "application/json"' in rust
    assert "PARLEY_MAX_HEADER_BYTES" in rust
    assert "PARLEY_MAX_BODY_BYTES: usize = 4096" in rust
    assert '("POST", "/api/hello")' in rust
    assert "std::fs::canonicalize" in rust
    assert '"application/wasm"' in rust


def test_browser_generation_has_stable_scalar_abi_and_bindings(tmp_path):
    project = load_project(write_project(tmp_path / "app"))
    checked = check_browser(project)
    assert checked is not None

    rust, _, javascript, declarations = render_browser(checked)
    assert 'pub extern "C" fn parley_score(arg0: i64, arg1: i32) -> i64' in rust
    assert "asI64(passed" in javascript
    assert "wasm.parley_score" in javascript
    assert "score(passed: number | bigint, ready: boolean): bigint" in declarations


def test_manifest_paths_cannot_escape_project(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    outside = tmp_path / "outside.par"
    outside.write_text("to main:\n    say 1\n")
    (root / "parley.web.json").write_text(json.dumps({
        "schema_version": 1,
        "name": "escape",
        "entrypoint": "../outside.par",
        "routes": [{"method": "GET", "path": "/", "handler": "main"}],
    }))

    with pytest.raises(WebProjectError, match="inside the project"):
        load_project(root)


def test_bundle_target_cannot_replace_a_project_parent(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    root = write_project(workspace / "app", browser=False)
    project = load_project(root)

    with pytest.raises(WebProjectError, match="dedicated directory"):
        _safe_bundle_target(project, str(workspace))


def test_route_to_missing_handler_is_actionable(tmp_path):
    root = write_project(tmp_path / "app", browser=False)
    manifest = json.loads((root / "parley.web.json").read_text())
    manifest["routes"][0]["handler"] = "missing"
    (root / "parley.web.json").write_text(json.dumps(manifest))

    with pytest.raises(ParleyError) as caught:
        check_web(load_project(root))
    assert caught.value.diagnostics[0].code == "P710"
    assert "missing function" in caught.value.diagnostics[0].message


def test_browser_export_rejects_platform_io(tmp_path):
    root = write_project(tmp_path / "app")
    with (root / "main.par").open("a") as source:
        source.write("""
to unsafe_score with path as number giving number:
    say path
    give back path
""")
    manifest = json.loads((root / "parley.web.json").read_text())
    manifest["browser"]["exports"] = [{"name": "unsafe_score"}]
    (root / "parley.web.json").write_text(json.dumps(manifest))

    with pytest.raises(ParleyError) as caught:
        check_browser(load_project(root))
    assert caught.value.diagnostics[0].code == "P723"
    assert "prints output" in caught.value.diagnostics[0].message


def test_release_radar_contract_is_checked():
    proc = run_cli(
        ["web", "check", str(REPO / "examples" / "release-radar"), "--json"],
        cwd=REPO,
    )
    assert proc.returncode == 0, proc.stderr
    contract = json.loads(proc.stdout)
    assert contract["ok"] is True
    assert len(contract["routes"]) == 2
    assert contract["routes"][1]["json_body"] == "release_input"
    assert contract["browser_exports"][0]["name"] == "readiness_score"


@pytest.mark.skipif(shutil.which("cargo") is None, reason="cargo not installed")
def test_native_web_bundle_serves_static_and_strict_typed_json(tmp_path):
    project = write_project(tmp_path / "app", browser=False)
    bundle = tmp_path / "bundle"
    build = run_cli(["web", "build", str(project), "-o", str(bundle)], cwd=REPO)
    assert build.returncode == 0, build.stderr
    assert (bundle / "server").is_file()
    assert (bundle / "public" / "index.html").is_file()

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = dict(**__import__("os").environ, PARLEY_WEB_PORT=str(port))
    server = subprocess.Popen(
        [str(bundle / "server")], cwd=bundle, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health") as response:
                    assert json.loads(response.read()) == {"message": "ready", "accepted": True}
                break
            except (OSError, urllib.error.URLError):
                time.sleep(0.05)
        else:
            pytest.fail("web server did not start")

        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/hello",
            data=json.dumps({"name": "Ada", "count": 2}).encode(),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            assert response.status == 201
            assert json.loads(response.read()) == {"message": "hello Ada", "accepted": True}

        unknown = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/hello",
            data=json.dumps({"name": "Ada", "count": 2, "typo": True}).encode(),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(unknown)
        assert caught.value.code == 400
        assert json.loads(caught.value.read())["error"] == "invalid_json"

        wrong_type = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/hello",
            data=b'{"name":"Ada","count":2}',
            headers={"content-type": "text/plain"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(wrong_type)
        assert caught.value.code == 415

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as response:
            assert response.headers["content-type"].startswith("text/html")
            assert b"fixture" in response.read()
    finally:
        server.terminate()
        server.wait(timeout=10)
