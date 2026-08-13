#!/usr/bin/env python3
"""Measure frozen non-043 cold `parley web build` latency."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile
import time
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO / "benchmarks/web_build_latency_002_result.json"

INDEX = "<!doctype html><meta charset=\"utf-8\"><title>build fixture</title>\n"

FIXTURES: dict[str, dict[str, Any]] = {
    "depot_overview": {
        "source": """\
a depot_mode is one of open, paused
a depot_status has label as text, mode as depot_mode, note as maybe text

to depot_health giving depot_status:
    give back a depot_status with label "North Depot", mode open, note nothing
""",
        "manifest": {
            "schema_version": 1,
            "name": "depot-overview",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [
                {"method": "GET", "path": "/status/depot", "handler": "depot_health"}
            ],
            "server": {"port": 18901, "max_body_bytes": 4096},
        },
        "browser": False,
        "primary": True,
    },
    "orchard_batch": {
        "source": """\
a harvest_request has standard_crates as number, chilled_crates as number, crews as number, priority as yesno
a harvest_response has fruit_total as number, labor_minutes as number, spare_minutes as number, batch_state as text

to orchard_spare with standard_crates as number, chilled_crates as number, crews as number, priority as yesno giving number:
    let labor be standard_crates times 4 plus chilled_crates times 9
    if priority:
        set labor to labor plus crews times 2
    let capacity be crews times 30
    if capacity is more than labor:
        give back capacity minus labor
    give back 0

to orchard_plan with request as harvest_request giving harvest_response:
    let labor be request's standard_crates times 4 plus request's chilled_crates times 9
    if request's priority:
        set labor to labor plus request's crews times 2
    let spare be (orchard_spare with request's standard_crates, request's chilled_crates, request's crews, request's priority)
    let state be "balanced"
    if spare is 0:
        set state to "full"
    give back a harvest_response with fruit_total (request's standard_crates plus request's chilled_crates), labor_minutes labor, spare_minutes spare, batch_state state
""",
        "manifest": {
            "schema_version": 1,
            "name": "orchard-batch",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [
                {"method": "POST", "path": "/api/orchard-batch", "handler": "orchard_plan"}
            ],
            "browser": {"exports": [{"name": "orchard_spare"}]},
            "server": {"port": 18902, "max_body_bytes": 8192},
        },
        "browser": True,
        "primary": True,
    },
    "weather_dispatch": {
        "source": """\
a weather_status has service as text, ready as yesno
a dispatch_request has routine_reports as number, severe_reports as number, analysts as number, overnight as yesno
a dispatch_response has report_total as number, required_minutes as number, available_minutes as number, overflow_minutes as number, dispatch_mode as text

to weather_health giving weather_status:
    give back a weather_status with service "Weather Dispatch", ready yes

to weather_overflow with routine_reports as number, severe_reports as number, analysts as number, overnight as yesno giving number:
    let required be routine_reports times 3 plus severe_reports times 13
    if overnight:
        set required to required plus analysts times 4
    let available be analysts times 26
    if required is more than available:
        give back required minus available
    give back 0

to weather_plan with request as dispatch_request giving dispatch_response:
    let required be request's routine_reports times 3 plus request's severe_reports times 13
    if request's overnight:
        set required to required plus request's analysts times 4
    let available be request's analysts times 26
    let overflow be (weather_overflow with request's routine_reports, request's severe_reports, request's analysts, request's overnight)
    let mode be "normal"
    if overflow is more than 0:
        set mode to "overflow"
    give back a dispatch_response with report_total (request's routine_reports plus request's severe_reports), required_minutes required, available_minutes available, overflow_minutes overflow, dispatch_mode mode
""",
        "manifest": {
            "schema_version": 1,
            "name": "weather-dispatch",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [
                {"method": "GET", "path": "/status/weather", "handler": "weather_health"},
                {"method": "POST", "path": "/api/weather-dispatch", "handler": "weather_plan"}
            ],
            "browser": {"exports": [{"name": "weather_overflow"}]},
            "server": {"port": 18903, "max_body_bytes": 8192},
        },
        "browser": True,
        "primary": True,
    },
    "explicit_json_control": {
        "source": """\
a archive_probe has code as text, copies as number, verified as yesno

to archive_encode with request as archive_probe giving text:
    give back request as json
