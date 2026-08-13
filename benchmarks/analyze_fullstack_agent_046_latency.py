#!/usr/bin/env python3
"""Recompute the post-result latency decomposition for study 046."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
from typing import Any, Callable


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "fullstack_agent_046_raw.json"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_046_latency.json"
RAW_SHA256 = "0117effbc633affb6d79d14e8f1b713634ca3c5c263537e1ba2207b7ccaf2d07"
LANGUAGES = ("parley", "python", "typescript", "rust")
CONFIGURATIONS = ("sol-medium", "terra-medium")
BOOTSTRAP_SEED = 460260814
BOOTSTRAP_SAMPLES = 50_000


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_check_seconds(row: dict[str, Any]) -> float:
    return sum(float(attempt["elapsed_seconds"]) for attempt in row["public_attempts"])


def public_build_seconds(row: dict[str, Any]) -> float:
    return sum(
        float(attempt["build"]["elapsed_seconds"])
        for attempt in row["public_attempts"]
    )


def public_runtime_seconds(row: dict[str, Any]) -> float:
    return public_check_seconds(row) - public_build_seconds(row)


def noncheck_seconds(row: dict[str, Any]) -> float:
    return float(row["elapsed_seconds"]) - public_check_seconds(row)


COMPONENTS: dict[str, Callable[[dict[str, Any]], float]] = {
    "session_elapsed_seconds": lambda row: float(row["elapsed_seconds"]),
    "public_check_seconds": public_check_seconds,
    "public_build_seconds": public_build_seconds,
    "public_runtime_seconds": public_runtime_seconds,
    "noncheck_session_seconds": noncheck_seconds,
}


def summarize(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "median": round(float(statistics.median(ordered)), 4),
        "mean": round(float(statistics.mean(ordered)), 4),
        "minimum": round(ordered[0], 4),
        "maximum": round(ordered[-1], 4),
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sessions": len(rows),
        **{
            name: summarize([function(row) for row in rows])
            for name, function in COMPONENTS.items()
        },
    }


def bootstrap_median_interval(values: list[float]) -> list[float]:
    rng = random.Random(BOOTSTRAP_SEED)
    count = len(values)
    medians = sorted(
        statistics.median(values[rng.randrange(count)] for _ in range(count))
        for _ in range(BOOTSTRAP_SAMPLES)
    )
    return [
        round(float(medians[int((BOOTSTRAP_SAMPLES - 1) * quantile)]), 4)
        for quantile in (0.025, 0.975)
    ]


def sign_test_two_sided(faster: int, slower: int) -> float:
    count = faster + slower
    tail = min(faster, slower)
    probability = sum(math.comb(count, index) for index in range(tail + 1)) / 2**count
    return round(min(2 * probability, 1.0), 6)


def relative_percent(value: float, baseline: float) -> float:
    return round((value / baseline - 1) * 100, 4)


def build() -> dict[str, Any]:
    assert digest(RAW) == RAW_SHA256
    raw = json.loads(RAW.read_text())
    rows = raw["results"]
    assert len(rows) == 96
    assert raw["summary"]["primary_gate"]["conditions"]["elapsed"] is False
    by_language = {
        language: summarize_rows([row for row in rows if row["language"] == language])
        for language in LANGUAGES
    }
    by_configuration = {
        configuration: {
            language: summarize_rows([
                row for row in rows
                if row["configuration_id"] == configuration
                and row["language"] == language
            ])
            for language in LANGUAGES
        }
        for configuration in CONFIGURATIONS
    }

    index = {
        (row["task_id"], row["configuration_id"], row["replicate"], row["language"]): row
        for row in rows
    }
    paired = []
    for key, parley in index.items():
        if key[-1] != "parley":
            continue
        python = index[(*key[:3], "python")]
        paired.append({
            "task_id": key[0],
            "configuration_id": key[1],
            "replicate": key[2],
            "elapsed_difference_seconds": (
                float(parley["elapsed_seconds"]) - float(python["elapsed_seconds"])
            ),
            "public_check_difference_seconds": (
                public_check_seconds(parley) - public_check_seconds(python)
            ),
            "public_build_difference_seconds": (
                public_build_seconds(parley) - public_build_seconds(python)
            ),
            "noncheck_difference_seconds": (
                noncheck_seconds(parley) - noncheck_seconds(python)
            ),
            "total_token_difference": int(parley["total_tokens"])
            - int(python["total_tokens"]),
        })
    paired.sort(key=lambda row: (
        row["task_id"], row["configuration_id"], row["replicate"]
    ))
    elapsed_differences = [row["elapsed_difference_seconds"] for row in paired]
    token_differences = [float(row["total_token_difference"]) for row in paired]
    parley_faster = sum(value < 0 for value in elapsed_differences)
    python_faster = sum(value > 0 for value in elapsed_differences)

    parley = by_language["parley"]
    python = by_language["python"]
    return {
        "schema_version": 1,
        "experiment_id": "046",
        "phase": "post-result secondary latency decomposition",
        "raw_sha256": RAW_SHA256,
        "bootstrap": {
            "seed": BOOTSTRAP_SEED,
            "samples": BOOTSTRAP_SAMPLES,
            "unit": "matched task/configuration/replicate pair",
        },
        "definitions": {
            "session_elapsed_seconds": (
                "Frozen primary wall time around the complete Codex subprocess and all "
                "parent public checks requested during it; hidden judgment is excluded."
            ),
            "public_check_seconds": "Sum of parent-recorded ./check attempt wall times.",
            "public_build_seconds": "Sum of exact application build wall times inside public checks.",
            "public_runtime_seconds": (
                "Public check time minus build time; includes server, HTTP, Chromium, "
                "proxy, and parent-check overhead."
            ),
            "noncheck_session_seconds": (
                "Session elapsed minus public check time; includes model service latency, "
                "source printing, editing, command transport, and other agent work."
            ),
        },
        "by_language": by_language,
        "by_configuration": by_configuration,
        "parley_vs_python": {
            "marginal_median": {
                "elapsed_difference_seconds": round(
                    parley["session_elapsed_seconds"]["median"]
                    - python["session_elapsed_seconds"]["median"], 4
                ),
                "elapsed_percent": relative_percent(
                    parley["session_elapsed_seconds"]["median"],
                    python["session_elapsed_seconds"]["median"],
                ),
                "public_check_difference_seconds": round(
                    parley["public_check_seconds"]["median"]
                    - python["public_check_seconds"]["median"], 4
                ),
                "public_build_difference_seconds": round(
                    parley["public_build_seconds"]["median"]
                    - python["public_build_seconds"]["median"], 4
                ),
                "noncheck_difference_seconds": round(
                    parley["noncheck_session_seconds"]["median"]
                    - python["noncheck_session_seconds"]["median"], 4
                ),
            },
            "matched_pairs": {
                "pairs": len(paired),
                "parley_faster": parley_faster,
                "python_faster": python_faster,
                "ties": len(paired) - parley_faster - python_faster,
                "elapsed_difference_seconds": {
                    **summarize(elapsed_differences),
                    "bootstrap_median_95_percent_interval": bootstrap_median_interval(
                        elapsed_differences
                    ),
                },
                "public_check_difference_seconds": summarize([
                    row["public_check_difference_seconds"] for row in paired
                ]),
                "public_build_difference_seconds": summarize([
                    row["public_build_difference_seconds"] for row in paired
                ]),
                "noncheck_difference_seconds": summarize([
                    row["noncheck_difference_seconds"] for row in paired
                ]),
                "total_token_difference": {
                    **summarize(token_differences),
                    "parley_no_higher_pairs": sum(value <= 0 for value in token_differences),
                },
                "two_sided_sign_test_p": sign_test_two_sided(
                    parley_faster, python_faster
                ),
            },
        },
        "interpretation": {
            "frozen_gate_unchanged": True,
            "conclusion": (
                "Parley's marginal median elapsed failure is valid, but it is not a "
                "clean estimate of compiler overhead. Public build/check overhead explains "
                "only part of the marginal gap, while separately scheduled matched cells "
                "show high noncheck variance and no stable directional paired effect."
            ),
            "limitations": (
                "Pairs share task, model configuration, and replicate label but were not "
                "simultaneous controlled executions. This post-result analysis is descriptive "
                "and cannot revise the primary gate or authorize a same-corpus rerun."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + "\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
