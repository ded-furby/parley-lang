import http.client
import json
from pathlib import Path
import shutil
import socket
import subprocess
import time

import pytest

from conftest import REPO, run_cli
from parley.diagnostics import ParleyError
from parley.web import WebProjectError, check_web, load_project, render_server


CONTROL_SOURCE = '''\
include "std/text"

a web_request has method as text, path as text, query as text, headers as map from text to text, body as text
a item_input has name as text, count as number
a response_body has message as text, accepted as yesno
a controlled_response has status as number, headers as map from text to text, body as response_body

to secure with request as web_request giving controlled_response:
    let headers be a map from text to text
    let authorization be (maybe item "authorization" of request's headers) otherwise ""
    if authorization is "Bearer parley":
        set item "x-auth-state" of headers to "accepted"
        set item "x-seen-method" of headers to request's method
        give back a controlled_response with status 200, headers headers, body (a response_body with message "welcome", accepted yes)
    set item "www-authenticate" of headers to "Bearer"
    set item "x-auth-state" of headers to "denied"
    set item "x-seen-method" of headers to request's method
    give back a controlled_response with status 401, headers headers, body (a response_body with message "unauthorized", accepted no)

to create with body as item_input giving controlled_response:
    let headers be a map from text to text
    if body's count is at most 0:
        set item "x-validation" of headers to "count"
        give back a controlled_response with status 422, headers headers, body (a response_body with message "count must be positive", accepted no)
    set item "location" of headers to "/api/items/{body's name}"
    give back a controlled_response with status 201, headers headers, body (a response_body with message body's name, accepted yes)

to unsafe_response with body as item_input giving controlled_response:
    let headers be a map from text to text
    if body's name is "status-low":
        give back a controlled_response with status 199, headers headers, body (a response_body with message "hidden", accepted no)
    if body's name is "status-high":
        give back a controlled_response with status 600, headers headers, body (a response_body with message "hidden", accepted no)
    if body's name is "reserved":
        set item "Content-Length" of headers to "1"
    otherwise if body's name is "control":
        set item "x-bad" of headers to "line\\nbreak"
    otherwise if body's name is "invalid-name":
        set item "bad name" of headers to "value"
    otherwise if body's name is "duplicate":
        set item "X-Dupe" of headers to "one"
        set item "x-dupe" of headers to "two"
    otherwise if body's name is "many":
        let index be 1
        repeat 101 times:
            set item "x-many-{index}" of headers to "value"
            set index to index plus 1
    otherwise if body's name is "large":
        set item "x-large" of headers to (repeated_text with "a", 32768)
    give back a controlled_response with status body's count, headers headers, body (a response_body with message "hidden", accepted yes)
'''


def write_control_project(root: Path) -> Path:
    root.mkdir()
    (root / "main.par").write_text(CONTROL_SOURCE)
    (root / "parley.web.json").write_text(json.dumps({
        "schema_version": 1,
        "name": "response-control",
        "entrypoint": "main.par",
        "routes": [
            {
                "method": "GET", "path": "/api/secure", "handler": "secure",
                "response": {
                    "status_field": "status", "headers_field": "headers",
                    "body_field": "body",
                },
            },
            {
                "method": "POST", "path": "/api/items", "handler": "create",
                "response": {
                    "status_field": "status", "headers_field": "headers",
                    "body_field": "body",
                },
            },
            {
                "method": "POST", "path": "/api/unsafe", "handler": "unsafe_response",
                "response": {
                    "status_field": "status", "headers_field": "headers",
                    "body_field": "body",
                },
            },
        ],
        "server": {"port": 18789, "max_body_bytes": 4096},
    }))
    return root


