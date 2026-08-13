#!/usr/bin/env python3
"""Build the canonical technical report artifact for agent study 042."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "fullstack_agent_042_raw.json"
PROTOCOL = BENCHMARKS / "fullstack_agent_042_protocol.json"
VALIDATION = BENCHMARKS / "fullstack_agent_042_validation.json"
AUDIT = BENCHMARKS / "fullstack_agent_042_audit.json"
SQL = REPORTS / "042-independent-fullstack-study-gate-not-met.sql"
OUTPUT = REPORTS / "042-independent-fullstack-study-gate-not-met.artifact.json"
RAW_SHA = "13f54a40b75ff55934c62a4e44400b0fbbae713392188979fce1f6c59aa3a889"
PROTOCOL_SHA = "2a8416d542141b6da0f28ae7b415182325113770b44a1e4e4458bdfb3f6ed149"
VALIDATION_SHA = "8aa1e086f28477b1ea04884e5873971eb7541182a084b3a6a7154b19bb9e950d"
AUDIT_SHA = "b71e9c1c405ea3853059e370239f261e4bd8ea87d3016c03181717e05fce05ec"
MEASUREMENT_COMMIT = "03a6abb716f6ae30f3dc5397ad2c951607ff1c6e"
SOURCE_ID = "fullstack_agent_evidence_042"
TITLE = "Independent Full-Stack Agent Study — Iteration 042"
LABELS = {
    "parley": "Parley",
    "python": "Python",
    "typescript": "TypeScript",
    "rust": "Rust",
}


def _helpers():
    path = REPORTS / "build_037_report.py"
    spec = importlib.util.spec_from_file_location("build_037_report_helpers_042", path)
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
    assert raw["experiment_id"] == audit["experiment_id"] == "042"
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
            "elapsed": False,
            "maintainability": True,
        },
        "passed": False,
    }


def source_record(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": SOURCE_ID,
        "label": "Complete frozen iteration 042 result, protocol, and independent audit",
        "path": "benchmarks/fullstack_agent_042_raw.json",
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
                "benchmarks/fullstack_agent_042_raw.json",
                "benchmarks/fullstack_agent_042_protocol.json",
                "benchmarks/fullstack_agent_042_validation.json",
                "benchmarks/fullstack_agent_042_audit.json",
            ],
            "filters": [
                "All 96 frozen cells; no exclusions, selective reruns, or model-selected subsets.",
                "Four tasks, four languages, two model configurations, three replicates.",
                "Every public attempt and hidden judgment retained, including the repaired Python cell.",
                "Complete token and elapsed medians use all 24 rows per language.",
            ],
            "metric_definitions": [
                "Hidden success: all five withheld HTTP/browser cases plus derived cross-target agreement pass.",
                "First check: the first parent-owned public build and all four HTTP/browser cases pass.",
                "Complete session tokens: Codex input plus output tokens; lower is better.",
                "Elapsed seconds: whole fresh-session wall time excluding dependency preparation; lower is better.",
                "Exact root: a hidden-correct maintenance result changes exactly its preregistered defect-root set.",
                "Source tokens: o200k_base tokens in final editable application files; secondary only.",
                "Strict gate: all six preregistered conditions must pass; five of six passed in 042.",
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
        {"order": 3, "condition": "First public check", "threshold": "Parley no lower than the best baseline overall and by task kind", "observed": "Parley 24/24, tied with TypeScript and Rust; Python 23/24 after one repair", "result": "PASS"},
        {"order": 4, "condition": "Complete session tokens", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "Parley 59,737 versus Python 60,309.5 overall (0.9493% lower); Parley was also lower under sol-medium and terra-medium", "result": "PASS"},
        {"order": 5, "condition": "Elapsed time", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "Parley was fastest overall at 28.05485 s, but terra-medium was 27.41515 s versus Python 25.183 s (8.8637% higher)", "result": "FAIL"},
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
        "The four bars make the binding terra-medium miss visible rather than hiding it behind the faster overall median.",
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
            "conditions_passed": 5,
            "conditions_total": 6,
            "hidden_assignments_passed": 96,
            "hidden_assignments_total": 96,
            "parley_first_checks": 24,
            "parley_first_check_total": 24,
            "token_advantage_percent": -audit["comparisons"]["parley_tokens_vs_python_percent"],
            "overall_elapsed_advantage_percent": -audit["comparisons"]["parley_elapsed_vs_python_percent"],
            "terra_elapsed_gap_percent": round(
                (
                    audit["by_configuration"]["terra-medium"]["parley"]["median_elapsed_seconds"]
                    / audit["by_configuration"]["terra-medium"]["python"]["median_elapsed_seconds"]
                    - 1
                )
                * 100,
                4,
            ),
        }],
        "languages": language_rows(audit),
        "configurations": configuration_rows(audit),
        "configuration_efficiency": configuration_efficiency_rows(audit),
        "gates": gate_rows(),
        "integrity": integrity_rows(audit),
        "scratch": scratch_rows(audit),
        "model_failures": [{
            "category": "Browser BigInt/Number mismatch, then repaired",
            "count": 1,
            "cell": audit["model_failure_classes"][
                "browser_bigint_number_mismatch_then_repaired"
            ][0],
            "cause": "Python browser.js mixed BigInt and Number; the second public check and hidden judgment passed",
        }],
    }
    cards = [
        {"id": "gate_card", "description": "The clean run passed five conditions but missed the all-six gate.", "dataset": "headline", "metrics": [{"field": "conditions_passed", "label": "Conditions passed", "format": "number", "unit": "of 6"}, {"field": "conditions_total", "label": "Required", "format": "number", "unit": "conditions"}], "sourceId": SOURCE_ID},
        {"id": "correctness_card", "description": "Every frozen assignment passed complete hidden judgment.", "dataset": "headline", "metrics": [{"field": "hidden_assignments_passed", "label": "Hidden assignments", "format": "number", "unit": "of 96"}, {"field": "hidden_assignments_total", "label": "Frozen", "format": "number", "unit": "assignments"}], "sourceId": SOURCE_ID},
        {"id": "first_card", "description": "Every Parley assignment passed its first public check.", "dataset": "headline", "metrics": [{"field": "parley_first_checks", "label": "Parley first checks", "format": "number", "unit": "of 24"}, {"field": "parley_first_check_total", "label": "Parley sessions", "format": "number", "unit": "total"}], "sourceId": SOURCE_ID},
        {"id": "efficiency_card", "description": "Parley used fewer tokens and was faster overall; terra-medium still missed the elapsed threshold.", "dataset": "headline", "metrics": [{"field": "token_advantage_percent", "label": "Token advantage vs Python", "format": "number", "unit": "%"}, {"field": "overall_elapsed_advantage_percent", "label": "Overall elapsed advantage", "format": "number", "unit": "%"}, {"field": "terra_elapsed_gap_percent", "label": "Terra elapsed gap", "format": "number", "unit": "%"}], "sourceId": SOURCE_ID},
    ]
    charts = [
        chart("correctness_chart", "Hidden assignment success rate", "Complete withheld HTTP/browser judgment; 24 sessions per language.", "hidden_success_rate", "Hidden success", "percent", "Did every arm satisfy the hidden contract?", "A direct categorical comparison shows the four-way correctness tie.", "fraction of 24 sessions", "descending"),
        chart("first_check_chart", "First public check success rate", "First parent-owned HTTP/browser attempt; higher is better.", "first_check_success_rate", "First-check rate", "percent", "Did Parley match the strongest first-pass arm?", "The comparison exposes Python's one repaired browser mismatch.", "fraction of 24 sessions", "descending"),
        chart("tokens_chart", "Median complete session tokens", "Codex input plus output across all 24 sessions per language; lower is better.", "median_total_tokens", "Median tokens", "compact", "Did Parley match the lowest complete-session token baseline?", "A sorted magnitude chart shows the first clean complete-session token win over every baseline.", "input plus output tokens per session", "ascending"),
        chart("elapsed_chart", "Median fresh-session elapsed time", "Whole session wall time across all 24 sessions; lower is better.", "median_elapsed_seconds", "Median seconds", "number", "Was Parley fastest at the overall language level?", "The sorted comparison shows Parley fastest overall while the model-stratified chart exposes the binding miss.", "seconds per session", "ascending"),
        configuration_elapsed_chart(),
        chart("source_chart", "Median final editable-source tokens", "o200k_base count over final editable application files; secondary metric.", "median_final_o200k_tokens", "Median source tokens", "number", "Did compact representation persist in final applications?", "This chart separates source compactness from complete agent-session cost.", "o200k_base tokens per final source", "ascending"),
    ]
    tables = [
        table("gate_table", "Frozen six-condition gate", "One failed condition makes the overall verdict false.", "gates", [{"field": "order", "label": "#", "format": "number"}, {"field": "condition", "label": "Condition", "type": "text"}, {"field": "threshold", "label": "Frozen threshold", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "result", "label": "Result", "type": "text"}], "order"),
        table("language_table", "Complete language-level audit", "All 24 sessions per language, with no exclusions.", "languages", [{"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "median_final_o200k_tokens", "label": "Median source", "format": "number"}, {"field": "exact_root_successes", "label": "Exact roots", "format": "number"}, {"field": "repair_turns", "label": "Repair turns", "format": "number"}], "language"),
        table("configuration_table", "Model-stratified result", "Twelve sessions per model/language cell.", "configurations", [{"field": "configuration", "label": "Configuration", "type": "text"}, {"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "exact_root_rate", "label": "Exact-root rate", "format": "percent"}], "configuration"),
        table("integrity_table", "Execution and evidence audit", "Every frozen execution-integrity control passed.", "integrity", [{"field": "order", "label": "#", "format": "number"}, {"field": "check", "label": "Check", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "status", "label": "Status", "type": "text"}], "order"),
        table("scratch_table", "Scratch capacity and cleanup", "Durable evidence stayed outside disposable per-cell workspaces.", "scratch", [{"field": "order", "label": "#", "format": "number"}, {"field": "measure", "label": "Measure", "type": "text"}, {"field": "bytes", "label": "Bytes", "format": "number"}, {"field": "status", "label": "Status", "type": "text"}], "order"),
        table("failure_table", "Observed repair class", "The only first-check miss was repaired and retained.", "model_failures", [{"field": "category", "label": "Category", "type": "text"}, {"field": "count", "label": "Cells", "format": "number"}, {"field": "cell", "label": "Cell", "type": "text"}, {"field": "cause", "label": "Observed cause", "type": "text"}], "count"),
    ]
    blocks = [
        {"id": "title", "type": "markdown", "layout": "full", "body": f"# {TITLE}"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Technical summary\n\n- **Iteration 042 is valid and clean, but its strict all-six gate remains false.** Execution integrity, correctness, first check, complete-session tokens, and maintainability passed; the model-stratified elapsed rule failed.\n- **All 96/96 assignments passed hidden judgment.** This includes 480/480 withheld named cases, 192 real-Chromium cases, and 96 browser/server agreement checks.\n- **Parley passed 24/24 first checks and 12/12 exact-root repairs.** Python required one repair for a browser BigInt/Number mismatch; TypeScript and Rust also passed 24/24 first checks.\n- **Parley was both fastest overall and cheapest in complete-session tokens.** Its median was 28.05485 seconds and 59,737 tokens, 8.4325% faster and 0.9493% lower-token than Python. Under terra-medium, however, Parley was 8.8637% slower than Python, so elapsed failed.\n- **Parley source remained smallest.** Median final editable source was 672 o200k tokens, 22.0418–53.2359% smaller than the baselines."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [card["id"] for card in cards]},
        {"id": "method", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Methodology\n\nThe corpus, gate, v0.5.3 product, compact 222-token task context, stacks, models, runner, exact-build controls, and scratch lifecycle were frozen before measurement. Four independent tasks crossed four languages, two medium-reasoning models, and three replicates for 96 fresh sessions. A parent-owned FIFO service executed every public check outside the agent sandbox; hidden judgment separately ran withheld HTTP and Chromium cases. The independent audit recomputed aggregates from raw rows and hash-verified every external journal, cleanup, and attempt record."},
        {"id": "verdict", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Verdict: first clean token pass; elapsed stratum missed\n\nThis is the first clean independent run in this sequence where Parley met the preregistered complete-session token threshold overall and within both models. It also retained perfect hidden correctness, first-check parity, exact-root locality, and the fastest overall median. The elapsed rule was stricter than the overall ordering: Parley also had to be no slower than the fastest baseline within each model. Terra-medium Parley took 27.41515 seconds versus Python's 25.183, so one binding condition remains false and the overall gate does not pass."},
        {"id": "gate_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "correctness", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Correctness tied at 24/24 for every language\n\nEvery final application passed all five hidden cases and its server/browser agreement check. The outcome holds overall, under both model configurations, and separately for implementation and maintenance. This supports parity on the frozen synthetic contracts; it does not estimate correctness on unmeasured production systems."},
        {"id": "correctness_chart_block", "type": "chart", "layout": "full", "chartId": "correctness_chart"},
        {"id": "first", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Parley needed no repair turn\n\nParley, TypeScript, and Rust each passed 24/24 first public checks. Python passed 23/24. Its terra-medium Radio Archive implementation replicate 2 initially mixed JavaScript BigInt and Number in `browser.js`, then passed its second check and hidden judgment. The frozen result retains both attempts and the repair cost."},
        {"id": "first_chart_block", "type": "chart", "layout": "full", "chartId": "first_check_chart"},
        {"id": "failure_block", "type": "table", "layout": "full", "tableId": "failure_table"},
        {"id": "language_block", "type": "table", "layout": "full", "tableId": "language_table"},
        {"id": "tokens", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Complete-session tokens beat every baseline\n\nParley's median input-plus-output total was **59,737**, versus **60,309.5 Python**, **77,620 TypeScript**, and **102,875 Rust**. It was 0.9493% below Python overall, 0.9954% below under sol-medium, and 0.8639% below under terra-medium. The compact 222-token v0.5.3 task context reduced the fixed Parley–Python prompt difference to 207 tokens, allowing representation compactness to survive the complete workflow for this frozen population."},
        {"id": "tokens_chart_block", "type": "chart", "layout": "full", "chartId": "tokens_chart"},
        {"id": "elapsed", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Fastest overall, but not within terra-medium\n\nParley's **28.05485 seconds** was 8.4325% below Python, 16.3597% below TypeScript, and 51.9853% below Rust overall. It was 2.8786% faster than Python under sol-medium, but 8.8637% slower under terra-medium (27.41515 versus 25.183 seconds). That single model-stratified miss fails the frozen elapsed condition. These are local complete-agent-workflow measurements, not application throughput benchmarks."},
        {"id": "elapsed_chart_block", "type": "chart", "layout": "full", "chartId": "elapsed_chart"},
        {"id": "configuration_elapsed_chart_block", "type": "chart", "layout": "full", "chartId": "configuration_elapsed_chart"},
        {"id": "source", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Final editable Parley source was the smallest\n\nMedian final source was **672 o200k tokens** for Parley, versus **945.5 Python**, **862 TypeScript**, and **1,437 Rust**. Parley was 28.9265%, 22.0418%, and 53.2359% smaller respectively. This secondary representation result now agrees with the passed primary complete-session token metric, while remaining scoped to the frozen applications."},
        {"id": "source_chart_block", "type": "chart", "layout": "full", "chartId": "source_chart"},
        {"id": "maintainability", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Maintenance locality tied at 12/12\n\nEvery hidden-correct maintenance assignment changed exactly its declared root. Parley changed only `logic.par`; TypeScript and Rust changed their single logic roots; Python changed its declared paired server/browser logic roots. All workspaces and protected inputs remained intact."},
        {"id": "configuration_block", "type": "table", "layout": "full", "tableId": "configuration_table"},
        {"id": "integrity", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Execution integrity passed cleanly\n\nThe audit verified 96 unique threads, 96 start/finish journals, 96 cleanup records, 97 public-attempt files, 290 exact-build hash boundaries, and stable repository/provenance state. Ninety-three capacity checks stayed above the frozen 16 GiB requirement. The largest disposable workspace was 161,142,516 bytes; all 96 were removed only after durable evidence, leaving zero retained scratch."},
        {"id": "integrity_block", "type": "table", "layout": "full", "tableId": "integrity_table"},
        {"id": "scratch_block", "type": "table", "layout": "full", "tableId": "scratch_table"},
        {"id": "limitations", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Limitations\n\nThe result covers four small synthetic server-plus-browser contracts, two model IDs, one reasoning setting, one local machine, and frozen application scaffolds. It does not measure databases, authentication, accessibility, deployment, sustained load, package discovery, ecosystem depth, security hardening, long-term evolution, or general runtime performance. Medians over 24 sessions describe this population; they are not universal language constants."},
        {"id": "next", "type": "markdown", "layout": "full", "body": "## Next phase\n\n1. Preserve 042 unchanged; never rerun, filter, or tune on its tasks.\n2. Attribute the terra-medium elapsed miss from complete, frozen timing and attempt evidence rather than outcome-selected rows.\n3. Prefer generic context, build-loop, or tooling reductions justified across prior independent populations.\n4. Regression-test any product change outside the 042 corpus, then freeze a new disjoint population before measuring it.\n5. Expand later evidence toward persistence, authentication, accessibility, deployment, and larger maintenance work without weakening the all-six gate."},
        {"id": "claim_boundary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Claim boundary\n\nIteration 042 provides clean evidence of frozen correctness parity, first-check parity, complete-session token superiority, exact-root parity, the fastest overall workflow median, and smaller editable source. It does **not** establish the preregistered strict parity/efficiency claim because terra-medium elapsed parity failed. It establishes neither universal language superiority nor that Parley is the best language for every task. Even a future all-six pass would support only its frozen comparison."},
    ]
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": TITLE,
            "description": "Valid preregistered 96-cell comparison: all assignments passed hidden judgment; five of six conditions passed; Parley won complete-session tokens but missed terra-medium elapsed parity.",
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
            "originUrl": "artifact://parley-fullstack-agent-042",
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
