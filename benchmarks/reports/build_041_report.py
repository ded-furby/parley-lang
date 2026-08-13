#!/usr/bin/env python3
"""Build the canonical technical report artifact for agent study 041."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "fullstack_agent_041_raw.json"
PROTOCOL = BENCHMARKS / "fullstack_agent_041_protocol.json"
VALIDATION = BENCHMARKS / "fullstack_agent_041_validation.json"
AUDIT = BENCHMARKS / "fullstack_agent_041_audit.json"
SQL = REPORTS / "041-independent-fullstack-study-gate-not-met.sql"
OUTPUT = REPORTS / "041-independent-fullstack-study-gate-not-met.artifact.json"
RAW_SHA = "37c27539e9003a7a28bc82b58bdc70fd9f0538a1dd5dc0ab6aa5ff6a6ffff65d"
PROTOCOL_SHA = "421aed5531ac0d6b40eab332282eac7d91c635b5022e351b819da2fe502cd655"
VALIDATION_SHA = "f17b72141c223574309910d8eda71b77c78a07b6de086765636fcac6f4343b78"
AUDIT_SHA = "f781ea8a7afb4cc7e7e3409a67036107db80e80fe43649084512d417ccb396e6"
MEASUREMENT_COMMIT = "d4bd76fbe14674804e81aeb4b50cefdd29b0e583"
SOURCE_ID = "fullstack_agent_evidence_041"
TITLE = "Independent Full-Stack Agent Study — Iteration 041"
LABELS = {
    "parley": "Parley",
    "python": "Python",
    "typescript": "TypeScript",
    "rust": "Rust",
}


def _helpers():
    path = REPORTS / "build_037_report.py"
    spec = importlib.util.spec_from_file_location("build_037_report_helpers_041", path)
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
    assert raw["experiment_id"] == audit["experiment_id"] == "041"
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
            "tokens": False,
            "elapsed": True,
            "maintainability": True,
        },
        "passed": False,
    }


def source_record(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": SOURCE_ID,
        "label": "Complete frozen iteration 041 result, protocol, and independent audit",
        "path": "benchmarks/fullstack_agent_041_raw.json",
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
                "benchmarks/fullstack_agent_041_raw.json",
                "benchmarks/fullstack_agent_041_protocol.json",
                "benchmarks/fullstack_agent_041_validation.json",
                "benchmarks/fullstack_agent_041_audit.json",
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
                "Strict gate: all six preregistered conditions must pass; five of six passed in 041.",
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


def gate_rows() -> list[dict[str, Any]]:
    return [
        {"order": 1, "condition": "Execution integrity", "threshold": "96 unique once-run cells, complete external evidence, stable protected inputs, passing capacity checks, and evidence-gated cleanup", "observed": "96 unique cells and threads; 96 journal/cleanup triples; 97 attempts; 290 exact-build hashes; 93 capacity checks; zero cleanup failures", "result": "PASS"},
        {"order": 2, "condition": "Hidden correctness", "threshold": "Parley 100% and no lower than every baseline overall, by model, and by kind", "observed": "Parley, Python, TypeScript, and Rust each passed 24/24 assignments and all 480 hidden cases", "result": "PASS"},
        {"order": 3, "condition": "First public check", "threshold": "Parley no lower than the best baseline overall and by task kind", "observed": "Parley 24/24, tied with TypeScript and Rust; Python 23/24 after one repair", "result": "PASS"},
        {"order": 4, "condition": "Complete session tokens", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "Parley 63,565.5 versus Python 60,591 overall (4.9091% higher); Parley also higher in both model strata", "result": "FAIL"},
        {"order": 5, "condition": "Elapsed time", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "Parley 30.2817 s, 1.4890% below Python and lower than every baseline overall and in both model strata", "result": "PASS"},
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
            "token_gap_percent": audit["comparisons"]["parley_tokens_vs_python_percent"],
            "elapsed_advantage_percent": -audit["comparisons"]["parley_elapsed_vs_python_percent"],
        }],
        "languages": language_rows(audit),
        "configurations": configuration_rows(audit),
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
        {"id": "efficiency_card", "description": "Parley was faster than Python but used more complete-session tokens.", "dataset": "headline", "metrics": [{"field": "token_gap_percent", "label": "Token gap vs Python", "format": "number", "unit": "%"}, {"field": "elapsed_advantage_percent", "label": "Elapsed advantage vs Python", "format": "number", "unit": "%"}], "sourceId": SOURCE_ID},
    ]
    charts = [
        chart("correctness_chart", "Hidden assignment success rate", "Complete withheld HTTP/browser judgment; 24 sessions per language.", "hidden_success_rate", "Hidden success", "percent", "Did every arm satisfy the hidden contract?", "A direct categorical comparison shows the four-way correctness tie.", "fraction of 24 sessions", "descending"),
        chart("first_check_chart", "First public check success rate", "First parent-owned HTTP/browser attempt; higher is better.", "first_check_success_rate", "First-check rate", "percent", "Did Parley match the strongest first-pass arm?", "The comparison exposes Python's one repaired browser mismatch.", "fraction of 24 sessions", "descending"),
        chart("tokens_chart", "Median complete session tokens", "Codex input plus output across all 24 sessions per language; lower is better.", "median_total_tokens", "Median tokens", "compact", "Did Parley match the lowest complete-session token baseline?", "A sorted magnitude chart directly evaluates the sole failed condition.", "input plus output tokens per session", "ascending"),
        chart("elapsed_chart", "Median fresh-session elapsed time", "Whole session wall time across all 24 sessions; lower is better.", "median_elapsed_seconds", "Median seconds", "number", "Did Parley match the fastest complete workflow?", "The sorted comparison shows Parley narrowly ahead of Python and more clearly ahead of TypeScript and Rust.", "seconds per session", "ascending"),
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
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Technical summary\n\n- **Iteration 041 is valid, clean, and still does not meet its strict all-six gate.** Execution integrity, correctness, first check, elapsed time, and maintainability passed; complete-session tokens failed.\n- **All 96/96 assignments passed hidden judgment.** This includes 480/480 withheld named cases, 192 real-Chromium cases, and 96 browser/server agreement checks.\n- **Parley passed 24/24 first checks and 12/12 exact-root repairs.** Python required one repair for a browser BigInt/Number mismatch; TypeScript and Rust also passed 24/24 first checks.\n- **Parley was fastest but not cheapest in tokens.** Its median was 30.2817 seconds and 63,565.5 tokens; Python used 60,591 tokens, 4.9091% fewer.\n- **Parley source remained smallest.** Median final editable source was 701 o200k tokens, 19.2861–51.1158% smaller than the baselines."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [card["id"] for card in cards]},
        {"id": "method", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Methodology\n\nThe corpus, gate, v0.5.2 product, contexts, stacks, models, runner, exact-build controls, and scratch lifecycle were frozen before measurement. Four independent tasks crossed four languages, two medium-reasoning models, and three replicates for 96 fresh sessions. A parent-owned FIFO service executed every public check outside the agent sandbox; hidden judgment separately ran withheld HTTP and Chromium cases. The independent audit recomputed aggregates from raw rows and hash-verified every external journal, cleanup, and attempt record."},
        {"id": "verdict", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Verdict: strong parity evidence, token threshold missed\n\nThis is the first clean independent v0.5.2 run in this sequence with full execution integrity and perfect hidden correctness across every arm. Parley also matched the best first-check and maintenance rates and had the lowest median elapsed time. But the preregistered token rule is intentionally strict: Parley had to be no higher than the cheapest baseline overall and within each model. Python remained cheaper in all three comparisons, so the overall gate is false."},
        {"id": "gate_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "correctness", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Correctness tied at 24/24 for every language\n\nEvery final application passed all five hidden cases and its server/browser agreement check. The outcome holds overall, under both model configurations, and separately for implementation and maintenance. This supports parity on the frozen synthetic contracts; it does not estimate correctness on unmeasured production systems."},
        {"id": "correctness_chart_block", "type": "chart", "layout": "full", "chartId": "correctness_chart"},
        {"id": "first", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Parley needed no repair turn\n\nParley, TypeScript, and Rust each passed 24/24 first public checks. Python passed 23/24. Its Terra Reef cell initially mixed JavaScript BigInt and Number in `browser.js`, then passed its second check and hidden judgment. The frozen result retains both attempts and the repair cost."},
        {"id": "first_chart_block", "type": "chart", "layout": "full", "chartId": "first_check_chart"},
        {"id": "failure_block", "type": "table", "layout": "full", "tableId": "failure_table"},
        {"id": "language_block", "type": "table", "layout": "full", "tableId": "language_table"},
        {"id": "tokens", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Complete-session tokens missed Python by 4.9091%\n\nParley's median input-plus-output total was **63,565.5**, versus **60,591 Python**, **77,544 TypeScript**, and **102,887.5 Rust**. The Parley–Python gap was 4.4576% under sol-medium and 4.9091% under terra-medium. Compact application syntax therefore did not fully offset context, reasoning, tool, and build-loop tokens."},
        {"id": "tokens_chart_block", "type": "chart", "layout": "full", "chartId": "tokens_chart"},
        {"id": "elapsed", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Parley had the lowest median complete workflow time\n\nParley's **30.2817 seconds** was 1.4890% below Python, 14.0353% below TypeScript, and 47.8767% below Rust. It remained fastest within sol-medium and terra-medium. These are local agent-workflow measurements, including build and feedback time—not application throughput or latency benchmarks."},
        {"id": "elapsed_chart_block", "type": "chart", "layout": "full", "chartId": "elapsed_chart"},
        {"id": "source", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Final editable Parley source was the smallest\n\nMedian final source was **701 o200k tokens** for Parley, versus **1,046 Python**, **868.5 TypeScript**, and **1,434 Rust**. Parley was 32.9828%, 19.2861%, and 51.1158% smaller respectively. This is a secondary representation result; the failed primary token metric correctly counts the whole agent session."},
        {"id": "source_chart_block", "type": "chart", "layout": "full", "chartId": "source_chart"},
        {"id": "maintainability", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Maintenance locality tied at 12/12\n\nEvery hidden-correct maintenance assignment changed exactly its declared root. Parley changed only `logic.par`; TypeScript and Rust changed their single logic roots; Python changed its declared paired server/browser logic roots. All workspaces and protected inputs remained intact."},
        {"id": "configuration_block", "type": "table", "layout": "full", "tableId": "configuration_table"},
        {"id": "integrity", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Execution integrity passed cleanly\n\nThe audit verified 96 unique threads, 96 start/finish journals, 96 cleanup records, 97 public-attempt files, 290 exact-build hash boundaries, and stable repository/provenance state. Ninety-three capacity checks stayed above the frozen 16 GiB requirement. The largest disposable workspace was 161,148,849 bytes; all 96 were removed only after durable evidence, leaving zero retained scratch."},
        {"id": "integrity_block", "type": "table", "layout": "full", "tableId": "integrity_table"},
        {"id": "scratch_block", "type": "table", "layout": "full", "tableId": "scratch_table"},
        {"id": "limitations", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Limitations\n\nThe result covers four small synthetic server-plus-browser contracts, two model IDs, one reasoning setting, one local machine, and frozen application scaffolds. It does not measure databases, authentication, accessibility, deployment, sustained load, package discovery, ecosystem depth, security hardening, long-term evolution, or general runtime performance. Medians over 24 sessions describe this population; they are not universal language constants."},
        {"id": "next", "type": "markdown", "layout": "full", "body": "## Next phase\n\n1. Preserve 041 unchanged; never rerun, filter, or tune on its tasks.\n2. Attribute the remaining approximately 3,000-token Parley–Python median gap using frozen transcript components rather than outcome-selected rows.\n3. Prefer generic context/build-loop reductions that can be justified across prior independent populations.\n4. Regression-test any product change outside the 041 corpus, then freeze a new disjoint population before measuring it.\n5. Expand later evidence toward persistence, authentication, accessibility, deployment, and larger maintenance work without weakening the all-six gate."},
        {"id": "claim_boundary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Claim boundary\n\nIteration 041 provides clean evidence of frozen correctness parity, first-check parity, elapsed superiority, exact-root parity, and smaller editable source. It does **not** establish the preregistered strict parity/efficiency claim because complete-session token parity failed. It establishes neither universal language superiority nor that Parley is the best language for every task. Even a future all-six pass would support only its frozen comparison."},
    ]
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": TITLE,
            "description": "Valid preregistered 96-cell comparison: all assignments passed hidden judgment; five of six conditions passed; complete-session token parity with Python was not met.",
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
            "originUrl": "artifact://parley-fullstack-agent-041",
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
