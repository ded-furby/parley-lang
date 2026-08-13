#!/usr/bin/env python3
"""Independently audit the immutable raw result from full-stack study 044."""

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
RAW = BENCHMARKS / "fullstack_agent_044_raw.json"
PROTOCOL = BENCHMARKS / "fullstack_agent_044_protocol.json"
VALIDATION = BENCHMARKS / "fullstack_agent_044_validation.json"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_044_audit.json"
RAW_SHA256 = "76512be28a1d0052c98aa4f601f4945b92423777a5a8560bba0a0c7afcef3399"
MEASUREMENT_COMMIT = "ecdbf5198ef9aad24408b0c2f86dfdb03981d62b"
LANGUAGES = ("parley", "python", "typescript", "rust")
CONFIGURATIONS = ("sol-medium", "terra-medium")
KINDS = ("implementation", "maintenance")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    maintenance = [
        row
        for row in rows
        if row["task_kind"] == "maintenance" and row.get("hidden_success")
    ]
    hidden = sum(bool(row.get("hidden_success")) for row in rows)
    first = sum(bool(row.get("first_public_check_success")) for row in rows)
    roots = sum(bool(row.get("exact_root")) for row in maintenance)
    return {
        "sessions": len(rows),
        "hidden_successes": hidden,
        "hidden_success_rate": hidden / len(rows),
        "first_check_successes": first,
        "first_check_success_rate": first / len(rows),
        "hidden_correct_maintenance_rows": len(maintenance),
        "exact_root_successes": roots,
        "exact_root_rate": roots / len(maintenance) if maintenance else 0.0,
        "median_total_tokens": statistics.median(
            float(row["total_tokens"]) for row in rows
        ),
        "median_elapsed_seconds": statistics.median(
            float(row["elapsed_seconds"]) for row in rows
        ),
        "repair_turns": sum(int(row["repair_turns"]) for row in rows),
    }


def relative_percent(value: float, baseline: float) -> float:
    return round((value / baseline - 1.0) * 100.0, 4)


