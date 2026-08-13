import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS = BENCHMARKS / "fullstack_agent_046_tasks.json"
CASES = BENCHMARKS / "fullstack_agent_046_cases.json"
BUILDER = BENCHMARKS / "freeze_fullstack_agent_046_corpus.py"

sys.path.insert(0, str(BENCHMARKS))
from freeze_fullstack_agent_046_corpus import oracle, outcome  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prior_documents():
    tasks, cases = [], []
    for experiment in range(36, 46):
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


def test_fullstack_046_corpus_is_disjoint_and_response_controlled():
    assert sha256(TASKS) == (
        "37588deca94b4e24dc633a705487db6a637380ff3c9a19475bdf69ef92e69091"
    )
    assert sha256(CASES) == (
        "8774d5804d45a6bb44aee24910dea0bf1c29046fbe87aadd100524edf448603c"
    )
    task_document = json.loads(TASKS.read_text())
    case_document = json.loads(CASES.read_text())
    assert task_document["schema_version"] == case_document["schema_version"] == 1
    assert task_document["experiment_id"] == case_document["experiment_id"] == "046"
    assert task_document["product_freeze_commit"] == (
        "d6ab7e114574c8f9e5c2aa2dd9e9b7efeb7cdb8e"
    )
    assert task_document["product_freeze_sha256"] == (
        "1dab21f26a2f49f8c398840816f1780dd51172cc66baff0c270c95fd2e805ce2"
    )
    assert task_document["common_contract"]["response_envelope"] == {
        "status_field": "status", "headers_field": "headers", "body_field": "body",
    }
    tasks = task_document["tasks"]
    assert [task["kind"] for task in tasks] == [
        "implementation", "implementation", "maintenance", "maintenance",
    ]

    prior_tasks, prior_cases = prior_documents()
    for name in ("id", "status_route", "post_route", "browser_export"):
        assert {task[name] for task in tasks}.isdisjoint(task[name] for task in prior_tasks)
    for name in ("request_fields", "response_fields"):
        current = {field for task in tasks for field in task[name]}
        prior = {field for task in prior_tasks for field in task[name]}
        assert current.isdisjoint(prior)
        assert len(current) == sum(len(task[name]) for task in tasks)

    all_ids = []
    statuses = set()
    headers = set()
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
        all_ids.extend(row["id"] for row in rows)

        if task["kind"] == "maintenance":
            assert task["root_cause_role"] == "route_handler"
            assert task["predeclared_defect"]

        for row in rows:
            if row["target"] == "browser":
                browser_value = dict(zip(task["browser_fields"], row["args"], strict=True))
                source = {
                    name: "browser" if kind == "text" else False if kind == "yesno" else 0
                    for name, kind in task["request_fields"].items()
                }
                source.update(browser_value)
                assert row["expected"] == oracle(task["id"], source)[
                    task["shared_result_field"]
                ]
                continue
            statuses.add(row["expected_status"])
            headers.update(row.get("expected_headers", {}))
            if row["method"] == "GET":
                assert row["expected_json"] == {"service": task["service"], "ready": True}
            elif "expected_json" in row:
                assert (
                    row["expected_status"], row["expected_headers"], row["expected_json"]
                ) == outcome(task, row["json"], row.get("request_headers", {}))
            else:
                assert row["expected_error"] in {
                    "invalid_json", "json_content_type_required", "body_too_large",
                }

    assert len(all_ids) == len(set(all_ids)) == 36
    assert set(all_ids).isdisjoint(row["id"] for row in prior_cases)
    assert {200, 201, 202, 207, 400, 401, 403, 409, 415, 422}.issubset(statuses)
    assert {
        "location", "www-authenticate", "retry-after", "x-access-denial",
        "x-validation", "x-conflict", "x-clearance-phase", "x-assay-phase",
        "x-transfer-phase", "x-enrollment-phase",
    }.issubset(headers)


def test_fullstack_046_maintenance_defects_are_publicly_observable():
    tasks = {task["id"]: task for task in json.loads(TASKS.read_text())["tasks"]}
    cases = json.loads(CASES.read_text())["tasks"]

    transfer = cases["archive_transfer_repair"][1]
    assert transfer["expected_status"] == 201
    assert transfer["expected_headers"]["x-transfer-phase"] == "shelved"
    assert "x-transfer-state" in tasks["archive_transfer_repair"]["predeclared_defect"]

    beacon = cases["beacon_enrollment_repair"][1]
    assert beacon["expected_status"] == 202
    assert beacon["expected_headers"]["retry-after"] == "4"
    assert "201" in tasks["beacon_enrollment_repair"]["predeclared_defect"]


def test_fullstack_046_frozen_formula_anchors_are_independently_auditable():
    cases = json.loads(CASES.read_text())["tasks"]
    orbital = cases["orbital_clearance_build"][1]
    assert orbital["expected_json"] == {
        "clearance_slug": "zenith-4", "payload_tally": 5,
        "transfer_effort": 62, "berth_allowance": 94,
        "approved_effort": 62, "spillover_effort": 0, "orbit_passes": 2,
        "clearance_rating": 74, "clearance_phase": "cleared",
    }
    assay = cases["estuary_assay_build"][1]
    assert assay["expected_json"]["assay_effort"] == 73
    assert assay["expected_json"]["assay_cycles"] == 3
    assert assay["expected_json"]["assay_rating"] == 97
    transfer_hidden = cases["archive_transfer_repair"][-1]
    assert transfer_hidden["args"] == [7, 4, 1, True]
    assert transfer_hidden["expected"] == 484
    beacon_hidden = cases["beacon_enrollment_repair"][-1]
    assert beacon_hidden["expected"] == 788


def test_fullstack_046_header_names_are_case_insensitive():
    task = json.loads(TASKS.read_text())["tasks"][0]
    value, expected_headers = json.loads(CASES.read_text())["tasks"][task["id"]][1][
        "json"
    ], {"X-ORBIT-CREDENTIAL": "orbit-046"}
    status, _, body = outcome(task, value, expected_headers)
    assert status == 207
    assert body["clearance_phase"] == "cleared"


def test_fullstack_046_corpus_builder_is_deterministic(tmp_path):
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
