#!/usr/bin/env python3
"""Build the canonical stakeholder report artifact for agent study 039."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
from typing import Any


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "results/fullstack_agent_039_raw.json"
PROTOCOL = BENCHMARKS / "fullstack_agent_039_protocol.json"
VALIDATION = BENCHMARKS / "fullstack_agent_039_validation.json"
AUDIT = BENCHMARKS / "fullstack_agent_039_audit.json"
SQL = REPORTS / "039-independent-fullstack-study-gate-not-met.sql"
OUTPUT = REPORTS / "039-independent-fullstack-study-gate-not-met.artifact.json"
RAW_SHA = "28ecc96591b4f0bc3561f302e271f392c30439767d220c5a9e5ba73f0b47a3c3"
PROTOCOL_SHA = "e827e55f99af7161931cd0c6c320895afe749217584c87fe2668a36b8170a95b"
VALIDATION_SHA = "24ecb9b640b380f644a69d14d602b662ddc86ad2f5b8acca603951f6637d230b"
AUDIT_SHA = "bf2270b79cc238d58dc864a6241a3ed982b31dc5f6ccf632bac72be9d71a1fd6"
MEASUREMENT_COMMIT = "11f41b06dc0e6e72aee39c324735749d91a39682"
SOURCE_ID = "fullstack_agent_evidence_039"
TITLE = "Independent Full-Stack Agent Study — Iteration 039"
LABELS = {
    "parley": "Parley",
    "python": "Python",
    "typescript": "TypeScript",
    "rust": "Rust",
}


def _report_helpers():
    path = REPORTS / "build_037_report.py"
    spec = importlib.util.spec_from_file_location("build_037_report_helpers_039", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load report helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCE_ID = SOURCE_ID
    return module


HELPERS = _report_helpers()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values: list[float | int]) -> float:
    return float(statistics.median(values))


def validate(raw: dict[str, Any], audit: dict[str, Any]) -> None:
    assert sha256(RAW) == RAW_SHA
    assert sha256(PROTOCOL) == PROTOCOL_SHA
    assert sha256(VALIDATION) == VALIDATION_SHA
    assert sha256(AUDIT) == AUDIT_SHA
    assert raw["experiment_id"] == audit["experiment_id"] == "039"
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
        "attempt_files_verified": 99,
    }
    assert audit["primary_gate"] == raw["summary"]["primary_gate"]
    assert audit["primary_gate"] == {
        "conditions": {
            "execution_integrity": True,
            "correctness": True,
            "first_check": False,
            "tokens": False,
            "elapsed": False,
            "maintainability": False,
        },
        "passed": False,
    }


def source_record() -> dict[str, Any]:
    return {
        "id": SOURCE_ID,
        "label": "Complete frozen iteration 039 result, protocol, and independent audit",
        "path": "benchmarks/results/fullstack_agent_039_raw.json",
        "query": {
            "engine": "Python 3.14 and SQLite JSON1",
            "language": "SQL and Python",
            "sql": SQL.read_text(encoding="utf-8"),
            "description": (
                "Deterministic extraction and independent recomputation of language, "
                "model, task-kind, gate, execution, token, elapsed, source, and failure "
                "summaries from every frozen session."
            ),
            "executed_at": "2026-08-12T21:01:23.018189Z",
            "tables_used": [
                "benchmarks/results/fullstack_agent_039_raw.json",
                "benchmarks/fullstack_agent_039_protocol.json",
                "benchmarks/fullstack_agent_039_validation.json",
                "benchmarks/fullstack_agent_039_audit.json",
            ],
            "filters": [
                "All 96 frozen cells; no exclusions, model-selected subsets, or reruns.",
                "Four tasks, four languages, two model configurations, three replicates.",
                "All 99 public attempts and all 96 hidden judgments retained.",
                "Complete-session medians include first-pass successes and repaired cells.",
            ],
            "metric_definitions": [
                "Hidden success: all five withheld cases plus derived browser/server agreement pass.",
                "First check: the first parent-owned public HTTP/browser attempt succeeds.",
                "Complete session tokens: Codex input plus output tokens over all 24 rows per language.",
                "Elapsed seconds: complete fresh-session wall time, excluding dependency preparation.",
                "Exact root: a hidden-correct maintenance output changes exactly the preregistered defect root with intact workspace integrity.",
                "Source tokens: o200k_base tokens in final editable application files.",
                "Strict gate: all six preregistered conditions must pass; two of six passed in 039.",
            ],
        },
    }


def language_rows(raw: dict[str, Any], audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for language, label in LABELS.items():
        selected = [row for row in raw["results"] if row["language"] == language]
        rows.append(
            {
                "language": label,
                **audit["by_language"][language],
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
        {"order": 1, "condition": "Execution integrity", "threshold": "96 unique once-run cells with stable repository, provenance, protected files, exact builds, transport, journals, and public execution", "observed": "96/96 cells; 291/291 exact-build hashes stable; 96 journal pairs and 99 attempt files verified", "result": "PASS"},
        {"order": 2, "condition": "Hidden correctness", "threshold": "Parley 100% and no lower than every baseline overall, by model, and by kind", "observed": "Parley/Python/TypeScript 24/24; Rust 23/24; Parley is perfect in every model/kind stratum", "result": "PASS"},
        {"order": 3, "condition": "First public check", "threshold": "Parley no lower than the best baseline overall and by task kind", "observed": "Parley 21/24 versus every baseline 24/24; implementation 9/12 versus every baseline 12/12", "result": "FAIL"},
        {"order": 4, "condition": "Complete session tokens", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "63,301 versus Python 59,784.5 overall; Parley 6.72% and 5.53% above Python by model", "result": "FAIL"},
        {"order": 5, "condition": "Elapsed time", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "28.073 s versus TypeScript 22.469 s overall; Parley 24.37% and 27.43% above TypeScript by model", "result": "FAIL"},
        {"order": 6, "condition": "Maintainability", "threshold": "Every hidden-correct Parley repair has exact root; rate no lower than baselines", "observed": "Parley 6/12 exact roots; Python and TypeScript 12/12, Rust 11/11 among hidden-correct repairs", "result": "FAIL"},
    ]


def integrity_rows() -> list[dict[str, Any]]:
    checks = [
        ("Frozen cells completed", "96/96"),
        ("Unique cell and thread IDs", "96/96 cells; 96/96 threads"),
        ("Immutable journal pairs", "96/96 external start/finish pairs hash-verified"),
        ("External public attempt records", "99/99 files hash-verified against embedded attempts"),
        ("Command protocol compliance", "96/96; one ./sources then 1–2 ./check calls"),
        ("Protected/read-only and symlink integrity", "96/96 final workspaces"),
        ("Immediate exact-build hashes", "291/291 command boundaries stable"),
        ("FIFO transport integrity", "96/96"),
        ("Required public execution", "384 named cases, 96 Chromium cases, 96 derived agreements"),
        ("Final public check", "96/96"),
        ("Hidden judgment", "478/480 named cases, 192 Chromium cases, 96/96 derived agreements"),
        ("Repository and provenance stable", f"commit {MEASUREMENT_COMMIT[:7]}; post-run state identical"),
    ]
    return [
        {"order": index, "check": check, "observed": observed, "status": "PASS"}
        for index, (check, observed) in enumerate(checks, 1)
    ]


def failure_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "category": "Parley first-check",
            "count": audit["first_failure_classes"][
                "redundant_fallback_after_total_conversion"
            ],
            "scope": "clinic_queue_build / sol-medium / all replicates",
            "cause": "Used `number from (...) otherwise 0`; the total decimal-to-number conversion rejects a redundant fallback",
        },
        {
            "category": "Parley off-root maintenance",
            "count": len(audit["parley_off_root_maintenance_cells"]),
            "scope": "seedling_dispatch_repair / both models / all replicates",
            "cause": "Changed main.par as well as the declared defect root logic.par; behavior was hidden-correct",
        },
        {
            "category": "Rust hidden correctness",
            "count": len(audit["hidden_failure_cells"]),
            "scope": "event_credit_repair / sol-medium / replicate 1",
            "cause": "Overpayment clamp was wrong in two withheld HTTP/browser cases after public checks passed",
        },
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
    *,
    direction: str = "asc",
) -> dict[str, Any]:
    result = HELPERS.table(table_id, title, subtitle, dataset, columns, sort_field)
    result["defaultSort"]["direction"] = direction
    return result


def build(raw: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    source = source_record()
    datasets = {
        "headline": [{"conditions_passed": 2, "conditions_total": 6, "parley_hidden": 24, "parley_first": 21, "stable_build_hashes": 291, "build_hash_total": 291}],
        "languages": language_rows(raw, audit),
        "configurations": configuration_rows(audit),
        "gates": gate_rows(),
        "integrity": integrity_rows(),
        "failure_classes": failure_rows(audit),
    }
    cards = [
        {"id": "gate_card", "description": "The full strict claim was not established.", "dataset": "headline", "metrics": [{"field": "conditions_passed", "label": "Gate conditions passed", "format": "number", "unit": "of 6"}, {"field": "conditions_total", "label": "Required", "format": "number", "unit": "conditions"}], "sourceId": SOURCE_ID},
        {"id": "hidden_card", "description": "Parley passed every hidden assignment.", "dataset": "headline", "metrics": [{"field": "parley_hidden", "label": "Parley hidden-correct", "format": "number", "unit": "of 24"}], "sourceId": SOURCE_ID},
        {"id": "first_card", "description": "Three sol-medium implementation cells needed one repair.", "dataset": "headline", "metrics": [{"field": "parley_first", "label": "Parley first checks", "format": "number", "unit": "of 24"}], "sourceId": SOURCE_ID},
        {"id": "build_card", "description": "Every immediate post-build frozen hash stayed stable.", "dataset": "headline", "metrics": [{"field": "stable_build_hashes", "label": "Stable build hashes", "format": "number", "unit": "of 291"}, {"field": "build_hash_total", "label": "Checked", "format": "number", "unit": "boundaries"}], "sourceId": SOURCE_ID},
    ]
    charts = [
        chart("correctness_chart", "Hidden assignment success rate", "Five withheld cases plus browser/server agreement; 24 sessions per language.", "hidden_success_rate", "Hidden success rate", "percent", "Which language arms passed the complete hidden judgment?", "A categorical bar exposes the single Rust miss while retaining the three perfect arms.", "fraction of 24 sessions", "descending"),
        chart("first_check_chart", "First public check success rate", "First parent-owned HTTP/browser check; higher is better.", "first_check_success_rate", "First-check rate", "percent", "Did Parley match the strongest baseline before repair?", "The four rates directly evaluate the frozen first-check condition.", "fraction of 24 sessions", "descending"),
        chart("tokens_chart", "Median complete session tokens", "Input plus output tokens across all 24 sessions per language; lower is better.", "median_total_tokens", "Median tokens", "compact", "Did Parley match the cheapest complete-session baseline?", "A sorted magnitude comparison evaluates the frozen token threshold.", "input plus output tokens per session", "ascending"),
        chart("elapsed_chart", "Median fresh-session elapsed time", "Complete wall time across all 24 sessions per language; lower is better.", "median_elapsed_seconds", "Median seconds", "number", "Did Parley match the fastest elapsed baseline?", "A sorted comparison exposes the Parley–TypeScript gap.", "seconds per session", "ascending"),
        chart("source_chart", "Median final editable-source tokens", "o200k_base count over final editable application files; lower is smaller.", "median_final_o200k_tokens", "Median source tokens", "number", "Did Parley retain a source-representation compactness advantage?", "This secondary chart separates source size from complete agent cost.", "o200k_base tokens per final source", "ascending"),
    ]
    tables = [
        table("gate_table", "Frozen six-condition gate", "Every condition is independent; one failure makes the overall verdict false.", "gates", [{"field": "order", "label": "#", "format": "number"}, {"field": "condition", "label": "Condition", "type": "text"}, {"field": "threshold", "label": "Frozen threshold", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "result", "label": "Result", "type": "text"}], "order"),
        table("language_table", "Complete language-level audit", "All 24 sessions per language, including all failed build attempts and repair turns.", "languages", [{"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "median_final_o200k_tokens", "label": "Median source", "format": "number"}, {"field": "exact_root_successes", "label": "Exact roots", "format": "number"}, {"field": "repair_turns", "label": "Repair turns", "format": "number"}], "language"),
        table("configuration_table", "Model-stratified result", "Twelve sessions per model/language cell; medians include every outcome.", "configurations", [{"field": "configuration", "label": "Configuration", "type": "text"}, {"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "exact_root_rate", "label": "Exact-root rate", "format": "percent"}], "configuration"),
        table("integrity_table", "Execution and measurement integrity audit", "Every preregistered control passed, including immediate post-command hashes.", "integrity", [{"field": "order", "label": "#", "format": "number"}, {"field": "check", "label": "Check", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "status", "label": "Status", "type": "text"}], "order"),
        table("failure_table", "Observed failure classes", "All misses are retained; category counts refer to cells, not individual cases.", "failure_classes", [{"field": "category", "label": "Category", "type": "text"}, {"field": "count", "label": "Cells", "format": "number"}, {"field": "scope", "label": "Scope", "type": "text"}, {"field": "cause", "label": "Observed cause", "type": "text"}], "count", direction="desc"),
    ]
    blocks = [
        {"id": "title", "type": "markdown", "layout": "full", "body": f"# {TITLE}"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Executive summary\n\n- **The strict claim is not established.** Iteration 039 passes execution integrity and hidden correctness, but fails first-check, complete-token, elapsed-time, and maintainability conditions—**2 of 6** gates passed.\n- **The v0.5.1 arithmetic fixes helped, but exposed a narrower diagnostic ambiguity.** Parley passed **21/24** first checks, up from 18/24 in 038. The prior decimal-result and multiplication-spelling failures did not recur; all three new misses added `otherwise` after a total conversion.\n- **Final Parley correctness remained perfect and source remained compact.** Parley passed **24/24** hidden assignments and its median final source was **22–52% smaller** than the baselines. Complete-agent cost still trailed Python by **5.88%** in tokens and TypeScript by **24.94%** in elapsed time.\n- **Change locality regressed on one maintenance shape.** All six Parley seedling repairs changed both the defect root and main.par, so only **6/12** hidden-correct maintenance cells met the exact-root rule."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [card["id"] for card in cards]},
        {"id": "scope", "type": "markdown", "layout": "full", "body": "## What was measured\n\nThe frozen comparison covers two independent implementation tasks and two independent maintenance tasks in Parley, Python, TypeScript, and Rust. Each language ran 24 fresh sessions: two medium-reasoning model configurations, three replicates, and no exclusions or reruns. Public checks combine build, HTTP, real Chromium, and browser/server agreement. Hidden judgment adds five withheld cases. Complete tokens are Codex input plus output; elapsed time is whole-session wall time; exact root requires a hidden-correct maintenance change confined to the preregistered defect root."},
        {"id": "verdict", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The experiment is valid; broad superiority is still false\n\nAll 96 cells ran once with unique threads, the repository and toolchain stayed frozen, 291/291 immediate post-build hashes were stable, and the independent audit matched every row to immutable journals and attempt records. The negative verdict is therefore substantive rather than an execution artifact. The result supports narrower claims: perfect Parley final correctness in this corpus, materially compact editable source, and improved first-pass arithmetic ergonomics. It does not support best-in-class complete agent cost or repair locality."},
        {"id": "gate_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "correctness", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Parley preserved perfect final correctness\n\nParley, Python, and TypeScript each passed **24/24** hidden assignments; Rust passed **23/24**. Parley remained perfect overall and within every frozen model and task-kind stratum. The one Rust failure was a public-passing event-credit maintenance solution that mishandled an overpayment clamp in two withheld HTTP/browser cases. This clears the correctness gate, while also demonstrating that public success alone did not guarantee hidden behavior."},
        {"id": "correctness_chart_block", "type": "chart", "layout": "full", "chartId": "correctness_chart"},
        {"id": "first", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The previous arithmetic failure classes closed; one conversion idiom remained unclear\n\nParley passed **21/24** first checks versus **24/24** for each baseline. All three misses were sol-medium clinic implementations that wrote `number from (...) otherwise 0`. The compiler correctly rejected the fallback because decimal-to-number conversion is total; each cell fixed it in one turn and passed hidden judgment. No 038 decimal-return mismatch or unsupported `multiplied by` syntax recurred. The next fix should make the total-conversion rule unmistakable without expanding the compact always-loaded context."},
        {"id": "first_chart_block", "type": "chart", "layout": "full", "chartId": "first_check_chart"},
        {"id": "failure_block", "type": "table", "layout": "full", "tableId": "failure_table"},
        {"id": "language_block", "type": "table", "layout": "full", "tableId": "language_table"},
        {"id": "tokens", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The compact prompt reduced the gap, but Python remained cheapest\n\nParley's median complete session cost was **63,301** tokens versus Python's **59,784.5**, a **5.88%** gap. The gap persisted in both model strata: **6.72%** under sol-medium and **5.53%** under terra-medium. Parley used fewer tokens than TypeScript (**75,741**) and Rust (**98,637**). This is a substantial improvement over 038's 11.79% Python gap, but the frozen threshold is best-baseline parity, so the token condition remains false."},
        {"id": "tokens_chart_block", "type": "chart", "layout": "full", "chartId": "tokens_chart"},
        {"id": "elapsed", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## TypeScript remained the elapsed-time baseline\n\nParley's **28.073 s** median was **24.94%** above TypeScript's **22.469 s**. The model-stratified gaps were **24.37%** under sol-medium and **27.43%** under terra-medium. Python's median was 26.920 s and Rust's was 37.900 s. These measurements cover complete local working sessions on the frozen environment; they are not application-runtime or universal model-latency claims."},
        {"id": "elapsed_chart_block", "type": "chart", "layout": "full", "chartId": "elapsed_chart"},
        {"id": "source", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Parley retained a large source-representation advantage\n\nMedian final editable source was **669.5 o200k tokens** in Parley, versus **977 Python, 857 TypeScript, and 1,387 Rust**. Parley was **31.47%**, **21.88%**, and **51.73%** smaller respectively. This is meaningful evidence for representation compactness. It remains secondary to complete-session token cost, where the agent still consumed more total context and repair effort than Python."},
        {"id": "source_chart_block", "type": "chart", "layout": "full", "chartId": "source_chart"},
        {"id": "maintainability", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Correct maintenance was broader than the declared defect root\n\nAll 12 Parley maintenance assignments were hidden-correct, but only the six event-credit repairs changed exactly their declared root. Every seedling-dispatch repair also edited main.par, producing **6/12** exact-root results versus **12/12** for Python and TypeScript and **11/11** among hidden-correct Rust repairs. The repeated pattern across both models and all replicates points to a task-independent modularity or guidance issue, not a single noisy session."},
        {"id": "configuration_block", "type": "table", "layout": "full", "tableId": "configuration_table"},
        {"id": "integrity", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Independent audit preserved the negative result\n\nThe audit verified **96** unique cell IDs, **96** unique thread IDs, **96** immutable journal pairs, and **99** external attempt files. Public evaluation retained **3** failed builds and executed **384** named cases, **96** Chromium cases, and **96** agreement checks. Hidden evaluation executed all **480** named cases, **192** Chromium cases, and **96** agreement checks. Every one of **291** exact-build command boundaries preserved frozen inputs. No integrity exclusion can remove the failed efficiency or locality gates."},
        {"id": "integrity_block", "type": "table", "layout": "full", "tableId": "integrity_table"},
        {"id": "next", "type": "markdown", "layout": "full", "body": "## Recommended next phase\n\n1. Preserve iteration 039 unchanged; do not rerun or tune on its tasks.\n2. Make the total `number from decimal` conversion diagnostic explicitly reject or rewrite a trailing fallback, using task-independent examples.\n3. Improve maintenance guidance so entry points remain untouched when the declared logic root already provides the required API.\n4. Profile the remaining fixed context and build loop against Python's 5.88% token advantage without hiding necessary typed-web rules.\n5. Freeze a new independent corpus only after generic fixes and regression tests are committed; retain the same exact-build and journal audit."},
        {"id": "questions", "type": "markdown", "layout": "full", "body": "## Further questions\n\n- Can a shorter diagnostic eliminate the redundant-fallback repair without increasing always-loaded context?\n- Why did every Parley seedling repair touch main.par, and can compiler/module affordances prevent equivalent off-root edits?\n- Which remaining fixed prompt sections explain the 5.88% complete-token gap to Python?\n- Does source compactness and perfect final correctness persist in larger applications with persistence, authentication, accessibility, deployment, and dependencies?"},
        {"id": "caveats", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Caveats and claim boundary\n\nThe evidence covers four small synthetic server-plus-browser contracts, two model IDs, one reasoning level, one machine, and one frozen toolchain. Scaffolds hold framework installation and transport wiring constant. The study does not measure greenfield dependency selection, databases, authentication, accessibility, load, deployment, ecosystem breadth, or long-term maintenance. Browser work is deterministic scalar behavior rather than user-interface quality. Even a future passing gate would establish only its frozen comparison, never universal language superiority."},
    ]
    return {
        "surface": "report",
        "manifest": {"version": 1, "surface": "report", "title": TITLE, "description": "Valid preregistered 96-session comparison: perfect Parley hidden correctness and compact source, but the strict agent-efficiency and maintainability gate was not met.", "generatedAt": raw["generated_at"], "cards": cards, "charts": charts, "tables": tables, "sources": [source], "blocks": blocks},
        "snapshot": {"version": 1, "status": "ready", "generatedAt": raw["generated_at"], "datasets": datasets},
        "sources": [source],
        "package_info": {"root": "benchmarks/results", "manifestPath": OUTPUT.name, "snapshotPath": "fullstack_agent_039_raw.json", "originUrl": "artifact://parley-fullstack-agent-039"},
    }


def main() -> int:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    validate(raw, audit)
    artifact = build(raw, audit)
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "raw_sha256": sha256(RAW), "protocol_sha256": sha256(PROTOCOL), "validation_sha256": sha256(VALIDATION), "audit_sha256": sha256(AUDIT), "datasets": {key: len(rows) for key, rows in artifact["snapshot"]["datasets"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
