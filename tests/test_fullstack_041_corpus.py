import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"


def oracle(task_id, value):
    if task_id == "observatory_schedule_build":
        sessions = value["public_talks"] + value["research_tracks"]
        opened = value["public_talks"] * 22 + value["research_tracks"] * 31
        weather = value["dome_sections"] * 7 if value["cloud_monitoring"] else 0
        scheduled = opened + weather
        staff = scheduled * value["dome_sections"]
        breaks = scheduled // 90
        score = staff + breaks * 13 + sessions * 5
        mode = (
            "research_first"
            if value["research_tracks"] > value["public_talks"]
            else "outreach"
            if value["public_talks"] > 0
            else "standby"
        )
        return {
            "session_total": sessions,
            "open_minutes": opened,
            "weather_minutes": weather,
            "scheduled_minutes": scheduled,
            "staff_minutes": staff,
            "rest_breaks": breaks,
            "coordination_score": score,
            "observatory_mode": mode,
        }
    if task_id == "reef_nursery_build":
        trays = value["coral_trays"] + value["algae_trays"]
        base = value["coral_trays"] * 12 + value["algae_trays"] * 7
        flush = value["circulation_pumps"] * 5 if value["night_cycle"] else 0
        required = base + flush
        capacity = value["circulation_pumps"] * 20
        served = min(required, capacity)
        overflow = max(required - capacity, 0)
        index = served + overflow * 9 + value["coral_trays"] * 3
        state = (
            "balanced"
            if overflow == 0
            else "night_overflow"
            if value["night_cycle"]
            else "daytime_overflow"
        )
        return {
            "nursery_trays": trays,
            "base_flow_liters": base,
            "night_flush_liters": flush,
            "required_flow_liters": required,
            "pump_capacity_liters": capacity,
            "served_flow_liters": served,
            "overflow_flow_liters": overflow,
            "reef_index": index,
            "nursery_state": state,
        }
    if task_id == "rescue_shelter_repair":
        hikers = value["arriving_hikers"] + value["injured_hikers"]
        baseline = value["arriving_hikers"] * 3 + value["injured_hikers"] * 6
        reduction = value["heater_packs"] * 2 if value["storm_lockdown"] else 0
        required = max(baseline - reduction, 0)
        capacity = value["heater_packs"] * 8
        delivered = min(required, capacity)
        uncovered = max(required - delivered, 0)
        unused = max(capacity - delivered, 0)
        state = (
            "covered"
            if uncovered == 0
            else "storm_gap"
            if value["storm_lockdown"]
            else "supply_gap"
        )
        return {
            "hiker_total": hikers,
            "baseline_warmth": baseline,
            "lockdown_reduction": reduction,
            "required_warmth": required,
            "pack_capacity": capacity,
            "delivered_warmth": delivered,
            "uncovered_warmth": uncovered,
            "unused_capacity": unused,
            "shelter_state": state,
        }
    if task_id == "aviary_feeding_repair":
        birds = value["resident_birds"] + value["rehab_birds"]
        resident = value["resident_birds"] * 2
        rehab = value["rehab_birds"] * 3
        winter = birds if value["winter_ration"] else 0
        required = resident + rehab + winter
        available = value["feed_bins"] * 10
        served = min(required, available)
        shortage = max(required - available, 0)
        state = (
            "stocked"
            if shortage == 0
            else "winter_shortage"
            if value["winter_ration"]
            else "shortage"
        )
        return {
            "bird_total": birds,
            "resident_scoops": resident,
            "rehab_scoops": rehab,
            "winter_scoops": winter,
            "required_scoops": required,
            "available_scoops": available,
            "served_scoops": served,
            "shortage_scoops": shortage,
            "feed_state": state,
        }
    raise AssertionError(f"unknown 041 task: {task_id}")


def test_fullstack_041_corpus_is_independent_complete_and_oracle_checked():
    task_document = json.loads(
        (BENCHMARKS / "fullstack_agent_041_tasks.json").read_text()
    )
    case_document = json.loads(
        (BENCHMARKS / "fullstack_agent_041_cases.json").read_text()
    )

    assert task_document["schema_version"] == case_document["schema_version"] == 1
    assert task_document["experiment_id"] == case_document["experiment_id"] == "041"
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
    for experiment in ("036", "037", "038", "039", "040"):
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

    assert {task["id"] for task in tasks}.isdisjoint(
        task["id"] for task in prior_tasks
    )
    assert fields(tasks, "request_fields").isdisjoint(
        fields(prior_tasks, "request_fields")
    )
    assert fields(tasks, "response_fields").isdisjoint(
        fields(prior_tasks, "response_fields")
    )
    assert {task["status_route"] for task in tasks}.isdisjoint(
        task["status_route"] for task in prior_tasks
    )
    assert {task["post_route"] for task in tasks}.isdisjoint(
        task["post_route"] for task in prior_tasks
    )
    assert {task["browser_export"] for task in tasks}.isdisjoint(
        task["browser_export"] for task in prior_tasks
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
                assert len(case["args"]) == len(field_order)
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


def test_fullstack_041_maintenance_defects_are_new_and_publicly_observable():
    tasks = {
        task["id"]: task
        for task in json.loads(
            (BENCHMARKS / "fullstack_agent_041_tasks.json").read_text()
        )["tasks"]
    }
    cases = json.loads(
        (BENCHMARKS / "fullstack_agent_041_cases.json").read_text()
    )["tasks"]

    shelter = cases["rescue_shelter_repair"][1]["expected_json"]
    assert shelter["required_warmth"] < shelter["baseline_warmth"]
    assert shelter["unused_capacity"] == 3
    assert "adjustment-before-allocation" in tasks["rescue_shelter_repair"][
        "historical_grounding"
    ]

    aviary = cases["aviary_feeding_repair"][1]["expected_json"]
    assert aviary["winter_scoops"] == aviary["bird_total"] == 7
    assert aviary["required_scoops"] == 24
    assert "subset-omission" in tasks["aviary_feeding_repair"][
        "historical_grounding"
    ]
