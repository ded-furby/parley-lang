import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TASKS = BENCHMARKS / "fullstack_agent_042_tasks.json"
CASES = BENCHMARKS / "fullstack_agent_042_cases.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle(task_id, value):
    if task_id == "radio_archive_build":
        segments = value["spoken_segments"] + value["music_segments"]
        speech = value["spoken_segments"] * 14
        music = value["music_segments"] * 24
        translation = value["language_tracks"] * 9 if value["live_broadcast"] else 0
        archive = speech + music + translation
        replicas = archive * value["language_tracks"]
        blocks = archive // 64
        score = replicas + blocks * 17 + segments * 3
        mode = (
            "multilingual_live"
            if value["live_broadcast"] and value["language_tracks"] > 1
            else "live"
            if value["live_broadcast"]
            else "catalog"
        )
        return {
            "segment_total": segments,
            "speech_megabytes": speech,
            "music_megabytes": music,
            "translation_megabytes": translation,
            "archive_megabytes": archive,
            "replica_megabytes": replicas,
            "upload_blocks": blocks,
            "archive_score": score,
            "archive_mode": mode,
        }
    if task_id == "theatre_turnaround_build":
        shows = value["matinee_shows"] + value["evening_shows"]
        base = value["matinee_shows"] * 18 + value["evening_shows"] * 27
        touring = value["stage_crews"] * 6 if value["touring_production"] else 0
        required = base + touring
        capacity = value["stage_crews"] * 45
        covered = min(required, capacity)
        delayed = max(required - capacity, 0)
        windows = required // 30
        score = covered + delayed * 8 + windows * 11
        state = (
            "on_time"
            if delayed == 0
            else "touring_delay"
            if value["touring_production"]
            else "repertory_delay"
        )
        return {
            "show_total": shows,
            "base_reset_minutes": base,
            "touring_minutes": touring,
            "required_minutes": required,
            "crew_capacity_minutes": capacity,
            "covered_minutes": covered,
            "delayed_minutes": delayed,
            "handoff_windows": windows,
            "turnaround_score": score,
            "turnaround_state": state,
        }
    if task_id == "bakery_batch_repair":
        loaves = value["sourdough_loaves"] + value["rye_loaves"]
        sourdough = value["sourdough_loaves"] * 11
        rye = value["rye_loaves"] * 8
        proof = loaves * 2 if value["overnight_proof"] else 0
        bake = sourdough + rye + proof
        capacity = value["oven_decks"] * 48
        used = min(bake, capacity)
        unscheduled = max(bake - capacity, 0)
        batches = (loaves + 11) // 12
        state = (
            "ready"
            if unscheduled == 0
            else "overnight_backlog"
            if value["overnight_proof"]
            else "daytime_backlog"
        )
        return {
            "loaf_total": loaves,
            "sourdough_minutes": sourdough,
            "rye_minutes": rye,
            "proof_minutes": proof,
            "bake_minutes": bake,
            "rack_capacity_minutes": capacity,
            "oven_minutes_used": used,
            "unscheduled_minutes": unscheduled,
            "tray_batches": batches,
            "bakery_state": state,
        }
    if task_id == "subsea_relay_repair":
        packets = value["shore_packets"] + value["vessel_packets"]
        shore = value["shore_packets"] * 4
        vessel = value["vessel_packets"] * 7
        storm = value["relay_nodes"] * 5 if value["storm_routing"] else 0
        required = shore + vessel + storm
        capacity = value["relay_nodes"] * 24
        forwarded = min(required, capacity)
        dropped = max(required - capacity, 0)
        reserve = max(capacity - forwarded, 0)
        state = (
            "clear"
            if dropped == 0
            else "storm_loss"
            if value["storm_routing"]
            else "packet_loss"
        )
        return {
            "packet_total": packets,
            "shore_units": shore,
            "vessel_units": vessel,
            "storm_units": storm,
            "required_units": required,
            "relay_capacity_units": capacity,
            "forwarded_units": forwarded,
            "dropped_units": dropped,
            "reserve_units": reserve,
            "relay_state": state,
        }
    raise AssertionError(f"unknown 042 task: {task_id}")


