#!/usr/bin/env python3
"""Build the canonical report artifact for independent confirmation 032."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW_NAME = "agent_deep_confirmation_032_protocol_v1_v0.3.158.json"
RAW = BENCHMARKS / "results" / RAW_NAME
TASK_MANIFEST = BENCHMARKS / "agent_tasks_deep_confirmation_032.json"
STEM = "032-independent-confirmation-strict-parity-not-met"
SOURCE_ID = "confirmation_results"
LANGUAGES = ("parley", "python", "rust")


def load_module(filename: str, module_name: str):
    path = REPORTS / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def chart(base, chart_id: str, title: str, subtitle: str, dataset: str,
          x: str, y: str, x_label: str, y_label: str, question: str,
          rationale: str, unit: str, grain: str, denominator: str,
          color: str | None = None, value_format: str = "number") -> dict:
    item = base.chart(
        chart_id, title, subtitle, dataset, x, y, color or x, x_label,
        y_label, question, rationale, unit, grain, denominator, value_format,
    )
    if color is None:
        item["encodings"].pop("color", None)
    return item


def build_datasets(raw: dict, tasks: dict, old) -> dict[str, list[dict]]:
    datasets = old.build_datasets(raw, tasks)
    headline = datasets["headline"][0]
    scale = {row["language"]: row for row in raw["summary"]["by_scale"]}
    parley = scale["parley"]
    lower_tokens = min(scale["python"]["median_total_tokens_per_task"], scale["rust"]["median_total_tokens_per_task"])
    lower_seconds = min(scale["python"]["median_elapsed_seconds_per_task"], scale["rust"]["median_elapsed_seconds_per_task"])
    higher_first = max(scale["python"]["first_public_task_success_rate"], scale["rust"]["first_public_task_success_rate"])
    headline.update({
        "elapsed_gap_python_percent": round(100.0 * (parley["median_elapsed_seconds_per_task"] / scale["python"]["median_elapsed_seconds_per_task"] - 1.0), 2),
        "elapsed_gap_rust_percent": round(100.0 * (parley["median_elapsed_seconds_per_task"] / scale["rust"]["median_elapsed_seconds_per_task"] - 1.0), 2),
        "overall_conditions": sum(raw["summary"]["strict_gate"]["conditions"].values()) + (headline["parley_exact_root"] == 24),
    })
    datasets["gate_detail"] = [
        {"condition": "Hidden correctness", "observed": "24/24", "threshold": "100% and no lower than either baseline", "passed": True},
        {"condition": "Median tokens/repository", "observed": f"{parley['median_total_tokens_per_task']:.2f}", "threshold": f"≤ {lower_tokens:.2f} (lower baseline)", "passed": False},
        {"condition": "Median seconds/repository", "observed": f"{parley['median_elapsed_seconds_per_task']:.4f}", "threshold": f"≤ {lower_seconds:.4f} (lower baseline)", "passed": False},
        {"condition": "First-check success", "observed": "24/24", "threshold": f"≥ {higher_first:.0%} (higher baseline)", "passed": True},
        {"condition": "Exact-root maintainability", "observed": "24/24", "threshold": "24/24 Parley assignments", "passed": True},
    ]
    datasets.pop("repair_detail", None)
    return datasets


def build_artifact(raw: dict, datasets: dict[str, list[dict]], old, base) -> dict:
    generated_at = raw["generated_at"]
    artifact = copy.deepcopy(old.build_artifact(raw, datasets, base))
    manifest = artifact["manifest"]
    manifest.update({
        "title": "Independent Confirmation: Reliability Holds, Strict Parity Does Not — Iteration 032",
        "description": "Preregistered independent 18-session confirmation over four new five-module project regressions after product work.",
        "generatedAt": generated_at,
        "sources": [{"id": SOURCE_ID, "label": "Frozen iteration 032 independent confirmation", "path": f"{STEM}.sql"}],
    })
    manifest["cards"] = [
        base.metric_card("sessions_card", "Every planned fresh session, retained exactly once.", "Fresh sessions", "sessions"),
        base.metric_card("hidden_card", "Assignments passing every withheld case.", "Hidden success", "hidden_successes", "of 72"),
        base.metric_card("first_card", "Assignments passing the untouched first check.", "First-check success", "first_successes", "of 72"),
        base.metric_card("repair_card", "Additional public-check turns across all languages.", "Repairs", "repairs"),
        base.metric_card("strict_card", "Preregistered efficiency/reliability conditions passed.", "Strict conditions", "strict_conditions", "of 4"),
        base.metric_card("overall_card", "Primary conditions plus exact-root maintainability.", "Overall conditions", "overall_conditions", "of 5"),
        base.metric_card("exact_card", "Parley assignments changing only the frozen defect file.", "Exact Parley roots", "parley_exact_root", "of 24"),
        base.metric_card("python_gap_card", "Positive means Parley used more median tokens.", "Token delta vs Python", "token_gap_python_percent", "%", True),
        base.metric_card("rust_gap_card", "Positive means Parley used more median tokens.", "Token delta vs Rust", "token_gap_rust_percent", "%", True),
        base.metric_card("python_time_card", "Positive means Parley took more median elapsed time.", "Time delta vs Python", "elapsed_gap_python_percent", "%", True),
        base.metric_card("rust_time_card", "Negative means Parley took less median elapsed time.", "Time delta vs Rust", "elapsed_gap_rust_percent", "%", True),
    ]
    manifest["charts"] = [
        chart(base, "token_chart", "Median reported tokens per repository", "Six complete four-project sessions per language; lower is better.", "language_summary", "language", "median_tokens_task", "Language", "Tokens per repository", "Did Parley reproduce strict token parity?", "The primary common-denominator metric directly applies the frozen lower-baseline condition.", "reported tokens per repository", "language median", "six sessions per language", value_format="compact"),
        chart(base, "session_chart", "Tokens in every fresh session", "All 18 retained values show the narrow complete distribution without exclusions.", "session_detail", "replicate", "tokens_task", "Replicate", "Tokens per repository", "Is the token ordering caused by one outlier?", "Grouped bars expose every observed session and preserve language identity.", "reported tokens per repository", "language-replicate session", "four repositories per session", color="language", value_format="compact"),
        chart(base, "elapsed_chart", "Median elapsed seconds per repository", "Compilation, checking, and the complete agent turn are included; lower is better.", "language_summary", "language", "median_seconds_task", "Language", "Seconds per repository", "Did Parley reproduce strict elapsed parity?", "Elapsed time is a separate preregistered gate and can differ from token ordering.", "seconds per repository", "language median", "six sessions per language"),
        chart(base, "source_chart", "Seed and final editable source", "Median rough lexical tokens per repository; read-only evidence is identical.", "source_stage", "language", "rough_tokens_task", "Language", "Rough source tokens per repository", "How much editable source did each agent read and leave?", "Stage comparison separates existing language volume from the patch itself.", "rough source tokens per repository", "language-stage median", "six sessions per language", color="stage"),
    ]
    manifest["tables"] = [
        base.table("gate_table", "Frozen gate audit", "The fifth exact-root condition is reported separately from the four-condition primary gate.", "gate_detail", [
            ("condition", "Condition", "text"), ("observed", "Parley observed", "text"), ("threshold", "Frozen threshold", "text"), ("passed", "Pass", "number"),
        ], "condition"),
        base.table("language_table", "Primary independent result", "All 72 assignments and six sessions per language.", "language_summary", [
            ("language", "Language", "text"), ("hidden_successes", "Hidden", "number"), ("first_successes", "First", "number"), ("repairs", "Repairs", "number"), ("median_tokens_task", "Median tokens/repo", "number"), ("weighted_tokens_task", "Weighted tokens/repo", "number"), ("median_seconds_task", "Seconds/repo", "number"), ("prompt_chars_task", "Prompt chars/repo", "number"), ("source_tokens_task", "Final source", "number"), ("edit_tokens_task", "Edit size", "number"), ("exact_root", "Exact roots", "number"),
        ], "language"),
        base.table("task_table", "Task-level diagnosis audit", "Each project appears six times per language; every aggregate is retained.", "task_detail", [
            ("repository", "Repository change", "text"), ("language", "Language", "text"), ("appearances", "Runs", "number"), ("first_successes", "First", "number"), ("hidden_successes", "Hidden", "number"), ("root_touched", "Root touched", "number"), ("exact_root", "Exact root", "number"), ("final_variants", "Variants", "number"), ("final_tokens", "Final source", "number"), ("edit_tokens", "Edit size", "number"),
        ], "repository"),
        base.table("root_table", "Root-cause and patch-scope audit", "Every patch changes exactly its owning defect file and preserves read-only evidence.", "root_audit", [
            ("language", "Language", "text"), ("assignments", "Assignments", "number"), ("root_touched", "Root touched", "number"), ("exact_root", "Exact root only", "number"), ("extra_file_assignments", "Extra-file runs", "number"), ("read_only_preserved", "Read-only preserved", "number"), ("final_variants", "Final variants", "number"),
        ], "language"),
        base.table("command_table", "Fresh-session and action audit", "Every session preserves source order, checker integrity, and command boundaries.", "command_audit", [
            ("language", "Language", "text"), ("sessions", "Sessions", "number"), ("fresh", "Fresh", "number"), ("sources_first", "Sources first", "number"), ("one_check", "One check", "number"), ("two_checks", "Two checks", "number"), ("protocol_ok", "Protocol", "number"), ("integrity_ok", "Integrity", "number"), ("file_change_actions", "File actions", "number"), ("agent_messages", "Messages", "number"),
        ], "language"),
        base.table("session_table", "Complete 18-session audit", "Every unique thread, token count, timing, check, and changed-file rate.", "session_detail", [
            ("replicate", "Rep", "number"), ("language", "Language", "text"), ("hidden_successes", "Hidden", "number"), ("first_successes", "First", "number"), ("checks", "Checks", "number"), ("repairs", "Repairs", "number"), ("tokens_task", "Tokens/repo", "number"), ("input_tokens_task", "Input/repo", "number"), ("output_tokens_task", "Output/repo", "number"), ("seconds_task", "Seconds/repo", "number"), ("changed_files_task", "Files/repo", "number"), ("thread", "Thread", "text"),
        ], "replicate"),
    ]
    metric_ids = [card["id"] for card in manifest["cards"]]
    manifest["blocks"] = [
        base.markdown("title", "# Independent Confirmation: Reliability Holds, Strict Parity Does Not — Iteration 032", False),
        base.markdown("summary", "## Technical summary\n\n**Parley's product-grade reliability and diagnosis quality fully repeat, but the strict efficiency win from report 031 does not.** All 72 assignments are hidden-correct and first-check-correct, every patch changes exactly the predeclared defect file, and no repair is needed. Parley records 15.70k median tokens/repository versus Python's 15.03k and Rust's 15.45k; elapsed time is 8.4545 seconds versus 7.5247 and 9.3756. The frozen primary gate is **2/4** and the exact-root gate passes, making the overall result **3/5**. This is a clean negative confirmation, not a compiler failure."),
        base.markdown("scope", "## Four new mechanisms were frozen after the workflow product phase\n\nThe corpus was committed before the protocol and selected independently of report 031 outcomes: quoted environment normalization, retry-header precedence, raw-body webhook verification, and stable pagination ordering. Each project exposes five editable modules plus three byte-identical read-only artifacts. Parley v0.3.158, the model, runner, 1,519-character instruction, gates, and exact-root definitions were frozen before any measured session."),
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": metric_ids},
        base.markdown("gate_read", "## Reliability passes; both lower-baseline efficiency conditions fail\n\nCorrectness and first-check reliability pass at 24/24 for every language. Parley exceeds Python's token median by **4.47%** and Rust's by **1.64%**, so the token condition fails. Parley takes **12.36%** longer than Python but **9.82%** less time than Rust; because the preregistered threshold is the faster baseline, elapsed also fails. Exact-root maintainability passes 24/24."),
        {"id": "gate_table_block", "type": "table", "tableId": "gate_table", "layout": "full"},
        {"id": "language_table_block", "type": "table", "tableId": "language_table", "layout": "full"},
        base.markdown("tokens", "## The token gap is small, consistent, and not repair-driven\n\nMedian tokens/repository are 15,704.50 for Parley, 15,033.00 for Python, and 15,451.38 for Rust. Weighted all-session values preserve the same ordering at 15,702.25, 15,034.63, and 15,451.67. Every session is repair-free, so report 031's reliability-driven efficiency advantage has disappeared on these new mechanisms."),
        {"id": "token_chart_block", "type": "chart", "chartId": "token_chart", "layout": "full"},
        base.markdown("distribution", "## All 18 sessions support the aggregate ordering\n\nParley's range is 15,658.25–15,751.75 tokens/repository, Python's is 15,000.00–15,085.50, and Rust's is 15,431.50–15,474.75. The bands do not overlap between languages in this run. That makes the directional finding robust to these six retained replicates, while still leaving the absolute gap modest."),
        {"id": "session_chart_block", "type": "chart", "chartId": "session_chart", "layout": "full"},
        base.markdown("elapsed", "## Parley remains faster than Rust but not Python\n\nParley's median 8.4545 seconds/repository sits between Python at 7.5247 and Rust at 9.3756. Complete ranges overlap, so these six timing replicates support only the preregistered median decision—not a universal runtime ranking. The elapsed gate fails because it requires Parley to match the faster baseline."),
        {"id": "elapsed_chart_block", "type": "chart", "chartId": "elapsed_chart", "layout": "full"},
        base.markdown("source", "## Editable source is between Python and Rust, but prompt context is larger\n\nMedian final editable source is 271.75 rough tokens/repository for Parley, 226.75 for Python, and 376.00 for Rust. Median prompt text is 1,111 characters/repository for Parley versus about 690 for both baselines because the unchanged Parley skill is injected once per session. The result does not isolate how much of the 671.5-token Python gap comes from instruction context versus source representation; it establishes only the complete observed cost."),
        {"id": "source_chart_block", "type": "chart", "chartId": "source_chart", "layout": "full"},
        base.markdown("root", "## Diagnosis quality is perfect across all four projects\n\nAll 72 patches touch exactly one file, and it is the owning defect location frozen before output. Every read-only issue, architecture, and regression artifact remains unchanged. Each project is 18/18 first-check-correct and hidden-correct across languages. Parley and Python converge on one final variant per task; Rust has two equivalent variants for normalization and pagination."),
        {"id": "task_table_block", "type": "table", "tableId": "task_table", "layout": "full"},
        {"id": "root_table_block", "type": "table", "tableId": "root_table", "layout": "full"},
        base.markdown("integrity", "## The run is complete, fresh, and unrepaired\n\nAll 18 planned sessions ran once and are retained under unique thread IDs. Every session starts with the protected source dump, makes a file change, invokes exactly one check, exits zero, preserves checker/context hashes, passes hidden judgment, and complies with the command protocol. There are no timeouts, agent errors, excluded cells, or selective reruns."),
        {"id": "command_table_block", "type": "table", "tableId": "command_table", "layout": "full"},
        {"id": "session_table_block", "type": "table", "tableId": "session_table", "layout": "full"},
        base.markdown("method", "## Frozen method and provenance\n\n- **Matrix:** four projects × three languages × six complete-bundle replicates = 18 sessions and 72 assignments; seed `320260805`.\n- **Toolchain:** pinned Parley 0.3.158, `gpt-5.6-sol` medium, Codex CLI runner.\n- **Product checkpoint:** workflow implementation commit `cb7820a`; no compiler or benchmark-instruction change.\n- **Corpus:** commit `d435ecd`, manifest SHA `49df28a2…`; all reference fixes pass 60/60 isolated cases.\n- **Protocol:** commit `0919607`, SHA `d702c340…`, committed before output.\n- **Instruction:** unchanged 1,519-character skill, SHA `6ca098e4…`; the compression experiment remains closed.\n- **Result:** raw SHA `0600ca9e…`; every planned cell ran once and remains in the report."),
        base.markdown("limits", "## Limits and robustness\n\nThe mechanisms are grounded in independent primary issue reports, but the executable repositories are deterministic cross-language adaptations, not the upstream production codebases. Six replicates cleanly establish this benchmark's direction, not population-level superiority. Reported tokens include the full model context across the agent turn; source and edit sizes are rough lexical estimates. Cross-report comparison with 031 is descriptive because every task mechanism changed."),
        base.markdown("decision", "## Decision: preserve the product, do not tune the language\n\n1. Preserve report 031 as its own positive result and report 032 as a clean independent non-confirmation.\n2. Treat reliability and exact-root diagnosis as the repeated strength: 72/72 first-check and hidden-correct, 24/24 exact Parley roots.\n3. Make no syntax, compiler, diagnostic, prompt, runner, task, or metric change from this corpus.\n4. Continue product dogfooding and collect real workflow friction; JSON remains a candidate only if it recurs in actual products, while CSV remains deferred.\n5. The next benchmark should use a mature external repository or a real Parley release operation, preregistered before output, where history, dependency search, and ambiguous evidence dominate fixture size."),
        base.markdown("questions", "## Further questions\n\n- Does the exact-root reliability persist on a mature repository with history and dependency navigation?\n- How much of Parley's small complete-token premium is fixed instruction context versus editable source?\n- Which missing data capability recurs across real installed workflows strongly enough to justify a general language feature?", False),
    ]
    artifact["snapshot"] = {"version": 1, "generatedAt": generated_at, "status": "ready", "datasets": datasets}
    artifact["sources"] = [{
        "id": SOURCE_ID,
        "label": "Frozen iteration 032 independent confirmation",
        "path": f"{STEM}.sql",
        "query": {
            "engine": "SQLite JSON1 + Python statistics",
            "query": f"python3 benchmarks/reports/build_032_report.py && sqlite3 ':memory:' < benchmarks/reports/{STEM}.sql",
            "description": "Reproducible aggregation of all 18 sessions, 72 judgments, frozen gate conditions, exact-root scope, event integrity, source size, and complete distributions.",
            "executed_at": generated_at,
            "language": "SQL / Python",
            "metric_definitions": [
                "Tokens per repository: reported session input plus output tokens divided by four assigned repositories.",
                "Strict primary gate: correctness, median tokens, median elapsed, and first-check rate must all satisfy the frozen better-baseline direction.",
                "Exact root: changed-files contains only the owning defect file frozen before measured output.",
                "Overall conditions: four primary conditions plus the separate exact-root maintainability condition.",
            ],
        },
    }]
    artifact["package_info"] = {"root": "benchmarks/results", "manifestPath": f"{STEM}.artifact.json", "snapshotPath": RAW_NAME, "originUrl": "artifact://parley-independent-confirmation-032"}
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
       json_extract(run.value,'$.thread_id') AS thread_id
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
    return """# Iteration 032 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does report 031's strict deeper-project efficiency win
  replicate on four independently selected mechanisms after product work?
