#!/usr/bin/env python3
"""Independently audit the immutable raw result from full-stack study 040."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "results/fullstack_agent_040_raw.json"
PROTOCOL = BENCHMARKS / "fullstack_agent_040_protocol.json"
VALIDATION = BENCHMARKS / "fullstack_agent_040_validation.json"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_040_audit.json"
RAW_SHA256 = "37b631af1ca17033ea30fe433699c52e90f7175b42454ac819e7bd2d3ff50914"
MEASUREMENT_COMMIT = "2820f4eb3bc44578bdc60237559782c07a2511df"
LANGUAGES = ("parley", "python", "typescript", "rust")
CONFIGURATIONS = ("sol-medium", "terra-medium")
KINDS = ("implementation", "maintenance")
INTERRUPTED_CELLS = {
    "museum_rotation_build__rust__sol-medium__r2",
    "harbor_signal_build__python__sol-medium__r2",
}
ENOSPC_CELLS = {
    "bookmobile_loading_repair__parley__sol-medium__r2",
    "rooftop_battery_repair__parley__terra-medium__r2",
    "bookmobile_loading_repair__rust__sol-medium__r3",
}
MODEL_REPAIR_CELLS = {"rooftop_battery_repair__python__terra-medium__r3"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    maintenance = [
        row
        for row in rows
        if row["task_kind"] == "maintenance" and row.get("hidden_success")
    ]
    return {
        "sessions": len(rows),
        "hidden_successes": sum(bool(row.get("hidden_success")) for row in rows),
        "hidden_success_rate": sum(bool(row.get("hidden_success")) for row in rows)
        / len(rows),
        "first_check_successes": sum(
            bool(row.get("first_public_check_success")) for row in rows
        ),
        "first_check_success_rate": sum(
            bool(row.get("first_public_check_success")) for row in rows
        )
        / len(rows),
        "hidden_correct_maintenance_rows": len(maintenance),
        "exact_root_successes": sum(bool(row.get("exact_root")) for row in maintenance),
        "exact_root_rate": (
            sum(bool(row.get("exact_root")) for row in maintenance) / len(maintenance)
            if maintenance
            else 0.0
        ),
        "median_total_tokens": statistics.median(
            float(row.get("total_tokens", 0)) for row in rows
        ),
        "median_elapsed_seconds": statistics.median(
            float(row.get("elapsed_seconds", 0)) for row in rows
        ),
        "repair_turns": sum(int(row.get("repair_turns", 0)) for row in rows),
    }


def relative_percent(value: float, baseline: float) -> float:
    return round((value / baseline - 1.0) * 100.0, 4)


def audit(*, verify_external: bool) -> dict[str, Any]:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    assert sha256(RAW) == RAW_SHA256
    assert raw["experiment_id"] == protocol["experiment_id"] == "040"
    assert raw["protocol"] == protocol
    assert raw["protocol_sha256"] == sha256(PROTOCOL)
    assert validation["protocol_sha256"] == sha256(PROTOCOL)
    assert raw["repository"] == raw["repository_after"]
    assert raw["repository"]["commit"] == MEASUREMENT_COMMIT
    assert raw["repository"]["status_porcelain"] == ""
    assert raw["provenance_after_execution_error"] == ""
    assert sha256(Path(raw["provenance_file"])) == raw["provenance_sha256"]
    assert sha256(Path(raw["run_manifest_file"])) == raw["run_manifest_sha256"]
    for key, path in (
        ("runner_sha256", BENCHMARKS / "run_fullstack_agent_040.py"),
        ("preparer_sha256", BENCHMARKS / "prepare_fullstack_agent_040.py"),
        ("scaffolds_sha256", BENCHMARKS / "fullstack_agent_040_scaffolds.py"),
        ("transport_sha256", BENCHMARKS / "agent_check_transport.py"),
        ("guard_sha256", BENCHMARKS / "fullstack_agent_040_guard.py"),
    ):
        assert raw[key] == sha256(path)
    for item in protocol["execution_freeze"]["files"]:
        assert sha256(REPO / item["file"]) == item["sha256"]

    rows = raw["results"]
    plan = raw["plan"]
    by_cell = {row["cell_id"]: row for row in rows}
    assert len(rows) == len(plan) == 96
    assert [row["cell_id"] for row in rows] == [row["cell_id"] for row in plan]
    assert [row["plan_index"] for row in rows] == list(range(1, 97))
    assert len(by_cell) == 96
    thread_ids = [row.get("thread_id") for row in rows if row.get("thread_id")]
    assert len(thread_ids) == len(set(thread_ids)) == 94
    assert Counter(row["language"] for row in rows) == Counter(
        {language: 24 for language in LANGUAGES}
    )
    assert Counter(row["configuration_id"] for row in rows) == Counter(
        {configuration: 48 for configuration in CONFIGURATIONS}
    )
    assert all(row.get("journal_attempt") == 1 for row in rows)
    assert all(not row.get("unexpected_files") for row in rows)

    interrupted = {
        row["cell_id"]
        for row in rows
        if row.get("interrupted_before_completion") is True
    }
    assert interrupted == INTERRUPTED_CELLS
    for cell_id in INTERRUPTED_CELLS:
        row = by_cell[cell_id]
        assert row["runner_error"] == (
            "process interrupted after cell start; selective rerun forbidden"
        )
        assert row.get("thread_id") is None
        assert not row["command_protocol"]["compliant"]
        assert not row["hidden_success"]

    external_journals = external_attempts = 0
    if verify_external:
        assert len(raw["journal"]) == 96
        for record in raw["journal"]:
            started = Path(record["started_file"])
            finished = Path(record["finished_file"])
            assert sha256(started) == record["started_sha256"]
            assert sha256(finished) == record["finished_sha256"]
            start_payload = json.loads(started.read_text(encoding="utf-8"))
            finish_payload = json.loads(finished.read_text(encoding="utf-8"))
            assert start_payload["status"] == "started"
            assert start_payload["cell"]["cell_id"] == record["cell_id"]
            assert finish_payload["status"] == "finished"
            assert finish_payload["result"] == by_cell[record["cell_id"]]
            external_journals += 1
        for row in rows:
            records = row.get("parent_attempt_records") or []
            attempts = row.get("public_attempts") or []
            if row["cell_id"] == "bookmobile_loading_repair__rust__sol-medium__r3":
                assert len(records) == 0 and len(attempts) == 1
                continue
            else:
                assert len(records) == len(attempts)
            for record, attempt in zip(records, attempts, strict=True):
                path = Path(record["file"])
                assert sha256(path) == record["sha256"]
                assert json.loads(path.read_text(encoding="utf-8")) == attempt
                external_attempts += 1
        assert external_attempts == 94

    attempts = [
        attempt for row in rows for attempt in (row.get("public_attempts") or [])
    ]
    assert len(attempts) == 95
    assert sum(bool(attempt["ok"]) for attempt in attempts) == 92
    assert sum(len(attempt.get("cases", [])) for attempt in attempts) == 372
    assert sum(
        case["target"] == "browser"
        for attempt in attempts
        for case in attempt.get("cases", [])
    ) == 93
    assert sum(attempt.get("cross_target") is not None for attempt in attempts) == 93
    assert sum(bool(row.get("final_public_check_success")) for row in rows) == 92
    assert sum(bool(row.get("first_public_check_success")) for row in rows) == 91
    assert sum(int(row.get("repair_turns", 0)) for row in rows) == 1
    for row in rows:
        if row["cell_id"] in INTERRUPTED_CELLS:
            continue
        commands = row["command_protocol"]["commands"]
        if row["cell_id"] == "bookmobile_loading_repair__rust__sol-medium__r3":
            assert len(commands) == 3 and row["public_check_attempts"] == 1
        else:
            assert len(commands) == row["public_check_attempts"] + 1
        assert commands[0].endswith("./sources")
        assert all(command.endswith("./check") for command in commands[1:])

    first_failures = {
        row["cell_id"] for row in rows if not row.get("first_public_check_success")
    }
    assert first_failures == INTERRUPTED_CELLS | {
        "rooftop_battery_repair__parley__terra-medium__r2",
        "bookmobile_loading_repair__rust__sol-medium__r3",
    } | MODEL_REPAIR_CELLS
    repaired = [
        row["cell_id"]
        for row in rows
        if not row.get("first_public_check_success")
        and row.get("final_public_check_success")
    ]
    assert repaired == ["rooftop_battery_repair__python__terra-medium__r3"]
    repair_stderr = by_cell[repaired[0]]["public_attempts"][0]["stderr"]
    assert "Unexpected strict mode reserved word" in repair_stderr

    hidden_failures = {
        row["cell_id"] for row in rows if not row.get("hidden_success")
    }
    assert hidden_failures == INTERRUPTED_CELLS | {
        "bookmobile_loading_repair__parley__sol-medium__r2",
        "rooftop_battery_repair__parley__terra-medium__r2",
    }
    hidden_cases = [
        case
        for row in rows
        for case in ((row.get("hidden_judgment") or {}).get("cases") or [])
    ]
    assert len(hidden_cases) == 460
    assert sum(case["target"] == "browser" for case in hidden_cases) == 184
    assert all(case["pass"] for case in hidden_cases)
    assert sum(
        (row.get("hidden_judgment") or {}).get("cross_target") is not None
        for row in rows
    ) == 92

    for cell_id in ENOSPC_CELLS:
        row = by_cell[cell_id]
        evidence = json.dumps(
            {
                "public": row.get("public_attempts"),
                "hidden": row.get("hidden_judgment"),
                "broker": row.get("broker_error"),
            }
        )
        assert "No space left on device" in evidence
    assert by_cell["bookmobile_loading_repair__rust__sol-medium__r3"][
        "hidden_success"
    ]
    assert not by_cell["bookmobile_loading_repair__rust__sol-medium__r3"][
        "exact_root"
    ]

    build_checks = []
    for row in rows:
        for attempt in row.get("public_attempts") or []:
            build_checks.extend((attempt.get("build") or {}).get(
                "protected_read_only_checks", []
            ))
        build_checks.extend((row.get("hidden_judgment") or {}).get("build", {}).get(
            "protected_read_only_checks", []
        ))
    assert len(build_checks) == 280
    assert all(check["hashes_ok"] and not check["changes"] for check in build_checks)
    assert sum(bool(check["ok"]) for check in build_checks) == 277
    assert sum(bool(check["command_error"]) for check in build_checks) == 3

    by_language = {
        language: aggregate([row for row in rows if row["language"] == language])
        for language in LANGUAGES
    }
    by_configuration = {
        configuration: {
            language: aggregate(
                [
                    row
                    for row in rows
                    if row["configuration_id"] == configuration
                    and row["language"] == language
                ]
            )
            for language in LANGUAGES
        }
        for configuration in CONFIGURATIONS
    }
    by_kind = {
        kind: {
            language: aggregate(
                [
                    row
                    for row in rows
                    if row["task_kind"] == kind and row["language"] == language
                ]
            )
            for language in LANGUAGES
        }
        for kind in KINDS
    }
    assert by_language == raw["summary"]["by_language"]
    assert by_configuration == raw["summary"]["by_configuration"]
    assert by_kind == raw["summary"]["by_kind"]

    baselines = [by_language[name] for name in LANGUAGES if name != "parley"]
    parley = by_language["parley"]
    conditions = {
        "execution_integrity": False,
        "correctness": (
            parley["hidden_success_rate"] == 1.0
            and all(
                parley["hidden_success_rate"] >= row["hidden_success_rate"]
                for row in baselines
            )
            and all(
                by_configuration[configuration]["parley"]["hidden_success_rate"]
                >= max(
                    by_configuration[configuration][language]["hidden_success_rate"]
                    for language in LANGUAGES
                    if language != "parley"
                )
                for configuration in CONFIGURATIONS
            )
            and all(
                by_kind[kind]["parley"]["hidden_success_rate"]
                >= max(
                    by_kind[kind][language]["hidden_success_rate"]
                    for language in LANGUAGES
                    if language != "parley"
                )
                for kind in KINDS
            )
        ),
        "first_check": (
            parley["first_check_success_rate"]
            >= max(row["first_check_success_rate"] for row in baselines)
            and all(
                by_kind[kind]["parley"]["first_check_success_rate"]
                >= max(
                    by_kind[kind][language]["first_check_success_rate"]
                    for language in LANGUAGES
                    if language != "parley"
                )
                for kind in KINDS
            )
        ),
        "tokens": (
            parley["median_total_tokens"]
            <= min(row["median_total_tokens"] for row in baselines)
            and all(
                by_configuration[configuration]["parley"]["median_total_tokens"]
                <= min(
                    by_configuration[configuration][language]["median_total_tokens"]
                    for language in LANGUAGES
                    if language != "parley"
                )
                for configuration in CONFIGURATIONS
            )
        ),
        "elapsed": (
            parley["median_elapsed_seconds"]
            <= min(row["median_elapsed_seconds"] for row in baselines)
            and all(
                by_configuration[configuration]["parley"]["median_elapsed_seconds"]
                <= min(
                    by_configuration[configuration][language]["median_elapsed_seconds"]
                    for language in LANGUAGES
                    if language != "parley"
                )
                for configuration in CONFIGURATIONS
            )
        ),
        "maintainability": (
            by_kind["maintenance"]["parley"]["exact_root_rate"] == 1.0
            and all(
                by_kind["maintenance"]["parley"]["exact_root_rate"]
                >= by_kind["maintenance"][language]["exact_root_rate"]
                for language in LANGUAGES
                if language != "parley"
            )
        ),
    }
    assert conditions == raw["summary"]["primary_gate"]["conditions"]
    assert not raw["summary"]["primary_gate"]["passed"]

    source_medians = {
        language: float(
            statistics.median(
                row["source"]["totals"]["o200k_base_tokens"]
                for row in rows
                if row["language"] == language and row.get("source")
            )
        )
        for language in LANGUAGES
    }
    integrity_failure_cells = {
        row["cell_id"]
        for row in rows
        if not all(
            row.get(field)
            for field in (
                "checker_integrity_ok",
                "read_only_integrity_ok",
                "symlink_integrity_ok",
                "transport_integrity_ok",
                "attempt_record_integrity_ok",
                "public_execution_ok",
                "post_build_integrity_ok",
                "editable_file_integrity_ok",
                "workspace_integrity_ok",
                "fresh_ephemeral_session",
            )
        )
    }
    assert integrity_failure_cells == INTERRUPTED_CELLS | {
        "rooftop_battery_repair__parley__terra-medium__r2",
        "bookmobile_loading_repair__rust__sol-medium__r3",
    }

    return {
        "schema_version": 1,
        "experiment_id": "040",
        "raw_sha256": sha256(RAW),
        "protocol_sha256": sha256(PROTOCOL),
        "validation_sha256": sha256(VALIDATION),
        "measurement_commit": MEASUREMENT_COMMIT,
        "external_evidence_verified": verify_external,
        "matrix": {
            "cells": len(rows),
            "unique_cell_ids": len(by_cell),
            "unique_non_null_thread_ids": len(set(thread_ids)),
            "interrupted_cells": len(INTERRUPTED_CELLS),
            "journal_pairs_verified": external_journals,
            "attempt_files_verified": external_attempts,
        },
        "public": {
            "attempts": len(attempts),
            "successful_attempts": sum(bool(attempt["ok"]) for attempt in attempts),
            "failed_attempts": sum(not attempt["ok"] for attempt in attempts),
            "named_cases_executed": sum(
                len(attempt.get("cases", [])) for attempt in attempts
            ),
            "browser_cases_executed": sum(
                case["target"] == "browser"
                for attempt in attempts
                for case in attempt.get("cases", [])
            ),
            "cross_target_checks_executed": sum(
                attempt.get("cross_target") is not None for attempt in attempts
            ),
            "first_check_successes": sum(
                bool(row.get("first_public_check_success")) for row in rows
            ),
            "final_check_successes": sum(
                bool(row.get("final_public_check_success")) for row in rows
            ),
            "repair_turns": sum(int(row.get("repair_turns", 0)) for row in rows),
        },
        "hidden": {
            "assignment_successes": sum(bool(row.get("hidden_success")) for row in rows),
            "named_cases_executed": len(hidden_cases),
            "named_case_passes": sum(bool(case["pass"]) for case in hidden_cases),
            "browser_cases_executed": sum(
                case["target"] == "browser" for case in hidden_cases
            ),
            "cross_target_checks_executed": sum(
                (row.get("hidden_judgment") or {}).get("cross_target") is not None
                for row in rows
            ),
            "semantic_case_failure_cells": [],
        },
        "exact_build": {
            "commands": len(build_checks),
            "stable_hash_checks": sum(bool(check["hashes_ok"]) for check in build_checks),
            "successful_commands": sum(bool(check["ok"]) for check in build_checks),
            "failed_commands_with_stable_hashes": sum(
                bool(check["command_error"]) and bool(check["hashes_ok"])
                for check in build_checks
            ),
        },
        "environment_incident": {
            "class": "host_disk_exhaustion_enospc",
            "affected_cells": sorted(INTERRUPTED_CELLS | ENOSPC_CELLS),
            "interrupted_cells": sorted(INTERRUPTED_CELLS),
            "explicit_enospc_cells": sorted(ENOSPC_CELLS),
            "selective_reruns": 0,
            "interpretation": (
                "The primary gate is invalidated and remains failed. All 460 hidden "
                "semantic cases that executed passed; four assignments had no hidden "
                "case execution because of ENOSPC or preserved interruption."
            ),
        },
        "model_failure_classes": {
            "javascript_reserved_identifier_then_repaired": sorted(MODEL_REPAIR_CELLS)
        },
        "by_language": by_language,
        "by_configuration": by_configuration,
        "by_kind": by_kind,
        "primary_gate": {"conditions": conditions, "passed": all(conditions.values())},
        "comparisons": {
            "parley_tokens_vs_python_percent": relative_percent(
                by_language["parley"]["median_total_tokens"],
                by_language["python"]["median_total_tokens"],
            ),
            "parley_elapsed_vs_typescript_percent": relative_percent(
                by_language["parley"]["median_elapsed_seconds"],
                by_language["typescript"]["median_elapsed_seconds"],
            ),
            "parley_source_smaller_than_python_percent": -relative_percent(
                source_medians["parley"], source_medians["python"]
            ),
            "parley_source_smaller_than_typescript_percent": -relative_percent(
                source_medians["parley"], source_medians["typescript"]
            ),
            "parley_source_smaller_than_rust_percent": -relative_percent(
                source_medians["parley"], source_medians["rust"]
            ),
        },
        "median_final_source_o200k_tokens": source_medians,
        "audit_pass": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-external", action="store_true")
    args = parser.parse_args()
    result = audit(verify_external=not args.skip_external)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
