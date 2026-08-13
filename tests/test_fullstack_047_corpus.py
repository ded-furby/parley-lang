import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS = BENCHMARKS / "fullstack_agent_047_tasks.json"
CASES = BENCHMARKS / "fullstack_agent_047_cases.json"
BUILDER = BENCHMARKS / "freeze_fullstack_agent_047_corpus.py"

sys.path.insert(0, str(BENCHMARKS))
from freeze_fullstack_agent_047_corpus import exact_outcome, outcome, score  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prior_documents():
    tasks, cases = [], []
    for experiment in range(36, 47):
        tasks.extend(json.loads(
            (BENCHMARKS / f"fullstack_agent_{experiment:03d}_tasks.json").read_text()
        )["tasks"])
        cases.extend(
            row
            for rows in json.loads(
                (BENCHMARKS / f"fullstack_agent_{experiment:03d}_cases.json").read_text()
            )["tasks"].values()
            for row in rows
        )
    return tasks, cases


def test_fullstack_047_corpus_is_frozen_disjoint_and_path_focused():
    assert sha256(TASKS) == (
        "c7cc0680ad62b0e78ce4fb1fda306f3f48ae5018f18ffdf19ad6e6a9df418348"
    )
    assert sha256(CASES) == (
        "11f08afbede6825f455d630ca0507c7e6661fccb0110c95aab2df2a2f8d4a5c9"
    )
    task_document = json.loads(TASKS.read_text())
    case_document = json.loads(CASES.read_text())
    assert task_document["schema_version"] == case_document["schema_version"] == 1
    assert task_document["experiment_id"] == case_document["experiment_id"] == "047"
    assert task_document["product_freeze_commit"] == (
        "f1959a5247db7444c161340110ec1782faa3d2b7"
    )
    assert [task["kind"] for task in task_document["tasks"]] == [
        "implementation", "implementation", "maintenance", "maintenance",
    ]
    assert "Exact routes win" in task_document["common_contract"]["server"]
    assert "exactly once as UTF-8" in task_document["common_contract"]["path_safety"]

    prior_tasks, prior_cases = prior_documents()
    tasks = task_document["tasks"]
    for name in ("id", "status_route", "browser_export"):
        assert {task[name] for task in tasks}.isdisjoint(
            task[name] for task in prior_tasks
        )
    current_routes = {
        route
        for task in tasks
        for route in (task["status_route"], task["parameter_route"], task["exact_route"])
    }
    prior_routes = {
        route
        for task in prior_tasks
        for route in (
            task.get("status_route"), task.get("post_route"),
            task.get("parameter_route"), task.get("exact_route"),
        )
        if route
    }
    assert current_routes.isdisjoint(prior_routes)
    current_fields = {field for task in tasks for field in task["response_fields"]}
    prior_fields = {
        field
        for task in prior_tasks
        for group in (task.get("request_fields", {}), task.get("response_fields", {}))
        for field in group
    }
    assert current_fields.isdisjoint(prior_fields)
    assert len(current_fields) == 16

    rows = [row for cases in case_document["tasks"].values() for row in cases]
    assert len(rows) == len({row["id"] for row in rows}) == 40
    assert {row["id"] for row in rows}.isdisjoint(row["id"] for row in prior_cases)
    assert sum(row["visibility"] == "public" for row in rows) == 20
    assert sum(row["visibility"] == "hidden" for row in rows) == 20
    assert sum(row["target"] == "browser" for row in rows) == 12
    assert sum(row.get("expected_error") == "invalid_path_parameter" for row in rows) == 4


def test_fullstack_047_frozen_cases_match_the_independent_oracle():
    tasks = {task["id"]: task for task in json.loads(TASKS.read_text())["tasks"]}
    cases = json.loads(CASES.read_text())["tasks"]
    for task_id, rows in cases.items():
        task = tasks[task_id]
        for row in rows:
            if row["target"] == "browser":
                assert row["expected"] == score(task, *row["args"])
                continue
            if row["path"] == task["status_route"]:
                assert row["expected_json"] == {"service": task["service"], "ready": True}
                assert row["expected_path_parameters"] == {}
                continue
            if row["path"] == task["exact_route"]:
                expected_status, expected_headers, expected_body = exact_outcome(task)
                assert (row["expected_status"], row["expected_headers"], row["expected_json"]) == (
                    expected_status, expected_headers, expected_body
                )
                assert row["expected_path_parameters"] == {}
                continue
            if row.get("expected_error"):
                assert row["expected_status"] == 400
                continue
            capture = row["expected_path_parameters"][task["path_parameter"]]
            expected_status, expected_headers, expected_body = outcome(
                task, capture, row["request_headers"]
            )
            assert (row["expected_status"], row["expected_headers"], row["expected_json"]) == (
                expected_status, expected_headers, expected_body
            )

    invalid_paths = {
        row["path"]
        for rows in cases.values()
        for row in rows
        if row.get("expected_error") == "invalid_path_parameter"
    }
    assert any("%ZZ" in path for path in invalid_paths)
    assert any("%FF" in path for path in invalid_paths)
    assert any("%2F" in path for path in invalid_paths)
    assert any("%5C" in path for path in invalid_paths)


def test_fullstack_047_maintenance_defects_are_public_and_single_owner():
    tasks = {task["id"]: task for task in json.loads(TASKS.read_text())["tasks"]}
    cases = json.loads(CASES.read_text())["tasks"]
    band = tasks["aviary_band_lookup_repair"]
    gate = tasks["canal_gate_lookup_repair"]
    assert band["root_cause_role"] == gate["root_cause_role"] == "route_handler"
    assert "band_code" in band["predeclared_defect"]
    assert "raw request.path" in gate["predeclared_defect"]
    for task_id in ("aviary_band_lookup_repair", "canal_gate_lookup_repair"):
        primary = next(row for row in cases[task_id] if row["id"].endswith("_primary"))
        assert primary["visibility"] == "public"
        assert primary["target"] == "http"
        assert primary["expected_status"] == 200


def test_fullstack_047_header_names_are_case_insensitive():
    task = json.loads(TASKS.read_text())["tasks"][0]
    status, headers, body = outcome(
        task,
        "18",
        {"X-TUNDRA-PASS": "tundra-047", "X-CALIBRATION-MODE": "precision"},
    )
    assert status == 200
    assert headers == {"x-probe-state": "catalogued"}
    assert body["calibration_score"] == 243


def test_fullstack_047_corpus_builder_is_deterministic(tmp_path):
    tasks_output = tmp_path / "tasks.json"
    cases_output = tmp_path / "cases.json"
    completed = subprocess.run(
        [
            sys.executable, str(BUILDER), "--tasks-output", str(tasks_output),
            "--cases-output", str(cases_output),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert tasks_output.read_bytes() == TASKS.read_bytes()
    assert cases_output.read_bytes() == CASES.read_bytes()