def audit(*, verify_external: bool) -> dict[str, Any]:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    assert sha256(RAW) == RAW_SHA256
    assert raw["experiment_id"] == protocol["experiment_id"] == "044"
    assert raw["protocol"] == protocol
    assert raw["protocol_sha256"] == sha256(PROTOCOL)
    assert validation["protocol_sha256"] == sha256(PROTOCOL)
    assert raw["repository"] == raw["repository_after"]
    assert raw["repository"]["commit"] == MEASUREMENT_COMMIT
    assert raw["repository"]["status_porcelain"] == ""
    assert raw["provenance_after_execution_error"] == ""
    assert raw["run_failure"] is None
    assert raw["run_failure_file"] is None
    for key, path in (
        ("runner_sha256", BENCHMARKS / "run_fullstack_agent_044.py"),
        ("preparer_sha256", BENCHMARKS / "prepare_fullstack_agent_044.py"),
        ("scaffolds_sha256", BENCHMARKS / "fullstack_agent_044_scaffolds.py"),
        ("transport_sha256", BENCHMARKS / "agent_check_transport.py"),
        ("guard_sha256", BENCHMARKS / "fullstack_agent_044_guard.py"),
    ):
        assert raw[key] == sha256(path)
    for item in protocol["execution_freeze"]["files"]:
        assert sha256(REPO / item["file"]) == item["sha256"]

    rows = raw["results"]
    plan = raw["plan"]
    by_cell = {row["cell_id"]: row for row in rows}
    assert len(rows) == len(plan) == len(by_cell) == 96
    assert [row["cell_id"] for row in rows] == [row["cell_id"] for row in plan]
    assert [row["plan_index"] for row in rows] == list(range(1, 97))
    thread_ids = [row["thread_id"] for row in rows]
    assert len(set(thread_ids)) == 96 and all(thread_ids)
    assert Counter(row["language"] for row in rows) == Counter(
        {language: 24 for language in LANGUAGES}
    )
    assert Counter(row["configuration_id"] for row in rows) == Counter(
        {configuration: 48 for configuration in CONFIGURATIONS}
    )

    integrity_fields = (
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
    assert all(all(row[field] for field in integrity_fields) for row in rows)
    assert all(row["agent_session_started"] for row in rows)
    assert all(row["agent_returncode"] == 0 for row in rows)
    assert all(not row["agent_timed_out"] and not row["agent_errors"] for row in rows)
    assert all(row["journal_attempt"] == 1 for row in rows)
    assert all(row["command_protocol"]["compliant"] for row in rows)
    assert all(not row["unexpected_files"] for row in rows)

    external_journals = external_cleanups = external_attempts = 0
    if verify_external:
        assert sha256(Path(raw["provenance_file"])) == raw["provenance_sha256"]
        assert sha256(Path(raw["run_manifest_file"])) == raw["run_manifest_sha256"]
        assert len(raw["journal"]) == 96
        for record in raw["journal"]:
            started = Path(record["started_file"])
            finished = Path(record["finished_file"])
            cleanup = Path(record["cleanup_file"])
            assert sha256(started) == record["started_sha256"]
            assert sha256(finished) == record["finished_sha256"]
            assert sha256(cleanup) == record["cleanup_sha256"]
            start_payload = json.loads(started.read_text(encoding="utf-8"))
            finish_payload = json.loads(finished.read_text(encoding="utf-8"))
            cleanup_payload = json.loads(cleanup.read_text(encoding="utf-8"))
            assert start_payload["status"] == "started"
            assert start_payload["cell"]["cell_id"] == record["cell_id"]
            assert finish_payload["status"] == "finished"
            assert finish_payload["result"] == by_cell[record["cell_id"]]
            assert cleanup_payload == record["cleanup"]
            assert cleanup_payload["status"] == "removed"
            external_journals += 1
            external_cleanups += 1
        for row in rows:
            records = row["parent_attempt_records"]
            attempts = row["public_attempts"]
            assert len(records) == len(attempts)
            for record, attempt in zip(records, attempts, strict=True):
                path = Path(record["file"])
                assert sha256(path) == record["sha256"]
                assert json.loads(path.read_text(encoding="utf-8")) == attempt
                external_attempts += 1
        assert external_journals == external_cleanups == 96
        assert external_attempts == 97

    attempts = [attempt for row in rows for attempt in row["public_attempts"]]
    assert len(attempts) == 97
    assert sum(bool(attempt["ok"]) for attempt in attempts) == 96
    assert sum(len(attempt["cases"]) for attempt in attempts) == 388
    assert sum(
        case["target"] == "browser"
        for attempt in attempts
        for case in attempt["cases"]
    ) == 97
    assert all(attempt["cross_target"] is not None for attempt in attempts)
    assert sum(row["first_public_check_success"] for row in rows) == 95
    assert sum(row["final_public_check_success"] for row in rows) == 96
    assert sum(row["repair_turns"] for row in rows) == 1
    first_failures = {
        row["cell_id"] for row in rows if not row["first_public_check_success"]
    }
    assert first_failures == {
        "museum_conservation_build__python__terra-medium__r2"
    }

    hidden_cases = [case for row in rows for case in row["hidden_judgment"]["cases"]]
    assert len(hidden_cases) == 480
    assert sum(case["target"] == "browser" for case in hidden_cases) == 192
    assert all(case["pass"] for case in hidden_cases)
    assert all(row["hidden_judgment"]["cross_target"] is not None for row in rows)
    assert all(row["hidden_success"] for row in rows)

    build_checks = []
    for row in rows:
        for attempt in row["public_attempts"]:
            build_checks.extend(attempt["build"]["protected_read_only_checks"])
        build_checks.extend(
            row["hidden_judgment"]["build"]["protected_read_only_checks"]
        )
    assert len(build_checks) == 290
    assert all(
        check["ok"] and check["hashes_ok"] and not check["changes"]
        for check in build_checks
    )

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
        "execution_integrity": True,
        "correctness": (
            parley["hidden_success_rate"] == 1.0
            and all(parley["hidden_success_rate"] >= row["hidden_success_rate"] for row in baselines)
            and all(
                by_configuration[configuration]["parley"]["hidden_success_rate"]
                >= max(
                    by_configuration[configuration][language]["hidden_success_rate"]
                    for language in LANGUAGES if language != "parley"
                )
                for configuration in CONFIGURATIONS
            )
            and all(
                by_kind[kind]["parley"]["hidden_success_rate"]
                >= max(
                    by_kind[kind][language]["hidden_success_rate"]
                    for language in LANGUAGES if language != "parley"
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
                    for language in LANGUAGES if language != "parley"
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
                    for language in LANGUAGES if language != "parley"
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
                    for language in LANGUAGES if language != "parley"
                )
                for configuration in CONFIGURATIONS
            )
        ),
        "maintainability": (
            by_kind["maintenance"]["parley"]["exact_root_rate"] == 1.0
            and all(
                by_kind["maintenance"]["parley"]["exact_root_rate"]
                >= by_kind["maintenance"][language]["exact_root_rate"]
                for language in LANGUAGES if language != "parley"
            )
        ),
    }
    assert conditions == raw["summary"]["primary_gate"]["conditions"]
    assert conditions == {
        "execution_integrity": True,
        "correctness": True,
        "first_check": True,
        "tokens": True,
        "elapsed": True,
        "maintainability": True,
    }

    scratch_checks = raw["scratch_capacity_checks"]
    cleanup_records = [entry["cleanup"] for entry in raw["journal"]]
    assert len(scratch_checks) == 93
    assert all(check["status"] == "pass" for check in scratch_checks)
    assert raw["scratch_final"]["status"] == "pass"
    assert all(record["status"] == "removed" for record in cleanup_records)
    assert raw["scratch_summary"] == {
        "integrity_ok": True,
        "cleanup_records": 96,
        "cleanup_failures": 0,
        "peak_cell_workspace_bytes": 161144484,
        "peak_per_worker_workspace_bytes": 161144484,
        "retained_workspace_bytes_after_cleanup": 0,
    }

    source_medians = {
        language: {
            field: float(
                statistics.median(
                    row["source"]["totals"][field]
                    for row in rows if row["language"] == language
                )
            )
            for field in ("bytes", "lines", "rough_tokens", "o200k_base_tokens")
        }
        for language in LANGUAGES
    }
    return {
        "schema_version": 1,
        "experiment_id": "044",
        "generated_at": raw["generated_at"],
        "raw_sha256": sha256(RAW),
        "protocol_sha256": sha256(PROTOCOL),
        "validation_sha256": sha256(VALIDATION),
        "measurement_commit": MEASUREMENT_COMMIT,
        "external_evidence_verified": verify_external,
        "matrix": {
            "cells": len(rows),
            "unique_cell_ids": len(by_cell),
            "unique_thread_ids": len(set(thread_ids)),
            "journal_pairs_verified": external_journals,
            "cleanup_records_verified": external_cleanups,
            "attempt_files_verified": external_attempts,
        },
        "public": {
            "attempts": len(attempts),
            "successful_attempts": sum(bool(attempt["ok"]) for attempt in attempts),
            "failed_attempts": sum(not attempt["ok"] for attempt in attempts),
            "named_cases_executed": sum(len(attempt["cases"]) for attempt in attempts),
            "browser_cases_executed": sum(
                case["target"] == "browser"
                for attempt in attempts for case in attempt["cases"]
            ),
            "cross_target_checks_executed": len(attempts),
            "first_check_successes": sum(row["first_public_check_success"] for row in rows),
            "final_check_successes": sum(row["final_public_check_success"] for row in rows),
            "repair_turns": sum(row["repair_turns"] for row in rows),
        },
        "hidden": {
            "assignment_successes": sum(row["hidden_success"] for row in rows),
            "named_cases_executed": len(hidden_cases),
            "named_case_passes": sum(case["pass"] for case in hidden_cases),
            "browser_cases_executed": sum(
                case["target"] == "browser" for case in hidden_cases
            ),
            "cross_target_checks_executed": len(rows),
        },
        "exact_build": {
            "commands": len(build_checks),
            "successful_commands": sum(check["ok"] for check in build_checks),
            "stable_hash_checks": sum(check["hashes_ok"] for check in build_checks),
        },
        "scratch": {
            "capacity_checks": len(scratch_checks),
            "minimum_free_bytes": min(check["filesystem_free_bytes"] for check in scratch_checks),
            "final_free_bytes": raw["scratch_final"]["filesystem_free_bytes"],
            **raw["scratch_summary"],
        },
        "model_failure_classes": {},
        "by_language": by_language,
        "by_configuration": by_configuration,
        "by_kind": by_kind,
        "primary_gate": {"conditions": conditions, "passed": all(conditions.values())},
        "comparisons": {
            "parley_tokens_vs_python_percent": relative_percent(
                parley["median_total_tokens"], by_language["python"]["median_total_tokens"]
            ),
            "parley_elapsed_vs_python_percent": relative_percent(
                parley["median_elapsed_seconds"], by_language["python"]["median_elapsed_seconds"]
            ),
            "parley_elapsed_vs_typescript_percent": relative_percent(
                parley["median_elapsed_seconds"], by_language["typescript"]["median_elapsed_seconds"]
            ),
            "parley_source_smaller_than_python_percent": -relative_percent(
                source_medians["parley"]["o200k_base_tokens"],
                source_medians["python"]["o200k_base_tokens"],
            ),
            "parley_source_smaller_than_typescript_percent": -relative_percent(
                source_medians["parley"]["o200k_base_tokens"],
                source_medians["typescript"]["o200k_base_tokens"],
            ),
            "parley_source_smaller_than_rust_percent": -relative_percent(
                source_medians["parley"]["o200k_base_tokens"],
                source_medians["rust"]["o200k_base_tokens"],
            ),
        },
        "median_final_source": source_medians,
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
