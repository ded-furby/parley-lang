import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS = BENCHMARKS / "fullstack_agent_043_tasks.json"
CASES = BENCHMARKS / "fullstack_agent_043_cases.json"
BUILDER = BENCHMARKS / "freeze_fullstack_agent_043_corpus.py"
PROTOCOL = BENCHMARKS / "fullstack_agent_043_protocol.json"
PROTOCOL_BUILDER = BENCHMARKS / "freeze_fullstack_agent_043_protocol.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle(task_id, value):
    if task_id == "wildfire_drone_build":
        scout = value["scout_drones"] * 13
        cargo = value["cargo_drones"] * 21
        extra = value["launch_pads"] * 8 if value["night_mission"] else 0
        required = scout + cargo + extra
        capacity = value["launch_pads"] * 50
        completed = min(required, capacity)
        delayed = max(required - capacity, 0)
        waves = required // 40
        return {
            "drone_total": value["scout_drones"] + value["cargo_drones"],
            "scout_flight_minutes": scout,
            "cargo_flight_minutes": cargo,
            "night_setup_minutes": extra,
            "mission_load_minutes": required,
            "launch_capacity_minutes": capacity,
            "completed_flight_minutes": completed,
            "delayed_flight_minutes": delayed,
            "flight_waves": waves,
            "wildfire_score": completed + delayed * 6 + waves * 9,
            "wildfire_mode": "ready" if delayed == 0 else "night_delay" if value["night_mission"] else "day_delay",
        }
    if task_id == "satellite_uplink_build":
        science = value["science_packets"] * 6
        navigation = value["navigation_packets"] * 10
        extra = value["ground_antennas"] * 7 if value["solar_interference"] else 0
        required = science + navigation + extra
        capacity = value["ground_antennas"] * 44
        sent = min(required, capacity)
        queued = max(required - capacity, 0)
        windows = required // 25
        return {
            "uplink_packet_total": value["science_packets"] + value["navigation_packets"],
            "science_transmit_seconds": science,
            "navigation_transmit_seconds": navigation,
            "interference_seconds": extra,
            "transmit_seconds": required,
            "antenna_capacity_seconds": capacity,
            "sent_seconds": sent,
            "queued_seconds": queued,
            "transmission_windows": windows,
            "uplink_score": sent + queued * 7 + windows * 12,
            "uplink_mode": "synchronized" if queued == 0 else "solar_queue" if value["solar_interference"] else "routine_queue",
        }
    if task_id == "alpine_gondola_repair":
        rider = value["passenger_groups"] * 8
        freight = value["supply_crates"] * 13
        extra = value["gondola_cabins"] * 5 if value["express_service"] else 0
        required = rider + freight + extra
        capacity = value["gondola_cabins"] * 42
        carried = min(required, capacity)
        stranded = max(required - capacity, 0)
        return {
            "gondola_item_total": value["passenger_groups"] + value["supply_crates"],
            "rider_load_units": rider,
            "freight_load_units": freight,
            "express_load_units": extra,
            "gondola_required_units": required,
            "gondola_capacity_units": capacity,
            "carried_load_units": carried,
            "stranded_load_units": stranded,
            "lift_margin_units": max(capacity - carried, 0),
            "gondola_condition": "clear" if stranded == 0 else "express_stranded" if value["express_service"] else "standard_stranded",
        }
    if task_id == "kelp_hatchery_repair":
        juvenile = value["juvenile_tanks"] * 9
        mature = value["mature_tanks"] * 16
        extra = value["aerators"] * 4 if value["heat_treatment"] else 0
        needed = juvenile + mature + extra
        capacity = value["aerators"] * 38
        delivered = min(needed, capacity)
        deficit = max(needed - capacity, 0)
        return {
            "hatchery_tank_total": value["juvenile_tanks"] + value["mature_tanks"],
            "juvenile_oxygen_units": juvenile,
            "mature_oxygen_units": mature,
            "treatment_oxygen_units": extra,
            "oxygen_needed_units": needed,
            "aeration_capacity_units": capacity,
            "oxygen_delivered_units": delivered,
            "oxygen_deficit_units": deficit,
            "oxygen_buffer_units": max(capacity - delivered, 0),
            "hatchery_condition": "balanced" if deficit == 0 else "heat_shortage" if value["heat_treatment"] else "oxygen_shortage",
        }
    raise AssertionError(task_id)


