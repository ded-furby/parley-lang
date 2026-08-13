#!/usr/bin/env python3
"""Measure frozen non-042 cold `parley web build` latency."""

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
DEFAULT_OUTPUT = REPO / "benchmarks/web_build_latency_001_result.json"

INDEX = "<!doctype html><meta charset=\"utf-8\"><title>build fixture</title>\n"

FIXTURES: dict[str, dict[str, Any]] = {
    "status_only": {
        "source": """\
a build_status has service as text, ready as yesno

to build_health giving build_status:
    give back a build_status with service "Cold Status", ready yes
""",
        "manifest": {
            "schema_version": 1,
            "name": "cold-status",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [
                {"method": "GET", "path": "/status/cold", "handler": "build_health"}
            ],
            "server": {"port": 18801, "max_body_bytes": 4096},
        },
        "browser": False,
    },
    "browser_score": {
        "source": """\
a score_status has service as text, ready as yesno

to score_health giving score_status:
    give back a score_status with service "Cold Score", ready yes

to cold_score with completed as number, urgent as yesno giving number:
    if urgent:
        give back completed times 3 plus 7
    give back completed times 2
""",
        "manifest": {
            "schema_version": 1,
            "name": "cold-score",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [
                {"method": "GET", "path": "/status/score", "handler": "score_health"}
            ],
            "browser": {"exports": [{"name": "cold_score"}]},
            "server": {"port": 18802, "max_body_bytes": 4096},
        },
        "browser": True,
    },
    "typed_post": {
        "source": """\
a queue_request has regular_jobs as number, priority_jobs as number, workers as number, urgent as yesno
a queue_response has job_total as number, required_minutes as number, capacity_minutes as number, delayed_minutes as number, queue_state as text

to queue_delay with regular_jobs as number, priority_jobs as number, workers as number, urgent as yesno giving number:
    let required be regular_jobs times 5 plus priority_jobs times 11
    if urgent:
        set required to required plus workers times 3
    let capacity be workers times 24
    if required is more than capacity:
        give back required minus capacity
    give back 0

to queue_plan with request as queue_request giving queue_response:
    let required be request's regular_jobs times 5 plus request's priority_jobs times 11
    if request's urgent:
        set required to required plus request's workers times 3
    let capacity be request's workers times 24
    let delayed be (queue_delay with request's regular_jobs, request's priority_jobs, request's workers, request's urgent)
    let state be "clear"
    if delayed is more than 0:
        set state to "delayed"
    give back a queue_response with job_total (request's regular_jobs plus request's priority_jobs), required_minutes required, capacity_minutes capacity, delayed_minutes delayed, queue_state state
""",
        "manifest": {
            "schema_version": 1,
            "name": "cold-queue",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [
                {"method": "POST", "path": "/api/cold-queue", "handler": "queue_plan"}
            ],
            "browser": {"exports": [{"name": "queue_delay"}]},
            "server": {"port": 18803, "max_body_bytes": 4096},
        },
        "browser": True,
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
    with tempfile.TemporaryDirectory(prefix="parley-web-build-001-") as temp:
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
    warmup = build_once(command, "browser_score")
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
    return {
        "schema_version": 1,
        "study_id": "web-build-latency-001",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "Three frozen non-042 projects; fresh target per cell; no exclusions or reruns.",
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
        "acceptance": {
            "minimum_latency_improvement_percent": 20.0,
            "maximum_unjustified_size_increase_percent": 25.0,
        },
        "claim_boundary": (
            "This local product benchmark measures cold web-build latency only; "
            "it is not an iteration-042 rerun or evidence of universal superiority."
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
