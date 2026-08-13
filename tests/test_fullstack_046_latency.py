import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
ANALYZER = BENCHMARKS / "analyze_fullstack_agent_046_latency.py"
LATENCY = BENCHMARKS / "fullstack_agent_046_latency.json"
REPORT = BENCHMARKS / "FULLSTACK_AGENT_046_LATENCY.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_046_latency_artifact_preserves_result_boundary():
    latency = json.loads(LATENCY.read_text())
    assert sha256(LATENCY) == (
        "d02880e5982248bc82f5a9bec845525bd8bbdee257cef3a369586b08e8f47a04"
    )
    assert latency["raw_sha256"] == (
        "0117effbc633affb6d79d14e8f1b713634ca3c5c263537e1ba2207b7ccaf2d07"
    )
    assert latency["interpretation"]["frozen_gate_unchanged"] is True
    assert latency["bootstrap"] == {
        "seed": 460260814,
        "samples": 50_000,
        "unit": "matched task/configuration/replicate pair",
    }


def test_fullstack_046_latency_findings_are_frozen():
    comparison = json.loads(LATENCY.read_text())["parley_vs_python"]
    assert comparison["marginal_median"] == {
        "elapsed_difference_seconds": 4.7767,
        "elapsed_percent": 16.5424,
        "public_check_difference_seconds": 0.8259,
        "public_build_difference_seconds": 0.91,
        "noncheck_difference_seconds": 2.8132,
    }
    paired = comparison["matched_pairs"]
    assert (paired["pairs"], paired["parley_faster"], paired["python_faster"]) == (
        24, 13, 11,
    )
    assert paired["elapsed_difference_seconds"]["median"] == -0.5204
    assert paired["elapsed_difference_seconds"][
        "bootstrap_median_95_percent_interval"
    ] == [-10.2032, 2.3991]
    assert paired["public_build_difference_seconds"]["median"] == 0.9042
    assert paired["noncheck_difference_seconds"]["median"] == -1.0202
    assert paired["total_token_difference"]["parley_no_higher_pairs"] == 15
    assert paired["two_sided_sign_test_p"] == 0.83882


def test_fullstack_046_latency_analysis_is_deterministic(tmp_path):
    output = tmp_path / "latency.json"
    completed = subprocess.run(
        [sys.executable, str(ANALYZER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == LATENCY.read_bytes()


def test_fullstack_046_latency_report_states_noncausal_boundary():
    report = REPORT.read_text()
    assert "does not revise the frozen gate" in report
    assert "cannot attribute" in report
    assert "scheduled separately" in report
    assert "does not establish universal language superiority" in report
