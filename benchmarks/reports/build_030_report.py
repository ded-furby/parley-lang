#!/usr/bin/env python3
"""Build the canonical report artifact for iteration 030's scaling curve."""

from __future__ import annotations

import copy
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW_NAME = "agent_scaling_030_protocol_v1_v0.3.155.json"
RAW = BENCHMARKS / "results" / RAW_NAME
TASK_MANIFEST = BENCHMARKS / "agent_tasks_historical_029.json"
PROTOCOL = BENCHMARKS / "bundle_protocol_030.json"
TEMPLATE = REPORTS / "029-historical-diagnosis-rust-parity.artifact.json"
STEM = "030-ninety-session-scaling-mechanism"
GENERATED_AT = "2026-08-04T20:01:25Z"
SOURCE_ID = "scaling_results"
LANGUAGES = ("parley", "python", "rust")
SCALES = (1, 2, 4, 8)


def display_language(language: str) -> str:
    return {"parley": "Parley", "python": "Python", "rust": "Rust"}[language]


def median(values) -> float:
    return float(statistics.median(values))


def reciprocal_fit(scale_rows: dict[tuple[int, str], dict], language: str) -> dict:
    xs = [1.0 / size for size in SCALES]
    ys = [scale_rows[(size, language)]["median_total_tokens_per_task"] for size in SCALES]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / sum(
        (x - x_mean) ** 2 for x in xs
    )
    intercept = y_mean - slope * x_mean
    predicted = [intercept + slope * x for x in xs]
    residual_sum = sum((y - estimate) ** 2 for y, estimate in zip(ys, predicted))
    total_sum = sum((y - y_mean) ** 2 for y in ys)
    return {
        "language": display_language(language),
        "residual_task_tokens": round(intercept, 3),
        "fixed_session_tokens": round(slope, 3),
        "r_squared": round(1.0 - residual_sum / total_sum, 8),
        "size8_observed": round(ys[-1], 4),
        "size8_fitted": round(predicted[-1], 4),
        "size8_residual": round(ys[-1] - predicted[-1], 4),
    }


