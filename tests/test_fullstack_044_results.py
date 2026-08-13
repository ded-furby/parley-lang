import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "fullstack_agent_044_raw.json"
AUDIT = BENCHMARKS / "fullstack_agent_044_audit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_044_raw_result_is_complete_clean_and_gate_passed():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    rows = raw["results"]

    assert sha256(RAW) == (
        "76512be28a1d0052c98aa4f601f4945b92423777a5a8560bba0a0c7afcef3399"
    )
    assert len(rows) == len({row["cell_id"] for row in rows}) == 96
    assert len({row["thread_id"] for row in rows}) == 96
    assert sum(row["hidden_success"] for row in rows) == 96
    assert sum(row["first_public_check_success"] for row in rows) == 95
    assert sum(row["final_public_check_success"] for row in rows) == 96
    assert sum(row["repair_turns"] for row in rows) == 1
    assert len(raw["journal"]) == 96
    assert all(entry["cleanup"]["status"] == "removed" for entry in raw["journal"])
    assert raw["scratch_summary"] == {
        "integrity_ok": True,
        "cleanup_records": 96,
        "cleanup_failures": 0,
        "peak_cell_workspace_bytes": 161_144_484,
        "peak_per_worker_workspace_bytes": 161_144_484,
        "retained_workspace_bytes_after_cleanup": 0,
    }
    assert raw["run_failure"] is None
    assert raw["summary"]["primary_gate"] == {
        "conditions": {
            "execution_integrity": True,
            "correctness": True,
            "first_check": True,
            "tokens": True,
            "elapsed": True,
            "maintainability": True,
        },
        "passed": True,
    }


def test_fullstack_044_audit_recomputes_portably(tmp_path):
    output = tmp_path / "audit.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARKS / "audit_fullstack_agent_044.py"),
            "--skip-external",
            "--output",
            str(output),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    audit = json.loads(output.read_text(encoding="utf-8"))
    assert audit["audit_pass"] is True
    assert audit["external_evidence_verified"] is False
    assert audit["matrix"]["cells"] == 96
    assert audit["hidden"]["named_case_passes"] == 480
    assert audit["public"]["attempts"] == 97
    assert audit["exact_build"] == {
        "commands": 290,
        "successful_commands": 290,
        "stable_hash_checks": 290,
    }
    assert all(audit["primary_gate"]["conditions"].values())
    assert audit["primary_gate"]["passed"] is True


def test_fullstack_044_committed_audit_verified_external_evidence():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))

    assert sha256(AUDIT) == (
        "a9f875c07f95333eeb3436de374bfe3b321480081625e311eeac950580f50c54"
    )
    assert audit["audit_pass"] is True
    assert audit["external_evidence_verified"] is True
    assert audit["matrix"] == {
        "cells": 96,
        "unique_cell_ids": 96,
        "unique_thread_ids": 96,
        "journal_pairs_verified": 96,
        "cleanup_records_verified": 96,
        "attempt_files_verified": 97,
    }
    assert audit["comparisons"]["parley_tokens_vs_python_percent"] == -1.0072
    assert audit["comparisons"]["parley_elapsed_vs_python_percent"] == -12.5438
    assert audit["by_configuration"]["terra-medium"]["parley"][
        "median_elapsed_seconds"
    ] == 23.4006
    assert audit["by_configuration"]["terra-medium"]["python"][
        "median_elapsed_seconds"
    ] == 25.42465
    assert audit["median_final_source"]["parley"]["o200k_base_tokens"] == 779.0
