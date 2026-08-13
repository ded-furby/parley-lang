#!/usr/bin/env python3
"""Run the non-model parent-check orchestration smoke for study 045."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

try:
    from .agent_check_transport import CHECK_FILE, CLIENT_FILE, ParentCheckBroker
    from .run_fullstack_agent_045 import (
        PROTOCOL_PATH,
        _integrity,
        atomic_write_json,
        digest,
        evaluate_application,
        load_cases,
        load_protocol,
        load_task_map,
        parent_public_evaluation,
        workspace_paths,
        write_workspace,
    )
except ImportError:
    from agent_check_transport import CHECK_FILE, CLIENT_FILE, ParentCheckBroker
    from run_fullstack_agent_045 import (
        PROTOCOL_PATH,
        _integrity,
        atomic_write_json,
        digest,
        evaluate_application,
        load_cases,
        load_protocol,
        load_task_map,
        parent_public_evaluation,
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


def run_smoke(parley_command: str, provenance: Path, work_root: Path) -> dict[str, Any]:
    load_protocol()
    task = load_task_map()["artifact_accession_build"]
    cases = load_cases()[task["id"]]
    work_root.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="045-orchestration-", dir=work_root))
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
            row for row in public["cases"] if row["id"] == "artifact_accession_primary"
        )
        hidden_auth = next(
            row for row in hidden["cases"] if row["id"] == "artifact_accession_unauthorized"
        )
        result = {
            "schema_version": 1,
            "experiment_id": "045",
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
            and result["public"]["case_count"] == 4
            and result["public"]["browser_cases"] == 1
            and not result["hidden"]["semantic_pass"]
            and result["hidden"]["build_pass"]
            and result["hidden"]["post_build_integrity"]
            and result["hidden"]["case_count"] == 5
            and result["hidden"]["browser_cases"] == 2
            and result["custom_header_judgment"][
                "failing_public_application_headers"
            ] == {}
            and result["custom_header_judgment"][
                "passing_hidden_application_headers"
            ] == {"www-authenticate": "Bearer realm=artifact-accession"}
            and result["custom_header_judgment"]["passing_hidden_case_pass"]
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
