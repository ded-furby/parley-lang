import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
FREEZER = REPO / "benchmarks/freeze_fullstack_agent_048_product.py"
PRODUCT = REPO / "benchmarks/fullstack_agent_048_product.json"


def test_fullstack_048_product_freeze_has_zero_corpus_and_sessions():
    payload = json.loads(PRODUCT.read_text())
    assert payload["experiment_id"] == "048"
    assert payload["parley"]["version"] == "0.5.8"
    assert payload["context"]["o200k_base_tokens"] == 217
    assert payload["corpus_selected_before_freeze"] is False
    assert payload["measured_sessions_before_freeze"] == 0
    assert payload["previous_study_boundary"]["selective_rerun"] is False
    assert payload["previous_study_boundary"]["same_corpus_reuse"] is False


def test_fullstack_048_product_freezer_is_deterministic(tmp_path):
    output = tmp_path / "product.json"
    completed = subprocess.run(
        [sys.executable, str(FREEZER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == PRODUCT.read_bytes()


def test_fullstack_048_product_binds_query_and_previous_evidence():
    payload = json.loads(PRODUCT.read_text())
    product = payload["files"]["product"]
    assert "benchmarks/WEB_QUERY_PARAMETERS_005_RESULT.md" in product
    assert "tests/test_web_query_parameters_005.py" in product
    previous = payload["previous_study_boundary"]["files"]
    assert previous["benchmarks/fullstack_agent_047_raw.json"] == (
        "f04515b84abfbb2a3fe0477c7d0d5c5de9eba8a6f4de3eba2cf062886e779d28"
    )
    assert previous["benchmarks/fullstack_agent_047_attribution.json"] == (
        "a9ee9b9961c408cef70ccd6bec6bfa23995abdea5fdf761080988c957f420865"
    )
