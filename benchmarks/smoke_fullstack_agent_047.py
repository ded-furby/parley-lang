#!/usr/bin/env python3
"""Run the non-model parent-check orchestration smoke for study 047."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
from typing import Any

try:
    from .agent_check_transport import CHECK_FILE, CLIENT_FILE, ParentCheckBroker
    from .run_fullstack_agent_047 import (
        PROTOCOL_PATH,
        _integrity,
        atomic_write_json,
        digest,
        evaluate_application,
        load_cases,
        load_protocol,
        load_task_map,
        parent_public_evaluation,
        request,
        workspace_paths,
        write_workspace,
    )
except ImportError:
    from agent_check_transport import CHECK_FILE, CLIENT_FILE, ParentCheckBroker
    from run_fullstack_agent_047 import (
        PROTOCOL_PATH,
        _integrity,
        atomic_write_json,
        digest,
        evaluate_application,
        load_cases,
        load_protocol,
        load_task_map,
        parent_public_evaluation,
        request,
        workspace_paths,
        write_workspace,
    )


def case_summary(result: dict[str, Any]) -> dict[str, Any]:
    cases = result.get("cases", [])
    cross_target = result.get("cross_target")
    return {
        "semantic_pass": bool(result.get("ok")),
        "build_pass": bool(result.get("build", {}).get("ok")),
        "post_build_integrity": bool(
            result.get("build", {}).get("protected_read_only_ok")
        ),
        "exact_build_commands": len(
            result.get("build", {}).get("protected_read_only_checks", [])
        ),
        "case_count": len(cases),
        "http_cases": sum(row.get("target") == "http" for row in cases),
        "browser_cases": sum(row.get("target") == "browser" for row in cases),
        "cross_target_executed": cross_target is not None,
    }


def duplicate_header_capture() -> dict[str, Any]:
    """Capture a real repeated response header through the measured request path."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = b'{"ok":true}'
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("x-repeat", "alpha")
            self.send_header("x-repeat", "beta")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        return request(
            int(server.server_address[1]),
            {
                "method": "GET", "path": "/", "expected_status": 200,
                "expected_json": {"ok": True}, "expected_headers": {},
            },
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def run_smoke(parley_command: str, provenance: Path, work_root: Path) -> dict[str, Any]:
    load_protocol()
    task = load_task_map()["tundra_probe_lookup_build"]
    cases = load_cases()[task["id"]]
    work_root.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="047-orchestration-", dir=work_root))
    attempt_root = workspace.parent / f"{workspace.name}-attempts"
    try:
        written = write_workspace(workspace, task, "python", parley_command)
        broker = ParentCheckBroker(
            workspace,
            lambda number, request_id: parent_public_evaluation(
                workspace,
                task,
                "python",
                parley_command,
                {**written["protected_hashes"], **written["read_only_hashes"]},
            ),
            attempt_root=attempt_root,
            max_attempts=1,
        )
        broker.install()
        written["protected_hashes"][CLIENT_FILE] = digest(workspace / CLIENT_FILE)
        written["protected_hashes"][CHECK_FILE] = digest(workspace / CHECK_FILE)
        frozen_hashes = {
            **written["protected_hashes"],
            **written["read_only_hashes"],
        }
        initial_paths = workspace_paths(workspace)
        broker.start()
        try:
            sources = subprocess.run(
                ["./sources"], cwd=workspace, capture_output=True, text=True
            )
            check = subprocess.run(
                ["./check"], cwd=workspace, capture_output=True, text=True
            )
        finally:
            broker.stop(timeout=900)

        if len(broker.attempts) != 1:
            raise RuntimeError("orchestration smoke did not record one public attempt")
        public = broker.attempts[0]
        hidden = evaluate_application(
            workspace,
            task,
            "python",
            [row for row in cases if row["visibility"] == "hidden"],
            parley_command,
            frozen_hashes,
        )
        transport = broker.integrity()
        protected = _integrity(workspace, written["protected_hashes"])
        read_only = _integrity(workspace, written["read_only_hashes"])
        unexpected = sorted(set(workspace_paths(workspace)) - set(initial_paths))
        public_primary = next(
            row for row in public["cases"] if row["id"] == "tundra_probe_lookup_primary"
        )
        public_status = next(
            row for row in public["cases"] if row["id"] == "tundra_probe_lookup_status"
        )
        hidden_auth = next(
            row for row in hidden["cases"] if row["id"] == "tundra_probe_lookup_unauthorized"
        )
        attempt_files = sorted(attempt_root.glob("attempt-*.json"))
        durable_public = (
            json.loads(attempt_files[0].read_text()) if len(attempt_files) == 1 else None
        )
        durable_primary = next(
            (
                row for row in durable_public.get("cases", [])
                if row["id"] == "tundra_probe_lookup_primary"
            ),
            None,
        ) if durable_public else None
        durable_status = next(
            (
                row for row in durable_public.get("cases", [])
                if row["id"] == "tundra_probe_lookup_status"
            ),
            None,
        ) if durable_public else None
        custom_control_path = attempt_root / "custom-header-control.json"
        atomic_write_json(
            custom_control_path,
            {"application_header_pairs": hidden_auth["application_header_pairs"]},
        )
        duplicate = duplicate_header_capture()
        duplicate_control_path = attempt_root / "duplicate-header-control.json"
        atomic_write_json(
            duplicate_control_path,
            {"application_header_pairs": duplicate["application_header_pairs"]},
        )
        evidence_controls = {
            "broker_attempt_exact": durable_public == public,
            "empty": {
                "live": public_status["application_header_pairs"],
                "persisted": (
                    durable_status["application_header_pairs"]
                    if durable_status else None
                ),
            },
            "custom": {
                "live": hidden_auth["application_header_pairs"],
                "persisted": json.loads(custom_control_path.read_text())[
                    "application_header_pairs"
                ],
            },
            "duplicate": {
                "live": duplicate["application_header_pairs"],
                "persisted": json.loads(duplicate_control_path.read_text())[
                    "application_header_pairs"
                ],
            },
            "routing": {
                "live_path": public_primary["request_path"],
                "persisted_path": (
                    durable_primary["request_path"] if durable_primary else None
                ),
                "live_path_parameters": public_primary["path_parameters"],
                "persisted_path_parameters": (
                    durable_primary["path_parameters"] if durable_primary else None
                ),
            },
        }
        evidence_controls["json_native_shape"] = all(
            isinstance(pairs, list)
            and all(isinstance(pair, list) and len(pair) == 2 for pair in pairs)
            for name in ("empty", "custom", "duplicate")
            for pairs in (
                evidence_controls[name]["live"],
                evidence_controls[name]["persisted"],
            )
        )
        evidence_controls["pass"] = bool(
            evidence_controls["broker_attempt_exact"]
            and evidence_controls["json_native_shape"]
            and evidence_controls["empty"]["live"]
            == evidence_controls["empty"]["persisted"]
            == []
            and evidence_controls["custom"]["live"]
            == evidence_controls["custom"]["persisted"]
            == [["x-access-denial", "tundra_pass"]]
            and evidence_controls["duplicate"]["live"]
            == evidence_controls["duplicate"]["persisted"]
            == [["x-repeat", "alpha"], ["x-repeat", "beta"]]
            and evidence_controls["routing"]["live_path"]
            == evidence_controls["routing"]["persisted_path"]
            == "/api/v11/tundra-probes/18"
            and evidence_controls["routing"]["live_path_parameters"]
            == evidence_controls["routing"]["persisted_path_parameters"]
            == {"probe_serial": "18"}
        )
        result = {
            "schema_version": 1,
            "experiment_id": "047",
            "purpose": "non-model end-to-end orchestration smoke",
            "task_id": task["id"],
            "language": "python",
            "protocol_sha256": digest(PROTOCOL_PATH),
            "provenance_sha256": digest(provenance),
            "commands": [
                {"command": "./sources", "returncode": sources.returncode},
                {"command": "./check", "returncode": check.returncode},
            ],
            "sources_listed_contract": "===== CONTRACT.md [read-only] ====="
            in sources.stdout,
            "check_returned_public_failure": check.returncode == 1,
            "attempt_count": len(broker.attempts),
            "public": case_summary(public),
            "hidden": case_summary(hidden),
            "custom_header_judgment": {
                "failing_public_case": public_primary["id"],
                "failing_public_application_headers": public_primary[
                    "application_headers"
                ],
                "passing_hidden_case": hidden_auth["id"],
                "passing_hidden_application_headers": hidden_auth[
                    "application_headers"
                ],
                "passing_hidden_case_pass": hidden_auth["pass"],
            },
            "json_evidence_controls": evidence_controls,
            "protected_integrity": protected,
            "read_only_integrity": read_only,
            "transport_integrity": bool(
                transport["ok"] and not transport["protocol_errors"]
            ),
            "unexpected_files": unexpected,
        }
        result["pass"] = bool(
            sources.returncode == 0
            and result["sources_listed_contract"]
            and result["check_returned_public_failure"]
            and result["attempt_count"] == 1
            and not result["public"]["semantic_pass"]
            and result["public"]["build_pass"]
            and result["public"]["post_build_integrity"]
            and result["public"]["case_count"] == 5
            and result["public"]["http_cases"] == 4
            and result["public"]["browser_cases"] == 1
            and not result["hidden"]["semantic_pass"]
            and result["hidden"]["build_pass"]
            and result["hidden"]["post_build_integrity"]
            and result["hidden"]["case_count"] == 5
            and result["hidden"]["browser_cases"] == 2
            and result["custom_header_judgment"][
                "failing_public_application_headers"
            ] == {"x-probe-state": "catalogued"}
            and result["custom_header_judgment"][
                "passing_hidden_application_headers"
            ] == {"x-access-denial": "tundra_pass"}
            and result["custom_header_judgment"]["passing_hidden_case_pass"]
            and result["json_evidence_controls"]["pass"]
            and protected
            and read_only
            and result["transport_integrity"]
            and not unexpected
        )
        return result
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
        shutil.rmtree(attempt_root, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parley-command", required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_smoke(
        args.parley_command,
        args.provenance,
        args.work_root,
    )
    atomic_write_json(args.output, result)
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
