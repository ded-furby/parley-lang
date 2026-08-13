#!/usr/bin/env python3
"""Recompute the post-result token and latency attribution for study 047."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
from typing import Any, Callable

try:
    from .run_fullstack_agent_047 import (
        CONTEXT_PATH,
        O200K,
        load_cases,
        load_task_map,
        render_prompt,
    )
except ImportError:
    from run_fullstack_agent_047 import (
        CONTEXT_PATH,
        O200K,
        load_cases,
        load_task_map,
        render_prompt,
    )


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "fullstack_agent_047_raw.json"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_047_attribution.json"
RAW_SHA256 = "f04515b84abfbb2a3fe0477c7d0d5c5de9eba8a6f4de3eba2cf062886e779d28"
LANGUAGES = ("parley", "python", "typescript", "rust")
BOOTSTRAP_SEED = 470260814
BOOTSTRAP_SAMPLES = 50_000


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values: list[float | int]) -> float:
    return float(statistics.median(values))


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


def summarize(values: list[float | int]) -> dict[str, float]:
    ordered = sorted(float(value) for value in values)
    return {
        "median": round(median(ordered), 4),
        "mean": round(statistics.mean(ordered), 4),
        "minimum": round(ordered[0], 4),
        "maximum": round(ordered[-1], 4),
    }


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sessions": len(rows),
        "total_tokens": summarize([row["total_tokens"] for row in rows]),
        "input_tokens": summarize([row["usage"]["input_tokens"] for row in rows]),
        "cached_input_tokens": summarize(
            [row["usage"]["cached_input_tokens"] for row in rows]
        ),
        "uncached_input_tokens": summarize(
            [row["usage"]["uncached_input_tokens"] for row in rows]
        ),
        "output_tokens": summarize([row["usage"]["output_tokens"] for row in rows]),
        "reasoning_output_tokens": summarize(
            [row["usage"]["reasoning_output_tokens"] for row in rows]
        ),
        "prompt_characters": summarize([row["prompt_chars"] for row in rows]),
        "source_edit_rough_tokens": summarize(
            [row["source_edits"]["rough_token_edit_count"] for row in rows]
        ),
        "agent_message_items": summarize(
            [len(row["agent_messages"]) for row in rows]
        ),
        "public_check_attempts": summarize(
            [row["public_check_attempts"] for row in rows]
        ),
        "session_elapsed_seconds": summarize(
            [row["elapsed_seconds"] for row in rows]
        ),
        "public_check_seconds": summarize(
            [public_check_seconds(row) for row in rows]
        ),
        "public_build_seconds": summarize(
            [public_build_seconds(row) for row in rows]
        ),
        "public_runtime_seconds": summarize(
            [public_runtime_seconds(row) for row in rows]
        ),
        "noncheck_session_seconds": summarize(
            [noncheck_seconds(row) for row in rows]
        ),
    }


def paired_summary(
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
    getter: Callable[[dict[str, Any]], float | int],
) -> dict[str, Any]:
    differences = [float(getter(parley) - getter(python)) for parley, python in pairs]
    return {
        **summarize(differences),
        "parley_lower_pairs": sum(value < 0 for value in differences),
        "equal_pairs": sum(value == 0 for value in differences),
        "parley_higher_pairs": sum(value > 0 for value in differences),
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


def sign_test_two_sided(lower: int, higher: int) -> float:
    count = lower + higher
    tail = min(lower, higher)
    probability = sum(math.comb(count, index) for index in range(tail + 1)) / 2**count
    return round(min(2 * probability, 1.0), 6)


def relative_percent(value: float, baseline: float) -> float:
    return round((value / baseline - 1.0) * 100.0, 4)


def build() -> dict[str, Any]:
    assert digest(RAW) == RAW_SHA256
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    rows = raw["results"]
    assert len(rows) == 32
    assert all(row["hidden_success"] for row in rows)
    assert raw["summary"]["primary_gate"]["conditions"] == {
        "execution_integrity": True,
        "correctness": True,
        "first_check": True,
        "tokens": False,
        "elapsed": False,
        "maintainability": True,
    }

    selected = {
        language: [row for row in rows if row["language"] == language]
        for language in LANGUAGES
    }
    assert all(len(language_rows) == 8 for language_rows in selected.values())
    index = {
        (row["task_id"], row["configuration_id"], row["replicate"], row["language"]): row
        for row in rows
    }
    pairs = []
    for key, parley in index.items():
        if key[-1] == "parley":
            pairs.append((parley, index[(*key[:3], "python")]))
    pairs.sort(key=lambda pair: (
        pair[0]["task_id"], pair[0]["configuration_id"], pair[0]["replicate"]
    ))
    assert len(pairs) == 8

    context = CONTEXT_PATH.read_text(encoding="utf-8")
    task_map = load_task_map()
    cases = load_cases()
    prompt_deltas = []
    for task_id, task in task_map.items():
        parley_prompt = render_prompt(task, cases[task_id], "parley", context)
        python_prompt = render_prompt(task, cases[task_id], "python", context)
        prompt_deltas.append({
            "task_id": task_id,
            "characters": len(parley_prompt) - len(python_prompt),
            "o200k_tokens": len(O200K.encode(parley_prompt))
            - len(O200K.encode(python_prompt)),
        })
    assert {row["characters"] for row in prompt_deltas} == {663}
    assert {row["o200k_tokens"] for row in prompt_deltas} == {161}

    getters: dict[str, Callable[[dict[str, Any]], float | int]] = {
        "total_tokens": lambda row: row["total_tokens"],
        "input_tokens": lambda row: row["usage"]["input_tokens"],
        "cached_input_tokens": lambda row: row["usage"]["cached_input_tokens"],
        "uncached_input_tokens": lambda row: row["usage"]["uncached_input_tokens"],
        "output_tokens": lambda row: row["usage"]["output_tokens"],
        "reasoning_output_tokens": lambda row: row["usage"]["reasoning_output_tokens"],
        "prompt_characters": lambda row: row["prompt_chars"],
        "source_edit_rough_tokens": (
            lambda row: row["source_edits"]["rough_token_edit_count"]
        ),
        "session_elapsed_seconds": lambda row: row["elapsed_seconds"],
        "public_check_seconds": public_check_seconds,
        "public_build_seconds": public_build_seconds,
        "public_runtime_seconds": public_runtime_seconds,
        "noncheck_session_seconds": noncheck_seconds,
    }
    paired = {name: paired_summary(pairs, getter) for name, getter in getters.items()}
    elapsed_differences = [
        float(parley["elapsed_seconds"]) - float(python["elapsed_seconds"])
        for parley, python in pairs
    ]
    total_differences = [
        float(parley["total_tokens"] - python["total_tokens"])
        for parley, python in pairs
    ]
    paired["session_elapsed_seconds"]["bootstrap_median_95_percent_interval"] = (
        bootstrap_median_interval(elapsed_differences)
    )
    paired["session_elapsed_seconds"]["two_sided_sign_test_p"] = sign_test_two_sided(
        paired["session_elapsed_seconds"]["parley_lower_pairs"],
        paired["session_elapsed_seconds"]["parley_higher_pairs"],
    )
    paired["total_tokens"]["bootstrap_median_95_percent_interval"] = (
        bootstrap_median_interval(total_differences)
    )
    paired["total_tokens"]["two_sided_sign_test_p"] = sign_test_two_sided(
        paired["total_tokens"]["parley_lower_pairs"],
        paired["total_tokens"]["parley_higher_pairs"],
    )

    pair_rows = []
    for parley, python in pairs:
        pair_rows.append({
            "task_id": parley["task_id"],
            "configuration_id": parley["configuration_id"],
            "replicate": parley["replicate"],
            "parley_public_check_attempts": parley["public_check_attempts"],
            "python_public_check_attempts": python["public_check_attempts"],
            **{
                f"{name}_difference": round(float(getter(parley) - getter(python)), 4)
                for name, getter in getters.items()
            },
        })

    extra_check_pairs = [
        pair for pair in pairs
        if pair[0]["public_check_attempts"] > 1 or pair[1]["public_check_attempts"] > 1
    ]
    assert len(extra_check_pairs) == 1
    retained_pairs = [pair for pair in pairs if pair not in extra_check_pairs]
    sensitivity = {}
    for language_index, language in enumerate(("parley", "python")):
        language_rows = [pair[language_index] for pair in retained_pairs]
        sensitivity[language] = {
            "sessions": len(language_rows),
            "median_total_tokens": median([row["total_tokens"] for row in language_rows]),
            "median_elapsed_seconds": median(
                [row["elapsed_seconds"] for row in language_rows]
            ),
        }

    by_language = {
        language: summarize_rows(selected[language]) for language in LANGUAGES
    }
    parley = by_language["parley"]
    python = by_language["python"]
    parley_rows = selected["parley"]
    python_rows = selected["python"]
    parley_elapsed_median = median([row["elapsed_seconds"] for row in parley_rows])
    python_elapsed_median = median([row["elapsed_seconds"] for row in python_rows])
    return {
        "schema_version": 1,
        "experiment_id": "047",
        "phase": "post-result secondary token and latency attribution",
        "generated_at": raw["generated_at"],
        "raw_sha256": RAW_SHA256,
        "bootstrap": {
            "seed": BOOTSTRAP_SEED,
            "samples": BOOTSTRAP_SAMPLES,
            "unit": "matched task/configuration/replicate pair",
        },
        "definitions": {
            "complete_session_tokens": "Frozen input plus output token total.",
            "session_elapsed_seconds": (
                "Frozen wall time around the complete Codex subprocess and all parent "
                "public checks requested during it; hidden judgment is excluded."
            ),
            "public_check_seconds": "Sum of parent-recorded ./check attempt wall times.",
            "public_build_seconds": (
                "Sum of exact application build wall times inside public checks."
            ),
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
        "frozen_prompt_difference": {
            "context_file": str(CONTEXT_PATH.relative_to(REPO)),
            "context_sha256": digest(CONTEXT_PATH),
            "context_bytes": len(context.encode()),
            "context_o200k_tokens": len(O200K.encode(context)),
            "task_prompt_deltas": prompt_deltas,
            "constant_extra_prompt_characters": 663,
            "constant_extra_prompt_o200k_tokens": 161,
        },
        "parley_vs_python": {
            "marginal_median": {
                "total_token_difference": round(
                    parley["total_tokens"]["median"]
                    - python["total_tokens"]["median"], 4
                ),
                "total_token_percent": relative_percent(
                    parley["total_tokens"]["median"],
                    python["total_tokens"]["median"],
                ),
                "elapsed_difference_seconds": round(
                    parley_elapsed_median - python_elapsed_median, 4
                ),
                "elapsed_percent": relative_percent(
                    parley_elapsed_median,
                    python_elapsed_median,
                ),
                "public_check_difference_seconds": round(
                    median([public_check_seconds(row) for row in parley_rows])
                    - median([public_check_seconds(row) for row in python_rows]), 4
                ),
                "public_build_difference_seconds": round(
                    median([public_build_seconds(row) for row in parley_rows])
                    - median([public_build_seconds(row) for row in python_rows]), 4
                ),
                "noncheck_difference_seconds": round(
                    median([noncheck_seconds(row) for row in parley_rows])
                    - median([noncheck_seconds(row) for row in python_rows]), 4
                ),
            },
            "matched_pairs": paired,
        },
        "redundant_check_sensitivity_outside_gate": {
            "excluded_pair": {
                "task_id": extra_check_pairs[0][0]["task_id"],
                "configuration_id": extra_check_pairs[0][0]["configuration_id"],
                "replicate": extra_check_pairs[0][0]["replicate"],
                "parley_public_check_attempts": extra_check_pairs[0][0][
                    "public_check_attempts"
                ],
                "python_public_check_attempts": extra_check_pairs[0][1][
                    "public_check_attempts"
                ],
                "all_attempts_succeeded": all(
                    attempt["ok"] for row in extra_check_pairs[0]
                    for attempt in row["public_attempts"]
                ),
            },
            "retained_matched_pairs": len(retained_pairs),
            "by_language": sensitivity,
            "interpretation": (
                "This exclusion is descriptive sensitivity only. The frozen primary "
                "result retains the cell and remains failed."
            ),
        },
        "matched_pair_rows": pair_rows,
        "finding": (
            "The eight matched pairs have a +384.5-token Parley median: +142.5 input "
            "tokens and +214 output tokens. Parley is lower in three total-token pairs "
            "and higher in five; its reasoning-output count is higher in all eight. "
            "The fixed rendered prompt delta is only 161 tokens. One successful cell "
            "made three redundant checks and is an extreme token/time outlier, but it "
            "remains part of the valid gate. The evidence does not isolate a generic "
            "language defect that would justify syntax or semantic tuning."
        ),
        "next_action": (
            "Preserve v0.5.7 and the compact context. Improve broadly useful product "
            "coverage independently, then use a larger disjoint evaluation to distinguish "
            "small token effects from interaction variance. Treat the stable roughly "
            "one-second public-build gap as a separate compiler-cost target."
        ),
        "claim_boundary": (
            "This descriptive analysis does not revise the frozen 047 gate, exclude a "
            "cell, authorize a same-corpus rerun, or establish universal superiority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
