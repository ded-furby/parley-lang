#!/usr/bin/env python3
"""Build the canonical report artifact for iteration 031's deeper-project pilot."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import statistics
from collections import Counter
from pathlib import Path


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW_NAME = "agent_deep_031_protocol_v1_v0.3.155.json"
RAW = BENCHMARKS / "results" / RAW_NAME
TASK_MANIFEST = BENCHMARKS / "agent_tasks_deep_031.json"
TEMPLATE = REPORTS / "030-ninety-session-scaling-mechanism.artifact.json"
STEM = "031-deeper-project-efficiency-win"
GENERATED_AT = "2026-08-04T20:28:06Z"
SOURCE_ID = "deep_results"
LANGUAGES = ("parley", "python", "rust")


def load_base():
    path = REPORTS / "build_030_report.py"
    spec = importlib.util.spec_from_file_location("parley_report_030", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load report 030 helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def display_language(language: str) -> str:
    return {"parley": "Parley", "python": "Python", "rust": "Rust"}[language]


def median(values) -> float:
    return float(statistics.median(values))


def completed_item_types(row: dict) -> list[str]:
    result = []
    for line in row["codex_stdout"].splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "item.completed":
            result.append(event.get("item", {}).get("type", ""))
    return result


def build_datasets(raw: dict, tasks: dict) -> dict[str, list[dict]]:
    rows = raw["results"]
    roots = tasks["predeclared_analysis"]["root_cause_files"]
    scale = {row["language"]: row for row in raw["summary"]["by_scale"]}
    parley = scale["parley"]

    def gap(metric: str, baseline: str) -> float:
        return 100.0 * (parley[metric] / scale[baseline][metric] - 1.0)

    parley_tasks = [
        (task_id, task)
        for row in rows if row["language"] == "parley"
        for task_id, task in row["task_results"].items()
    ]
    headline = [{
        "sessions": len(rows),
        "assignments": sum(row["task_count"] for row in rows),
        "hidden_successes": sum(row["hidden_task_successes"] for row in rows),
        "first_successes": sum(row["first_public_task_successes"] for row in rows),
        "repairs": sum(row["repair_turns"] for row in rows),
        "strict_conditions": sum(raw["summary"]["strict_gate"]["conditions"].values()),
        "parley_root_touched": sum(roots[task_id]["parley"] in task["changed_files"] for task_id, task in parley_tasks),
        "parley_exact_root": sum(task["changed_files"] == [roots[task_id]["parley"]] for task_id, task in parley_tasks),
        "token_gap_python_percent": round(gap("median_total_tokens_per_task", "python"), 2),
        "token_gap_rust_percent": round(gap("median_total_tokens_per_task", "rust"), 2),
        "elapsed_gap_python_percent": round(gap("median_elapsed_seconds_per_task", "python"), 2),
        "elapsed_gap_rust_percent": round(gap("median_elapsed_seconds_per_task", "rust"), 2),
    }]

    language_summary = []
    for language in LANGUAGES:
        summary = scale[language]
        selected = [row for row in rows if row["language"] == language]
        task_rows = [(task_id, task) for row in selected for task_id, task in row["task_results"].items()]
        clean = [row for row in selected if row["repair_turns"] == 0]
        language_summary.append({
            "language": display_language(language),
            "sessions": len(selected),
            "hidden_successes": summary["hidden_task_successes"],
            "first_successes": summary["first_public_task_successes"],
            "first_rate_percent": round(100.0 * summary["first_public_task_success_rate"], 2),
            "repairs": summary["repair_turns"],
            "median_tokens_task": summary["median_total_tokens_per_task"],
            "weighted_tokens_task": summary["weighted_total_tokens_per_task"],
            "clean_median_tokens_task": round(median(row["total_tokens_per_task"] for row in clean), 4),
            "median_seconds_task": summary["median_elapsed_seconds_per_task"],
            "clean_median_seconds_task": round(median(row["elapsed_seconds_per_task"] for row in clean), 4),
            "prompt_chars_task": summary["median_prompt_chars_per_task"],
            "source_tokens_task": summary["median_source_rough_tokens_per_task"],
            "edit_tokens_task": summary["median_source_edit_rough_tokens_per_task"],
            "root_touched": sum(roots[task_id][language] in task["changed_files"] for task_id, task in task_rows),
            "exact_root": sum(task["changed_files"] == [roots[task_id][language]] for task_id, task in task_rows),
        })

    session_detail = []
    for row in rows:
        session_detail.append({
            "replicate": row["replicate"],
            "language": display_language(row["language"]),
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

    task_detail = []
    root_audit = []
    command_audit = []
    for language in LANGUAGES:
        selected = [row for row in rows if row["language"] == language]
        task_rows = [(row, task_id, task) for row in selected for task_id, task in row["task_results"].items()]
        for task_id in roots:
            appearances = [task for _, candidate, task in task_rows if candidate == task_id]
            task_detail.append({
                "repository": appearances[0]["task_title"],
                "language": display_language(language),
                "appearances": len(appearances),
                "first_successes": sum(task["first_public_check_success"] for task in appearances),
                "hidden_successes": sum(task["hidden_success"] for task in appearances),
                "root_touched": sum(roots[task_id][language] in task["changed_files"] for task in appearances),
                "exact_root": sum(task["changed_files"] == [roots[task_id][language]] for task in appearances),
                "final_variants": len({task["source_text"] for task in appearances}),
                "final_tokens": round(median(task["source_rough_tokens"] for task in appearances), 2),
                "edit_tokens": round(median(task["source_edit_rough_tokens"] for task in appearances), 2),
            })
        root_audit.append({
            "language": display_language(language),
            "assignments": len(task_rows),
            "root_touched": sum(roots[task_id][language] in task["changed_files"] for _, task_id, task in task_rows),
            "exact_root": sum(task["changed_files"] == [roots[task_id][language]] for _, task_id, task in task_rows),
            "extra_file_assignments": sum(len(task["changed_files"]) > 1 for _, _, task in task_rows),
            "read_only_preserved": sum(len(task["context_source_files"]) for _, _, task in task_rows),
            "final_variants": sum(len({task["source_text"] for _, candidate, task in task_rows if candidate == task_id}) for task_id in roots),
        })
        item_types = [completed_item_types(row) for row in selected]
        command_audit.append({
            "language": display_language(language),
            "sessions": len(selected),
            "fresh": sum(row["fresh_ephemeral_session"] for row in selected),
            "sources_first": sum(row["command_events"][0]["command"] == "/bin/zsh -lc ./sources" for row in selected),
            "one_check": sum(row["public_check_attempts"] == 1 for row in selected),
            "two_checks": sum(row["public_check_attempts"] == 2 for row in selected),
            "protocol_ok": sum(row["command_protocol_compliant"] for row in selected),
            "integrity_ok": sum(row["check_integrity_ok"] for row in selected),
            "file_change_actions": sum(events.count("file_change") for events in item_types),
            "agent_messages": sum(len(row["agent_messages"]) for row in selected),
        })

    repairs = []
    for row in rows:
        failures = [task_id for task_id, task in row["task_results"].items() if not task["first_public_check_success"]]
        for task_id in failures:
            task = row["task_results"][task_id]
            repairs.append({
                "language": display_language(row["language"]),
                "replicate": row["replicate"],
                "repository": task["task_title"],
                "checks": row["public_check_attempts"],
                "tokens_task": round(row["total_tokens_per_task"], 4),
                "seconds_task": round(row["elapsed_seconds_per_task"], 4),
                "changed_files": ", ".join(task["changed_files"]),
                "root_touched": roots[task_id][row["language"]] in task["changed_files"],
                "exact_root": task["changed_files"] == [roots[task_id][row["language"]]],
            })

    source_stage = []
    for language in LANGUAGES:
        selected = [row for row in rows if row["language"] == language]
        source_stage.extend([
            {"language": display_language(language), "stage": "Seed", "rough_tokens_task": round(median(row["seed_source_rough_tokens_per_task"] for row in selected), 4)},
            {"language": display_language(language), "stage": "Final", "rough_tokens_task": round(median(row["source_rough_tokens_per_task"] for row in selected), 4)},
        ])
    return {
        "headline": headline,
        "language_summary": language_summary,
        "session_detail": session_detail,
        "task_detail": task_detail,
        "repair_detail": repairs,
        "root_audit": root_audit,
        "command_audit": command_audit,
        "source_stage": source_stage,
    }


def build_artifact(raw: dict, datasets: dict[str, list[dict]], base) -> dict:
    artifact = copy.deepcopy(json.loads(TEMPLATE.read_text(encoding="utf-8")))
    manifest = artifact["manifest"]
    manifest.update({
        "title": "Deeper-Project Efficiency Win — Iteration 031",
        "description": "Preregistered 18-session comparison over four five-module project regressions.",
        "generatedAt": GENERATED_AT,
        "sources": [{"id": SOURCE_ID, "label": "Frozen iteration 031 deeper-project results", "path": f"{STEM}.sql"}],
    })
    manifest["cards"] = [
        base.metric_card("sessions_card", "Every planned fresh session, retained once.", "Fresh sessions", "sessions"),
        base.metric_card("hidden_card", "Assignments passing every withheld case.", "Hidden success", "hidden_successes", "of 72"),
        base.metric_card("first_card", "Assignments passing the untouched first check.", "First-check success", "first_successes", "of 72"),
        base.metric_card("repair_card", "Additional public-check turns across all languages.", "Repairs", "repairs"),
        base.metric_card("strict_card", "Strict efficiency/reliability conditions passed.", "Strict conditions", "strict_conditions", "of 4"),
        base.metric_card("exact_card", "Parley assignments changing exactly the frozen root file.", "Exact Parley roots", "parley_exact_root", "of 24"),
        base.metric_card("python_gap_card", "Parley median token delta relative to Python.", "Token delta vs Python", "token_gap_python_percent", "%", True),
        base.metric_card("rust_gap_card", "Parley median token delta relative to Rust.", "Token delta vs Rust", "token_gap_rust_percent", "%", True),
    ]
    manifest["charts"] = [
        base.chart("token_chart", "Median reported tokens per repository", "Six complete four-project sessions per language.", "language_summary", "language", "median_tokens_task", "language", "Language", "Tokens per repository", "Did Parley beat both baseline token medians?", "The primary common-denominator metric directly answers the frozen efficiency condition.", "reported tokens per repository", "language median", "six sessions per language", "compact"),
        base.chart("session_chart", "Tokens in every fresh session", "All 18 values expose the repair-driven distribution without exclusions.", "session_detail", "replicate", "tokens_task", "language", "Replicate", "Tokens per repository", "Is the median win robust to complete session values?", "Grouped session bars show clean and repaired clusters and prevent the median from hiding outliers.", "reported tokens per repository", "language-replicate session", "four repositories per session", "compact"),
        base.chart("elapsed_chart", "Median elapsed seconds per repository", "All timing cells include compilation, checks, and repair turns.", "language_summary", "language", "median_seconds_task", "language", "Language", "Seconds per repository", "Did Parley beat both baselines on elapsed effort?", "Elapsed time is a separate preregistered strict condition.", "seconds per repository", "language median", "six sessions per language"),
        base.chart("first_chart", "First-check repository success", "Twenty-four assignments per language; higher is better.", "language_summary", "language", "first_rate_percent", "language", "Language", "First-check success (%)", "Did Parley retain or exceed baseline reliability?", "First-check rate exposes whether efficiency came from skipping necessary verification or from cleaner diagnosis.", "percent of repositories", "language aggregate", "24 assignments per language"),
        base.chart("source_chart", "Seed and final editable source", "Median rough lexical tokens per repository.", "source_stage", "language", "rough_tokens_task", "stage", "Language", "Rough source tokens per repository", "How compact is the deeper code each agent reads and leaves?", "Stage bars separate existing source volume from patch volume and explain part of the cross-language effort.", "rough source tokens per repository", "language-stage median", "six sessions per language"),
    ]
    manifest["tables"] = [
        base.table("language_table", "Primary deeper-project result", "All 72 assignments and six sessions per language.", "language_summary", [
            ("language", "Language", "text"), ("hidden_successes", "Hidden", "number"), ("first_successes", "First", "number"), ("repairs", "Repairs", "number"), ("median_tokens_task", "Median tokens/repo", "number"), ("weighted_tokens_task", "Weighted tokens/repo", "number"), ("clean_median_tokens_task", "Clean median", "number"), ("median_seconds_task", "Seconds/repo", "number"), ("source_tokens_task", "Final source", "number"), ("exact_root", "Exact roots", "number"),
        ], "language"),
        base.table("task_table", "Task-level diagnosis audit", "Six appearances per language/task; all 12 aggregates retained.", "task_detail", [
            ("repository", "Repository change", "text"), ("language", "Language", "text"), ("appearances", "Runs", "number"), ("first_successes", "First", "number"), ("hidden_successes", "Hidden", "number"), ("root_touched", "Root touched", "number"), ("exact_root", "Exact root", "number"), ("final_variants", "Variants", "number"), ("final_tokens", "Final source", "number"), ("edit_tokens", "Edit size", "number"),
        ], "repository"),
        base.table("repair_table", "Complete first-check failure audit", "All ten repaired sessions fail the same configuration-state task first.", "repair_detail", [
            ("language", "Language", "text"), ("replicate", "Rep", "number"), ("repository", "Repository", "text"), ("checks", "Checks", "number"), ("tokens_task", "Tokens/repo", "number"), ("seconds_task", "Seconds/repo", "number"), ("changed_files", "Changed files", "text"), ("root_touched", "Root touched", "number"), ("exact_root", "Exact root", "number"),
        ], "language"),
        base.table("root_table", "Root-cause and patch-scope audit", "Every patch touches its owning root; one assignment per language also leaves a harmless extra count edit.", "root_audit", [
            ("language", "Language", "text"), ("assignments", "Assignments", "number"), ("root_touched", "Root touched", "number"), ("exact_root", "Exact root only", "number"), ("extra_file_assignments", "Extra-file runs", "number"), ("read_only_preserved", "Read-only preserved", "number"), ("final_variants", "Final variants", "number"),
        ], "language"),
        base.table("command_table", "Fresh-session and action audit", "All sessions preserve source order, checker integrity, and protocol boundaries.", "command_audit", [
            ("language", "Language", "text"), ("sessions", "Sessions", "number"), ("fresh", "Fresh", "number"), ("sources_first", "Sources first", "number"), ("one_check", "One check", "number"), ("two_checks", "Two checks", "number"), ("protocol_ok", "Protocol", "number"), ("integrity_ok", "Integrity", "number"), ("file_change_actions", "File actions", "number"), ("agent_messages", "Messages", "number"),
        ], "language"),
        base.table("session_table", "Complete 18-session audit", "Every unique thread, result, token count, timing, and changed-file rate.", "session_detail", [
            ("replicate", "Rep", "number"), ("language", "Language", "text"), ("hidden_successes", "Hidden", "number"), ("first_successes", "First", "number"), ("checks", "Checks", "number"), ("repairs", "Repairs", "number"), ("tokens_task", "Tokens/repo", "number"), ("input_tokens_task", "Input/repo", "number"), ("output_tokens_task", "Output/repo", "number"), ("seconds_task", "Seconds/repo", "number"), ("changed_files_task", "Files/repo", "number"), ("thread", "Thread", "text"),
        ], "replicate"),
    ]

    blocks = [
        base.markdown("title", "# Deeper-Project Efficiency Win — Iteration 031", False),
        base.markdown("summary", "## Technical summary\n\n**Parley beats both Python and Rust on all four preregistered efficiency/reliability conditions in the deeper project corpus.** All 72 assignments are hidden-correct. Parley records 15.94k median tokens and 7.3906 seconds/repository versus Python's 23.67k/9.2024 and Rust's 24.48k/10.2195, while first-check success is 22/24 versus 20/24 for both baselines. The strict gate is 4/4. The separate exact-root maintainability gate is 23/24, so the overall five-condition pilot is **4/5**, not a full maintainable-parity claim."),
        base.markdown("scope", "## What changed from the scaling study\n\nThe compiler, runner, model, and 1,519-character instruction remain frozen. The workload is new and committed before output: four independently sourced regressions, each with five editable modules and three read-only issue/architecture/test artifacts. Every six-replicate session diagnoses all four projects. The corpus tests credential scope, configuration state, forwarded-origin trust, and terminal lifecycle reconciliation—not narrow syntax."),
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": ["sessions_card", "hidden_card", "first_card", "repair_card", "strict_card", "exact_card", "python_gap_card", "rust_gap_card"]},
        base.markdown("reliability", "## Hidden correctness is perfect and Parley is more reliable first\n\nParley, Python, and Rust each pass 24/24 hidden assignments. Parley passes 22/24 on the untouched first check; Python and Rust each pass 20/24. Repairs are 2, 4, and 4. The strict correctness and first-check conditions both pass, and no language trades final correctness for lower effort."),
        {"id": "language_table_block", "type": "table", "tableId": "language_table", "layout": "full"},
        base.markdown("tokens", "## Parley uses 32.67% fewer median tokens than Python\n\nParley's 15.94k median tokens/repository is **32.67% below Python** and **34.89% below Rust**. The unweighted median rewards the four clean Parley sessions, so the weighted all-session check matters: Parley remains 15.60% below Python and 15.67% below Rust after every repair-heavy session is included."),
        {"id": "token_chart_block", "type": "chart", "chartId": "token_chart", "layout": "full"},
        base.markdown("distribution", "## The complete distribution shows the mechanism\n\nRepair-free sessions cluster near 15.9k tokens/repository for all three languages. Parley has four clean sessions and two repaired sessions; Python and Rust have only two clean and four repaired. Repair-free medians are 15,922.63 for Parley, 17,512.50 for Python, and 15,994.00 for Rust. Thus the large primary win is mostly reliability, while Parley still narrowly leads the clean sensitivity against both baselines."),
        {"id": "session_chart_block", "type": "chart", "chartId": "session_chart", "layout": "full"},
        base.markdown("elapsed", "## Parley is also faster end to end\n\nParley's 7.3906 median seconds/repository is **19.69% faster than Python** and **27.68% faster than Rust**. These values include compilation and second checks. Clean-session medians are 6.9334, 8.5087, and 9.3217 seconds, so the time win is not solely a repair-count artifact."),
        {"id": "elapsed_chart_block", "type": "chart", "chartId": "elapsed_chart", "layout": "full"},
        base.markdown("first_read", "## One task creates every repair\n\nAll ten first-check failures occur in explicit empty-collection configuration. Agents initially preserve precedence but label the value `list` instead of the evidence's distinct `empty` state; checker feedback resolves every case on check two. Parley makes this mistake twice, versus four times each for Python and Rust. The other three projects are 54/54 first-check clean across languages."),
        {"id": "first_chart_block", "type": "chart", "chartId": "first_chart", "layout": "full"},
        {"id": "repair_table_block", "type": "table", "tableId": "repair_table", "layout": "full"},
        base.markdown("source", "## Parley is compact relative to Rust, not Python\n\nMedian final source is 325.50 rough tokens/repository for Parley, 279.25 for Python, and 460.38 for Rust. Parley's token win over Python therefore cannot be attributed to shorter source. Instead, the model reaches more first-check solutions and uses fewer repair turns. Equal read-only evidence is 158.5 rough tokens/repository after session-level division."),
        {"id": "source_chart_block", "type": "chart", "chartId": "source_chart", "layout": "full"},
        {"id": "task_table_block", "type": "table", "tableId": "task_table", "layout": "full"},
        base.markdown("root", "## Every patch fixes the right layer, but one Parley patch is broader\n\nAll 72 assignments touch the predeclared owning root file. Exact one-root scope is 23/24 for every language. In one repaired empty-collection session per language, the agent first treats `empty` as a zero-length list and edits the count helper; after feedback it correctly restores the distinct `empty` classification but leaves the now-unreachable count guard. The extra edit is harmless and symmetric, yet it fails the frozen exact-root condition."),
        {"id": "root_table_block", "type": "table", "tableId": "root_table", "layout": "full"},
        base.markdown("actions", "## Event order and integrity remain controlled\n\nEvery session starts with one protected `./sources` call, performs file changes, and uses one or two exact `./check` calls. All 18 threads are fresh, exit zero, preserve read-only/checker hashes, and comply with the command protocol. There are no timeouts, agent errors, hidden failures, excluded rows, or selective reruns."),
        {"id": "command_table_block", "type": "table", "tableId": "command_table", "layout": "full"},
        base.markdown("method", "## Frozen method and provenance\n\n- **Matrix:** four projects × three languages × six complete-bundle replicates = 18 sessions and 72 assignments; seed `20260825`.\n- **Toolchain:** pinned Parley 0.3.155, `gpt-5.6-sol` medium, Codex CLI 0.146.0.\n- **Corpus:** checkpoint `f836fce`, manifest SHA `7f81e6e6…`; independent source/adaptation record preserved.\n- **Protocol:** committed before output at `34bd08e`, SHA `4ede556b…`.\n- **Instruction:** unchanged 1,519-character skill, SHA `6ca098e4…`; the one allowed compression experiment remains closed.\n- **Result:** raw SHA `e6415531…`; every planned cell ran once and is retained."),
        base.markdown("integrity", "## Complete session evidence\n\nThe session table retains all token/input/output totals, elapsed times, checks, repairs, changed-file rates, and unique thread IDs. Raw JSON additionally preserves every prompt hash, agent message, command event, file-change event, final source file, public attempt, hidden case, and compiler output."),
        {"id": "session_table_block", "type": "table", "tableId": "session_table", "layout": "full"},
        base.markdown("limitations", "## Limits and robustness\n\nThe mechanisms come from independent primary issue reports, but the executable repositories remain synthetic, deterministic, and much smaller than mature production systems. Six replicates establish a strong pilot distribution, not a population estimate. All tasks are repaired in one or two checks; none tests history search, services, concurrency, or ambiguous multi-cause failure. Cross-corpus comparisons with iteration 030 are descriptive because task content changed."),
        base.markdown("boundary", "## No compiler or instruction change follows\n\nThere is no Parley parse, type, runtime, hidden, root-location, or task-specific syntax failure. The shared empty-state interpretation error occurs more often in Python and Rust and resolves from checker feedback. It is not a language defect. Parley stays at v0.3.155; no syntax, diagnostic, prompt, skill, task, runner, or metric change is justified from this corpus."),
        base.markdown("decision", "## Decision and next step\n\n1. Preserve iteration 031 unchanged as a strict efficiency/reliability **4/4 win** over both Python and Rust.\n2. Preserve the separate exact-root result as 23/24 and the overall five-condition status as **4/5**; do not erase the harmless extra edit.\n3. Make no compiler or instruction change.\n4. Do not claim universal language superiority from four synthetic projects.\n5. Preregister an independent deeper-project confirmation with new mechanisms and the same gates. A confirmation must reproduce the efficiency win and exact-root quality without selecting tasks from iteration-031 failures."),
        base.markdown("questions", "## Further questions\n\n- Does the reliability-driven token win replicate on independently sourced deeper episodes?\n- Does exact-root scope return to 100% without changing the empty-state task or checker?\n- How does Parley compare on mature repositories where history and dependency search dominate source inspection?", False),
    ]
    manifest["blocks"] = blocks
    artifact["snapshot"] = {"version": 1, "generatedAt": GENERATED_AT, "status": "ready", "datasets": datasets}
    artifact["sources"] = [{
        "id": SOURCE_ID,
        "label": "Frozen iteration 031 deeper-project results",
        "path": f"{STEM}.sql",
        "query": {
            "engine": "SQLite JSON1 + Python statistics",
            "query": f"python3 benchmarks/reports/build_031_report.py && sqlite3 ':memory:' < benchmarks/reports/{STEM}.sql",
            "description": "Reproducible aggregation of all 18 sessions, 72 hidden judgments, task-level failures, action events, source/edit metrics, and predeclared exact-root scope.",
            "executed_at": GENERATED_AT,
            "language": "SQL / Python",
            "metric_definitions": [
                "Strict parity: correctness, median tokens, median elapsed, and first-check rate all beat the required baseline direction.",
                "Exact root: changed-files list contains only the defect file frozen before measured output.",
                "Weighted tokens per repository: total reported session tokens divided by 24 language assignments.",
                "Repair-free sensitivity: median over sessions with one public check and zero repair turns.",
            ],
        },
    }]
    artifact["package_info"] = {"root": "benchmarks/results", "manifestPath": f"{STEM}.artifact.json", "snapshotPath": RAW_NAME, "originUrl": "artifact://parley-deeper-project-031"}
    return artifact


def build_sql() -> str:
    return f""".mode list
