import importlib.util
import json
from pathlib import Path

from parley.web import check_browser, check_web, load_project


REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "benchmarks/measure_web_build_backend_003.py"


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