def build_datasets(raw: dict, tasks: dict) -> dict[str, list[dict]]:
    rows = raw["results"]
    roots = tasks["predeclared_analysis"]["root_cause_files"]
    scale_rows = {
        (row["bundle_size"], row["language"]): row
        for row in raw["summary"]["by_scale"]
    }
    fits = {language: reciprocal_fit(scale_rows, language) for language in LANGUAGES}
    size8 = {language: scale_rows[(8, language)] for language in LANGUAGES}

    def percent_gap(metric: str, baseline: str) -> float:
        return 100.0 * (size8["parley"][metric] / size8[baseline][metric] - 1.0)

    headline = [{
        "sessions": len(rows),
        "assignments": sum(row["task_count"] for row in rows),
        "hidden_successes": sum(row["hidden_task_successes"] for row in rows),
        "first_successes": sum(row["first_public_task_successes"] for row in rows),
        "repairs": sum(row["repair_turns"] for row in rows),
        "gate_conditions_passed": sum(raw["summary"]["strict_gate"]["conditions"].values()),
        "parley_root_fixes": sum(
            roots[task_id]["parley"] in task["changed_files"]
            for row in rows if row["language"] == "parley"
            for task_id, task in row["task_results"].items()
        ),
        "token_gap_python_percent": round(percent_gap("median_total_tokens_per_task", "python"), 2),
        "token_gap_rust_percent": round(percent_gap("median_total_tokens_per_task", "rust"), 2),
        "elapsed_gap_python_percent": round(percent_gap("median_elapsed_seconds_per_task", "python"), 2),
        "elapsed_gap_rust_percent": round(percent_gap("median_elapsed_seconds_per_task", "rust"), 2),
    }]

    scale_summary = []
    for size in SCALES:
        for language in LANGUAGES:
            row = scale_rows[(size, language)]
            scale_summary.append({
                "bundle_size": str(size),
                "bundle_size_number": size,
                "language": display_language(language),
                "sessions": row["sessions"],
                "assignments": row["assigned_tasks"],
                "hidden_successes": row["hidden_task_successes"],
                "first_successes": row["first_public_task_successes"],
                "repairs": row["repair_turns"],
                "median_tokens_task": row["median_total_tokens_per_task"],
                "weighted_tokens_task": row["weighted_total_tokens_per_task"],
                "median_input_tokens_task": row["median_input_tokens_per_task"],
                "median_output_tokens_task": row["median_output_tokens_per_task"],
                "median_seconds_task": row["median_elapsed_seconds_per_task"],
                "prompt_chars_task": row["median_prompt_chars_per_task"],
                "source_tokens_task": row["median_source_rough_tokens_per_task"],
                "context_tokens_task": row.get("median_context_source_rough_tokens_per_task", 0),
                "edit_tokens_task": row["median_source_edit_rough_tokens_per_task"],
            })

    gaps = []
    for size in SCALES:
        parley = scale_rows[(size, "parley")]
        for baseline in ("python", "rust"):
            other = scale_rows[(size, baseline)]
            p_tokens = parley["median_total_tokens_per_task"]
            b_tokens = other["median_total_tokens_per_task"]
            p_seconds = parley["median_elapsed_seconds_per_task"]
            b_seconds = other["median_elapsed_seconds_per_task"]
            gaps.append({
                "bundle_size": str(size),
                "bundle_size_number": size,
                "baseline": display_language(baseline),
                "token_gap": round(p_tokens - b_tokens, 4),
                "token_gap_percent": round(100.0 * (p_tokens / b_tokens - 1.0), 4),
                "elapsed_gap": round(p_seconds - b_seconds, 4),
                "elapsed_gap_percent": round(100.0 * (p_seconds / b_seconds - 1.0), 4),
            })

    fit_gap = []
    for baseline in ("python", "rust"):
        fit_gap.extend([
            {
                "baseline": display_language(baseline),
                "component": "Fixed session",
                "token_gap": round(
                    fits["parley"]["fixed_session_tokens"] - fits[baseline]["fixed_session_tokens"], 3
                ),
            },
            {
                "baseline": display_language(baseline),
                "component": "Residual per task",
                "token_gap": round(
                    fits["parley"]["residual_task_tokens"] - fits[baseline]["residual_task_tokens"], 3
                ),
            },
        ])

    session_detail = []
    for row in rows:
        session_detail.append({
            "bundle_size": row["bundle_size"],
            "bundle": row["bundle_id"],
            "replicate": row["replicate"],
            "language": display_language(row["language"]),
            "tasks": row["task_count"],
            "hidden_successes": row["hidden_task_successes"],
            "first_successes": row["first_public_task_successes"],
            "checks": row["public_check_attempts"],
            "repairs": row["repair_turns"],
            "tokens_task": round(row["total_tokens_per_task"], 4),
            "input_tokens_task": round(row["input_tokens_per_task"], 4),
            "output_tokens_task": round(row["output_tokens_per_task"], 4),
            "seconds_task": round(row["elapsed_seconds_per_task"], 4),
            "changed_files_task": round(row["changed_files_per_task"], 4),
            "thread": row["thread_id"],
        })

    root_audit = []
    command_audit = []
    for language in LANGUAGES:
        selected = [row for row in rows if row["language"] == language]
        task_rows = [
            (task_id, task)
            for row in selected
            for task_id, task in row["task_results"].items()
        ]
        root_audit.append({
            "language": display_language(language),
            "sessions": len(selected),
            "assignments": len(task_rows),
            "root_fixes": sum(roots[task_id][language] in task["changed_files"] for task_id, task in task_rows),
            "one_file_fixes": sum(len(task["changed_files"]) == 1 for _, task in task_rows),
            "final_variants": sum(
                len({
                    row["task_results"][task_id]["source_text"]
                    for row in selected if task_id in row["task_results"]
                })
                for task_id in roots
            ),
            "read_only_preserved": sum(len(task["context_source_files"]) for _, task in task_rows),
        })
        messages = Counter(len(row["agent_messages"]) for row in selected)
        command_audit.append({
            "language": display_language(language),
            "sessions": len(selected),
            "fresh": sum(row["fresh_ephemeral_session"] for row in selected),
            "sources_first": sum(
                [event["command"] for event in row["command_events"]]
                == ["/bin/zsh -lc ./sources", "/bin/zsh -lc ./check"]
                for row in selected
            ),
            "one_check": sum(row["public_check_attempts"] == 1 for row in selected),
            "protocol_ok": sum(row["command_protocol_compliant"] for row in selected),
            "integrity_ok": sum(row["check_integrity_ok"] for row in selected),
            "zero_exit": sum(row["agent_returncode"] == 0 for row in selected),
            "file_change_actions": len(selected),
            "three_messages": messages[3],
            "four_messages": messages[4],
        })

    task_detail = []
    for size in SCALES:
        for language in LANGUAGES:
            selected = [
                row for row in rows
                if row["bundle_size"] == size and row["language"] == language
            ]
            for task_id, root_map in roots.items():
                appearances = [row["task_results"][task_id] for row in selected if task_id in row["task_results"]]
                task_detail.append({
                    "bundle_size": size,
                    "repository": appearances[0]["task_title"],
                    "language": display_language(language),
                    "appearances": len(appearances),
                    "first_successes": sum(task["first_public_check_success"] for task in appearances),
                    "hidden_successes": sum(task["hidden_success"] for task in appearances),
                    "root_fixes": sum(root_map[language] in task["changed_files"] for task in appearances),
                    "final_tokens": round(median(task["source_rough_tokens"] for task in appearances), 2),
                    "edit_tokens": round(median(task["source_edit_rough_tokens"] for task in appearances), 2),
                })

    source_stage = []
    for language in LANGUAGES:
        selected = [row for row in rows if row["bundle_size"] == 8 and row["language"] == language]
        source_stage.extend([
            {
                "language": display_language(language),
                "stage": "Seed",
                "rough_tokens_task": round(median(row["seed_source_rough_tokens_per_task"] for row in selected), 4),
            },
            {
                "language": display_language(language),
                "stage": "Final",
                "rough_tokens_task": round(median(row["source_rough_tokens_per_task"] for row in selected), 4),
            },
        ])

    return {
        "headline": headline,
        "scale_summary": scale_summary,
        "gap_by_scale": gaps,
        "fit_summary": [fits[language] for language in LANGUAGES],
        "fit_gap": fit_gap,
        "session_detail": session_detail,
        "root_audit": root_audit,
        "command_audit": command_audit,
        "task_detail": task_detail,
        "source_stage": source_stage,
    }


