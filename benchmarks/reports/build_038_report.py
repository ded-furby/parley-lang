#!/usr/bin/env python3
"""Build the canonical stakeholder report artifact for agent study 038."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
from typing import Any


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "results/fullstack_agent_038_raw.json"
PROTOCOL = BENCHMARKS / "fullstack_agent_038_protocol.json"
VALIDATION = BENCHMARKS / "fullstack_agent_038_validation.json"
AUDIT = BENCHMARKS / "fullstack_agent_038_audit.json"
SQL = REPORTS / "038-unseen-fullstack-study-gate-not-met.sql"
OUTPUT = REPORTS / "038-unseen-fullstack-study-gate-not-met.artifact.json"
RAW_SHA = "84a7f30e534098b4fcc864aa08ac601cfe5b6a19d2b22c9350390bde8381a49f"
PROTOCOL_SHA = "9a0f2c8792987ec1f4841485e4d5168d317d2bbd93b7bd2904e7f5d96c74fa12"
VALIDATION_SHA = "f445e2a57652328e42c913ec93908857e03c7b6a3ccc91572a3a3921da4c24f2"
AUDIT_SHA = "12f86034bdb7ce1a7bb4dd67b05347961d66a0c53db5fd655b726caf483b7a02"
MEASUREMENT_COMMIT = "b27cac4ead4b31982eed0de9f01274dbdf8131a9"
SOURCE_ID = "fullstack_agent_evidence_038"
TITLE = "Unseen Full-Stack Agent Study — Iteration 038"
LABELS = {
    "parley": "Parley",
    "python": "Python",
    "typescript": "TypeScript",
    "rust": "Rust",
}


def _legacy_helpers():
    path = REPORTS / "build_037_report.py"
    spec = importlib.util.spec_from_file_location("build_037_report_helpers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load report helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCE_ID = SOURCE_ID
    return module


HELPERS = _legacy_helpers()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values: list[float | int]) -> float:
    return float(statistics.median(values))


def validate(raw: dict[str, Any], audit: dict[str, Any]) -> None:
    assert sha256(RAW) == RAW_SHA
    assert sha256(PROTOCOL) == PROTOCOL_SHA
    assert sha256(VALIDATION) == VALIDATION_SHA
    assert sha256(AUDIT) == AUDIT_SHA
    assert raw["experiment_id"] == audit["experiment_id"] == "038"
    assert raw["protocol_sha256"] == PROTOCOL_SHA
    assert raw["repository"]["commit"] == MEASUREMENT_COMMIT
    assert raw["repository"] == raw["repository_after"]
    assert raw["provenance_after_execution_error"] == ""
    assert audit["audit_pass"] is True
    assert audit["external_evidence_verified"] is True
    assert audit["matrix"] == {
        "cells": 96,
        "unique_cell_ids": 96,
        "unique_thread_ids": 96,
        "journal_pairs_verified": 96,
        "attempt_files_verified": 104,
    }
    assert audit["primary_gate"] == raw["summary"]["primary_gate"]
    assert audit["primary_gate"] == {
        "conditions": {
            "execution_integrity": True,
            "correctness": True,
            "first_check": False,
            "tokens": False,
            "elapsed": False,
            "maintainability": True,
        },
        "passed": False,
    }


def source_record() -> dict[str, Any]:
    return {
        "id": SOURCE_ID,
        "label": "Complete frozen iteration 038 result, protocol, and independent audit",
        "path": "benchmarks/results/fullstack_agent_038_raw.json",
        "query": {
            "engine": "Python 3.14 and SQLite JSON1",
            "language": "SQL and Python",
            "sql": SQL.read_text(encoding="utf-8"),
            "description": (
                "Deterministic extraction and independent recomputation of language, "
                "model, task-kind, gate, execution, token, elapsed, and source summaries "
                "from every frozen session."
            ),
            "executed_at": "2026-08-12T19:39:04.604010Z",
            "tables_used": [
                "benchmarks/results/fullstack_agent_038_raw.json",
                "benchmarks/fullstack_agent_038_protocol.json",
                "benchmarks/fullstack_agent_038_validation.json",
                "benchmarks/fullstack_agent_038_audit.json",
            ],
            "filters": [
                "All 96 frozen cells; no exclusions, model-selected subsets, or reruns.",
                "Four tasks, four languages, two model configurations, three replicates.",
                "All 104 public attempts and all 96 hidden judgments retained.",
                "Complete session medians include successful first checks and repaired cells.",
            ],
            "metric_definitions": [
                "Hidden success: all five withheld cases plus derived browser/server agreement pass.",
                "First check: the first parent-owned public HTTP/browser attempt succeeds.",
                "Complete session tokens: Codex input plus output tokens over all 24 rows per language.",
                "Elapsed seconds: complete fresh-session wall time, excluding dependency preparation.",
                "Exact root: a hidden-correct maintenance output changes exactly the preregistered root set with intact workspace integrity.",
                "Source tokens: o200k_base tokens in final editable application files.",
                "Strict gate: all six preregistered conditions must pass; three of six passed in 038.",
            ],
        },
    }


def language_rows(raw: dict[str, Any], audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for language, label in LABELS.items():
        selected = [row for row in raw["results"] if row["language"] == language]
        summary = audit["by_language"][language]
        rows.append(
            {
                "language": label,
                **summary,
                "median_final_o200k_tokens": audit[
                    "median_final_source_o200k_tokens"
                ][language],
                "median_rough_edit_tokens": median(
                    [row["source_edits"]["rough_token_edit_count"] for row in selected]
                ),
                "workspace_integrity_rows": sum(
                    row["workspace_integrity_ok"] for row in selected
                ),
                "post_build_integrity_rows": sum(
                    row["post_build_integrity_ok"] for row in selected
                ),
            }
        )
    return rows


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
        {"order": 1, "condition": "Execution integrity", "threshold": "96 unique, once-run cells with stable repository, provenance, protected files, exact builds, transport, journals, and public execution", "observed": "96/96 cells; 297/297 exact-build hash checks stable; 96 journal pairs and 104 attempt files independently verified", "result": "PASS"},
        {"order": 2, "condition": "Hidden correctness", "threshold": "Parley 100% and no lower than every baseline overall, by model, and by kind", "observed": "Parley, Python, TypeScript, and Rust each 24/24; every model/kind stratum 100%", "result": "PASS"},
        {"order": 3, "condition": "First public check", "threshold": "Parley no lower than the best baseline overall and by task kind", "observed": "Parley 18/24 versus every baseline 24/24; implementation 6/12 versus every baseline 12/12", "result": "FAIL"},
        {"order": 4, "condition": "Complete session tokens", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "67,715 versus Python 60,571.5 overall; Parley 12.07% and 11.54% above Python by model", "result": "FAIL"},
        {"order": 5, "condition": "Elapsed time", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "29.669 s versus TypeScript 22.876 s overall; Parley 19.29% and 30.00% above TypeScript by model", "result": "FAIL"},
        {"order": 6, "condition": "Maintainability", "threshold": "Every hidden-correct Parley repair has exact root; rate no lower than baselines", "observed": "Every language 12/12 exact roots with intact workspaces", "result": "PASS"},
    ]


def integrity_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("Frozen cells completed", "96/96"),
        ("Unique cell and thread IDs", "96/96 cells; 96/96 threads"),
        ("Immutable journal pairs", "96/96 external start/finish pairs hash-verified"),
        ("External public attempt records", "104/104 files hash-verified against embedded attempts"),
        ("Command protocol compliance", "96/96; one ./sources then 1–3 ./check calls"),
        ("Protected/read-only and symlink integrity", "96/96 final workspaces"),
        ("Immediate exact-build hashes", "297/297 command boundaries stable"),
        ("FIFO transport integrity", "96/96"),
        ("Required public execution", "388 named cases, 97 Chromium cases, 97 derived agreements"),
        ("Final public check", "96/96"),
        ("Hidden judgment", "480/480 named cases, 192 Chromium cases, 96/96 derived agreements"),
        ("Repository and provenance stable", f"commit {MEASUREMENT_COMMIT[:7]}; post-run state identical"),
    ]
    assert audit["exact_build"]["stable_hash_checks"] == 297
    return [
        {"order": index, "check": check, "observed": observed, "status": "PASS"}
        for index, (check, observed) in enumerate(checks, 1)
    ]


def failure_class_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "class": "Decimal-to-number result",
            "first_failures": audit["first_failure_classes"]["decimal_to_number"],
            "scope": "Parley archive implementation",
            "diagnostic": "Division produced decimal where the declared function returned number",
        },
        {
            "class": "Unsupported `multiplied by` spelling",
            "first_failures": audit["first_failure_classes"][
                "unsupported_multiplied_by"
            ],
            "scope": "Parley archive implementation",
            "diagnostic": "Parser rejected the attempted operator wording",
        },
    ]


def chart(
    chart_id: str,
    title: str,
    subtitle: str,
    field: str,
    label: str,
    value_format: str,
    question: str,
    rationale: str,
    unit: str,
    sort: str,
) -> dict[str, Any]:
    return HELPERS.chart(
        chart_id,
        title,
        subtitle,
        field,
        label,
        value_format,
        question,
        rationale,
        unit,
        sort,
    )


def table(
    table_id: str,
    title: str,
    subtitle: str,
    dataset: str,
    columns: list[dict[str, Any]],
    sort_field: str,
    *,
    direction: str = "asc",
) -> dict[str, Any]:
    result = HELPERS.table(
        table_id, title, subtitle, dataset, columns, sort_field
    )
    result["defaultSort"]["direction"] = direction
    return result


def build(raw: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    languages = language_rows(raw, audit)
    configurations = configuration_rows(audit)
    gates = gate_rows()
    integrity = integrity_rows(audit)
    failures = failure_class_rows(audit)
    source = source_record()
    headline = [
        {
            "conditions_passed": 3,
            "conditions_total": 6,
            "hidden_successes": 96,
            "hidden_total": 96,
            "parley_first": 18,
            "baseline_first": 24,
            "stable_build_hashes": 297,
            "build_hash_total": 297,
        }
    ]
    cards = [
        {"id": "gate_card", "description": "The full strict claim was not established.", "dataset": "headline", "metrics": [{"field": "conditions_passed", "label": "Gate conditions passed", "format": "number", "unit": "of 6"}, {"field": "conditions_total", "label": "Required", "format": "number", "unit": "conditions"}], "sourceId": SOURCE_ID},
        {"id": "hidden_card", "description": "Every final assignment passed hidden judgment.", "dataset": "headline", "metrics": [{"field": "hidden_successes", "label": "Hidden-correct", "format": "number", "unit": "of 96"}, {"field": "hidden_total", "label": "Measured", "format": "number", "unit": "assignments"}], "sourceId": SOURCE_ID},
        {"id": "first_card", "description": "Parley missed six first checks; baselines missed none.", "dataset": "headline", "metrics": [{"field": "parley_first", "label": "Parley first checks", "format": "number", "unit": "of 24"}, {"field": "baseline_first", "label": "Each baseline", "format": "number", "unit": "of 24"}], "sourceId": SOURCE_ID},
        {"id": "build_card", "description": "The 037 lockfile-integrity defect is closed.", "dataset": "headline", "metrics": [{"field": "stable_build_hashes", "label": "Stable build hashes", "format": "number", "unit": "of 297"}, {"field": "build_hash_total", "label": "Checked", "format": "number", "unit": "command boundaries"}], "sourceId": SOURCE_ID},
    ]
    charts = [
        chart("correctness_chart", "Hidden assignment success rate", "Five withheld cases plus browser/server agreement; 24 sessions per language.", "hidden_success_rate", "Hidden success rate", "percent", "Which language arms passed the complete hidden judgment?", "A categorical bar confirms the four perfect language arms under one denominator.", "fraction of 24 sessions", "descending"),
        chart("first_check_chart", "First public check success rate", "First parent-owned HTTP/browser check; higher is better.", "first_check_success_rate", "First-check rate", "percent", "Did Parley match the strongest baseline before repair?", "The four rates directly evaluate the frozen first-check condition.", "fraction of 24 sessions", "descending"),
        chart("tokens_chart", "Median complete session tokens", "Input plus output tokens across all 24 sessions per language; lower is better.", "median_total_tokens", "Median tokens", "compact", "Did Parley match the cheapest complete-session baseline?", "A sorted magnitude comparison directly evaluates the token threshold.", "input plus output tokens per session", "ascending"),
        chart("elapsed_chart", "Median fresh-session elapsed time", "Complete wall time across all 24 sessions per language; lower is better.", "median_elapsed_seconds", "Median seconds", "number", "Did Parley match the fastest elapsed baseline?", "A sorted category comparison exposes the Parley–TypeScript gap.", "seconds per session", "ascending"),
        chart("source_chart", "Median final editable-source tokens", "o200k_base count over final editable application files; lower is smaller.", "median_final_o200k_tokens", "Median source tokens", "number", "Did Parley retain a source-representation compactness advantage?", "This secondary chart separates source size from complete agent cost.", "o200k_base tokens per final source", "ascending"),
    ]
    tables = [
        table("gate_table", "Frozen six-condition gate", "Every condition is reported independently; one failure makes the overall verdict false.", "gates", [{"field": "order", "label": "#", "format": "number"}, {"field": "condition", "label": "Condition", "type": "text"}, {"field": "threshold", "label": "Frozen threshold", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "result", "label": "Result", "type": "text"}], "order"),
        table("language_table", "Complete language-level audit", "All 24 sessions per language, including every failed build attempt and repair turn.", "languages", [{"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "median_final_o200k_tokens", "label": "Median source", "format": "number"}, {"field": "exact_root_successes", "label": "Exact roots", "format": "number"}, {"field": "workspace_integrity_rows", "label": "Intact workspaces", "format": "number"}, {"field": "repair_turns", "label": "Repair turns", "format": "number"}], "language"),
        table("configuration_table", "Model-stratified result", "Twelve sessions per model/language cell; medians include every outcome.", "configurations", [{"field": "configuration", "label": "Configuration", "type": "text"}, {"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "exact_root_rate", "label": "Exact-root rate", "format": "percent"}], "configuration"),
        table("integrity_table", "Execution and measurement integrity audit", "Every preregistered control passed, including exact post-command frozen-input hashes.", "integrity", [{"field": "order", "label": "#", "format": "number"}, {"field": "check", "label": "Check", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "status", "label": "Status", "type": "text"}], "order"),
        table("failure_table", "First-check failure classes", "Six Parley archive implementations account for every first-check miss.", "failure_classes", [{"field": "class", "label": "Class", "type": "text"}, {"field": "first_failures", "label": "First failures", "format": "number"}, {"field": "scope", "label": "Scope", "type": "text"}, {"field": "diagnostic", "label": "Observed diagnostic", "type": "text"}], "first_failures", direction="desc"),
    ]
    blocks = [
        {"id": "title", "type": "markdown", "layout": "full", "body": f"# {TITLE}"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Executive Summary\n\n- **The strict claim is not established.** Iteration 038 passes execution integrity, hidden correctness, and maintainability, but fails first-check, complete-token, and elapsed-time conditions—**3 of 6** gates passed.\n- **Reliability is now cleanly measured and strong.** All **96/96** assignments passed hidden judgment, every final public check passed, all maintenance arms achieved **12/12** exact roots, and **297/297** exact-build hash boundaries stayed frozen.\n- **The remaining gap is agent effort, not final correctness.** Parley passed **18/24** first checks versus **24/24** for every baseline, used **11.79%** more complete-session tokens than Python, and took **29.70%** longer than TypeScript. Its final editable source was still **18–49%** smaller than the baselines."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [card["id"] for card in cards]},
        {"id": "scope", "type": "markdown", "layout": "full", "body": "## What was measured\n\nThe frozen comparison covers two implementation tasks and two maintenance tasks in Parley, Python, TypeScript, and Rust. Each language ran 24 fresh sessions: two medium-reasoning model configurations, three replicates, and no exclusions or reruns. A first check means the first parent-owned public build plus three HTTP cases, one real-Chromium case, and derived browser/server agreement. Hidden success adds five withheld cases. Complete tokens are Codex input plus output; elapsed time is whole-session wall time; exact root requires a hidden-correct maintenance change confined to the preregistered defect root with intact workspace integrity."},
        {"id": "verdict", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The experiment is valid, but the superiority gate is false\n\nIteration 038 closes the execution defect that invalidated 037. The canonical Rust lock stayed unchanged under every native and WASM build, all frozen repository and toolchain checks held, and the independent audit matched each raw row to its journal and public-attempt files. That makes the negative gate result interpretable: Parley reached perfect final correctness, but did not match the best baseline on first-pass reliability, complete token cost, or elapsed time. The result supports a narrower claim—compact, reliable final applications—not broad efficiency superiority."},
        {"id": "gate_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "correctness", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Final correctness and repair scope were perfect across all four languages\n\nEvery language passed **24/24** hidden assignments, including all **480** withheld named cases, **192** hidden Chromium cases, and **96** derived agreement checks. Every hidden-correct maintenance result in every language changed exactly its declared root set (**12/12** each). This removes correctness and patch-scope as differentiators in this corpus; the decision turns on how much repair and session cost each stack required to reach the same outcome."},
        {"id": "correctness_chart_block", "type": "chart", "layout": "full", "chartId": "correctness_chart"},
        {"id": "first", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## One implementation shape caused all six Parley first-check misses\n\nParley passed **18/24** first checks while Python, TypeScript, and Rust each passed **24/24**. All six misses were the archive-retention implementation: five first builds returned a decimal where a whole `number` was declared, and one tried unsupported `multiplied by` wording. Every cell recovered and later passed hidden judgment; one Parley cell needed two repair turns. A Python cell ran an unnecessary second passing check, producing eight total repair turns despite only six first-check failures. The actionable target is therefore first-pass arithmetic guidance for integer division and accepted operator spelling—not broader runtime correctness."},
        {"id": "first_chart_block", "type": "chart", "layout": "full", "chartId": "first_check_chart"},
        {"id": "failure_block", "type": "table", "layout": "full", "tableId": "failure_table"},
        {"id": "language_block", "type": "table", "layout": "full", "tableId": "language_table"},
        {"id": "tokens", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Python remained the complete-session token baseline\n\nParley's median was **67,715** input-plus-output tokens versus Python's **60,571.5**, a **11.79%** gap. The gap repeats in both frozen model strata: **12.07%** under sol-medium and **11.54%** under terra-medium. Parley still used fewer tokens than TypeScript (**75,756**) and Rust (**98,230.5**), but the preregistered condition compares against the cheapest baseline. Because all sessions are retained, the archive repairs correctly remain part of Parley's measured cost."},
        {"id": "tokens_chart_block", "type": "chart", "layout": "full", "chartId": "tokens_chart"},
        {"id": "elapsed", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## TypeScript remained the elapsed-time baseline\n\nParley's **29.669 s** median was **29.70%** above TypeScript's **22.876 s**. The model-stratified gaps are **19.29%** under sol-medium and **30.00%** under terra-medium. Python's overall median was 29.563 s and Rust's was 38.398 s. These are complete working-session measurements on the frozen local environment—not application runtime benchmarks or universal model latency claims."},
        {"id": "elapsed_chart_block", "type": "chart", "layout": "full", "chartId": "elapsed_chart"},
        {"id": "source", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Parley source stayed smaller, but representation is not total effort\n\nThe median final editable application contained **681.5 o200k tokens** in Parley, versus **829 TypeScript, 1,009.5 Python, and 1,345 Rust**. Parley was **17.79%**, **32.49%**, and **49.33%** smaller respectively. That is meaningful representation evidence, but it does not override the frozen complete-session metric: concise output still required more model tokens than Python and more wall time than TypeScript."},
        {"id": "source_chart_block", "type": "chart", "layout": "full", "chartId": "source_chart"},
        {"id": "configuration_block", "type": "table", "layout": "full", "tableId": "configuration_table"},
        {"id": "integrity", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The negative result survived independent integrity audit\n\nThe audit verified **96** unique cell IDs, **96** unique thread IDs, **96** immutable journal pairs, and all **104** external attempt files. Public evaluation executed **388** named cases, **97** Chromium cases, and **97** derived agreement checks; seven failed build attempts retained stable frozen hashes and all **96** final checks passed. Hidden evaluation executed the full **480-case** matrix. Every one of **297** exact-build command boundaries preserved protected/read-only inputs. There is no integrity exclusion available to explain away the failed efficiency gates."},
        {"id": "integrity_block", "type": "table", "layout": "full", "tableId": "integrity_table"},
        {"id": "next", "type": "markdown", "layout": "full", "body": "## Recommended next phase\n\n1. Preserve iteration 038 unchanged; do not rerun or tune on its tasks.\n2. Improve general Parley guidance and diagnostics for whole-number division and accepted multiplication syntax, using task-independent examples.\n3. Reduce always-injected full-stack context and repeated build-repair explanation without hiding necessary typed-web rules.\n4. Freeze a new independent corpus only after those generic changes are committed, then require the same exact-build and journal audit.\n5. Keep final-source compactness as a secondary measure while optimizing the primary complete-session token and elapsed gates."},
        {"id": "questions", "type": "markdown", "layout": "full", "body": "## Further questions\n\n- Can a task-independent integer-division diagnostic eliminate the recurring first-build mistake without adding more prompt tokens than it saves?\n- Which parts of the frozen Parley skill and typed-web reference are actually consulted in successful first-pass sessions?\n- Does Parley's source compactness persist in larger applications with persistence, authentication, accessibility, deployment, and dependency choices?\n- Can a later independent corpus confirm both perfect final correctness and baseline-leading complete-session cost?"},
        {"id": "caveats", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Caveats and assumptions\n\nThe evidence covers four small synthetic server-plus-browser contracts, two model IDs, one reasoning level, one machine, and one frozen toolchain. Scaffolds deliberately hold framework installation and transport wiring constant; the study does not measure greenfield dependency selection, databases, authentication, accessibility, load, deployment, ecosystem breadth, or long-term maintenance. Browser work is deterministic scalar module behavior rather than user-interface quality. A passing future gate would support only its frozen comparison, never universal language superiority."},
    ]
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": TITLE,
            "description": "Valid preregistered 96-session comparison: perfect final correctness and execution integrity, but the strict agent-efficiency gate was not met.",
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
            "datasets": {
                "headline": headline,
                "languages": languages,
                "configurations": configurations,
                "gates": gates,
                "integrity": integrity,
                "failure_classes": failures,
            },
        },
        "sources": [source],
        "package_info": {
            "root": "benchmarks/results",
            "manifestPath": OUTPUT.name,
            "snapshotPath": "fullstack_agent_038_raw.json",
            "originUrl": "artifact://parley-fullstack-agent-038",
        },
    }


def main() -> int:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    validate(raw, audit)
    artifact = build(raw, audit)
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "raw_sha256": sha256(RAW),
                "protocol_sha256": sha256(PROTOCOL),
                "validation_sha256": sha256(VALIDATION),
                "audit_sha256": sha256(AUDIT),
                "datasets": {
                    key: len(rows)
                    for key, rows in artifact["snapshot"]["datasets"].items()
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
