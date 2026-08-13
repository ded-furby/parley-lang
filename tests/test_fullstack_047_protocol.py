import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
PROTOCOL = BENCHMARKS / "fullstack_agent_047_protocol.json"
BUILDER = BENCHMARKS / "freeze_fullstack_agent_047_protocol.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_047_protocol_preregisters_product_matrix_and_gate():
    assert sha256(PROTOCOL) == (
        "c0434ac473d014beaca6e3d2b0c3577023dd6402db13257b58e17ee60d398a1f"
    )
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    product = protocol["frozen_product"]
    assert protocol["schema_version"] == 1
    assert protocol["protocol_revision"] == 1
    assert protocol["experiment_id"] == "047"
    assert product["parley_version"] == "parley 0.5.7"
    assert product["product_commit"] == "c9e8c9bea770c9243ac244663c28209bb18264df"
    assert product["corpus_commit"] == "32017e311379d007481c7c52a06f652a76830aea"
    for file_key, hash_key in (
        ("tasks_file", "tasks_sha256"),
        ("cases_file", "cases_sha256"),
        ("parley_context_file", "parley_context_sha256"),
        ("context_freeze_file", "context_freeze_sha256"),
        ("product_freeze_file", "product_freeze_sha256"),
        ("json_evidence_file", "json_evidence_sha256"),
        ("path_protocol_file", "path_protocol_sha256"),
        ("path_result_file", "path_result_sha256"),
    ):
        assert sha256(REPO / product[file_key]) == product[hash_key]
    assert product["parley_context_o200k_tokens"] == 176
    assert product["frozen_path_parameter_tests"] == 21
    assert product["frozen_full_regression_tests"] == 727

    assert protocol["matrix"]["fresh_sessions"] == 32
    assert protocol["matrix"]["frozen_public_case_executions_across_first_checks"] == 160
    assert protocol["matrix"]["hidden_case_executions"] == 160
    assert protocol["frozen_config"]["languages"] == [
        "parley", "python", "typescript", "rust",
    ]
    assert protocol["frozen_config"]["agent_configurations"] == [
        {"id": "sol-medium", "model": "gpt-5.6-sol", "reasoning": "medium"}
    ]
    assert protocol["frozen_config"]["replicates_per_task_language_configuration"] == 2
    assert protocol["frozen_config"]["seed"] == 470260813
    assert protocol["frozen_config"]["max_public_check_attempts"] == 8
    assert set(protocol["primary_gate"]) == {
        "execution_integrity", "correctness", "first_check", "tokens",
        "elapsed", "maintainability", "verdict",
    }
    assert "complete input-plus-output" in protocol["primary_gate"]["tokens"]
    assert "lowest baseline" in protocol["primary_gate"]["elapsed"]
    assert "cannot prove universal" in " ".join(protocol["interpretation_boundary"])


def test_fullstack_047_protocol_blocks_measurement_until_revision_2():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    execution = protocol["execution_freeze"]
    assert execution["status"] == "pending post-protocol harness implementation"
    assert execution["measured_sessions_before_freeze"] == 0
    assert execution["required_revision"] == 2
    assert len(execution["requirements"]) == 7
    assert "No measured session may start" in execution["prohibition"]
    assert "decoded captures" in execution["requirements"][2]
    assert "committed in revision 2" in protocol["implementation_rule"]
    assert "outside iteration 047" in protocol["stop_rule"]


def test_fullstack_047_protocol_builder_is_deterministic(tmp_path):
    output = tmp_path / "protocol.json"
    completed = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == PROTOCOL.read_bytes()