def metric_card(card_id: str, description: str, label: str, field: str, unit: str | None = None, signed: bool = False) -> dict:
    metric = {"label": label, "field": field, "format": "number"}
    if unit:
        metric["unit"] = unit
    if signed:
        metric["signed"] = True
    return {"id": card_id, "description": description, "dataset": "headline", "sourceId": SOURCE_ID, "metrics": [metric]}


def chart(chart_id: str, title: str, subtitle: str, dataset: str, x: str, y: str, color: str, x_label: str, y_label: str, question: str, rationale: str, unit: str, grain: str, denominator: str, value_format: str = "number") -> dict:
    return {
        "id": chart_id,
        "title": title,
        "subtitle": subtitle,
        "intent": "comparison",
        "question": question,
        "rationale": rationale,
        "comparisonContext": {"unit": unit, "grain": grain, "denominator": denominator, "semanticFamily": title.lower()},
        "type": "bar",
        "dataset": dataset,
        "sourceId": SOURCE_ID,
        "encodings": {
            "x": {"field": x, "type": "nominal", "label": x_label},
            "y": {"field": y, "type": "quantitative", "label": y_label, "format": value_format},
            "color": {"field": color, "type": "nominal", "label": color.replace("_", " ").title()},
        },
        "xAxisTitle": x_label,
        "yAxisTitle": y_label,
        "valueFormat": value_format,
        "layout": "full",
    }


def table(table_id: str, title: str, subtitle: str, dataset: str, columns: list[tuple[str, str, str]], sort_field: str) -> dict:
    return {
        "id": table_id,
        "title": title,
        "subtitle": subtitle,
        "dataset": dataset,
        "sourceId": SOURCE_ID,
        "defaultSort": {"field": sort_field, "direction": "asc"},
        "density": "dense",
        "layout": "full",
        "columns": [
            {"field": field, "label": label, **({"type": "text"} if kind == "text" else {"format": kind})}
            for field, label, kind in columns
        ],
    }


def markdown(block_id: str, body: str, sourced: bool = True) -> dict:
    block = {"id": block_id, "type": "markdown", "layout": "full", "body": body}
    if sourced:
        block["sourceId"] = SOURCE_ID
    return block