- Decision-useful answer: reliability and exact-root quality repeat perfectly,
  but strict efficiency/reliability finishes 2/4 and overall finishes 3/5.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Tokens | Did strict token parity repeat? | Category comparison / bar | language, median_tokens_task | Parley trails Python by 4.47% and Rust by 1.64% | Single-root palette; axis labels identify language |
| Distribution | Is one outlier driving the result? | Grouped discrete comparison / bar | replicate, language, tokens_task | All 18 sessions preserve the aggregate ordering | Relaxed three-language palette |
| Elapsed | Did strict time parity repeat? | Category comparison / bar | language, median_seconds_task | Parley trails Python and beats Rust | Single-root palette; axis labels identify language |
| Source | Is complete effort aligned with editable source size? | Grouped stage comparison / bar | language, stage, rough_tokens_task | Parley source sits between Python and Rust | Hard two-stage palette |

Correctness, exact-root scope, task cuts, action protocol, and all session
values remain in metric cards and audit tables. Each chart answers a distinct
decision and is paired with adjacent interpretation.
"""


def validate(raw: dict, tasks: dict) -> None:
    rows = raw["results"]
    roots = tasks["predeclared_analysis"]["root_cause_files"]
    assert len(rows) == 18 and sum(row["task_count"] for row in rows) == 72
    assert len({row["thread_id"] for row in rows}) == 18
    assert raw["summary"]["strict_gate"]["conditions"] == {"correctness": True, "tokens": False, "elapsed": False, "first_check": True}
    for row in rows:
        assert row["fresh_ephemeral_session"] and row["agent_returncode"] == 0 and not row["agent_timed_out"]
        assert row["check_integrity_ok"] and row["command_protocol_compliant"] and not row["agent_errors"]
        assert row["hidden_bundle_success"] and row["public_check_attempts"] == 1 and row["repair_turns"] == 0
        for task_id, task in row["task_results"].items():
            assert task["first_public_check_success"] and task["hidden_success"]
            assert task["changed_files"] == [roots[task_id][row["language"]]]


def main() -> None:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    tasks = json.loads(TASK_MANIFEST.read_text(encoding="utf-8"))
    validate(raw, tasks)
    old = load_module("build_031_report.py", "parley_report_031")
    base = old.load_base()
    old.SOURCE_ID = SOURCE_ID
    base.SOURCE_ID = SOURCE_ID
    datasets = build_datasets(raw, tasks, old)
    artifact = build_artifact(raw, datasets, old, base)
    (REPORTS / f"{STEM}.artifact.json").write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    (REPORTS / f"{STEM}.sql").write_text(build_sql(), encoding="utf-8")
    (REPORTS / f"{STEM}.chart-map.md").write_text(build_chart_map(), encoding="utf-8")
    print(json.dumps({"artifact": str(REPORTS / f"{STEM}.artifact.json"), "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(), "datasets": {key: len(value) for key, value in datasets.items()}}, indent=2))


if __name__ == "__main__":
    main()
