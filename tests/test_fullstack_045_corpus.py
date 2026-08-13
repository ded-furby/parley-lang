import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS = BENCHMARKS / "fullstack_agent_045_tasks.json"
CASES = BENCHMARKS / "fullstack_agent_045_cases.json"
BUILDER = BENCHMARKS / "freeze_fullstack_agent_045_corpus.py"

sys.path.insert(0, str(BENCHMARKS))
from freeze_fullstack_agent_045_corpus import oracle, outcome  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_045_corpus_is_disjoint_and_response_controlled():
    assert sha256(TASKS) == (
        "39c76f1a4a5e02d5afde27b8e010bc9fb5f75ea670a04c89063eb1cdb160aebb"
    )
    assert sha256(CASES) == (
        "99d255b2e49153a99900775ac3d947336abf7fb415ffb4186dc1c7b8710e755b"
    )
    task_document = json.loads(TASKS.read_text(encoding="utf-8"))
    case_document = json.loads(CASES.read_text(encoding="utf-8"))
    assert task_document["schema_version"] == case_document["schema_version"] == 1
    assert task_document["experiment_id"] == case_document["experiment_id"] == "045"
    assert task_document["product_freeze_commit"] == (
        "6b39eeffca34c7a9b05e1596eb8e8b4d3272a8e4"
    )
    assert task_document["product_freeze_sha256"] == (
        "49e1ee43ce014e3888a193442e426269f7bdf19b0403ab29a2b3a40505596216"
    )
    assert task_document["common_contract"]["response_envelope"] == {
        "status_field": "status", "headers_field": "headers", "body_field": "body",
    }
    tasks = task_document["tasks"]
    assert [task["kind"] for task in tasks] == [
        "implementation", "implementation", "maintenance", "maintenance",
    ]

    prior_tasks, prior_cases = [], []
    for experiment in range(36, 45):
        prior_tasks.extend(json.loads(
            (BENCHMARKS / f"fullstack_agent_{experiment:03d}_tasks.json").read_text()
        )["tasks"])
        prior_cases.extend(
            case
            for rows in json.loads(
                (BENCHMARKS / f"fullstack_agent_{experiment:03d}_cases.json").read_text()
            )["tasks"].values()
            for case in rows
        )

    def fields(rows, name):
        return {field for row in rows for field in row[name]}

    assert {task["id"] for task in tasks}.isdisjoint(task["id"] for task in prior_tasks)
    assert fields(tasks, "request_fields").isdisjoint(fields(prior_tasks, "request_fields"))
    assert fields(tasks, "response_fields").isdisjoint(fields(prior_tasks, "response_fields"))
    for name in ("status_route", "post_route", "browser_export"):
        assert {task[name] for task in tasks}.isdisjoint(task[name] for task in prior_tasks)

    all_case_ids = []
    statuses = set()
    custom_headers = set()
    for task in tasks:
        rows = case_document["tasks"][task["id"]]
        public = [row for row in rows if row["visibility"] == "public"]
        hidden = [row for row in rows if row["visibility"] == "hidden"]
        assert len(rows) == 9
        assert len(public) == 4 and len(hidden) == 5
        assert sum(row["target"] == "browser" for row in public) == 1
        assert sum(row["target"] == "browser" for row in hidden) == 2
        assert task["public_case_ids"] == [row["id"] for row in public]
        assert task["hidden_case_ids"] == [row["id"] for row in hidden]
        assert all(task["request_fields"][name] in {"number", "yesno"}
                   for name in task["browser_fields"])
        all_case_ids.extend(row["id"] for row in rows)
        if task["kind"] == "maintenance":
            assert task["root_cause_role"] == "route_handler"
            assert task["predeclared_defect"]

        for row in rows:
            if row["target"] == "browser":
                browser_value = dict(zip(task["browser_fields"], row["args"], strict=True))
                source = {
                    name: ("browser" if ty == "text" else False if ty == "yesno" else 0)
                    for name, ty in task["request_fields"].items()
                }
                source.update(browser_value)
                assert row["expected"] == oracle(task["id"], source)[
                    task["shared_result_field"]]
                continue
            statuses.add(row["expected_status"])
            custom_headers.update(row.get("expected_headers", {}))
            if row["method"] == "GET":
                assert row["expected_json"] == {"service": task["service"], "ready": True}
            elif "expected_json" in row:
                assert (row["expected_status"], row["expected_headers"], row["expected_json"]) == outcome(
                    task, row["json"], row.get("request_headers", {}))
            else:
                assert row["expected_error"] in {
                    "invalid_json", "json_content_type_required", "body_too_large",
                }

    assert len(all_case_ids) == len(set(all_case_ids)) == 36
    assert set(all_case_ids).isdisjoint(row["id"] for row in prior_cases)
    assert {200, 201, 202, 400, 401, 409, 415, 422}.issubset(statuses)
    assert {
        "location", "www-authenticate", "retry-after", "x-validation",
        "x-conflict", "x-accession-state", "x-bid-state", "x-permit-state",
        "x-booking-state",
    }.issubset(custom_headers)
    negative = next(
        row for row in case_document["tasks"]["cold_chain_booking_repair"]
        if row["id"] == "cold_chain_negative_crates"
    )
    assert negative["expected_status"] == 422
    assert negative["expected_headers"] == {"x-validation": "nonnegative"}


def test_fullstack_045_maintenance_defects_are_publicly_observable():
    tasks = {task["id"]: task for task in json.loads(TASKS.read_text())["tasks"]}
    cases = json.loads(CASES.read_text())["tasks"]

    trail = cases["trail_permit_repair"][1]
    assert trail["request_headers"]["authorization"] == "Bearer trail-045"
    assert trail["expected_status"] == 200
    assert "authorization-polarity" in tasks["trail_permit_repair"][
        "historical_grounding"]

    cold = cases["cold_chain_booking_repair"][1]
    assert cold["expected_status"] == 201
    assert cold["expected_headers"]["location"].endswith("/polar-8")
    assert "content-length" in tasks["cold_chain_booking_repair"]["predeclared_defect"]
    assert "server-owned" in tasks["cold_chain_booking_repair"][
        "historical_grounding"]


def test_fullstack_045_frozen_formula_anchors_are_independently_auditable():
    cases = json.loads(CASES.read_text())["tasks"]

    artifact = cases["artifact_accession_build"][1]
    assert artifact["expected_json"] == {
        "accession_key": "bronze-lyre", "artifact_total": 5,
        "packing_units": 48, "capacity_units": 80, "overflow_units": 0,
        "inspection_rounds": 1, "priority_score": 55,
        "accession_state": "accepted",
    }
    grid = cases["microgrid_bid_build"][1]
    assert grid["expected_json"]["grid_required_units"] == 67
    assert grid["expected_json"]["bid_score"] == 85
    assert grid["expected_headers"]["retry-after"] == "3"
    trail_hidden = cases["trail_permit_repair"][-1]
    assert trail_hidden["args"] == [8, 4, 1, True]
    assert trail_hidden["expected"] == 374
    cold_hidden = cases["cold_chain_booking_repair"][5]
    assert cold_hidden["expected_json"]["cooling_units"] == 100
    assert cold_hidden["expected_json"]["booking_score"] == 332


def test_fullstack_045_corpus_builder_is_deterministic(tmp_path):
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