def build_artifact(raw: dict, datasets: dict[str, list[dict]]) -> dict:
    artifact = copy.deepcopy(json.loads(TEMPLATE.read_text(encoding="utf-8")))
    manifest = artifact["manifest"]
    manifest.update({
        "title": "Ninety-Session Scaling Mechanism — Iteration 030",
        "description": "Preregistered size 1/2/4/8 diagnosis scaling curve over 90 fresh sessions.",
        "generatedAt": GENERATED_AT,
        "sources": [{"id": SOURCE_ID, "label": "Frozen iteration 030 scaling results", "path": f"{STEM}.sql"}],
    })
    manifest["cards"] = [
        metric_card("sessions_card", "Every planned fresh session, retained once.", "Fresh sessions", "sessions"),
        metric_card("hidden_card", "Assignments passing every withheld case.", "Hidden success", "hidden_successes", "of 192"),
        metric_card("first_card", "Assignments passing the untouched first check.", "First-check success", "first_successes", "of 192"),
        metric_card("repair_card", "Additional public-check turns across all sessions.", "Repairs", "repairs"),
        metric_card("gate_card", "Strict size-eight parity conditions passed.", "Gate conditions", "gate_conditions_passed", "of 4"),
        metric_card("root_card", "Parley assignments modifying the frozen root-defect file.", "Parley root fixes", "parley_root_fixes", "of 64"),
        metric_card("python_gap_card", "Size-eight Parley token delta relative to Python.", "Token delta vs Python", "token_gap_python_percent", "%", True),
        metric_card("rust_gap_card", "Size-eight Parley token delta relative to Rust; negative is lower.", "Token delta vs Rust", "token_gap_rust_percent", "%", True),
    ]
    manifest["charts"] = [
        chart("scale_chart", "Token effort across workload sizes", "Median reported tokens per assigned repository at each frozen bundle size.", "scale_summary", "bundle_size", "median_tokens_task", "language", "Repositories per session", "Tokens per repository", "How does task bundling change reported agent effort?", "Grouped scale bars expose the steep amortization curve while preserving all language medians.", "reported tokens per repository", "language-size median", "two complete task appearances per language/scale", "compact"),
        chart("gap_chart", "Parley token gap at each workload size", "Positive values mean Parley uses more tokens; negative values mean Parley uses fewer.", "gap_by_scale", "bundle_size", "token_gap", "baseline", "Repositories per session", "Parley minus baseline tokens", "Does the absolute baseline gap shrink with bundling?", "Direct deltas reveal fixed overhead more clearly than the common steep scale curve.", "reported token delta per repository", "baseline-size comparison", "same frozen assignments at each scale", "compact"),
        chart("fit_chart", "Estimated token-gap components", "Descriptive fit: median tokens/task = residual task cost + fixed session cost / bundle size.", "fit_gap", "baseline", "token_gap", "component", "Baseline", "Parley minus baseline tokens", "Which fitted component explains the remaining gap?", "The two-component delta separates amortizable session context from the residual per-task estimate.", "estimated reported-token delta", "baseline-fit component", "four observed workload sizes", "compact"),
        chart("elapsed_chart", "Elapsed effort across workload sizes", "Median seconds per assigned repository; all sessions are repair-free.", "scale_summary", "bundle_size", "median_seconds_task", "language", "Repositories per session", "Seconds per repository", "Does bundling also amortize wall-clock effort?", "Elapsed medians test whether the token mechanism is reflected in actual session time.", "seconds per repository", "language-size median", "two complete task appearances per language/scale"),
        chart("source_chart", "Seed and final editable source at size eight", "Median rough lexical tokens per assigned repository.", "source_stage", "language", "rough_tokens_task", "stage", "Language", "Rough source tokens per repository", "How compact is the code the agent reads and leaves behind?", "Seed/final bars isolate editable source size from fixed instruction and tool context.", "rough source tokens per repository", "language-stage median", "two size-eight sessions per language"),
    ]
    manifest["tables"] = [
        table("scale_table", "Complete scale summary", "All twelve language-size cells; no exclusions or reruns.", "scale_summary", [
            ("bundle_size_number", "Size", "number"), ("language", "Language", "text"), ("sessions", "Sessions", "number"), ("assignments", "Assignments", "number"), ("first_successes", "First", "number"), ("hidden_successes", "Hidden", "number"), ("repairs", "Repairs", "number"), ("median_tokens_task", "Tokens/repo", "number"), ("median_seconds_task", "Seconds/repo", "number"), ("prompt_chars_task", "Prompt chars/repo", "number"), ("source_tokens_task", "Final source", "number"), ("edit_tokens_task", "Edit size", "number"),
        ], "bundle_size_number"),
        table("fit_table", "Reciprocal-size fit", "Ordinary least squares over four language medians; descriptive, not causal.", "fit_summary", [
            ("language", "Language", "text"), ("residual_task_tokens", "Residual task", "number"), ("fixed_session_tokens", "Fixed session", "number"), ("r_squared", "R²", "number"), ("size8_observed", "Size-8 observed", "number"), ("size8_fitted", "Size-8 fitted", "number"), ("size8_residual", "Residual", "number"),
        ], "language"),
        table("root_table", "Root-cause and patch-scope audit", "Every assignment changes exactly one predeclared root-defect file.", "root_audit", [
            ("language", "Language", "text"), ("sessions", "Sessions", "number"), ("assignments", "Assignments", "number"), ("root_fixes", "Root fixes", "number"), ("one_file_fixes", "One-file fixes", "number"), ("final_variants", "Final variants", "number"), ("read_only_preserved", "Read-only preserved", "number"),
        ], "language"),
        table("command_table", "Fresh-session and action-graph audit", "Protected source dump, one file-change action, then one successful check.", "command_audit", [
            ("language", "Language", "text"), ("sessions", "Sessions", "number"), ("fresh", "Fresh", "number"), ("sources_first", "Sources → check", "number"), ("one_check", "One check", "number"), ("protocol_ok", "Protocol", "number"), ("integrity_ok", "Integrity", "number"), ("zero_exit", "Zero exit", "number"), ("file_change_actions", "File changes", "number"), ("three_messages", "3 messages", "number"), ("four_messages", "4 messages", "number"),
        ], "language"),
        table("task_table", "Task-level balance and correctness", "Every task appears twice per language at every scale; all 96 rows are retained.", "task_detail", [
            ("bundle_size", "Size", "number"), ("repository", "Repository change", "text"), ("language", "Language", "text"), ("appearances", "Appearances", "number"), ("first_successes", "First", "number"), ("hidden_successes", "Hidden", "number"), ("root_fixes", "Root fixes", "number"), ("final_tokens", "Final source", "number"), ("edit_tokens", "Edit size", "number"),
        ], "bundle_size"),
        table("session_table", "Complete 90-session audit", "Every unique thread, token count, timing, check, and patch-scope row.", "session_detail", [
            ("bundle_size", "Size", "number"), ("bundle", "Bundle", "text"), ("replicate", "Rep", "number"), ("language", "Language", "text"), ("tasks", "Tasks", "number"), ("first_successes", "First", "number"), ("hidden_successes", "Hidden", "number"), ("checks", "Checks", "number"), ("repairs", "Repairs", "number"), ("tokens_task", "Tokens/repo", "number"), ("seconds_task", "Seconds/repo", "number"), ("changed_files_task", "Files/repo", "number"), ("thread", "Thread", "text"),
        ], "bundle_size"),
    ]

    blocks = [
        markdown("title", "# Ninety-Session Scaling Mechanism — Iteration 030", False),
        markdown("summary", "## Technical summary\n\n**The confirmation is clean and explains the benchmark mechanism.** All 90 fresh sessions and 192 assignments pass first check, hidden judgment, command protocol, and integrity with zero repairs. At size eight, Parley uses **8,344.00 tokens/repository**, 3.53% above Python's 8,059.56 and 1.93% below Rust's 8,508.31. It takes 4.5740 seconds/repository versus Python's 4.0855 and Rust's 5.1263. The strict better-baseline gate remains 2/4; the separate 64/64 Parley root-cause condition passes."),
        markdown("scope", "## What this confirmation measures\n\nThe exact iteration-029 corpus is replayed at bundle sizes 1, 2, 4, and 8. Every task appears exactly twice per language at every scale. Per-language session counts are 16, 8, 4, and 2, giving 90 fresh sessions and 192 independently hidden-judged repository assignments. The compiler, task files, runner, model, and 1,519-character instruction are frozen before output."),
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": ["sessions_card", "hidden_card", "first_card", "repair_card", "gate_card", "root_card", "python_gap_card", "rust_gap_card"]},
        markdown("reliability", "## Correctness and diagnosis quality are perfect\n\nEvery assignment passes the untouched first public check and all hidden cases. Each patch changes exactly one file, and all 192 patches touch the predeclared root-defect location. There is no repair turn, timeout, nonzero agent exit, runner error, protocol violation, integrity failure, excluded row, or selective rerun."),
        {"id": "scale_table_block", "type": "table", "tableId": "scale_table", "layout": "full"},
        markdown("scale_read", "## Bundling amortizes the dominant cost\n\nTokens per repository fall by roughly 85% from size one to size eight for every language because instruction, model, and tool-session context is paid once per bundle. The curves are almost parallel: Parley moves from 55.30k to 8.34k, Python from 53.24k to 8.06k, and Rust from 53.94k to 8.51k. Read each group at a common bundle size; comparisons across sizes describe amortization, not easier tasks."),
        {"id": "scale_chart_block", "type": "chart", "chartId": "scale_chart", "layout": "full"},
        markdown("gap_read", "## The Python gap shrinks in absolute terms but does not cross\n\nParley minus Python falls from 2,058 tokens/repository at size one to 284 at size eight, yet the percentage stays near 3.5–4.1%. Against Rust, the absolute gap falls from +1,354 to −164 and crosses between sizes four and eight. This is strong evidence that fixed Parley session context explains the Rust crossover; it does not establish Python parity."),
        {"id": "gap_chart_block", "type": "chart", "chartId": "gap_chart", "layout": "full"},
        markdown("fit_read", "## The reciprocal-size fit separates fixed and residual cost\n\nFor each language, ordinary least squares fits `tokens/task = residual task cost + fixed session cost / bundle size` with R² above 0.99999. Relative to Python, Parley carries an estimated **2,009.53 extra fixed tokens/session** and **74.36 extra tokens/task**; both terms are positive, so this fit predicts no crossover. Relative to Rust, Parley carries 1,677.02 extra fixed tokens/session but saves 287.74 tokens/task, implying a descriptive crossover near 5.83 tasks/session. The fit summarizes four aggregate medians and is not a causal model."),
        {"id": "fit_chart_block", "type": "chart", "chartId": "fit_chart", "layout": "full"},
        {"id": "fit_table_block", "type": "table", "tableId": "fit_table", "layout": "full"},
        markdown("elapsed_read", "## Elapsed time tells the same directional story\n\nAt size eight, Parley's 4.5740 seconds/repository is **10.78% faster than Rust** and 11.96% slower than Python. All timing cells are repair-free, so the result is not caused by additional compile/check loops. Two size-eight sessions per language are enough for the preregistered directional curve, not a population timing claim."),
        {"id": "elapsed_chart_block", "type": "chart", "chartId": "elapsed_chart", "layout": "full"},
        markdown("source_read", "## Source size explains the non-amortizing remainder\n\nAt size eight, median final editable source is 191.63 rough tokens/repository for Parley, 169.44 for Python, and 322.25 for Rust. Equal read-only context is 88.75 rough tokens/repository. The manifest's eight raw context files total 3,614 characters/47 lines; the runner records 3,622/55 after inserting one join newline per task. That disclosed bookkeeping difference is identical across languages and changes no file, prompt evidence, or judgment. Parley is substantially more compact than Rust but modestly larger than Python, matching the signs of the fitted residual task costs. This is a language/readability tradeoff in the current corpus, not a recurring semantic failure."),
        {"id": "source_chart_block", "type": "chart", "chartId": "source_chart", "layout": "full"},
        markdown("root_read", "## Root-cause quality survives all four scales\n\nParley, Python, and Rust each modify the frozen root-defect file in 64/64 assignments, always with one changed file. Across all scales, Parley has eight distinct final task solutions, Python nine, and Rust ten; the additional baseline variants are formatting-equivalent. All 384 read-only issue/test exposures remain preserved."),
        {"id": "root_table_block", "type": "table", "tableId": "root_table", "layout": "full"},
        markdown("action_read", "## The action graph is controlled\n\nEvery session runs exactly `/bin/zsh -lc ./sources`, performs one file-change action, then runs exactly `/bin/zsh -lc ./check`. Seventy-five sessions contain four agent messages and fifteen contain three; the shorter shape only omits the message between file completion and the check. The optional-message split is Parley 8/22, Python 4/26, and Rust 3/27 for three/four messages. No language performs an extra command, edit action, check, or repair, so message phrasing—not workflow depth—is the only event-shape variation."),
        {"id": "command_table_block", "type": "table", "tableId": "command_table", "layout": "full"},
        markdown("task_read", "## Every task is balanced at every scale\n\nThe task table retains all 96 language-size-task aggregates. Each row has two appearances, two first-check passes, two hidden passes, and two root fixes. This balance prevents one mechanism, language, or bundle partition from receiving more measured work."),
        {"id": "task_table_block", "type": "table", "tableId": "task_table", "layout": "full"},
        markdown("replication", "## Size-eight direction replicates iteration 029\n\nIteration 029 reported Parley/Python/Rust medians of 8,408.56/8,034.69/8,489.06 tokens and 4.5455/3.9298/5.0027 seconds per repository. The independent size-eight cells here report 8,344.00/8,059.56/8,508.31 and 4.5740/4.0855/5.1263. Both iterations place Parley between Python and Rust on tokens and elapsed time; neither supports Python-and-Rust parity."),
        markdown("integrity", "## All raw evidence is retained\n\nThe complete session table exposes every unique thread, cell, check count, token total, elapsed time, and changed-file rate. Ninety of ninety sessions are fresh, exit zero, preserve checker/context hashes, obey the command boundary, pass the first check, and pass hidden judgment. Raw JSON remains the authority for prompts, event streams, final source, hidden-case outputs, and per-session usage."),
        {"id": "session_table_block", "type": "table", "tableId": "session_table", "layout": "full"},
        markdown("method", "## Frozen method and integrity\n\n- **Matrix:** sizes 1/2/4/8 × three languages × two complete task appearances = 90 sessions and 192 assignments; seed `20260823`.\n- **Toolchain:** pinned Parley 0.3.155, `gpt-5.6-sol` medium, Codex CLI 0.146.0.\n- **Corpus:** exact iteration-029 task manifest, SHA `50e55b98…`; corpus checkpoint `59ff991…`.\n- **Protocol:** committed before output at `8b9f7e0`; SHA `1eae4604…`.\n- **Instruction:** unchanged 1,519-character skill, SHA `6ca098e4…`; the one allowed compression experiment remains closed.\n- **Result:** raw SHA `ab49ad72…`; every planned cell ran once and is retained."),
        markdown("limitations", "## Limits and robustness\n\nThe task mechanisms are historically grounded, but the cross-language fixtures are synthetic, deterministic, and small. They do not reproduce mature dependency graphs, repository history, services, concurrency, or ambiguous multi-cause failures. Reported tokens include full model context over tool turns; source/context/edit tokens are lexical estimates. The reciprocal fit has only four scale medians and should be read as a compact description, not causal identification or asymptotic truth."),
        markdown("boundary", "## No compiler or instruction change follows\n\nParley records zero parse, type, runtime, hidden, diagnosis, root-location, or draft failures across 64 assignments. The remaining Python gap is mostly fixed session context plus a modest source-size remainder—not a repeated language defect. Adding syntax to shave benchmark tokens would violate the general-usefulness boundary. Parley stays at v0.3.155, and the instruction stays byte-for-byte frozen."),
        markdown("decision", "## Decision and next experiment\n\n1. Preserve iteration 030 unchanged as a clean 90-session mechanism result: strict parity 2/4, root-cause condition passed.\n2. Treat Rust efficiency parity as confirmed for diagnosis bundles of roughly six or more independent tasks; do not claim Python parity.\n3. Make no syntax, compiler, diagnostic, prompt, or skill change from this evidence.\n4. Move to genuinely deeper project episodes where dependency navigation, state reconstruction, and multi-file reasoning dominate fixed instruction cost.\n5. Predeclare those episodes and root-cause criteria before output; accept any future language change only if failures recur across independent projects and the design is generally useful, semantically consistent, and maintainable."),
        markdown("questions", "## Further questions\n\n- Does Parley's lower residual cost than Rust persist when one project contains deeper dependency navigation rather than eight independent fixtures?\n- Can mature project episodes erase the small Python residual without changing instructions or selecting Parley-favorable tasks?\n- Which failure mechanisms, if any, recur broadly enough to justify a language design review?", False),
    ]
    manifest["blocks"] = blocks
    artifact["snapshot"] = {"version": 1, "generatedAt": GENERATED_AT, "status": "ready", "datasets": datasets}
    artifact["sources"] = [{
        "id": SOURCE_ID,
        "label": "Frozen iteration 030 ninety-session scaling results",
        "path": f"{STEM}.sql",
        "query": {
            "engine": "SQLite JSON1 + Python statistics",
            "query": f"python3 benchmarks/reports/build_030_report.py && sqlite3 ':memory:' < benchmarks/reports/{STEM}.sql",
            "description": "Reproducible aggregation of all 90 sessions, 192 hidden judgments, four workload sizes, reciprocal-size fits, event-order integrity, and frozen root-cause locations.",
            "executed_at": GENERATED_AT,
            "language": "SQL / Python",
            "metric_definitions": [
                "Tokens per repository: reported session input plus output tokens divided by assigned repositories.",
                "First success: repository passes in its untouched first public bundle check.",
                "Hidden success: final repository passes every withheld stdout case.",
                "Root-cause repair: final patch modifies the defect file frozen before measured output.",
                "Fixed session fit: OLS slope for median tokens/repository against reciprocal bundle size.",
                "Residual task fit: OLS intercept for median tokens/repository against reciprocal bundle size.",
            ],
        },
    }]
    artifact["package_info"] = {
        "root": "benchmarks/results",
        "manifestPath": f"{STEM}.artifact.json",
        "snapshotPath": RAW_NAME,
        "originUrl": "artifact://parley-scaling-mechanism-030",
    }
    return artifact


