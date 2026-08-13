#!/usr/bin/env python3
"""Measure frozen v0.5.6 cold web-build backend latency."""

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
DEFAULT_OUTPUT = REPO / "benchmarks/web_build_backend_003_result.json"
INDEX = '<!doctype html><meta charset="utf-8"><title>backend fixture</title>\n'

FIXTURES: dict[str, dict[str, Any]] = {
    "harbor_admission": {
        "source": """\
a harbor_request has vessel_code as text, cargo_units as number, priority as yesno
a harbor_body has vessel_code as text, accepted_units as number, decision as text
a harbor_reply has code as number, metadata as map from text to text, payload as harbor_body

to admit_vessel with request as harbor_request giving harbor_reply:
    let metadata be a map from text to text
    if request's cargo_units is less than 0:
        set item "x-harbor-error" of metadata to "cargo_units"
        give back a harbor_reply with code 422, metadata metadata, payload (a harbor_body with vessel_code request's vessel_code, accepted_units 0, decision "rejected")
    if request's priority:
        set item "retry-after" of metadata to "30"
        give back a harbor_reply with code 202, metadata metadata, payload (a harbor_body with vessel_code request's vessel_code, accepted_units request's cargo_units, decision "queued")
    set item "location" of metadata to "/api/harbor/admissions/{request's vessel_code}"
    give back a harbor_reply with code 201, metadata metadata, payload (a harbor_body with vessel_code request's vessel_code, accepted_units request's cargo_units, decision "berthed")
""",
        "manifest": {
            "schema_version": 1,
            "name": "harbor-admission",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [{
                "method": "POST",
                "path": "/api/harbor-admissions",
                "handler": "admit_vessel",
                "response": {
                    "status_field": "code",
                    "headers_field": "metadata",
                    "body_field": "payload",
                },
            }],
            "server": {"port": 19101, "max_body_bytes": 8192},
        },
        "browser": False,
        "primary": True,
        "response_mode": "dynamic",
    },
    "forest_inventory": {
        "source": """\
a inventory_request has sector as text, plots as number, crews as number, fire_watch as yesno
a inventory_body has sector as text, survey_slots as number, state as text
a inventory_reply has status as number, headers as map from text to text, body as inventory_body

to forest_slots with plots as number, crews as number, fire_watch as yesno giving number:
    let slots be crews times 12 minus plots times 2
    if fire_watch:
        set slots to slots minus crews
    if slots is less than 0:
        give back 0
    give back slots

to inventory_sector with request as inventory_request giving inventory_reply:
    let headers be a map from text to text
    let slots be (forest_slots with request's plots, request's crews, request's fire_watch)
    if request's plots is less than 0:
        set item "x-inventory-error" of headers to "plots"
        give back an inventory_reply with status 422, headers headers, body (an inventory_body with sector request's sector, survey_slots 0, state "invalid")
    if slots is 0:
        set item "retry-after" of headers to "90"
        give back an inventory_reply with status 409, headers headers, body (an inventory_body with sector request's sector, survey_slots slots, state "blocked")
    set item "x-inventory-sector" of headers to request's sector
    give back an inventory_reply with status 200, headers headers, body (an inventory_body with sector request's sector, survey_slots slots, state "scheduled")
""",
        "manifest": {
            "schema_version": 1,
            "name": "forest-inventory",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [{
                "method": "POST",
                "path": "/api/forest-inventory",
                "handler": "inventory_sector",
                "response": {
                    "status_field": "status",
                    "headers_field": "headers",
                    "body_field": "body",
                },
            }],
            "browser": {"exports": [{"name": "forest_slots"}]},
            "server": {"port": 19102, "max_body_bytes": 8192},
        },
        "browser": True,
        "primary": True,
        "response_mode": "dynamic",
    },
    "glacier_manifest": {
        "source": """\
a glacier_health has service as text, ready as yesno
a manifest_request has supply_crates as number, instrument_cases as number, sleds as number
a manifest_result has cargo_total as number, haul_minutes as number, overflow_minutes as number

to glacier_status giving glacier_health:
    give back a glacier_health with service "Glacier Manifest", ready yes

to glacier_overflow with supply_crates as number, instrument_cases as number, sleds as number giving number:
    let required be supply_crates times 5 plus instrument_cases times 18
    let available be sleds times 40
    if required is more than available:
        give back required minus available
    give back 0

to plan_glacier_manifest with request as manifest_request giving manifest_result:
    let required be request's supply_crates times 5 plus request's instrument_cases times 18
    give back a manifest_result with cargo_total (request's supply_crates plus request's instrument_cases), haul_minutes required, overflow_minutes (glacier_overflow with request's supply_crates, request's instrument_cases, request's sleds)
""",
        "manifest": {
            "schema_version": 1,
            "name": "glacier-manifest",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [
                {"method": "GET", "path": "/status/glacier", "handler": "glacier_status"},
                {"method": "POST", "path": "/api/glacier-manifest", "handler": "plan_glacier_manifest"},
            ],
            "browser": {"exports": [{"name": "glacier_overflow"}]},
            "server": {"port": 19103, "max_body_bytes": 8192},
        },
        "browser": True,
        "primary": True,
        "response_mode": "static",
    },
    "manual_json_control": {
        "source": """\
a specimen_label has accession as text, samples as number, sealed as yesno

to encode_specimen with request as specimen_label giving text:
    give back request as json
""",
        "manifest": {
            "schema_version": 1,
            "name": "manual-json-control",
            "entrypoint": "main.par",
            "static_dir": "public",
            "routes": [{
                "method": "POST",
                "path": "/api/specimen-encoding",
                "handler": "encode_specimen",
            }],
            "server": {"port": 19104, "max_body_bytes": 4096},
        },
        "browser": False,
        "primary": False,
        "response_mode": "static",
    },
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fixture_files(name: str) -> dict[str, bytes]:
    fixture = FIXTURES[name]
    return {
        "main.par": fixture["source"].encode(),
        "parley.web.json": (json.dumps(fixture["manifest"], indent=2) + "\n").encode(),
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
    with tempfile.TemporaryDirectory(prefix="parley-web-backend-003-") as temp:
        root = Path(temp)
        project = write_fixture(root, fixture_name)
        checked = run_command([command, "web", "check", str(project), "--json"], cwd=root)
        if checked.returncode != 0:
            raise RuntimeError(f"{fixture_name} check failed: {checked.stderr}")
        output = root / "bundle"
        started = time.perf_counter()
        built = run_command(
            [command, "web", "build", str(project), "-o", str(output)], cwd=root
        )
        elapsed = time.perf_counter() - started
        if built.returncode != 0:
            raise RuntimeError(f"{fixture_name} build failed: {built.stderr}")
        required = [output / "server", output / "public/index.html", output / "parley.build.json"]
        if FIXTURES[fixture_name]["browser"]:
            required.extend([
                output / "public/parley.wasm",
                output / "public/parley.js",
                output / "public/parley.d.ts",
            ])
        missing = [str(path.relative_to(output)) for path in required if not path.is_file()]
        if missing:
            raise RuntimeError(f"{fixture_name} bundle missing {missing}")
        metadata = json.loads((output / "parley.build.json").read_text())
        return {
            "fixture": fixture_name,
            "elapsed_seconds": round(elapsed, 6),
            "server_bytes": (output / "server").stat().st_size,
            "wasm_bytes": (
                (output / "public/parley.wasm").stat().st_size
                if FIXTURES[fixture_name]["browser"] else 0
            ),
            "build_manifest_sha256": sha256_bytes(
                (output / "parley.build.json").read_bytes()
            ),
            "response_modes": [route["response"]["mode"] for route in metadata["routes"]],
            "stdout_sha256": sha256_bytes(built.stdout.encode()),
            "stderr": built.stderr,
        }


def measure(command: str, repetitions: int) -> dict[str, Any]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    warmup = build_once(command, "forest_inventory")
    cells = [
        build_once(command, fixture_name)
        for fixture_name in FIXTURES
        for _replicate in range(repetitions)
    ]
    summaries = {}
    for fixture_name, fixture in FIXTURES.items():
        rows = [row for row in cells if row["fixture"] == fixture_name]
        summaries[fixture_name] = {
            "sessions": len(rows),
            "primary": fixture["primary"],
            "response_mode": fixture["response_mode"],
            "median_elapsed_seconds": round(
                statistics.median(row["elapsed_seconds"] for row in rows), 6
            ),
            "mean_elapsed_seconds": round(
                statistics.mean(row["elapsed_seconds"] for row in rows), 6
            ),
            "median_server_bytes": statistics.median(row["server_bytes"] for row in rows),
            "median_wasm_bytes": statistics.median(row["wasm_bytes"] for row in rows),
        }
    primary_medians = [
        summary["median_elapsed_seconds"]
        for summary in summaries.values() if summary["primary"]
    ]
    return {
        "schema_version": 1,
        "study_id": "web-build-backend-003",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "Four frozen non-046 v0.5.6 projects; fresh target per cell; no exclusions or reruns.",
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
        "primary_median_of_fixture_medians_seconds": round(
            statistics.median(primary_medians), 6
        ),
        "acceptance": {
            "minimum_latency_improvement_percent": 20.0,
            "maximum_fixture_regression_percent": 5.0,
            "maximum_unjustified_size_increase_percent": 25.0,
        },
        "claim_boundary": (
            "This local product benchmark measures cold web-build backend latency only; "
            "it cannot revise study 046 or establish universal superiority."
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
