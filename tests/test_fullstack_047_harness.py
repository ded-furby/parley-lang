from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import threading

from benchmarks.fullstack_agent_047_guard import DomainGuard
from benchmarks.fullstack_agent_047_scaffolds import LANGUAGES, load_task_map
from benchmarks.prepare_fullstack_agent_047 import SOURCE_COMMIT, SOURCE_TREE
from benchmarks.run_fullstack_agent_047 import (
    CONTEXT_PATH,
    O200K,
    allocate_port,
    build_plan,
    command_protocol,
    load_cases,
    load_provenance,
    load_protocol,
    render_prompt,
    request,
    validate_corpus,
)


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"


def test_fullstack_047_plan_and_corpus_match_the_preregistered_budget():
    protocol = load_protocol()
    config = protocol["frozen_config"]
    tasks = list(load_task_map().values())
    assert validate_corpus() == {
        "tasks": 4,
        "cases": 40,
        "public_cases": 20,
        "hidden_cases": 20,
        "sessions": 32,
    }
    plan = build_plan(
        tasks,
        config["languages"],
        config["agent_configurations"],
        config["replicates_per_task_language_configuration"],
        config["seed"],
    )
    assert len(plan) == len({row["cell_id"] for row in plan}) == 32
    assert all(
        sum(row["language"] == language for row in plan) == 8
        for language in LANGUAGES
    )
    assert SOURCE_COMMIT == "c9e8c9bea770c9243ac244663c28209bb18264df"
    assert SOURCE_TREE == "c749b23a61ec360cd4ad33d5fd93dc700a278927"


def test_fullstack_047_prompt_uses_only_the_frozen_compact_context():
    context = CONTEXT_PATH.read_text(encoding="utf-8")
    cases = load_cases()
    for task in load_task_map().values():
        parley_prompt = render_prompt(task, cases[task["id"]], "parley", context)
        python_prompt = render_prompt(task, cases[task["id"]], "python", context)
        assert context.rstrip() in parley_prompt
        assert "# Frozen Parley scaffolded-web context" in parley_prompt
        assert task["parameter_route"] in parley_prompt
        assert task["exact_route"] in parley_prompt
        assert len(O200K.encode(parley_prompt)) - len(O200K.encode(python_prompt)) == 161


def test_fullstack_047_command_protocol_uses_the_eight_check_limit():
    assert command_protocol(
        [{"command": "./sources"}, {"command": "./check"}]
    )["compliant"] is True
    assert command_protocol(
        [{"command": "./sources"}] + [{"command": "./check"}] * 8
    )["compliant"] is True
    result = command_protocol(
        [{"command": "./sources"}] + [{"command": "./check"}] * 9
    )
    assert result["compliant"] is False
    assert result["violations"] == ["public check limit exceeded: 9 > 8"]


def test_fullstack_047_guard_preserves_raw_path_and_json_native_capture_evidence():
    observed: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            observed.append(self.path)
            body = b'{"probe_serial":"42"}'
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("x-probe-state", "catalogued")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    proxy_port = allocate_port()
    guard = DomainGuard(load_task_map()["tundra_probe_lookup_build"], int(upstream.server_address[1]), proxy_port)
    guard.start()
    try:
        result = request(proxy_port, {
            "method": "GET",
            "path": "/api/v11/tundra-probes/%34%32",
            "expected_status": 200,
            "expected_json": {"probe_serial": "42"},
            "expected_headers": {"x-probe-state": "catalogued"},
            "expected_path_parameters": {"probe_serial": "42"},
        })
    finally:
        guard.stop()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)
    assert result["pass"] is True
    assert result["request_path"] == "/api/v11/tundra-probes/%34%32"
    assert result["expected_path_parameters"] == {"probe_serial": "42"}
    assert result["path_parameters"] == {"probe_serial": "42"}
    assert observed == ["/api/v11/tundra-probes/%34%32"]


def test_fullstack_047_revision_2_records_the_zero_session_unlock_boundary():
    protocol = json.loads(
        (BENCHMARKS / "fullstack_agent_047_protocol.json").read_text()
    )
    assert protocol["protocol_revision"] == 2
    assert protocol["execution_freeze"]["measured_sessions_before_freeze"] == 0
    assert protocol["execution_freeze"]["named_reference_case_executions"] == 160


def test_fullstack_047_provenance_and_reference_validation_are_complete():
    provenance_path = BENCHMARKS / "fullstack_agent_047_provenance.json"
    validation_path = BENCHMARKS / "fullstack_agent_047_validation.json"
    provenance = load_provenance(
        provenance_path, "/private/tmp/parley-fullstack-047-parley/bin/parley"
    )
    validation = json.loads(validation_path.read_text())
    assert provenance["experiment_id"] == "047"
    assert provenance["parley"]["reported_version"] == "parley 0.5.7"
    assert validation["protocol_sha256"] == (
        "c0434ac473d014beaca6e3d2b0c3577023dd6402db13257b58e17ee60d398a1f"
    )
    assert validation["provenance_sha256"] == hashlib.sha256(
        provenance_path.read_bytes()
    ).hexdigest()
    assert validation["reference_cells_passed"] == 16
    assert validation["seed_cells_built"] == 16
    assert validation["seed_cells_correct"] == 0
    assert validation["maintenance_root_boundaries_passed"] == 8
    assert len(validation["cells"]) == 16
    assert sum(row["reference_cases"] for row in validation["cells"]) == 160
    assert all(row["reference_post_build_integrity"] for row in validation["cells"])
    assert all(row["seed_post_build_integrity"] for row in validation["cells"])
    assert validation["peak_validation_workspace_bytes"] == max(
        max(row["reference_workspace_bytes"], row["seed_workspace_bytes"])
        for row in validation["cells"]
    )
    assert validation["peak_validation_workspace_bytes"] < 2 * 1024**3


def test_fullstack_047_orchestration_smoke_persists_routing_evidence():
    smoke = json.loads(
        (BENCHMARKS / "fullstack_agent_047_orchestration_smoke.json").read_text()
    )
    assert smoke["experiment_id"] == "047"
    assert smoke["task_id"] == "tundra_probe_lookup_build"
    assert smoke["commands"] == [
        {"command": "./sources", "returncode": 0},
        {"command": "./check", "returncode": 1},
    ]
    assert smoke["public"]["case_count"] == smoke["hidden"]["case_count"] == 5
    assert smoke["public"]["http_cases"] == 4
    assert smoke["hidden"]["http_cases"] == 3
    controls = smoke["json_evidence_controls"]
    assert controls["broker_attempt_exact"] is True
    assert controls["empty"] == {"live": [], "persisted": []}
    assert controls["custom"]["live"] == controls["custom"]["persisted"] == [
        ["x-access-denial", "tundra_pass"]
    ]
    assert controls["duplicate"]["live"] == controls["duplicate"]["persisted"] == [
        ["x-repeat", "alpha"], ["x-repeat", "beta"]
    ]
    assert controls["routing"] == {
        "live_path": "/api/v11/tundra-probes/18",
        "persisted_path": "/api/v11/tundra-probes/18",
        "live_path_parameters": {"probe_serial": "18"},
        "persisted_path_parameters": {"probe_serial": "18"},
    }
    assert controls["json_native_shape"] is controls["pass"] is True
    assert smoke["pass"] is True
