"""Transparent language-neutral loopback proxy for full-stack study 047."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
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
    """Return false: numeric domain decisions belong to the typed handler in 047."""
    del task, body
    return False


class DomainGuard:
    """Proxy one candidate service without changing application semantics."""

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
            name=f"response-proxy-{self.listen_port}",
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
                raise RuntimeError("response proxy did not stop")
