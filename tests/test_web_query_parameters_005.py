import hashlib
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import time

import pytest

from conftest import run_cli
from parley import __version__
from parley.diagnostics import ParleyError
from parley.web import check_web, load_project


REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "benchmarks/WEB_QUERY_PARAMETERS_005.md"
BASELINE_COMMIT = "7d21f51d35cb271c15873a0c417a1bfe89c9eefd"
BASELINE_TREE = "13206bc2194d8f1de64aca3c3831c09fc28bd09b"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_web_query_parameters_005_preserves_preimplementation_freeze():
    assert tuple(map(int, __version__.split("."))) >= (0, 5, 8)
    assert git("show", "-s", "--format=%T", BASELINE_COMMIT) == BASELINE_TREE
    baseline = git("show", f"{BASELINE_COMMIT}:parley/web.py")
    assert "query_parameters" not in baseline
    assert "query_parameters" in (REPO / "parley/web.py").read_text()


def test_web_query_parameters_005_freezes_complete_gate():
    protocol = PROTOCOL.read_text(encoding="utf-8")
    normalized = " ".join(protocol.lower().split())
    for boundary in (
        "seven-field",
        "map from text to list of text",
        "Percent-decode names and values exactly once as UTF-8",
        "Repeated names append values in arrival order",
        "invalid_query_parameter",
        "More than 128 non-empty query pairs",
        "invalid path captures win before query errors",
        "complete repository suite before and after version advance",
        "universal language superiority",
    ):
        assert boundary.lower() in normalized


def test_web_query_parameters_005_protocol_hash_is_frozen():
    assert hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() == (
        "8c4d96512af3759d635d410b4b7372e268e80af5d90a94a00b895c6c9c1a64c3"
    )


LEGACY_REQUEST = """\
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text
"""

PATH_REQUEST = """\
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text, path_parameters as map from text to text
"""

QUERY_REQUEST = """\
a web_request has method as text, path as text, query as text, headers as map from text to text, body as text, path_parameters as map from text to text, query_parameters as map from text to list of text
"""

QUERY_SOURCE = QUERY_REQUEST + """\
a query_result has route as text, raw as text, paths as map from text to text, values as map from text to list of text, label as text
a query_body has label as text

to inspect with request as web_request giving query_result:
    give back a query_result with route "exact", raw request's query, paths request's path_parameters, values request's query_parameters, label ""

to inspect_item with request as web_request giving query_result:
    give back a query_result with route "item", raw request's query, paths request's path_parameters, values request's query_parameters, label ""

to update_item with request as web_request, body as query_body giving query_result:
    give back a query_result with route "post", raw request's query, paths request's path_parameters, values request's query_parameters, label body's label
"""


def simple_source(request_record: str) -> str:
    return request_record + """\
a query_result has raw as text
to inspect with request as web_request giving query_result:
    give back a query_result with raw request's query
"""


def write_project(root: Path, source: str, routes: list[dict]) -> Path:
    root.mkdir()
    (root / "main.par").write_text(source)
    public = root / "public"
    public.mkdir()
    (public / "index.html").write_text("<!doctype html><title>query</title>")
    (root / "parley.web.json").write_text(json.dumps({
        "schema_version": 1,
        "name": "query-fixture",
        "entrypoint": "main.par",
        "static_dir": "public",
        "routes": routes,
        "server": {"port": 19202, "max_body_bytes": 4096},
    }))
    return root


def route(path: str, handler: str = "inspect", method: str = "GET") -> dict:
    return {"method": method, "path": path, "handler": handler}


def test_checker_accepts_three_shapes_and_rejects_query_shortcuts(tmp_path):
    assert check_web(load_project(write_project(
        tmp_path / "legacy", simple_source(LEGACY_REQUEST), [route("/inspect")]
    )))
    assert check_web(load_project(write_project(
        tmp_path / "path", simple_source(PATH_REQUEST), [route("/inspect/{item}")]
    )))
    checked = check_web(load_project(write_project(
        tmp_path / "query", QUERY_SOURCE, [
            route("/inspect"), route("/items/{item}", "inspect_item")
        ]
    )))
    assert [item.has_query_parameters for item in checked.routes] == [True, True]

    wrong_shapes = [
        QUERY_REQUEST.replace(
            "path_parameters as map from text to text, query_parameters",
            "query_parameters as map from text to list of text, path_parameters",
        ),
        QUERY_REQUEST.replace("list of text", "text", 1),
        LEGACY_REQUEST.rstrip() + ", query_parameters as map from text to list of text\n",
    ]
    for index, request_record in enumerate(wrong_shapes):
        project = write_project(
            tmp_path / f"wrong-{index}", simple_source(request_record), [route("/inspect")]
        )
        with pytest.raises(ParleyError) as caught:
            check_web(load_project(project))
        assert caught.value.diagnostics[0].code == "P714"


def test_contract_and_bundle_report_query_metadata(tmp_path):
    project = write_project(tmp_path / "app", QUERY_SOURCE, [
        route("/inspect"),
        route("/items/{item}", "inspect_item"),
    ])
    checked = run_cli(["web", "check", str(project), "--json"], cwd=tmp_path)
    assert checked.returncode == 0, checked.stderr
    routes = json.loads(checked.stdout)["routes"]
    assert [item["path_parameters"] for item in routes] == [[], ["item"]]
    assert [item["query_parameters"] for item in routes] == [True, True]

    bundle = tmp_path / "bundle"
    built = run_cli(["web", "build", str(project), "-o", str(bundle)], cwd=tmp_path)
    assert built.returncode == 0, built.stderr
    metadata = json.loads((bundle / "parley.build.json").read_text())
    assert [item["query_parameters"] for item in metadata["routes"]] == [True, True]

    explained = run_cli(["explain", "P714"], cwd=tmp_path)
    assert explained.returncode == 0
    assert "query_parameters" in explained.stdout