.separator |
CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/{RAW_NAME}'));
CREATE TEMP VIEW runs AS
SELECT CAST(json_extract(run.value,'$.replicate') AS INTEGER) AS replicate,
       json_extract(run.value,'$.language') AS language,
       CAST(json_extract(run.value,'$.hidden_task_successes') AS INTEGER) AS hidden,
       CAST(json_extract(run.value,'$.first_public_task_successes') AS INTEGER) AS first_success,
       CAST(json_extract(run.value,'$.public_check_attempts') AS INTEGER) AS checks,
       CAST(json_extract(run.value,'$.repair_turns') AS INTEGER) AS repairs,
       CAST(json_extract(run.value,'$.total_tokens_per_task') AS REAL) AS tokens_task,
       CAST(json_extract(run.value,'$.elapsed_seconds_per_task') AS REAL) AS seconds_task,
       json_extract(run.value,'$.thread_id') AS thread_id,
       run.value AS run_json
FROM raw, json_each(json_extract(raw.document,'$.results')) AS run;
CREATE TEMP VIEW language_summary AS
SELECT CASE json_extract(row.value,'$.language') WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
       json_extract(row.value,'$.hidden_task_successes') AS hidden,
       json_extract(row.value,'$.first_public_task_successes') AS first_success,
       json_extract(row.value,'$.repair_turns') AS repairs,
       json_extract(row.value,'$.median_total_tokens_per_task') AS median_tokens_task,
       json_extract(row.value,'$.weighted_total_tokens_per_task') AS weighted_tokens_task,
       json_extract(row.value,'$.median_elapsed_seconds_per_task') AS median_seconds_task
