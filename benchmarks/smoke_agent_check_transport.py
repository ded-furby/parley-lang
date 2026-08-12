#!/usr/bin/env python3
"""Exercise the parent-owned checker through a network-denied Codex session."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
from typing import Any

try:
    from .agent_check_transport import ParentCheckBroker
    from .agent_runner import parse_codex_events, utc_now
except ImportError:
    from agent_check_transport import ParentCheckBroker
    from agent_runner import parse_codex_events, utc_now


REPO = Path(__file__).resolve().parents[1]
PROMPT = """You are validating a controlled checker transport in a fresh workspace.
Do not edit any file. Your first shell command must be exactly `./sources`.
Your second and final shell command must be exactly `./check`.
After the check passes, reply with `transport passed` and do not use more tools.
"""
APP = r"""#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os

PORT = int(os.environ["TRANSPORT_SMOKE_PORT"])
INDEX = b'''<!doctype html><meta charset="utf-8"><title>Transport smoke</title><p id="result">loading</p><script type="module">import { answer } from "/app.js"; document.querySelector("#result").textContent = String(answer());</script>'''
MODULE = b'''export function answer() { return 42; }'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            body = json.dumps({"service": "parent-check-transport", "ready": True}).encode()
            content_type = "application/json"
        elif self.path == "/app.js":
            body = MODULE
            content_type = "text/javascript"
        elif self.path == "/":
            body = INDEX
            content_type = "text/html"
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
"""
SOURCES = """#!/bin/sh
printf '%s\n' '===== app.py [read-only] ====='
cat app.py
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def allocate_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def status(port: int) -> dict[str, Any]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", "/status")
        response = connection.getresponse()
        body = response.read()
    finally:
        connection.close()
    return {"status": response.status, "json": json.loads(body)}


def stop_process(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def evaluate_fixture(workspace: Path) -> dict[str, Any]:
    compile_result = subprocess.run(
        ["python3", "-m", "py_compile", "app.py"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if compile_result.returncode:
        return {
            "ok": False,
            "stdout": "",
            "stderr": compile_result.stderr,
            "build": {"ok": False, "returncode": compile_result.returncode},
        }
    port = allocate_port()
    process = subprocess.Popen(
        ["python3", "app.py"],
        cwd=workspace,
        env={**os.environ, "TRANSPORT_SMOKE_PORT": str(port)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    http_result: dict[str, Any] | None = None
    browser_result: dict[str, Any] | None = None
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                raise RuntimeError(f"fixture server exited early: {stdout}\n{stderr}")
            try:
                http_result = status(port)
                break
            except OSError:
                time.sleep(0.02)
        if http_result is None:
            raise TimeoutError("fixture server did not become ready")
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")
            browser_result = {
                "text": page.locator("#result").text_content(),
                "title": page.title(),
            }
            browser.close()
        ok = (
            http_result
            == {
                "status": 200,
                "json": {"service": "parent-check-transport", "ready": True},
            }
            and browser_result == {"text": "42", "title": "Transport smoke"}
        )
        return {
            "ok": ok,
            "stdout": "parent HTTP and Chromium checks passed\n" if ok else "",
            "stderr": "" if ok else "parent HTTP or Chromium check failed\n",
            "build": {"ok": True, "returncode": 0},
            "http": http_result,
            "browser": browser_result,
        }
    except Exception as exc:
        return {
            "ok": False,
            "stdout": "",
            "stderr": f"parent fixture evaluation failed: {exc}\n",
            "build": {"ok": True, "returncode": 0},
            "http": http_result,
            "browser": browser_result,
            "runtime_error": repr(exc),
        }
    finally:
        stop_process(process)


def command_protocol(events: list[dict[str, Any]]) -> dict[str, Any]:
    commands = [str(event.get("command", "")).strip() for event in events]
    source = re.compile(r"^(?:/bin/(?:zsh|sh)\s+-lc\s+)?[\"']?\./sources[\"']?$")
    check = re.compile(r"^(?:/bin/(?:zsh|sh)\s+-lc\s+)?[\"']?\./check[\"']?$")
    return {
        "commands": commands,
        "compliant": (
            len(commands) == 2
            and bool(source.fullmatch(commands[0]))
            and bool(check.fullmatch(commands[1]))
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--reasoning", default="medium")
    parser.add_argument("--codex-command", default=shutil.which("codex") or "codex")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args(argv)

    workspace = args.workspace or Path(
        tempfile.mkdtemp(prefix="parley-agent-check-transport-smoke-")
    )
    workspace.mkdir(parents=True, exist_ok=True)
    if any(workspace.iterdir()):
        raise RuntimeError(f"transport smoke workspace must be empty: {workspace}")
    (workspace / "app.py").write_text(APP, encoding="utf-8")
    (workspace / "sources").write_text(SOURCES, encoding="utf-8")
    (workspace / "sources").chmod(0o700)
    attempts = workspace.parent / f"{workspace.name}-parent-attempts"
    broker = ParentCheckBroker(
        workspace,
        lambda number, request_id: evaluate_fixture(workspace),
        attempt_root=attempts,
        max_attempts=1,
    )
    broker.install()
    protected = {
        name: sha256(workspace / name)
        for name in ("app.py", "sources", ".benchmark_check_client.py", "check")
    }
    broker.start()
    command = [
        args.codex_command,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--disable", "plugins",
        "--disable", "apps",
        "--disable", "browser_use",
        "--disable", "computer_use",
        "--disable", "multi_agent",
        "--skip-git-repo-check",
        "-s", "workspace-write",
        "-m", args.model,
        "-c", f'model_reasoning_effort="{args.reasoning}"',
        "-c", 'approval_policy="never"',
        "-c", 'shell_environment_policy.inherit="all"',
        "-c", "sandbox_workspace_write.network_access=false",
        "--json",
        "-C", str(workspace),
        PROMPT,
    ]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
        )
    finally:
        broker.stop()
    parsed = parse_codex_events(completed.stdout)
    protocol = command_protocol(parsed["command_events"])
    protected_integrity = all(
        (workspace / name).is_file() and sha256(workspace / name) == digest
        for name, digest in protected.items()
    )
    transport_integrity = broker.integrity()
    ok = (
        completed.returncode == 0
        and protocol["compliant"]
        and len(broker.attempts) == 1
        and broker.attempts[0]["ok"]
        and protected_integrity
        and transport_integrity["ok"]
        and any(message.strip().lower() == "transport passed" for message in parsed["agent_messages"])
    )
    result = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "ok": ok,
        "model": args.model,
        "reasoning": args.reasoning,
        "network_policy": "sandbox_workspace_write.network_access=false",
        "workspace": str(workspace.resolve()),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "agent_returncode": completed.returncode,
        "thread_id": parsed["thread_id"],
        "usage": parsed["usage"],
        "command_protocol": protocol,
        "parent_attempts": broker.attempts,
        "protected_integrity_ok": protected_integrity,
        "transport_integrity": transport_integrity,
        "agent_messages": parsed["agent_messages"],
        "agent_errors": parsed["errors"],
        "codex_stdout": completed.stdout,
        "codex_stderr": completed.stderr,
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
