import hashlib
import http.client
import json
import socket
from pathlib import Path
import subprocess
import time

import pytest

from conftest import run_cli
from parley import __version__
from parley.diagnostics import ParleyError
from parley.web import WebProjectError, check_web, load_project, render_server


REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "benchmarks/WEB_PATH_PARAMETERS_004.md"
BASELINE_COMMIT = "bed8fde8f9e0c2f603d2f6a764619c676d123f2a"
BASELINE_TREE = "6e3b0c94227d25d3a4c47e5015270a4a4de52d75"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_web_path_parameters_004_preserves_preimplementation_freeze():
    assert tuple(map(int, __version__.split("."))) >= (0, 5, 7)
    assert git("show", "-s", "--format=%T", BASELINE_COMMIT) == BASELINE_TREE
    assert "path_parameters" not in git("show", f"{BASELINE_COMMIT}:parley/web.py")
    assert "P725" not in git("show", f"{BASELINE_COMMIT}:parley/diagnostics.py")
    assert "path_parameters" in (REPO / "parley/web.py").read_text()
    assert "P725" in (REPO / "parley/diagnostics.py").read_text()


def test_web_path_parameters_004_freezes_complete_gate():
    protocol = PROTOCOL.read_text(encoding="utf-8")
    for boundary in (
        "Exact routes take priority",
        "Two templates for the same method are rejected",
        "sixth and final field",
        "stable diagnostic P725",
        "percent-decoded exactly once as UTF-8",
        "invalid_path_parameter",
        "without invoking handler logic",
        "historical frozen references remain byte-for-byte unchanged",
        "universal language superiority",
    ):
        assert boundary in protocol
    assert len(protocol.split("## Preregistered verification gate", 1)[1].splitlines()) > 20


def test_web_path_parameters_004_protocol_hash_is_frozen():
    assert hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() == (
        "d27d2f3ab39dd4ec3578f362ee7a3d4cf347526cc5039d7ac0159f29b398a531"
    )


EXTENDED_REQUEST = """\
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text, path_parameters as map from text to text
"""


PATH_SOURCE = EXTENDED_REQUEST + """\
a path_result has route as text, first as text, second as text, raw_path as text, raw_query as text
a post_input has label as text

to exact_item with request as web_request giving path_result:
    let captured be (maybe item "item_id" of request's path_parameters) otherwise "empty"
    give back a path_result with route "exact", first captured, second "", raw_path request's path, raw_query request's query

to show_item with request as web_request giving path_result:
    let item_id be (maybe item "item_id" of request's path_parameters) otherwise ""
    give back a path_result with route "item", first item_id, second "", raw_path request's path, raw_query request's query

to post_item with request as web_request, body as post_input giving path_result:
    let item_id be (maybe item "item_id" of request's path_parameters) otherwise ""
    give back a path_result with route "post", first item_id, second body's label, raw_path request's path, raw_query request's query

to team_item with request as web_request giving path_result:
    let team be (maybe item "team" of request's path_parameters) otherwise ""
    let item_id be (maybe item "item_id" of request's path_parameters) otherwise ""
    give back a path_result with route "team", first team, second item_id, raw_path request's path, raw_query request's query
"""

LEGACY_SOURCE = """\
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text
a path_result has route as text, first as text, second as text, raw_path as text, raw_query as text

to show_item with request as web_request giving path_result:
    give back a path_result with route "legacy", first "", second "", raw_path request's path, raw_query request's query
"""


def write_project(root: Path, source: str, routes: list[dict]) -> Path:
    root.mkdir()
    (root / "main.par").write_text(source)
    public = root / "public"
    public.mkdir()
    (public / "index.html").write_text("<!doctype html><title>paths</title>")
    (root / "parley.web.json").write_text(json.dumps({
        "schema_version": 1,
        "name": "path-fixture",
        "entrypoint": "main.par",
        "static_dir": "public",
        "routes": routes,
        "server": {"port": 19201, "max_body_bytes": 4096},
    }))
    return root


def route(path: str, handler: str = "show_item", method: str = "GET") -> dict:
    return {"method": method, "path": path, "handler": handler}


@pytest.mark.parametrize("bad_path,fragment", [
    ("/api/{}", "Parley field name"),
    ("/api/x{item}", "complete path segment"),
    ("/api/{item}tail", "complete path segment"),
    ("/api/{item}/{item}", "repeats path capture"),
    ("/api//{item}", "empty segments"),
    ("/api/{item}/", "empty segments"),
    ("/api/{bad-name}", "Parley field name"),
    ("/api/{item", "complete path segment"),
])
def test_manifest_rejects_invalid_path_templates(tmp_path, bad_path, fragment):
    project = write_project(tmp_path / "app", PATH_SOURCE, [route(bad_path)])
    with pytest.raises(WebProjectError, match=fragment):
        load_project(project)