def build_sql() -> str:
    return f""".mode list
.separator |

CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/{RAW_NAME}'));

CREATE TEMP VIEW runs AS
SELECT
  CAST(json_extract(run.value, '$.bundle_size') AS INTEGER) AS bundle_size,
  json_extract(run.value, '$.bundle_id') AS bundle_id,
  CAST(json_extract(run.value, '$.replicate') AS INTEGER) AS replicate,
  json_extract(run.value, '$.language') AS language,
  CAST(json_extract(run.value, '$.task_count') AS INTEGER) AS task_count,
  CAST(json_extract(run.value, '$.hidden_task_successes') AS INTEGER) AS hidden_successes,
  CAST(json_extract(run.value, '$.first_public_task_successes') AS INTEGER) AS first_successes,
  CAST(json_extract(run.value, '$.public_check_attempts') AS INTEGER) AS checks,
  CAST(json_extract(run.value, '$.repair_turns') AS INTEGER) AS repairs,
  CAST(json_extract(run.value, '$.total_tokens_per_task') AS REAL) AS tokens_task,
  CAST(json_extract(run.value, '$.elapsed_seconds_per_task') AS REAL) AS seconds_task,
  CAST(json_extract(run.value, '$.check_integrity_ok') AS INTEGER) AS integrity_ok,
  CAST(json_extract(run.value, '$.command_protocol_compliant') AS INTEGER) AS protocol_ok,
  json_extract(run.value, '$.thread_id') AS thread_id,
  run.value AS run_json
FROM raw, json_each(json_extract(raw.document, '$.results')) AS run;

CREATE TEMP VIEW scale_summary AS
SELECT
  CAST(json_extract(row.value, '$.bundle_size') AS INTEGER) AS bundle_size,
  CASE json_extract(row.value, '$.language') WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  CAST(json_extract(row.value, '$.sessions') AS INTEGER) AS sessions,
  CAST(json_extract(row.value, '$.assigned_tasks') AS INTEGER) AS assignments,
  CAST(json_extract(row.value, '$.hidden_task_successes') AS INTEGER) AS hidden_successes,
  CAST(json_extract(row.value, '$.first_public_task_successes') AS INTEGER) AS first_successes,
  CAST(json_extract(row.value, '$.repair_turns') AS INTEGER) AS repairs,
  CAST(json_extract(row.value, '$.median_total_tokens_per_task') AS REAL) AS median_tokens_task,
  CAST(json_extract(row.value, '$.median_elapsed_seconds_per_task') AS REAL) AS median_seconds_task
FROM raw, json_each(json_extract(raw.document, '$.summary.by_scale')) AS row;

CREATE TEMP VIEW fit_summary AS
WITH points AS (
  SELECT language, 1.0 / bundle_size AS x, median_tokens_task AS y FROM scale_summary
), moments AS (
  SELECT language, AVG(x) AS mx, AVG(y) AS my, AVG(x*y) AS mxy, AVG(x*x) AS mxx FROM points GROUP BY language
), coefficients AS (
  SELECT language, (mxy-mx*my)/(mxx-mx*mx) AS fixed_session_tokens,
         my-((mxy-mx*my)/(mxx-mx*mx))*mx AS residual_task_tokens
  FROM moments
)
SELECT * FROM coefficients;

SELECT 'headline', COUNT(*), SUM(task_count), COUNT(DISTINCT thread_id),
       SUM(first_successes), SUM(hidden_successes), SUM(repairs)
FROM runs;
SELECT 'scale_summary', * FROM scale_summary ORDER BY bundle_size, language;
SELECT 'fit_summary', * FROM fit_summary ORDER BY language;
SELECT 'session_detail', bundle_size, bundle_id, replicate, language, task_count,
       first_successes, hidden_successes, checks, repairs, tokens_task, seconds_task,
       integrity_ok, protocol_ok, thread_id
FROM runs ORDER BY bundle_size, language, replicate, bundle_id;
"""


