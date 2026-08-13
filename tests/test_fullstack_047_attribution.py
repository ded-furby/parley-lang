import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
ANALYZER = BENCHMARKS / "analyze_fullstack_agent_047.py"
ATTRIBUTION = BENCHMARKS / "fullstack_agent_047_attribution.json"
REPORT = BENCHMARKS / "FULLSTACK_AGENT_047_ATTRIBUTION.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_047_attribution_is_frozen_and_preserves_result():
    attribution = json.loads(ATTRIBUTION.read_text())
    assert sha256(ATTRIBUTION) == (
        "a9ee9b9961c408cef70ccd6bec6bfa23995abdea5fdf761080988c957f420865"
    )
    assert attribution["raw_sha256"] == (
        "f04515b84abfbb2a3fe0477c7d0d5c5de9eba8a6f4de3eba2cf062886e779d28"
    )
    assert attribution["frozen_prompt_difference"][
        "constant_extra_prompt_o200k_tokens"
    ] == 161
    assert attribution["parley_vs_python"]["marginal_median"] == {
        "total_token_difference": 205.5,
        "total_token_percent": 0.3394,
        "elapsed_difference_seconds": 3.4404,
        "elapsed_percent": 11.4461,
        "public_check_difference_seconds": 1.0589,
        "public_build_difference_seconds": 0.9926,
        "noncheck_difference_seconds": 2.1158,
    }


def test_fullstack_047_matched_findings_and_sensitivity_are_frozen():
    attribution = json.loads(ATTRIBUTION.read_text())
    paired = attribution["parley_vs_python"]["matched_pairs"]
    assert paired["total_tokens"]["median"] == 384.5
    assert paired["total_tokens"]["bootstrap_median_95_percent_interval"] == [
        -88.0, 771.0,
    ]
    assert paired["total_tokens"]["two_sided_sign_test_p"] == 0.726562
    assert paired["reasoning_output_tokens"]["parley_higher_pairs"] == 8
    assert paired["public_build_seconds"]["parley_higher_pairs"] == 8
    assert paired["session_elapsed_seconds"][
        "bootstrap_median_95_percent_interval"
    ] == [-2.9256, 12.6811]
    sensitivity = attribution["redundant_check_sensitivity_outside_gate"]
    assert sensitivity["excluded_pair"] == {
        "task_id": "magma_core_lookup_build",
        "configuration_id": "sol-medium",
        "replicate": 1,
        "parley_public_check_attempts": 4,
        "python_public_check_attempts": 1,
        "all_attempts_succeeded": True,
    }
    assert sensitivity["by_language"]["parley"]["median_total_tokens"] == 60515.0
    assert sensitivity["by_language"]["python"]["median_total_tokens"] == 60551.0


def test_fullstack_047_attribution_is_deterministic(tmp_path):
    output = tmp_path / "attribution.json"
    completed = subprocess.run(
        [sys.executable, str(ANALYZER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == ATTRIBUTION.read_bytes()


def test_fullstack_047_attribution_report_preserves_noncausal_boundary():
    report = REPORT.read_text()
    assert "does not revise the frozen gate" in report
    assert "sensitivity analysis only" in report
    assert "cannot attribute" in report
    assert "same-corpus rerun" in report
    assert "universal language superiority" in report