def test_manifest_allows_exact_priority_and_method_specific_templates(tmp_path):
    project = write_project(tmp_path / "app", PATH_SOURCE, [
        route("/api/items/{item_id}"),
        route("/api/items/current", "exact_item"),
        route("/api/items/{item_id}", "post_item", "POST"),
        route("/api/teams/{team}/items/{item_id}", "team_item"),
    ])
    loaded = load_project(project)
    assert [item.path_parameters for item in loaded.routes] == [
        ("item_id",), (), ("item_id",), ("team", "item_id"),
    ]


@pytest.mark.parametrize("left,right", [
    ("/api/{item}", "/api/{other}"),
    ("/api/{left}/status", "/api/current/{right}"),
    ("/api/{left}/{right}", "/api/current/{value}"),
])
def test_manifest_rejects_overlapping_templates(tmp_path, left, right):
    project = write_project(
        tmp_path / "app", PATH_SOURCE, [route(left), route(right, "team_item")]
    )
    with pytest.raises(WebProjectError, match="route templates .* overlap"):
        load_project(project)


def test_manifest_keeps_duplicate_exact_route_rejection(tmp_path):
    project = write_project(tmp_path / "app", PATH_SOURCE, [
        route("/api/items/current", "exact_item"),
        route("/api/items/current", "exact_item"),
    ])
    with pytest.raises(WebProjectError, match="declared twice"):
        load_project(project)


def test_parameterized_route_requires_extended_web_request(tmp_path):
    without_request = """\
a path_result has value as text
to show_item giving path_result:
    give back a path_result with value "missing"
"""
    project = write_project(
        tmp_path / "none", without_request, [route("/api/items/{item_id}")]
    )
    with pytest.raises(ParleyError) as caught:
        check_web(load_project(project))
    assert caught.value.diagnostics[0].code == "P725"

    project = write_project(
        tmp_path / "legacy", LEGACY_SOURCE, [route("/api/items/{item_id}")]
    )
    with pytest.raises(ParleyError) as caught:
        check_web(load_project(project))
    assert caught.value.diagnostics[0].code == "P725"


def test_exact_routes_accept_legacy_extended_and_reject_other_shapes(tmp_path):
    assert check_web(load_project(write_project(
        tmp_path / "legacy", LEGACY_SOURCE, [route("/exact")]
    )))
    assert check_web(load_project(write_project(
        tmp_path / "extended", PATH_SOURCE, [route("/exact")]
    )))
    wrong = PATH_SOURCE.replace(
        "body as text, path_parameters as map from text to text",
        "path_parameters as map from text to text, body as text",
    )
    with pytest.raises(ParleyError) as caught:
        check_web(load_project(write_project(
            tmp_path / "wrong", wrong, [route("/exact")]
        )))
    assert caught.value.diagnostics[0].code == "P714"


def test_generated_contract_reports_ordered_path_parameters(tmp_path):
    project = write_project(tmp_path / "app", PATH_SOURCE, [
        route("/exact"),
        route("/api/teams/{team}/items/{item_id}", "team_item"),
    ])
    checked = check_web(load_project(project))
    rust, _ = render_server(checked)
    assert 'parley_match_path("/api/teams/{team}/items/{item_id}"' in rust
    assert rust.index('request.path == "/exact"') < rust.index("match parley_match_path")

    contract = run_cli(["web", "check", str(project), "--json"], cwd=tmp_path)
    assert contract.returncode == 0, contract.stderr
    assert [item["path_parameters"] for item in json.loads(contract.stdout)["routes"]] == [
        [], ["team", "item_id"],
    ]
    explained = run_cli(["explain", "P725"], cwd=tmp_path)
    assert explained.returncode == 0
    assert "path_parameters" in explained.stdout


def request(port: int, method: str, path: str, body: bytes | None = None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"content-type": "application/json"} if body is not None else {}
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    payload = response.read()
    result = response.status, dict(response.getheaders()), payload
    connection.close()
    return result


def wait_for_server(port: int) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            status, _, _ = request(port, "GET", "/")
            if status == 200:
                return
        except OSError:
            time.sleep(0.05)
    pytest.fail("web server did not start")


