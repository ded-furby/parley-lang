"""Language-neutral HTTP numeric-domain guard for full-stack study 039."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
import json
import threading
from typing import Any


HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def invalid_numeric_domain(task: dict[str, Any], body: bytes) -> bool:
    """Return true only for well-shaped numeric values outside the shared domain."""
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(value, dict):
        return False
    for name, kind in task["request_fields"].items():
        item = value.get(name)
        if kind == "number" and type(item) is int and item < 0:
            return True
    return False


class DomainGuard:
    """Proxy one candidate service while enforcing the shared numeric domain."""

    def __init__(self, task: dict[str, Any], upstream_port: int, listen_port: int):
        self.task = task
        self.upstream_port = upstream_port
        self.listen_port = listen_port
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        task = self.task
        upstream_port = self.upstream_port

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def _handle(self) -> None:
                declared = self.headers.get("content-length", "0")
                length = int(declared) if declared.isdigit() else 0
                body = self.rfile.read(length) if length else b""
                media_type = self.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if (
                    self.command == "POST"
                    and self.path == task["post_route"]
                    and (media_type == "application/json" or media_type.endswith("+json"))
                    and invalid_numeric_domain(task, body)
                ):
                    payload = json.dumps(
                        {
                            "error": "invalid_json",
                            "detail": "numeric value outside contract",
                        },
                        separators=(",", ":"),
                    ).encode()
                    self.send_response(400)
                    self.send_header("content-type", "application/json")
                    self.send_header("content-length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return

                headers = {
                    name: value
                    for name, value in self.headers.items()
                    if name.lower() not in HOP_BY_HOP | {"host", "content-length"}
                }
                if body:
                    headers["content-length"] = str(len(body))
                connection = http.client.HTTPConnection(
                    "127.0.0.1", upstream_port, timeout=15
                )
                try:
                    connection.request(
                        self.command,
                        self.path,
                        body=body or None,
                        headers=headers,
                    )
                    response = connection.getresponse()
                    payload = response.read()
                    response_headers = list(response.getheaders())
                finally:
                    connection.close()
                self.send_response(response.status)
                for name, value in response_headers:
                    lowered = name.lower()
                    if lowered not in HOP_BY_HOP | {"content-length", "server", "date"}:
                        self.send_header(name, value)
                self.send_header("content-length", str(len(payload)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(payload)

            do_GET = _handle
            do_HEAD = _handle
            do_POST = _handle
            do_PUT = _handle
            do_PATCH = _handle
            do_DELETE = _handle

            def log_message(self, format: str, *args: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", self.listen_port), Handler)
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            name=f"domain-guard-{self.listen_port}",
            daemon=True,
        )
        self.thread.start()

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                raise RuntimeError("numeric-domain guard did not stop")
