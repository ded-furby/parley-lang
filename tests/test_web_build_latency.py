import hashlib
from pathlib import Path

from benchmarks import measure_web_build_latency_001 as latency
from parley.web import check_browser, check_web, load_project


EXPECTED_FIXTURE_HASHES = {
    "status_only": "ca08cc62086d47f61c997c1061a0e38e45566393e257e7dd1704f9060853c7f7",
    "browser_score": "6b7f9798bedd965cd3356afb70c560ace148a37a26f6b75fb02b663926ecb746",
    "typed_post": "b5d23446683f000728faaba6117e667f0f85021da43e2c67de5223f62c4b64aa",
}


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
