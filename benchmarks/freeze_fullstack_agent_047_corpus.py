#!/usr/bin/env python3
"""Build the deterministic semantics-only path-routing corpus for study 047."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
DEFAULT_TASKS = BENCHMARKS / "fullstack_agent_047_tasks.json"
DEFAULT_CASES = BENCHMARKS / "fullstack_agent_047_cases.json"
PRODUCT_FREEZE_COMMIT = "f1959a5247db7444c161340110ec1782faa3d2b7"
PRODUCT_FREEZE_SHA256 = "33e1c581162e7ab617ad972a65bdf41eaf5ac61b06860d1d6a159b8c48cf4b5f"


COMMON_CONTRACT = {
    "server": (
        "Expose the exact status and named-item routes declared by the task plus the "
        "whole-segment parameterized GET route. Exact routes win over the template "
        "regardless of declaration order. Parameterized handlers receive decoded "
        "path_parameters while request.path remains raw."
    ),
    "path_safety": (
        "Percent-decode a captured segment exactly once as UTF-8. Malformed escapes, "
        "invalid UTF-8, decoded slash or backslash, NUL, controls, and DEL return 400 "
        "invalid_path_parameter before handler logic."
    ),
    "application": (
        "Authorized captures must contain a positive ASCII decimal integer. Invalid "
        "values return the declared 422 envelope. Header names are case-insensitive."
    ),
    "dynamic_response": (
        "Return the exact status, JSON body, and custom application headers. Framing, "
        "hop-by-hop, and security headers remain server-owned."
    ),
    "browser": (
        "Expose the declared deterministic scalar ES-module export and return the exact "
        "frozen values in real Chromium."
    ),
    "cross_target": (
        "For a valid parameter request, the response score equals the browser export for "
        "the decoded integer and whether the declared mode header is active."
    ),
    "network": "Bind only to 127.0.0.1 on the harness-selected port.",
    "response_envelope": {
        "status_field": "status",
        "headers_field": "headers",
        "body_field": "body",
    },
}


TASKS: list[dict[str, Any]] = [
    {
        "id": "tundra_probe_lookup_build",
        "kind": "implementation",
        "title": "Build an authenticated tundra-probe lookup",
        "statement": (
            "Implement Tundra Probe Lookup. GET /status/tundra-probe-ready returns the "
            "ready body. The exact /api/v11/tundra-probes/current route wins over the "
            "{probe_serial} template and returns probe_serial current, probe_sequence 47, "
            "calibration_score 611, probe_state current, and x-probe-state current without "
            "authorization. The template requires x-tundra-pass: tundra-047; otherwise "
            "return 403 with x-access-denial tundra_pass and a zeroed "
            "authorization_required body. Decode probe_serial once; it must be a positive "
            "ASCII decimal integer or return 422 with x-validation probe_serial and a "
            "zeroed invalid body. calibration_score is probe_sequence*13 plus 9 when "
            "x-calibration-mode is precision. Success returns 200 with x-probe-state "
            "catalogued and probe_state catalogued. The browser export computes the score."
        ),
        "service": "Tundra Probe Lookup",
        "status_route": "/status/tundra-probe-ready",
        "parameter_route": "/api/v11/tundra-probes/{probe_serial}",
        "exact_route": "/api/v11/tundra-probes/current",
        "exact_segment": "current",
        "browser_export": "tundra_calibration_score",
        "path_parameter": "probe_serial",
        "sequence_field": "probe_sequence",
        "score_field": "calibration_score",
        "state_field": "probe_state",
        "success_state": "catalogued",
        "state_header": "x-probe-state",
        "factor": 13,
        "boost": 9,
        "mode_header": "x-calibration-mode",
        "mode_value": "precision",
        "exact_sequence": 47,
        "authorization": {
            "header": "x-tundra-pass",
            "value": "tundra-047",
            "failure_status": 403,
            "failure_headers": {"x-access-denial": "tundra_pass"},
        },
        "independence": (
            "New tundra vocabulary, v11 routes, capture, fields, headers, formula, "
            "fixtures, and export selected after the study-047 product freeze."
        ),
    },
    {
        "id": "magma_core_lookup_build",
        "kind": "implementation",
        "title": "Build an authenticated magma-core lookup",
        "statement": (
            "Implement Magma Core Lookup. GET /status/magma-core-ready returns the ready "
            "body. Exact /api/v11/magma-cores/prime wins over {core_marker} and returns "
            "core_marker prime, core_sequence 31, thermal_index 527, core_disposition "
            "prime, and x-core-disposition prime without authorization. The template "
            "requires Authorization: Core core-047; otherwise return 401 with "
            "www-authenticate Core realm=magma and a zeroed authorization_required body. "
            "Decode core_marker once; it must be a positive ASCII decimal integer or "
            "return 422 with x-validation core_marker and a zeroed invalid body. "
            "thermal_index is core_sequence*17 plus 6 when x-analysis-mode is thermal. "
            "Success returns 200 with x-core-disposition indexed and that body state. The "
            "browser export computes the index."
        ),
        "service": "Magma Core Lookup",
        "status_route": "/status/magma-core-ready",
        "parameter_route": "/api/v11/magma-cores/{core_marker}",
        "exact_route": "/api/v11/magma-cores/prime",
        "exact_segment": "prime",
        "browser_export": "magma_thermal_index",
        "path_parameter": "core_marker",
        "sequence_field": "core_sequence",
        "score_field": "thermal_index",
        "state_field": "core_disposition",
        "success_state": "indexed",
        "state_header": "x-core-disposition",
        "factor": 17,
        "boost": 6,
        "mode_header": "x-analysis-mode",
        "mode_value": "thermal",
        "exact_sequence": 31,
        "authorization": {
            "header": "authorization",
            "value": "Core core-047",
            "failure_status": 401,
            "failure_headers": {"www-authenticate": "Core realm=magma"},
        },
        "independence": (
            "New magma vocabulary, v11 routes, capture, fields, headers, formula, "
            "fixtures, and export selected after the study-047 product freeze."
        ),
    },
    {
        "id": "aviary_band_lookup_repair",
        "kind": "maintenance",
        "title": "Repair an aviary-band capture lookup",
        "statement": (
            "Repair Aviary Band Lookup. The ready route is exact. Exact "
            "/api/v11/aviary-bands/resident wins over {band_marker} and returns "
            "band_marker resident, band_sequence 23, migration_rank 253, band_status "
            "resident, and x-band-status resident. Decode band_marker once; it must be a "
            "positive ASCII decimal integer or return 422 with x-validation band_marker "
            "and a zeroed invalid body. migration_rank is band_sequence*11 plus 8 when "
            "x-flight-mode is migration. Success returns 200 with x-band-status traced "
            "and band_status traced. The browser export computes the rank."
        ),
        "service": "Aviary Band Lookup",
        "status_route": "/status/aviary-band-ready",
        "parameter_route": "/api/v11/aviary-bands/{band_marker}",
        "exact_route": "/api/v11/aviary-bands/resident",
        "exact_segment": "resident",
        "browser_export": "aviary_migration_rank",
        "path_parameter": "band_marker",
        "sequence_field": "band_sequence",
        "score_field": "migration_rank",
        "state_field": "band_status",
        "success_state": "traced",
        "state_header": "x-band-status",
        "factor": 11,
        "boost": 8,
        "mode_header": "x-flight-mode",
        "mode_value": "migration",
        "exact_sequence": 23,
        "predeclared_defect": (
            "The route-handler seed reads band_code from path parameters instead of the "
            "declared band_marker, so the public parameterized lookup fails."
        ),
        "root_cause_role": "route_handler",
        "historical_grounding": "synthetic path-parameter key substitution defect",
        "adaptation_boundary": (
            "The capture-key defect and all aviary semantics were selected only after "
            "the study-047 product freeze."
        ),
    },
    {
        "id": "canal_gate_lookup_repair",
        "kind": "maintenance",
        "title": "Repair decoded capture use in a canal-gate lookup",
        "statement": (
            "Repair Canal Gate Lookup. The ready route is exact. Exact "
            "/api/v11/canal-gates/control wins over {gate_token} and returns gate_token "
            "control, gate_sequence 17, flow_measure 323, gate_condition control, and "
            "x-gate-condition control without authorization. The template requires "
            "x-lock-key: canal-047; otherwise return 403 with x-access-denial lock_key and "
            "a zeroed authorization_required body. Decode gate_token once; it must be a "
            "positive ASCII decimal integer or return 422 with x-validation gate_token and "
            "a zeroed invalid body. flow_measure is gate_sequence*19 plus 5 when "
            "x-flow-mode is flood. Success returns 200 with x-gate-condition mapped and "
            "that body state. The browser export computes the measure."
        ),
        "service": "Canal Gate Lookup",
        "status_route": "/status/canal-gate-ready",
        "parameter_route": "/api/v11/canal-gates/{gate_token}",
        "exact_route": "/api/v11/canal-gates/control",
        "exact_segment": "control",
        "browser_export": "canal_flow_measure",
        "path_parameter": "gate_token",
        "sequence_field": "gate_sequence",
        "score_field": "flow_measure",
        "state_field": "gate_condition",
        "success_state": "mapped",
        "state_header": "x-gate-condition",
        "factor": 19,
        "boost": 5,
        "mode_header": "x-flow-mode",
        "mode_value": "flood",
        "exact_sequence": 17,
        "authorization": {
            "header": "x-lock-key",
            "value": "canal-047",
            "failure_status": 403,
            "failure_headers": {"x-access-denial": "lock_key"},
        },
        "predeclared_defect": (
            "The route-handler seed converts the raw request.path instead of the decoded "
            "gate_token path parameter, so the public parameterized lookup fails."
        ),
        "root_cause_role": "route_handler",
        "historical_grounding": "synthetic raw-path-for-capture substitution defect",
        "adaptation_boundary": (
            "The decoded-capture defect and all canal semantics were selected only after "
            "the study-047 product freeze."
        ),
    },
]


PRIMARY = {
    "tundra_probe_lookup_build": ("18", True),
    "magma_core_lookup_build": ("14", True),
    "aviary_band_lookup_repair": ("27", True),
    "canal_gate_lookup_repair": ("12", True),
}
ENCODED = {
    "tundra_probe_lookup_build": ("%34%32", "42", False),
    "magma_core_lookup_build": ("%32%39", "29", True),
    "aviary_band_lookup_repair": ("%33%36", "36", False),
    "canal_gate_lookup_repair": ("%32%34", "24", True),
}
INVALID_SEGMENTS = {
    "tundra_probe_lookup_build": "%ZZ",
    "magma_core_lookup_build": "%FF",
    "aviary_band_lookup_repair": "%2F",
    "canal_gate_lookup_repair": "%5C",
}
BROWSER_INPUTS = {
    "tundra_probe_lookup_build": [(18, True), (7, False), (41, True)],
    "magma_core_lookup_build": [(14, True), (9, False), (33, True)],
    "aviary_band_lookup_repair": [(27, True), (8, False), (44, True)],
    "canal_gate_lookup_repair": [(12, True), (6, False), (37, True)],
}


def lower_headers(headers: dict[str, str]) -> dict[str, str]:
    return {name.lower(): value for name, value in headers.items()}


def score(task: dict[str, Any], sequence: int, active: bool) -> int:
    return sequence * task["factor"] + (task["boost"] if active else 0)


def body(
    task: dict[str, Any], capture: str, sequence: int, result: int, state: str
) -> dict[str, Any]:
    return {
        task["path_parameter"]: capture,
        task["sequence_field"]: sequence,
        task["score_field"]: result,
        task["state_field"]: state,
    }


def request_headers(task: dict[str, Any], active: bool) -> dict[str, str]:
    headers = {}
    if auth := task.get("authorization"):
        headers[auth["header"]] = auth["value"]
    if active:
        headers[task["mode_header"]] = task["mode_value"]
    return headers


def outcome(
    task: dict[str, Any], capture: str, headers: dict[str, str]
) -> tuple[int, dict[str, str], dict[str, Any]]:
    lowered = lower_headers(headers)
    auth = task.get("authorization")
    if auth and lowered.get(auth["header"], "") != auth["value"]:
        return (
            auth["failure_status"],
            auth["failure_headers"],
            body(task, capture, 0, 0, "authorization_required"),
        )
    if not capture.isascii() or not capture.isdecimal() or int(capture) <= 0:
        return (
            422,
            {"x-validation": task["path_parameter"]},
            body(task, capture, 0, 0, "invalid"),
        )
    sequence = int(capture)
    active = lowered.get(task["mode_header"], "") == task["mode_value"]
    return (
        200,
        {task["state_header"]: task["success_state"]},
        body(
            task,
            capture,
            sequence,
            score(task, sequence, active),
            task["success_state"],
        ),
    )


def exact_outcome(task: dict[str, Any]) -> tuple[int, dict[str, str], dict[str, Any]]:
    sequence = task["exact_sequence"]
    segment = task["exact_segment"]
    return (
        200,
        {task["state_header"]: segment},
        body(task, segment, sequence, score(task, sequence, False), segment),
    )


def http_case(
    *, case_id: str, visibility: str, path: str, status: int,
    headers: dict[str, str] | None = None, expected_headers: dict[str, str] | None = None,
    expected_json: dict[str, Any] | None = None,
    expected_path_parameters: dict[str, str] | None = None,
    expected_error: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": case_id,
        "visibility": visibility,
        "target": "http",
        "method": "GET",
        "path": path,
        "request_headers": headers or {},
        "expected_status": status,
        "expected_headers": expected_headers or {},
    }
    if expected_json is not None:
        row["expected_json"] = expected_json
    if expected_path_parameters is not None:
        row["expected_path_parameters"] = expected_path_parameters
    if expected_error is not None:
        row["expected_error"] = expected_error
    return row


def task_cases(task: dict[str, Any]) -> list[dict[str, Any]]:
    task_id = task["id"]
    stem = task_id.removesuffix("_build").removesuffix("_repair")
    capture, active = PRIMARY[task_id]
    headers = request_headers(task, active)
    status, response_headers, response_body = outcome(task, capture, headers)
    exact_status, exact_headers, exact_body = exact_outcome(task)
    zero_headers = request_headers(task, False)
    zero_status, zero_response_headers, zero_body = outcome(task, "0", zero_headers)
    encoded_path, decoded_capture, encoded_active = ENCODED[task_id]
    encoded_headers = request_headers(task, encoded_active)
    encoded_status, encoded_response_headers, encoded_body = outcome(
        task, decoded_capture, encoded_headers
    )
    browser = BROWSER_INPUTS[task_id]
    rows = [
        http_case(
            case_id=f"{stem}_status",
            visibility="public",
            path=task["status_route"],
            status=200,
            expected_json={"service": task["service"], "ready": True},
            expected_path_parameters={},
        ),
        http_case(
            case_id=f"{stem}_exact",
            visibility="public",
            path=task["exact_route"],
            status=exact_status,
            expected_headers=exact_headers,
            expected_json=exact_body,
            expected_path_parameters={},
        ),
        http_case(
            case_id=f"{stem}_primary",
            visibility="public",
            path=task["parameter_route"].replace(
                "{" + task["path_parameter"] + "}", capture
            ),
            status=status,
            headers=headers,
            expected_headers=response_headers,
            expected_json=response_body,
            expected_path_parameters={task["path_parameter"]: capture},
        ),
        http_case(
            case_id=f"{stem}_zero",
            visibility="public",
            path=task["parameter_route"].replace(
                "{" + task["path_parameter"] + "}", "0"
            ),
            status=zero_status,
            headers=zero_headers,
            expected_headers=zero_response_headers,
            expected_json=zero_body,
            expected_path_parameters={task["path_parameter"]: "0"},
        ),
        {
            "id": f"{stem}_browser_primary",
            "visibility": "public",
            "target": "browser",
            "export": task["browser_export"],
            "args": list(browser[0]),
            "expected": score(task, *browser[0]),
        },
    ]
    if auth := task.get("authorization"):
        unauthorized_headers = {task["mode_header"]: task["mode_value"]}
        unauthorized_status, unauthorized_response_headers, unauthorized_body = outcome(
            task, capture, unauthorized_headers
        )
        rows.append(http_case(
            case_id=f"{stem}_unauthorized",
            visibility="hidden",
            path=task["parameter_route"].replace(
                "{" + task["path_parameter"] + "}", capture
            ),
            status=unauthorized_status,
            headers=unauthorized_headers,
            expected_headers=unauthorized_response_headers,
            expected_json=unauthorized_body,
            expected_path_parameters={task["path_parameter"]: capture},
        ))
    else:
        negative_status, negative_headers, negative_body = outcome(task, "-3", {})
        rows.append(http_case(
            case_id=f"{stem}_negative",
            visibility="hidden",
            path=task["parameter_route"].replace(
                "{" + task["path_parameter"] + "}", "-3"
            ),
            status=negative_status,
            expected_headers=negative_headers,
            expected_json=negative_body,
            expected_path_parameters={task["path_parameter"]: "-3"},
        ))
    rows.extend([
        http_case(
            case_id=f"{stem}_encoded",
            visibility="hidden",
            path=task["parameter_route"].replace(
                "{" + task["path_parameter"] + "}", encoded_path
            ),
            status=encoded_status,
            headers=encoded_headers,
            expected_headers=encoded_response_headers,
            expected_json=encoded_body,
            expected_path_parameters={task["path_parameter"]: decoded_capture},
        ),
        http_case(
            case_id=f"{stem}_invalid_escape",
            visibility="hidden",
            path=task["parameter_route"].replace(
                "{" + task["path_parameter"] + "}", INVALID_SEGMENTS[task_id]
            ),
            status=400,
            headers=request_headers(task, False),
            expected_error="invalid_path_parameter",
        ),
        {
            "id": f"{stem}_browser_hidden_1",
            "visibility": "hidden",
            "target": "browser",
            "export": task["browser_export"],
            "args": list(browser[1]),
            "expected": score(task, *browser[1]),
        },
        {
            "id": f"{stem}_browser_hidden_2",
            "visibility": "hidden",
            "target": "browser",
            "export": task["browser_export"],
            "args": list(browser[2]),
            "expected": score(task, *browser[2]),
        },
    ])
    assert len(rows) == 10
    return rows


def prior_documents() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tasks: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    for experiment in range(36, 47):
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


def assert_disjoint(tasks: list[dict[str, Any]], cases: dict[str, list[dict[str, Any]]]) -> None:
    previous_tasks, previous_cases = prior_documents()
    for name in ("id", "status_route", "browser_export"):
        assert {task[name] for task in tasks}.isdisjoint(
            task[name] for task in previous_tasks
        )
    previous_routes = {
        route
        for task in previous_tasks
        for route in (
            task.get("status_route"), task.get("post_route"),
            task.get("parameter_route"), task.get("exact_route"),
        )
        if route
    }
    assert {
        route
        for task in tasks
        for route in (task["status_route"], task["parameter_route"], task["exact_route"])
    }.isdisjoint(previous_routes)
    current_fields = {
        task[key]
        for task in tasks
        for key in ("path_parameter", "sequence_field", "score_field", "state_field")
    }
    previous_fields = {
        field
        for task in previous_tasks
        for group in (task.get("request_fields", {}), task.get("response_fields", {}))
        for field in group
    }
    assert current_fields.isdisjoint(previous_fields)
    assert len(current_fields) == 16
    current_ids = [row["id"] for rows in cases.values() for row in rows]
    assert len(current_ids) == len(set(current_ids)) == 40
    assert set(current_ids).isdisjoint(row["id"] for row in previous_cases)


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    assert hashlib.sha256(
        (BENCHMARKS / "fullstack_agent_047_product.json").read_bytes()
    ).hexdigest() == PRODUCT_FREEZE_SHA256
    cases = {task["id"]: task_cases(task) for task in TASKS}
    assert_disjoint(TASKS, cases)
    frozen_tasks = []
    for task in TASKS:
        frozen = dict(task)
        rows = cases[task["id"]]
        frozen["response_fields"] = {
            task["path_parameter"]: "text",
            task["sequence_field"]: "number",
            task["score_field"]: "number",
            task["state_field"]: "text",
        }
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
            "experiment_id": "047",
            "description": (
                "Two path-routing implementations and two route-handler repairs, frozen "
                "after the study-047 product/evidence boundary and before scaffolds, "
                "reference applications, protocol thresholds, or model output."
            ),
            "frozen_on": "2026-08-13",
            "product_freeze_commit": PRODUCT_FREEZE_COMMIT,
            "product_freeze_sha256": PRODUCT_FREEZE_SHA256,
            "common_contract": COMMON_CONTRACT,
            "tasks": frozen_tasks,
        },
        {
            "schema_version": 1,
            "experiment_id": "047",
            "visibility_policy": (
                "Prompts expose only public case IDs and expected outcomes. Hidden cases "
                "remain parent-owned and never enter agent workspaces."
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
        "tasks": len(tasks["tasks"]),
        "cases": sum(len(rows) for rows in cases["tasks"].values()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
