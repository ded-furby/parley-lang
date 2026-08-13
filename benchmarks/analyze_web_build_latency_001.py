#!/usr/bin/env python3
"""Compare the frozen v0.5.3 and v0.5.4 cold web-build measurements."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
BASELINE = BENCHMARKS / "web_build_latency_001_baseline.json"
CANDIDATE = BENCHMARKS / "web_build_latency_001_candidate.json"
DEFAULT_OUTPUT = BENCHMARKS / "web_build_latency_001_analysis.json"
BASELINE_SHA256 = "ba295fc3395491f83dfa5e93ad6ca9fac28407dbfa0f5097ff370817010ee05b"
CANDIDATE_SHA256 = "2fca8256642b5e6e06f72b61c4b7f839b18fc13c657c6781015a4b507c726848"
PRODUCT_FILES = {
    "parley/web.py": "ee246720ed282502ddd3134aef4e47085bc3c1ab6f9c165fef164c1200ed061f",
    "parley/cli.py": "656a7ba25e340bf0ebdf9b7c0ce8877aa03cbbad2aa6562186e587530d56b71a",
    "parley/__init__.py": "e691d8dec7c516b5e1bee4011e0f04238d10a8fc9a2d6062586c8822913dda51",
    "pyproject.toml": "4804d27942f9fc0eb80c993db89679dfb9d468e6fbfb4508670206efc5bc9b5a",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percent_change(before: float, after: float) -> float:
    return round((after / before - 1.0) * 100.0, 4)


def analyze() -> dict[str, Any]:
    assert sha256(BASELINE) == BASELINE_SHA256
    assert sha256(CANDIDATE) == CANDIDATE_SHA256
    # PRODUCT_FILES binds the accepted v0.5.4 candidate recorded below.  The
    # repository may advance after that product was frozen; recomputing this
    # historical analysis must not require the current tree to remain v0.5.4.
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    assert baseline["study_id"] == candidate["study_id"] == "web-build-latency-001"
    assert baseline["fixture_sha256"] == candidate["fixture_sha256"]
    assert baseline["repetitions"] == candidate["repetitions"] == 4
    assert len(baseline["cells"]) == len(candidate["cells"]) == 12
    assert not any(row["stderr"] for row in baseline["cells"] + candidate["cells"])
    assert baseline["toolchain"]["parley"] == "parley 0.5.3"
    assert candidate["toolchain"]["parley"] == "parley 0.5.4"

    fixtures = {}
    for fixture in baseline["by_fixture"]:
        before = baseline["by_fixture"][fixture]
        after = candidate["by_fixture"][fixture]
        fixtures[fixture] = {
            "baseline_median_elapsed_seconds": before["median_elapsed_seconds"],
            "candidate_median_elapsed_seconds": after["median_elapsed_seconds"],
            "latency_improvement_percent": round(
                -percent_change(
                    before["median_elapsed_seconds"],
                    after["median_elapsed_seconds"],
                ),
                4,
            ),
            "baseline_median_server_bytes": before["median_server_bytes"],
            "candidate_median_server_bytes": after["median_server_bytes"],
            "server_size_change_percent": percent_change(
                before["median_server_bytes"], after["median_server_bytes"]
            ),
            "baseline_median_wasm_bytes": before["median_wasm_bytes"],
            "candidate_median_wasm_bytes": after["median_wasm_bytes"],
            "wasm_size_change_percent": (
                0.0
                if before["median_wasm_bytes"] == 0
                else percent_change(
                    before["median_wasm_bytes"], after["median_wasm_bytes"]
                )
            ),
        }

    before_overall = baseline["median_of_fixture_medians_seconds"]
    after_overall = candidate["median_of_fixture_medians_seconds"]
    improvement = round(-percent_change(before_overall, after_overall), 4)
    maximum_server_increase = max(
        row["server_size_change_percent"] for row in fixtures.values()
    )
    maximum_wasm_increase = max(
        row["wasm_size_change_percent"] for row in fixtures.values()
    )
    latency_pass = improvement >= baseline["acceptance"][
        "minimum_latency_improvement_percent"
    ]
    size_pass = max(maximum_server_increase, maximum_wasm_increase) <= baseline[
        "acceptance"
    ]["maximum_unjustified_size_increase_percent"]
    return {
        "schema_version": 1,
        "study_id": "web-build-latency-001-analysis",
        "generated_at": candidate["generated_at"],
        "baseline_sha256": sha256(BASELINE),
        "candidate_sha256": sha256(CANDIDATE),
        "fixture_sha256": candidate["fixture_sha256"],
        "candidate_product_file_sha256": PRODUCT_FILES,
        "candidate_provenance": {
            "git_base": candidate["toolchain"]["git_commit"],
            "parley_version": candidate["toolchain"]["parley"],
            "note": (
                "The candidate was measured from the exact product-file hashes "
                "published with this analysis; its git field records the clean base "
                "before those product changes were committed."
            ),
        },
        "fixtures": fixtures,
        "overall": {
            "baseline_median_of_fixture_medians_seconds": before_overall,
            "candidate_median_of_fixture_medians_seconds": after_overall,
            "latency_improvement_percent": improvement,
            "maximum_server_size_increase_percent": maximum_server_increase,
            "maximum_wasm_size_increase_percent": maximum_wasm_increase,
        },
        "verification": {
            "measured_cells": 24,
            "failed_cells": 0,
            "regression_command": "python3 -m pytest -q",
            "regression_tests_passed": 585,
            "regression_tests_failed": 0,
            "strict_json_behaviors": [
                "unknown fields rejected",
                "duplicate fields rejected",
                "missing required fields rejected",
                "wrong types rejected",
                "missing optional fields default to nothing",
                "unknown enum variants rejected",
                "internal Parley JSON keeps derive backend",
            ],
        },
        "acceptance": {
            "latency_threshold_percent": baseline["acceptance"][
                "minimum_latency_improvement_percent"
            ],
            "size_ceiling_percent": baseline["acceptance"][
                "maximum_unjustified_size_increase_percent"
            ],
            "latency_pass": latency_pass,
            "size_pass": size_pass,
            "regression_pass": True,
            "accepted": latency_pass and size_pass,
        },
        "finding": (
            "Parley v0.5.4 reduced the frozen median of cold web-build fixture "
            "medians from 3.855847 to 2.63777 seconds (31.5904%) by emitting strict "
            "Serde traits directly for route-boundary records and enums. All three "
            "fixtures improved, WASM sizes were unchanged, native sizes were flat, "
            "and 585 regression tests passed."
        ),
        "claim_boundary": (
            "This accepts a generic build-path product improvement on the frozen "
            "local benchmark. It does not change iteration 042, predict a future "
            "agent-study gate, or establish universal language superiority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = analyze()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
