import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "fullstack_agent_046_raw.json"
AUDIT = BENCHMARKS / "fullstack_agent_046_audit.json"
REPORT = BENCHMARKS / "FULLSTACK_AGENT_046_RESULT.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_046_raw_is_complete_valid_and_gate_failed_only_elapsed():
    raw = json.loads(RAW.read_text())
    rows = raw["results"]
    assert sha256(RAW) == (
        "0117effbc633affb6d79d14e8f1b713634ca3c5c263537e1ba2207b7ccaf2d07"
    )
    assert len(rows) == len({row["cell_id"] for row in rows}) == 96
    assert len({row["thread_id"] for row in rows}) == 96
    assert sum(row["hidden_success"] for row in rows) == 96
    assert sum(row["first_public_check_success"] for row in rows) == 91
    assert sum(row["final_public_check_success"] for row in rows) == 96
    assert sum(row["repair_turns"] for row in rows) == 5
    assert all(row["attempt_record_integrity_ok"] for row in rows)
    assert all(row["workspace_integrity_ok"] for row in rows)
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


def test_fullstack_046_audit_recomputes_valid_result_portably(tmp_path):
    output = tmp_path / "audit.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARKS / "audit_fullstack_agent_046.py"),
            "--skip-external", "--output", str(output),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    audit = json.loads(output.read_text())
    assert audit["audit_pass"] is audit["study_valid"] is True
    assert audit["external_evidence_verified"] is False
    assert audit["json_evidence_boundary"]["integrity_cells"] == 96
    assert audit["hidden"]["named_case_passes"] == 480
    assert audit["public"]["attempts"] == 101
    assert audit["exact_build"] == {
        "commands": 294,
        "successful_commands": 293,
        "stable_hash_checks": 294,
    }


def test_fullstack_046_committed_audit_and_report_preserve_boundary():
    audit = json.loads(AUDIT.read_text())
    assert sha256(AUDIT) == (
        "5251e814218fc7b502e9e05c2fc6a13da6d3cdabe41906a9eb024e1b0e3ccbad"
    )
    assert audit["external_evidence_verified"] is True
    assert audit["primary_gate"]["passed"] is False
    assert audit["primary_gate"]["conditions"] == {
        "execution_integrity": True, "correctness": True,
        "first_check": True, "tokens": True,
        "elapsed": False, "maintainability": True,
    }
    assert audit["comparisons"]["parley_tokens_vs_python_percent"] == -0.3905
    assert audit["comparisons"]["parley_elapsed_vs_python_percent"] == 16.5424
    assert audit["structural_root_analysis_outside_primary_gate"]["parley"] == {
        "eligible": 12, "exact": 12,
    }
    report = REPORT.read_text()
    assert "valid / strict gate failed" in report
    assert "selective reruns" in report
    assert "does not" in report
    assert "any language—is universally best" in report
