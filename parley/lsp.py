"""Minimal Language Server Protocol support for Parley.

The server speaks JSON-RPC over stdio and publishes compiler diagnostics for
open documents. It deliberately reuses the normal parser/checker path so editor
diagnostics carry the same stable P-codes as `parley check --json`.
"""

from __future__ import annotations

import json
import sys
from typing import BinaryIO, Any

from .checker import check_program
from .diagnostics import Diagnostic, ParleyError
from .parser import parse


def lsp_position(line: int, col: int) -> dict[str, int]:
    return {"line": max(line - 1, 0), "character": max(col - 1, 0)}


def lsp_diagnostic(diag: Diagnostic) -> dict[str, Any]:
    start = lsp_position(diag.line or 1, diag.col or 1)
    end = {"line": start["line"], "character": start["character"] + 1}
    message = diag.message
    if diag.hint:
        message += f"\nHint: {diag.hint}"
    if diag.replacement:
        message += f"\nTry: {diag.replacement}"
    return {
        "range": {"start": start, "end": end},
        "severity": 1 if diag.severity == "error" else 2,
        "code": diag.code,
        "source": "parley",
        "message": message,
    }


def diagnostics_for_text(uri: str, text: str) -> list[dict[str, Any]]:
    try:
        program = parse(text)
        diagnostics = check_program(program)
    except ParleyError as exc:
        diagnostics = exc.diagnostics
    for diag in diagnostics:
        if not diag.file:
            diag.file = uri
    return [lsp_diagnostic(diag) for diag in diagnostics]


def read_message(reader: BinaryIO) -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = reader.readline()
        if line == b"":
            return None
        if line in (b"\r\n", b"\n"):
            break
        name, _, value = line.decode("ascii").partition(":")
        headers[name.lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    return json.loads(reader.read(length).decode("utf-8"))


def write_message(writer: BinaryIO, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    writer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    writer.write(body)
    writer.flush()


class LanguageServer:
    def __init__(self, reader: BinaryIO, writer: BinaryIO):
        self.reader = reader
        self.writer = writer
        self.documents: dict[str, str] = {}
        self.shutdown_requested = False

    def send_response(self, message_id: int | str | None, result: Any = None) -> None:
        write_message(
            self.writer,
            {"jsonrpc": "2.0", "id": message_id, "result": result},
        )

    def send_error(self, message_id: int | str | None, code: int, message: str) -> None:
        write_message(
            self.writer,
            {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}},
        )

    def publish_diagnostics(self, uri: str, text: str) -> None:
        write_message(
            self.writer,
            {
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {"uri": uri, "diagnostics": diagnostics_for_text(uri, text)},
            },
        )

    def handle(self, message: dict[str, Any]) -> bool:
        method = message.get("method")
        message_id = message.get("id")
        params = message.get("params") or {}

        if method == "initialize":
            self.send_response(
                message_id,
                {
                    "capabilities": {
                        "textDocumentSync": {"openClose": True, "change": 1},
                    },
                    "serverInfo": {"name": "parley-lsp"},
                },
            )
            return True
        if method == "shutdown":
            self.shutdown_requested = True
            self.send_response(message_id, None)
            return True
        if method == "exit":
            return False
        if method == "textDocument/didOpen":
            doc = params.get("textDocument") or {}
            uri = str(doc.get("uri", ""))
            text = str(doc.get("text", ""))
            self.documents[uri] = text
            self.publish_diagnostics(uri, text)
            return True
        if method == "textDocument/didChange":
            doc = params.get("textDocument") or {}
            changes = params.get("contentChanges") or []
            uri = str(doc.get("uri", ""))
            if changes:
                text = str(changes[-1].get("text", ""))
                self.documents[uri] = text
                self.publish_diagnostics(uri, text)
            return True
        if method == "textDocument/didClose":
            doc = params.get("textDocument") or {}
            uri = str(doc.get("uri", ""))
            self.documents.pop(uri, None)
            write_message(
                self.writer,
                {
                    "jsonrpc": "2.0",
                    "method": "textDocument/publishDiagnostics",
                    "params": {"uri": uri, "diagnostics": []},
                },
            )
            return True

        if message_id is not None:
            self.send_error(message_id, -32601, f"Method not found: {method}")
        return True

    def run(self) -> None:
        while True:
            message = read_message(self.reader)
            if message is None or not self.handle(message):
                break


def run_server(reader: BinaryIO | None = None, writer: BinaryIO | None = None) -> None:
    LanguageServer(reader or sys.stdin.buffer, writer or sys.stdout.buffer).run()


def main() -> int:
    run_server()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