def build_chart_map() -> str:
    return """# Iteration 030 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does balanced workload scaling reveal whether Parley's
  remaining Python gap is fixed session overhead or per-task language cost?
- Decision-useful answer: the dominant gap is fixed, but a small positive
  residual versus Python remains; Parley crosses Rust near size six.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Scaling | How does workload size change effort? | Grouped scale comparison / bar | bundle_size, language, median_tokens_task | All languages amortize fixed context steeply | Relaxed three-language palette |
| Gaps | Does Parley close the absolute gap? | Diverging grouped comparison / bar | bundle_size, baseline, token_gap | Python gap shrinks; Rust crosses below zero at size eight | Hard two-baseline palette |
| Fit | Which fitted component differs? | Grouped component comparison / bar | baseline, component, token_gap | Extra fixed context dominates; residual is +74 vs Python and -288 vs Rust | Hard two-component palette |
| Elapsed | Does time follow token amortization? | Grouped scale comparison / bar | bundle_size, language, median_seconds_task | Parley is between Python and Rust at size eight | Relaxed three-language palette |
| Source | How compact is editable code? | Grouped stage comparison / bar | language, stage, rough_tokens_task | Parley is shorter than Rust and longer than Python | Hard two-stage palette |

Exact reliability, root-cause, action-order, task-balance, fit-coefficient, and
session values remain in metrics/tables. A line chart was intentionally omitted:
four logarithmically spaced scales are clearer as discrete preregistered groups,
and the direct-gap panel preserves the small size-eight differences hidden by
the common steep scale.
"""


