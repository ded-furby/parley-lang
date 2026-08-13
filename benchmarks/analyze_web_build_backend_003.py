#!/usr/bin/env python3
"""Compare the frozen v0.5.6 baseline and rejected v0.5.7 backend candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
BASELINE = BENCHMARKS / "web_build_backend_003_baseline.json"
CANDIDATE = BENCHMARKS / "web_build_backend_003_candidate.json"
DEFAULT_OUTPUT = BENCHMARKS / "web_build_backend_003_analysis.json"
BASELINE_SHA256 = "5588e490c22c74d5a9e9be8751438ea645341433d264b723b39594acc1dfb9f0"
CANDIDATE_SHA256 = "ac161529241f770fed935b455da466f4f24b49e88e68b82ee109ea7011d8602b"
PRODUCT_FILES = {
    "parley/cli.py": "505af69739d87a6fd7e954b5e74303654af85d6be25bf192ceda14a543295b5b",
    "parley/__init__.py": "ed63eafd1e9c6a64064364846b0246112e957e3620545b96f98a2d45cf68d150",
    "pyproject.toml": "410b6f5da1f4246f1949a80a40d8926c9cc5db69219f714cd14d654be7992273",
    "docs/WEB_BUILD_BACKEND_V057.md": "c5f28b247196fae2d7bcb33437cbe0b9f296d04b139a45b7f9b30a1daec82d97",
}
VERIFICATION_FILES = {
    "tests/test_web_build_backend_003.py": "b14e0fd7543496e1159f74bc5518c12c9a1b939606b96645b30b31b2121af440",
    "benchmarks/freeze_fullstack_agent_046_product.py": "47554bbb237a8245a3a8f4d412291c11a6d0b779b64c757cceb2a041b895b592",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percent_change(before: float, after: float) -> float:
    return round((after / before - 1.0) * 100.0, 4)


def verify_current_files() -> None:
    actual = {
        relative: sha256(REPO / relative)
        for relative in (*PRODUCT_FILES, *VERIFICATION_FILES)
    }
    expected = {**PRODUCT_FILES, **VERIFICATION_FILES}
    if actual != expected:
        raise AssertionError(f"candidate file hashes changed: {actual}")


def analyze() -> dict[str, Any]:
    assert sha256(BASELINE) == BASELINE_SHA256
    assert sha256(CANDIDATE) == CANDIDATE_SHA256
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert baseline["study_id"] == candidate["study_id"] == "web-build-backend-003"
    assert baseline["fixture_sha256"] == candidate["fixture_sha256"]
    assert baseline["repetitions"] == candidate["repetitions"] == 4
    assert len(baseline["cells"]) == len(candidate["cells"]) == 16
    assert not any(row["stderr"] for row in baseline["cells"] + candidate["cells"])
    assert baseline["toolchain"]["parley"] == "parley 0.5.6"
    assert candidate["toolchain"]["parley"] == "parley 0.5.7"
    assert baseline["acceptance"] == candidate["acceptance"]

    fixtures = {}
    for fixture in baseline["by_fixture"]:
        before = baseline["by_fixture"][fixture]
        after = candidate["by_fixture"][fixture]
        latency_change = percent_change(
            before["median_elapsed_seconds"], after["median_elapsed_seconds"]
        )
        server_change = percent_change(
            before["median_server_bytes"], after["median_server_bytes"]
        )
        wasm_change = (
            0.0
            if before["median_wasm_bytes"] == 0
            else percent_change(
                before["median_wasm_bytes"], after["median_wasm_bytes"]
            )
        )
        fixtures[fixture] = {
            "primary": before["primary"],
            "response_mode": before["response_mode"],
            "baseline_median_elapsed_seconds": before["median_elapsed_seconds"],
            "candidate_median_elapsed_seconds": after["median_elapsed_seconds"],
            "latency_change_percent": latency_change,
            "latency_improvement_percent": round(-latency_change, 4),
            "baseline_median_server_bytes": before["median_server_bytes"],
            "candidate_median_server_bytes": after["median_server_bytes"],
            "server_size_change_percent": server_change,
            "baseline_median_wasm_bytes": before["median_wasm_bytes"],
            "candidate_median_wasm_bytes": after["median_wasm_bytes"],
            "wasm_size_change_percent": wasm_change,
        }

    before_primary = baseline["primary_median_of_fixture_medians_seconds"]
    after_primary = candidate["primary_median_of_fixture_medians_seconds"]
    primary_improvement = round(-percent_change(before_primary, after_primary), 4)
    maximum_fixture_regression = max(
        row["latency_change_percent"] for row in fixtures.values()
    )
    maximum_server_increase = max(
        row["server_size_change_percent"] for row in fixtures.values()
    )
    maximum_wasm_increase = max(
        row["wasm_size_change_percent"] for row in fixtures.values()
    )
    acceptance = baseline["acceptance"]
    latency_pass = primary_improvement >= acceptance[
        "minimum_latency_improvement_percent"
    ]
    fixture_regression_pass = maximum_fixture_regression <= acceptance[
        "maximum_fixture_regression_percent"
    ]
    size_pass = max(maximum_server_increase, maximum_wasm_increase) <= acceptance[
        "maximum_unjustified_size_increase_percent"
    ]
    return {
        "schema_version": 1,
        "study_id": "web-build-backend-003-analysis",
        "generated_at": candidate["generated_at"],
        "baseline_sha256": BASELINE_SHA256,
        "candidate_sha256": CANDIDATE_SHA256,
        "fixture_sha256": candidate["fixture_sha256"],
        "candidate_product_file_sha256": PRODUCT_FILES,
        "candidate_verification_file_sha256": VERIFICATION_FILES,
        "candidate_provenance": {
            "git_base": candidate["toolchain"]["git_commit"],
            "parley_version": candidate["toolchain"]["parley"],
            "note": (
                "The rejected candidate was measured from the exact file hashes "
                "published here before those files were committed."
            ),
        },
        "fixtures": fixtures,
        "overall": {
            "baseline_primary_median_of_fixture_medians_seconds": before_primary,
            "candidate_primary_median_of_fixture_medians_seconds": after_primary,
            "primary_latency_improvement_percent": primary_improvement,
            "maximum_fixture_regression_percent": maximum_fixture_regression,
            "maximum_server_size_increase_percent": maximum_server_increase,
            "maximum_wasm_size_increase_percent": maximum_wasm_increase,
        },
        "verification": {
            "measured_cells": 32,
            "failed_cells": 0,
            "regression_command": "python3 -m pytest -q",
            "regression_tests_passed": 705,
            "regression_tests_failed": 0,
            "boundaries": [
                "direct rustc JSON diagnostics retain Parley source mapping",
                "dependency-free native and browser artifacts use direct rustc",
                "explicit language JSON retains Cargo and pinned Serde",
                "dynamic response controls retain dedicated native execution coverage",
                "historical web references remain byte-for-byte frozen",
                "historical study 046 product rebuilding survives product advancement",
            ],
        },
        "acceptance": {
            "latency_threshold_percent": acceptance[
                "minimum_latency_improvement_percent"
            ],
            "fixture_regression_ceiling_percent": acceptance[
                "maximum_fixture_regression_percent"
            ],
            "size_ceiling_percent": acceptance[
                "maximum_unjustified_size_increase_percent"
            ],
            "latency_pass": latency_pass,
            "fixture_regression_pass": fixture_regression_pass,
            "size_pass": size_pass,
            "regression_pass": True,
            "accepted": (
                latency_pass and fixture_regression_pass and size_pass
            ),
        },
        "decision": {
            "release_candidate": False,
            "restore_version": "0.5.6",
            "same_population_retuning": False,
            "reason": (
                "The 4.3864% primary improvement is below the frozen 20% threshold."
            ),
        },
        "claim_boundary": (
            "This rejects a local build-path candidate. It cannot revise study 046, "
            "support a v0.5.7 release, or establish universal superiority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-current-files", action="store_true")
    args = parser.parse_args()
    if args.verify_current_files:
        verify_current_files()
    args.output.write_text(json.dumps(analyze(), indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
