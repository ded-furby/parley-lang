#!/usr/bin/env python3
"""Exercise study 039's parent checker and hidden evaluator without a model call."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any

try:
    from .agent_check_transport import CHECK_FILE, CLIENT_FILE, ParentCheckBroker
    from .run_fullstack_agent_039 import (
        _integrity,
        digest,
        evaluate_application,
        load_cases,
        load_protocol,
        load_provenance,
        load_task_map,
        parent_public_evaluation,
        workspace_paths,
        write_workspace,
    )
except ImportError:
    from agent_check_transport import CHECK_FILE, CLIENT_FILE, ParentCheckBroker
    from run_fullstack_agent_039 import (
        _integrity,
        digest,
        evaluate_application,
        load_cases,
        load_protocol,
        load_provenance,
        load_task_map,
        parent_public_evaluation,
        workspace_paths,
        write_workspace,
    )


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO / "benchmarks/fullstack_agent_039_orchestration_smoke.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_summary(result: dict[str, Any]) -> dict[str, Any]:
    cases = result.get("cases", [])
    build = result.get("build", {})
    return {
        "semantic_pass": bool(result.get("ok")),
        "build_pass": bool(build.get("ok")),
        "post_build_integrity": bool(build.get("protected_read_only_ok")),
        "exact_build_commands": len(build.get("protected_read_only_checks", [])),
        "case_count": len(cases),
        "http_cases": sum(row.get("target") == "http" for row in cases),
        "browser_cases": sum(row.get("target") == "browser" for row in cases),
        "cross_target_executed": result.get("cross_target") is not None,
    }


def run_smoke(parley_command: str, provenance: Path) -> dict[str, Any]:
    protocol = load_protocol()
    load_provenance(provenance, parley_command)
    task = load_task_map()["festival_power_build"]
    hidden_cases = [
        row
        for row in load_cases()[task["id"]]
        if row["visibility"] == "hidden"
    ]

    with tempfile.TemporaryDirectory(prefix="parley-fullstack-039-orchestration-") as root:
        workspace = Path(root) / "workspace"
        workspace.mkdir()
        written = write_workspace(workspace, task, "python", parley_command)
        broker = ParentCheckBroker(
            workspace,
            lambda _number, _request_id: parent_public_evaluation(
                workspace,
                task,
                "python",
                parley_command,
                {**written["protected_hashes"], **written["read_only_hashes"]},
            ),
            max_attempts=protocol["frozen_config"]["max_public_check_attempts"],
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
                ["./sources"], cwd=workspace, capture_output=True, text=True, timeout=30
            )
            check = subprocess.run(
                ["./check"], cwd=workspace, capture_output=True, text=True, timeout=600
            )
        finally:
            broker.stop(timeout=600)

        hidden = evaluate_application(
            workspace,
            task,
            "python",
            hidden_cases,
            parley_command,
            frozen_hashes,
        )
        transport = broker.integrity()
        unexpected = sorted(set(workspace_paths(workspace)) - set(initial_paths))
        if len(broker.attempts) != 1:
            raise RuntimeError(f"expected one parent-check attempt, got {len(broker.attempts)}")
        public = broker.attempts[0]
        result = {
            "schema_version": 1,
            "experiment_id": "039",
            "purpose": "non-model end-to-end orchestration smoke",
            "task_id": task["id"],
            "language": "python",
            "protocol_sha256": sha256(REPO / "benchmarks/fullstack_agent_039_protocol.json"),
            "provenance_sha256": sha256(provenance),
            "commands": [
                {"command": "./sources", "returncode": sources.returncode},
                {"command": "./check", "returncode": check.returncode},
            ],
            "sources_listed_contract": "CONTRACT.md [read-only]" in sources.stdout,
            "check_returned_public_failure": check.returncode == 1,
            "attempt_count": len(broker.attempts),
            "public": case_summary(public),
            "hidden": case_summary(hidden),
            "protected_integrity": _integrity(workspace, written["protected_hashes"]),
            "read_only_integrity": _integrity(workspace, written["read_only_hashes"]),
            "transport_integrity": bool(
                transport["ok"] and not transport["protocol_errors"]
            ),
            "unexpected_files": unexpected,
        }

    required = (
        result["commands"] == [
            {"command": "./sources", "returncode": 0},
            {"command": "./check", "returncode": 1},
        ]
        and result["sources_listed_contract"]
        and result["check_returned_public_failure"]
        and result["attempt_count"] == 1
        and result["public"]["build_pass"]
        and result["public"]["post_build_integrity"]
        and result["public"]["case_count"] == 4
        and result["public"]["browser_cases"] == 1
        and result["public"]["cross_target_executed"]
        and not result["public"]["semantic_pass"]
        and result["hidden"]["build_pass"]
        and result["hidden"]["post_build_integrity"]
        and result["hidden"]["case_count"] == 5
        and result["hidden"]["browser_cases"] == 2
        and result["hidden"]["cross_target_executed"]
        and not result["hidden"]["semantic_pass"]
        and result["protected_integrity"]
        and result["read_only_integrity"]
        and result["transport_integrity"]
        and not result["unexpected_files"]
    )
    result["pass"] = bool(required)
    if not result["pass"]:
        raise RuntimeError("study 039 orchestration smoke failed: " + json.dumps(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parley-command", required=True)
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run_smoke(args.parley_command, args.provenance)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