def request(
    port: int, method: str, path: str, body: bytes | None = None
) -> tuple[int, dict[str, str], bytes]:
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
            if request(port, "GET", "/")[0] == 200:
                return
        except OSError:
            time.sleep(0.05)
    pytest.fail("web server did not start")


def start_server(bundle: Path) -> tuple[subprocess.Popen, int]:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = subprocess.Popen(
        [str(bundle / "server")],
        cwd=bundle,
        env={**os.environ, "PARLEY_WEB_PORT": str(port)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    wait_for_server(port)
    return server, port


def test_native_query_decoding_repetition_bounds_and_precedence(tmp_path):
    project = write_project(tmp_path / "app", QUERY_SOURCE, [
        route("/inspect"),
        route("/items/{item}", "inspect_item"),
        route("/items/{item}", "update_item", "POST"),
    ])
    bundle = tmp_path / "bundle"
    built = run_cli(["web", "build", str(project), "-o", str(bundle)], cwd=tmp_path)
    assert built.returncode == 0, built.stderr
    server, port = start_server(bundle)
    try:
        for target, expected in (
            ("/inspect", {}),
            ("/inspect?", {}),
            ("/inspect?flag&blank=&flag=two", {"blank": [""], "flag": ["", "two"]}),
            ("/inspect?term=red+fox&plus=%2B", {"plus": ["+"], "term": ["red fox"]}),
            ("/inspect?caf%C3%A9=na%C3%AFve", {"café": ["naïve"]}),
            ("/inspect?token=a%26b%3Dc&&", {"token": ["a&b=c"]}),
        ):
            status, _, payload = request(port, "GET", target)
            assert status == 200, target
            decoded = json.loads(payload)
            assert decoded["values"] == expected
            assert decoded["raw"] == target.partition("?")[2]

        status, _, payload = request(port, "GET", "/items/A%20B?q=1&q=2")
        assert status == 200
        decoded = json.loads(payload)
        assert decoded["paths"] == {"item": "A B"}
        assert decoded["values"] == {"q": ["1", "2"]}

        status, headers, payload = request(port, "HEAD", "/inspect?q=1")
        assert status == 200 and payload == b""
        assert int(headers["Content-Length"]) > 0

        status, _, payload = request(
            port, "POST", "/items/7?mode=strict", b'{"label":"ready"}'
        )
        assert status == 200
        assert json.loads(payload)["label"] == "ready"

        for query in ("=value", "%", "%2", "%GG", "%FF", "x=%00", "x=%1F", "x=%7F"):
            status, _, payload = request(port, "GET", f"/inspect?{query}")
            assert status == 400, query
            assert json.loads(payload)["error"] == "invalid_query_parameter"

        too_many = "&".join(f"x={index}" for index in range(129))
        status, _, payload = request(port, "GET", f"/inspect?{too_many}")
        assert status == 400
        assert json.loads(payload)["error"] == "invalid_query_parameter"

        status, _, payload = request(port, "GET", "/items/%GG?%GG=x")
        assert status == 400
        assert json.loads(payload)["error"] == "invalid_path_parameter"

        status, _, payload = request(port, "POST", "/items/7?%GG=x", b'{')
        assert status == 400
        assert json.loads(payload)["error"] == "invalid_query_parameter"

        status, _, payload = request(port, "POST", "/items/7?q=ok", b'{')
        assert status == 400
        assert json.loads(payload)["error"] == "invalid_json"
    finally:
        server.terminate()
        server.wait(timeout=10)


@pytest.mark.parametrize("request_record", [LEGACY_REQUEST, PATH_REQUEST])
def test_older_request_shapes_preserve_raw_invalid_query(tmp_path, request_record):
    project = write_project(
        tmp_path / "app", simple_source(request_record), [route("/inspect")]
    )
    bundle = tmp_path / "bundle"
    built = run_cli(["web", "build", str(project), "-o", str(bundle)], cwd=tmp_path)
    assert built.returncode == 0, built.stderr
    server, port = start_server(bundle)
    try:
        status, _, payload = request(port, "GET", "/inspect?%GG=x")
        assert status == 200
        assert json.loads(payload) == {"raw": "%GG=x"}
    finally:
        server.terminate()
        server.wait(timeout=10)


def test_query_parameters_compose_with_dynamic_response_and_explicit_json(tmp_path):
    source = QUERY_REQUEST + """\
a response_body has values as map from text to list of text
a response_control has status as number, headers as map from text to text, body as response_body

to inspect with request as web_request giving response_control:
    let headers be a map from text to text
    set item "x-query-state" of headers to "decoded"
    let body be a response_body with values request's query_parameters
    give back a response_control with status 202, headers headers, body body

to encode_body with body as response_body giving text:
    give back body as json
"""
    dynamic = route("/inspect")
    dynamic["response"] = {
        "status_field": "status",
        "headers_field": "headers",
        "body_field": "body",
    }
    project = write_project(tmp_path / "app", source, [dynamic])
    bundle = tmp_path / "bundle"
    built = run_cli(["web", "build", str(project), "-o", str(bundle)], cwd=tmp_path)
    assert built.returncode == 0, built.stderr
    server, port = start_server(bundle)
    try:
        status, headers, payload = request(port, "GET", "/inspect?q=one&q=two")
        assert status == 202
        assert headers["x-query-state"] == "decoded"
        assert json.loads(payload) == {"values": {"q": ["one", "two"]}}
    finally:
        server.terminate()
        server.wait(timeout=10)
