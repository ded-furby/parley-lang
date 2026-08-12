#!/usr/bin/env python3
"""Build the canonical technical report artifact for agent study 037."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "results/fullstack_agent_037_raw.json"
PROTOCOL = BENCHMARKS / "fullstack_agent_037_protocol.json"
VALIDATION = BENCHMARKS / "fullstack_agent_037_validation.json"
SQL = REPORTS / "037-unseen-fullstack-study-invalid.sql"
OUTPUT = REPORTS / "037-unseen-fullstack-study-invalid.artifact.json"
RAW_SHA = "541d43b74cf9939d8a6bfc5ce7761dda74825b3d4eb8e8482fa6ef698014549f"
PROTOCOL_SHA = "83fd7ad152068e436a253f6f5992ae9d2214db646ceb7923c29734d2786e0080"
VALIDATION_SHA = "75d0bbf02e079f13906a7fb950dacea67e00ada23c4b289b397bc6c9d36adac5"
SOURCE_ID = "fullstack_agent_evidence_037"
TITLE = "Unseen Full-Stack Agent Study — Iteration 037"
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
    assert sha256(VALIDATION) == VALIDATION_SHA
    assert raw["experiment_id"] == protocol["experiment_id"] == "037"
    assert raw["protocol_sha256"] == PROTOCOL_SHA
    assert raw["repository"]["commit"] == "5d38c77dbc99251b1def00da8a6c2e3c79e8778f"
    assert raw["repository"] == raw["repository_after"]
    assert raw["provenance_after_execution_error"] == ""
    rows = raw["results"]
    assert len(rows) == 96
    assert len({row["cell_id"] for row in rows}) == 96
    assert len({row["thread_id"] for row in rows}) == 96
    assert all(row["journal_attempt"] == 1 for row in rows)
    assert all(row["agent_returncode"] == 0 for row in rows)
    assert all(row["command_protocol"]["compliant"] for row in rows)
    assert raw["summary"]["primary_gate"]["conditions"] == {
        "execution_integrity": False,
        "correctness": True,
        "first_check": False,
        "tokens": False,
        "elapsed": False,
        "maintainability": True,
    }
    assert raw["summary"]["primary_gate"]["passed"] is False

    attempts = [attempt for row in rows for attempt in row["public_attempts"]]
    assert len(attempts) == 104
    assert sum(attempt["ok"] for attempt in attempts) == 97
    assert sum(len(attempt["cases"]) for attempt in attempts) == 392
    assert sum(
        case["target"] == "browser"
        for attempt in attempts
        for case in attempt["cases"]
    ) == 98
    assert sum(attempt["cross_target"] is not None for attempt in attempts) == 98
    assert all(row["final_public_check_success"] for row in rows)
    assert all(row["public_execution_ok"] for row in rows)
    assert all(row["transport_integrity_ok"] for row in rows)
    assert all(row["attempt_record_integrity_ok"] for row in rows)

    rust = [row for row in rows if row["language"] == "rust"]
    assert len(rust) == 24
    assert all(not row["read_only_integrity_ok"] for row in rust)
    assert all(not row["workspace_integrity_ok"] for row in rust)
    assert all(row["read_only_integrity_ok"] for row in rows if row["language"] != "rust")
    assert all(row["workspace_integrity_ok"] for row in rows if row["language"] != "rust")
    hidden_failures = [row for row in rows if not row["hidden_success"]]
    assert {row["cell_id"] for row in hidden_failures} == {
        "orchard_irrigation_build__rust__terra-medium__r2",
        "orchard_irrigation_build__rust__terra-medium__r3",
    }


def source() -> dict:
    return {
        "id": SOURCE_ID,
        "label": "Complete frozen iteration 037 raw result and protocol",
        "path": "benchmarks/results/fullstack_agent_037_raw.json",
        "query": {
            "engine": "Python 3.14 and SQLite JSON1",
            "language": "SQL and Python",
            "sql": SQL.read_text(encoding="utf-8"),
            "description": (
                "Deterministic extraction of language, configuration, gate, public-check, "
                "source, hidden-failure, and integrity summaries from all 96 sessions."
            ),
            "executed_at": "2026-08-12T18:17:47.804085Z",
            "tables_used": [
                "benchmarks/results/fullstack_agent_037_raw.json",
                "benchmarks/fullstack_agent_037_protocol.json",
                "benchmarks/fullstack_agent_037_validation.json",
            ],
            "filters": [
                "All 96 frozen cells; no exclusions, retries, or selective reruns.",
                "Four tasks, four languages, two model configurations, three replicates.",
                "All public attempts retained; hidden judgment follows each fresh session.",
                "Strict execution remains failed when a frozen read-only hash changes.",
            ],
            "metric_definitions": [
                "Hidden success: all five withheld cases plus cross-target agreement pass.",
                "First check: the first parent-owned public HTTP/browser attempt succeeds.",
                "Complete session tokens: Codex input plus output tokens; medians include all 24 language rows.",
                "Elapsed seconds: complete fresh-session wall time, excluding dependency preparation.",
                "Exact root: hidden-correct maintenance output changes exactly the preregistered root set and has intact workspace integrity.",
                "Source tokens: o200k_base tokens in final editable application files.",
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
                "hidden_successes": summary["hidden_successes"],
                "hidden_success_rate": summary["hidden_success_rate"],
                "first_check_successes": summary["first_check_successes"],
                "first_check_success_rate": summary["first_check_success_rate"],
                "implementation_successes": sum(row["hidden_success"] for row in implementation),
                "maintenance_successes": sum(row["hidden_success"] for row in maintenance),
                "median_total_tokens": summary["median_total_tokens"],
                "median_elapsed_seconds": summary["median_elapsed_seconds"],
                "median_final_o200k_tokens": median(
                    [row["source"]["totals"]["o200k_base_tokens"] for row in selected]
                ),
                "median_rough_edit_tokens": median(
                    [row["source_edits"]["rough_token_edit_count"] for row in selected]
                ),
                "exact_root_successes": summary["exact_root_successes"],
                "hidden_correct_maintenance_rows": summary["hidden_correct_maintenance_rows"],
                "workspace_integrity_rows": sum(row["workspace_integrity_ok"] for row in selected),
                "repair_turns": summary["repair_turns"],
            }
        )
    return rows


def configuration_rows(raw: dict) -> list[dict]:
    rows = []
    for configuration in ("sol-medium", "terra-medium"):
        for language, label in LABELS.items():
            summary = raw["summary"]["by_configuration"][configuration][language]
            rows.append({"configuration": configuration, "language": label, **summary})
    return rows


def gate_rows() -> list[dict]:
    return [
        {"order": 1, "condition": "Execution integrity", "threshold": "96 unique, single-attempt cells with every protected/read-only hash intact and usable public HTTP/browser execution", "observed": "96/96 unique and public transport valid; Cargo.lock reordered in all 24 Rust workspaces", "result": "FAIL"},
        {"order": 2, "condition": "Hidden correctness", "threshold": "Parley 100% and no lower than every baseline overall, by model, and by kind", "observed": "Parley 24/24; Python 24/24; TypeScript 24/24; Rust 22/24", "result": "PASS"},
        {"order": 3, "condition": "First public check", "threshold": "Parley no lower than the best baseline overall and by task kind", "observed": "Parley 18/24 vs Python 23/24 and TypeScript/Rust 24/24; implementation 6/12 vs best 12/12", "result": "FAIL"},
        {"order": 4, "condition": "Complete session tokens", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "66,686.5 vs Python 59,603.5 overall; Parley also above Python in both model strata", "result": "FAIL"},
        {"order": 5, "condition": "Elapsed time", "threshold": "Parley median no higher than the lowest baseline overall and within each model", "observed": "30.799 s vs TypeScript 23.890 s overall; Parley also above TypeScript in both model strata", "result": "FAIL"},
        {"order": 6, "condition": "Maintainability", "threshold": "Every hidden-correct Parley repair has exact root; rate no lower than baselines", "observed": "Parley/Python/TypeScript 12/12; Rust 0/12 under the frozen workspace-integrity rule", "result": "PASS"},
    ]


def integrity_rows(raw: dict) -> list[dict]:
    rows = raw["results"]
    attempts = [attempt for row in rows for attempt in row["public_attempts"]]
    checks = [
        ("Frozen cells completed", "96/96", True),
        ("Unique cell and thread IDs", f"{len({row['cell_id'] for row in rows})}/96 cells; {len({row['thread_id'] for row in rows})}/96 threads", True),
        ("One journal attempt per cell", f"{sum(row['journal_attempt'] == 1 for row in rows)}/96", True),
        ("Command protocol compliance", f"{sum(row['command_protocol']['compliant'] for row in rows)}/96", True),
        ("Checker and symlink integrity", f"{sum(row['checker_integrity_ok'] and row['symlink_integrity_ok'] for row in rows)}/96", True),
        ("FIFO transport integrity", f"{sum(row['transport_integrity_ok'] for row in rows)}/96", True),
        ("External attempt-record integrity", f"{sum(row['attempt_record_integrity_ok'] for row in rows)}/96", True),
        ("Required public HTTP/browser execution", f"{sum(row['public_execution_ok'] for row in rows)}/96 cells; {len(attempts)} attempts", True),
        ("Final public check", f"{sum(row['final_public_check_success'] for row in rows)}/96", True),
        ("Read-only file integrity", f"{sum(row['read_only_integrity_ok'] for row in rows)}/96; all 24 Rust Cargo.lock files reordered", False),
        ("Hidden judgment", f"{sum(len(row['hidden_judgment']['cases']) for row in rows)}/480 cases plus 96/96 cross-target checks", True),
        ("Repository and provenance stable", f"commit {raw['repository']['commit'][:7]}; post-run revalidation clean", True),
    ]
    return [
        {"order": index, "check": check, "observed": observed, "status": "PASS" if ok else "FAIL"}
        for index, (check, observed, ok) in enumerate(checks, 1)
    ]


def hidden_failure_rows(raw: dict) -> list[dict]:
    result = []
    for row in raw["results"]:
        if row["hidden_success"]:
            continue
        failed = [case["id"] for case in row["hidden_judgment"]["cases"] if not case["pass"]]
        result.append(
            {
                "cell": row["cell_id"],
                "language": LABELS[row["language"]],
                "configuration": row["configuration_id"],
                "task": row["task_id"],
                "failed_cases": ", ".join(failed),
                "cause": "Signed i64::saturating_sub returned -8 instead of clamping at zero",
            }
        )
    return result


def chart(chart_id: str, title: str, subtitle: str, field: str, label: str, value_format: str, question: str, rationale: str, unit: str, sort: str) -> dict:
    return {
        "id": chart_id,
        "title": title,
        "subtitle": subtitle,
        "type": "bar",
        "intent": "comparison",
        "dataset": "languages",
        "encodings": {
            "x": {"field": "language", "type": "nominal", "label": "Language"},
            "y": {"field": field, "type": "quantitative", "label": label, "format": value_format},
            "tooltip": [
                {"field": "sessions", "type": "quantitative", "label": "Sessions"},
                {"field": "hidden_successes", "type": "quantitative", "label": "Hidden successes"},
                {"field": "first_check_successes", "type": "quantitative", "label": "First checks"},
                {"field": "median_final_o200k_tokens", "type": "quantitative", "label": "Median final source tokens"},
            ],
        },
        "xAxisTitle": "Language",
        "yAxisTitle": label,
        "valueFormat": value_format,
        "layout": "full",
        "sourceId": SOURCE_ID,
        "question": question,
        "rationale": rationale,
        "comparisonContext": {"unit": unit, "grain": "language summary across 24 frozen sessions", "denominator": "all 24 sessions per language; no exclusions", "semanticFamily": "fresh-agent full-stack comparison"},
        "palette": {"kind": "sequential", "name": "blue"},
        "labels": {"values": "all"},
        "settings": {"sort": sort, "showValues": True},
    }


def table(table_id: str, title: str, subtitle: str, dataset: str, columns: list[dict], sort_field: str) -> dict:
    return {
        "id": table_id,
        "title": title,
        "subtitle": subtitle,
        "dataset": dataset,
        "columns": columns,
        "defaultSort": {"field": sort_field, "direction": "asc"},
        "density": "dense",
        "layout": "full",
        "sourceId": SOURCE_ID,
    }


def build(raw: dict) -> dict:
    languages = language_rows(raw)
    configurations = configuration_rows(raw)
    gates = gate_rows()
    integrity = integrity_rows(raw)
    failures = hidden_failure_rows(raw)
    source_record = source()
    headline = [{"sessions": 96, "parley_hidden": 24, "parley_first": 18, "public_final": 96, "public_attempts": 104, "strict_gate": 0}]
    cards = [
        {"id": "sessions_card", "description": "All frozen cells completed once.", "dataset": "headline", "metrics": [{"field": "sessions", "label": "Sessions", "format": "number", "unit": "of 96"}], "sourceId": SOURCE_ID},
        {"id": "hidden_card", "description": "Parley passed every hidden judgment.", "dataset": "headline", "metrics": [{"field": "parley_hidden", "label": "Parley hidden-correct", "format": "number", "unit": "of 24"}], "sourceId": SOURCE_ID},
        {"id": "first_card", "description": "All six misses were orchard build attempts.", "dataset": "headline", "metrics": [{"field": "parley_first", "label": "Parley first checks", "format": "number", "unit": "of 24"}], "sourceId": SOURCE_ID},
        {"id": "public_card", "description": "Parent-owned feedback was usable in every final workspace.", "dataset": "headline", "metrics": [{"field": "public_final", "label": "Final public passes", "format": "number", "unit": "of 96"}, {"field": "public_attempts", "label": "Public attempts", "format": "number", "unit": "total"}], "sourceId": SOURCE_ID},
        {"id": "gate_card", "description": "The frozen six-condition claim was not established.", "dataset": "headline", "metrics": [{"field": "strict_gate", "label": "Strict gate", "format": "number", "unit": "of 1"}], "sourceId": SOURCE_ID},
    ]
    charts = [
        chart("correctness_chart", "Hidden assignment success rate", "Five withheld cases plus browser/server agreement; 24 sessions per language.", "hidden_success_rate", "Hidden success rate", "percent", "Which language arms passed the complete hidden judgment?", "A categorical bar displays the two Rust misses while preserving the three perfect arms.", "fraction of 24 sessions", "descending"),
        chart("first_check_chart", "First public check success rate", "First parent-owned HTTP/browser check; higher is better.", "first_check_success_rate", "First-check rate", "percent", "Did Parley match the strongest baseline before repair?", "The four rates directly evaluate the frozen first-check condition.", "fraction of 24 sessions", "descending"),
        chart("tokens_chart", "Median complete session tokens", "Input plus output tokens across all 24 sessions per language; lower is better.", "median_total_tokens", "Median tokens", "compact", "Did Parley match the cheapest complete-session baseline?", "A sorted magnitude comparison directly evaluates the primary token threshold.", "input plus output tokens per session", "ascending"),
        chart("elapsed_chart", "Median fresh-session elapsed time", "Complete wall time across all 24 sessions per language; lower is better.", "median_elapsed_seconds", "Median seconds", "number", "Did Parley match the fastest elapsed baseline?", "A sorted category comparison exposes the Parley–TypeScript gap.", "seconds per session", "ascending"),
        chart("source_chart", "Median final editable-source tokens", "o200k_base count over final editable application files; lower is smaller.", "median_final_o200k_tokens", "Median source tokens", "number", "Did Parley retain a source-representation compactness advantage?", "This secondary chart separates source size from complete agent cost.", "o200k_base tokens per final source", "ascending"),
    ]
    tables = [
        table("gate_table", "Frozen six-condition gate", "All conditions are reported independently; one failure is sufficient for the overall false verdict.", "gates", [{"field": "order", "label": "#", "format": "number"}, {"field": "condition", "label": "Condition", "type": "text"}, {"field": "threshold", "label": "Frozen threshold", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "result", "label": "Result", "type": "text"}], "order"),
        table("language_table", "Complete language-level audit", "All 24 sessions per language, including failures and every repair turn.", "languages", [{"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "median_final_o200k_tokens", "label": "Median source", "format": "number"}, {"field": "exact_root_successes", "label": "Exact roots", "format": "number"}, {"field": "workspace_integrity_rows", "label": "Intact workspaces", "format": "number"}, {"field": "repair_turns", "label": "Repair turns", "format": "number"}], "language"),
        table("configuration_table", "Model-stratified result", "Twelve sessions per model/language cell; medians include every outcome.", "configurations", [{"field": "configuration", "label": "Configuration", "type": "text"}, {"field": "language", "label": "Language", "type": "text"}, {"field": "hidden_successes", "label": "Hidden", "format": "number"}, {"field": "first_check_successes", "label": "First check", "format": "number"}, {"field": "median_total_tokens", "label": "Median tokens", "format": "number"}, {"field": "median_elapsed_seconds", "label": "Median seconds", "format": "number"}, {"field": "exact_root_rate", "label": "Exact-root rate", "format": "percent"}], "configuration"),
        table("integrity_table", "Execution and measurement integrity audit", "Valid controls are retained alongside the single deterministic freeze failure.", "integrity", [{"field": "order", "label": "#", "format": "number"}, {"field": "check", "label": "Check", "type": "text"}, {"field": "observed", "label": "Observed", "type": "text"}, {"field": "status", "label": "Status", "type": "text"}], "order"),
        table("failure_table", "Hidden failures", "Both failures are independent Terra/Rust solutions to the orchard implementation task.", "hidden_failures", [{"field": "cell", "label": "Cell", "type": "text"}, {"field": "failed_cases", "label": "Failed cases", "type": "text"}, {"field": "cause", "label": "Observed cause", "type": "text"}], "cell"),
    ]
    blocks = [
        {"id": "title", "type": "markdown", "layout": "full", "body": f"# {TITLE}"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Technical summary\n\n**Iteration 037 restored valid agent-visible public feedback but still does not establish strict parity or superiority.** All **96/96** frozen sessions ran exactly once. Parley passed **24/24** hidden judgments and **12/12** exact-root repairs, while all **96/96** final workspaces passed parent-owned public HTTP and Chromium checks. Its first-check rate was only **18/24**, its **66,686.5** median complete-session tokens were **11.88% above Python**, and its **30.799 s** median elapsed time was **28.92% above TypeScript**. The overall run is additionally invalid under its frozen execution rule because Cargo canonically relocated an otherwise identical root package block in all **24/24** Rust lockfiles. No row was repaired, excluded, or rerun."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [card["id"] for card in cards]},
        {"id": "verdict", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The transport succeeded; the strict experiment did not\n\nThe parent-owned FIFO checker fixed iteration 036's dominant execution defect. Across **104** public attempts it ran **392** named cases, including **98** real-browser cases and **98** derived cross-target checks; all **96** final public checks passed. The remaining execution failure is narrower but binding: the frozen Rust `Cargo.lock` contained the correct package and dependencies in a noncanonical position. `cargo build` moved that block without changing its content, so read-only integrity failed in every Rust cell. The reference preflight used `cargo metadata --locked --offline`, which did not expose the later build rewrite. Under the preregistered all-six-conditions rule, this is an invalid strict run, not a narrow win."},
        {"id": "gate_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "integrity_block", "type": "table", "layout": "full", "tableId": "integrity_table"},
        {"id": "correctness", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Final correctness was strong and fully measured\n\nParley, Python, and TypeScript each passed **24/24** hidden assignments. Rust passed **22/24**. Both failures were independent Terra orchard implementations that treated signed `i64::saturating_sub` as a clamp to zero: `32 - 40` produced `-8`, leaving one pump cycle active. The public fixtures did not reveal the rain-cancels boundary, while the hidden HTTP, browser, and cross-target checks did. This is valid descriptive evidence about the final artifacts even though the experiment-wide integrity gate is false."},
        {"id": "correctness_chart_block", "type": "chart", "layout": "full", "chartId": "correctness_chart"},
        {"id": "failure_block", "type": "table", "layout": "full", "tableId": "failure_table"},
        {"id": "first", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Parley required more first-pass repair\n\nParley passed **18/24** first public checks, below Python's **23/24** and TypeScript/Rust at **24/24**. All six Parley misses were blank orchard implementations whose first attempt failed to build; each passed after one repair and later passed hidden judgment. One Python orchard session voluntarily ran a second passing check after already passing its first, which is why the report retains **eight** aggregate repair turns despite only **seven** first-check failures."},
        {"id": "first_chart_block", "type": "chart", "layout": "full", "chartId": "first_check_chart"},
        {"id": "language_block", "type": "table", "layout": "full", "tableId": "language_table"},
        {"id": "tokens", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Compact Parley source did not produce the lowest complete-session token cost\n\nParley's **66,686.5** median session tokens were **11.88% above Python's 59,603.5**, failing the frozen best-baseline threshold. The gap repeats under sol-medium (**12.22%**) and terra-medium (**11.24%**). Parley remained below TypeScript by **11.50%** and Rust by **31.83%**, so the result is competitive but not best. Every session and failure remains in the median."},
        {"id": "tokens_chart_block", "type": "chart", "layout": "full", "chartId": "tokens_chart"},
        {"id": "elapsed", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## TypeScript was fastest on the frozen elapsed-time gate\n\nParley's **30.799 s** median was **28.92% above TypeScript's 23.890 s**. The same ordering holds within sol-medium (**33.75%**) and terra-medium (**25.03%**). Python's overall median was 28.694 s and Rust's was 37.740 s. These are local wall-time measurements of the complete working-feedback protocol, not universal runtime-performance results."},
        {"id": "elapsed_chart_block", "type": "chart", "layout": "full", "chartId": "elapsed_chart"},
        {"id": "source", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Parley retained a substantial source-compactness advantage\n\nThe median final editable application contained **552 o200k tokens** in Parley, versus **839 TypeScript, 926 Python, and 1,353 Rust**. That is **34.21%**, **40.39%**, and **59.20%** smaller respectively. It is a real secondary representation result, but it cannot substitute for the preregistered complete-session metric where Python remained cheaper."},
        {"id": "source_chart_block", "type": "chart", "layout": "full", "chartId": "source_chart"},
        {"id": "configuration_block", "type": "table", "layout": "full", "tableId": "configuration_table"},
        {"id": "scope", "type": "markdown", "layout": "full", "body": "## Scope and metrics\n\nThe frozen population is two blank-logic implementations and two seeded maintenance tasks, crossed with four languages, two medium-reasoning model configurations, and three replicates. Each cell is one fresh session. Public feedback uses a protected client and parent-owned FIFO broker; successful attempts execute three HTTP cases, one Chromium case, and a derived agreement check. Hidden success requires five withheld cases plus browser/server agreement. Complete tokens are Codex input plus output tokens. Exact-root quality is defined among hidden-correct maintenance rows and requires intact workspace integrity."},
        {"id": "method", "type": "markdown", "layout": "full", "body": "## Methodology and frozen boundaries\n\nThe parent transport was independently proven before any task existed. Task/case semantics were then frozen at `b3ddad8`, the balanced protocol at `6ef336a`, the validated harness at `10664d5`, and the zero-session execution boundary at `5d38c77`. Clean-room reference validation passed **16/16** language/task cells, **144/144** named cases plus **16/16** cross-target checks; every broken seed built and failed the public set. The measured matrix ran with four workers, immutable external journals, one unique thread per cell, and post-run repository/provenance revalidation."},
        {"id": "limits", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Limitations and robustness\n\nThe dominant limitation is the noncanonical Rust lock freeze: all Rust workspace-integrity and exact-root outcomes fail mechanically even though the package contents did not change. The public and hidden evaluators themselves are complete, and checker hashes, FIFO identities, attempt records, symlink policy, command policy, journals, repository state, and toolchain provenance all passed. The shared positive-number guard remains infrastructure applied identically before every candidate stack. Beyond execution, the corpus has four synthetic applications, one machine, two models, one reasoning level, and no production database, authentication, accessibility, load, deployment, package-ecosystem, or long-term evolution evidence."},
        {"id": "next", "type": "markdown", "layout": "full", "body": "## Next phase: make builds prove read-only stability before another freeze\n\n1. Preserve iteration 037 unchanged and never rerun its corpus.\n2. Generate the next Rust lockfile canonically from the final manifest instead of relocating a package block textually.\n3. Extend clean-room validation to hash every protected/read-only file after the exact release and debug build paths used in measurement.\n4. Add a regression that fails on any post-build lock rewrite, even when `cargo metadata --locked --offline` is stable.\n5. Freeze an independent 038 corpus only after the corrected execution mechanism passes, then target the observed Parley orchard first-build burden without training on 037 cases."},
        {"id": "questions", "type": "markdown", "layout": "full", "body": "## Further questions\n\n- Can Parley preserve 24/24 hidden correctness while matching TypeScript's first-check rate on independently named implementation tasks?\n- Which fixed context or build diagnostics explain Parley's approximately 12% complete-token gap to Python?\n- Does Parley's 34–59% source compactness advantage persist in larger applications with persistence, authentication, and deployment concerns?\n- Does Rust's signed saturation misconception recur under another model/corpus, or was it specific to this orchard boundary?"},
    ]
    return {
        "surface": "report",
        "manifest": {"version": 1, "surface": "report", "title": TITLE, "description": "Preregistered 96-session comparison with valid public feedback; strict result invalidated by a noncanonical Rust lock freeze and failed product-efficiency gates.", "generatedAt": raw["generated_at"], "cards": cards, "charts": charts, "tables": tables, "sources": [source_record], "blocks": blocks},
        "snapshot": {"version": 1, "status": "ready", "generatedAt": raw["generated_at"], "datasets": {"headline": headline, "languages": languages, "configurations": configurations, "gates": gates, "integrity": integrity, "hidden_failures": failures}},
        "sources": [source_record],
        "package_info": {"root": "benchmarks/results", "manifestPath": OUTPUT.name, "snapshotPath": "fullstack_agent_037_raw.json", "originUrl": "artifact://parley-fullstack-agent-037"},
    }


def main() -> int:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate(raw, protocol)
    artifact = build(raw)
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "raw_sha256": sha256(RAW), "protocol_sha256": sha256(PROTOCOL), "validation_sha256": sha256(VALIDATION), "datasets": {key: len(rows) for key, rows in artifact["snapshot"]["datasets"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