def request(port: int, method: str, path: str, *, payload=None, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    body = None if payload is None else json.dumps(payload).encode()
    request_headers = {} if headers is None else dict(headers)
    if body is not None:
        request_headers.setdefault("content-type", "application/json")
    connection.request(method, path, body=body, headers=request_headers)
    response = connection.getresponse()
    result = (response.status,
              {name.lower(): value for name, value in response.getheaders()},
              response.read())
    connection.close()
    return result


def test_response_control_manifest_and_checker_contract(tmp_path):
    project = write_control_project(tmp_path / "app")
    checked = check_web(load_project(project))
    control = checked.routes[0].route.response
    assert control is not None
    assert (control.status_field, control.headers_field, control.body_field) == (
        "status", "headers", "body")

    rust, _ = render_server(checked)
    assert "parley_dynamic_json_response(result.status, result.headers, body)" in rust
    assert "parley_web_json_runtime::encode(&result.body)" in rust
    assert "PARLEY_MAX_RESPONSE_HEADERS: usize = 100" in rust
    assert "serde_json::to_vec" not in rust

    manifest_path = project / "parley.web.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["routes"][0]["success_status"] = 200
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(WebProjectError, match="cannot combine response with success_status"):
        load_project(project)


def test_response_control_accepts_custom_field_names(tmp_path):
    project = write_control_project(tmp_path / "app")
    (project / "main.par").write_text('''\
a payload has message as text
a custom_envelope has _code as number, metadata as map from text to text, result as payload

to secure giving custom_envelope:
    let metadata be a map from text to text
    set item "x-result" of metadata to "custom"
    give back a custom_envelope with _code 202, metadata metadata, result (a payload with message "ok")
''')
    manifest_path = project / "parley.web.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["routes"] = [{
        "method": "GET", "path": "/api/secure", "handler": "secure",
        "response": {
            "status_field": "_code", "headers_field": "metadata",
            "body_field": "result",
        },
    }]
    manifest_path.write_text(json.dumps(manifest))
    checked = check_web(load_project(project))
    rust, _ = render_server(checked)
    assert "parley_dynamic_json_response(result._code, result.metadata, body)" in rust
    assert "parley_web_json_runtime::encode(&result.result)" in rust


@pytest.mark.parametrize(
    ("response", "message"),
    [
        ([], "response must be a JSON object"),
        ({"status_field": "status"}, "must contain exactly"),
        (
            {"status_field": "bad field", "headers_field": "headers", "body_field": "body"},
            "is not a Parley field name",
        ),
        (
            {"status_field": "value", "headers_field": "value", "body_field": "body"},
            "field names must be distinct",
        ),
    ],
)
def test_response_control_manifest_rejects_ambiguous_shapes(tmp_path, response, message):
    project = write_control_project(tmp_path / "app")
    manifest_path = project / "parley.web.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["routes"][0]["response"] = response
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(WebProjectError, match=message):
        load_project(project)


@pytest.mark.parametrize(
    ("record", "constructor", "code"),
    [
        (None, '"wrong"', "P716"),
        (
            "a controlled_response has status as number, headers as map from text to text, payload as response_body",
            'a controlled_response with status 200, headers headers, payload (a response_body with message "ok", accepted yes)',
            "P717",
        ),
        (
            "a controlled_response has status as text, headers as map from text to text, body as response_body",
            'a controlled_response with status "200", headers headers, body (a response_body with message "ok", accepted yes)',
            "P718",
        ),
        (
            "a controlled_response has status as number, headers as map from text to number, body as response_body",
            'a controlled_response with status 200, headers headers, body (a response_body with message "ok", accepted yes)',
            "P719",
        ),
    ],
)
def test_response_control_checker_rejects_wrong_envelopes(
        tmp_path, record, constructor, code):
    project = write_control_project(tmp_path / "app")
    source_path = project / "main.par"
    if record is None:
        source = 'to secure giving text:\n    give back "wrong"\n'
    else:
        header_value = "number" if "text to number" in record else "text"
        source = (
            'a response_body has message as text, accepted as yesno\n'
            f'{record}\n\n'
            'to secure giving controlled_response:\n'
            f'    let headers be a map from text to {header_value}\n'
            f'    give back {constructor}\n'
        )
    source_path.write_text(source)
    manifest_path = project / "parley.web.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["routes"] = [manifest["routes"][0]]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ParleyError) as caught:
        check_web(load_project(project))
    assert caught.value.diagnostics[0].code == code


def test_response_control_checker_rejects_non_json_body(tmp_path):
    project = write_control_project(tmp_path / "app")
    (project / "main.par").write_text('''\
a controlled_response has status as number, headers as map from text to text, body as map from number to text

to secure giving controlled_response:
    let headers be a map from text to text
    let body be a map from number to text
    give back a controlled_response with status 200, headers headers, body body
''')
    manifest_path = project / "parley.web.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["routes"] = [manifest["routes"][0]]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ParleyError) as caught:
        check_web(load_project(project))
    assert caught.value.diagnostics[0].code == "P719"
    assert "response body is not JSON-safe" in caught.value.diagnostics[0].message


