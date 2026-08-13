#!/usr/bin/env python3
"""Attribute the frozen iteration-043 Parley/Python elapsed result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any, Callable


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "fullstack_agent_043_raw.json"
AUDIT = BENCHMARKS / "fullstack_agent_043_audit.json"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_043_elapsed_attribution.json"
RAW_SHA256 = "13ab8043bfb973a51d339838a90936b7ec4624fe2d2813e8c297954e958fb021"
AUDIT_SHA256 = "004f0dcf241b36512f327d0d588a569170309fe85097be1d407c9ef9a42411b8"
LANGUAGES = ("parley", "python")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rounded(value: float | int) -> float:
    return round(float(value), 6)


def median(values: list[float | int]) -> float:
    return rounded(statistics.median(values))


def public_seconds(row: dict[str, Any]) -> float:
    return sum(attempt["elapsed_seconds"] for attempt in row["public_attempts"])


def build_seconds(row: dict[str, Any]) -> float:
    return sum(
        attempt["build"]["elapsed_seconds"] for attempt in row["public_attempts"]
    )


def browser_seconds(row: dict[str, Any]) -> float:
    return sum(
        case.get("elapsed_seconds", 0.0)
        for attempt in row["public_attempts"]
        for case in attempt["cases"]
        if case["target"] == "browser"
    )


def cross_target_seconds(row: dict[str, Any]) -> float:
    return sum(
        attempt["cross_target"].get("elapsed_seconds", 0.0)
        for attempt in row["public_attempts"]
    )


MEASURES: dict[str, Callable[[dict[str, Any]], float | int]] = {
    "elapsed_seconds": lambda row: row["elapsed_seconds"],
    "public_check_seconds": public_seconds,
    "build_seconds": build_seconds,
    "browser_seconds": browser_seconds,
    "cross_target_seconds": cross_target_seconds,
    "agent_seconds_excluding_public_check": lambda row: row["elapsed_seconds"]
    - public_seconds(row),
    "elapsed_seconds_excluding_build": lambda row: row["elapsed_seconds"]
    - build_seconds(row),
    "total_tokens": lambda row: row["total_tokens"],
    "output_tokens": lambda row: row["usage"]["output_tokens"],
    "reasoning_output_tokens": lambda row: row["usage"][
        "reasoning_output_tokens"
    ],
    "source_edit_rough_tokens": lambda row: row["source_edits"][
        "rough_token_edit_count"
    ],
    "public_attempts": lambda row: len(row["public_attempts"]),
}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "sessions": len(rows),
        "first_check_successes": sum(row["first_public_check_success"] for row in rows),
        "repair_turns": sum(row["repair_turns"] for row in rows),
    }
    for name, getter in MEASURES.items():
        values = [getter(row) for row in rows]
        result[f"median_{name}"] = median(values)
        if name == "elapsed_seconds":
            result[f"mean_{name}"] = rounded(statistics.mean(values))
    return result


def paired_delta(
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
    getter: Callable[[dict[str, Any]], float | int],
) -> dict[str, Any]:
    differences = [float(getter(parley) - getter(python)) for parley, python in pairs]
    return {
        "pairs": len(differences),
        "median": median(differences),
        "mean": rounded(statistics.mean(differences)),
        "minimum": rounded(min(differences)),
        "maximum": rounded(max(differences)),
        "parley_lower_pairs": sum(value < 0 for value in differences),
        "equal_pairs": sum(value == 0 for value in differences),
        "parley_higher_pairs": sum(value > 0 for value in differences),
    }


def paired_summary(
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
) -> dict[str, Any]:
    return {
        name: paired_delta(pairs, getter) for name, getter in MEASURES.items()
    }


def central_bracket(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row["elapsed_seconds"], row["cell_id"]))
    assert len(ordered) % 2 == 0
    lower = ordered[len(ordered) // 2 - 1]
    upper = ordered[len(ordered) // 2]
    return {
        "lower_cell": lower["cell_id"],
        "lower_seconds": lower["elapsed_seconds"],
        "upper_cell": upper["cell_id"],
        "upper_seconds": upper["elapsed_seconds"],
        "median_seconds": median(
            [lower["elapsed_seconds"], upper["elapsed_seconds"]]
        ),
    }


def analyze() -> dict[str, Any]:
    assert sha256(RAW) == RAW_SHA256
    assert sha256(AUDIT) == AUDIT_SHA256
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    rows = raw["results"]
    assert len(rows) == 96
    assert all(row["hidden_success"] for row in rows)
    assert audit["audit_pass"] is True
    assert audit["primary_gate"]["conditions"]["elapsed"] is False

    selected = {
        language: [row for row in rows if row["language"] == language]
        for language in LANGUAGES
    }
    assert all(len(language_rows) == 24 for language_rows in selected.values())
    pair_key = lambda row: (
        row["task_id"],
        row["configuration_id"],
        int(row["replicate"]),
    )
    indexed = {
        language: {pair_key(row): row for row in selected[language]}
        for language in LANGUAGES
    }
    assert indexed["parley"].keys() == indexed["python"].keys()

    pair_records = [
        (key, indexed["parley"][key], indexed["python"][key])
        for key in sorted(indexed["parley"])
    ]

    def choose(
        predicate: Callable[[tuple[str, str, int], dict[str, Any]], bool]
    ) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        return [
            (parley, python)
            for key, parley, python in pair_records
            if predicate(key, parley)
        ]

    all_pairs = choose(lambda _key, _row: True)
    by_configuration = {
        configuration: paired_summary(
            choose(lambda key, _row, expected=configuration: key[1] == expected)
        )
        for configuration in ("sol-medium", "terra-medium")
    }
    by_kind = {
        kind: paired_summary(
            choose(lambda _key, row, expected=kind: row["task_kind"] == expected)
        )
        for kind in ("implementation", "maintenance")
    }
    terra_by_kind = {
        kind: paired_summary(
            choose(
                lambda key, row, expected=kind: key[1] == "terra-medium"
                and row["task_kind"] == expected
            )
        )
        for kind in ("implementation", "maintenance")
    }
    task_ids = sorted({key[0] for key, _parley, _python in pair_records})
    terra_by_task = {
        task_id: paired_summary(
            choose(
                lambda key, _row, expected=task_id: key[1] == "terra-medium"
                and key[0] == expected
            )
        )
        for task_id in task_ids
    }

    terra_rows = {
        language: [
            row
            for row in selected[language]
            if row["configuration_id"] == "terra-medium"
        ]
        for language in LANGUAGES
    }
    terra_kind_marginals = {
        kind: {
            language: summarize(
                [row for row in terra_rows[language] if row["task_kind"] == kind]
            )
            for language in LANGUAGES
        }
        for kind in ("implementation", "maintenance")
    }
    terra_task_marginals = {
        task_id: {
            language: summarize(
                [row for row in terra_rows[language] if row["task_id"] == task_id]
            )
            for language in LANGUAGES
        }
        for task_id in task_ids
    }

    matched_rows = []
    for key, parley, python in pair_records:
        parley_measures = {name: rounded(getter(parley)) for name, getter in MEASURES.items()}
        python_measures = {name: rounded(getter(python)) for name, getter in MEASURES.items()}
        matched_rows.append(
            {
                "task_id": key[0],
                "task_kind": parley["task_kind"],
                "configuration_id": key[1],
                "replicate": key[2],
                "parley": parley_measures,
                "python": python_measures,
                "parley_minus_python": {
                    name: rounded(parley_measures[name] - python_measures[name])
                    for name in MEASURES
                },
            }
        )

    terra_parley = summarize(terra_rows["parley"])
    terra_python = summarize(terra_rows["python"])
    terra_elapsed_percent = rounded(
        (
            terra_parley["median_elapsed_seconds"]
            / terra_python["median_elapsed_seconds"]
            - 1
        )
        * 100
    )
    return {
        "schema_version": 1,
        "experiment_id": "043-elapsed-attribution",
        "generated_at": raw["generated_at"],
        "raw_sha256": sha256(RAW),
        "audit_sha256": sha256(AUDIT),
        "scope": (
            "Post-study descriptive attribution over all 24 matched Parley/Python "
            "cells and all 12 terra-medium pairs. No row is excluded and the frozen "
            "043 gate is unchanged."
        ),
        "language_elapsed": {
            "overall": {
                language: summarize(selected[language]) for language in LANGUAGES
            },
            "by_configuration": {
                configuration: {
                    language: summarize(
                        [
                            row
                            for row in selected[language]
                            if row["configuration_id"] == configuration
                        ]
                    )
                    for language in LANGUAGES
                }
                for configuration in ("sol-medium", "terra-medium")
            },
            "by_kind": {
                kind: {
                    language: summarize(
                        [row for row in selected[language] if row["task_kind"] == kind]
                    )
                    for language in LANGUAGES
                }
                for kind in ("implementation", "maintenance")
            },
        },
        "paired_parley_minus_python": {
            "overall": paired_summary(all_pairs),
            "by_configuration": by_configuration,
            "by_kind": by_kind,
            "terra_by_kind": terra_by_kind,
            "terra_by_task": terra_by_task,
        },
        "terra_gate_mechanism": {
            "parley_marginal_median_seconds": terra_parley[
                "median_elapsed_seconds"
            ],
            "python_marginal_median_seconds": terra_python[
                "median_elapsed_seconds"
            ],
            "parley_marginal_gap_percent": terra_elapsed_percent,
            "parley_faster_matched_pairs": by_configuration["terra-medium"][
                "elapsed_seconds"
            ]["parley_lower_pairs"],
            "matched_pairs": 12,
            "median_paired_delta_seconds": by_configuration["terra-medium"][
                "elapsed_seconds"
            ]["median"],
            "central_brackets": {
                language: central_bracket(terra_rows[language])
                for language in LANGUAGES
            },
            "by_kind_marginals": terra_kind_marginals,
            "by_task_marginals": terra_task_marginals,
            "interpretation": (
                "The registered gate compares separate language medians, not the "
                "median matched-pair difference. Parley was faster in 5 of 12 Terra "
                "pairs and its median paired delta was positive. The task-kind split "
                "is heterogeneous: Parley has a negative paired median on implementation "
                "cells and a positive paired median on maintenance cells."
            ),
        },
        "build_phase_diagnostic": {
            "overall_paired_build_delta": paired_summary(all_pairs)["build_seconds"],
            "terra_paired_build_delta": by_configuration["terra-medium"][
                "build_seconds"
            ],
            "terra_marginal_medians": {
                language: {
                    "elapsed_seconds": summarize(terra_rows[language])[
                        "median_elapsed_seconds"
                    ],
                    "public_check_seconds": summarize(terra_rows[language])[
                        "median_public_check_seconds"
                    ],
                    "build_seconds": summarize(terra_rows[language])[
                        "median_build_seconds"
                    ],
                    "agent_seconds_excluding_public_check": summarize(
                        terra_rows[language]
                    )["median_agent_seconds_excluding_public_check"],
                    "elapsed_seconds_excluding_build": summarize(
                        terra_rows[language]
                    )["median_elapsed_seconds_excluding_build"],
                }
                for language in LANGUAGES
            },
            "interpretation": (
                "The frozen Parley public build phase was slower than Python in all "
                "24 matched pairs, with a 2.935-second median delta overall and a "
                "3.34245-second median delta under Terra. Subtracting observed build "
                "time makes the Terra Parley marginal median lower, but this is a "
                "component diagnostic, not a measured alternative outcome or gate pass."
            ),
        },
        "matched_pairs": matched_rows,
        "finding": (
            "Parley was faster than Python overall by 1.56685 seconds at the paired "
            "median and in 15/24 matched cells, but under Terra it was faster in only "
            "5/12 pairs and slower by 1.4336 seconds at the paired median. The Terra "
            "miss is concentrated in maintenance, whose paired median is +2.61335 "
            "seconds. The remaining systematic disadvantage is the public build phase: "
            "Parley was slower in 24/24 pairs by 2.935 seconds at the paired median."
        ),
        "claim_boundary": (
            "Iteration 043 remains gate-not-met. Component subtraction does not pass "
            "a gate, and any build-path change requires regression validation outside "
            "the 043 corpus followed by a new disjoint preregistered population."
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
