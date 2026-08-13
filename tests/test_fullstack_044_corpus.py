import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS = BENCHMARKS / "fullstack_agent_044_tasks.json"
CASES = BENCHMARKS / "fullstack_agent_044_cases.json"
BUILDER = BENCHMARKS / "freeze_fullstack_agent_044_corpus.py"
PROTOCOL = BENCHMARKS / "fullstack_agent_044_protocol.json"
PROTOCOL_BUILDER = BENCHMARKS / "freeze_fullstack_agent_044_protocol.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle(task_id, value):
    if task_id == "seismic_array_build":
        first, second = value["short_sensors"] * 12, value["deep_sensors"] * 20
        extra = value["relay_towers"] * 7 if value["ash_warning"] else 0
        required, capacity = first + second + extra, value["relay_towers"] * 48
        done, delayed = min(required, capacity), max(required - capacity, 0)
        rounds = required // 37
        return {
            "sensor_total": value["short_sensors"] + value["deep_sensors"],
            "short_scan_seconds": first, "deep_scan_seconds": second,
            "ash_sync_seconds": extra, "array_required_seconds": required,
            "relay_capacity_seconds": capacity, "processed_seconds": done,
            "backlogged_seconds": delayed, "scan_rounds": rounds,
            "array_score": done + delayed * 6 + rounds * 10,
            "array_state": "aligned" if delayed == 0 else "ash_backlog" if value["ash_warning"] else "routine_backlog",
        }
    if task_id == "museum_conservation_build":
        first, second = value["canvas_crates"] * 9, value["textile_crates"] * 15
        extra = value["work_tables"] * 6 if value["emergency_drying"] else 0
        required, capacity = first + second + extra, value["work_tables"] * 43
        done, delayed = min(required, capacity), max(required - capacity, 0)
        rounds = required // 34
        return {
            "crate_total": value["canvas_crates"] + value["textile_crates"],
            "canvas_work_minutes": first, "textile_work_minutes": second,
            "drying_setup_minutes": extra, "conservation_required_minutes": required,
            "table_capacity_minutes": capacity, "completed_minutes": done,
            "deferred_minutes": delayed, "conservation_rounds": rounds,
            "conservation_score": done + delayed * 7 + rounds * 11,
            "conservation_state": "preserved" if delayed == 0 else "emergency_queue" if value["emergency_drying"] else "routine_queue",
        }
    if task_id == "canal_lock_repair":
        first, second = value["freight_barges"] * 10, value["tour_barges"] * 17
        extra = value["lock_chambers"] * 8 if value["flood_protocol"] else 0
        required, capacity = first + second + extra, value["lock_chambers"] * 45
        done, delayed = min(required, capacity), max(required - capacity, 0)
        return {
            "barge_total": value["freight_barges"] + value["tour_barges"],
            "freight_lock_units": first, "tour_lock_units": second,
            "flood_lock_units": extra, "lock_required_units": required,
            "lock_capacity_units": capacity, "passed_lock_units": done,
            "held_lock_units": delayed, "clearance_units": max(capacity - done, 0),
            "canal_state": "clear" if delayed == 0 else "flood_hold" if value["flood_protocol"] else "routine_hold",
        }
    if task_id == "thermal_greenhouse_repair":
        first, second = value["seedling_rows"] * 8, value["fruit_rows"] * 14
        extra = value["heat_pumps"] * 5 if value["frost_cycle"] else 0
        required, capacity = first + second + extra, value["heat_pumps"] * 41
        done, delayed, cycles = min(required, capacity), max(required - capacity, 0), required // 29
        return {
            "row_total": value["seedling_rows"] + value["fruit_rows"],
            "seedling_heat_units": first, "fruit_heat_units": second,
            "frost_heat_units": extra, "heat_required_units": required,
            "pump_capacity_units": capacity, "delivered_heat_units": done,
            "heat_deficit_units": delayed, "heat_reserve_units": max(capacity - done, 0),
            "heating_cycles": cycles,
            "greenhouse_score": done + delayed * 5 + cycles * 7,
            "greenhouse_state": "balanced" if delayed == 0 else "frost_shortage" if value["frost_cycle"] else "heat_shortage",
        }
    raise AssertionError(task_id)


