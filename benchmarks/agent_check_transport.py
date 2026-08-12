#!/usr/bin/env python3
"""Parent-owned evaluator transport for network-denied agent workspaces.

The agent's ``./check`` command communicates over two protected POSIX FIFOs.
The parent process receives only an authenticated check request, evaluates the
workspace outside the agent sandbox, preserves the full attempt record, and
returns bounded public feedback. No TCP/IP socket is opened inside the agent
sandbox.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import secrets
import select
import stat
import threading
import time
from typing import Any, Callable


REQUEST_FIFO = ".benchmark_check_request"
RESPONSE_FIFO = ".benchmark_check_response"
CLIENT_FILE = ".benchmark_check_client.py"
CHECK_FILE = "check"
MAX_REQUEST_BYTES = 16_384
MAX_RESPONSE_BYTES = 1_000_000


Evaluator = Callable[[int, str], dict[str, Any]]


def client_script(nonce: str, *, timeout_seconds: int = 900) -> str:
    """Return the protected client used by ``./check`` inside the sandbox."""
    return f'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import secrets
import select
import sys
import time

NONCE = {nonce!r}
REQUEST = Path({REQUEST_FIFO!r})
RESPONSE = Path({RESPONSE_FIFO!r})
TIMEOUT_SECONDS = {timeout_seconds}
request_id = secrets.token_hex(16)
payload = json.dumps({{"nonce": NONCE, "request_id": request_id}}, separators=(",", ":")) + "\\n"

deadline = time.monotonic() + TIMEOUT_SECONDS
request_fd = os.open(REQUEST, os.O_WRONLY | os.O_NONBLOCK)
try:
    os.write(request_fd, payload.encode())
finally:
    os.close(request_fd)

response_fd = os.open(RESPONSE, os.O_RDONLY | os.O_NONBLOCK)
buffer = b""
try:
    while time.monotonic() < deadline:
        ready, _, _ = select.select([response_fd], [], [], min(0.25, deadline - time.monotonic()))
        if not ready:
            continue
        chunk = os.read(response_fd, 65536)
        if not chunk:
            continue
        buffer += chunk
        if b"\\n" in buffer:
            break
finally:
    os.close(response_fd)

if b"\\n" not in buffer:
    print("parent evaluator timed out", file=sys.stderr)
    raise SystemExit(1)
response = json.loads(buffer.split(b"\\n", 1)[0])
if response.get("request_id") != request_id:
    print("parent evaluator response id mismatch", file=sys.stderr)
    raise SystemExit(1)
stdout = str(response.get("stdout", ""))
stderr = str(response.get("stderr", ""))
if stdout:
    print(stdout, end="" if stdout.endswith("\\n") else "\\n")
if stderr:
    print(stderr, end="" if stderr.endswith("\\n") else "\\n", file=sys.stderr)
raise SystemExit(0 if response.get("ok") else 1)
'''


def check_script() -> str:
    return "#!/bin/sh\nexec python3 .benchmark_check_client.py\n"


@dataclass(frozen=True)
class FifoIdentity:
    device: int
    inode: int
    mode: int
    uid: int


def fifo_identity(path: Path) -> FifoIdentity:
    metadata = path.lstat()
    if not stat.S_ISFIFO(metadata.st_mode):
        raise RuntimeError(f"protected transport path is not a FIFO: {path}")
    return FifoIdentity(metadata.st_dev, metadata.st_ino, metadata.st_mode, metadata.st_uid)


class ParentCheckBroker:
    """Serve sequential check requests from one isolated agent workspace."""

    def __init__(
        self,
        workspace: Path,
        evaluator: Evaluator,
        *,
        attempt_root: Path | None = None,
        max_attempts: int = 100,
    ) -> None:
        self.workspace = workspace.resolve()
        self.evaluator = evaluator
        self.attempt_root = attempt_root.resolve() if attempt_root else None
        self.max_attempts = max_attempts
        self.nonce = secrets.token_hex(32)
        self.request_path = self.workspace / REQUEST_FIFO
        self.response_path = self.workspace / RESPONSE_FIFO
        self.client_path = self.workspace / CLIENT_FILE
        self.check_path = self.workspace / CHECK_FILE
        self.attempts: list[dict[str, Any]] = []
        self.protocol_errors: list[str] = []
        self._identities: dict[str, FifoIdentity] = {}
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._exception: BaseException | None = None

    def install(self) -> dict[str, str]:
        self.workspace.mkdir(parents=True, exist_ok=True)
        for path in (self.request_path, self.response_path):
            if path.exists() or path.is_symlink():
                raise RuntimeError(f"transport path already exists: {path}")
            os.mkfifo(path, mode=0o600)
        self.client_path.write_text(client_script(self.nonce), encoding="utf-8")
        self.check_path.write_text(check_script(), encoding="utf-8")
        self.client_path.chmod(0o700)
        self.check_path.chmod(0o700)
        self._identities = {
            REQUEST_FIFO: fifo_identity(self.request_path),
            RESPONSE_FIFO: fifo_identity(self.response_path),
        }
        return {
            "request_fifo": str(self.request_path),
            "response_fifo": str(self.response_path),
            "client": str(self.client_path),
            "check": str(self.check_path),
        }

    def start(self) -> None:
        if not self._identities:
            raise RuntimeError("install the parent check broker before starting it")
        if self._thread is not None:
            raise RuntimeError("parent check broker already started")
        self._thread = threading.Thread(
            target=self._serve,
            name=f"check-broker-{self.workspace.name}",
            daemon=True,
        )
        self._thread.start()
        if not self._ready.wait(timeout=5):
            raise RuntimeError("parent check broker did not become ready")

    def stop(self, *, timeout: float = 10.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                raise RuntimeError("parent check broker did not stop")
        if self._exception is not None:
            raise RuntimeError("parent check broker failed") from self._exception

    def integrity(self) -> dict[str, Any]:
        actual: dict[str, FifoIdentity | None] = {}
        for name, path in (
            (REQUEST_FIFO, self.request_path),
            (RESPONSE_FIFO, self.response_path),
        ):
            try:
                actual[name] = fifo_identity(path)
            except (OSError, RuntimeError):
                actual[name] = None
        return {
            "ok": actual == self._identities,
            "expected": {
                name: identity.__dict__ for name, identity in self._identities.items()
            },
            "actual": {
                name: identity.__dict__ if identity else None
                for name, identity in actual.items()
            },
            "protocol_errors": list(self.protocol_errors),
        }

    def _record(self, attempt: dict[str, Any]) -> None:
        self.attempts.append(attempt)
        if self.attempt_root is None:
            return
        self.attempt_root.mkdir(parents=True, exist_ok=True)
        path = self.attempt_root / f"attempt-{attempt['attempt']:03d}.json"
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(attempt, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)

    def _write_response(self, descriptor: int, response: dict[str, Any]) -> None:
        payload = (json.dumps(response, separators=(",", ":")) + "\n").encode()
        if len(payload) > MAX_RESPONSE_BYTES:
            payload = (
                json.dumps(
                    {
                        "request_id": response.get("request_id"),
                        "ok": False,
                        "stdout": "",
                        "stderr": "parent evaluator response exceeded the transport limit",
                    },
                    separators=(",", ":"),
                )
                + "\n"
            ).encode()
        offset = 0
        deadline = time.monotonic() + 30
        while offset < len(payload):
            if time.monotonic() >= deadline:
                raise TimeoutError("timed out writing parent evaluator response")
            try:
                offset += os.write(descriptor, payload[offset:])
            except BlockingIOError:
                select.select([], [descriptor], [], 0.1)

    def _handle(self, request: dict[str, Any], response_descriptor: int) -> None:
        request_id = str(request.get("request_id", ""))
        if request.get("nonce") != self.nonce or len(request_id) != 32:
            error = "invalid parent-check request authentication"
            self.protocol_errors.append(error)
            self._write_response(
                response_descriptor,
                {"request_id": request_id, "ok": False, "stdout": "", "stderr": error},
            )
            return
        if len(self.attempts) >= self.max_attempts:
            error = "parent-check attempt limit exceeded"
            self.protocol_errors.append(error)
            self._write_response(
                response_descriptor,
                {"request_id": request_id, "ok": False, "stdout": "", "stderr": error},
            )
            return
        number = len(self.attempts) + 1
        started = time.perf_counter()
        try:
            evaluation = self.evaluator(number, request_id)
            if not isinstance(evaluation, dict) or not isinstance(evaluation.get("ok"), bool):
                raise TypeError("evaluator must return a mapping with boolean ok")
        except Exception as exc:
            evaluation = {
                "ok": False,
                "stdout": "",
                "stderr": f"parent evaluator error: {exc}",
                "evaluator_error": repr(exc),
            }
        attempt = {
            "attempt": number,
            "request_id": request_id,
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            **evaluation,
        }
        self._record(attempt)
        self._write_response(
            response_descriptor,
            {
                "request_id": request_id,
                "ok": bool(evaluation["ok"]),
                "stdout": str(evaluation.get("stdout", "")),
                "stderr": str(evaluation.get("stderr", "")),
            },
        )

    def _serve(self) -> None:
        request_descriptor = response_descriptor = None
        try:
            request_descriptor = os.open(self.request_path, os.O_RDWR | os.O_NONBLOCK)
            response_descriptor = os.open(self.response_path, os.O_RDWR | os.O_NONBLOCK)
            self._ready.set()
            buffer = b""
            while not self._stop.is_set():
                ready, _, _ = select.select([request_descriptor], [], [], 0.1)
                if not ready:
                    continue
                chunk = os.read(request_descriptor, 65536)
                if not chunk:
                    continue
                buffer += chunk
                if len(buffer) > MAX_REQUEST_BYTES:
                    raise RuntimeError("parent-check request exceeded the transport limit")
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line:
                        continue
                    try:
                        request = json.loads(line)
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        self.protocol_errors.append(f"invalid request JSON: {exc}")
                        continue
                    self._handle(request, response_descriptor)
        except BaseException as exc:
            self._exception = exc
            self._ready.set()
        finally:
            for descriptor in (request_descriptor, response_descriptor):
                if descriptor is not None:
                    os.close(descriptor)
