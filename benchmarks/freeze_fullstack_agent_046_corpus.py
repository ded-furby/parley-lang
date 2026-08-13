#!/usr/bin/env python3
"""Build the deterministic semantics-only corpus for full-stack study 046."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
DEFAULT_TASKS = BENCHMARKS / "fullstack_agent_046_tasks.json"
DEFAULT_CASES = BENCHMARKS / "fullstack_agent_046_cases.json"
PRODUCT_FREEZE_COMMIT = "d6ab7e114574c8f9e5c2aa2dd9e9b7efeb7cdb8e"
PRODUCT_FREEZE_SHA256 = "1dab21f26a2f49f8c398840816f1780dd51172cc66baff0c270c95fd2e805ce2"


COMMON_CONTRACT = {
    "server": (
        "Expose the exact GET status route and typed POST JSON route declared by "
        "the task. The POST route returns the frozen dynamic status/header/body envelope. "
        "Request header names are compared case-insensitively."
    ),
    "request_precedence": (
        "Typed JSON decoding precedes authorization and domain decisions. Malformed JSON, "
        "missing or unknown fields, and wrong JSON types return 400 invalid_json before a "
        "typed application envelope."
    ),
    "transport_errors": (
        "Return 415 json_content_type_required without application/json and 413 "
        "body_too_large above 16384 bytes."
    ),
    "dynamic_response": (
        "Return the exact task status, JSON body, and custom headers. Content-Type, "
        "Content-Length, Connection, Transfer-Encoding, and X-Content-Type-Options are "
        "server-owned."
    ),
    "browser": (
        "Expose the declared deterministic scalar browser function as an ES module export "
        "and return the exact frozen values in real Chromium."
    ),
    "cross_target": (
        "For a domain-valid request, shared_result_field equals the browser export for the "
        "same numeric and boolean inputs."
    ),
    "network": "Bind only to 127.0.0.1 on the harness-selected port.",
    "body_limit_bytes": 16384,
    "response_envelope": {
        "status_field": "status", "headers_field": "headers", "body_field": "body",
    },
}


TASKS: list[dict[str, Any]] = [
    {
        "id": "orbital_clearance_build",
        "kind": "implementation",
        "title": "Build an authenticated orbital cargo-clearance workflow",
        "statement": (
            "Implement Orbital Cargo Clearance. POST requires x-orbit-credential: "
            "orbit-046; otherwise return 403 with x-access-denial orbit_credential and "
            "clearance_phase authorization_required. Negative numbers return 422 with "
            "x-validation nonnegative. Positive payload_tally with zero docking_arms "
            "returns 422 with x-validation docking_arms. payload_tally is pressurized_pods "
            "+ vacuum_pods. transfer_effort is pressurized_pods*8 + vacuum_pods*14, plus "
            "docking_arms*5 during solar_flare. berth_allowance is docking_arms*47. "
            "approved_effort is min(effort, allowance); spillover_effort is max(effort - "
            "allowance, 0); orbit_passes is ceiling(payload_tally/4). clearance_rating is "
            "approved_effort + spillover_effort*7 + orbit_passes*6. clearance_phase is "
            "cleared with no spillover, flare_hold during a flare, and routine_hold "
            "otherwise. Success returns 207 with location /api/v10/orbital-clearances/"
            "{clearance_slug} and x-clearance-phase. The browser export returns the rating."
        ),
        "service": "Orbital Cargo Clearance",
        "status_route": "/status/orbital-clearance-ready",
        "post_route": "/api/v10/orbital-clearances",
        "browser_export": "orbital_clearance_rating",
        "browser_fields": [
            "pressurized_pods", "vacuum_pods", "docking_arms", "solar_flare",
        ],
        "shared_result_field": "clearance_rating",
        "request_fields": {
            "clearance_slug": "text", "pressurized_pods": "number",
            "vacuum_pods": "number", "docking_arms": "number",
            "solar_flare": "yesno",
        },
        "response_fields": {
            "clearance_slug": "text", "payload_tally": "number",
            "transfer_effort": "number", "berth_allowance": "number",
            "approved_effort": "number", "spillover_effort": "number",
            "orbit_passes": "number", "clearance_rating": "number",
            "clearance_phase": "text",
        },
        "authorization": {
            "header": "x-orbit-credential", "value": "orbit-046",
            "failure_status": 403,
            "failure_headers": {"x-access-denial": "orbit_credential"},
        },
        "success_status": 207,
        "independence": (
            "New orbital vocabulary, v10 routes, 207 response, credential header, formulas, "
            "fixtures, and export selected after the 046 product freeze."
        ),
    },
    {
        "id": "estuary_assay_build",
        "kind": "implementation",
        "title": "Build an authenticated asynchronous estuary-assay workflow",
        "statement": (
            "Implement Estuary Assay Dispatch. POST requires Authorization: Sample "
            "sample-046; otherwise return 401 with www-authenticate Sample realm=estuary "
            "and assay_phase authorization_required. Negative numbers return 422 with "
            "x-validation nonnegative. Positive sample_tally with zero assay_benches returns "
            "422 with x-validation assay_benches. repeated_submission returns 409 with "
            "x-conflict repeated_submission. sample_tally is inlet_vials + outlet_vials. "
            "assay_effort is inlet_vials*11 + outlet_vials*7 + reagent_cartridges*9, plus "
            "reagent_cartridges*4 during contamination_alert. bench_allowance is "
            "assay_benches*52. examined_effort is min(effort, allowance); pending_assay is "
            "max(effort - allowance, 0); assay_cycles is ceiling(effort/27). assay_rating is "
            "examined_effort + pending_assay*4 + assay_cycles*8. assay_phase is dispatched "
            "with no pending work, contamination_queue during an alert, and routine_queue "
            "otherwise. Success returns 202 with location /api/v10/estuary-assays/"
            "{assay_ref}, retry-after 5, and x-assay-phase. The browser export returns rating."
        ),
        "service": "Estuary Assay Dispatch",
        "status_route": "/status/estuary-assay-ready",
        "post_route": "/api/v10/estuary-assays",
        "browser_export": "estuary_assay_rating",
        "browser_fields": [
            "inlet_vials", "outlet_vials", "reagent_cartridges", "assay_benches",
            "contamination_alert",
        ],
        "shared_result_field": "assay_rating",
        "request_fields": {
            "assay_ref": "text", "inlet_vials": "number", "outlet_vials": "number",
            "reagent_cartridges": "number", "assay_benches": "number",
            "contamination_alert": "yesno", "repeated_submission": "yesno",
        },
        "response_fields": {
            "assay_ref": "text", "sample_tally": "number", "assay_effort": "number",
            "bench_allowance": "number", "examined_effort": "number",
            "pending_assay": "number", "assay_cycles": "number",
            "assay_rating": "number", "assay_phase": "text",
        },
        "authorization": {
            "header": "authorization", "value": "Sample sample-046",
            "failure_status": 401,
            "failure_headers": {"www-authenticate": "Sample realm=estuary"},
        },
        "success_status": 202,
        "independence": (
            "New estuary vocabulary, v10 routes, Sample authorization, formulas, fixtures, "
            "conflict branch, headers, and export selected after the 046 product freeze."
        ),
    },
    {
        "id": "archive_transfer_repair",
        "kind": "maintenance",
        "title": "Repair a custom response-header name in an archive transfer",
        "statement": (
            "Repair Archive Transfer. Negative numbers return 422 with x-validation "
            "nonnegative. Positive volume_tally with zero catalog_carts returns 422 with "
            "x-validation catalog_carts. volume_tally is folio_boxes + atlas_tubes. "
            "relocation_effort is folio_boxes*6 + atlas_tubes*17, plus catalog_carts*3 "
            "during humidity_warning. cart_allowance is catalog_carts*43. shelved_effort is "
            "min(effort, allowance); quarantined_effort is max(effort - allowance, 0); "
            "transfer_rounds is ceiling(volume_tally/5). transfer_rating is shelved_effort "
            "+ quarantined_effort*6 + transfer_rounds*7. transfer_phase is shelved with no "
            "quarantine, humidity_hold during a warning, and routine_hold otherwise. Success "
            "returns 201 with location /api/v10/archive-transfers/{transfer_tag} and "
            "x-transfer-phase. The browser export returns the rating."
        ),
        "service": "Archive Transfer",
        "status_route": "/status/archive-transfer-ready",
        "post_route": "/api/v10/archive-transfers",
        "browser_export": "archive_transfer_rating",
        "browser_fields": [
            "folio_boxes", "atlas_tubes", "catalog_carts", "humidity_warning",
        ],
        "shared_result_field": "transfer_rating",
        "request_fields": {
            "transfer_tag": "text", "folio_boxes": "number", "atlas_tubes": "number",
            "catalog_carts": "number", "humidity_warning": "yesno",
        },
        "response_fields": {
            "transfer_tag": "text", "volume_tally": "number",
            "relocation_effort": "number", "cart_allowance": "number",
            "shelved_effort": "number", "quarantined_effort": "number",
            "transfer_rounds": "number", "transfer_rating": "number",
            "transfer_phase": "text",
        },
        "success_status": 201,
        "predeclared_defect": (
            "The route-handler seed writes the calculated phase under x-transfer-state "
            "instead of the required x-transfer-phase response header."
        ),
        "root_cause_role": "route_handler",
        "historical_grounding": "synthetic custom response-header name substitution defect",
        "adaptation_boundary": (
            "The custom-header defect, archive-transfer workflow, v10 routes, formulas, "
            "fixtures, and repair were selected after the 046 product freeze."
        ),
    },
    {
        "id": "beacon_enrollment_repair",
        "kind": "maintenance",
        "title": "Repair a success status in a beacon-enrollment workflow",
        "statement": (
            "Repair Beacon Enrollment. POST requires x-rescue-pass: beacon-046; otherwise "
            "return 403 with x-access-denial rescue_pass and enrollment_phase "
            "authorization_required. Negative numbers return 422 with x-validation "
            "nonnegative. Positive transponder_tally with zero calibration_frames returns "
            "422 with x-validation calibration_frames. transponder_tally is "
            "analog_transponders + digital_transponders. tuning_effort is analog*9 + "
            "digital*16, plus calibration_frames*7 during whiteout_warning. frame_allowance "
            "is calibration_frames*50. commissioned_effort is min(effort, allowance); "
            "uncommissioned_effort is max(effort - allowance, 0); tuning_rounds is "
            "ceiling(transponder_tally/6). enrollment_rating is commissioned_effort + "
            "uncommissioned_effort*8 + tuning_rounds*5. enrollment_phase is enrolled with "
            "no remainder, whiteout_hold during a warning, and routine_hold otherwise. "
            "Success returns 202 with location /api/v10/beacon-enrollments/{enrollment_ref}, "
            "retry-after 4, and x-enrollment-phase. The browser export returns the rating."
        ),
        "service": "Beacon Enrollment",
        "status_route": "/status/beacon-enrollment-ready",
        "post_route": "/api/v10/beacon-enrollments",
        "browser_export": "beacon_enrollment_rating",
        "browser_fields": [
            "analog_transponders", "digital_transponders", "calibration_frames",
            "whiteout_warning",
        ],
        "shared_result_field": "enrollment_rating",
        "request_fields": {
            "enrollment_ref": "text", "analog_transponders": "number",
            "digital_transponders": "number", "calibration_frames": "number",
            "whiteout_warning": "yesno",
        },
        "response_fields": {
            "enrollment_ref": "text", "transponder_tally": "number",
            "tuning_effort": "number", "frame_allowance": "number",
            "commissioned_effort": "number", "uncommissioned_effort": "number",
            "tuning_rounds": "number", "enrollment_rating": "number",
            "enrollment_phase": "text",
        },
        "authorization": {
            "header": "x-rescue-pass", "value": "beacon-046",
            "failure_status": 403,
            "failure_headers": {"x-access-denial": "rescue_pass"},
        },
        "success_status": 202,
        "predeclared_defect": (
            "The route-handler seed returns 201 for a valid enrollment instead of the "
            "required asynchronous 202 status."
        ),
        "root_cause_role": "route_handler",
        "historical_grounding": "synthetic successful response-status substitution defect",
        "adaptation_boundary": (
            "The status defect, beacon workflow, v10 routes, formulas, fixtures, and repair "
            "were selected after the 046 product freeze."
        ),
    },
]


def zero_body(task: dict[str, Any], key: str, phase: str) -> dict[str, Any]:
    names = list(task["response_fields"])
    return {
        name: key if index == 0 else phase if index == len(names) - 1 else 0
        for index, name in enumerate(names)
    }


def oracle(task_id: str, value: dict[str, Any]) -> dict[str, Any]:
    if task_id == "orbital_clearance_build":
        total = value["pressurized_pods"] + value["vacuum_pods"]
        effort = value["pressurized_pods"] * 8 + value["vacuum_pods"] * 14
        effort += value["docking_arms"] * 5 if value["solar_flare"] else 0
        allowance = value["docking_arms"] * 47
        approved, spillover = min(effort, allowance), max(effort - allowance, 0)
        passes = (total + 3) // 4
        return {
            "clearance_slug": value["clearance_slug"], "payload_tally": total,
            "transfer_effort": effort, "berth_allowance": allowance,
            "approved_effort": approved, "spillover_effort": spillover,
            "orbit_passes": passes,
            "clearance_rating": approved + spillover * 7 + passes * 6,
            "clearance_phase": (
                "cleared" if spillover == 0 else
                "flare_hold" if value["solar_flare"] else "routine_hold"
            ),
        }
    if task_id == "estuary_assay_build":
        total = value["inlet_vials"] + value["outlet_vials"]
        effort = (
            value["inlet_vials"] * 11 + value["outlet_vials"] * 7
            + value["reagent_cartridges"] * 9
        )
        effort += value["reagent_cartridges"] * 4 if value["contamination_alert"] else 0
        allowance = value["assay_benches"] * 52
        examined, pending = min(effort, allowance), max(effort - allowance, 0)
        cycles = (effort + 26) // 27
        return {
            "assay_ref": value["assay_ref"], "sample_tally": total,
            "assay_effort": effort, "bench_allowance": allowance,
            "examined_effort": examined, "pending_assay": pending,
            "assay_cycles": cycles, "assay_rating": examined + pending * 4 + cycles * 8,
            "assay_phase": (
                "dispatched" if pending == 0 else
                "contamination_queue" if value["contamination_alert"] else "routine_queue"
            ),
        }
    if task_id == "archive_transfer_repair":
        total = value["folio_boxes"] + value["atlas_tubes"]
        effort = value["folio_boxes"] * 6 + value["atlas_tubes"] * 17
        effort += value["catalog_carts"] * 3 if value["humidity_warning"] else 0
        allowance = value["catalog_carts"] * 43
        shelved, quarantine = min(effort, allowance), max(effort - allowance, 0)
        rounds = (total + 4) // 5
        return {
            "transfer_tag": value["transfer_tag"], "volume_tally": total,
            "relocation_effort": effort, "cart_allowance": allowance,
            "shelved_effort": shelved, "quarantined_effort": quarantine,
            "transfer_rounds": rounds,
            "transfer_rating": shelved + quarantine * 6 + rounds * 7,
            "transfer_phase": (
                "shelved" if quarantine == 0 else
                "humidity_hold" if value["humidity_warning"] else "routine_hold"
            ),
        }
    if task_id == "beacon_enrollment_repair":
        total = value["analog_transponders"] + value["digital_transponders"]
        effort = value["analog_transponders"] * 9 + value["digital_transponders"] * 16
        effort += value["calibration_frames"] * 7 if value["whiteout_warning"] else 0
        allowance = value["calibration_frames"] * 50
        commissioned, remainder = min(effort, allowance), max(effort - allowance, 0)
        rounds = (total + 5) // 6
        return {
            "enrollment_ref": value["enrollment_ref"], "transponder_tally": total,
            "tuning_effort": effort, "frame_allowance": allowance,
            "commissioned_effort": commissioned, "uncommissioned_effort": remainder,
            "tuning_rounds": rounds,
            "enrollment_rating": commissioned + remainder * 8 + rounds * 5,
            "enrollment_phase": (
                "enrolled" if remainder == 0 else
                "whiteout_hold" if value["whiteout_warning"] else "routine_hold"
            ),
        }
    raise AssertionError(task_id)


ZERO_RULES = {
    "orbital_clearance_build": ("docking_arms", "payload_tally"),
    "estuary_assay_build": ("assay_benches", "sample_tally"),
    "archive_transfer_repair": ("catalog_carts", "volume_tally"),
    "beacon_enrollment_repair": ("calibration_frames", "transponder_tally"),
}


def outcome(
    task: dict[str, Any], value: dict[str, Any], headers: dict[str, str]
) -> tuple[int, dict[str, str], dict[str, Any]]:
    key = value[next(iter(task["request_fields"]))]
    auth = task.get("authorization")
    lowered = {name.lower(): item for name, item in headers.items()}
    if auth and lowered.get(auth["header"], "") != auth["value"]:
        return auth["failure_status"], auth["failure_headers"], zero_body(
            task, key, "authorization_required"
        )
    if any(
        value[name] < 0 for name, kind in task["request_fields"].items()
        if kind == "number"
    ):
        return 422, {"x-validation": "nonnegative"}, zero_body(task, key, "invalid")
    body = oracle(task["id"], value)
    zero_field, total_field = ZERO_RULES[task["id"]]
    if value[zero_field] == 0 and body[total_field] > 0:
        return 422, {"x-validation": zero_field}, zero_body(task, key, "invalid")
    if task["id"] == "estuary_assay_build" and value["repeated_submission"]:
        return 409, {"x-conflict": "repeated_submission"}, zero_body(
            task, key, "duplicate"
        )
    phase = body[next(reversed(task["response_fields"]))]
    response_headers = {
        "orbital_clearance_build": {
            "location": f"/api/v10/orbital-clearances/{key}",
            "x-clearance-phase": phase,
        },
        "estuary_assay_build": {
            "location": f"/api/v10/estuary-assays/{key}",
            "retry-after": "5", "x-assay-phase": phase,
        },
        "archive_transfer_repair": {
            "location": f"/api/v10/archive-transfers/{key}",
            "x-transfer-phase": phase,
        },
        "beacon_enrollment_repair": {
            "location": f"/api/v10/beacon-enrollments/{key}",
            "retry-after": "4", "x-enrollment-phase": phase,
        },
    }[task["id"]]
    return task["success_status"], response_headers, body


SUCCESS_INPUTS = {
    "orbital_clearance_build": (
        {"clearance_slug": "zenith-4", "pressurized_pods": 3, "vacuum_pods": 2,
         "docking_arms": 2, "solar_flare": True},
        {"X-Orbit-Credential": "orbit-046"},
    ),
    "estuary_assay_build": (
        {"assay_ref": "delta-9", "inlet_vials": 3, "outlet_vials": 2,
         "reagent_cartridges": 2, "assay_benches": 2,
         "contamination_alert": True, "repeated_submission": False},
        {"authorization": "Sample sample-046"},
    ),
    "archive_transfer_repair": (
        {"transfer_tag": "folio-8", "folio_boxes": 4, "atlas_tubes": 2,
         "catalog_carts": 2, "humidity_warning": True},
        {},
    ),
    "beacon_enrollment_repair": (
        {"enrollment_ref": "ridge-6", "analog_transponders": 3,
         "digital_transponders": 2, "calibration_frames": 2,
         "whiteout_warning": True},
        {"x-rescue-pass": "beacon-046"},
    ),
}


HIDDEN_OUTCOMES = {
    "orbital_clearance_build": [
        ("orbital_clearance_unauthorized", SUCCESS_INPUTS["orbital_clearance_build"][0], {}),
        ("orbital_clearance_zero_arms",
         {"clearance_slug": "nadir-2", "pressurized_pods": 1, "vacuum_pods": 2,
          "docking_arms": 0, "solar_flare": False},
         {"x-orbit-credential": "orbit-046"}),
    ],
    "estuary_assay_build": [
        ("estuary_assay_duplicate",
         {**SUCCESS_INPUTS["estuary_assay_build"][0], "repeated_submission": True},
         {"authorization": "Sample sample-046"}),
        ("estuary_assay_unauthorized", SUCCESS_INPUTS["estuary_assay_build"][0], {}),
    ],
    "archive_transfer_repair": [
        ("archive_transfer_negative_folios",
         {"transfer_tag": "stack-3", "folio_boxes": -1, "atlas_tubes": 2,
          "catalog_carts": 1, "humidity_warning": False}, {}),
        ("archive_transfer_zero_carts",
         {"transfer_tag": "vault-5", "folio_boxes": 2, "atlas_tubes": 1,
          "catalog_carts": 0, "humidity_warning": False}, {}),
    ],
    "beacon_enrollment_repair": [
        ("beacon_enrollment_unauthorized",
         SUCCESS_INPUTS["beacon_enrollment_repair"][0], {"x-rescue-pass": "wrong"}),
        ("beacon_enrollment_zero_frames",
         {"enrollment_ref": "scree-2", "analog_transponders": 2,
          "digital_transponders": 1, "calibration_frames": 0,
          "whiteout_warning": False}, {"x-rescue-pass": "beacon-046"}),
    ],
}


BROWSER_INPUTS = {
    "orbital_clearance_build": [
        SUCCESS_INPUTS["orbital_clearance_build"][0],
        {"clearance_slug": "a", "pressurized_pods": 1, "vacuum_pods": 1,
         "docking_arms": 2, "solar_flare": False},
        {"clearance_slug": "b", "pressurized_pods": 7, "vacuum_pods": 4,
         "docking_arms": 1, "solar_flare": True},
    ],
    "estuary_assay_build": [
        SUCCESS_INPUTS["estuary_assay_build"][0],
        {"assay_ref": "a", "inlet_vials": 1, "outlet_vials": 2,
         "reagent_cartridges": 1, "assay_benches": 2,
         "contamination_alert": False, "repeated_submission": False},
        {"assay_ref": "b", "inlet_vials": 6, "outlet_vials": 5,
         "reagent_cartridges": 3, "assay_benches": 1,
         "contamination_alert": True, "repeated_submission": False},
    ],
    "archive_transfer_repair": [
        SUCCESS_INPUTS["archive_transfer_repair"][0],
        {"transfer_tag": "a", "folio_boxes": 1, "atlas_tubes": 1,
         "catalog_carts": 2, "humidity_warning": False},
        {"transfer_tag": "b", "folio_boxes": 7, "atlas_tubes": 4,
         "catalog_carts": 1, "humidity_warning": True},
    ],
    "beacon_enrollment_repair": [
        SUCCESS_INPUTS["beacon_enrollment_repair"][0],
        {"enrollment_ref": "a", "analog_transponders": 1,
         "digital_transponders": 1, "calibration_frames": 2,
         "whiteout_warning": False},
        {"enrollment_ref": "b", "analog_transponders": 6,
         "digital_transponders": 5, "calibration_frames": 1,
         "whiteout_warning": True},
    ],
}


INVALID_CASES = {
    "orbital_clearance_build": {
        "id": "orbital_clearance_wrong_vacuum_type", "visibility": "public",
        "target": "http", "method": "POST",
        "json": {"clearance_slug": "zenith-4", "pressurized_pods": 3,
                 "vacuum_pods": True, "docking_arms": 2, "solar_flare": True},
        "request_headers": {"x-orbit-credential": "orbit-046"},
        "expected_status": 400, "expected_error": "invalid_json",
    },
    "estuary_assay_build": {
        "id": "estuary_assay_wrong_media", "visibility": "public", "target": "http",
        "method": "POST", "raw_body": "{}", "content_type": "text/plain",
        "request_headers": {"authorization": "Sample sample-046"},
        "expected_status": 415, "expected_error": "json_content_type_required",
    },
    "archive_transfer_repair": {
        "id": "archive_transfer_missing_carts", "visibility": "public",
        "target": "http", "method": "POST",
        "json": {"transfer_tag": "folio-8", "folio_boxes": 4,
                 "atlas_tubes": 2, "humidity_warning": True},
        "request_headers": {}, "expected_status": 400, "expected_error": "invalid_json",
    },
    "beacon_enrollment_repair": {
        "id": "beacon_enrollment_wrong_frame_type", "visibility": "public",
        "target": "http", "method": "POST",
        "json": {"enrollment_ref": "ridge-6", "analog_transponders": 3,
                 "digital_transponders": 2, "calibration_frames": False,
                 "whiteout_warning": True},
        "request_headers": {"x-rescue-pass": "beacon-046"},
        "expected_status": 400, "expected_error": "invalid_json",
    },
}


UNKNOWN_FIELDS = {
    "orbital_clearance_build": ("cargo_latch", 3),
    "estuary_assay_build": ("salinity_band", "high"),
    "archive_transfer_repair": ("shelf_aisle", 7),
    "beacon_enrollment_repair": ("rescue_sector", "north"),
}


def task_cases(task: dict[str, Any]) -> list[dict[str, Any]]:
    task_id = task["id"]
    stem = task_id.removesuffix("_build").removesuffix("_repair")
    value, headers = SUCCESS_INPUTS[task_id]
    status, response_headers, body = outcome(task, value, headers)
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
            "request_headers": headers, "expected_status": status,
            "expected_json": body, "expected_headers": response_headers,
        },
        INVALID_CASES[task_id],
        {
            "id": stem + "_browser_primary", "visibility": "public",
            "target": "browser", "export": task["browser_export"],
            "args": [value[name] for name in task["browser_fields"]],
            "expected": oracle(task_id, value)[task["shared_result_field"]],
        },
    ]
    for case_id, hidden_value, hidden_headers in HIDDEN_OUTCOMES[task_id]:
        hidden_status, custom_headers, hidden_body = outcome(
            task, hidden_value, hidden_headers
        )
        rows.append({
            "id": case_id, "visibility": "hidden", "target": "http",
            "method": "POST", "path": task["post_route"], "json": hidden_value,
            "request_headers": hidden_headers, "expected_status": hidden_status,
            "expected_json": hidden_body, "expected_headers": custom_headers,
        })
    unknown = dict(value)
    field, extra = UNKNOWN_FIELDS[task_id]
    unknown[field] = extra
    rows.append({
        "id": stem + "_unknown_field", "visibility": "hidden", "target": "http",
        "method": "POST", "path": task["post_route"], "json": unknown,
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


def assert_disjoint(tasks: list[dict[str, Any]]) -> None:
    prior = [
        task
        for experiment in range(36, 46)
        for task in json.loads(
            (BENCHMARKS / f"fullstack_agent_{experiment:03d}_tasks.json").read_text()
        )["tasks"]
    ]
    for name in ("id", "status_route", "post_route", "browser_export"):
        assert {task[name] for task in tasks}.isdisjoint(task[name] for task in prior)
    for name in ("request_fields", "response_fields"):
        current = {field for task in tasks for field in task[name]}
        previous = {field for task in prior for field in task[name]}
        assert current.isdisjoint(previous)
        assert len(current) == sum(len(task[name]) for task in tasks)


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    assert hashlib.sha256(
        (BENCHMARKS / "fullstack_agent_046_product.json").read_bytes()
    ).hexdigest() == PRODUCT_FREEZE_SHA256
    assert_disjoint(TASKS)
    cases = {task["id"]: task_cases(task) for task in TASKS}
    frozen_tasks = []
    for task in TASKS:
        frozen = dict(task)
        rows = cases[task["id"]]
        frozen["public_case_ids"] = [
            row["id"] for row in rows if row["visibility"] == "public"
        ]
        frozen["hidden_case_ids"] = [
            row["id"] for row in rows if row["visibility"] == "hidden"
        ]
        frozen_tasks.append(frozen)
    return (
        {
            "schema_version": 1,
            "experiment_id": "046",
            "description": (
                "Two response-control implementations and two route-handler repairs, "
                "frozen after the 046 product/evidence boundary and before scaffolds, "
                "reference implementations, protocol thresholds, or model output."
            ),
            "frozen_on": "2026-08-13",
            "product_freeze_commit": PRODUCT_FREEZE_COMMIT,
            "product_freeze_sha256": PRODUCT_FREEZE_SHA256,
            "common_contract": COMMON_CONTRACT,
            "tasks": frozen_tasks,
        },
        {
            "schema_version": 1,
            "experiment_id": "046",
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
