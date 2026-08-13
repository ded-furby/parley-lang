#!/usr/bin/env python3
"""Build the canonical technical report artifact for agent study 044."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "fullstack_agent_044_raw.json"
PROTOCOL = BENCHMARKS / "fullstack_agent_044_protocol.json"
VALIDATION = BENCHMARKS / "fullstack_agent_044_validation.json"
AUDIT = BENCHMARKS / "fullstack_agent_044_audit.json"
SQL = REPORTS / "044-independent-fullstack-study-gate-passed.sql"
OUTPUT = REPORTS / "044-independent-fullstack-study-gate-passed.artifact.json"
RAW_SHA = "76512be28a1d0052c98aa4f601f4945b92423777a5a8560bba0a0c7afcef3399"
PROTOCOL_SHA = "b5d40db4de13e96fc5f93bdf9f916e86a4f4438e4e7328b47b6cd711525feb38"
VALIDATION_SHA = "4f5c4474d7b82fb5e13cd529c573a9c1a5dac42856fdf5f0dfc2e625a297e1ad"
AUDIT_SHA = "a9f875c07f95333eeb3436de374bfe3b321480081625e311eeac950580f50c54"
MEASUREMENT_COMMIT = "ecdbf5198ef9aad24408b0c2f86dfdb03981d62b"
SOURCE_ID = "fullstack_agent_evidence_044"
TITLE = "Independent Full-Stack Agent Study — Iteration 044"
LABELS = {
    "parley": "Parley",
    "python": "Python",
    "typescript": "TypeScript",
    "rust": "Rust",
}


def _helpers():
    path = REPORTS / "build_037_report.py"
    spec = importlib.util.spec_from_file_location("build_037_report_helpers_044", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load report helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCE_ID = SOURCE_ID
    return module


HELPERS = _helpers()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(raw: dict[str, Any], audit: dict[str, Any]) -> None:
    assert sha256(RAW) == RAW_SHA
    assert sha256(PROTOCOL) == PROTOCOL_SHA
    assert sha256(VALIDATION) == VALIDATION_SHA
    assert sha256(AUDIT) == AUDIT_SHA
    assert raw["experiment_id"] == audit["experiment_id"] == "044"
    assert raw["protocol_sha256"] == PROTOCOL_SHA
    assert raw["repository"]["commit"] == MEASUREMENT_COMMIT
    assert raw["repository"] == raw["repository_after"]
    assert audit["audit_pass"] is True
    assert audit["external_evidence_verified"] is True
    assert audit["matrix"] == {
        "cells": 96,
        "unique_cell_ids": 96,
        "unique_thread_ids": 96,
        "journal_pairs_verified": 96,
        "cleanup_records_verified": 96,
        "attempt_files_verified": 97,
    }
    assert audit["primary_gate"] == raw["summary"]["primary_gate"]
    assert audit["primary_gate"] == {
        "conditions": {
            "execution_integrity": True,
            "correctness": True,
            "first_check": True,
            "tokens": True,
            "elapsed": True,
            "maintainability": True,
        },
        "passed": True,
    }


def source_record(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": SOURCE_ID,
        "label": "Complete frozen iteration 044 result, protocol, and independent audit",
        "path": "benchmarks/fullstack_agent_044_raw.json",
        "query": {
            "engine": "Python 3.14 and SQLite JSON1",
            "language": "SQL and Python",
            "sql": SQL.read_text(encoding="utf-8"),
            "description": (
                "Deterministic extraction and independent recomputation of every "
                "language, model, task-kind, gate, semantic, exact-build, scratch, "
                "source, token, and elapsed summary from all 96 frozen cells."
            ),
            "executed_at": raw["generated_at"],
            "tables_used": [
                "benchmarks/fullstack_agent_044_raw.json",
                "benchmarks/fullstack_agent_044_protocol.json",
                "benchmarks/fullstack_agent_044_validation.json",
                "benchmarks/fullstack_agent_044_audit.json",
            ],
            "filters": [
                "All 96 frozen cells; no exclusions, selective reruns, or model-selected subsets.",
                "Four tasks, four languages, two model configurations, three replicates.",
                "Every public attempt and hidden judgment retained; one Python cell repaired after its first public check.",
                "Complete token and elapsed medians use all 24 rows per language.",
            ],
            "metric_definitions": [
                "Hidden success: all five withheld HTTP/browser cases plus derived cross-target agreement pass.",
                "First check: the first parent-owned public build and all four HTTP/browser cases pass.",
                "Complete session tokens: Codex input plus output tokens; lower is better.",
                "Elapsed seconds: whole fresh-session wall time excluding dependency preparation; lower is better.",
                "Exact root: a hidden-correct maintenance result changes exactly its preregistered defect-root set.",
                "Source tokens: o200k_base tokens in final editable application files; secondary only.",
                "Strict gate: all six preregistered conditions must pass; all six passed in 044.",
            ],
        },
    }


def language_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "language": label,
            **audit["by_language"][language],
            "median_final_bytes": audit["median_final_source"][language]["bytes"],
            "median_final_lines": audit["median_final_source"][language]["lines"],
            "median_final_o200k_tokens": audit["median_final_source"][language][
                "o200k_base_tokens"
            ],
        }
        for language, label in LABELS.items()
    ]


def configuration_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "configuration": configuration,
            "language": LABELS[language],
            **audit["by_configuration"][configuration][language],
        }
        for configuration in ("sol-medium", "terra-medium")
        for language in LABELS
    ]


def configuration_efficiency_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "model_language": f"{configuration} · {LABELS[language]}",
            "configuration": configuration,
            "language": LABELS[language],
            "median_total_tokens": audit["by_configuration"][configuration][language][
                "median_total_tokens"
            ],
            "median_elapsed_seconds": audit["by_configuration"][configuration][language][
                "median_elapsed_seconds"
            ],
        }
        for configuration in ("sol-medium", "terra-medium")
        for language in ("parley", "python")
    ]


def gate_rows() -> list[dict[str, Any]]:
    return [
        {"order": 1, "condition": "Execution integrity", "threshold": "96 unique once-run cells, complete external evidence, stable protected inputs, passing capacity checks, and evidence-gated cleanup", "observed": "96 unique cells and threads; 96 journal/cleanup triples; 97 attempts; 290 exact-build hashes; 93 capacity checks; zero cleanup failures", "result": "PASS"},
        {"order": 2, "condition": "Hidden correctness", "threshold": "Parley 100% and no lower than every baseline overall, by model, and by kind", "observed": "Parley, Python, TypeScript, and Rust each passed 24/24 assignments and all 480 hidden cases", "result": "PASS"},
        {"order": 3, "condition": "First public check", "threshold": "Parley no lower than the best baseline overall and by task kind", "observed": "Parley, TypeScript, and Rust passed 24/24; Python passed 23/24 and repaired one cell on its second attempt", "result": "PASS"},
        {"order": 4, "condition": "Complete session tokens", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "Parley 60,103.5 versus Python 60,715.0 overall (1.0072% lower); Parley was also lower under sol-medium and terra-medium", "result": "PASS"},
        {"order": 5, "condition": "Elapsed time", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "Parley 23.4006 s versus Python 26.75695 s overall (12.5438% lower); Parley was also lower under sol-medium and terra-medium", "result": "PASS"},
        {"order": 6, "condition": "Maintainability", "threshold": "Every hidden-correct Parley repair has exact root; rate no lower than baselines", "observed": "Every language passed 12/12 hidden-correct maintenance roots; Parley changed only logic.par", "result": "PASS"},
    ]


def integrity_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    values = [
        ("Frozen matrix", "96/96 unique cells and unique completed threads", "PASS"),
        ("External journals", "96/96 start/finish pairs hash-verified", "PASS"),
        ("External cleanup evidence", "96/96 records hash-verified; all removed", "PASS"),
        ("External public attempts", "97/97 files hash-verified", "PASS"),
        ("Command and agent protocol", "96/96 compliant; no timeout, agent error, or nonzero exit", "PASS"),
        ("Protected/read-only state", "96/96 final workspaces and 290/290 exact-build boundaries stable", "PASS"),
        ("Public HTTP/browser execution", "388 named cases, 97 Chromium cases, and 97 agreement checks", "PASS"),
        ("Hidden HTTP/browser execution", "480/480 named cases, 192 Chromium cases, and 96 agreement checks", "PASS"),
        ("Scratch capacity", f"{audit['scratch']['capacity_checks']} passing checks; minimum {audit['scratch']['minimum_free_bytes']:,} bytes free", "PASS"),
        ("Bounded cleanup", f"Peak cell {audit['scratch']['peak_cell_workspace_bytes']:,} bytes; zero retained bytes", "PASS"),
        ("Repository and provenance", f"Measurement commit {MEASUREMENT_COMMIT[:7]}; pre/post state identical", "PASS"),
    ]
    return [
        {"order": index, "check": check, "observed": observed, "status": status}
        for index, (check, observed, status) in enumerate(values, 1)
    ]


def scratch_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    scratch = audit["scratch"]
    return [
        {"order": 1, "measure": "Frozen required free space", "bytes": 17179869184, "status": "PASS"},
        {"order": 2, "measure": "Minimum observed free space", "bytes": scratch["minimum_free_bytes"], "status": "PASS"},
        {"order": 3, "measure": "Final observed free space", "bytes": scratch["final_free_bytes"], "status": "PASS"},
        {"order": 4, "measure": "Largest measured cell workspace", "bytes": scratch["peak_cell_workspace_bytes"], "status": "PASS"},
        {"order": 5, "measure": "Retained disposable workspace after cleanup", "bytes": scratch["retained_workspace_bytes_after_cleanup"], "status": "PASS"},
    ]


def chart(*args: Any) -> dict[str, Any]:
    return HELPERS.chart(*args)


def configuration_elapsed_chart() -> dict[str, Any]:
    result = chart(
        "configuration_elapsed_chart",
        "Parley–Python elapsed time by model",
        "Twelve sessions per model/language cell; lower is better.",
        "median_elapsed_seconds",
        "Median seconds",
        "number",
        "Did Parley meet the elapsed threshold within both frozen models?",
        "The four bars show that the elapsed threshold passed under both frozen model configurations.",
        "seconds per model/language median",
        "ascending",
    )
    result["dataset"] = "configuration_efficiency"
    result["encodings"]["x"] = {
        "field": "model_language",
        "type": "nominal",
        "label": "Model and language",
    }
    result["encodings"]["tooltip"] = [
        {"field": "configuration", "type": "nominal", "label": "Model"},
        {"field": "language", "type": "nominal", "label": "Language"},
        {
            "field": "median_total_tokens",
            "type": "quantitative",
            "label": "Median tokens",
        },
    ]
    result["xAxisTitle"] = "Model and language"
    result["comparisonContext"] = {
        "unit": "seconds per model/language median",
        "grain": "model/language summary across 12 frozen sessions",
        "denominator": "all 12 sessions per model/language cell; no exclusions",
        "semanticFamily": "fresh-agent full-stack comparison",
    }
    return result


def table(
    table_id: str,
    title: str,
    subtitle: str,
    dataset: str,
    columns: list[dict[str, Any]],
    sort_field: str,
) -> dict[str, Any]:
    return HELPERS.table(table_id, title, subtitle, dataset, columns, sort_field)


def build(raw: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    source = source_record(raw)
    datasets = {
        "headline": [{
            "conditions_passed": 6,
            "conditions_total": 6,
            "hidden_assignments_passed": 96,
            "hidden_assignments_total": 96,
            "parley_first_checks": 24,
            "parley_first_check_total": 24,
            "token_advantage_percent": -audit["comparisons"]["parley_tokens_vs_python_percent"],
            "overall_elapsed_advantage_percent": -audit["comparisons"]["parley_elapsed_vs_python_percent"],
            "terra_elapsed_advantage_percent": round(
                (1 - audit["by_configuration"]["terra-medium"]["parley"]["median_elapsed_seconds"]
                    / audit["by_configuration"]["terra-medium"]["python"]["median_elapsed_seconds"])
                * 100, 4),
        }],
        "languages": language_rows(audit),
        "configurations": configuration_rows(audit),
        "configuration_efficiency": configuration_efficiency_rows(audit),
        "gates": gate_rows(),
        "integrity": integrity_rows(audit),
        "scratch": scratch_rows(audit),
    }
    cards = [
        {"id": "gate_card", "description": "The clean run passed the complete preregistered six-condition gate.", "dataset": "headline", "metrics": [{"field": "conditions_passed", "label": "Conditions passed", "format": "number", "unit": "of 6"}, {"field": "conditions_total", "label": "Required", "format": "number", "unit": "conditions"}], "sourceId": SOURCE_ID},
        {"id": "correctness_card", "description": "Every frozen assignment passed complete hidden judgment.", "dataset": "headline", "metrics": [{"field": "hidden_assignments_passed", "label": "Hidden assignments", "format": "number", "unit": "of 96"}, {"field": "hidden_assignments_total", "label": "Frozen", "format": "number", "unit": "assignments"}], "sourceId": SOURCE_ID},
        {"id": "first_card", "description": "Every Parley assignment passed its first public check.", "dataset": "headline", "metrics": [{"field": "parley_first_checks", "label": "Parley first checks", "format": "number", "unit": "of 24"}, {"field": "parley_first_check_total", "label": "Parley sessions", "format": "number", "unit": "total"}], "sourceId": SOURCE_ID},
        {"id": "efficiency_card", "description": "Parley used fewer complete-session tokens and was faster overall and within both models.", "dataset": "headline", "metrics": [{"field": "token_advantage_percent", "label": "Token advantage vs Python", "format": "number", "unit": "%"}, {"field": "overall_elapsed_advantage_percent", "label": "Overall elapsed advantage", "format": "number", "unit": "%"}, {"field": "terra_elapsed_advantage_percent", "label": "Terra elapsed advantage", "format": "number", "unit": "%"}], "sourceId": SOURCE_ID},
    ]
    charts = [
        chart("correctness_chart", "Hidden assignment success rate", "Complete withheld HTTP/browser judgment; 24 sessions per language.", "hidden_success_rate", "Hidden success", "percent", "Did every arm satisfy the hidden contract?", "A direct categorical comparison shows the four-way correctness tie.", "fraction of 24 sessions", "descending"),
        chart("first_check_chart", "First public check success rate", "First parent-owned HTTP/browser attempt; higher is better.", "first_check_success_rate", "First-check rate", "percent", "Did Parley match the strongest first-pass arm?", "Parley, TypeScript, and Rust passed 24/24; Python passed 23/24.", "fraction of 24 sessions", "descending"),
        chart("tokens_chart", "Median complete session tokens", "Codex input plus output across all 24 sessions per language; lower is better.", "median_total_tokens", "Median tokens", "compact", "Did Parley match the lowest complete-session token baseline?", "A sorted magnitude chart shows the repeated clean complete-session token win over every baseline.", "input plus output tokens per session", "ascending"),
        chart("elapsed_chart", "Median fresh-session elapsed time", "Whole session wall time across all 24 sessions; lower is better.", "median_elapsed_seconds", "Median seconds", "number", "Was Parley fastest at the overall language level?", "The sorted comparison shows Parley fastest overall; the model-stratified chart confirms both model thresholds passed.", "seconds per session", "ascending"),
        configuration_elapsed_chart(),
        chart("source_chart", "Median final editable-source tokens", "o200k_base count over final editable application files; secondary metric.", "median_final_o200k_tokens", "Median source tokens", "number", "Did compact representation persist in final applications?", "This chart separates source compactness from complete agent-session cost.", "o200k_base tokens per final source", "ascending"),
    ]
    tables = [
        table("gate_table", "Frozen six-condition gate", "Every preregistered condition passed.", "gates", [{"field": "order", "label": "#", "format": "number"}, {"field": "condition", "label": "Condition", "type": "text"}, {"field": "threshold", "label": "Frozen threshold", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "result", "label": "Result", "type": "text"}], "order"),
        table("language_table", "Complete language-level audit", "All 24 sessions per language, with no exclusions.", "languages", [{"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "median_final_o200k_tokens", "label": "Median source", "format": "number"}, {"field": "exact_root_successes", "label": "Exact roots", "format": "number"}, {"field": "repair_turns", "label": "Repair turns", "format": "number"}], "language"),
        table("configuration_table", "Model-stratified result", "Twelve sessions per model/language cell.", "configurations", [{"field": "configuration", "label": "Configuration", "type": "text"}, {"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "exact_root_rate", "label": "Exact-root rate", "format": "percent"}], "configuration"),
        table("integrity_table", "Execution and evidence audit", "Every frozen execution-integrity control passed.", "integrity", [{"field": "order", "label": "#", "format": "number"}, {"field": "check", "label": "Check", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "status", "label": "Status", "type": "text"}], "order"),
        table("scratch_table", "Scratch capacity and cleanup", "Durable evidence stayed outside disposable per-cell workspaces.", "scratch", [{"field": "order", "label": "#", "format": "number"}, {"field": "measure", "label": "Measure", "type": "text"}, {"field": "bytes", "label": "Bytes", "format": "number"}, {"field": "status", "label": "Status", "type": "text"}], "order"),
    ]
    blocks = [
        {"id": "title", "type": "markdown", "layout": "full", "body": f"# {TITLE}"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Technical summary\n\n- **Iteration 044 is valid, clean, and passed its complete six-condition gate.** Execution integrity, correctness, first check, complete-session tokens, elapsed time, and maintainability all passed.\n- **All 96/96 assignments passed hidden judgment.** This includes 480/480 withheld named cases, 192 real-Chromium cases, and 96 browser/server agreement checks. Parley passed 24/24 first checks; Python repaired one cell on its second public attempt.\n- **Parley passed 12/12 exact-root repairs.** Every baseline also passed its declared maintenance root boundary.\n- **Parley was both fastest and cheapest in complete-session tokens.** Its median was 23.4006 seconds and 60,103.5 tokens, 12.5438% faster and 1.0072% lower-token than Python, with both thresholds also passing under sol-medium and terra-medium.\n- **Parley source remained smallest.** Median final editable source was 779 o200k tokens, 11.4269–46.3683% smaller than the baselines."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [card["id"] for card in cards]},
        {"id": "method", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Methodology\n\nThe corpus, gate, v0.5.5 product, unchanged compact 222-token task context, stacks, models, runner, exact-build controls, and scratch lifecycle were frozen before measurement. Four independent tasks crossed four languages, two medium-reasoning models, and three replicates for 96 fresh sessions. A parent-owned FIFO service executed every public check outside the agent sandbox; hidden judgment separately ran withheld HTTP and Chromium cases. The independent audit recomputed aggregates from raw rows and hash-verified every external journal, cleanup, and attempt record."},
        {"id": "verdict", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Verdict: the frozen six-condition gate passed\n\nParley met the preregistered complete-session token and elapsed thresholds overall and within both models. It also retained perfect hidden correctness, 24/24 first-check success, 12/12 exact-root maintenance locality, and complete execution integrity. This is the first frozen population in this benchmark program to satisfy the full gate. The conclusion remains scoped to these synthetic contracts, scaffolds, model configurations, and machine; it is not proof of universal language superiority."},
        {"id": "gate_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "correctness", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Correctness tied at 24/24 for every language\n\nEvery final application passed all five hidden cases and its server/browser agreement check. The outcome holds overall, under both model configurations, and separately for implementation and maintenance. This supports parity on the frozen synthetic contracts; it does not estimate correctness on unmeasured production systems."},
        {"id": "correctness_chart_block", "type": "chart", "layout": "full", "chartId": "correctness_chart"},
        {"id": "first", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Parley matched the best first-check rate\n\nParley, TypeScript, and Rust each passed 24/24 first public checks. Python passed 23/24; its terra-medium museum-conservation cell passed on the second public attempt. Parley therefore met the frozen overall and task-kind first-check threshold."},
        {"id": "first_chart_block", "type": "chart", "layout": "full", "chartId": "first_check_chart"},
        {"id": "language_block", "type": "table", "layout": "full", "tableId": "language_table"},
        {"id": "tokens", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Complete-session tokens beat every baseline\n\nParley's median input-plus-output total was **60,103.5**, versus **60,715 Python**, **77,704.5 TypeScript**, and **103,114.5 Rust**. It was 1.0072% below Python overall, 0.6407% below under sol-medium, and 1.0942% below under terra-medium. The unchanged compact 222-token context keeps the fixed Parley–Python prompt difference at 207 tokens, allowing representation compactness to survive the complete workflow for this frozen population."},
        {"id": "tokens_chart_block", "type": "chart", "layout": "full", "chartId": "tokens_chart"},
        {"id": "elapsed", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Fastest overall and within both models\n\nParley's **23.4006 seconds** was 12.5438% below Python, 26.5095% below TypeScript, and 56.6301% below Rust overall. It was 13.6353% faster than Python under sol-medium and 7.9610% faster under terra-medium. The frozen elapsed condition therefore passed at every required level. These are local complete-agent-workflow measurements, not application throughput benchmarks."},
        {"id": "elapsed_chart_block", "type": "chart", "layout": "full", "chartId": "elapsed_chart"},
        {"id": "configuration_elapsed_chart_block", "type": "chart", "layout": "full", "chartId": "configuration_elapsed_chart"},
        {"id": "source", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Final editable Parley source was the smallest\n\nMedian final source was **779 o200k tokens** for Parley, versus **992 Python**, **879.5 TypeScript**, and **1,452.5 Rust**. Parley was 21.4718%, 11.4269%, and 46.3683% smaller respectively. This secondary representation result agrees with the passed primary complete-session token metric, while remaining scoped to the frozen applications."},
        {"id": "source_chart_block", "type": "chart", "layout": "full", "chartId": "source_chart"},
        {"id": "maintainability", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Maintenance locality tied at 12/12\n\nEvery hidden-correct maintenance assignment changed exactly its declared root. Parley changed only `logic.par`; TypeScript and Rust changed their single logic roots; Python changed its declared paired server/browser logic roots. All workspaces and protected inputs remained intact."},
        {"id": "configuration_block", "type": "table", "layout": "full", "tableId": "configuration_table"},
        {"id": "integrity", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Execution integrity passed cleanly\n\nThe audit verified 96 unique threads, 96 start/finish journals, 96 cleanup records, 97 public-attempt files, 290 exact-build hash boundaries, and stable repository/provenance state. Ninety-three capacity checks stayed above the frozen 16 GiB requirement. The largest disposable workspace was 161,144,484 bytes; all 96 were removed only after durable evidence, leaving zero retained scratch."},
        {"id": "integrity_block", "type": "table", "layout": "full", "tableId": "integrity_table"},
        {"id": "scratch_block", "type": "table", "layout": "full", "tableId": "scratch_table"},
        {"id": "limitations", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Limitations and claim boundary\n\nThe result covers four small synthetic server-plus-browser contracts, two model IDs, one reasoning setting, one local machine, and frozen application scaffolds. It does not measure databases, authentication, accessibility, deployment, sustained load, package discovery, ecosystem depth, security hardening, long-term evolution, or general runtime performance. This study does **not** establish universal language superiority; medians over 24 sessions describe this population and are not universal language constants."},
        {"id": "next", "type": "markdown", "layout": "full", "body": "## Next phase\n\n1. Preserve 044 unchanged; never rerun, filter, or tune on its tasks.\n2. Treat the passed gate as scoped evidence, not permission to declare universal superiority.\n3. Freeze a materially broader phase before measurement: persistence, authentication, accessibility, deployment, larger programs, security, and sustained runtime behavior.\n4. Keep the compact context and strict six-condition logic unchanged so later evidence is comparable.\n5. Publish every result, including regressions or invalidations, without selective filtering."},
    ]
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": TITLE,
            "description": "Valid preregistered 96-cell comparison: all assignments passed hidden judgment and all six conditions passed; Parley led complete-session tokens and elapsed time overall and within both model strata.",
            "generatedAt": raw["generated_at"],
            "cards": cards,
            "charts": charts,
            "tables": tables,
            "sources": [source],
            "blocks": blocks,
        },
        "snapshot": {
            "version": 1,
            "status": "ready",
            "generatedAt": raw["generated_at"],
            "datasets": datasets,
        },
        "sources": [source],
        "package_info": {
            "root": "benchmarks",
            "manifestPath": OUTPUT.name,
            "snapshotPath": RAW.name,
            "originUrl": "artifact://parley-fullstack-agent-044",
        },
    }


def main() -> int:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    validate(raw, audit)
    artifact = build(raw, audit)
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "raw_sha256": sha256(RAW),
        "protocol_sha256": sha256(PROTOCOL),
        "validation_sha256": sha256(VALIDATION),
        "audit_sha256": sha256(AUDIT),
        "datasets": {
            key: len(rows) for key, rows in artifact["snapshot"]["datasets"].items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
