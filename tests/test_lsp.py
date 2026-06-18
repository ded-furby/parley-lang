import io
import json

from parley.lsp import diagnostics_for_text, run_server


def encode_message(payload: dict) -> bytes:
    body = json.dumps(payload).encode("utf-8")
    return b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body


def decode_messages(data: bytes) -> list[dict]:
    messages = []
    pos = 0
    while pos < len(data):
        header_end = data.index(b"\r\n\r\n", pos)
        headers = data[pos:header_end].decode("ascii").split("\r\n")
        length = 0
        for header in headers:
            name, value = header.split(":", 1)
            if name.lower() == "content-length":
                length = int(value.strip())
        body_start = header_end + 4
        body_end = body_start + length
        messages.append(json.loads(data[body_start:body_end]))
        pos = body_end
    return messages


def test_lsp_diagnostics_use_parley_pcodes():
    uri = "file:///tmp/main.par"
    diagnostics = diagnostics_for_text(uri, "to main:\n    say missing_name\n")

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic["code"] == "P201"
    assert diagnostic["source"] == "parley"
    assert 'There is no "missing_name" here.' in diagnostic["message"]
    assert "Hint:" in diagnostic["message"]
    assert diagnostic["range"]["start"]["line"] == 1
    assert diagnostic["range"]["start"]["character"] >= 4


def test_lsp_server_publishes_diagnostics_for_open_document():
    uri = "file:///tmp/main.par"
    incoming = b"".join(
        [
            encode_message(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {},
                }
            ),
            encode_message(
                {
                    "jsonrpc": "2.0",
                    "method": "textDocument/didOpen",
                    "params": {
                        "textDocument": {
                            "uri": uri,
                            "languageId": "parley",
                            "version": 1,
                            "text": "to main:\n    say missing_name\n",
                        }
                    },
                }
            ),
            encode_message({"jsonrpc": "2.0", "id": 2, "method": "shutdown"}),
            encode_message({"jsonrpc": "2.0", "method": "exit"}),
        ]
    )
    output = io.BytesIO()

    run_server(io.BytesIO(incoming), output)

    messages = decode_messages(output.getvalue())
    assert messages[0]["id"] == 1
    assert messages[0]["result"]["capabilities"]["textDocumentSync"]["openClose"] is True
    published = next(msg for msg in messages if msg.get("method") == "textDocument/publishDiagnostics")
    assert published["params"]["uri"] == uri
    assert published["params"]["diagnostics"][0]["code"] == "P201"
    assert messages[-1]["id"] == 2
    assert messages[-1]["result"] is None
