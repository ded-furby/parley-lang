import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "fullstack_agent_045_raw.json"
AUDIT = BENCHMARKS / "fullstack_agent_045_audit.json"
REPORT = BENCHMARKS / "FULLSTACK_AGENT_045_RESULT.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_045_raw_is_complete_and_frozen_gate_failed():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    rows = raw["results"]
    assert sha256(RAW) == (
        "521f706074526ec34a34d6cbba98ce4db427d1490433e8188b23094a7313e7f9"
    )
    assert len(rows) == len({row["cell_id"] for row in rows}) == 96
    assert len({row["thread_id"] for row in rows}) == 96
    assert sum(row["hidden_success"] for row in rows) == 96
    assert sum(row["first_public_check_success"] for row in rows) == 93
    assert sum(row["final_public_check_success"] for row in rows) == 96
    assert sum(row["repair_turns"] for row in rows) == 3
    assert all(not row["attempt_record_integrity_ok"] for row in rows)
    assert all(not row["workspace_integrity_ok"] for row in rows)
    assert raw["summary"]["primary_gate"] == {
        "conditions": {
            "execution_integrity": False,
            "correctness": True,
            "first_check": False,
            "tokens": False,
            "elapsed": False,
            "maintainability": False,
        },
        "passed": False,
    }


def test_fullstack_045_audit_recomputes_invalid_result_portably(tmp_path):
    output = tmp_path / "audit.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARKS / "audit_fullstack_agent_045.py"),
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
    assert audit["study_valid"] is False
    assert audit["external_evidence_verified"] is False
    assert audit["integrity_defect"]["affected_cells"] == 96
    assert audit["hidden"]["named_case_passes"] == 480
    assert audit["public"]["attempts"] == 99
    assert audit["exact_build"] == {
        "commands": 293,
        "successful_commands": 292,
        "stable_hash_checks": 293,
    }


def test_fullstack_045_committed_audit_and_report_preserve_boundary():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert sha256(AUDIT) == (
        "26c8b3ed87a68b50411c8f0232db9d848d6faab3aebf34f496596b66f2122f07"
    )
    assert audit["external_evidence_verified"] is True
    assert audit["primary_gate"]["passed"] is False
    assert audit["comparisons"]["parley_tokens_vs_python_percent"] == 0.9717
    assert audit["comparisons"]["parley_elapsed_vs_python_percent"] == 16.6501
    assert audit["structural_root_analysis_outside_primary_gate"]["parley"] == {
        "eligible": 12,
        "exact": 12,
    }
    report = REPORT.read_text(encoding="utf-8")
    assert "invalid / gate failed" in report
    assert "cannot be selectively rerun" in report
    assert "does not establish that any language is universally best" in report
