#!/usr/bin/env python3
"""Build the canonical technical report artifact for agent study 040."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "results/fullstack_agent_040_raw.json"
PROTOCOL = BENCHMARKS / "fullstack_agent_040_protocol.json"
VALIDATION = BENCHMARKS / "fullstack_agent_040_validation.json"
AUDIT = BENCHMARKS / "fullstack_agent_040_audit.json"
SQL = REPORTS / "040-independent-fullstack-study-invalidated.sql"
OUTPUT = REPORTS / "040-independent-fullstack-study-invalidated.artifact.json"
RAW_SHA = "37b631af1ca17033ea30fe433699c52e90f7175b42454ac819e7bd2d3ff50914"
PROTOCOL_SHA = "3f0dc69b18b5f2dcad5a21eaddcefd498a2ebfd81694a7f2cd516e5b6875ed83"
VALIDATION_SHA = "26193ee74c0a13bf8165f4844443b9ad62fac8d36bc3f62a503164a47fa25420"
AUDIT_SHA = "feffa77e5e9840d9a65bc0d34fb251b280c4dbbab37932cf9ad2fd23b3322904"
MEASUREMENT_COMMIT = "2820f4eb3bc44578bdc60237559782c07a2511df"
SOURCE_ID = "fullstack_agent_evidence_040"
TITLE = "Independent Full-Stack Agent Study — Iteration 040"
LABELS = {
    "parley": "Parley",
    "python": "Python",
    "typescript": "TypeScript",
    "rust": "Rust",
}


def _report_helpers():
    path = REPORTS / "build_037_report.py"
    spec = importlib.util.spec_from_file_location("build_037_report_helpers_040", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load report helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCE_ID = SOURCE_ID
    return module


HELPERS = _report_helpers()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(raw: dict[str, Any], audit: dict[str, Any]) -> None:
    assert sha256(RAW) == RAW_SHA
    assert sha256(PROTOCOL) == PROTOCOL_SHA
    assert sha256(VALIDATION) == VALIDATION_SHA
    assert sha256(AUDIT) == AUDIT_SHA
    assert raw["experiment_id"] == audit["experiment_id"] == "040"
    assert raw["protocol_sha256"] == PROTOCOL_SHA
    assert raw["repository"]["commit"] == MEASUREMENT_COMMIT
    assert raw["repository"] == raw["repository_after"]
    assert raw["provenance_after_execution_error"] == ""
    assert audit["audit_pass"] is True
    assert audit["external_evidence_verified"] is True
    assert audit["matrix"] == {
        "cells": 96,
        "unique_cell_ids": 96,
        "unique_non_null_thread_ids": 94,
        "interrupted_cells": 2,
        "journal_pairs_verified": 96,
        "attempt_files_verified": 94,
    }
    assert audit["hidden"] == {
        "assignment_successes": 92,
        "named_cases_executed": 460,
        "named_case_passes": 460,
        "browser_cases_executed": 184,
        "cross_target_checks_executed": 92,
        "semantic_case_failure_cells": [],
    }
    assert audit["environment_incident"]["selective_reruns"] == 0
    assert len(audit["environment_incident"]["affected_cells"]) == 5
    assert audit["primary_gate"] == raw["summary"]["primary_gate"]
    assert audit["primary_gate"] == {
        "conditions": {
            "execution_integrity": False,
            "correctness": False,
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
        "label": "Complete frozen iteration 040 result, protocol, and independent audit",
        "path": "benchmarks/results/fullstack_agent_040_raw.json",
        "query": {
            "engine": "Python 3.14 and SQLite JSON1",
            "language": "SQL and Python",
            "sql": SQL.read_text(encoding="utf-8"),
            "description": (
                "Deterministic extraction and independent recomputation of language, "
                "model, task-kind, gate, execution, token, elapsed, source, incident, "
                "and failure summaries from every frozen session."
            ),
            "executed_at": "2026-08-12T22:43:56.752783Z",
            "tables_used": [
                "benchmarks/results/fullstack_agent_040_raw.json",
                "benchmarks/fullstack_agent_040_protocol.json",
                "benchmarks/fullstack_agent_040_validation.json",
                "benchmarks/fullstack_agent_040_audit.json",
            ],
            "filters": [
                "All 96 frozen cells; no exclusions, model-selected subsets, or reruns.",
                "Four tasks, four languages, two model configurations, three replicates.",
                "All five ENOSPC-affected cells remain failures under the frozen policy.",
                "Raw medians retain interrupted zero rows and incident-affected sessions.",
            ],
            "metric_definitions": [
                "Raw hidden success: all five withheld cases plus derived browser/server agreement pass; assignments with no hidden execution remain failures.",
                "Executed hidden case pass: a named withheld case actually ran and matched its exact expected result.",
                "First check: the first parent-owned public HTTP/browser attempt succeeds; interrupted and ENOSPC attempts remain failures.",
                "Complete session tokens: Codex input plus output tokens over all 24 frozen rows per language.",
                "Elapsed seconds: fresh-session wall time, excluding dependency preparation, over all frozen rows.",
                "Exact root: a hidden-correct maintenance output changes exactly the preregistered defect root with intact workspace integrity.",
                "Source tokens: o200k_base tokens in final editable application files.",
                "Strict gate: all six preregistered conditions must pass; one of six passed in 040 and the run is invalidated.",
            ],
        },
    }


def language_rows(raw: dict[str, Any], audit: dict[str, Any]) -> list[dict[str, Any]]:
    affected = set(audit["environment_incident"]["affected_cells"])
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
                "infrastructure_affected_cells": sum(
                    row["cell_id"] in affected for row in selected
                ),
                "workspace_integrity_rows": sum(
                    bool(row.get("workspace_integrity_ok")) for row in selected
                ),
                "post_build_integrity_rows": sum(
                    bool(row.get("post_build_integrity_ok")) for row in selected
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
        {"order": 1, "condition": "Execution integrity", "threshold": "96 unique once-run cells with complete threads, journals, public execution, protected files, exact builds, and transport", "observed": "96 rows and journals, but 94 completed threads; five cells affected by host ENOSPC and no selective reruns", "result": "FAIL"},
        {"order": 2, "condition": "Hidden correctness", "threshold": "Parley 100% and no lower than every baseline overall, by model, and by kind", "observed": "Raw Parley 22/24 versus TypeScript 24/24; four assignments had no hidden execution, although all 460 executed cases passed", "result": "FAIL"},
        {"order": 3, "condition": "First public check", "threshold": "Parley no lower than the best baseline overall and by task kind", "observed": "Raw Parley 23/24 versus TypeScript 24/24; the Parley miss was ENOSPC-affected", "result": "FAIL"},
        {"order": 4, "condition": "Complete session tokens", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "Raw Parley 63,196 versus Python 60,295 overall, 4.8113% higher; Parley also higher in both model strata", "result": "FAIL"},
        {"order": 5, "condition": "Elapsed time", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "Raw Parley 28.9052 s versus TypeScript 23.6683 s overall, 22.1262% higher; Parley also higher in both model strata", "result": "FAIL"},
        {"order": 6, "condition": "Maintainability", "threshold": "Every hidden-correct Parley repair has exact root; rate no lower than baselines", "observed": "Parley 10/10 exact roots among hidden-correct maintenance rows; Python/TypeScript 12/12 and Rust 11/12", "result": "PASS"},
    ]


def integrity_rows() -> list[dict[str, Any]]:
    checks = [
        ("Frozen result rows", "96/96 unique cell IDs retained", "PASS"),
        ("Completed unique threads", "94/96; two started cells permanently interrupted", "FAIL"),
        ("Immutable journal pairs", "96/96 external start/finish pairs hash-verified", "PASS"),
        ("External public attempt records", "94/95 embedded attempts hash-verified; one record write hit ENOSPC", "FAIL"),
        ("Command protocol compliance", "94/96; interrupted cells never entered a complete command session", "FAIL"),
        ("Checker and symlink integrity", "94/96", "FAIL"),
        ("FIFO transport integrity", "93/96", "FAIL"),
        ("Required public execution", "92/96 assignments; 372 named, 93 Chromium, 93 agreement checks", "FAIL"),
        ("Final public check", "92/96", "FAIL"),
        ("Hidden judgment completeness", "92/96 assignments; all 460 executed named cases passed", "FAIL"),
        ("Immediate exact-build hashes", "280/280 command boundaries stable; 277 commands succeeded", "PASS"),
        ("Repository and provenance stable", f"commit {MEASUREMENT_COMMIT[:7]}; post-run state identical", "PASS"),
    ]
    return [
        {"order": index, "check": check, "observed": observed, "status": status}
        for index, (check, observed, status) in enumerate(checks, 1)
    ]


def incident_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {"order": 1, "cell": "museum_rotation_build__rust__sol-medium__r2", "language": "Rust", "phase": "Session", "effect": "Started but interrupted; no thread or public/hidden execution"},
        {"order": 2, "cell": "harbor_signal_build__python__sol-medium__r2", "language": "Python", "phase": "Session", "effect": "Started but interrupted; no thread or public/hidden execution"},
        {"order": 3, "cell": "bookmobile_loading_repair__parley__sol-medium__r2", "language": "Parley", "phase": "Hidden build", "effect": "Public pass retained; hidden build failed with ENOSPC"},
        {"order": 4, "cell": "rooftop_battery_repair__parley__terra-medium__r2", "language": "Parley", "phase": "Public and hidden build", "effect": "Both build phases failed with ENOSPC"},
        {"order": 5, "cell": "bookmobile_loading_repair__rust__sol-medium__r3", "language": "Rust", "phase": "Public record", "effect": "Public broker record hit ENOSPC; later hidden semantics passed"},
    ]
    assert {row["cell"] for row in rows} == set(
        audit["environment_incident"]["affected_cells"]
    )
    return rows


def model_failure_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    cells = audit["model_failure_classes"][
        "javascript_reserved_identifier_then_repaired"
    ]
    return [
        {
            "category": "JavaScript reserved identifier, then repaired",
            "count": len(cells),
            "cell": cells[0],
            "cause": "browser.js used strict-mode reserved identifier `protected`; the second public check and hidden judgment passed",
        }
    ]


def chart(*args: Any) -> dict[str, Any]:
    result = HELPERS.chart(*args)
    result["encodings"]["tooltip"].append(
        {
            "field": "infrastructure_affected_cells",
            "type": "quantitative",
            "label": "Infrastructure-affected cells",
        }
    )
    return result


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
        "headline": [{
            "conditions_passed": 1,
            "conditions_total": 6,
            "hidden_cases_passed": 460,
            "hidden_cases_executed": 460,
            "incident_cells": 5,
            "interrupted_cells": 2,
            "token_gap_percent": audit["comparisons"]["parley_tokens_vs_python_percent"],
            "elapsed_gap_percent": audit["comparisons"]["parley_elapsed_vs_typescript_percent"],
        }],
        "languages": language_rows(raw, audit),
        "configurations": configuration_rows(audit),
        "gates": gate_rows(),
        "integrity": integrity_rows(),
        "incident_cells": incident_rows(audit),
        "model_failures": model_failure_rows(audit),
    }
    cards = [
        {"id": "gate_card", "description": "The run is invalidated and the strict gate remains false.", "dataset": "headline", "metrics": [{"field": "conditions_passed", "label": "Gate conditions passed", "format": "number", "unit": "of 6"}, {"field": "conditions_total", "label": "Required", "format": "number", "unit": "conditions"}], "sourceId": SOURCE_ID},
        {"id": "semantic_card", "description": "Every hidden named case that actually executed matched its oracle.", "dataset": "headline", "metrics": [{"field": "hidden_cases_passed", "label": "Executed hidden cases passed", "format": "number", "unit": "of 460"}, {"field": "hidden_cases_executed", "label": "Executed", "format": "number", "unit": "cases"}], "sourceId": SOURCE_ID},
        {"id": "incident_card", "description": "Host disk exhaustion contaminated five frozen cells.", "dataset": "headline", "metrics": [{"field": "incident_cells", "label": "ENOSPC-affected cells", "format": "number", "unit": "of 96"}, {"field": "interrupted_cells", "label": "Permanently interrupted", "format": "number", "unit": "cells"}], "sourceId": SOURCE_ID},
        {"id": "efficiency_card", "description": "Raw complete-session medians still missed the best baselines.", "dataset": "headline", "metrics": [{"field": "token_gap_percent", "label": "Parley token gap vs Python", "format": "number", "unit": "%"}, {"field": "elapsed_gap_percent", "label": "Parley elapsed gap vs TypeScript", "format": "number", "unit": "%"}], "sourceId": SOURCE_ID},
    ]
    charts = [
        chart("correctness_chart", "Raw hidden assignment success rate", "Frozen assignment outcomes include infrastructure-caused failures; 24 rows per language.", "hidden_success_rate", "Raw hidden success rate", "percent", "What hidden outcome did the frozen runner record by language?", "A categorical bar reports the unmodified assignment outcome while the adjacent text separates missing execution from semantic failure.", "fraction of 24 frozen rows", "descending"),
        chart("first_check_chart", "First public check success rate", "Frozen first-attempt outcomes include interrupted and ENOSPC-affected cells; higher is better.", "first_check_success_rate", "First-check rate", "percent", "Did Parley match the strongest raw baseline before repair?", "The direct four-arm comparison evaluates the frozen first-check condition without exclusions.", "fraction of 24 frozen rows", "descending"),
        chart("tokens_chart", "Median complete session tokens", "Input plus output tokens across all 24 frozen rows per language; lower is better.", "median_total_tokens", "Median tokens", "compact", "Did Parley match the cheapest raw complete-session baseline?", "A sorted magnitude comparison reports the frozen token metric while the run-level invalidation remains explicit.", "input plus output tokens per frozen row", "ascending"),
        chart("elapsed_chart", "Median fresh-session elapsed time", "Complete wall time across all 24 frozen rows per language; lower is better.", "median_elapsed_seconds", "Median seconds", "number", "Did Parley match the fastest raw elapsed baseline?", "A sorted comparison exposes the descriptive Parley–TypeScript gap.", "seconds per frozen row", "ascending"),
        chart("source_chart", "Median final editable-source tokens", "o200k_base count over available final editable application files; lower is smaller.", "median_final_o200k_tokens", "Median source tokens", "number", "Did Parley retain a source-representation compactness advantage?", "This secondary chart separates available final-source size from complete agent cost and execution validity.", "o200k_base tokens per available final source", "ascending"),
    ]
    tables = [
        table("gate_table", "Frozen six-condition gate", "Every condition is independent; one failure makes the overall verdict false.", "gates", [{"field": "order", "label": "#", "format": "number"}, {"field": "condition", "label": "Condition", "type": "text"}, {"field": "threshold", "label": "Frozen threshold", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "result", "label": "Result", "type": "text"}], "order"),
        table("incident_table", "Host disk incident impact", "All five affected cells remain in the frozen outcome; none was selectively rerun.", "incident_cells", [{"field": "order", "label": "#", "format": "number"}, {"field": "cell", "label": "Cell", "type": "text"}, {"field": "language", "label": "Language", "type": "text"}, {"field": "phase", "label": "Affected phase", "type": "text"}, {"field": "effect", "label": "Frozen effect", "type": "text"}], "order"),
        table("language_table", "Raw language-level audit", "All 24 frozen rows per language, including interruption and ENOSPC outcomes.", "languages", [{"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "median_final_o200k_tokens", "label": "Median source", "format": "number"}, {"field": "exact_root_successes", "label": "Exact roots", "format": "number"}, {"field": "infrastructure_affected_cells", "label": "Infra affected", "format": "number"}, {"field": "repair_turns", "label": "Repair turns", "format": "number"}], "language"),
        table("configuration_table", "Model-stratified raw result", "Twelve frozen rows per model/language cell; incident outcomes remain included.", "configurations", [{"field": "configuration", "label": "Configuration", "type": "text"}, {"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "exact_root_rate", "label": "Exact-root rate", "format": "percent"}], "configuration"),
        table("integrity_table", "Execution and measurement integrity audit", "Stable hashes and evidence preservation succeeded, but the session matrix did not complete cleanly.", "integrity", [{"field": "order", "label": "#", "format": "number"}, {"field": "check", "label": "Check", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "status", "label": "Status", "type": "text"}], "order"),
        table("model_failure_table", "Observed model failure class", "The only non-infrastructure model error recovered on its second public check.", "model_failures", [{"field": "category", "label": "Category", "type": "text"}, {"field": "count", "label": "Cells", "format": "number"}, {"field": "cell", "label": "Cell", "type": "text"}, {"field": "cause", "label": "Observed cause", "type": "text"}], "count", direction="desc"),
    ]
    blocks = [
        {"id": "title", "type": "markdown", "layout": "full", "body": f"# {TITLE}"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Technical summary\n\n- **Iteration 040 is invalidated and the strict claim is not established.** Host disk exhaustion affected **5/96** frozen cells, including two permanent interruptions. The raw gate passes only maintainability—**1 of 6** conditions.\n- **No executed hidden semantic case failed.** All **460/460** named hidden cases that actually ran passed, alongside 184 Chromium cases and 92 cross-target checks. Four assignments had no hidden semantic execution, so this diagnostic fact cannot restore correctness or execution-integrity gates.\n- **The raw efficiency thresholds still miss.** Parley's median complete cost was **63,196 tokens**, 4.8113% above Python, and **28.9052 seconds**, 22.1262% above TypeScript.\n- **Compact source and exact-root repair quality persist descriptively.** Parley's median available final source was **669 tokens**, 24.0636–56.2459% smaller than the baselines, and its hidden-correct maintenance rows were **10/10** exact-root."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [card["id"] for card in cards]},
        {"id": "scope", "type": "markdown", "layout": "full", "body": "## Scope, data, and metrics\n\nThe frozen comparison contains two independent implementation tasks and two independent maintenance tasks in Parley, Python, TypeScript, and Rust. It preregistered 96 fresh cells: four tasks × four languages × two medium-reasoning model configurations × three replicates. Public checks combine builds, HTTP, real Chromium, and browser/server agreement; hidden judgment adds five withheld cases per assignment. Complete tokens are Codex input plus output, elapsed time is whole-session wall time, source size uses `o200k_base`, and exact root requires a hidden-correct maintenance change confined to the preregistered defect root."},
        {"id": "methodology", "type": "markdown", "layout": "full", "body": "## Methodology\n\nThe task/case corpus, six-condition gate, product version, agent contexts, models, stacks, runner, and exact-build controls were frozen in separate commits before measurement. A parent-owned FIFO service evaluated each `./check` outside the agent sandbox and preserved attempts plus immutable start/finish journals. The independent audit recomputed every aggregate from the raw 96-row result and verified external evidence. After disk exhaustion, the frozen resume policy converted started-but-unfinished cells into permanent failures and ran only never-started cells; no affected cell was rerun."},
        {"id": "verdict", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Key finding: the primary result is failed and invalidated\n\nExecution integrity is a prerequisite, not a caveat to average away. Two cells never acquired a completed thread, three more recorded explicit ENOSPC effects, and required public or hidden execution was incomplete. The once-run policy correctly preserved those outcomes. Therefore the report cannot claim full-stack parity, correctness parity, or efficiency superiority from iteration 040—even though all semantics that actually executed passed."},
        {"id": "gate_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "incident", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The host incident affected five distinct measurement cells\n\nDisk exhaustion accumulated across disposable native and WebAssembly build workspaces. Two cells were interrupted before completion, two Parley cells lost hidden execution, and one Rust cell lost its public attempt record while later hidden semantics passed. Cleanup removed only inactive scratch build roots from older studies; canonical raw results, journals, attempts, and repository files remained. The incident classification explains the failure but does not erase it."},
        {"id": "incident_block", "type": "table", "layout": "full", "tableId": "incident_table"},
        {"id": "correctness", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Executed semantics were clean, but assignment correctness was incomplete\n\nThe frozen assignment metric records Parley at **22/24**, Python and Rust at **23/24**, and TypeScript at **24/24**. Those rates mix execution completeness with semantic correctness because missing hidden execution must fail. Separately, the audit found **zero semantic case failure cells**: all 460 named hidden cases that ran passed. This is encouraging evidence for v0.5.2 behavior, but it is not a valid 24/24 comparison and cannot satisfy the preregistered condition."},
        {"id": "correctness_chart_block", "type": "chart", "layout": "full", "chartId": "correctness_chart"},
        {"id": "first", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## First-check outcomes contain one real model error\n\nThe raw first-check rates are Parley **23/24**, Python and Rust **22/24**, and TypeScript **24/24**. Four misses are incident-related or interrupted. The one non-infrastructure model error was Python `rooftop_battery_repair__terra-medium__r3`, whose browser module used the strict-mode reserved identifier `protected`; it passed on the second check and then passed hidden judgment. Parley's v0.5.2 total-conversion and locality target classes did not recur in any completed semantic execution."},
        {"id": "first_chart_block", "type": "chart", "layout": "full", "chartId": "first_check_chart"},
        {"id": "model_failure_block", "type": "table", "layout": "full", "tableId": "model_failure_table"},
        {"id": "language_block", "type": "table", "layout": "full", "tableId": "language_table"},
        {"id": "tokens", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Raw complete-token cost remained above Python\n\nParley's raw median was **63,196** input-plus-output tokens versus Python's **60,295**, a **4.8113%** gap. The gap was also positive in both model strata. Parley remained below TypeScript (**76,178**) and Rust (**102,214.5**). These medians retain every frozen row, including two interrupted zero rows and the ENOSPC-affected sessions; they are published for completeness, not as a valid confirmatory estimate."},
        {"id": "tokens_chart_block", "type": "chart", "layout": "full", "chartId": "tokens_chart"},
        {"id": "elapsed", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Raw elapsed time remained above TypeScript\n\nParley's raw median was **28.9052 seconds** versus TypeScript's **23.6683**, a **22.1262%** gap. Python's median was 27.7607 seconds and Rust's was 52.84495. Parley also trailed TypeScript in both model strata. These are local whole-session measurements on the frozen machine and include incident effects; they are neither application-runtime measurements nor a valid superiority result."},
        {"id": "elapsed_chart_block", "type": "chart", "layout": "full", "chartId": "elapsed_chart"},
        {"id": "source", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Available final Parley source remained the smallest\n\nMedian available final editable source was **669 o200k tokens** in Parley, versus **970 Python, 881 TypeScript, and 1,529 Rust**. Parley was **31.0309%**, **24.0636%**, and **56.2459%** smaller respectively. This is descriptive evidence for representation compactness. It does not substitute for complete-session token cost and cannot restore an invalidated execution."},
        {"id": "source_chart_block", "type": "chart", "layout": "full", "chartId": "source_chart"},
        {"id": "maintainability", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Exact-root maintenance passed its frozen condition\n\nEvery hidden-correct Parley maintenance row changed exactly its declared defect root: **10/10**. Python and TypeScript were 12/12; Rust was 11/12 because its ENOSPC-affected bookmobile row passed hidden semantics but did not preserve a qualifying exact-root public result. Maintainability is the sole passing primary condition. The two Parley maintenance rows without hidden execution are excluded only by the condition's preregistered hidden-correct denominator, not from the overall study."},
        {"id": "configuration_block", "type": "table", "layout": "full", "tableId": "configuration_table"},
        {"id": "limitations", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Limitations and robustness\n\nThe audit is reproducible and evidence-complete for what the frozen runner retained: 96 unique cell rows, 96 immutable journal pairs, 94 verified external attempt files, stable repository provenance, and **280/280** stable exact-build hash boundaries. The central limitation is not sampling uncertainty but missing required execution caused by host ENOSPC. The corpus also covers only four small synthetic server-plus-browser contracts, two models, one reasoning setting, one machine, and one toolchain. It does not measure deployment, databases, authentication, accessibility, sustained load, ecosystem breadth, or production maintenance."},
        {"id": "integrity_block", "type": "table", "layout": "full", "tableId": "integrity_table"},
        {"id": "next", "type": "markdown", "layout": "full", "body": "## Next steps\n\n1. Preserve iteration 040 unchanged; do not rerun, filter, or tune on its population.\n2. Add a generic scratch-capacity preflight, per-cell cleanup policy, and retained-evidence boundary to the benchmark runner before any new measurement.\n3. Regression-test low-space refusal and cleanup using synthetic temporary workspaces, without touching historical evidence.\n4. Freeze a wholly independent iteration 041 corpus only after the runner fix is committed and validated.\n5. Keep the same six-condition gate and publish the full next matrix whether positive, mixed, negative, or invalid."},
        {"id": "questions", "type": "markdown", "layout": "full", "body": "## Further questions\n\n- Would v0.5.2 preserve complete hidden semantics in an uncontaminated independent run?\n- Which fixed context or build-loop costs explain the remaining 4.8113% raw token gap to Python?\n- Can build artifacts be safely reclaimed per cell while retaining every source snapshot, journal, attempt, and exact-build proof?\n- Does Parley's source compactness persist in larger applications with persistence, authentication, accessibility, deployment, and dependencies?"},
        {"id": "claim_boundary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Claim boundary\n\nIteration 040 establishes neither universal language superiority nor the narrower frozen parity claim. The valid statements are limited to preserved observations: the run was invalidated by host disk exhaustion; all 460 hidden named cases that executed passed; maintainability met its frozen denominator; available Parley source was the smallest; and raw Parley token/time medians still exceeded the best baselines. Even a future clean gate pass would support only its frozen comparison, never ‘best language in the world for everything.’"},
    ]
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": TITLE,
            "description": "Invalidated preregistered 96-cell comparison: host ENOSPC affected five cells, all 460 executed hidden cases passed, and the strict gate was not met.",
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
            "root": "benchmarks/results",
            "manifestPath": OUTPUT.name,
            "snapshotPath": "fullstack_agent_040_raw.json",
            "originUrl": "artifact://parley-fullstack-agent-040",
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
