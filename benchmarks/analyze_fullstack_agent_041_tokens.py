#!/usr/bin/env python3
"""Attribute the frozen iteration-041 Parley/Python token difference."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any, Callable

import tiktoken

try:
    from .run_fullstack_agent_041 import (
        SKILL_PATH,
        WEB_REFERENCE_PATH,
        load_cases,
        load_task_map,
        render_prompt,
    )
except ImportError:
    from run_fullstack_agent_041 import (
        SKILL_PATH,
        WEB_REFERENCE_PATH,
        load_cases,
        load_task_map,
        render_prompt,
    )


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
RAW = BENCHMARKS / "fullstack_agent_041_raw.json"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_041_token_attribution.json"
RAW_SHA256 = "37c27539e9003a7a28bc82b58bdc70fd9f0538a1dd5dc0ab6aa5ff6a6ffff65d"
LANGUAGES = ("parley", "python", "typescript", "rust")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values: list[float | int]) -> float:
    return float(statistics.median(values))


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sessions": len(rows),
        "median_total_tokens": median([row["total_tokens"] for row in rows]),
        "mean_total_tokens": round(statistics.mean(row["total_tokens"] for row in rows), 4),
        "median_input_tokens": median([row["usage"]["input_tokens"] for row in rows]),
        "median_cached_input_tokens": median(
            [row["usage"]["cached_input_tokens"] for row in rows]
        ),
        "median_uncached_input_tokens": median(
            [row["usage"]["uncached_input_tokens"] for row in rows]
        ),
        "median_output_tokens": median([row["usage"]["output_tokens"] for row in rows]),
        "median_reasoning_output_tokens": median(
            [row["usage"]["reasoning_output_tokens"] for row in rows]
        ),
        "median_prompt_chars": median([row["prompt_chars"] for row in rows]),
        "median_agent_message_items": median(
            [len(row["agent_messages"]) for row in rows]
        ),
        "median_source_edit_rough_tokens": median(
            [row["source_edits"]["rough_token_edit_count"] for row in rows]
        ),
    }


def paired_delta(
    parley: dict[tuple[str, str, int], dict[str, Any]],
    python: dict[tuple[str, str, int], dict[str, Any]],
    getter: Callable[[dict[str, Any]], float | int],
) -> dict[str, Any]:
    differences = [float(getter(parley[key]) - getter(python[key])) for key in parley]
    return {
        "median": median(differences),
        "mean": round(statistics.mean(differences), 4),
        "minimum": min(differences),
        "maximum": max(differences),
        "parley_lower_pairs": sum(value < 0 for value in differences),
        "equal_pairs": sum(value == 0 for value in differences),
        "parley_higher_pairs": sum(value > 0 for value in differences),
    }


def analyze() -> dict[str, Any]:
    assert sha256(RAW) == RAW_SHA256
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    rows = raw["results"]
    assert len(rows) == 96
    assert all(row["hidden_success"] for row in rows)
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
    paired = {
        language: {pair_key(row): row for row in selected[language]}
        for language in ("parley", "python")
    }
    assert paired["parley"].keys() == paired["python"].keys()

    tasks = load_task_map()
    cases = load_cases()
    skill = SKILL_PATH.read_text(encoding="utf-8")
    web_reference = WEB_REFERENCE_PATH.read_text(encoding="utf-8")
    encoder = tiktoken.get_encoding("o200k_base")
    prompt_deltas = []
    for task_id, task in tasks.items():
        parley_prompt = render_prompt(
            task, cases[task_id], "parley", skill, web_reference
        )
        python_prompt = render_prompt(
            task, cases[task_id], "python", skill, web_reference
        )
        prompt_deltas.append(
            {
                "task_id": task_id,
                "characters": len(parley_prompt) - len(python_prompt),
                "o200k_tokens": len(encoder.encode(parley_prompt))
                - len(encoder.encode(python_prompt)),
            }
        )
    assert {row["characters"] for row in prompt_deltas} == {4270}
    assert {row["o200k_tokens"] for row in prompt_deltas} == {1154}
    extra_prompt_tokens = prompt_deltas[0]["o200k_tokens"]

    parley_rows = selected["parley"]
    python_median = median([row["total_tokens"] for row in selected["python"]])
    three_call_counterfactual = median(
        [row["total_tokens"] - 3 * extra_prompt_tokens for row in parley_rows]
    )
    message_proxy_counterfactual = median(
        [
            row["total_tokens"]
            - len(row["agent_messages"]) * extra_prompt_tokens
            for row in parley_rows
        ]
    )

    pair_rows = []
    for key in sorted(paired["parley"]):
        parley_row = paired["parley"][key]
        python_row = paired["python"][key]
        pair_rows.append(
            {
                "task_id": key[0],
                "configuration_id": key[1],
                "replicate": key[2],
                "parley_total_tokens": parley_row["total_tokens"],
                "python_total_tokens": python_row["total_tokens"],
                "total_token_delta": parley_row["total_tokens"]
                - python_row["total_tokens"],
                "input_token_delta": parley_row["usage"]["input_tokens"]
                - python_row["usage"]["input_tokens"],
                "output_token_delta": parley_row["usage"]["output_tokens"]
                - python_row["usage"]["output_tokens"],
                "reasoning_output_token_delta": parley_row["usage"][
                    "reasoning_output_tokens"
                ]
                - python_row["usage"]["reasoning_output_tokens"],
                "source_edit_rough_token_delta": parley_row["source_edits"][
                    "rough_token_edit_count"
                ]
                - python_row["source_edits"]["rough_token_edit_count"],
                "parley_agent_message_items": len(parley_row["agent_messages"]),
                "python_agent_message_items": len(python_row["agent_messages"]),
            }
        )

    aggregate_gap = summarize(selected["parley"])["median_total_tokens"] - python_median
    return {
        "schema_version": 1,
        "experiment_id": "041-token-attribution",
        "generated_at": raw["generated_at"],
        "raw_sha256": sha256(RAW),
        "scope": (
            "Post-study descriptive attribution over all 24 matched Parley/Python "
            "cells. It does not alter the frozen 041 gate or authorize a rerun."
        ),
        "language_usage": {
            language: summarize(selected[language]) for language in LANGUAGES
        },
        "paired_parley_minus_python": {
            "total_tokens": paired_delta(
                paired["parley"], paired["python"], lambda row: row["total_tokens"]
            ),
            "input_tokens": paired_delta(
                paired["parley"],
                paired["python"],
                lambda row: row["usage"]["input_tokens"],
            ),
            "cached_input_tokens": paired_delta(
                paired["parley"],
                paired["python"],
                lambda row: row["usage"]["cached_input_tokens"],
            ),
            "uncached_input_tokens": paired_delta(
                paired["parley"],
                paired["python"],
                lambda row: row["usage"]["uncached_input_tokens"],
            ),
            "output_tokens": paired_delta(
                paired["parley"],
                paired["python"],
                lambda row: row["usage"]["output_tokens"],
            ),
            "reasoning_output_tokens": paired_delta(
                paired["parley"],
                paired["python"],
                lambda row: row["usage"]["reasoning_output_tokens"],
            ),
            "prompt_characters": paired_delta(
                paired["parley"], paired["python"], lambda row: row["prompt_chars"]
            ),
            "source_edit_rough_tokens": paired_delta(
                paired["parley"],
                paired["python"],
                lambda row: row["source_edits"]["rough_token_edit_count"],
            ),
        },
        "frozen_prompt_difference": {
            "core_file": str(SKILL_PATH.relative_to(REPO)),
            "core_sha256": sha256(SKILL_PATH),
            "web_file": str(WEB_REFERENCE_PATH.relative_to(REPO)),
            "web_sha256": sha256(WEB_REFERENCE_PATH),
            "combined_context_bytes": len(skill.encode())
            + len(web_reference.encode()),
            "combined_context_o200k_tokens": len(encoder.encode(skill))
            + len(encoder.encode(web_reference)),
            "task_prompt_deltas": prompt_deltas,
            "constant_extra_prompt_characters": 4270,
            "constant_extra_prompt_o200k_tokens": extra_prompt_tokens,
        },
        "counterfactual_diagnostic": {
            "observed_parley_median_total_tokens": summarize(selected["parley"])[
                "median_total_tokens"
            ],
            "observed_python_median_total_tokens": python_median,
            "observed_aggregate_median_gap_tokens": aggregate_gap,
            "three_prompt_repetitions_removed_parley_median": three_call_counterfactual,
            "three_prompt_repetitions_removed_gap_percent": round(
                (three_call_counterfactual / python_median - 1.0) * 100.0, 4
            ),
            "agent_message_item_proxy_removed_parley_median": message_proxy_counterfactual,
            "agent_message_item_proxy_removed_gap_percent": round(
                (message_proxy_counterfactual / python_median - 1.0) * 100.0, 4
            ),
            "interpretation": (
                "These arithmetic scenarios assume the fixed rendered prompt delta is "
                "billed again at each model interaction. They identify a plausible "
                "context target but are not measured alternative outcomes."
            ),
        },
        "matched_pairs": pair_rows,
        "finding": (
            "The median paired input delta (+3,309 tokens) dominates the median "
            "paired total delta (+3,028.5), while Parley uses 254 fewer output "
            "tokens and 73.5 fewer rough edit tokens. The constant 1,154-token "
            "rendered prompt delta is therefore the highest-priority generic target."
        ),
        "claim_boundary": (
            "Iteration 041 remains gate-not-met. No counterfactual passes a gate, and "
            "any compressed context requires independent reliability validation on a "
            "new population before comparative measurement."
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
