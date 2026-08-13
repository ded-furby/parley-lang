import hashlib
import json
from pathlib import Path
import subprocess
import sys

from benchmarks import measure_web_build_latency_001 as latency
from parley.web import check_browser, check_web, load_project


EXPECTED_FIXTURE_HASHES = {
    "status_only": "ca08cc62086d47f61c997c1061a0e38e45566393e257e7dd1704f9060853c7f7",
    "browser_score": "6b7f9798bedd965cd3356afb70c560ace148a37a26f6b75fb02b663926ecb746",
    "typed_post": "b5d23446683f000728faaba6117e667f0f85021da43e2c67de5223f62c4b64aa",
}
BASELINE = latency.REPO / "benchmarks/web_build_latency_001_baseline.json"
CANDIDATE = latency.REPO / "benchmarks/web_build_latency_001_candidate.json"
ANALYSIS = latency.REPO / "benchmarks/web_build_latency_001_analysis.json"
ANALYZER = latency.REPO / "benchmarks/analyze_web_build_latency_001.py"


def test_web_build_latency_fixture_hashes_are_frozen():
    assert {
        name: latency.fixture_sha256(name) for name in latency.FIXTURES
    } == EXPECTED_FIXTURE_HASHES


def test_web_build_latency_population_is_non_042_and_checked(tmp_path):
    for name, fixture in latency.FIXTURES.items():
        project_root = latency.write_fixture(tmp_path, name)
        project = load_project(project_root)
        web = check_web(project)
        browser = check_browser(project)

        assert web.routes
        assert (browser is not None) is fixture["browser"]
        combined = b"".join(
            content for _relative, content in sorted(latency.fixture_files(name).items())
        )
        assert b"042" not in combined


def test_web_build_latency_protocol_is_bound_to_script():
    script = Path(latency.__file__)
    assert hashlib.sha256(script.read_bytes()).hexdigest()
    assert latency.DEFAULT_OUTPUT.name == "web_build_latency_001_result.json"


def test_web_build_latency_baseline_is_complete_and_frozen():
    assert hashlib.sha256(BASELINE.read_bytes()).hexdigest() == (
        "ba295fc3395491f83dfa5e93ad6ca9fac28407dbfa0f5097ff370817010ee05b"
    )
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    assert baseline["toolchain"]["parley"] == "parley 0.5.3"
    assert baseline["toolchain"]["git_commit"] == (
        "42c464a95245427918ee5e8e48a1fc1abf0a4e04"
    )
    assert baseline["fixture_sha256"] == EXPECTED_FIXTURE_HASHES
    assert baseline["repetitions"] == 4
    assert len(baseline["cells"]) == 12
    assert not any(row["stderr"] for row in baseline["cells"])
    assert baseline["median_of_fixture_medians_seconds"] == 3.855847


def test_web_build_latency_candidate_passes_frozen_acceptance():
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == (
        "2fca8256642b5e6e06f72b61c4b7f839b18fc13c657c6781015a4b507c726848"
    )
    assert hashlib.sha256(ANALYSIS.read_bytes()).hexdigest() == (
        "380c2309102acf570eebd94140d2106bdacebea87ebbebadf2d0c103fc80ee22"
    )
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))

    assert candidate["toolchain"]["parley"] == "parley 0.5.4"
    assert candidate["fixture_sha256"] == EXPECTED_FIXTURE_HASHES
    assert len(candidate["cells"]) == 12
    assert not any(row["stderr"] for row in candidate["cells"])
    assert candidate["median_of_fixture_medians_seconds"] == 2.63777
    assert analysis["overall"]["latency_improvement_percent"] == 31.5904
    assert analysis["overall"]["maximum_server_size_increase_percent"] == 0.0036
    assert analysis["overall"]["maximum_wasm_size_increase_percent"] == 0.0
    assert analysis["verification"]["regression_tests_passed"] == 585
    assert analysis["acceptance"] == {
        "latency_threshold_percent": 20.0,
        "size_ceiling_percent": 25.0,
        "latency_pass": True,
        "size_pass": True,
        "regression_pass": True,
        "accepted": True,
    }


def test_web_build_latency_analysis_is_deterministic(tmp_path):
    output = tmp_path / "analysis.json"
    completed = subprocess.run(
        [sys.executable, str(ANALYZER), "--output", str(output)],
        cwd=latency.REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == ANALYSIS.read_bytes()
