#!/usr/bin/env python3
"""Prove exact-build hash checks catch the lock ordering missed in study 037."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Sequence

try:
    from .exact_build_freeze import run_frozen_builds, sha256, snapshot_read_only
except ImportError:
    from exact_build_freeze import run_frozen_builds, sha256, snapshot_read_only


BENCHMARKS = Path(__file__).resolve().parent
FIXTURE = BENCHMARKS / "fullstack_038/rust_smoke"
READ_ONLY = ["Cargo.toml", "Cargo.lock"]
BUILD_COMMANDS = [
    ["cargo", "build", "--locked", "--offline", "--release"],
    [
        "cargo",
        "build",
        "--locked",
        "--offline",
        "--release",
        "--lib",
        "--target",
        "wasm32-unknown-unknown",
    ],
]


def noncanonical_lock(text: str, package_name: str) -> str:
    prefix, *packages = text.split("[[package]]")
    target = None
    retained = []
    needle = f'name = "{package_name}"'
    for package in packages:
        if needle in package:
            if target is not None:
                raise ValueError(f"duplicate root package: {package_name}")
            target = package
        else:
            retained.append(package)
    if target is None:
        raise ValueError(f"missing root package: {package_name}")
    return "[[package]]".join([prefix, *retained, target])


def metadata_probe(workspace: Path, environment: dict[str, str]) -> dict:
    before = snapshot_read_only(workspace, READ_ONLY)
    completed = subprocess.run(
        ["cargo", "metadata", "--locked", "--offline", "--format-version", "1"],
        cwd=workspace,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )
    after = snapshot_read_only(workspace, READ_ONLY)
    return {
        "command": ["cargo", "metadata", "--locked", "--offline", "--format-version", "1"],
        "returncode": completed.returncode,
        "stderr_tail": completed.stderr[-2000:],
        "read_only_before": before,
        "read_only_after": after,
        "lock_unchanged": before["Cargo.lock"]["sha256"] == after["Cargo.lock"]["sha256"],
        "ok": completed.returncode == 0 and before == after,
    }


def scrub(result: dict, workspace: Path) -> dict:
    encoded = json.dumps(result).replace(str(workspace), "<workspace>")
    value = json.loads(encoded)
    value.pop("root", None)
    for command in value.get("commands", []):
        command.pop("elapsed_seconds", None)
    return value


def run_smoke() -> dict:
    if not (FIXTURE / "Cargo.lock").is_file():
        raise RuntimeError("generate and review the canonical fixture Cargo.lock first")
    with tempfile.TemporaryDirectory(prefix="parley-exact-build-freeze-038-") as raw_root:
        root = Path(raw_root)
        canonical = root / "canonical"
        noncanonical = root / "noncanonical"
        shutil.copytree(FIXTURE, canonical)
        shutil.copytree(FIXTURE, noncanonical)
        rewritten = noncanonical_lock(
            (noncanonical / "Cargo.lock").read_text(encoding="utf-8"),
            "fullstack-freeze-smoke-038",
        )
        (noncanonical / "Cargo.lock").write_text(rewritten, encoding="utf-8")

        common_environment = {"CARGO_NET_OFFLINE": "true"}
        metadata_environment = {
            **os.environ,
            **common_environment,
            "CARGO_TARGET_DIR": str(root / "metadata-target"),
        }
        metadata = metadata_probe(noncanonical, metadata_environment)
        canonical_result = run_frozen_builds(
            canonical,
            READ_ONLY,
            BUILD_COMMANDS,
            environment={
                **common_environment,
                "CARGO_TARGET_DIR": str(root / "canonical-target"),
            },
        )
        noncanonical_result = run_frozen_builds(
            noncanonical,
            READ_ONLY,
            [["cargo", "build", "--release"]],
            environment={
                **common_environment,
                "CARGO_TARGET_DIR": str(root / "noncanonical-target"),
            },
        )
        canonical_result = scrub(canonical_result, canonical)
        noncanonical_result = scrub(noncanonical_result, noncanonical)

    assert metadata["ok"]
    assert canonical_result["ok"]
    assert not noncanonical_result["ok"]
    assert set(noncanonical_result["read_only_changes"]) == {"Cargo.lock"}
    assert noncanonical_result["commands"][0]["returncode"] == 0
    return {
        "schema_version": 1,
        "experiment_id": "038-execution-mechanism",
        "task_semantics_frozen": False,
        "purpose": "Prove exact measured builds preserve canonical frozen inputs and expose noncanonical lock ordering that metadata alone misses.",
        "fixture": {
            "path": "benchmarks/fullstack_038/rust_smoke",
            "cargo_toml_sha256": sha256(FIXTURE / "Cargo.toml"),
            "cargo_lock_sha256": sha256(FIXTURE / "Cargo.lock"),
            "lib_sha256": sha256(FIXTURE / "src/lib.rs"),
            "main_sha256": sha256(FIXTURE / "src/main.rs"),
        },
        "exact_build_commands": BUILD_COMMANDS,
        "iteration_037_build_command": ["cargo", "build", "--release"],
        "canonical_exact_build": canonical_result,
        "noncanonical_metadata_probe": metadata,
        "noncanonical_exact_build": noncanonical_result,
        "gate": {
            "canonical_exact_build_passes": canonical_result["ok"],
            "metadata_false_negative_reproduced": metadata["ok"],
            "exact_build_detects_noncanonical_lock": not noncanonical_result["ok"],
            "passed": canonical_result["ok"] and metadata["ok"] and not noncanonical_result["ok"],
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=BENCHMARKS / "exact_build_freeze_038_smoke.json",
    )
    args = parser.parse_args(argv)
    result = run_smoke()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "gate": result["gate"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