def test_fullstack_042_corpus_is_frozen_independent_complete_and_oracle_checked():
    task_document = json.loads(TASKS.read_text(encoding="utf-8"))
    case_document = json.loads(CASES.read_text(encoding="utf-8"))

    assert sha256(TASKS) == (
        "14f946574d2c5fa6a552496fb6eba4e51380a2af0c85445e1b6d0a60d66da302"
    )
    assert sha256(CASES) == (
        "f233dc0fa944a7a956619c8755801e882da974bc5e927b6dba67312084d4fe0c"
    )
    assert task_document["schema_version"] == case_document["schema_version"] == 1
    assert task_document["experiment_id"] == case_document["experiment_id"] == "042"
    assert task_document["common_contract"]["body_limit_bytes"] == 16_384
    tasks = task_document["tasks"]
    assert [task["kind"] for task in tasks] == [
        "implementation",
        "implementation",
        "maintenance",
        "maintenance",
    ]
    assert set(case_document["tasks"]) == {task["id"] for task in tasks}

    prior_tasks = []
    prior_cases = []
    for experiment in ("036", "037", "038", "039", "040", "041"):
        prior_tasks.extend(
            json.loads(
                (BENCHMARKS / f"fullstack_agent_{experiment}_tasks.json").read_text()
            )["tasks"]
        )
        prior_cases.extend(
            case
            for cases in json.loads(
                (BENCHMARKS / f"fullstack_agent_{experiment}_cases.json").read_text()
            )["tasks"].values()
            for case in cases
        )

    def fields(rows, name):
        return {field for row in rows for field in row[name]}

    assert {task["id"] for task in tasks}.isdisjoint(task["id"] for task in prior_tasks)
    assert fields(tasks, "request_fields").isdisjoint(
        fields(prior_tasks, "request_fields")
    )
    assert fields(tasks, "response_fields").isdisjoint(
        fields(prior_tasks, "response_fields")
    )
    for name in ("status_route", "post_route", "browser_export"):
        assert {task[name] for task in tasks}.isdisjoint(
            task[name] for task in prior_tasks
        )

    all_case_ids = []
    for task in tasks:
        assert task["shared_result_field"] in task["response_fields"]
        if task["kind"] == "maintenance":
            assert task["root_cause_role"] == "application_logic"
            assert task["predeclared_defect"]

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

        field_order = list(task["request_fields"])
        for case in cases:
            if case["target"] == "browser":
                assert case["export"] == task["browser_export"]
                values = dict(zip(field_order, case["args"], strict=True))
                result = oracle(task["id"], values)
                assert case["expected"] == result[task["shared_result_field"]]
            elif case["method"] == "GET":
                assert case["path"] == task["status_route"]
                assert case["expected_json"] == {
                    "service": task["service"],
                    "ready": True,
                }
            elif case["expected_status"] == 200:
                assert case["path"] == task["post_route"]
                assert set(case["json"]) == set(task["request_fields"])
                assert case["expected_json"] == oracle(task["id"], case["json"])
            else:
                assert case["expected_error"] in {
                    "invalid_json",
                    "json_content_type_required",
                    "body_too_large",
                }

    assert len(all_case_ids) == len(set(all_case_ids)) == 36
    assert set(all_case_ids).isdisjoint(case["id"] for case in prior_cases)


def test_fullstack_042_maintenance_defects_are_new_and_publicly_observable():
    tasks = {
        task["id"]: task for task in json.loads(TASKS.read_text())["tasks"]
    }
    cases = json.loads(CASES.read_text())["tasks"]

    bakery = cases["bakery_batch_repair"][1]
    loaves = bakery["json"]["sourdough_loaves"] + bakery["json"]["rye_loaves"]
    assert loaves // 12 == 0
    assert bakery["expected_json"]["tray_batches"] == 1
    assert "ceiling-rounding omission" in tasks["bakery_batch_repair"][
        "historical_grounding"
    ]

    relay = cases["subsea_relay_repair"][1]
    value = relay["json"]
    defective_required = (
        value["shore_packets"] * 4
        + value["vessel_packets"] * 7
        - value["relay_nodes"] * 5
    )
    defective_reserve = value["relay_nodes"] * 24 - defective_required
    assert defective_reserve == 13
    assert relay["expected_json"]["reserve_units"] == 0
    assert "sign-inversion" in tasks["subsea_relay_repair"][
        "historical_grounding"
    ]


