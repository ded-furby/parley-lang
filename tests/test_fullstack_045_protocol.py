import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
PROTOCOL = BENCHMARKS / "fullstack_agent_045_protocol.json"
BUILDER = BENCHMARKS / "freeze_fullstack_agent_045_protocol.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_045_protocol_preregisters_product_matrix_and_gate():
    assert sha256(PROTOCOL) == (
        "04bb01b863d32bf3ba0e52cccd2515d77cc122ca0bb36f8ae17538cb91ec0de3"
    )
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    product = protocol["frozen_product"]
    assert protocol["schema_version"] == 1
    assert protocol["protocol_revision"] == 2
    assert protocol["experiment_id"] == "045"
    assert product["parley_version"] == "parley 0.5.6"
    assert product["product_commit"] == (
        "6bae1149d101d5a483f31f55905083e0a939c1da"
    )
    assert product["corpus_commit"] == (
        "3f3a5943532cd63a151ec8221715f75ab352a931"
    )
    for file_key, hash_key in (
        ("tasks_file", "tasks_sha256"),
        ("cases_file", "cases_sha256"),
        ("parley_context_file", "parley_context_sha256"),
        ("context_freeze_file", "context_freeze_sha256"),
        ("product_freeze_file", "product_freeze_sha256"),
        ("response_protocol_file", "response_protocol_sha256"),
    ):
        assert sha256(REPO / product[file_key]) == product[hash_key]
    assert product["parley_context_o200k_tokens"] == 313
    assert product["frozen_response_control_tests"] == 14
    assert product["frozen_full_regression_tests"] == 643

    assert protocol["matrix"]["fresh_sessions"] == 96
    assert protocol["matrix"]["hidden_case_executions"] == 480
    assert protocol["frozen_config"]["languages"] == [
        "parley", "python", "typescript", "rust",
    ]
    assert protocol["frozen_config"]["agent_configurations"] == [
        {"id": "sol-medium", "model": "gpt-5.6-sol", "reasoning": "medium"},
        {"id": "terra-medium", "model": "gpt-5.6-terra", "reasoning": "medium"},
    ]
    assert protocol["frozen_config"]["replicates_per_task_language_configuration"] == 3
    assert protocol["frozen_config"]["seed"] == 450260813
    assert set(protocol["primary_gate"]) == {
        "execution_integrity", "correctness", "first_check", "tokens",
        "elapsed", "maintainability", "verdict",
    }
    assert "custom-header" in protocol["primary_gate"]["correctness"]
    assert "complete input-plus-output" in protocol["primary_gate"]["tokens"]
    assert "separately within each agent configuration" in protocol[
        "primary_gate"]["elapsed"]


def test_fullstack_045_protocol_freezes_validated_zero_session_execution():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    execution = protocol["execution_freeze"]
    assert execution["measured_sessions_before_freeze"] == 0
    assert execution["protocol_revision_1_sha256"] == (
        "0de1f0048d99a94d08a3b0419bca646da6eaae74c2dd8e2f2fc9da1d7345da5b"
    )
    assert execution["harness_commit"] == (
        "58aaf262bffa97a28a0a23cb310de45c9fd59719"
    )
    assert execution["reference_cells_passed"] == 16
    assert execution["seed_cells_built"] == 16
    assert execution["seed_cells_correct"] == 0
    assert execution["maintenance_root_boundaries_passed"] == 8
    assert execution["named_reference_case_executions"] == 144
    assert execution["calibrated_max_workspace_bytes"] == 161230321
    assert execution["application_header_judgment"].startswith(
        "Compare the complete normalized multiset"
    )
    assert all(
        sha256(REPO / item["file"]) == item["sha256"]
        for item in execution["files"]
    )
    assert "does not pre-reject negative integers" in protocol[
        "session_protocol"]["domain_judgment"]
    assert protocol["scratch_space_control"]["required_free_bytes"] == 16 * 1024**3
    assert protocol["scratch_space_control"]["max_workers"] == 4
    assert "only after this protocol commit" in protocol["implementation_rule"]
    assert "outside iteration 045" in protocol["stop_rule"]


def test_fullstack_045_protocol_builder_is_deterministic(tmp_path):
    output = tmp_path / "protocol.json"
    completed = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert sha256(output) == protocol["execution_freeze"][
        "protocol_revision_1_sha256"
    ]
