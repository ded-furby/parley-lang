#!/usr/bin/env python3
"""Build the deterministic semantics-only corpus for full-stack study 043."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
DEFAULT_TASKS = BENCHMARKS / "fullstack_agent_043_tasks.json"
DEFAULT_CASES = BENCHMARKS / "fullstack_agent_043_cases.json"
PRODUCT_FREEZE_COMMIT = "863c3d6d18911b565f8e91efaebf24fe90978176"
PRODUCT_FREEZE_SHA256 = "1ca7bb4fe501eda55991af61cabb715c5c5c53e202df976ef051809576635ed0"


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
        "id": "wildfire_drone_build",
        "kind": "implementation",
        "title": "Build a wildfire drone mission planner across HTTP and browser targets",
        "statement": "Implement the frozen Wildfire Drone contract in the supplied stack. drone_total is scout_drones + cargo_drones. scout_flight_minutes is scout_drones * 13. cargo_flight_minutes is cargo_drones * 21. night_setup_minutes is launch_pads * 8 during a night_mission and zero otherwise. mission_load_minutes is scout_flight_minutes + cargo_flight_minutes + night_setup_minutes. launch_capacity_minutes is launch_pads * 50. completed_flight_minutes is min(mission_load_minutes, launch_capacity_minutes). delayed_flight_minutes is max(mission_load_minutes - launch_capacity_minutes, 0). flight_waves is mission_load_minutes divided by 40 using floor division. wildfire_score is completed_flight_minutes + delayed_flight_minutes * 6 + flight_waves * 9. wildfire_mode is ready when delayed_flight_minutes is zero, night_delay when delay remains during a night mission, and day_delay otherwise. The browser export returns wildfire_score.",
        "service": "Wildfire Drone",
        "status_route": "/status/wildfire-drone-ready",
        "post_route": "/api/v7/wildfire-drone",
        "browser_export": "wildfire_mission_score",
        "shared_result_field": "wildfire_score",
        "request_fields": {
            "scout_drones": "number",
            "cargo_drones": "number",
            "launch_pads": "number",
            "night_mission": "yesno",
        },
        "response_fields": {
            "drone_total": "number",
            "scout_flight_minutes": "number",
            "cargo_flight_minutes": "number",
            "night_setup_minutes": "number",
            "mission_load_minutes": "number",
            "launch_capacity_minutes": "number",
            "completed_flight_minutes": "number",
            "delayed_flight_minutes": "number",
            "flight_waves": "number",
            "wildfire_score": "number",
            "wildfire_mode": "text",
        },
        "independence": "New wildfire-drone domain, v7 route, flight-wave and mission formulas, vocabulary, fixtures, and browser export selected after the v0.5.4 product freeze and before any 043 scaffold or model output.",
    },
    {
        "id": "satellite_uplink_build",
        "kind": "implementation",
        "title": "Build a satellite uplink scheduler across HTTP and browser targets",
        "statement": "Implement the frozen Satellite Uplink contract in the supplied stack. uplink_packet_total is science_packets + navigation_packets. science_transmit_seconds is science_packets * 6. navigation_transmit_seconds is navigation_packets * 10. interference_seconds is ground_antennas * 7 during solar_interference and zero otherwise. transmit_seconds is science_transmit_seconds + navigation_transmit_seconds + interference_seconds. antenna_capacity_seconds is ground_antennas * 44. sent_seconds is min(transmit_seconds, antenna_capacity_seconds). queued_seconds is max(transmit_seconds - antenna_capacity_seconds, 0). transmission_windows is transmit_seconds divided by 25 using floor division. uplink_score is sent_seconds + queued_seconds * 7 + transmission_windows * 12. uplink_mode is synchronized when queued_seconds is zero, solar_queue when delay remains during solar interference, and routine_queue otherwise. The browser export returns uplink_score.",
        "service": "Satellite Uplink",
        "status_route": "/status/satellite-uplink-ready",
        "post_route": "/api/v7/satellite-uplink",
        "browser_export": "satellite_uplink_score",
        "shared_result_field": "uplink_score",
        "request_fields": {
            "science_packets": "number",
            "navigation_packets": "number",
            "ground_antennas": "number",
            "solar_interference": "yesno",
        },
        "response_fields": {
            "uplink_packet_total": "number",
            "science_transmit_seconds": "number",
            "navigation_transmit_seconds": "number",
            "interference_seconds": "number",
            "transmit_seconds": "number",
            "antenna_capacity_seconds": "number",
            "sent_seconds": "number",
            "queued_seconds": "number",
            "transmission_windows": "number",
            "uplink_score": "number",
            "uplink_mode": "text",
        },
        "independence": "New satellite-uplink domain, v7 route, antenna and transmission-window formulas, vocabulary, fixtures, and browser export selected after the v0.5.4 product freeze and before any 043 scaffold or model output.",
    },
    {
        "id": "alpine_gondola_repair",
        "kind": "maintenance",
        "title": "Repair transposed load coefficients in an alpine gondola",
        "statement": "Repair the supplied Alpine Gondola application. gondola_item_total is passenger_groups + supply_crates. rider_load_units is passenger_groups * 8. freight_load_units is supply_crates * 13. express_load_units is gondola_cabins * 5 during express_service and zero otherwise. gondola_required_units is rider_load_units + freight_load_units + express_load_units. gondola_capacity_units is gondola_cabins * 42. carried_load_units is min(gondola_required_units, gondola_capacity_units). stranded_load_units is max(gondola_required_units - gondola_capacity_units, 0). lift_margin_units is max(gondola_capacity_units - carried_load_units, 0). gondola_condition is clear when stranded_load_units is zero, express_stranded when load remains during express service, and standard_stranded otherwise. The HTTP response and browser export must use the same rule; the browser export returns lift_margin_units.",
        "service": "Alpine Gondola",
        "status_route": "/status/alpine-gondola-ready",
        "post_route": "/api/v7/alpine-gondola",
        "browser_export": "gondola_lift_margin",
        "shared_result_field": "lift_margin_units",
        "request_fields": {
            "passenger_groups": "number",
            "supply_crates": "number",
            "gondola_cabins": "number",
            "express_service": "yesno",
        },
        "response_fields": {
            "gondola_item_total": "number",
            "rider_load_units": "number",
            "freight_load_units": "number",
            "express_load_units": "number",
            "gondola_required_units": "number",
            "gondola_capacity_units": "number",
            "carried_load_units": "number",
            "stranded_load_units": "number",
            "lift_margin_units": "number",
            "gondola_condition": "text",
        },
        "predeclared_defect": "The application-logic module transposes the passenger-group and supply-crate coefficients, multiplying passenger_groups by 13 and supply_crates by 8.",
        "root_cause_role": "application_logic",
        "historical_grounding": "synthetic coefficient-transposition defect",
        "adaptation_boundary": "The two coefficients, alpine-gondola vocabulary, fixtures, and expected repair are new and were selected after the v0.5.4 product freeze and before any measured output.",
    },
    {
        "id": "kelp_hatchery_repair",
        "kind": "maintenance",
        "title": "Repair delivered-oxygen selection in a kelp hatchery",
        "statement": "Repair the supplied Kelp Hatchery application. hatchery_tank_total is juvenile_tanks + mature_tanks. juvenile_oxygen_units is juvenile_tanks * 9. mature_oxygen_units is mature_tanks * 16. treatment_oxygen_units is aerators * 4 during heat_treatment and zero otherwise. oxygen_needed_units is juvenile_oxygen_units + mature_oxygen_units + treatment_oxygen_units. aeration_capacity_units is aerators * 38. oxygen_delivered_units is min(oxygen_needed_units, aeration_capacity_units). oxygen_deficit_units is max(oxygen_needed_units - aeration_capacity_units, 0). oxygen_buffer_units is max(aeration_capacity_units - oxygen_delivered_units, 0). hatchery_condition is balanced when oxygen_deficit_units is zero, heat_shortage when a deficit remains during heat treatment, and oxygen_shortage otherwise. The HTTP response and browser export must use the same rule; the browser export returns oxygen_delivered_units.",
        "service": "Kelp Hatchery",
        "status_route": "/status/kelp-hatchery-ready",
        "post_route": "/api/v7/kelp-hatchery",
        "browser_export": "hatchery_oxygen_delivered",
        "shared_result_field": "oxygen_delivered_units",
        "request_fields": {
            "juvenile_tanks": "number",
            "mature_tanks": "number",
            "aerators": "number",
            "heat_treatment": "yesno",
        },
        "response_fields": {
            "hatchery_tank_total": "number",
            "juvenile_oxygen_units": "number",
            "mature_oxygen_units": "number",
            "treatment_oxygen_units": "number",
            "oxygen_needed_units": "number",
            "aeration_capacity_units": "number",
            "oxygen_delivered_units": "number",
            "oxygen_deficit_units": "number",
            "oxygen_buffer_units": "number",
            "hatchery_condition": "text",
        },
        "predeclared_defect": "The application-logic module selects max(oxygen_needed_units, aeration_capacity_units) for oxygen_delivered_units instead of min, reporting oxygen that cannot be supplied or consumed.",
        "root_cause_role": "application_logic",
        "historical_grounding": "synthetic extremum-selector inversion defect",
        "adaptation_boundary": "The delivered-oxygen extremum, kelp-hatchery vocabulary, fixtures, and expected repair are new and were selected after the v0.5.4 product freeze and before any measured output.",
    },
]


def oracle(task_id: str, value: dict[str, Any]) -> dict[str, Any]:
    if task_id == "wildfire_drone_build":
        total = value["scout_drones"] + value["cargo_drones"]
        scout = value["scout_drones"] * 13
        cargo = value["cargo_drones"] * 21
        night = value["launch_pads"] * 8 if value["night_mission"] else 0
        required = scout + cargo + night
        capacity = value["launch_pads"] * 50
        completed = min(required, capacity)
        delayed = max(required - capacity, 0)
        waves = required // 40
        return {
            "drone_total": total,
            "scout_flight_minutes": scout,
            "cargo_flight_minutes": cargo,
            "night_setup_minutes": night,
            "mission_load_minutes": required,
            "launch_capacity_minutes": capacity,
            "completed_flight_minutes": completed,
            "delayed_flight_minutes": delayed,
            "flight_waves": waves,
            "wildfire_score": completed + delayed * 6 + waves * 9,
            "wildfire_mode": "ready" if delayed == 0 else "night_delay" if value["night_mission"] else "day_delay",
        }
    if task_id == "satellite_uplink_build":
        total = value["science_packets"] + value["navigation_packets"]
        science = value["science_packets"] * 6
        navigation = value["navigation_packets"] * 10
        interference = value["ground_antennas"] * 7 if value["solar_interference"] else 0
        required = science + navigation + interference
        capacity = value["ground_antennas"] * 44
        sent = min(required, capacity)
        queued = max(required - capacity, 0)
        windows = required // 25
        return {
            "uplink_packet_total": total,
            "science_transmit_seconds": science,
            "navigation_transmit_seconds": navigation,
            "interference_seconds": interference,
            "transmit_seconds": required,
            "antenna_capacity_seconds": capacity,
            "sent_seconds": sent,
            "queued_seconds": queued,
            "transmission_windows": windows,
            "uplink_score": sent + queued * 7 + windows * 12,
            "uplink_mode": "synchronized" if queued == 0 else "solar_queue" if value["solar_interference"] else "routine_queue",
        }
    if task_id == "alpine_gondola_repair":
        total = value["passenger_groups"] + value["supply_crates"]
        rider = value["passenger_groups"] * 8
        freight = value["supply_crates"] * 13
        express = value["gondola_cabins"] * 5 if value["express_service"] else 0
        required = rider + freight + express
        capacity = value["gondola_cabins"] * 42
        carried = min(required, capacity)
        stranded = max(required - capacity, 0)
        return {
            "gondola_item_total": total,
            "rider_load_units": rider,
            "freight_load_units": freight,
            "express_load_units": express,
            "gondola_required_units": required,
            "gondola_capacity_units": capacity,
            "carried_load_units": carried,
            "stranded_load_units": stranded,
            "lift_margin_units": max(capacity - carried, 0),
            "gondola_condition": "clear" if stranded == 0 else "express_stranded" if value["express_service"] else "standard_stranded",
        }
    if task_id == "kelp_hatchery_repair":
        total = value["juvenile_tanks"] + value["mature_tanks"]
        juvenile = value["juvenile_tanks"] * 9
        mature = value["mature_tanks"] * 16
        treatment = value["aerators"] * 4 if value["heat_treatment"] else 0
        needed = juvenile + mature + treatment
        capacity = value["aerators"] * 38
        delivered = min(needed, capacity)
        deficit = max(needed - capacity, 0)
        return {
            "hatchery_tank_total": total,
            "juvenile_oxygen_units": juvenile,
            "mature_oxygen_units": mature,
            "treatment_oxygen_units": treatment,
            "oxygen_needed_units": needed,
            "aeration_capacity_units": capacity,
            "oxygen_delivered_units": delivered,
            "oxygen_deficit_units": deficit,
            "oxygen_buffer_units": max(capacity - delivered, 0),
            "hatchery_condition": "balanced" if deficit == 0 else "heat_shortage" if value["heat_treatment"] else "oxygen_shortage",
        }
    raise AssertionError(task_id)


SUCCESS_INPUTS = {
    "wildfire_drone_build": [
        ("wildfire_drone_night_delay", "public", {"scout_drones": 2, "cargo_drones": 3, "launch_pads": 2, "night_mission": True}),
        ("wildfire_drone_ready", "hidden", {"scout_drones": 1, "cargo_drones": 1, "launch_pads": 2, "night_mission": False}),
        ("wildfire_drone_day_delay", "hidden", {"scout_drones": 4, "cargo_drones": 3, "launch_pads": 2, "night_mission": False}),
    ],
    "satellite_uplink_build": [
        ("satellite_uplink_solar_queue", "public", {"science_packets": 4, "navigation_packets": 3, "ground_antennas": 1, "solar_interference": True}),
        ("satellite_uplink_synchronized", "hidden", {"science_packets": 2, "navigation_packets": 1, "ground_antennas": 2, "solar_interference": False}),
        ("satellite_uplink_routine_queue", "hidden", {"science_packets": 8, "navigation_packets": 2, "ground_antennas": 1, "solar_interference": False}),
    ],
    "alpine_gondola_repair": [
        ("alpine_gondola_clear", "public", {"passenger_groups": 3, "supply_crates": 2, "gondola_cabins": 2, "express_service": True}),
        ("alpine_gondola_standard_stranded", "hidden", {"passenger_groups": 6, "supply_crates": 3, "gondola_cabins": 2, "express_service": False}),
        ("alpine_gondola_express_stranded", "hidden", {"passenger_groups": 5, "supply_crates": 4, "gondola_cabins": 2, "express_service": True}),
    ],
    "kelp_hatchery_repair": [
        ("kelp_hatchery_balanced", "public", {"juvenile_tanks": 2, "mature_tanks": 1, "aerators": 2, "heat_treatment": True}),
        ("kelp_hatchery_heat_shortage", "hidden", {"juvenile_tanks": 4, "mature_tanks": 3, "aerators": 1, "heat_treatment": True}),
        ("kelp_hatchery_oxygen_shortage", "hidden", {"juvenile_tanks": 3, "mature_tanks": 2, "aerators": 1, "heat_treatment": False}),
    ],
}


BROWSER_INPUTS = {
    "wildfire_drone_build": [
        ("wildfire_drone_browser_night", "public", SUCCESS_INPUTS["wildfire_drone_build"][0][2]),
        ("wildfire_drone_browser_ready", "hidden", SUCCESS_INPUTS["wildfire_drone_build"][1][2]),
        ("wildfire_drone_browser_day", "hidden", SUCCESS_INPUTS["wildfire_drone_build"][2][2]),
    ],
    "satellite_uplink_build": [
        ("satellite_uplink_browser_solar", "public", SUCCESS_INPUTS["satellite_uplink_build"][0][2]),
        ("satellite_uplink_browser_sync", "hidden", SUCCESS_INPUTS["satellite_uplink_build"][1][2]),
        ("satellite_uplink_browser_routine", "hidden", SUCCESS_INPUTS["satellite_uplink_build"][2][2]),
    ],
    "alpine_gondola_repair": [
        ("alpine_gondola_browser_clear", "public", SUCCESS_INPUTS["alpine_gondola_repair"][0][2]),
        ("alpine_gondola_browser_standard", "hidden", {"passenger_groups": 1, "supply_crates": 3, "gondola_cabins": 2, "express_service": False}),
        ("alpine_gondola_browser_express", "hidden", {"passenger_groups": 4, "supply_crates": 1, "gondola_cabins": 2, "express_service": True}),
    ],
    "kelp_hatchery_repair": [
        ("kelp_hatchery_browser_balanced", "public", SUCCESS_INPUTS["kelp_hatchery_repair"][0][2]),
        ("kelp_hatchery_browser_heat", "hidden", SUCCESS_INPUTS["kelp_hatchery_repair"][1][2]),
        ("kelp_hatchery_browser_oxygen", "hidden", SUCCESS_INPUTS["kelp_hatchery_repair"][2][2]),
    ],
}


INVALID_CASES = {
    "wildfire_drone_build": {
        "id": "wildfire_drone_wrong_pad_type", "visibility": "public", "target": "http", "method": "POST",
        "json": {"scout_drones": 2, "cargo_drones": 3, "launch_pads": True, "night_mission": True},
        "expected_status": 400, "expected_error": "invalid_json",
    },
    "satellite_uplink_build": {
        "id": "satellite_uplink_wrong_media", "visibility": "public", "target": "http", "method": "POST",
        "raw_body": "{}", "content_type": "text/plain", "expected_status": 415, "expected_error": "json_content_type_required",
    },
    "alpine_gondola_repair": {
        "id": "alpine_gondola_missing_cabins", "visibility": "public", "target": "http", "method": "POST",
        "json": {"passenger_groups": 3, "supply_crates": 2, "express_service": True},
        "expected_status": 400, "expected_error": "invalid_json",
    },
    "kelp_hatchery_repair": {
        "id": "kelp_hatchery_wrong_heat_type", "visibility": "public", "target": "http", "method": "POST",
        "json": {"juvenile_tanks": 2, "mature_tanks": 1, "aerators": 2, "heat_treatment": 1},
        "expected_status": 400, "expected_error": "invalid_json",
    },
}


UNKNOWN_FIELDS = {
    "wildfire_drone_build": ("wind_sector", 4),
    "satellite_uplink_build": ("orbital_lane", 3),
    "alpine_gondola_repair": ("snow_depth", 6),
    "kelp_hatchery_repair": ("salinity_band", 2),
}


def task_cases(task: dict[str, Any]) -> list[dict[str, Any]]:
    task_id = task["id"]
    status = {
        "id": task_id.removesuffix("_build").removesuffix("_repair") + "_status",
        "visibility": "public",
        "target": "http",
        "method": "GET",
        "path": task["status_route"],
        "expected_status": 200,
        "expected_json": {"service": task["service"], "ready": True},
    }
    successes = []
    for case_id, visibility, value in SUCCESS_INPUTS[task_id]:
        successes.append({
            "id": case_id, "visibility": visibility, "target": "http", "method": "POST",
            "path": task["post_route"], "json": value, "expected_status": 200,
            "expected_json": oracle(task_id, value),
        })
    invalid = {**INVALID_CASES[task_id], "path": task["post_route"]}
    unknown_name, unknown_value = UNKNOWN_FIELDS[task_id]
    unknown_input = {**SUCCESS_INPUTS[task_id][0][2], unknown_name: unknown_value}
    unknown = {
        "id": task_id.removesuffix("_build").removesuffix("_repair") + "_unknown_field",
        "visibility": "hidden", "target": "http", "method": "POST", "path": task["post_route"],
        "json": unknown_input, "expected_status": 400, "expected_error": "invalid_json",
    }
    field_order = list(task["request_fields"])
    browsers = []
    for case_id, visibility, value in BROWSER_INPUTS[task_id]:
        result = oracle(task_id, value)
        browsers.append({
            "id": case_id, "visibility": visibility, "target": "browser",
            "export": task["browser_export"], "args": [value[field] for field in field_order],
            "expected": result[task["shared_result_field"]],
        })
    return [status, successes[0], invalid, browsers[0], successes[1], successes[2], unknown, browsers[1], browsers[2]]


def build_documents() -> tuple[dict[str, Any], dict[str, Any]]:
    cases = {task["id"]: task_cases(task) for task in TASKS}
    tasks = json.loads(json.dumps(TASKS))
    for task in tasks:
        task_cases_for_id = cases[task["id"]]
        task["public_case_ids"] = [case["id"] for case in task_cases_for_id if case["visibility"] == "public"]
        task["hidden_case_ids"] = [case["id"] for case in task_cases_for_id if case["visibility"] == "hidden"]
    task_document = {
        "schema_version": 1,
        "experiment_id": "043",
        "description": "Two new full-stack implementation assignments and two new maintenance assignments, frozen after the v0.5.4 product checkpoint and before stack scaffolds, reference implementations, protocol thresholds, or measured agent output.",
        "frozen_on": "2026-08-13",
        "product_freeze_commit": PRODUCT_FREEZE_COMMIT,
        "product_freeze_sha256": PRODUCT_FREEZE_SHA256,
        "common_contract": COMMON_CONTRACT,
        "tasks": tasks,
    }
    case_document = {
        "schema_version": 1,
        "experiment_id": "043",
        "tasks": cases,
    }
    return task_document, case_document


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