def test_fullstack_043_corpus_is_frozen_disjoint_complete_and_oracle_checked():
    task_document = json.loads(TASKS.read_text(encoding="utf-8"))
    case_document = json.loads(CASES.read_text(encoding="utf-8"))

    assert sha256(TASKS) == "7dc4df635d713be18f222aa2954de28b756083c01a159bf8b42a263f96b205da"
    assert sha256(CASES) == "ae52c292e16b0eb82db2aedacd7c063cd742a330093efd0a970ddf34306f1691"
    assert task_document["experiment_id"] == case_document["experiment_id"] == "043"
    assert task_document["product_freeze_commit"] == "863c3d6d18911b565f8e91efaebf24fe90978176"
    assert task_document["common_contract"]["body_limit_bytes"] == 16_384
    tasks = task_document["tasks"]
    assert [task["kind"] for task in tasks] == [
        "implementation", "implementation", "maintenance", "maintenance"
    ]

    prior_tasks = []
    prior_cases = []
    for experiment in ("036", "037", "038", "039", "040", "041", "042"):
        prior_tasks.extend(json.loads((BENCHMARKS / f"fullstack_agent_{experiment}_tasks.json").read_text())["tasks"])
        prior_cases.extend(
            case
            for rows in json.loads((BENCHMARKS / f"fullstack_agent_{experiment}_cases.json").read_text())["tasks"].values()
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
        cases = case_document["tasks"][task["id"]]
        public = [case for case in cases if case["visibility"] == "public"]
        hidden = [case for case in cases if case["visibility"] == "hidden"]
        assert len(cases) == 9
        assert len(public) == 4 and len(hidden) == 5
        assert sum(case["target"] == "browser" for case in public) == 1
        assert sum(case["target"] == "browser" for case in hidden) == 2
        assert task["public_case_ids"] == [case["id"] for case in public]
        assert task["hidden_case_ids"] == [case["id"] for case in hidden]
        all_case_ids.extend(case["id"] for case in cases)
        if task["kind"] == "maintenance":
            assert task["root_cause_role"] == "application_logic"
            assert task["predeclared_defect"]

        order = list(task["request_fields"])
        for case in cases:
            if case["target"] == "browser":
                value = dict(zip(order, case["args"], strict=True))
                assert case["expected"] == oracle(task["id"], value)[task["shared_result_field"]]
            elif case["method"] == "GET":
                assert case["expected_json"] == {"service": task["service"], "ready": True}
            elif case["expected_status"] == 200:
                assert case["expected_json"] == oracle(task["id"], case["json"])
            else:
                assert case["expected_error"] in {"invalid_json", "json_content_type_required", "body_too_large"}

    assert len(all_case_ids) == len(set(all_case_ids)) == 36
    assert set(all_case_ids).isdisjoint(case["id"] for case in prior_cases)


def test_fullstack_043_maintenance_defects_are_new_and_publicly_observable():
    tasks = {task["id"]: task for task in json.loads(TASKS.read_text())["tasks"]}
    cases = json.loads(CASES.read_text())["tasks"]

    gondola = cases["alpine_gondola_repair"][1]
    value = gondola["json"]
    defective_required = value["passenger_groups"] * 13 + value["supply_crates"] * 8 + value["gondola_cabins"] * 5
    assert 84 - defective_required == 19
    assert gondola["expected_json"]["lift_margin_units"] == 24
    assert "coefficient-transposition" in tasks["alpine_gondola_repair"]["historical_grounding"]

    hatchery = cases["kelp_hatchery_repair"][1]
    assert hatchery["expected_json"]["oxygen_needed_units"] == 42
    assert hatchery["expected_json"]["aeration_capacity_units"] == 76
    assert hatchery["expected_json"]["oxygen_delivered_units"] == 42
    assert "extremum-selector" in tasks["kelp_hatchery_repair"]["historical_grounding"]


def test_fullstack_043_corpus_builder_is_deterministic(tmp_path):
    tasks_output = tmp_path / "tasks.json"
    cases_output = tmp_path / "cases.json"
    completed = subprocess.run(
        [sys.executable, str(BUILDER), "--tasks-output", str(tasks_output), "--cases-output", str(cases_output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert tasks_output.read_bytes() == TASKS.read_bytes()
    assert cases_output.read_bytes() == CASES.read_bytes()


def test_fullstack_043_protocol_preregisters_matrix_gate_and_scratch_boundary():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    product = protocol["frozen_product"]
    scratch = protocol["scratch_space_control"]

    assert sha256(PROTOCOL) == "a6ba21dc60dfee27027232f648d622363ead3a4e4063f67bded670ef4dc72cc4"
    assert protocol["protocol_revision"] == 2
    assert protocol["experiment_id"] == "043"
    execution = protocol["execution_freeze"]
    assert execution["measured_sessions_before_freeze"] == 0
    assert execution["harness_commit"] == (
        "9ca28d531197c69b5171c52b64c165b193faa767"
    )
    assert execution["calibrated_max_workspace_bytes"] == 161_170_519
    assert execution["parley_prompt_delta_vs_python_o200k_tokens"] == 207
    assert len(execution["files"]) == 19
    for item in execution["files"]:
        assert sha256(REPO / item["file"]) == item["sha256"]
    assert product["parley_version"] == "parley 0.5.4"
    assert product["product_commit"] == "bf0f85aa33dbd6d52c17260d85a04155d11518c2"
    assert product["corpus_commit"] == "b5d2fc4b23dbd0716f4e09ab4472372f1d7dbf01"
    for file_key, hash_key in (
        ("tasks_file", "tasks_sha256"),
        ("cases_file", "cases_sha256"),
        ("parley_context_file", "parley_context_sha256"),
        ("product_freeze_file", "product_freeze_sha256"),
        ("build_analysis_file", "build_analysis_sha256"),
    ):
        assert sha256(REPO / product[file_key]) == product[hash_key]
    assert product["parley_context_o200k_tokens"] == 222
    assert product["frozen_build_improvement_percent"] == 31.5904
    assert protocol["matrix"]["fresh_sessions"] == 96
    assert protocol["matrix"]["hidden_case_executions"] == 480
    assert protocol["frozen_config"]["languages"] == ["parley", "python", "typescript", "rust"]
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
    assert "outside iteration 043" in protocol["stop_rule"]


def test_fullstack_043_protocol_builder_is_deterministic(tmp_path):
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
