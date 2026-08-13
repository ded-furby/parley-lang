import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from conftest import run_cli
from parley.cli import _map_rustc_errors
from parley.parser import parse_program
from parley.web import check_browser, check_web, load_project


REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "benchmarks/measure_web_build_backend_003.py"
BASELINE = REPO / "benchmarks/web_build_backend_003_baseline.json"
CANDIDATE = REPO / "benchmarks/web_build_backend_003_candidate.json"
ANALYSIS = REPO / "benchmarks/web_build_backend_003_analysis.json"
ANALYZER = REPO / "benchmarks/analyze_web_build_backend_003.py"


def load_harness():
    spec = importlib.util.spec_from_file_location("web_build_backend_003", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_web_build_backend_003_population_is_frozen_and_distinct():
    harness = load_harness()
    assert list(harness.FIXTURES) == [
        "harbor_admission",
        "forest_inventory",
        "glacier_manifest",
        "manual_json_control",
    ]
    assert sum(fixture["primary"] for fixture in harness.FIXTURES.values()) == 3
    assert harness.FIXTURES["manual_json_control"]["primary"] is False
    assert " as json" in harness.FIXTURES["manual_json_control"]["source"]
    assert sum(
        fixture["response_mode"] == "dynamic"
        for fixture in harness.FIXTURES.values()
    ) == 2

    historical = "\n".join(
        path.read_text(encoding="utf-8")
        for study in range(36, 47)
        for suffix in ("tasks.json", "cases.json")
        if (path := REPO / f"benchmarks/fullstack_agent_{study:03d}_{suffix}").is_file()
    )
    identifiers = [
        *harness.FIXTURES,
        *(fixture["manifest"]["name"] for fixture in harness.FIXTURES.values()),
        *(
            route["path"]
            for fixture in harness.FIXTURES.values()
            for route in fixture["manifest"]["routes"]
        ),
        *(
            route["handler"]
            for fixture in harness.FIXTURES.values()
            for route in fixture["manifest"]["routes"]
        ),
    ]
    assert all(identifier not in historical for identifier in identifiers)


def test_web_build_backend_003_fixture_hashes_are_frozen():
    harness = load_harness()
    assert {
        name: harness.fixture_sha256(name) for name in harness.FIXTURES
    } == {
        "harbor_admission": "7def72af37b813a90f9b993980c32da66ec44e0012571ad24a0d98806a914069",
        "forest_inventory": "216405e22242bfb1283b2ccd1ee3bd826caaaf08fae1daf4f71ca4ac308c96ce",
        "glacier_manifest": "55a604460f741037ad3e7dfefa994a1841928211bc09c6d1c6a4af6f619d7819",
        "manual_json_control": "ae6f86bfdc28ed1ee7fb30175fbb1bd3a70a1c052d7457abf53a8c3d32b6d365",
    }


def test_web_build_backend_003_fixtures_pass_contract_checks(tmp_path):
    harness = load_harness()
    for name, fixture in harness.FIXTURES.items():
        project = load_project(harness.write_fixture(tmp_path, name))
        checked = check_web(project)
        assert len(checked.routes) == len(fixture["manifest"]["routes"])
        browser = check_browser(project)
        assert (browser is not None) is fixture["browser"]


def test_web_build_backend_003_gate_is_frozen():
    source = HARNESS.read_text(encoding="utf-8")
    assert '"minimum_latency_improvement_percent": 20.0' in source
    assert '"maximum_fixture_regression_percent": 5.0' in source
    assert '"maximum_unjustified_size_increase_percent": 25.0' in source
    assert "cannot revise study 046" in source


def test_web_build_backend_003_baseline_is_complete_and_frozen():
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert hashlib.sha256(BASELINE.read_bytes()).hexdigest() == (
        "5588e490c22c74d5a9e9be8751438ea645341433d264b723b39594acc1dfb9f0"
    )
    assert baseline["study_id"] == "web-build-backend-003"
    assert baseline["toolchain"]["parley"] == "parley 0.5.6"
    assert baseline["toolchain"]["git_commit"] == (
        "d04acec70ffbed84381cb555652ca6e6eac2926d"
    )
    assert len(baseline["cells"]) == 16
    assert all(cell["stderr"] == "" for cell in baseline["cells"])
    assert baseline["primary_median_of_fixture_medians_seconds"] == 0.811446
    assert baseline["by_fixture"]["manual_json_control"][
        "median_elapsed_seconds"
    ] == 3.715876
    assert baseline["acceptance"] == {
        "minimum_latency_improvement_percent": 20.0,
        "maximum_fixture_regression_percent": 5.0,
        "maximum_unjustified_size_increase_percent": 25.0,
    }


def test_direct_rustc_diagnostics_keep_source_mapping(tmp_path):
    source = tmp_path / "main.par"
    source.write_text('say "ready"\n')
    _, srcmap = parse_program(source)
    raw = json.dumps({
        "$message_type": "diagnostic",
        "message": "mismatched types",
        "level": "error",
        "spans": [{"is_primary": True, "line_start": 9}],
    })
    diagnostics = _map_rustc_errors(raw, {9: 1}, srcmap)
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "P901"
    assert diagnostics[0].line == 1
    assert diagnostics[0].file == str(source)
    assert "mismatched types" in diagnostics[0].message


@pytest.mark.skipif(
    shutil.which("cargo") is None or shutil.which("rustc") is None,
    reason="Rust toolchain not installed",
)
def test_web_backend_uses_rustc_only_when_generated_code_has_no_dependencies(
    tmp_path,
):
    harness = load_harness()

    direct_project = harness.write_fixture(tmp_path, "forest_inventory")
    direct_bundle = tmp_path / "direct-bundle"
    direct = run_cli(
        ["web", "build", str(direct_project), "-o", str(direct_bundle)],
        cwd=tmp_path,
    )
    assert direct.returncode == 0, direct.stderr
    direct_roots = list((tmp_path / ".parley-build/web").glob("forest-inventory-*/"))
    assert len(direct_roots) == 1
    direct_root = direct_roots[0]
    assert (direct_root / "server/parley_web").is_file()
    assert (direct_root / "browser/parley_browser.wasm").is_file()
    assert not (direct_root / "server/Cargo.toml").exists()
    assert not (direct_root / "browser/Cargo.toml").exists()

    cargo_project = harness.write_fixture(tmp_path, "manual_json_control")
    cargo_bundle = tmp_path / "cargo-bundle"
    cargo = run_cli(
        ["web", "build", str(cargo_project), "-o", str(cargo_bundle)],
        cwd=tmp_path,
    )
    assert cargo.returncode == 0, cargo.stderr
    cargo_roots = list((tmp_path / ".parley-build/web").glob("manual-json-control-*/"))
    assert len(cargo_roots) == 1
    cargo_root = cargo_roots[0]
    assert (cargo_root / "server/Cargo.toml").is_file()
    assert not (cargo_root / "browser").exists()


def test_web_build_backend_003_candidate_is_valid_but_rejected():
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == (
        "ac161529241f770fed935b455da466f4f24b49e88e68b82ee109ea7011d8602b"
    )
    assert candidate["toolchain"]["parley"] == "parley 0.5.7"
    assert len(candidate["cells"]) == 16
    assert all(cell["stderr"] == "" for cell in candidate["cells"])
    assert analysis["overall"] == {
        "baseline_primary_median_of_fixture_medians_seconds": 0.811446,
        "candidate_primary_median_of_fixture_medians_seconds": 0.775853,
        "primary_latency_improvement_percent": 4.3864,
        "maximum_fixture_regression_percent": 1.5242,
        "maximum_server_size_increase_percent": 0.0,
        "maximum_wasm_size_increase_percent": 4.403,
    }
    assert analysis["acceptance"] == {
        "latency_threshold_percent": 20.0,
        "fixture_regression_ceiling_percent": 5.0,
        "size_ceiling_percent": 25.0,
        "latency_pass": False,
        "fixture_regression_pass": True,
        "size_pass": True,
        "regression_pass": True,
        "accepted": False,
    }
    assert analysis["decision"] == {
        "release_candidate": False,
        "restore_version": "0.5.6",
        "same_population_retuning": False,
        "reason": "The 4.3864% primary improvement is below the frozen 20% threshold.",
    }


def test_web_build_backend_003_analysis_is_deterministic(tmp_path):
    output = tmp_path / "analysis.json"
    completed = __import__("subprocess").run(
        [__import__("sys").executable, str(ANALYZER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == ANALYSIS.read_bytes()
