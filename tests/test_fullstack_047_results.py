import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "fullstack_agent_047_raw.json"
AUDIT = BENCHMARKS / "fullstack_agent_047_audit.json"
REPORT = BENCHMARKS / "FULLSTACK_AGENT_047_RESULT.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_047_raw_is_complete_valid_and_gate_failed_tokens_and_elapsed():
    raw = json.loads(RAW.read_text())
    rows = raw["results"]
    assert sha256(RAW) == (
        "f04515b84abfbb2a3fe0477c7d0d5c5de9eba8a6f4de3eba2cf062886e779d28"
    )
    assert len(rows) == len({row["cell_id"] for row in rows}) == 32
    assert len({row["thread_id"] for row in rows}) == 32
    assert sum(row["hidden_success"] for row in rows) == 32
    assert sum(row["first_public_check_success"] for row in rows) == 32
    assert sum(row["final_public_check_success"] for row in rows) == 32
    assert sum(row["repair_turns"] for row in rows) == 3
    assert all(row["attempt_record_integrity_ok"] for row in rows)
    assert all(row["workspace_integrity_ok"] for row in rows)
    assert raw["summary"]["primary_gate"] == {
        "conditions": {
            "execution_integrity": True,
            "correctness": True,
            "first_check": True,
            "tokens": False,
            "elapsed": False,
            "maintainability": True,
        },
        "passed": False,
    }


def test_fullstack_047_audit_recomputes_valid_result_portably(tmp_path):
    output = tmp_path / "audit.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARKS / "audit_fullstack_agent_047.py"),
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
    assert audit["json_evidence_boundary"]["integrity_cells"] == 32
    assert audit["hidden"]["named_case_passes"] == 160
    assert audit["public"]["attempts"] == 35
    assert audit["exact_build"] == {
        "commands": 99,
        "successful_commands": 99,
        "stable_hash_checks": 99,
    }


def test_fullstack_047_committed_audit_and_report_preserve_boundary():
    audit = json.loads(AUDIT.read_text())
    assert sha256(AUDIT) == (
        "0fc04897b4ba3a5e24c35b1b7d6235f1cde5835c005004a1f5a0fb2053182f5a"
    )
    assert audit["external_evidence_verified"] is True
    assert audit["primary_gate"]["passed"] is False
    assert audit["primary_gate"]["conditions"] == {
        "execution_integrity": True, "correctness": True,
        "first_check": True, "tokens": False,
        "elapsed": False, "maintainability": True,
    }
    assert audit["comparisons"]["parley_tokens_vs_python_percent"] == 0.3394
    assert audit["comparisons"]["parley_elapsed_vs_python_percent"] == 11.4461
    assert audit["structural_root_analysis_outside_primary_gate"]["parley"] == {
        "eligible": 4, "exact": 4,
    }
    report = REPORT.read_text()
    assert "valid / strict gate failed" in report
    assert "token and elapsed-time conditions" in report
    assert "selective reruns" in report
    assert "does not" in report
    assert "any language—is universally best" in report
