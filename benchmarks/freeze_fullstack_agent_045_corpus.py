#!/usr/bin/env python3
"""Build the deterministic semantics-only corpus for full-stack study 045."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
DEFAULT_TASKS = BENCHMARKS / "fullstack_agent_045_tasks.json"
DEFAULT_CASES = BENCHMARKS / "fullstack_agent_045_cases.json"
PRODUCT_FREEZE_COMMIT = "6b39eeffca34c7a9b05e1596eb8e8b4d3272a8e4"
PRODUCT_FREEZE_SHA256 = "49e1ee43ce014e3888a193442e426269f7bdf19b0403ab29a2b3a40505596216"


COMMON_CONTRACT = {
    "server": (
        "Expose the exact GET status route and typed POST JSON route declared by "
        "the task. The POST route uses the frozen dynamic status/header/body "
        "response envelope. Request header names are compared case-insensitively."
    ),
    "request_precedence": (
        "Typed JSON decoding precedes handler authorization and domain decisions. "
        "Malformed JSON, missing/unknown fields, and wrong JSON types therefore "
        "return the generated 400 invalid_json response before a typed envelope."
    ),
    "transport_errors": (
        "Return 415 json_content_type_required without application/json and 413 "
        "body_too_large above 16384 bytes."
    ),
    "dynamic_response": (
        "Return the exact task status, JSON body, and custom headers. Content-Type, "
        "Content-Length, Connection, and X-Content-Type-Options remain server-owned."
    ),
    "browser": (
        "Expose the declared deterministic scalar browser function as an ES module "
        "export and return the exact frozen values in real Chromium."
    ),
    "cross_target": (
        "For an authorized, domain-valid request, the response field named by "
        "shared_result_field equals the browser export for the same numeric/boolean inputs."
    ),
    "network": "Bind only to 127.0.0.1 on the harness-selected port.",
    "body_limit_bytes": 16384,
    "response_envelope": {
        "status_field": "status", "headers_field": "headers", "body_field": "body",
    },
}


TASKS = [
    {
        "id": "artifact_accession_build",
        "kind": "implementation",
        "title": "Build an authenticated artifact accession workflow",
        "statement": (
            "Implement the frozen Artifact Accession contract. The POST route requires "
            "Authorization: Bearer accession-045; otherwise return 401 with "
            "www-authenticate Bearer realm=artifact-accession and accession_state "
            "authorization_required. Negative numeric inputs return 422 with "
            "x-validation nonnegative. A positive artifact_total with zero packing_stations "
            "returns 422 with x-validation packing_stations. Otherwise artifact_total is "
            "stable_units + fragile_units. packing_units is stable_units * 6 + "
            "fragile_units * 11 plus packing_stations * 4 when expedited. "
            "capacity_units is packing_stations * 40. overflow_units is max(packing_units "
            "- capacity_units, 0). inspection_rounds is artifact_total divided by 5 using "
            "floor division. priority_score is packing_units + overflow_units * 5 + "
            "inspection_rounds * 7. accession_state is accepted when overflow is zero and "
            "queued otherwise. Success returns 201 with location "
            "/api/v9/artifact-accessions/{accession_key} and x-accession-state. The browser "
            "export returns priority_score. Failure bodies use the request key and zero for "
            "all numeric result fields."
        ),
        "service": "Artifact Accession",
        "status_route": "/status/artifact-accession-ready",
        "post_route": "/api/v9/artifact-accessions",
        "browser_export": "artifact_priority_score",
        "browser_fields": ["stable_units", "fragile_units", "packing_stations", "expedited"],
        "shared_result_field": "priority_score",
        "request_fields": {
            "accession_key": "text", "stable_units": "number",
            "fragile_units": "number", "packing_stations": "number",
            "expedited": "yesno",
        },
        "response_fields": {
            "accession_key": "text", "artifact_total": "number",
            "packing_units": "number", "capacity_units": "number",
            "overflow_units": "number", "inspection_rounds": "number",
            "priority_score": "number", "accession_state": "text",
        },
        "authorization": {
            "header": "authorization", "value": "Bearer accession-045",
            "failure_status": 401,
            "failure_headers": {"www-authenticate": "Bearer realm=artifact-accession"},
        },
        "success_status": 201,
        "independence": (
            "New authenticated artifact-accession workflow, v9 routes, response statuses, "
            "headers, formulas, vocabulary, fixtures, and browser export selected after "
            "the v0.5.6 product freeze and before any 045 scaffold or model output."
        ),
    },
    {
        "id": "microgrid_bid_build",
        "kind": "implementation",
        "title": "Build an authenticated asynchronous microgrid bid workflow",
        "statement": (
            "Implement the frozen Microgrid Bid contract. The POST route requires "
            "x-grid-key: grid-045; otherwise return 401 with www-authenticate GridKey and "
            "bid_state authorization_required. Negative numeric inputs return 422 with "
            "x-validation nonnegative. Positive generation with zero interconnects returns "
            "422 with x-validation interconnects. A duplicate_bid returns 409 with "
            "x-conflict duplicate_bid. Otherwise generation_units is solar_arrays * 9 + "
            "wind_turbines * 13. battery_buffer_units is storage_banks * 7 during "
            "emergency_mode and storage_banks * 3 otherwise. grid_required_units is generation "
            "+ buffer. grid_capacity_units is interconnects * 55. delivered_units is the "
            "minimum of required and capacity. shortfall_units is max(required - capacity, "
            "0). dispatch_windows is grid_required_units divided by 31 using floor division. "
            "bid_score is delivered_units + shortfall_units * 4 + dispatch_windows * 9. "
            "bid_state is accepted when shortfall is zero, emergency_shortfall during "
            "emergency mode, and routine_shortfall otherwise. Success returns 202 with "
            "location /api/v9/microgrid-bids/{bid_key}, retry-after 3, and x-bid-state. "
            "The browser export returns bid_score. Failure bodies use the request key and "
            "zero numeric fields."
        ),
        "service": "Microgrid Bid",
        "status_route": "/status/microgrid-bid-ready",
        "post_route": "/api/v9/microgrid-bids",
        "browser_export": "microgrid_bid_score",
        "browser_fields": [
            "solar_arrays", "wind_turbines", "storage_banks", "interconnects",
            "emergency_mode",
        ],
        "shared_result_field": "bid_score",
        "request_fields": {
            "bid_key": "text", "solar_arrays": "number", "wind_turbines": "number",
            "storage_banks": "number", "interconnects": "number",
            "emergency_mode": "yesno", "duplicate_bid": "yesno",
        },
        "response_fields": {
            "bid_key": "text", "generation_units": "number",
            "battery_buffer_units": "number", "grid_required_units": "number",
            "grid_capacity_units": "number", "delivered_units": "number",
            "shortfall_units": "number", "dispatch_windows": "number",
            "bid_score": "number", "bid_state": "text",
        },
        "authorization": {
            "header": "x-grid-key", "value": "grid-045", "failure_status": 401,
            "failure_headers": {"www-authenticate": "GridKey"},
        },
        "success_status": 202,
        "independence": (
            "New authenticated asynchronous microgrid-bid workflow, v9 routes, conflict "
            "and validation branches, headers, formulas, vocabulary, fixtures, and browser "
            "export selected after the v0.5.6 product freeze."
        ),
    },
    {
        "id": "trail_permit_repair",
        "kind": "maintenance",
        "title": "Repair authorization polarity in a trail permit workflow",
        "statement": (
            "Repair the supplied Trail Permit application. The POST route requires "
            "Authorization: Bearer trail-045; otherwise return 401 with www-authenticate "
            "Bearer realm=trail-permit and permit_state authorization_required. Negative "
            "numeric inputs return 422 with x-validation nonnegative. Positive visitor_total "
            "with zero trail_guides returns 422 with x-validation trail_guides. Otherwise "
            "visitor_total is day_hikers + overnight_hikers. trail_units is day_hikers * 5 "
            "+ overnight_hikers * 12 plus trail_guides * 6 during storm_alert. "
            "guide_capacity_units is trail_guides * 38. admitted_units is min(trail_units, "
            "capacity). waiting_units is max(trail_units - capacity, 0). permit_score is "
            "admitted_units + waiting_units * 6. permit_state is issued when waiting is zero, "
            "storm_queue during a storm, and routine_queue otherwise. Success returns 200 "
            "with x-permit-state. The browser export returns permit_score. Failure bodies "
            "use the request code and zero numeric fields."
        ),
        "service": "Trail Permit",
        "status_route": "/status/trail-permit-ready",
        "post_route": "/api/v9/trail-permits",
        "browser_export": "trail_permit_score",
        "browser_fields": [
            "day_hikers", "overnight_hikers", "trail_guides", "storm_alert",
        ],
        "shared_result_field": "permit_score",
        "request_fields": {
            "permit_code": "text", "day_hikers": "number",
            "overnight_hikers": "number", "trail_guides": "number",
            "storm_alert": "yesno",
        },
        "response_fields": {
            "permit_code": "text", "visitor_total": "number", "trail_units": "number",
            "guide_capacity_units": "number", "admitted_units": "number",
            "waiting_units": "number", "permit_score": "number", "permit_state": "text",
        },
        "authorization": {
            "header": "authorization", "value": "Bearer trail-045",
            "failure_status": 401,
            "failure_headers": {"www-authenticate": "Bearer realm=trail-permit"},
        },
        "success_status": 200,
        "predeclared_defect": (
            "The route-handler module reverses the bearer-token comparison, denying the "
            "correct token and allowing an incorrect token."
        ),
        "root_cause_role": "route_handler",
        "historical_grounding": "synthetic authorization-polarity inversion defect",
        "adaptation_boundary": (
            "The authorization polarity, trail-permit workflow, v9 routes, statuses, "
            "headers, formulas, fixtures, and expected repair were selected only after "
            "the v0.5.6 product freeze."
        ),
    },
    {
        "id": "cold_chain_booking_repair",
        "kind": "maintenance",
        "title": "Repair a server-owned header in a cold-chain booking workflow",
        "statement": (
            "Repair the supplied Cold-Chain Booking application. Negative numeric inputs "
            "return 422 with x-validation nonnegative. A positive shipment_total with zero "
            "loading_docks returns 422 with x-validation loading_docks. Otherwise "
            "shipment_total is chilled_crates + frozen_crates. cooling_units is "
            "chilled_crates * 7 + frozen_crates * 15 plus loading_docks * 5 during rush_load. "
            "dock_capacity_units is loading_docks * 44. loaded_units is min(cooling_units, "
            "capacity). deferred_units is max(cooling_units - capacity, 0). loading_rounds "
            "is shipment_total divided by 6 using floor division. booking_score is "
            "loaded_units + deferred_units * 5 + loading_rounds * 8. booking_state is booked "
            "when deferred is zero, rush_queue during rush load, and routine_queue otherwise. "
            "Success returns 201 with location /api/v9/cold-chain-bookings/{booking_code} "
            "and x-booking-state. The browser export returns booking_score. Validation "
            "bodies use the request code and zero numeric fields."
        ),
        "service": "Cold-Chain Booking",
        "status_route": "/status/cold-chain-booking-ready",
        "post_route": "/api/v9/cold-chain-bookings",
        "browser_export": "cold_chain_booking_score",
        "browser_fields": [
            "chilled_crates", "frozen_crates", "loading_docks", "rush_load",
        ],
        "shared_result_field": "booking_score",
        "request_fields": {
            "booking_code": "text", "chilled_crates": "number",
            "frozen_crates": "number", "loading_docks": "number", "rush_load": "yesno",
        },
        "response_fields": {
            "booking_code": "text", "shipment_total": "number", "cooling_units": "number",
            "dock_capacity_units": "number", "loaded_units": "number",
            "deferred_units": "number", "loading_rounds": "number",
            "booking_score": "number", "booking_state": "text",
        },
        "success_status": 201,
        "predeclared_defect": (
            "The route-handler module writes the generated Location value under the "
            "server-owned content-length header, so valid creation responses become 500 "
            "invalid_response_headers instead of 201."
        ),
        "root_cause_role": "route_handler",
        "historical_grounding": "synthetic server-owned response-header substitution defect",
        "adaptation_boundary": (
            "The reserved-header defect, cold-chain workflow, v9 routes, formulas, fixtures, "
            "and expected repair were selected only after the v0.5.6 product freeze."
        ),
    },
]


def zero_body(task: dict[str, Any], key: str, state: str) -> dict[str, Any]:
    fields = list(task["response_fields"])
    return {name: key if index == 0 else state if index == len(fields) - 1 else 0
            for index, name in enumerate(fields)}


def oracle(task_id: str, value: dict[str, Any]) -> dict[str, Any]:
    if task_id == "artifact_accession_build":
        total = value["stable_units"] + value["fragile_units"]
        packing = value["stable_units"] * 6 + value["fragile_units"] * 11
        if value["expedited"]:
            packing += value["packing_stations"] * 4
        capacity = value["packing_stations"] * 40
        overflow = max(packing - capacity, 0)
        rounds = total // 5
        return {
            "accession_key": value["accession_key"], "artifact_total": total,
            "packing_units": packing, "capacity_units": capacity,
            "overflow_units": overflow, "inspection_rounds": rounds,
            "priority_score": packing + overflow * 5 + rounds * 7,
            "accession_state": "accepted" if overflow == 0 else "queued",
        }
    if task_id == "microgrid_bid_build":
        generation = value["solar_arrays"] * 9 + value["wind_turbines"] * 13
        buffer = value["storage_banks"] * (7 if value["emergency_mode"] else 3)
        required = generation + buffer
        capacity = value["interconnects"] * 55
        delivered, shortfall = min(required, capacity), max(required - capacity, 0)
        windows = required // 31
        return {
            "bid_key": value["bid_key"], "generation_units": generation,
            "battery_buffer_units": buffer, "grid_required_units": required,
            "grid_capacity_units": capacity, "delivered_units": delivered,
            "shortfall_units": shortfall, "dispatch_windows": windows,
            "bid_score": delivered + shortfall * 4 + windows * 9,
            "bid_state": ("accepted" if shortfall == 0 else
                          "emergency_shortfall" if value["emergency_mode"] else
                          "routine_shortfall"),
        }
    if task_id == "trail_permit_repair":
        total = value["day_hikers"] + value["overnight_hikers"]
        units = value["day_hikers"] * 5 + value["overnight_hikers"] * 12
        if value["storm_alert"]:
            units += value["trail_guides"] * 6
        capacity = value["trail_guides"] * 38
        admitted, waiting = min(units, capacity), max(units - capacity, 0)
        return {
            "permit_code": value["permit_code"], "visitor_total": total,
            "trail_units": units, "guide_capacity_units": capacity,
            "admitted_units": admitted, "waiting_units": waiting,
            "permit_score": admitted + waiting * 6,
            "permit_state": ("issued" if waiting == 0 else
                             "storm_queue" if value["storm_alert"] else "routine_queue"),
        }
    if task_id == "cold_chain_booking_repair":
        total = value["chilled_crates"] + value["frozen_crates"]
        cooling = value["chilled_crates"] * 7 + value["frozen_crates"] * 15
        if value["rush_load"]:
            cooling += value["loading_docks"] * 5
        capacity = value["loading_docks"] * 44
        loaded, deferred = min(cooling, capacity), max(cooling - capacity, 0)
        rounds = total // 6
        return {
            "booking_code": value["booking_code"], "shipment_total": total,
            "cooling_units": cooling, "dock_capacity_units": capacity,
            "loaded_units": loaded, "deferred_units": deferred,
            "loading_rounds": rounds,
            "booking_score": loaded + deferred * 5 + rounds * 8,
            "booking_state": ("booked" if deferred == 0 else
                              "rush_queue" if value["rush_load"] else "routine_queue"),
        }
    raise AssertionError(task_id)


def negative_numeric(task: dict[str, Any], value: dict[str, Any]) -> bool:
    return any(value[name] < 0 for name, ty in task["request_fields"].items()
               if ty == "number")


def outcome(task: dict[str, Any], value: dict[str, Any], headers: dict[str, str]) -> tuple[int, dict[str, str], dict[str, Any]]:
    task_id = task["id"]
    key = value[next(iter(task["request_fields"]))]
    auth = task.get("authorization")
    if auth and headers.get(auth["header"], "") != auth["value"]:
        return auth["failure_status"], auth["failure_headers"], zero_body(
            task, key, "authorization_required")
    if negative_numeric(task, value):
        return 422, {"x-validation": "nonnegative"}, zero_body(task, key, "invalid")
    zero_field = {
        "artifact_accession_build": ("packing_stations", "artifact_total"),
        "microgrid_bid_build": ("interconnects", "generation_units"),
        "trail_permit_repair": ("trail_guides", "visitor_total"),
        "cold_chain_booking_repair": ("loading_docks", "shipment_total"),
    }[task_id]
    body = oracle(task_id, value)
    if value[zero_field[0]] == 0 and body[zero_field[1]] > 0:
        return 422, {"x-validation": zero_field[0]}, zero_body(task, key, "invalid")
    if task_id == "microgrid_bid_build" and value["duplicate_bid"]:
        return 409, {"x-conflict": "duplicate_bid"}, zero_body(task, key, "duplicate")
    if task_id == "artifact_accession_build":
        response_headers = {
            "location": f"/api/v9/artifact-accessions/{key}",
            "x-accession-state": body["accession_state"],
        }
    elif task_id == "microgrid_bid_build":
        response_headers = {
            "location": f"/api/v9/microgrid-bids/{key}", "retry-after": "3",
            "x-bid-state": body["bid_state"],
        }
    elif task_id == "trail_permit_repair":
        response_headers = {"x-permit-state": body["permit_state"]}
    else:
        response_headers = {
            "location": f"/api/v9/cold-chain-bookings/{key}",
            "x-booking-state": body["booking_state"],
        }
    return task["success_status"], response_headers, body


SUCCESS_INPUTS = {
    "artifact_accession_build": (
        {"accession_key": "bronze-lyre", "stable_units": 3, "fragile_units": 2,
         "packing_stations": 2, "expedited": True},
        {"authorization": "Bearer accession-045"},
    ),
    "microgrid_bid_build": (
        {"bid_key": "sunset-7", "solar_arrays": 3, "wind_turbines": 2,
         "storage_banks": 2, "interconnects": 2, "emergency_mode": True,
         "duplicate_bid": False},
        {"x-grid-key": "grid-045"},
    ),
    "trail_permit_repair": (
        {"permit_code": "ridge-12", "day_hikers": 4, "overnight_hikers": 2,
         "trail_guides": 2, "storm_alert": True},
        {"authorization": "Bearer trail-045"},
    ),
    "cold_chain_booking_repair": (
        {"booking_code": "polar-8", "chilled_crates": 3, "frozen_crates": 2,
         "loading_docks": 2, "rush_load": False},
        {},
    ),
}


HIDDEN_OUTCOMES = {
    "artifact_accession_build": [
        ("artifact_accession_unauthorized", SUCCESS_INPUTS["artifact_accession_build"][0], {}),
        ("artifact_accession_zero_stations",
         {"accession_key": "marble-4", "stable_units": 2, "fragile_units": 1,
          "packing_stations": 0, "expedited": False},
         {"authorization": "Bearer accession-045"}),
    ],
    "microgrid_bid_build": [
        ("microgrid_bid_duplicate",
         {**SUCCESS_INPUTS["microgrid_bid_build"][0], "duplicate_bid": True},
         {"x-grid-key": "grid-045"}),
        ("microgrid_bid_zero_interconnect",
         {"bid_key": "island-3", "solar_arrays": 1, "wind_turbines": 2,
          "storage_banks": 1, "interconnects": 0, "emergency_mode": False,
          "duplicate_bid": False}, {"x-grid-key": "grid-045"}),
    ],
    "trail_permit_repair": [
        ("trail_permit_unauthorized", SUCCESS_INPUTS["trail_permit_repair"][0],
         {"authorization": "Bearer wrong"}),
        ("trail_permit_zero_guides",
         {"permit_code": "valley-2", "day_hikers": 2, "overnight_hikers": 1,
          "trail_guides": 0, "storm_alert": False},
         {"authorization": "Bearer trail-045"}),
    ],
    "cold_chain_booking_repair": [
        ("cold_chain_negative_crates",
         {"booking_code": "frost-5", "chilled_crates": -1, "frozen_crates": 2,
          "loading_docks": 1, "rush_load": False}, {}),
        ("cold_chain_rush_queue",
         {"booking_code": "ice-11", "chilled_crates": 5, "frozen_crates": 4,
          "loading_docks": 1, "rush_load": True}, {}),
    ],
}


BROWSER_INPUTS = {
    "artifact_accession_build": [
        SUCCESS_INPUTS["artifact_accession_build"][0],
        {"accession_key": "a", "stable_units": 1, "fragile_units": 1,
         "packing_stations": 2, "expedited": False},
        {"accession_key": "b", "stable_units": 6, "fragile_units": 4,
         "packing_stations": 1, "expedited": True},
    ],
    "microgrid_bid_build": [
        SUCCESS_INPUTS["microgrid_bid_build"][0],
        {"bid_key": "a", "solar_arrays": 1, "wind_turbines": 1,
         "storage_banks": 1, "interconnects": 2, "emergency_mode": False,
         "duplicate_bid": False},
        {"bid_key": "b", "solar_arrays": 7, "wind_turbines": 5,
         "storage_banks": 2, "interconnects": 1, "emergency_mode": True,
         "duplicate_bid": False},
    ],
    "trail_permit_repair": [
        SUCCESS_INPUTS["trail_permit_repair"][0],
        {"permit_code": "a", "day_hikers": 2, "overnight_hikers": 1,
         "trail_guides": 2, "storm_alert": False},
        {"permit_code": "b", "day_hikers": 8, "overnight_hikers": 4,
         "trail_guides": 1, "storm_alert": True},
    ],
    "cold_chain_booking_repair": [
        SUCCESS_INPUTS["cold_chain_booking_repair"][0],
        {"booking_code": "a", "chilled_crates": 1, "frozen_crates": 1,
         "loading_docks": 2, "rush_load": False},
        {"booking_code": "b", "chilled_crates": 6, "frozen_crates": 4,
         "loading_docks": 1, "rush_load": True},
    ],
}


INVALID_CASES = {
    "artifact_accession_build": {
        "id": "artifact_accession_wrong_fragile_type", "visibility": "public",
        "target": "http", "method": "POST",
        "json": {"accession_key": "bronze-lyre", "stable_units": 3,
                 "fragile_units": True, "packing_stations": 2, "expedited": True},
        "request_headers": {"authorization": "Bearer accession-045"},
        "expected_status": 400, "expected_error": "invalid_json",
    },
    "microgrid_bid_build": {
        "id": "microgrid_bid_wrong_media", "visibility": "public", "target": "http",
        "method": "POST", "raw_body": "{}", "content_type": "text/plain",
        "request_headers": {"x-grid-key": "grid-045"},
        "expected_status": 415, "expected_error": "json_content_type_required",
    },
    "trail_permit_repair": {
        "id": "trail_permit_missing_guides", "visibility": "public", "target": "http",
        "method": "POST", "json": {"permit_code": "ridge-12", "day_hikers": 4,
        "overnight_hikers": 2, "storm_alert": True},
        "request_headers": {"authorization": "Bearer trail-045"},
        "expected_status": 400, "expected_error": "invalid_json",
    },
    "cold_chain_booking_repair": {
        "id": "cold_chain_wrong_dock_type", "visibility": "public", "target": "http",
        "method": "POST", "json": {"booking_code": "polar-8", "chilled_crates": 3,
        "frozen_crates": 2, "loading_docks": False, "rush_load": False},
        "expected_status": 400, "expected_error": "invalid_json",
    },
}


UNKNOWN_FIELDS = {
    "artifact_accession_build": ("gallery_code", "west"),
    "microgrid_bid_build": ("market_zone", 4),
    "trail_permit_repair": ("ranger_post", 2),
    "cold_chain_booking_repair": ("coolant_lane", 3),
}


def task_cases(task: dict[str, Any]) -> list[dict[str, Any]]:
    task_id = task["id"]
    stem = task_id.removesuffix("_build").removesuffix("_repair")
    value, headers = SUCCESS_INPUTS[task_id]
    status_code, response_headers, body = outcome(task, value, headers)
    rows: list[dict[str, Any]] = [
        {
            "id": stem + "_status", "visibility": "public", "target": "http",
            "method": "GET", "path": task["status_route"], "expected_status": 200,
            "expected_json": {"service": task["service"], "ready": True},
            "expected_headers": {},
        },
        {
            "id": stem + "_primary", "visibility": "public", "target": "http",
            "method": "POST", "path": task["post_route"], "json": value,
            "request_headers": headers, "expected_status": status_code,
            "expected_json": body, "expected_headers": response_headers,
        },
        INVALID_CASES[task_id],
        {
            "id": stem + "_browser_primary", "visibility": "public",
            "target": "browser", "export": task["browser_export"],
            "args": [BROWSER_INPUTS[task_id][0][name]
                     for name in task["browser_fields"]],
            "expected": oracle(task_id, BROWSER_INPUTS[task_id][0])[
                task["shared_result_field"]],
        },
    ]
    for case_id, hidden_value, hidden_headers in HIDDEN_OUTCOMES[task_id]:
        hidden_status, custom_headers, hidden_body = outcome(
            task, hidden_value, hidden_headers)
        rows.append({
            "id": case_id, "visibility": "hidden", "target": "http",
            "method": "POST", "path": task["post_route"], "json": hidden_value,
            "request_headers": hidden_headers, "expected_status": hidden_status,
            "expected_json": hidden_body, "expected_headers": custom_headers,
        })
    unknown_value = dict(value)
    field, extra = UNKNOWN_FIELDS[task_id]
    unknown_value[field] = extra
    rows.append({
        "id": stem + "_unknown_field", "visibility": "hidden", "target": "http",
        "method": "POST", "path": task["post_route"], "json": unknown_value,
        "request_headers": headers, "expected_status": 400,
        "expected_error": "invalid_json",
    })
    for index, browser_value in enumerate(BROWSER_INPUTS[task_id][1:], 1):
        rows.append({
            "id": f"{stem}_browser_hidden_{index}", "visibility": "hidden",
            "target": "browser", "export": task["browser_export"],
            "args": [browser_value[name] for name in task["browser_fields"]],
            "expected": oracle(task_id, browser_value)[task["shared_result_field"]],
        })
    return rows


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    cases = {task["id"]: task_cases(task) for task in TASKS}
    tasks = []
    for task in TASKS:
        frozen = dict(task)
        rows = cases[task["id"]]
        frozen["public_case_ids"] = [row["id"] for row in rows
                                     if row["visibility"] == "public"]
        frozen["hidden_case_ids"] = [row["id"] for row in rows
                                     if row["visibility"] == "hidden"]
        tasks.append(frozen)
    return (
        {
            "schema_version": 1,
            "experiment_id": "045",
            "description": (
                "Two dynamic-response implementations and two route-handler repairs, "
                "frozen after the v0.5.6 product checkpoint and before scaffolds, "
                "reference implementations, protocol thresholds, or model output."
            ),
            "frozen_on": "2026-08-13",
            "product_freeze_commit": PRODUCT_FREEZE_COMMIT,
            "product_freeze_sha256": PRODUCT_FREEZE_SHA256,
            "common_contract": COMMON_CONTRACT,
            "tasks": tasks,
        },
        {
            "schema_version": 1,
            "experiment_id": "045",
            "visibility_policy": (
                "Prompts expose only public case IDs and expected outcomes. Hidden cases "
                "remain parent-owned and are never placed in agent workspaces."
            ),
            "tasks": cases,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks-output", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--cases-output", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()
    tasks, cases = build()
    args.tasks_output.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    args.cases_output.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "tasks": len(TASKS),
        "cases": sum(len(rows) for rows in cases["tasks"].values()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
