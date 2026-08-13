import importlib.util
from pathlib import Path

from parley.web import check_browser, check_web, load_project


REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "benchmarks/measure_web_build_latency_002.py"


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