def test_response_control_check_json_and_explicit_json_backend(tmp_path):
    project = write_control_project(tmp_path / "app")
    with (project / "main.par").open("a") as source:
        source.write('''\

to encode_item with value as item_input giving text:
    give back value as json
''')
    checked = check_web(load_project(project))
    rust, _ = render_server(checked)
    assert "serde_json::to_vec(&result.body)" in rust
    assert "serde::Serialize, serde::Deserialize" in rust

    check = run_cli(["web", "check", str(project), "--json"], cwd=REPO)
    assert check.returncode == 0, check.stderr
    contract = json.loads(check.stdout)
    assert contract["routes"][0]["response"] == {
        "mode": "dynamic", "status_field": "status",
        "headers_field": "headers", "body_field": "body",
    }


@pytest.mark.skipif(shutil.which("cargo") is None, reason="cargo not installed")
def test_response_control_explicit_json_backend_builds(tmp_path):
    project = write_control_project(tmp_path / "app")
    with (project / "main.par").open("a") as source:
        source.write('''\

to encode_item with value as item_input giving text:
    give back value as json
''')
    build = run_cli(
        ["web", "build", str(project), "-o", str(tmp_path / "bundle")], cwd=REPO)
    assert build.returncode == 0, build.stderr


@pytest.mark.skipif(shutil.which("cargo") is None, reason="cargo not installed")
def test_native_dynamic_response_status_headers_security_and_http_semantics(tmp_path):
    project = write_control_project(tmp_path / "app")
    bundle = tmp_path / "bundle"
    build = run_cli(["web", "build", str(project), "-o", str(bundle)], cwd=REPO)
    assert build.returncode == 0, build.stderr

    contract = json.loads((bundle / "parley.build.json").read_text())
    assert contract["routes"][0]["response"] == {
        "mode": "dynamic", "status_field": "status",
        "headers_field": "headers", "body_field": "body",
    }

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
                status, headers, body = request(port, "GET", "/api/secure")
                if status == 401:
                    break
            except OSError:
                time.sleep(0.05)
        else:
            pytest.fail("web server did not start")

        assert headers["www-authenticate"] == "Bearer"
        assert headers["x-auth-state"] == "denied"
        assert json.loads(body) == {"message": "unauthorized", "accepted": False}

        status, headers, body = request(
            port, "GET", "/api/secure", headers={"authorization": "Bearer parley"})
        assert status == 200
        assert headers["x-auth-state"] == "accepted"
        assert json.loads(body) == {"message": "welcome", "accepted": True}

        status, headers, body = request(
            port, "POST", "/api/items", payload={"name": "harbor", "count": 2})
        assert status == 201
        assert headers["location"] == "/api/items/harbor"
        assert json.loads(body)["accepted"] is True

        status, headers, body = request(
            port, "POST", "/api/items", payload={"name": "harbor", "count": 0})
        assert status == 422
        assert headers["x-validation"] == "count"
        assert json.loads(body)["accepted"] is False

        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        connection.request(
            "POST", "/api/items", body=b'{"name":"harbor"}',
            headers={"content-type": "application/json"})
        invalid = connection.getresponse()
        assert invalid.status == 400
        assert json.loads(invalid.read())["error"] == "invalid_json"
        connection.close()

        for name, value in [
            ("status-low", 200), ("status-high", 200), ("reserved", 200),
            ("control", 200), ("invalid-name", 200), ("duplicate", 200),
            ("many", 200), ("large", 200),
        ]:
            status, headers, body = request(
                port, "POST", "/api/unsafe", payload={"name": name, "count": value})
            assert status == 500
            expected = ("invalid_response_status" if name.startswith("status-")
                        else "invalid_response_headers")
            assert json.loads(body)["error"] == expected
            assert "x-dupe" not in headers

        for status_code in (204, 205, 304):
            status, headers, body = request(
                port, "POST", "/api/unsafe",
                payload={"name": "bodyless", "count": status_code})
            assert status == status_code
            assert body == b""
            if status_code in (204, 304):
                assert "content-length" not in headers
            else:
                assert headers["content-length"] == "0"

        get_status, get_headers, get_body = request(
            port, "GET", "/api/secure", headers={"authorization": "Bearer parley"})
        head_status, head_headers, head_body = request(
            port, "HEAD", "/api/secure", headers={"authorization": "Bearer parley"})
        assert (head_status, head_headers["x-auth-state"], head_body) == (
            get_status, "accepted", b"")
        assert head_headers["x-seen-method"] == "GET"
        assert head_headers["content-length"] == str(len(get_body))
    finally:
        server.terminate()
        server.wait(timeout=10)
