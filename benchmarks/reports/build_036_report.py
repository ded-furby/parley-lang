#!/usr/bin/env python3
"""Build the canonical technical report artifact for agent study 036."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "results/fullstack_agent_036_raw.json"
PROTOCOL = BENCHMARKS / "fullstack_agent_036_protocol.json"
SQL = REPORTS / "036-unseen-fullstack-study-invalid.sql"
OUTPUT = REPORTS / "036-unseen-fullstack-study-invalid.artifact.json"
RAW_SHA = "bb644554d9cf135198e31330c6a8d6a2e5876de6633a487335679947aaced096"
PROTOCOL_SHA = "4dba0ba9eb845e2b7ad37c6ff979f6492bd6a20b1f3a7dc63d3fc39df4bdbecf"
SOURCE_ID = "fullstack_agent_evidence_036"
TITLE = "Unseen Full-Stack Agent Study — Iteration 036"
LABELS = {
    "parley": "Parley",
    "python": "Python",
    "typescript": "TypeScript",
    "rust": "Rust",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values: list[float | int]) -> float:
    return float(statistics.median(values))


def validate(raw: dict, protocol: dict) -> None:
    assert sha256(RAW) == RAW_SHA
    assert sha256(PROTOCOL) == PROTOCOL_SHA
    assert raw["experiment_id"] == protocol["experiment_id"] == "036"
    assert raw["protocol_sha256"] == PROTOCOL_SHA
    assert raw["repository"]["commit"] == "42bb923f6085ef19749138f5a8204299ca8cf0e1"
    assert raw["repository"] == raw["repository_after"]
    assert raw["provenance_after_execution_error"] == ""
    assert len(raw["results"]) == 96
    assert len({row["cell_id"] for row in raw["results"]}) == 96
    assert len({row["thread_id"] for row in raw["results"]}) == 96
    assert all(row["journal_attempt"] == 1 for row in raw["results"])
    assert all(row["agent_returncode"] == 0 for row in raw["results"])
    assert all(row["command_protocol"]["compliant"] for row in raw["results"])
    assert raw["summary"]["primary_gate"]["conditions"] == {
        "execution_integrity": False,
        "correctness": True,
        "first_check": True,
        "tokens": False,
        "elapsed": False,
        "maintainability": True,
    }
    assert raw["summary"]["primary_gate"]["passed"] is False

    attempts = [attempt for row in raw["results"] for attempt in row["public_attempts"]]
    assert len(attempts) == 179
    assert all(attempt["build"]["ok"] for attempt in attempts)
    assert all(attempt.get("runtime_error") == "[Errno 1] Operation not permitted" for attempt in attempts)
    assert all(not attempt["cases"] and attempt["cross_target"] is None for attempt in attempts)

    rust = [row for row in raw["results"] if row["language"] == "rust"]
    assert len(rust) == 24
    assert all(row["checker_integrity_ok"] for row in rust)
    assert all(not row["read_only_integrity_ok"] for row in rust)
    assert all(row["workspace_integrity_ok"] is False for row in rust)
    assert all(row["unexpected_files"] == [] for row in rust)
    assert all(
        row["read_only_integrity_ok"]
        for row in raw["results"]
        if row["language"] != "rust"
    )


def source() -> dict:
    return {
        "id": SOURCE_ID,
        "label": "Complete frozen iteration 036 raw result and embedded protocol",
        "path": "benchmarks/results/fullstack_agent_036_raw.json",
        "query": {
            "engine": "Python 3.14 and SQLite JSON1",
            "language": "SQL and Python",
            "sql": SQL.read_text(encoding="utf-8"),
            "description": (
                "Deterministic extraction of language, configuration, gate, public-check, "
                "source, and integrity summaries from the complete 96-cell result."
            ),
            "executed_at": "2026-08-12T16:44:02.721948Z",
            "tables_used": [
                "benchmarks/results/fullstack_agent_036_raw.json",
                "benchmarks/fullstack_agent_036_protocol.json",
            ],
            "filters": [
                "All 96 frozen cells; no exclusions or selective reruns.",
                "Four tasks, four languages, two model configurations, three replicates.",
                "Hidden judgment executed after each fresh agent session.",
                "Public feedback attempts are retained even though loopback execution was blocked.",
            ],
            "metric_definitions": [
                "Hidden success: the final application passes all five withheld cases and the cross-target agreement check for its assignment.",
                "Complete session tokens: Codex input tokens plus output tokens for one fresh assignment session; medians use all 24 language rows, including failures.",
                "Elapsed seconds: monotonic wall time for the complete fresh agent session, including attempted public builds/checks but excluding dependency preparation.",
                "Exact root: among hidden-correct maintenance rows, changed editable files equal the preregistered root set and workspace integrity passes.",
                "First check: whether the first public HTTP/browser check succeeds; this metric is not interpretable in iteration 036 because sandbox loopback was blocked in all 179 attempts.",
            ],
        },
    }


def language_rows(raw: dict) -> list[dict]:
    rows = []
    for language, label in LABELS.items():
        selected = [row for row in raw["results"] if row["language"] == language]
        implementation = [row for row in selected if row["task_kind"] == "implementation"]
        maintenance = [row for row in selected if row["task_kind"] == "maintenance"]
        summary = raw["summary"]["by_language"][language]
        rows.append(
            {
                "language": label,
                "sessions": len(selected),
                "hidden_successes": sum(row["hidden_success"] for row in selected),
                "hidden_success_rate": summary["hidden_success_rate"],
                "implementation_successes": sum(row["hidden_success"] for row in implementation),
                "implementation_sessions": len(implementation),
                "maintenance_successes": sum(row["hidden_success"] for row in maintenance),
                "maintenance_sessions": len(maintenance),
                "median_total_tokens": summary["median_total_tokens"],
                "median_elapsed_seconds": summary["median_elapsed_seconds"],
                "median_final_o200k_tokens": median(
                    [row["source"]["totals"]["o200k_base_tokens"] for row in selected]
                ),
                "median_rough_edit_tokens": median(
                    [row["source_edits"]["rough_token_edit_count"] for row in selected]
                ),
                "hidden_correct_maintenance_rows": summary[
                    "hidden_correct_maintenance_rows"
                ],
                "exact_root_successes": summary["exact_root_successes"],
                "exact_root_rate": summary["exact_root_rate"],
                "workspace_integrity_rows": sum(
                    row["workspace_integrity_ok"] for row in selected
                ),
                "final_public_successes": sum(
                    row["final_public_check_success"] for row in selected
                ),
            }
        )
    return rows


def configuration_rows(raw: dict) -> list[dict]:
    rows = []
    for configuration in ("sol-medium", "terra-medium"):
        for language, label in LABELS.items():
            summary = raw["summary"]["by_configuration"][configuration][language]
            rows.append(
                {
                    "configuration": configuration,
                    "language": label,
                    "sessions": summary["sessions"],
                    "hidden_successes": summary["hidden_successes"],
                    "hidden_success_rate": summary["hidden_success_rate"],
                    "median_total_tokens": summary["median_total_tokens"],
                    "median_elapsed_seconds": summary["median_elapsed_seconds"],
                    "exact_root_rate": summary["exact_root_rate"],
                }
            )
    return rows


def gate_rows(raw: dict) -> list[dict]:
    summary = raw["summary"]
    return [
        {
            "order": 1,
            "condition": "Execution integrity",
            "threshold": "96 unique single-attempt cells; intact workspace and usable public feedback",
            "observed": "96/96 unique; Rust Cargo.lock changed in 24/24 and loopback failed in 179/179 public attempts",
            "raw_result": "FAIL",
            "interpretation": "FAIL",
        },
        {
            "order": 2,
            "condition": "Hidden correctness",
            "threshold": "Parley 100% and no lower than every baseline overall, by model, and by kind",
            "observed": "Parley 24/24; TypeScript 24/24; Rust 24/24; Python 12/24",
            "raw_result": "PASS",
            "interpretation": "PASS (hidden judgment only)",
        },
        {
            "order": 3,
            "condition": "First public check",
            "threshold": "Parley rate no lower than the best baseline overall and by task kind",
            "observed": "Raw 0/24 for every language; no public runtime case executed because loopback was blocked",
            "raw_result": "PASS",
            "interpretation": "NOT INTERPRETABLE",
        },
        {
            "order": 4,
            "condition": "Complete session tokens",
            "threshold": "Parley median no higher than the lowest baseline overall and within each model",
            "observed": "82,903 vs Python 74,064.5 overall; Parley also above Python in both model strata",
            "raw_result": "FAIL",
            "interpretation": "FAIL",
        },
        {
            "order": 5,
            "condition": "Elapsed time",
            "threshold": "Parley median no higher than the lowest baseline overall and within each model",
            "observed": "38.442 s vs TypeScript 37.021 s overall; Parley above TypeScript in both model strata",
            "raw_result": "FAIL",
            "interpretation": "FAIL",
        },
        {
            "order": 6,
            "condition": "Maintainability",
            "threshold": "Every hidden-correct Parley repair has exact root; rate no lower than baselines",
            "observed": "Parley 12/12; Python 12/12; TypeScript 11/12; Rust 0/12 under frozen integrity rule",
            "raw_result": "PASS",
            "interpretation": "PASS",
        },
    ]


def integrity_rows(raw: dict) -> list[dict]:
    rows = raw["results"]
    attempts = [attempt for row in rows for attempt in row["public_attempts"]]
    return [
        {"check": "Frozen cells completed", "observed": "96/96", "status": "PASS"},
        {"check": "Unique cell IDs", "observed": f"{len({row['cell_id'] for row in rows})}/96", "status": "PASS"},
        {"check": "Unique thread IDs", "observed": f"{len({row['thread_id'] for row in rows})}/96", "status": "PASS"},
        {"check": "One journal attempt per cell", "observed": f"{sum(row['journal_attempt'] == 1 for row in rows)}/96", "status": "PASS"},
        {"check": "Command protocol compliance", "observed": f"{sum(row['command_protocol']['compliant'] for row in rows)}/96", "status": "PASS"},
        {"check": "Protected checker integrity", "observed": f"{sum(row['checker_integrity_ok'] for row in rows)}/96", "status": "PASS"},
        {"check": "Read-only file integrity", "observed": f"{sum(row['read_only_integrity_ok'] for row in rows)}/96; all 24 Rust rows changed Cargo.lock", "status": "FAIL"},
        {"check": "Public check builds", "observed": f"{sum(attempt['build']['ok'] for attempt in attempts)}/{len(attempts)}", "status": "PASS"},
        {"check": "Public check runtime", "observed": f"0/{len(attempts)}; loopback bind returned operation-not-permitted", "status": "FAIL"},
        {"check": "Hidden cases executed", "observed": f"{sum(len(row['hidden_judgment']['cases']) for row in rows)}/480 plus 96/96 cross-target checks", "status": "PASS"},
        {"check": "Repository stable during run", "observed": raw["repository"]["commit"][:7], "status": "PASS"},
        {"check": "Frozen provenance stable", "observed": "Revalidated after matrix", "status": "PASS"},
    ]


def chart(
    chart_id: str,
    title: str,
    subtitle: str,
    dataset: str,
    field: str,
    label: str,
    value_format: str,
    question: str,
    rationale: str,
    unit: str,
    sort: str,
) -> dict:
    return {
        "id": chart_id,
        "title": title,
        "subtitle": subtitle,
        "type": "bar",
        "intent": "comparison",
        "dataset": dataset,
        "encodings": {
            "x": {"field": "language", "type": "nominal", "label": "Language"},
            "y": {
                "field": field,
                "type": "quantitative",
                "label": label,
                "format": value_format,
            },
            "tooltip": [
                {"field": "sessions", "type": "quantitative", "label": "Sessions"},
                {
                    "field": "implementation_successes",
                    "type": "quantitative",
                    "label": "Implementation successes",
                },
                {
                    "field": "maintenance_successes",
                    "type": "quantitative",
                    "label": "Maintenance successes",
                },
                {
                    "field": "median_final_o200k_tokens",
                    "type": "quantitative",
                    "label": "Median final source tokens",
                },
            ],
        },
        "xAxisTitle": "Language",
        "yAxisTitle": label,
        "valueFormat": value_format,
        "layout": "full",
        "sourceId": SOURCE_ID,
        "question": question,
        "rationale": rationale,
        "comparisonContext": {
            "unit": unit,
            "grain": "language median or rate across 24 frozen sessions",
            "denominator": "all 24 sessions per language; no exclusions",
            "semanticFamily": "fresh-agent full-stack comparison",
        },
        "palette": {"kind": "sequential", "name": "blue"},
        "labels": {"values": "all"},
        "settings": {"sort": sort, "showValues": True},
    }


def build(raw: dict) -> dict:
    languages = language_rows(raw)
    configurations = configuration_rows(raw)
    gates = gate_rows(raw)
    integrity = integrity_rows(raw)
    source_record = source()
    headline = [
        {
            "sessions": 96,
            "parley_hidden_successes": 24,
            "parley_sessions": 24,
            "parley_median_tokens": 82903,
            "python_median_tokens": 74064.5,
            "public_runtime_attempts": 0,
            "public_attempts": 179,
            "strict_gate": 0,
        }
    ]
    cards = [
        {
            "id": "sessions_card",
            "description": "All frozen cells completed once with unique threads.",
            "dataset": "headline",
            "metrics": [{"field": "sessions", "label": "Measured sessions", "format": "number", "unit": "of 96"}],
            "sourceId": SOURCE_ID,
        },
        {
            "id": "correctness_card",
            "description": "Parley passed every parent-run hidden judgment.",
            "dataset": "headline",
            "metrics": [
                {"field": "parley_hidden_successes", "label": "Parley hidden-correct", "format": "number", "unit": "of 24"},
            ],
            "sourceId": SOURCE_ID,
        },
        {
            "id": "tokens_card",
            "description": "Primary complete-session median; Python was lower at 74,064.5.",
            "dataset": "headline",
            "metrics": [
                {"field": "parley_median_tokens", "label": "Parley median", "format": "compact", "unit": "tokens"},
                {"field": "python_median_tokens", "label": "Python median", "format": "compact", "unit": "tokens"},
            ],
            "sourceId": SOURCE_ID,
        },
        {
            "id": "feedback_card",
            "description": "Every public runtime attempt was blocked after a successful build.",
            "dataset": "headline",
            "metrics": [
                {"field": "public_runtime_attempts", "label": "Usable public checks", "format": "number", "unit": "of 179"},
            ],
            "sourceId": SOURCE_ID,
        },
        {
            "id": "gate_card",
            "description": "The frozen six-condition study did not establish its target claim.",
            "dataset": "headline",
            "metrics": [{"field": "strict_gate", "label": "Strict gate", "format": "number", "unit": "of 1"}],
            "sourceId": SOURCE_ID,
        },
    ]
    charts = [
        chart(
            "correctness_chart",
            "Hidden assignment success rate",
            "Five withheld cases plus cross-target agreement per session; 24 sessions per language.",
            "languages",
            "hidden_success_rate",
            "Hidden success rate",
            "percent",
            "Which language arms produced applications that passed the complete hidden judgment?",
            "A four-category bar makes the exact success-rate separation visible without implying a trend.",
            "fraction of 24 sessions",
            "descending",
        ),
        chart(
            "tokens_chart",
            "Median complete session tokens",
            "Input plus output tokens over all 24 assignments per language; lower is better.",
            "languages",
            "median_total_tokens",
            "Median tokens",
            "compact",
            "Did Parley use no more complete session tokens than the cheapest baseline?",
            "A sorted magnitude comparison directly evaluates the frozen efficiency threshold.",
            "input plus output tokens per assignment",
            "ascending",
        ),
        chart(
            "elapsed_chart",
            "Median fresh-session elapsed time",
            "Complete session wall time over all 24 assignments per language; lower is better.",
            "languages",
            "median_elapsed_seconds",
            "Median seconds",
            "number",
            "Did Parley complete assignments no slower than the fastest baseline?",
            "A category bar exposes the small Parley–TypeScript gap and the larger Rust cost.",
            "seconds per assignment",
            "ascending",
        ),
        chart(
            "source_chart",
            "Median final editable-source tokens",
            "o200k_base count across the final editable files in each of 24 sessions; lower is smaller.",
            "languages",
            "median_final_o200k_tokens",
            "Median source tokens",
            "number",
            "Did Parley retain a descriptive application-source compactness advantage?",
            "A secondary source-size comparison separates representation compactness from complete agent cost.",
            "o200k_base tokens per final assignment source",
            "ascending",
        ),
    ]
    tables = [
        {
            "id": "gate_table",
            "title": "Frozen six-condition gate",
            "subtitle": "Raw runner outcomes are preserved; the blocked first-check metric is explicitly classified as uninterpretable.",
            "dataset": "gates",
            "columns": [
                {"field": "order", "label": "#", "format": "number"},
                {"field": "condition", "label": "Condition", "type": "text"},
                {"field": "threshold", "label": "Frozen threshold", "type": "text"},
                {"field": "observed", "label": "Observed", "type": "text"},
                {"field": "raw_result", "label": "Raw", "type": "text"},
                {"field": "interpretation", "label": "Audited interpretation", "type": "text"},
            ],
            "defaultSort": {"field": "order", "direction": "asc"},
            "density": "spacious",
            "layout": "full",
            "sourceId": SOURCE_ID,
        },
        {
            "id": "language_table",
            "title": "Complete language-level audit",
            "subtitle": "All 24 frozen sessions per language, including failures and invalid public feedback.",
            "dataset": "languages",
            "columns": [
                {"field": "language", "label": "Language", "type": "text"},
                {"field": "hidden_successes", "label": "Hidden successes", "format": "number"},
                {"field": "sessions", "label": "Sessions", "format": "number"},
                {"field": "implementation_successes", "label": "Build successes", "format": "number"},
                {"field": "maintenance_successes", "label": "Repair successes", "format": "number"},
                {"field": "median_total_tokens", "label": "Median tokens", "format": "number"},
                {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"},
                {"field": "median_final_o200k_tokens", "label": "Median source o200k", "format": "number"},
                {"field": "exact_root_successes", "label": "Exact-root successes", "format": "number"},
                {"field": "hidden_correct_maintenance_rows", "label": "Root denominator", "format": "number"},
                {"field": "workspace_integrity_rows", "label": "Intact workspaces", "format": "number"},
            ],
            "defaultSort": {"field": "hidden_successes", "direction": "desc"},
            "density": "dense",
            "layout": "full",
            "sourceId": SOURCE_ID,
        },
        {
            "id": "configuration_table",
            "title": "Model-stratified result",
            "subtitle": "Twelve sessions per model/language cell; complete-session medians include every outcome.",
            "dataset": "configurations",
            "columns": [
                {"field": "configuration", "label": "Configuration", "type": "text"},
                {"field": "language", "label": "Language", "type": "text"},
                {"field": "hidden_successes", "label": "Hidden successes", "format": "number"},
                {"field": "sessions", "label": "Sessions", "format": "number"},
                {"field": "median_total_tokens", "label": "Median tokens", "format": "number"},
                {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"},
                {"field": "exact_root_rate", "label": "Exact-root rate", "format": "percent"},
            ],
            "defaultSort": {"field": "configuration", "direction": "asc"},
            "density": "dense",
            "layout": "full",
            "sourceId": SOURCE_ID,
        },
        {
            "id": "integrity_table",
            "title": "Execution and measurement integrity audit",
            "subtitle": "The complete journal and raw result are retained; failures are not repaired post hoc.",
            "dataset": "integrity",
            "columns": [
                {"field": "check", "label": "Check", "type": "text"},
                {"field": "observed", "label": "Observed", "type": "text"},
                {"field": "status", "label": "Status", "type": "text"},
            ],
            "defaultSort": {"field": "check", "direction": "asc"},
            "density": "spacious",
            "layout": "full",
            "sourceId": SOURCE_ID,
        },
    ]
    blocks = [
        {"id": "title", "type": "markdown", "layout": "full", "body": f"# {TITLE}"},
        {
            "id": "summary",
            "type": "markdown",
            "layout": "full",
            "sourceId": SOURCE_ID,
            "body": (
                "## Technical summary\n\n"
                "**Iteration 036 does not establish strict unseen full-stack parity or efficiency.** "
                "All **96/96** frozen sessions ran exactly once, and Parley passed **24/24** parent-run "
                "hidden judgments, tying TypeScript and Rust and exceeding Python's **12/24**. Parley "
                "also achieved exact-root maintenance quality in **12/12** hidden-correct repairs. "
                "However, the frozen overall gate is false: Parley's **82,903** median complete-session "
                "tokens were **11.93% above Python's 74,064.5**, and its **38.442 s** median elapsed time "
                "was **3.84% above TypeScript's 37.021 s**. More importantly, all **179/179** public "
                "runtime attempts were blocked by sandbox loopback denial, and all **24/24** Rust "
                "workspaces deterministically changed the reused root entry in `Cargo.lock`. Hidden "
                "correctness remains valid descriptive evidence; first-check and repair-feedback claims do not."
            ),
        },
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [card["id"] for card in cards]},
        {
            "id": "invalid",
            "type": "markdown",
            "layout": "full",
            "sourceId": SOURCE_ID,
            "body": (
                "## The strict result is invalid, not a narrow win\n\n"
                "The raw runner correctly records an overall failure, but its six booleans need one "
                "audit qualification: `first_check=true` is only a mechanical four-way tie at zero. "
                "Every `./check` compiled the application and then failed before executing a public HTTP "
                "or browser case because the network-disabled Codex sandbox denied loopback socket "
                "binding. Agents therefore solved from the visible contract and build diagnostics rather "
                "than from the intended semantic feedback loop. Separately, Cargo rewrote the stale "
                "`release-radar-035` package record in the supplied Rust lockfile to "
                "`fullstack-agent-036`; this deterministic harness mutation makes all 24 Rust workspace "
                "integrity rows fail. The no-rerun rule is binding, so neither defect is repaired here."
            ),
        },
        {"id": "gate_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "integrity_block", "type": "table", "layout": "full", "tableId": "integrity_table"},
        {
            "id": "correctness",
            "type": "markdown",
            "layout": "full",
            "sourceId": SOURCE_ID,
            "body": (
                "## Hidden judgment shows strong Parley correctness, within a compromised protocol\n\n"
                "The parent process successfully executed all **480/480** withheld cases and all **96/96** "
                "browser/server cross-target checks. Parley, TypeScript, and Rust each passed **24/24** "
                "assignments. Python passed every repair (**12/12**) and no blank-logic implementation "
                "(**0/12**). This is exact descriptive evidence for the final artifacts agents produced, "
                "but it is not evidence for the intended repair loop because public semantic feedback never ran."
            ),
        },
        {"id": "correctness_chart_block", "type": "chart", "layout": "full", "chartId": "correctness_chart"},
        {"id": "language_block", "type": "table", "layout": "full", "tableId": "language_table"},
        {
            "id": "tokens",
            "type": "markdown",
            "layout": "full",
            "sourceId": SOURCE_ID,
            "body": (
                "## Parley beat the larger typed stacks on session tokens, but not Python\n\n"
                "Parley's **82,903** median input-plus-output tokens were **13.43% below TypeScript** and "
                "**40.51% below Rust**, but **11.93% above Python**, the frozen best-baseline comparison. "
                "The failure repeats within both models: Parley exceeded Python by **10.91%** under "
                "sol-medium and **38.34%** under terra-medium. These medians include all assignments and "
                "failures as preregistered; Python's low cost cannot be filtered away because its build-task failures are part of the population."
            ),
        },
        {"id": "tokens_chart_block", "type": "chart", "layout": "full", "chartId": "tokens_chart"},
        {
            "id": "elapsed",
            "type": "markdown",
            "layout": "full",
            "sourceId": SOURCE_ID,
            "body": (
                "## TypeScript remained faster on the frozen elapsed-time gate\n\n"
                "Parley's **38.442 s** median was close to but above TypeScript's **37.021 s**, a **3.84%** "
                "gap. The model strata preserve the ordering: Parley was **6.93%** slower than TypeScript "
                "under sol-medium and **10.72%** slower under terra-medium. Python's overall median was "
                "39.967 s and Rust's was 64.353 s. Timing includes repeated public builds that could not "
                "reach runtime judgment, so it describes this failed execution protocol rather than a clean productive-work benchmark."
            ),
        },
        {"id": "elapsed_chart_block", "type": "chart", "layout": "full", "chartId": "elapsed_chart"},
        {
            "id": "source",
            "type": "markdown",
            "layout": "full",
            "sourceId": SOURCE_ID,
            "body": (
                "## Parley's representation remained compact, but compact source did not guarantee the lowest session cost\n\n"
                "The median final editable application used **501.5 o200k tokens** in Parley, versus "
                "**801 TypeScript, 854 Python, and 1,252.5 Rust**. This secondary result is consistent "
                "with iteration 035's source-compactness motivation. The primary efficiency metric is still "
                "the complete agent session, where Python was cheaper; source size and agent effort are related but not interchangeable."
            ),
        },
        {"id": "source_chart_block", "type": "chart", "layout": "full", "chartId": "source_chart"},
        {"id": "configuration_block", "type": "table", "layout": "full", "tableId": "configuration_table"},
        {
            "id": "scope",
            "type": "markdown",
            "layout": "full",
            "body": (
                "## Scope and metric definitions\n\n"
                "The frozen population is four small server-plus-browser assignments: two blank-logic "
                "implementations and two seeded repairs, crossed with Parley, Python, TypeScript, and Rust; "
                "two model IDs at medium reasoning; and three replicates. Each cell is one fresh ephemeral "
                "session. Hidden success requires five withheld cases plus browser/server scalar agreement. "
                "Complete tokens are reported Codex input plus output tokens. Exact-root rate is defined only "
                "among hidden-correct maintenance rows. Source tokens use tiktoken 0.13.0 `o200k_base`."
            ),
        },
        {
            "id": "method",
            "type": "markdown",
            "layout": "full",
            "body": (
                "## Product, corpus, protocol, and execution were frozen in order\n\n"
                "Parley v0.5.0 was frozen at product commit `02cd809`; the unseen task/case corpus at "
                "`0d26bb9`; the execution amendment at `f9d6b05`; and final validation at `42bb923`. "
                "The task, case, skill, reference, runner, scaffold, and preparer hashes are embedded in "
                "the protocol. Clean-room reference validation passed 16/16 language/task cells before "
                "measurement. The measured matrix used four workers and immutable start/finish journals. "
                "After all cells, the repository and exact compiler/dependency provenance were revalidated."
            ),
        },
        {
            "id": "limits",
            "type": "markdown",
            "layout": "full",
            "sourceId": SOURCE_ID,
            "body": (
                "## Limitations and robustness checks\n\n"
                "**Public-feedback validity is the dominant limitation.** Zero public runtime cases ran, "
                "so first-check success, final-public success, and repair-turn interpretations are invalid. "
                "Hidden judgment is isolated from that failure and executed all 480 withheld cases plus 96 "
                "cross-target checks, but it evaluates final artifacts without proving how agents would use "
                "working feedback. Rust's lockfile mutation is deterministic harness behavior, not evidence "
                "that 24 independent agents edited a protected file; the frozen integrity verdict nevertheless "
                "remains false. The study has four synthetic contracts, one machine, two models, one reasoning "
                "level, and no production database, authentication, UI, accessibility, load, deployment, or ecosystem evaluation."
            ),
        },
        {
            "id": "next",
            "type": "markdown",
            "layout": "full",
            "body": (
                "## Next: freeze iteration 037 around a loopback-safe checker\n\n"
                "1. Preserve iteration 036 unchanged as the failed execution it is.\n"
                "2. Build a new checker architecture whose agent command exchanges files with a parent-owned "
                "loopback evaluator, or otherwise proves local-only sockets work while external network remains denied.\n"
                "3. Generate a Rust lockfile whose root package matches the scaffold, then assert read-only "
                "integrity during reference validation.\n"
                "4. Add a pre-measurement sandbox smoke that runs one complete public HTTP and browser case, "
                "not merely a model-response smoke.\n"
                "5. Freeze new tasks and cases for iteration 037; do not reuse or tune on the 036 corpus."
            ),
        },
        {
            "id": "questions",
            "type": "markdown",
            "layout": "full",
            "body": (
                "## Further questions\n\n"
                "- Does Parley's 24/24 hidden correctness replicate when agents receive a functioning public feedback loop?\n"
                "- Can compact Parley source translate into lower complete-session cost after fixed tool/context overhead is isolated?\n"
                "- Why did every Python blank-logic implementation fail while all Python repairs passed, and does that split survive a valid protocol?\n"
                "- Which checker transport best preserves external-network denial without blocking localhost services or browser execution?"
            ),
        },
    ]
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": TITLE,
            "description": "Preregistered 96-session comparison; strict result invalidated by execution defects.",
            "generatedAt": raw["generated_at"],
            "cards": cards,
            "charts": charts,
            "tables": tables,
            "sources": [source_record],
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
            },
        },
        "sources": [source_record],
        "package_info": {
            "root": "benchmarks/results",
            "manifestPath": OUTPUT.name,
            "snapshotPath": "fullstack_agent_036_raw.json",
            "originUrl": "artifact://parley-fullstack-agent-036",
        },
    }


def main() -> int:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate(raw, protocol)
    artifact = build(raw)
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "raw_sha256": sha256(RAW),
                "protocol_sha256": sha256(PROTOCOL),
                "datasets": {
                    key: len(rows)
                    for key, rows in artifact["snapshot"]["datasets"].items()
                },
                "public_runtime_errors": dict(
                    Counter(
                        attempt.get("runtime_error", "")
                        for row in raw["results"]
                        for attempt in row["public_attempts"]
                    )
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
