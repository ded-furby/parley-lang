#!/usr/bin/env python3
"""Build the deterministic semantics-only corpus for full-stack study 044."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
DEFAULT_TASKS = BENCHMARKS / "fullstack_agent_044_tasks.json"
DEFAULT_CASES = BENCHMARKS / "fullstack_agent_044_cases.json"
PRODUCT_FREEZE_COMMIT = "cbe2d8aceba3733cebe61af39815d7781e9cc18b"
PRODUCT_FREEZE_SHA256 = "181e26d1204765f3e14a1a24dfe9d82a545d271b3da900785716e509e1551e89"


COMMON_CONTRACT = {
    "server": "Expose the exact GET status route and typed POST JSON route declared by the task. Reject malformed JSON, missing fields, unknown fields, wrong field types, and out-of-domain numeric values. A number is a JSON integer and never a boolean; yesno is a JSON boolean.",
    "errors": "Return status 400 with {\"error\":\"invalid_json\"} for invalid JSON shape, types, or values. Return status 415 with {\"error\":\"json_content_type_required\"} for a POST body without application/json. Return status 413 with {\"error\":\"body_too_large\"} when the request body exceeds the frozen limit.",
    "browser": "Expose the declared deterministic scalar browser function as an ES module export and return the exact frozen values in real Chromium.",
    "cross_target": "The response field named by shared_result_field must equal the browser export for equivalent inputs.",
    "network": "Bind only to 127.0.0.1 on the harness-selected port.",
    "numeric_domain": "All numeric inputs are nonnegative integers.",
    "body_limit_bytes": 16384,
}


TASKS = [
    {
        "id": "seismic_array_build",
        "kind": "implementation",
        "title": "Build a seismic sensor array planner across HTTP and browser targets",
        "statement": "Implement the frozen Seismic Array contract in the supplied stack. sensor_total is short_sensors + deep_sensors. short_scan_seconds is short_sensors * 12. deep_scan_seconds is deep_sensors * 20. ash_sync_seconds is relay_towers * 7 during an ash_warning and zero otherwise. array_required_seconds is short_scan_seconds + deep_scan_seconds + ash_sync_seconds. relay_capacity_seconds is relay_towers * 48. processed_seconds is min(array_required_seconds, relay_capacity_seconds). backlogged_seconds is max(array_required_seconds - relay_capacity_seconds, 0). scan_rounds is array_required_seconds divided by 37 using floor division. array_score is processed_seconds + backlogged_seconds * 6 + scan_rounds * 10. array_state is aligned when backlogged_seconds is zero, ash_backlog when backlog remains during an ash warning, and routine_backlog otherwise. The browser export returns array_score.",
        "service": "Seismic Array",
        "status_route": "/status/seismic-array-ready",
        "post_route": "/api/v8/seismic-array",
        "browser_export": "seismic_array_score",
        "shared_result_field": "array_score",
        "request_fields": {
            "short_sensors": "number", "deep_sensors": "number",
            "relay_towers": "number", "ash_warning": "yesno",
        },
        "response_fields": {
            "sensor_total": "number", "short_scan_seconds": "number",
            "deep_scan_seconds": "number", "ash_sync_seconds": "number",
            "array_required_seconds": "number", "relay_capacity_seconds": "number",
            "processed_seconds": "number", "backlogged_seconds": "number",
            "scan_rounds": "number", "array_score": "number", "array_state": "text",
        },
        "independence": "New seismic-array domain, v8 route, scan-round and relay formulas, vocabulary, fixtures, and browser export selected after the v0.5.5 product freeze and before any 044 scaffold or model output.",
    },
    {
        "id": "museum_conservation_build",
        "kind": "implementation",
        "title": "Build a museum conservation scheduler across HTTP and browser targets",
        "statement": "Implement the frozen Museum Conservation contract in the supplied stack. crate_total is canvas_crates + textile_crates. canvas_work_minutes is canvas_crates * 9. textile_work_minutes is textile_crates * 15. drying_setup_minutes is work_tables * 6 during emergency_drying and zero otherwise. conservation_required_minutes is canvas_work_minutes + textile_work_minutes + drying_setup_minutes. table_capacity_minutes is work_tables * 43. completed_minutes is min(conservation_required_minutes, table_capacity_minutes). deferred_minutes is max(conservation_required_minutes - table_capacity_minutes, 0). conservation_rounds is conservation_required_minutes divided by 34 using floor division. conservation_score is completed_minutes + deferred_minutes * 7 + conservation_rounds * 11. conservation_state is preserved when deferred_minutes is zero, emergency_queue when delay remains during emergency drying, and routine_queue otherwise. The browser export returns conservation_score.",
        "service": "Museum Conservation",
        "status_route": "/status/museum-conservation-ready",
        "post_route": "/api/v8/museum-conservation",
        "browser_export": "museum_conservation_score",
        "shared_result_field": "conservation_score",
        "request_fields": {
            "canvas_crates": "number", "textile_crates": "number",
            "work_tables": "number", "emergency_drying": "yesno",
        },
        "response_fields": {
            "crate_total": "number", "canvas_work_minutes": "number",
            "textile_work_minutes": "number", "drying_setup_minutes": "number",
            "conservation_required_minutes": "number", "table_capacity_minutes": "number",
            "completed_minutes": "number", "deferred_minutes": "number",
            "conservation_rounds": "number", "conservation_score": "number",
            "conservation_state": "text",
        },
        "independence": "New museum-conservation domain, v8 route, conservation-round and work-table formulas, vocabulary, fixtures, and browser export selected after the v0.5.5 product freeze and before any 044 scaffold or model output.",
    },
    {
        "id": "canal_lock_repair",
        "kind": "maintenance",
        "title": "Repair flood-protocol polarity in a canal lock scheduler",
        "statement": "Repair the supplied Canal Lock application. barge_total is freight_barges + tour_barges. freight_lock_units is freight_barges * 10. tour_lock_units is tour_barges * 17. flood_lock_units is lock_chambers * 8 during flood_protocol and zero otherwise. lock_required_units is freight_lock_units + tour_lock_units + flood_lock_units. lock_capacity_units is lock_chambers * 45. passed_lock_units is min(lock_required_units, lock_capacity_units). held_lock_units is max(lock_required_units - lock_capacity_units, 0). clearance_units is max(lock_capacity_units - passed_lock_units, 0). canal_state is clear when held_lock_units is zero, flood_hold when load remains during flood protocol, and routine_hold otherwise. The HTTP response and browser export must use the same rule; the browser export returns clearance_units.",
        "service": "Canal Lock",
        "status_route": "/status/canal-lock-ready",
        "post_route": "/api/v8/canal-lock",
        "browser_export": "canal_clearance_units",
        "shared_result_field": "clearance_units",
        "request_fields": {
            "freight_barges": "number", "tour_barges": "number",
            "lock_chambers": "number", "flood_protocol": "yesno",
        },
        "response_fields": {
            "barge_total": "number", "freight_lock_units": "number",
            "tour_lock_units": "number", "flood_lock_units": "number",
            "lock_required_units": "number", "lock_capacity_units": "number",
            "passed_lock_units": "number", "held_lock_units": "number",
            "clearance_units": "number", "canal_state": "text",
        },
        "predeclared_defect": "The application-logic module reverses the flood_protocol condition, adding flood_lock_units during routine operation and omitting them during flood protocol.",
        "root_cause_role": "application_logic",
        "historical_grounding": "synthetic conditional-polarity inversion defect",
        "adaptation_boundary": "The conditional polarity, canal-lock vocabulary, fixtures, and expected repair are new and were selected after the v0.5.5 product freeze and before any measured output.",
    },
    {
        "id": "thermal_greenhouse_repair",
        "kind": "maintenance",
        "title": "Repair a heating-cycle divisor in a thermal greenhouse",
        "statement": "Repair the supplied Thermal Greenhouse application. row_total is seedling_rows + fruit_rows. seedling_heat_units is seedling_rows * 8. fruit_heat_units is fruit_rows * 14. frost_heat_units is heat_pumps * 5 during frost_cycle and zero otherwise. heat_required_units is seedling_heat_units + fruit_heat_units + frost_heat_units. pump_capacity_units is heat_pumps * 41. delivered_heat_units is min(heat_required_units, pump_capacity_units). heat_deficit_units is max(heat_required_units - pump_capacity_units, 0). heat_reserve_units is max(pump_capacity_units - delivered_heat_units, 0). heating_cycles is heat_required_units divided by 29 using floor division. greenhouse_score is delivered_heat_units + heat_deficit_units * 5 + heating_cycles * 7. greenhouse_state is balanced when heat_deficit_units is zero, frost_shortage when a deficit remains during a frost cycle, and heat_shortage otherwise. The HTTP response and browser export must use the same rule; the browser export returns greenhouse_score.",
        "service": "Thermal Greenhouse",
        "status_route": "/status/thermal-greenhouse-ready",
        "post_route": "/api/v8/thermal-greenhouse",
        "browser_export": "thermal_greenhouse_score",
        "shared_result_field": "greenhouse_score",
        "request_fields": {
            "seedling_rows": "number", "fruit_rows": "number",
            "heat_pumps": "number", "frost_cycle": "yesno",
        },
        "response_fields": {
            "row_total": "number", "seedling_heat_units": "number",
            "fruit_heat_units": "number", "frost_heat_units": "number",
            "heat_required_units": "number", "pump_capacity_units": "number",
            "delivered_heat_units": "number", "heat_deficit_units": "number",
            "heat_reserve_units": "number", "heating_cycles": "number",
            "greenhouse_score": "number", "greenhouse_state": "text",
        },
        "predeclared_defect": "The application-logic module divides heat_required_units by 23 instead of 29 when computing heating_cycles.",
        "root_cause_role": "application_logic",
        "historical_grounding": "synthetic floor-divisor substitution defect",
        "adaptation_boundary": "The heating-cycle divisor, greenhouse vocabulary, fixtures, and expected repair are new and were selected after the v0.5.5 product freeze and before any measured output.",
    },
]


def oracle(task_id: str, value: dict[str, Any]) -> dict[str, Any]:
    if task_id == "seismic_array_build":
        short = value["short_sensors"] * 12
        deep = value["deep_sensors"] * 20
        extra = value["relay_towers"] * 7 if value["ash_warning"] else 0
        required = short + deep + extra
        capacity = value["relay_towers"] * 48
        processed, backlog, rounds = min(required, capacity), max(required - capacity, 0), required // 37
        return {
            "sensor_total": value["short_sensors"] + value["deep_sensors"],
            "short_scan_seconds": short, "deep_scan_seconds": deep,
            "ash_sync_seconds": extra, "array_required_seconds": required,
            "relay_capacity_seconds": capacity, "processed_seconds": processed,
            "backlogged_seconds": backlog, "scan_rounds": rounds,
            "array_score": processed + backlog * 6 + rounds * 10,
            "array_state": "aligned" if backlog == 0 else "ash_backlog" if value["ash_warning"] else "routine_backlog",
        }
    if task_id == "museum_conservation_build":
        canvas = value["canvas_crates"] * 9
        textile = value["textile_crates"] * 15
        extra = value["work_tables"] * 6 if value["emergency_drying"] else 0
        required = canvas + textile + extra
        capacity = value["work_tables"] * 43
        completed, deferred, rounds = min(required, capacity), max(required - capacity, 0), required // 34
        return {
            "crate_total": value["canvas_crates"] + value["textile_crates"],
            "canvas_work_minutes": canvas, "textile_work_minutes": textile,
            "drying_setup_minutes": extra, "conservation_required_minutes": required,
            "table_capacity_minutes": capacity, "completed_minutes": completed,
            "deferred_minutes": deferred, "conservation_rounds": rounds,
            "conservation_score": completed + deferred * 7 + rounds * 11,
            "conservation_state": "preserved" if deferred == 0 else "emergency_queue" if value["emergency_drying"] else "routine_queue",
        }
    if task_id == "canal_lock_repair":
        freight = value["freight_barges"] * 10
        tour = value["tour_barges"] * 17
        extra = value["lock_chambers"] * 8 if value["flood_protocol"] else 0
        required = freight + tour + extra
        capacity = value["lock_chambers"] * 45
        passed, held = min(required, capacity), max(required - capacity, 0)
        return {
            "barge_total": value["freight_barges"] + value["tour_barges"],
            "freight_lock_units": freight, "tour_lock_units": tour,
            "flood_lock_units": extra, "lock_required_units": required,
            "lock_capacity_units": capacity, "passed_lock_units": passed,
            "held_lock_units": held, "clearance_units": max(capacity - passed, 0),
            "canal_state": "clear" if held == 0 else "flood_hold" if value["flood_protocol"] else "routine_hold",
        }
    if task_id == "thermal_greenhouse_repair":
        seedling = value["seedling_rows"] * 8
        fruit = value["fruit_rows"] * 14
        extra = value["heat_pumps"] * 5 if value["frost_cycle"] else 0
        required = seedling + fruit + extra
        capacity = value["heat_pumps"] * 41
        delivered, deficit, cycles = min(required, capacity), max(required - capacity, 0), required // 29
        return {
            "row_total": value["seedling_rows"] + value["fruit_rows"],
            "seedling_heat_units": seedling, "fruit_heat_units": fruit,
            "frost_heat_units": extra, "heat_required_units": required,
            "pump_capacity_units": capacity, "delivered_heat_units": delivered,
            "heat_deficit_units": deficit, "heat_reserve_units": max(capacity - delivered, 0),
            "heating_cycles": cycles,
            "greenhouse_score": delivered + deficit * 5 + cycles * 7,
            "greenhouse_state": "balanced" if deficit == 0 else "frost_shortage" if value["frost_cycle"] else "heat_shortage",
        }
    raise AssertionError(task_id)


SUCCESS_INPUTS = {
    "seismic_array_build": [
        ("seismic_array_ash_backlog", "public", {"short_sensors": 2, "deep_sensors": 3, "relay_towers": 2, "ash_warning": True}),
        ("seismic_array_aligned", "hidden", {"short_sensors": 1, "deep_sensors": 1, "relay_towers": 2, "ash_warning": False}),
        ("seismic_array_routine_backlog", "hidden", {"short_sensors": 4, "deep_sensors": 3, "relay_towers": 2, "ash_warning": False}),
    ],
    "museum_conservation_build": [
        ("museum_conservation_emergency_queue", "public", {"canvas_crates": 3, "textile_crates": 2, "work_tables": 1, "emergency_drying": True}),
        ("museum_conservation_preserved", "hidden", {"canvas_crates": 1, "textile_crates": 1, "work_tables": 2, "emergency_drying": False}),
        ("museum_conservation_routine_queue", "hidden", {"canvas_crates": 5, "textile_crates": 3, "work_tables": 2, "emergency_drying": False}),
    ],
    "canal_lock_repair": [
        ("canal_lock_clear", "public", {"freight_barges": 2, "tour_barges": 1, "lock_chambers": 2, "flood_protocol": True}),
        ("canal_lock_routine_hold", "hidden", {"freight_barges": 5, "tour_barges": 3, "lock_chambers": 2, "flood_protocol": False}),
        ("canal_lock_flood_hold", "hidden", {"freight_barges": 4, "tour_barges": 3, "lock_chambers": 2, "flood_protocol": True}),
    ],
    "thermal_greenhouse_repair": [
        ("thermal_greenhouse_balanced", "public", {"seedling_rows": 2, "fruit_rows": 2, "heat_pumps": 2, "frost_cycle": True}),
        ("thermal_greenhouse_frost_shortage", "hidden", {"seedling_rows": 5, "fruit_rows": 3, "heat_pumps": 1, "frost_cycle": True}),
        ("thermal_greenhouse_heat_shortage", "hidden", {"seedling_rows": 4, "fruit_rows": 2, "heat_pumps": 1, "frost_cycle": False}),
    ],
}


BROWSER_INPUTS = {
    "seismic_array_build": [
        ("seismic_array_browser_ash", "public", SUCCESS_INPUTS["seismic_array_build"][0][2]),
        ("seismic_array_browser_aligned", "hidden", SUCCESS_INPUTS["seismic_array_build"][1][2]),
        ("seismic_array_browser_routine", "hidden", SUCCESS_INPUTS["seismic_array_build"][2][2]),
    ],
    "museum_conservation_build": [
        ("museum_conservation_browser_emergency", "public", SUCCESS_INPUTS["museum_conservation_build"][0][2]),
        ("museum_conservation_browser_preserved", "hidden", SUCCESS_INPUTS["museum_conservation_build"][1][2]),
        ("museum_conservation_browser_routine", "hidden", SUCCESS_INPUTS["museum_conservation_build"][2][2]),
    ],
    "canal_lock_repair": [
        ("canal_lock_browser_clear", "public", SUCCESS_INPUTS["canal_lock_repair"][0][2]),
        ("canal_lock_browser_routine", "hidden", {"freight_barges": 1, "tour_barges": 2, "lock_chambers": 2, "flood_protocol": False}),
        ("canal_lock_browser_flood", "hidden", {"freight_barges": 3, "tour_barges": 1, "lock_chambers": 2, "flood_protocol": True}),
    ],
    "thermal_greenhouse_repair": [
        ("thermal_greenhouse_browser_balanced", "public", SUCCESS_INPUTS["thermal_greenhouse_repair"][0][2]),
        ("thermal_greenhouse_browser_frost", "hidden", SUCCESS_INPUTS["thermal_greenhouse_repair"][1][2]),
        ("thermal_greenhouse_browser_heat", "hidden", SUCCESS_INPUTS["thermal_greenhouse_repair"][2][2]),
    ],
}


INVALID_CASES = {
    "seismic_array_build": {
        "id": "seismic_array_wrong_relay_type", "visibility": "public", "target": "http", "method": "POST",
        "json": {"short_sensors": 2, "deep_sensors": 3, "relay_towers": True, "ash_warning": True},
        "expected_status": 400, "expected_error": "invalid_json",
    },
    "museum_conservation_build": {
        "id": "museum_conservation_wrong_media", "visibility": "public", "target": "http", "method": "POST",
        "raw_body": "{}", "content_type": "text/plain", "expected_status": 415, "expected_error": "json_content_type_required",
    },
    "canal_lock_repair": {
        "id": "canal_lock_missing_chambers", "visibility": "public", "target": "http", "method": "POST",
        "json": {"freight_barges": 2, "tour_barges": 1, "flood_protocol": True},
        "expected_status": 400, "expected_error": "invalid_json",
    },
    "thermal_greenhouse_repair": {
        "id": "thermal_greenhouse_wrong_frost_type", "visibility": "public", "target": "http", "method": "POST",
        "json": {"seedling_rows": 2, "fruit_rows": 2, "heat_pumps": 2, "frost_cycle": 1},
        "expected_status": 400, "expected_error": "invalid_json",
    },
}


UNKNOWN_FIELDS = {
    "seismic_array_build": ("magma_band", 4),
    "museum_conservation_build": ("gallery_wing", 3),
    "canal_lock_repair": ("water_level", 6),
    "thermal_greenhouse_repair": ("humidity_zone", 2),
}


def task_cases(task: dict[str, Any]) -> list[dict[str, Any]]:
    task_id = task["id"]
    stem = task_id.removesuffix("_build").removesuffix("_repair")
    status = {
        "id": stem + "_status", "visibility": "public", "target": "http",
        "method": "GET", "path": task["status_route"], "expected_status": 200,
        "expected_json": {"service": task["service"], "ready": True},
    }
    successes = [
        {
            "id": case_id, "visibility": visibility, "target": "http",
            "method": "POST", "path": task["post_route"], "json": value,
            "expected_status": 200, "expected_json": oracle(task_id, value),
        }
        for case_id, visibility, value in SUCCESS_INPUTS[task_id]
    ]
    invalid = {**INVALID_CASES[task_id], "path": task["post_route"]}
    unknown_name, unknown_value = UNKNOWN_FIELDS[task_id]
    unknown = {
        "id": stem + "_unknown_field", "visibility": "hidden", "target": "http",
        "method": "POST", "path": task["post_route"],
        "json": {**SUCCESS_INPUTS[task_id][0][2], unknown_name: unknown_value},
        "expected_status": 400, "expected_error": "invalid_json",
    }
    field_order = list(task["request_fields"])
    browsers = [
        {
            "id": case_id, "visibility": visibility, "target": "browser",
            "export": task["browser_export"],
            "args": [value[field] for field in field_order],
            "expected": oracle(task_id, value)[task["shared_result_field"]],
        }
        for case_id, visibility, value in BROWSER_INPUTS[task_id]
    ]
    return [status, successes[0], invalid, browsers[0], successes[1], successes[2], unknown, browsers[1], browsers[2]]


def build_documents() -> tuple[dict[str, Any], dict[str, Any]]:
    cases = {task["id"]: task_cases(task) for task in TASKS}
    tasks = json.loads(json.dumps(TASKS))
    for task in tasks:
        rows = cases[task["id"]]
        task["public_case_ids"] = [row["id"] for row in rows if row["visibility"] == "public"]
        task["hidden_case_ids"] = [row["id"] for row in rows if row["visibility"] == "hidden"]
    return (
        {
            "schema_version": 1,
            "experiment_id": "044",
            "description": "Two new full-stack implementation assignments and two new maintenance assignments, frozen after the v0.5.5 product checkpoint and before stack scaffolds, reference implementations, protocol thresholds, or measured agent output.",
            "frozen_on": "2026-08-13",
            "product_freeze_commit": PRODUCT_FREEZE_COMMIT,
            "product_freeze_sha256": PRODUCT_FREEZE_SHA256,
            "common_contract": COMMON_CONTRACT,
            "tasks": tasks,
        },
        {"schema_version": 1, "experiment_id": "044", "tasks": cases},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks-output", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--cases-output", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()
    tasks, cases = build_documents()
    args.tasks_output.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    args.cases_output.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tasks": str(args.tasks_output), "cases": str(args.cases_output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