def test_fullstack_042_corpus_was_created_after_the_context_only_freeze():
    freeze = json.loads(
        (BENCHMARKS / "fullstack_agent_042_context.json").read_text(encoding="utf-8")
    )
    assert freeze["context_sha256"] == (
        "f40a1030de6b3ed75f47183dee41d1ac3185dd87b747f779dab8835d4d63e8c4"
    )
    assert "before any iteration-042 task semantics" in freeze[
        "construction_boundary"
    ]


def test_fullstack_042_protocol_preregisters_matrix_gate_and_scratch_boundary():
    protocol_path = BENCHMARKS / "fullstack_agent_042_protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    product = protocol["frozen_product"]
    scratch = protocol["scratch_space_control"]

    assert sha256(protocol_path) == (
        "2a8416d542141b6da0f28ae7b415182325113770b44a1e4e4458bdfb3f6ed149"
    )
    assert protocol["schema_version"] == 1
    assert protocol["protocol_revision"] == 2
    assert protocol["experiment_id"] == "042"
    execution = protocol["execution_freeze"]
    assert execution["measured_sessions_before_freeze"] == 0
    assert execution["harness_commit"] == (
        "8e9535473ac0e0d172de6c18131da2e65a3a87aa"
    )
    assert execution["calibrated_max_workspace_bytes"] == 161_165_133
    assert execution["parley_prompt_delta_vs_python_o200k_tokens"] == 207
    assert len(execution["files"]) == 19
    for item in execution["files"]:
        assert sha256(REPO / item["file"]) == item["sha256"]
    assert product["parley_version"] == "parley 0.5.3"
    assert product["product_commit"] == (
        "dd6ee476ee8f244f8470a6524d1885103d919aa3"
    )
    assert product["corpus_commit"] == (
        "3e46ee290e0da156fcb18c8a4a2cf865ba13b7a1"
    )
    for file_key, hash_key in (
        ("tasks_file", "tasks_sha256"),
        ("cases_file", "cases_sha256"),
        ("parley_context_file", "parley_context_sha256"),
        ("context_freeze_file", "context_freeze_sha256"),
    ):
        assert sha256(REPO / product[file_key]) == product[hash_key]
    assert product["parley_context_bytes"] == 892
    assert product["parley_context_o200k_tokens"] == 222

    for file_key, hash_key in (
        ("implementation_file", "implementation_sha256"),
        ("policy_file", "policy_sha256"),
    ):
        assert sha256(REPO / scratch[file_key]) == scratch[hash_key]
    config = protocol["frozen_config"]
    assert config["languages"] == ["parley", "python", "typescript", "rust"]
    assert config["max_workers"] == scratch["max_workers"] == 4
    assert scratch["reserve_bytes"] == 8 * 1024**3
    assert scratch["per_worker_bytes"] == 2 * 1024**3
    assert scratch["required_free_bytes"] == 16 * 1024**3
    assert "before journal initialization" in scratch["preflight_timing"]
    assert "before removing" in scratch["cleanup_order"]
    assert "never authorizes a rerun" in scratch["failure_policy"]
    assert protocol["matrix"]["fresh_sessions"] == 96
    assert protocol["matrix"]["hidden_case_executions"] == 480
    assert set(protocol["primary_gate"]) == {
        "execution_integrity",
        "correctness",
        "first_check",
        "tokens",
        "elapsed",
        "maintainability",
        "verdict",
    }
    assert "implemented only after this protocol commit" in protocol[
        "implementation_rule"
    ]
    assert "Scratch calibration may only increase" in protocol["change_rule"]