FROM raw, json_each(json_extract(raw.document,'$.summary.by_scale')) AS row;
SELECT 'headline', COUNT(*), SUM(hidden), SUM(first_success), SUM(repairs), COUNT(DISTINCT thread_id) FROM runs;
SELECT 'language_summary', * FROM language_summary ORDER BY language;
SELECT 'session_detail', replicate, language, hidden, first_success, checks, repairs, tokens_task, seconds_task, thread_id FROM runs ORDER BY replicate, language;
"""


def build_chart_map() -> str:
    return """# Iteration 031 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: do deeper multi-file diagnosis episodes let Parley match or
  beat Python and Rust without language or instruction tuning?
- Decision-useful answer: strict efficiency/reliability passes 4/4, while the
  separate exact-root maintainability condition finishes 23/24.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Tokens | Did Parley beat both baselines? | Category comparison / bar | language, median_tokens_task | Parley is 32.67% below Python and 34.89% below Rust | Relaxed three-language palette |
| Distribution | Does the win survive full session disclosure? | Grouped discrete comparison / bar | replicate, language, tokens_task | Repair frequency creates high-cost baseline clusters | Relaxed three-language palette |
| Elapsed | Did wall time also pass? | Category comparison / bar | language, median_seconds_task | Parley is faster than both baselines | Relaxed three-language palette |
| Reliability | Which language succeeds first? | Category comparison / bar | language, first_rate_percent | Parley is 22/24 versus 20/24 | Relaxed three-language palette |
| Source | Is the win just shorter code? | Grouped stage comparison / bar | language, stage, rough_tokens_task | Parley is longer than Python but shorter than Rust | Hard two-stage palette |