""",
        "manifest": {
            "schema_version": 1,
            "name": "archive-json-control",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [
                {"method": "POST", "path": "/api/archive-encode", "handler": "archive_encode"}
            ],
            "server": {"port": 18904, "max_body_bytes": 4096},
        },
        "browser": False,
        "primary": False,
    },
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fixture_files(name: str) -> dict[str, bytes]:
    fixture = FIXTURES[name]
    return {
        "main.par": fixture["source"].encode(),
        "parley.web.json": (
            json.dumps(fixture["manifest"], indent=2) + "\n"
        ).encode(),
        "public/index.html": INDEX.encode(),
    }


def fixture_sha256(name: str) -> str:
    digest = hashlib.sha256()
    for relative, content in sorted(fixture_files(name).items()):
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def write_fixture(root: Path, name: str) -> Path:
    project = root / name
    project.mkdir(parents=True)
    for relative, content in fixture_files(name).items():
        destination = project / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    return project


def run_command(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=600)


def command_version(command: str) -> str:
    completed = run_command([command, "--version"], cwd=REPO)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or f"{command} --version failed")
    return completed.stdout.strip()


def build_once(command: str, fixture_name: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="parley-web-build-002-") as temp:
        root = Path(temp)
        project = write_fixture(root, fixture_name)
        checked = run_command([command, "web", "check", str(project), "--json"], cwd=root)
        if checked.returncode != 0:
            raise RuntimeError(f"{fixture_name} check failed: {checked.stderr}")
        output = root / "bundle"
        started = time.perf_counter()
        built = run_command(
            [command, "web", "build", str(project), "-o", str(output)],
            cwd=root,
        )
        elapsed = time.perf_counter() - started
        if built.returncode != 0:
            raise RuntimeError(f"{fixture_name} build failed: {built.stderr}")
        required = [
            output / "server",
            output / "public/index.html",
            output / "parley.build.json",
        ]
        if FIXTURES[fixture_name]["browser"]:
            required.extend(
                [
                    output / "public/parley.wasm",
                    output / "public/parley.js",
                    output / "public/parley.d.ts",
                ]
            )
        missing = [str(path.relative_to(output)) for path in required if not path.is_file()]
        if missing:
            raise RuntimeError(f"{fixture_name} bundle missing {missing}")
        return {
            "fixture": fixture_name,
            "elapsed_seconds": round(elapsed, 6),
            "server_bytes": (output / "server").stat().st_size,
            "wasm_bytes": (
                (output / "public/parley.wasm").stat().st_size
                if FIXTURES[fixture_name]["browser"]
                else 0
            ),
            "stdout_sha256": sha256_bytes(built.stdout.encode()),
            "stderr": built.stderr,
        }


def measure(command: str, repetitions: int) -> dict[str, Any]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    # One unmeasured full-stack warmup stabilizes process and filesystem caches;
    # each measured target directory remains new and cold.
    warmup = build_once(command, "weather_dispatch")
    cells = [
        build_once(command, fixture_name)
        for fixture_name in FIXTURES
        for _replicate in range(repetitions)
    ]
    summaries = {}
    for fixture_name in FIXTURES:
        rows = [row for row in cells if row["fixture"] == fixture_name]
        summaries[fixture_name] = {
            "sessions": len(rows),
            "primary": FIXTURES[fixture_name]["primary"],
            "median_elapsed_seconds": round(
                statistics.median(row["elapsed_seconds"] for row in rows), 6
            ),
            "mean_elapsed_seconds": round(
                statistics.mean(row["elapsed_seconds"] for row in rows), 6
            ),
            "median_server_bytes": statistics.median(
                row["server_bytes"] for row in rows
            ),
            "median_wasm_bytes": statistics.median(row["wasm_bytes"] for row in rows),
        }
    fixture_medians = [
        summary["median_elapsed_seconds"] for summary in summaries.values()
    ]
    primary_fixture_medians = [
        summary["median_elapsed_seconds"]
        for summary in summaries.values()
        if summary["primary"]
    ]
    return {
        "schema_version": 1,
        "study_id": "web-build-latency-002",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "Four frozen non-043 projects; fresh target per cell; no exclusions or reruns.",
        "repetitions": repetitions,
        "toolchain": {
            "parley": command_version(command),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cargo": command_version("cargo"),
            "rustc": command_version("rustc"),
            "git_commit": run_command(["git", "rev-parse", "HEAD"], cwd=REPO).stdout.strip(),
        },
        "fixture_sha256": {name: fixture_sha256(name) for name in FIXTURES},
        "warmup": warmup,
        "cells": cells,
        "by_fixture": summaries,
        "median_of_fixture_medians_seconds": round(
            statistics.median(fixture_medians), 6
        ),
        "primary_median_of_fixture_medians_seconds": round(
            statistics.median(primary_fixture_medians), 6
        ),
        "acceptance": {
            "minimum_latency_improvement_percent": 20.0,
            "maximum_fixture_regression_percent": 5.0,
            "maximum_unjustified_size_increase_percent": 25.0,
        },
        "claim_boundary": (
            "This local product benchmark measures cold web-build latency only; "
            "it is not an iteration-043 rerun or evidence of universal superiority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parley-command", default="parley")
    parser.add_argument("--repetitions", type=int, default=4)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = measure(args.parley_command, args.repetitions)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