def test_native_parameter_routing_decoding_safety_and_metadata(tmp_path):
    project = write_project(tmp_path / "app", PATH_SOURCE, [
        route("/api/items/{item_id}"),
        route("/api/items/current", "exact_item"),
        route("/api/items/{item_id}", "post_item", "POST"),
        route("/api/teams/{team}/items/{item_id}", "team_item"),
    ])
    bundle = tmp_path / "bundle"
    built = run_cli(["web", "build", str(project), "-o", str(bundle)], cwd=tmp_path)
    assert built.returncode == 0, built.stderr
    metadata = json.loads((bundle / "parley.build.json").read_text())
    assert [item["path_parameters"] for item in metadata["routes"]] == [
        ["item_id"], [], ["item_id"], ["team", "item_id"],
    ]

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = subprocess.Popen(
        [str(bundle / "server")],
        cwd=bundle,
        env={**__import__("os").environ, "PARLEY_WEB_PORT": str(port)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        wait_for_server(port)
        status, headers, payload = request(
            port, "GET", "/api/items/current?view=raw"
        )
        assert status == 200
        assert json.loads(payload) == {
            "route": "exact", "first": "empty", "second": "",
            "raw_path": "/api/items/current", "raw_query": "view=raw",
        }

        status, _, payload = request(port, "GET", "/api/items/%63urrent")
        assert status == 200
        assert json.loads(payload)["route"] == "item"
        assert json.loads(payload)["first"] == "current"

        status, _, payload = request(
            port, "GET", "/api/items/caf%C3%A9?view=full"
        )
        assert status == 200
        assert json.loads(payload) == {
            "route": "item", "first": "café", "second": "",
            "raw_path": "/api/items/caf%C3%A9", "raw_query": "view=full",
        }

        status, _, payload = request(
            port, "GET", "/api/teams/red/items/A%20B"
        )
        assert status == 200
        decoded = json.loads(payload)
        assert (decoded["first"], decoded["second"]) == ("red", "A B")

        status, _, payload = request(
            port, "POST", "/api/items/order-7", b'{"label":"fragile"}'
        )
        assert status == 200
        decoded = json.loads(payload)
        assert (decoded["route"], decoded["first"], decoded["second"]) == (
            "post", "order-7", "fragile",
        )

        status, _, payload = request(port, "POST", "/api/items/order-7", b'{')
        assert status == 400
        assert json.loads(payload)["error"] == "invalid_json"
        status, _, _ = request(port, "GET", "/api/items/a/more")
        assert status == 404

        status, headers, payload = request(port, "HEAD", "/api/items/head-value")
        assert status == 200
        assert payload == b""
        assert int(headers["Content-Length"]) > 0

        for value in ("%", "%2", "%GG", "%FF", "%2F", "%5C", "%00", "%1F", "%7F", "raw\\slash"):
            status, _, payload = request(port, "GET", f"/api/items/{value}")
            assert status == 400, value
            assert json.loads(payload)["error"] == "invalid_path_parameter"

        status, _, payload = request(port, "POST", "/api/items/%GG", b'{')
        assert status == 400
        assert json.loads(payload)["error"] == "invalid_path_parameter"
    finally:
        server.terminate()
        server.wait(timeout=10)


def test_parameterized_response_control_works_with_explicit_json_backend(tmp_path):
    source = EXTENDED_REQUEST + """\
a item_body has item_id as text, state as text
a item_reply has status as number, headers as map from text to text, body as item_body

to show_item with request as web_request giving item_reply:
    let item_id be (maybe item "item_id" of request's path_parameters) otherwise ""
    let headers be a map from text to text
    set item "x-item-id" of headers to item_id
    give back an item_reply with status 202, headers headers, body (an item_body with item_id item_id, state "queued")

to encode_item with body as item_body giving text:
    give back body as json
"""
    dynamic = route("/api/items/{item_id}")
    dynamic["response"] = {
        "status_field": "status",
        "headers_field": "headers",
        "body_field": "body",
    }
    project = write_project(tmp_path / "app", source, [dynamic])
    bundle = tmp_path / "bundle"
    built = run_cli(["web", "build", str(project), "-o", str(bundle)], cwd=tmp_path)
    assert built.returncode == 0, built.stderr

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = subprocess.Popen(
        [str(bundle / "server")],
        cwd=bundle,
        env={**__import__("os").environ, "PARLEY_WEB_PORT": str(port)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                status, headers, payload = request(
                    port, "GET", "/api/items/queue%2042"
                )
                break
            except OSError:
                time.sleep(0.05)
        else:
            pytest.fail("web server did not start")
        assert status == 202
        assert headers["x-item-id"] == "queue 42"
        assert json.loads(payload) == {"item_id": "queue 42", "state": "queued"}
    finally:
        server.terminate()
        server.wait(timeout=10)