Exact root scope, repairs, task cuts, action protocol, and all session values
remain in metrics and audit tables. Five charts answer distinct decisions; none
duplicates the exact lookup tables.
"""


def validate(raw: dict, tasks: dict) -> None:
    rows = raw["results"]
    roots = tasks["predeclared_analysis"]["root_cause_files"]
    assert len(rows) == 18 and sum(row["task_count"] for row in rows) == 72
    assert len({row["thread_id"] for row in rows}) == 18
    assert raw["summary"]["strict_gate"]["passed"]
    for row in rows:
        assert row["fresh_ephemeral_session"] and row["agent_returncode"] == 0 and not row["agent_timed_out"]
        assert row["check_integrity_ok"] and row["command_protocol_compliant"] and not row["agent_errors"]
        assert row["hidden_bundle_success"]
        for task_id, task in row["task_results"].items():
            assert task["hidden_success"]
            assert roots[task_id][row["language"]] in task["changed_files"]
    exact = {
        language: sum(
            task["changed_files"] == [roots[task_id][language]]
            for row in rows if row["language"] == language
            for task_id, task in row["task_results"].items()
        ) for language in LANGUAGES
    }
    assert exact == {"parley": 23, "python": 23, "rust": 23}


def main() -> None:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    tasks = json.loads(TASK_MANIFEST.read_text(encoding="utf-8"))
    validate(raw, tasks)
    base = load_base()
    base.SOURCE_ID = SOURCE_ID
    artifact = build_artifact(raw, build_datasets(raw, tasks), base)
    (REPORTS / f"{STEM}.artifact.json").write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    (REPORTS / f"{STEM}.sql").write_text(build_sql(), encoding="utf-8")
    (REPORTS / f"{STEM}.chart-map.md").write_text(build_chart_map(), encoding="utf-8")
    print(json.dumps({"artifact": str(REPORTS / f"{STEM}.artifact.json"), "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(), "datasets": {key: len(value) for key, value in artifact["snapshot"]["datasets"].items()}}, indent=2))


if __name__ == "__main__":
    main()
