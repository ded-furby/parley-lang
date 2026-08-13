import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from parley.web import check_browser, check_web, load_project


REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "benchmarks/measure_web_build_latency_002.py"
BASELINE = REPO / "benchmarks/web_build_latency_002_baseline.json"
CANDIDATE = REPO / "benchmarks/web_build_latency_002_candidate.json"
ANALYSIS = REPO / "benchmarks/web_build_latency_002_analysis.json"
ANALYZER = REPO / "benchmarks/analyze_web_build_latency_002.py"


def load_harness():
    spec = importlib.util.spec_from_file_location("web_build_latency_002", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_web_build_latency_002_population_is_frozen_and_distinct():
    harness = load_harness()

    assert list(harness.FIXTURES) == [
        "depot_overview",
        "orchard_batch",
        "weather_dispatch",
        "explicit_json_control",
    ]
    assert {
        name: harness.fixture_sha256(name) for name in harness.FIXTURES
    } == {
        "depot_overview": "88620befb8e6070919c7f49403e59c082f605305605d82dd864be3211a4e43ae",
        "orchard_batch": "933d950cb7b24ff426c5cbd2eadb51bb30962142eb3f9792f3ef6eafcc12b345",
        "weather_dispatch": "9b462bda84cfee3f655e1bb6e650e7281abc045f27a67a19be7483881eddbf9c",
        "explicit_json_control": "480a72e05ecea8a15f94a680c733b46acac9863de9ed502e901eb5db6558ff10",
    }
    assert sum(fixture["primary"] for fixture in harness.FIXTURES.values()) == 3
    assert harness.FIXTURES["explicit_json_control"]["primary"] is False
    assert " as json" in harness.FIXTURES["explicit_json_control"]["source"]

    names = [fixture["manifest"]["name"] for fixture in harness.FIXTURES.values()]
    paths = [
        route["path"]
        for fixture in harness.FIXTURES.values()
        for route in fixture["manifest"]["routes"]
    ]
    handlers = [
        route["handler"]
        for fixture in harness.FIXTURES.values()
        for route in fixture["manifest"]["routes"]
    ]
    assert len(names) == len(set(names))
    assert len(paths) == len(set(paths))
    assert len(handlers) == len(set(handlers))


def test_web_build_latency_002_fixtures_pass_contract_checks(tmp_path):
    harness = load_harness()

    for name, fixture in harness.FIXTURES.items():
        project = load_project(harness.write_fixture(tmp_path, name))
        checked = check_web(project)
        assert len(checked.routes) == len(fixture["manifest"]["routes"])
        browser = check_browser(project)
        assert (browser is not None) is fixture["browser"]


def test_web_build_latency_002_gate_is_not_weakened():
    harness = load_harness()

    source = HARNESS.read_text(encoding="utf-8")
    assert '"minimum_latency_improvement_percent": 20.0' in source
    assert '"maximum_fixture_regression_percent": 5.0' in source
    assert '"maximum_unjustified_size_increase_percent": 25.0' in source
    assert "universal superiority" in source


def test_web_build_latency_002_baseline_is_complete_and_frozen():
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    assert hashlib.sha256(BASELINE.read_bytes()).hexdigest() == (
        "b6c951d84f1754f0d7fa640379accbdf1e2dccf2a3af6c333a354d0080e8f62b"
    )
    assert baseline["toolchain"]["parley"] == "parley 0.5.4"
    assert baseline["toolchain"]["git_commit"] == (
        "3772eaa0a485f3c56334837c2459499d2de7d8bc"
    )
    assert len(baseline["cells"]) == 16
    assert all(cell["stderr"] == "" for cell in baseline["cells"])
    assert baseline["primary_median_of_fixture_medians_seconds"] == 2.72572
    assert baseline["by_fixture"]["explicit_json_control"][
        "median_elapsed_seconds"
    ] == 3.869316
    assert baseline["acceptance"] == {
        "minimum_latency_improvement_percent": 20.0,
        "maximum_fixture_regression_percent": 5.0,
        "maximum_unjustified_size_increase_percent": 25.0,
    }


def test_web_build_latency_002_candidate_passes_frozen_acceptance():
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))

    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == (
        "25efbcc80906060c3403c0e00852ff43ff8f7c0dcd4440c672613dbff9fdb9f7"
    )
    assert hashlib.sha256(ANALYSIS.read_bytes()).hexdigest() == (
        "fc00677316db8969dee86460899fb8d84ad0e5fb4cda9fafe3275305f2c19c40"
    )
    assert candidate["toolchain"]["parley"] == "parley 0.5.5"
    assert len(candidate["cells"]) == 16
    assert all(cell["stderr"] == "" for cell in candidate["cells"])
    assert candidate["primary_median_of_fixture_medians_seconds"] == 0.802735
    assert analysis["overall"] == {
        "baseline_primary_median_of_fixture_medians_seconds": 2.72572,
        "candidate_primary_median_of_fixture_medians_seconds": 0.802735,
        "primary_latency_improvement_percent": 70.5496,
        "maximum_fixture_regression_percent": -5.5866,
        "maximum_server_size_increase_percent": -3.2321,
        "maximum_wasm_size_increase_percent": 0.0,
    }
    assert analysis["verification"]["regression_tests_passed"] == 609
    assert analysis["acceptance"] == {
        "latency_threshold_percent": 20.0,
        "fixture_regression_ceiling_percent": 5.0,
        "size_ceiling_percent": 25.0,
        "latency_pass": True,
        "fixture_regression_pass": True,
        "size_pass": True,
        "regression_pass": True,
        "accepted": True,
    }


def test_web_build_latency_002_analysis_is_deterministic(tmp_path):
    output = tmp_path / "analysis.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(ANALYZER),
            "--verify-current-files",
            "--output",
            str(output),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == ANALYSIS.read_bytes()
