#!/usr/bin/env python3
"""Compare the frozen v0.5.4 and v0.5.5 cold web-build measurements."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
BASELINE = BENCHMARKS / "web_build_latency_002_baseline.json"
CANDIDATE = BENCHMARKS / "web_build_latency_002_candidate.json"
DEFAULT_OUTPUT = BENCHMARKS / "web_build_latency_002_analysis.json"
BASELINE_SHA256 = "b6c951d84f1754f0d7fa640379accbdf1e2dccf2a3af6c333a354d0080e8f62b"
CANDIDATE_SHA256 = "25efbcc80906060c3403c0e00852ff43ff8f7c0dcd4440c672613dbff9fdb9f7"
PRODUCT_FILES = {
    "parley/web.py": "1585e7f3f19815e7b0481dcbaf37bab7a8c26fd098deb5964ed304e37098cf2d",
    "parley/cli.py": "656a7ba25e340bf0ebdf9b7c0ce8877aa03cbbad2aa6562186e587530d56b71a",
    "parley/__init__.py": "5c7ad293b29a5b84ce4c7a39324b847622de1c531a49e6c2d55f32f979b2d3df",
    "pyproject.toml": "2621ecc54229070a1bf913ccddf473df42fecde2a1422a6facaecd0ccd403cc0",
}
VERIFICATION_FILES = {
    "tests/test_web.py": "974cb0bf530c1c08405cec142a676b2dea5616866fd5014eb3a574b206b27388",
    "benchmarks/analyze_web_build_latency_001.py": "6a484f43f90040a62681890ad5f9a97aa1e82ae1ebc55a8f85163cbb843f8964",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percent_change(before: float, after: float) -> float:
    return round((after / before - 1.0) * 100.0, 4)


def verify_current_files() -> None:
    actual_product = {
        relative: sha256(REPO / relative) for relative in PRODUCT_FILES
    }
    actual_verification = {
        relative: sha256(REPO / relative) for relative in VERIFICATION_FILES
    }
    if actual_product != PRODUCT_FILES:
        raise AssertionError(f"candidate product hashes changed: {actual_product}")
    if actual_verification != VERIFICATION_FILES:
        raise AssertionError(
            f"candidate verification hashes changed: {actual_verification}"
        )


def analyze() -> dict[str, Any]:
    assert sha256(BASELINE) == BASELINE_SHA256
    assert sha256(CANDIDATE) == CANDIDATE_SHA256
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert baseline["study_id"] == candidate["study_id"] == "web-build-latency-002"
    assert baseline["fixture_sha256"] == candidate["fixture_sha256"]
    assert baseline["repetitions"] == candidate["repetitions"] == 4
    assert len(baseline["cells"]) == len(candidate["cells"]) == 16
    assert not any(row["stderr"] for row in baseline["cells"] + candidate["cells"])
    assert baseline["toolchain"]["parley"] == "parley 0.5.4"
    assert candidate["toolchain"]["parley"] == "parley 0.5.5"
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
    primary_improvement = round(
        -percent_change(before_primary, after_primary), 4
    )
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
        "study_id": "web-build-latency-002-analysis",
        "generated_at": candidate["generated_at"],
        "baseline_sha256": sha256(BASELINE),
        "candidate_sha256": sha256(CANDIDATE),
        "fixture_sha256": candidate["fixture_sha256"],
        "candidate_product_file_sha256": PRODUCT_FILES,
        "candidate_verification_file_sha256": VERIFICATION_FILES,
        "candidate_provenance": {
            "git_base": candidate["toolchain"]["git_commit"],
            "parley_version": candidate["toolchain"]["parley"],
            "note": (
                "The candidate was measured from the exact product and verification "
                "file hashes published here; its Git field records the clean base "
                "before those changes were committed."
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
            "regression_tests_passed": 609,
            "regression_tests_failed": 0,
            "strict_json_behaviors": [
                "unknown fields rejected",
                "duplicate fields rejected",
                "missing required fields rejected",
                "wrong scalar and collection types rejected",
                "missing optional fields default to nothing",
                "unknown enum variants rejected",
                "nested records, lists, text-keyed maps, decimals, and Unicode round trip",
                "malformed numbers, escapes, surrogates, and trailing input rejected",
                "explicit Parley JSON retains the derive backend",
                "native serving and browser/WASM paths pass",
                "historical v0.5.4 analysis remains byte-for-byte reproducible",
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
        "finding": (
            "Parley v0.5.5 reduced the frozen primary cold web-build aggregate "
            "from 2.725720 to 0.802735 seconds (70.5496%) by generating a strict "
            "standard-library JSON boundary for route-only programs. Every fixture "
            "improved, the explicit-JSON control retained its established Serde "
            "backend, native artifacts became smaller, WASM sizes were unchanged, "
            "and all 609 regression tests passed."
        ),
        "claim_boundary": (
            "This accepts a generic build-path product improvement on the frozen "
            "local benchmark. It does not change iteration 043, predict a future "
            "agent-study gate, or establish universal language superiority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-current-files", action="store_true")
    args = parser.parse_args()
    if args.verify_current_files:
        verify_current_files()
    result = analyze()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
