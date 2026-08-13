import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "fullstack_agent_041_raw.json"
AUDIT = BENCHMARKS / "fullstack_agent_041_audit.json"
REPORT = (
    BENCHMARKS
    / "reports/041-independent-fullstack-study-gate-not-met.artifact.json"
)
ATTRIBUTION = BENCHMARKS / "fullstack_agent_041_token_attribution.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_041_raw_result_is_complete_clean_and_gate_not_met():
    raw = json.loads(RAW.read_text())
    rows = raw["results"]

    assert sha256(RAW) == (
        "37c27539e9003a7a28bc82b58bdc70fd9f0538a1dd5dc0ab6aa5ff6a6ffff65d"
    )
    assert len(rows) == len({row["cell_id"] for row in rows}) == 96
    assert len({row["thread_id"] for row in rows}) == 96
    assert sum(row["hidden_success"] for row in rows) == 96
    assert sum(row["first_public_check_success"] for row in rows) == 95
    assert sum(row["repair_turns"] for row in rows) == 1
    assert len(raw["journal"]) == 96
    assert all(entry["cleanup"]["status"] == "removed" for entry in raw["journal"])
    assert raw["scratch_summary"]["integrity_ok"] is True
    assert raw["scratch_summary"]["cleanup_failures"] == 0
    assert raw["scratch_summary"]["retained_workspace_bytes_after_cleanup"] == 0
    assert raw["run_failure"] is None
    assert raw["summary"]["primary_gate"] == {
        "conditions": {
            "execution_integrity": True,
            "correctness": True,
            "first_check": True,
            "tokens": False,
            "elapsed": True,
            "maintainability": True,
        },
        "passed": False,
    }


def test_fullstack_041_audit_recomputes_portably(tmp_path):
    output = tmp_path / "audit.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARKS / "audit_fullstack_agent_041.py"),
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
    audit = json.loads(output.read_text())
    assert audit["audit_pass"] is True
    assert audit["external_evidence_verified"] is False
    assert audit["matrix"]["cells"] == 96
    assert audit["hidden"]["named_case_passes"] == 480
    assert audit["exact_build"] == {
        "commands": 290,
        "successful_commands": 290,
        "stable_hash_checks": 290,
    }
    assert audit["primary_gate"]["conditions"]["tokens"] is False


def test_fullstack_041_committed_audit_verified_external_evidence():
    audit = json.loads(AUDIT.read_text())

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
    assert audit["comparisons"]["parley_tokens_vs_python_percent"] == 4.9091
    assert audit["comparisons"]["parley_elapsed_vs_python_percent"] == -1.489
    assert audit["median_final_source"]["parley"]["o200k_base_tokens"] == 701.0


def test_fullstack_041_report_preserves_gate_and_claim_boundary():
    report = json.loads(REPORT.read_text())

    assert report["surface"] == "report"
    assert report["snapshot"]["status"] == "ready"
    assert report["manifest"]["title"] == (
        "Independent Full-Stack Agent Study — Iteration 041"
    )
    datasets = report["snapshot"]["datasets"]
    assert len(datasets["languages"]) == 4
    assert len(datasets["configurations"]) == 8
    assert [row["result"] for row in datasets["gates"]] == [
        "PASS", "PASS", "PASS", "FAIL", "PASS", "PASS"
    ]
    assert datasets["headline"][0] == {
        "conditions_passed": 5,
        "conditions_total": 6,
        "hidden_assignments_passed": 96,
        "hidden_assignments_total": 96,
        "parley_first_checks": 24,
        "parley_first_check_total": 24,
        "token_gap_percent": 4.9091,
        "elapsed_advantage_percent": 1.489,
    }
    claim = next(
        block for block in report["manifest"]["blocks"]
        if block["id"] == "claim_boundary"
    )
    assert "does **not** establish" in claim["body"]
    assert "neither universal language superiority" in claim["body"]


def test_fullstack_041_report_builder_is_deterministic():
    before = sha256(REPORT)
    completed = subprocess.run(
        [sys.executable, str(BENCHMARKS / "reports/build_041_report.py")],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert sha256(REPORT) == before


def test_fullstack_041_token_attribution_uses_all_pairs_and_preserves_boundary(
    tmp_path,
):
    output = tmp_path / "attribution.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARKS / "analyze_fullstack_agent_041_tokens.py"),
            "--output",
            str(output),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == ATTRIBUTION.read_bytes()
    attribution = json.loads(output.read_text())
    assert len(attribution["matched_pairs"]) == 24
    assert attribution["paired_parley_minus_python"]["input_tokens"]["median"] == 3309.0
    assert attribution["paired_parley_minus_python"]["output_tokens"]["median"] == -254.0
    assert attribution["frozen_prompt_difference"][
        "constant_extra_prompt_o200k_tokens"
    ] == 1154
    assert attribution["counterfactual_diagnostic"][
        "three_prompt_repetitions_removed_parley_median"
    ] == 60103.5
    assert "not measured alternative outcomes" in attribution[
        "counterfactual_diagnostic"
    ]["interpretation"]
    assert "remains gate-not-met" in attribution["claim_boundary"]