def validate_raw(raw: dict, tasks: dict) -> None:
    rows = raw["results"]
    roots = tasks["predeclared_analysis"]["root_cause_files"]
    assert len(rows) == 90
    assert sum(row["task_count"] for row in rows) == 192
    assert len({row["thread_id"] for row in rows}) == 90
    for row in rows:
        assert row["fresh_ephemeral_session"]
        assert row["agent_returncode"] == 0 and not row["agent_timed_out"]
        assert row["check_integrity_ok"] and row["command_protocol_compliant"]
        assert row["public_check_attempts"] == 1 and row["repair_turns"] == 0
        assert row["first_bundle_check_success"] and row["hidden_bundle_success"]
        assert not row["agent_errors"]
        assert [event["command"] for event in row["command_events"]] == [
            "/bin/zsh -lc ./sources", "/bin/zsh -lc ./check"
        ]
        for task_id, task in row["task_results"].items():
            assert task["first_public_check_success"] and task["hidden_success"]
            assert task["changed_files"] == [roots[task_id][row["language"]]]
    balance = Counter(
        (row["bundle_size"], row["language"], task_id)
        for row in rows for task_id in row["task_results"]
    )
    assert len(balance) == 96 and set(balance.values()) == {2}


def main() -> None:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    tasks = json.loads(TASK_MANIFEST.read_text(encoding="utf-8"))
    validate_raw(raw, tasks)
    artifact = build_artifact(raw, build_datasets(raw, tasks))
    (REPORTS / f"{STEM}.artifact.json").write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    (REPORTS / f"{STEM}.sql").write_text(build_sql(), encoding="utf-8")
    (REPORTS / f"{STEM}.chart-map.md").write_text(build_chart_map(), encoding="utf-8")
    print(json.dumps({
        "artifact": str(REPORTS / f"{STEM}.artifact.json"),
        "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "datasets": {key: len(value) for key, value in artifact["snapshot"]["datasets"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()
