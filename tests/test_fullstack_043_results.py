import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "fullstack_agent_043_raw.json"
AUDIT = BENCHMARKS / "fullstack_agent_043_audit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_043_raw_result_is_complete_clean_and_gate_not_met():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    rows = raw["results"]

    assert sha256(RAW) == (
        "13ab8043bfb973a51d339838a90936b7ec4624fe2d2813e8c297954e958fb021"
    )
    assert len(rows) == len({row["cell_id"] for row in rows}) == 96
    assert len({row["thread_id"] for row in rows}) == 96
    assert sum(row["hidden_success"] for row in rows) == 96
    assert sum(row["first_public_check_success"] for row in rows) == 96
    assert sum(row["repair_turns"] for row in rows) == 0
    assert len(raw["journal"]) == 96
    assert all(entry["cleanup"]["status"] == "removed" for entry in raw["journal"])
    assert raw["scratch_summary"] == {
        "integrity_ok": True,
        "cleanup_records": 96,
        "cleanup_failures": 0,
        "peak_cell_workspace_bytes": 161_144_494,
        "peak_per_worker_workspace_bytes": 161_144_494,
        "retained_workspace_bytes_after_cleanup": 0,
    }
    assert raw["run_failure"] is None
    assert raw["summary"]["primary_gate"] == {
        "conditions": {
            "execution_integrity": True,
            "correctness": True,
            "first_check": True,
            "tokens": True,
            "elapsed": False,
            "maintainability": True,
        },
        "passed": False,
    }


def test_fullstack_043_audit_recomputes_portably(tmp_path):
    output = tmp_path / "audit.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARKS / "audit_fullstack_agent_043.py"),
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
    assert audit["exact_build"] == {
        "commands": 288,
        "successful_commands": 288,
        "stable_hash_checks": 288,
    }
    assert audit["primary_gate"]["conditions"]["tokens"] is True
    assert audit["primary_gate"]["conditions"]["elapsed"] is False


def test_fullstack_043_committed_audit_verified_external_evidence():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))

    assert sha256(AUDIT) == (
        "004f0dcf241b36512f327d0d588a569170309fe85097be1d407c9ef9a42411b8"
    )
    assert audit["audit_pass"] is True
    assert audit["external_evidence_verified"] is True
    assert audit["matrix"] == {
        "cells": 96,
        "unique_cell_ids": 96,
        "unique_thread_ids": 96,
        "journal_pairs_verified": 96,
        "cleanup_records_verified": 96,
        "attempt_files_verified": 96,
    }
    assert audit["comparisons"]["parley_tokens_vs_python_percent"] == -0.8253
    assert audit["comparisons"]["parley_elapsed_vs_python_percent"] == -1.6899
    assert audit["by_configuration"]["terra-medium"]["parley"][
        "median_elapsed_seconds"
    ] == 26.264699999999998
    assert audit["by_configuration"]["terra-medium"]["python"][
        "median_elapsed_seconds"
    ] == 25.5915
    assert audit["median_final_source"]["parley"]["o200k_base_tokens"] == 751.5