def test_fullstack_044_corpus_is_frozen_disjoint_complete_and_oracle_checked():
    task_document = json.loads(TASKS.read_text(encoding="utf-8"))
    case_document = json.loads(CASES.read_text(encoding="utf-8"))

    assert sha256(TASKS) == "8b476f2285ba45ba937c739fd1f3036f4b58791951ee73b2f61bc78039d87659"
    assert sha256(CASES) == "6299db88780c417e68f2a6377710c6d3b83ff4bb8870f7c2d865cad7a5114b25"
    assert task_document["experiment_id"] == case_document["experiment_id"] == "044"
    assert task_document["product_freeze_commit"] == (
        "cbe2d8aceba3733cebe61af39815d7781e9cc18b"
    )
    assert task_document["common_contract"]["body_limit_bytes"] == 16_384
    tasks = task_document["tasks"]
    assert [task["kind"] for task in tasks] == [
        "implementation", "implementation", "maintenance", "maintenance"
    ]

    prior_tasks, prior_cases = [], []
    for experiment in ("036", "037", "038", "039", "040", "041", "042", "043"):
        prior_tasks.extend(json.loads(
            (BENCHMARKS / f"fullstack_agent_{experiment}_tasks.json").read_text()
        )["tasks"])
        prior_cases.extend(
            case
            for rows in json.loads(
                (BENCHMARKS / f"fullstack_agent_{experiment}_cases.json").read_text()
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
        all_case_ids.extend(row["id"] for row in rows)
        if task["kind"] == "maintenance":
            assert task["root_cause_role"] == "application_logic"
            assert task["predeclared_defect"]

        order = list(task["request_fields"])
        for row in rows:
            if row["target"] == "browser":
                value = dict(zip(order, row["args"], strict=True))
                assert row["expected"] == oracle(task["id"], value)[task["shared_result_field"]]
            elif row["method"] == "GET":
                assert row["expected_json"] == {"service": task["service"], "ready": True}
            elif row["expected_status"] == 200:
                assert row["expected_json"] == oracle(task["id"], row["json"])
            else:
                assert row["expected_error"] in {
                    "invalid_json", "json_content_type_required", "body_too_large"
                }

    assert len(all_case_ids) == len(set(all_case_ids)) == 36
    assert set(all_case_ids).isdisjoint(row["id"] for row in prior_cases)


def test_fullstack_044_maintenance_defects_are_new_and_publicly_observable():
    tasks = {task["id"]: task for task in json.loads(TASKS.read_text())["tasks"]}
    cases = json.loads(CASES.read_text())["tasks"]

    canal = cases["canal_lock_repair"][1]
    value = canal["json"]
    defective_required = value["freight_barges"] * 10 + value["tour_barges"] * 17
    assert value["lock_chambers"] * 45 - defective_required == 53
    assert canal["expected_json"]["clearance_units"] == 37
    assert "conditional-polarity" in tasks["canal_lock_repair"]["historical_grounding"]

    greenhouse = cases["thermal_greenhouse_repair"][1]
    assert greenhouse["expected_json"]["heat_required_units"] == 54
    assert greenhouse["expected_json"]["heating_cycles"] == 1
    assert 54 // 23 == 2
    assert greenhouse["expected_json"]["greenhouse_score"] == 61
    assert "floor-divisor" in tasks["thermal_greenhouse_repair"]["historical_grounding"]


def test_fullstack_044_corpus_builder_is_deterministic(tmp_path):
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


def test_fullstack_044_protocol_preregisters_matrix_gate_and_scratch_boundary():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    product = protocol["frozen_product"]
    scratch = protocol["scratch_space_control"]

    assert sha256(PROTOCOL) == "9a2d25d1e8c90e686c972ed18b34096780efde950057fd2b27244408159c3da4"
    assert protocol["protocol_revision"] == 1
    assert protocol["experiment_id"] == "044"
    assert "execution_freeze" not in protocol
    assert product["parley_version"] == "parley 0.5.5"
    assert product["product_commit"] == "a098996847927c4eb622e2af8d0b7ebee81011c6"
    assert product["corpus_commit"] == "cef46dcdf70183e2c64e235bf9699184ba166eb5"
    for file_key, hash_key in (
        ("tasks_file", "tasks_sha256"),
        ("cases_file", "cases_sha256"),
        ("parley_context_file", "parley_context_sha256"),
        ("product_freeze_file", "product_freeze_sha256"),
        ("build_analysis_file", "build_analysis_sha256"),
    ):
        assert sha256(REPO / product[file_key]) == product[hash_key]
    assert product["parley_context_o200k_tokens"] == 222
    assert product["frozen_build_improvement_percent"] == 70.5496
    assert protocol["matrix"]["fresh_sessions"] == 96
    assert protocol["matrix"]["hidden_case_executions"] == 480
    assert protocol["frozen_config"]["languages"] == [
        "parley", "python", "typescript", "rust"
    ]
    assert protocol["frozen_config"]["max_workers"] == scratch["max_workers"] == 4
    assert scratch["required_free_bytes"] == 16 * 1024**3
    assert "before journal initialization" in scratch["preflight_timing"]
    assert "before removing" in scratch["cleanup_order"]
    assert "never authorizes a rerun" in scratch["failure_policy"]
    assert set(protocol["primary_gate"]) == {
        "execution_integrity", "correctness", "first_check", "tokens",
        "elapsed", "maintainability", "verdict",
    }
    assert "implemented only after this protocol commit" in protocol["implementation_rule"]
    assert "outside iteration 044" in protocol["stop_rule"]


def test_fullstack_044_protocol_builder_is_deterministic(tmp_path):
    output = tmp_path / "protocol.json"
    completed = subprocess.run(
        [sys.executable, str(PROTOCOL_BUILDER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == PROTOCOL.read_bytes()
