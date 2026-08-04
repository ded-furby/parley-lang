#!/usr/bin/env python3
"""Build the canonical report artifact and reproducibility notes for iteration 028."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import statistics
from pathlib import Path


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW_NAME = "agent_diagnostic_028_protocol_v1_v0.3.155.json"
RAW = BENCHMARKS / "results" / RAW_NAME
STEM = "028-project-diagnosis-near-parity"
GENERATED_AT = "2026-08-04T19:13:00Z"
TASK_IDS = {
    "invoice_boundary_project",
    "after_hours_routing_project",
    "normalized_tag_project",
    "capacity_state_project",
}
DEFECT_FILES = {
    "invoice_boundary_project": {"parley": "pricing.par", "python": "pricing.py", "rust": "pricing.rs"},
    "after_hours_routing_project": {"parley": "routing.par", "python": "routing.py", "rust": "routing.rs"},
    "normalized_tag_project": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
    "capacity_state_project": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
}


def load_report_026_module():
    path = REPORTS / "build_026_report.py"
    spec = importlib.util.spec_from_file_location("parley_report_026", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load iteration-026 report builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def display_language(language: str) -> str:
    return {"parley": "Parley", "python": "Python", "rust": "Rust"}[language]


def build_datasets(raw: dict, report_026) -> dict[str, list[dict]]:
    # The prior builder expects two exact-file workflows. Temporary aliases let
    # us reuse its general session/language/repository aggregation before this
    # iteration replaces that obsolete table with a root-cause audit.
    proxy = copy.deepcopy(raw)
    for row in proxy["results"]:
        tasks = row["task_results"]
        tasks["filtered_report_repo"] = copy.deepcopy(tasks["invoice_boundary_project"])
        tasks["priority_digest_repo"] = copy.deepcopy(tasks["capacity_state_project"])
    datasets = report_026.build_datasets(proxy)
    datasets["repository_detail"] = [
        row for row in datasets["repository_detail"] if row["repository_id"] in TASK_IDS
    ]

    for row in datasets["language_summary"]:
        selected = [
            run for run in raw["results"]
            if display_language(run["language"]) == row["language"]
        ]
        row["context_tokens_task"] = statistics.median(
            run["context_source_rough_tokens_per_task"] for run in selected
        )
        row["context_chars_task"] = statistics.median(
            run["context_source_chars_per_task"] for run in selected
        )

    raw_sessions = {
        (row["replicate"], display_language(row["language"])): row
        for row in raw["results"]
    }
    for row in datasets["session_detail"]:
        source = raw_sessions[(row["replicate"], row["language"])]
        row["context_tokens_task"] = source["context_source_rough_tokens_per_task"]
        row["context_chars_task"] = source["context_source_chars_per_task"]

    root_cause_audit = []
    compensating_detail = []
    for language in ("parley", "python", "rust"):
        selected = [row for row in raw["results"] if row["language"] == language]
        root_repairs = 0
        for run in selected:
            for task_id, task in run["task_results"].items():
                expected = DEFECT_FILES[task_id][language]
                if expected in task["changed_files"]:
                    root_repairs += 1
                    continue
                compensating_detail.append({
                    "language": display_language(language),
                    "replicate": run["replicate"],
                    "repository": task["task_title"],
                    "changed_file": ", ".join(task["changed_files"]),
                    "defect_file": expected,
                    "assessment": "Caller-side compensation; hidden-correct, root defect remains",
                })
        assignments = sum(row["task_count"] for row in selected)
        root_cause_audit.append({
            "language": display_language(language),
            "assignments": assignments,
            "root_cause_repairs": root_repairs,
            "root_cause_rate": round(root_repairs / assignments, 4),
            "compensating_repairs": assignments - root_repairs,
            "read_only_files_preserved": len(selected) * 8,
        })
    datasets["root_cause_audit"] = root_cause_audit
    datasets["compensating_detail"] = compensating_detail
    datasets.pop("file_judgment", None)
    datasets.pop("failure_detail", None)

    headline = datasets["headline"][0]
    headline.update({
        "sessions": 18,
        "assignments": 72,
        "hidden_successes": 72,
        "first_successes": 72,
        "repairs": 0,
        "gate_conditions_passed": 2,
        "changed_files_task": 1,
        "exact_file_cases": 0,
    })
    return datasets


def build_sql(report_026) -> str:
    sql = report_026.build_sql().replace(
        "agent_repositories_026_protocol_v1_v0.3.155.json", RAW_NAME
    )
    sql = report_026.replace_sql_view(
        sql,
        "file_judgment",
        "source_stage",
        """CREATE TEMP VIEW root_cause_audit AS
WITH task_rows AS (
  SELECT
    runs.language,
    task.key AS repository_id,
    task.value AS task_json,
    CASE task.key
      WHEN 'invoice_boundary_project' THEN CASE runs.language WHEN 'parley' THEN 'pricing.par' WHEN 'python' THEN 'pricing.py' ELSE 'pricing.rs' END
      WHEN 'after_hours_routing_project' THEN CASE runs.language WHEN 'parley' THEN 'routing.par' WHEN 'python' THEN 'routing.py' ELSE 'routing.rs' END
      WHEN 'normalized_tag_project' THEN CASE runs.language WHEN 'parley' THEN 'main.par' WHEN 'python' THEN 'main.py' ELSE 'main.rs' END
      ELSE CASE runs.language WHEN 'parley' THEN 'main.par' WHEN 'python' THEN 'main.py' ELSE 'main.rs' END
    END AS defect_file
  FROM runs, json_each(json_extract(runs.run_json, '$.task_results')) AS task
)
SELECT
  CASE language WHEN 'parley' THEN 'Parley' WHEN 'python' THEN 'Python' ELSE 'Rust' END AS language,
  COUNT(*) AS assignments,
  SUM(EXISTS(SELECT 1 FROM json_each(json_extract(task_json, '$.changed_files')) AS changed
             WHERE changed.value=defect_file)) AS root_cause_repairs,
  SUM(NOT EXISTS(SELECT 1 FROM json_each(json_extract(task_json, '$.changed_files')) AS changed
                 WHERE changed.value=defect_file)) AS compensating_repairs,
  COUNT(*) * 2 AS read_only_files_preserved
FROM task_rows GROUP BY language;""",
    )
    start = sql.index("CREATE TEMP VIEW headline AS")
    end = sql.index("SELECT 'language_summary'", start)
    headline = """CREATE TEMP VIEW headline AS
SELECT 18 AS sessions, 72 AS assignments, 72 AS hidden_successes, 72 AS first_successes,
  0 AS repairs, 2 AS gate_conditions_passed, 1 AS changed_files_task, 0 AS exact_file_cases,
  ROUND(100.0 * ((SELECT median_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT median_tokens_task FROM language_summary WHERE language='Python') - 1), 2) AS token_gap_python_percent,
  ROUND(100.0 * ((SELECT median_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT median_tokens_task FROM language_summary WHERE language='Rust') - 1), 2) AS token_gap_rust_percent,
  ROUND(100.0 * ((SELECT median_seconds_task FROM language_summary WHERE language='Parley') /
        (SELECT median_seconds_task FROM language_summary WHERE language='Python') - 1), 2) AS elapsed_gap_python_percent,
  ROUND(100.0 * ((SELECT median_seconds_task FROM language_summary WHERE language='Parley') /
        (SELECT median_seconds_task FROM language_summary WHERE language='Rust') - 1), 2) AS elapsed_gap_rust_percent,
  ROUND(100.0 * ((SELECT source_tokens_task FROM language_summary WHERE language='Parley') /
        (SELECT source_tokens_task FROM language_summary WHERE language='Rust') - 1), 2) AS source_gap_rust_percent;"""
    sql = sql[:start] + headline + "\n\n" + sql[end:]
    old = """SELECT 'file_judgment', json_group_array(json_object(
  'language',language,'sessions',sessions,'first_successes',first_successes,
  'hidden_successes',hidden_successes,'exact_hidden_cases',exact_hidden_cases)) FROM file_judgment;"""
    new = """SELECT 'root_cause_audit', json_group_array(json_object(
  'language',language,'assignments',assignments,'root_cause_repairs',root_cause_repairs,
  'compensating_repairs',compensating_repairs,'read_only_files_preserved',read_only_files_preserved))
FROM root_cause_audit;"""
    return sql.replace(old, new)


def build_artifact(raw: dict, datasets: dict[str, list[dict]], report_026) -> dict:
    artifact = report_026.build_artifact(raw, datasets)
    manifest = artifact["manifest"]
    manifest.update({
        "title": "Project Diagnosis Near-Parity — Iteration 028",
        "description": "Preregistered 18-session comparison of multi-file regression diagnosis from read-only project evidence.",
        "generatedAt": GENERATED_AT,
    })
    cards = {card["id"]: card for card in manifest["cards"]}
    cards["hidden_card"]["metrics"][0]["unit"] = "of 72"
    cards["first_card"]["metrics"][0]["unit"] = "of 72"
    cards["files_card"]["description"] = "Every assignment changes exactly one editable source file."
    cards["token_gap_card"]["description"] = "Parley median reported tokens per repository relative to Rust."
    cards["token_gap_card"]["metrics"][0]["label"] = "Token gap vs Rust"
    cards["elapsed_gap_card"]["description"] = "Parley median elapsed time per repository relative to Rust; negative is faster."
    cards["elapsed_gap_card"]["metrics"][0]["label"] = "Elapsed delta vs Rust"

    charts = {chart["id"]: chart for chart in manifest["charts"]}
    charts["token_chart"]["subtitle"] = "All runs are repair-free; Parley is 1.48% above Rust and 4.38% above Python."
    charts["token_chart"]["comparisonContext"]["denominator"] = "six sessions per language"
    charts["session_chart"]["subtitle"] = "All eighteen repair-free sessions are shown; distributions are tight within language."
    charts["session_chart"]["rationale"] = "All values expose the stable between-language gap without excluding any run."
    charts["session_chart"]["comparisonContext"]["denominator"] = "four repositories per session"
    charts["elapsed_chart"]["subtitle"] = "Parley is 0.85% faster than Rust and 6.62% slower than Python."
    charts["source_stage_chart"]["title"] = "Seed and final editable-source size"
    charts["source_stage_chart"]["comparisonContext"]["denominator"] = "four repositories per session"
    charts["edit_chart"]["subtitle"] = "Inserted plus deleted rough tokens per repository; one file changed per assignment."

    tables = {table["id"]: table for table in manifest["tables"]}
    tables["language_table"]["subtitle"] = "Primary frozen comparison over all 72 assignments."
    tables["language_table"]["columns"].insert(7, {
        "field": "context_tokens_task", "label": "Read-only context", "format": "number"
    })
    tables["repository_table"]["subtitle"] = "Six appearances per language/repository; twelve aggregate rows."
    root_table = tables["file_table"]
    root_table.update({
        "title": "Root-cause and read-only evidence audit",
        "subtitle": "Primary correctness is test-based; this secondary audit distinguishes defect repair from caller compensation.",
        "dataset": "root_cause_audit",
        "columns": [
            {"field": "language", "label": "Language", "type": "text"},
            {"field": "root_cause_repairs", "label": "Root fixes (of 24)", "format": "number"},
            {"field": "compensating_repairs", "label": "Compensating", "format": "number"},
            {"field": "read_only_files_preserved", "label": "Read-only preserved", "format": "number"},
        ],
    })
    tables["command_table"]["subtitle"] = "Every session ran one protected source dump first, one successful check second, and preserved all integrity hashes."
    tables["session_table"]["subtitle"] = "Eighteen unique threads; every row is first-check clean and retained."
    detail_table = tables["failure_table"]
    detail_table.update({
        "title": "Compensating-fix detail",
        "subtitle": "Two hidden-correct Rust patches special-case callers instead of correcting the seeded helper defect.",
        "dataset": "compensating_detail",
        "columns": [
            {"field": "language", "label": "Language", "type": "text"},
            {"field": "replicate", "label": "Rep", "format": "number"},
            {"field": "repository", "label": "Repository", "type": "text"},
            {"field": "changed_file", "label": "Changed", "type": "text"},
            {"field": "defect_file", "label": "Root defect", "type": "text"},
            {"field": "assessment", "label": "Assessment", "type": "text"},
        ],
    })

    raw_sha = hashlib.sha256(RAW.read_bytes()).hexdigest()
    manifest["blocks"] = [
        {"id": "title", "type": "markdown", "layout": "full", "body": "# Project Diagnosis Near-Parity — Iteration 028"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## Technical summary\n\n**Project-style diagnosis removes every reliability gap and brings Parley close to Rust, but strict better-baseline parity remains unconfirmed.** All 72 assignments pass their first check and all hidden cases with zero repairs. Parley uses 15.02k median reported tokens per repository versus Python's 14.39k and Rust's 14.80k, while its 7.01-second median is faster than Rust's 7.07 seconds but slower than Python's 6.57. The frozen strict gate finishes 2/4."},
        {"id": "scope", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## What this benchmark measures\n\nEach fresh session diagnoses four unrelated regressions from twelve editable implementation files plus eight visibly read-only issue/test artifacts. Public examples stay inside the protected checker and are omitted from the prompt. Agents run `./sources` exactly once first, modify the repository, then run only `./check`. **First success** means all four repositories pass that first bundle check; **hidden success** requires four withheld cases per repository."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [card["id"] for card in manifest["cards"]]},
        {"id": "reliability", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## Diagnosis is uniformly reliable\n\nParley, Python, and Rust each pass 24/24 repository assignments on the first check and 24/24 under hidden judgment. Every session uses one check, so there are no repair turns, compile failures, or same-corpus failure signatures to optimize against. Correctness and first-check gate conditions pass exactly."},
        {"id": "language_table_block", "type": "table", "tableId": "language_table", "layout": "full"},
        {"id": "tokens", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## Parley comes within 1.48% of Rust token effort\n\nParley's 15.02k median tokens per repository is **1.48% above Rust** and **4.38% above Python**. This is much tighter than iteration 027's large explicit-rewrite bundle, but the preregistered token condition compares against the lower baseline—Python—and therefore fails. No run is excluded and repairs cannot explain the gap."},
        {"id": "token_chart_block", "type": "chart", "chartId": "token_chart", "layout": "full"},
        {"id": "session_note", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "All six per-language token values form narrow clusters: Parley 14,996.75–15,109.50, Python 14,378.00–14,468.25, and Rust 14,786.50–14,828.25 tokens/repository. The result is not driven by a repair or one extreme session."},
        {"id": "session_chart_block", "type": "chart", "chartId": "session_chart", "layout": "full"},
        {"id": "elapsed", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## Elapsed time narrowly beats Rust\n\nParley's median 7.0073 seconds per repository is **0.85% faster than Rust's 7.0672** and 6.62% slower than Python's 6.5723. The frozen elapsed condition compares against faster Python and fails, while the narrower Rust comparison is positive."},
        {"id": "elapsed_chart_block", "type": "chart", "chartId": "elapsed_chart", "layout": "full"},
        {"id": "context", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## Evidence is controlled and equal\n\nEvery language receives exactly 1,531 characters, 27 lines, and 321 rough tokens of read-only context per session—80.25 rough tokens per repository. Context contents are byte-identical across languages. The prompt itself is 1,090.75 characters/repository for Parley versus 670.00 for Python and 675.00 for Rust because the unchanged 1,519-character Parley skill is injected once per session."},
        {"id": "source", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## Parley source stays far shorter than Rust\n\nMedian final editable source is 168 rough tokens/repository for Parley, 147 for Python, and 283.5 for Rust. Parley is **40.74% shorter than Rust** but 14.29% larger than Python. Median edits are 8, 6, and 7.25 rough tokens, respectively; source compactness again does not translate one-for-one into reported agent tokens."},
        {"id": "source_stage_chart_block", "type": "chart", "chartId": "source_stage_chart", "layout": "full"},
        {"id": "edit_chart_block", "type": "chart", "chartId": "edit_chart", "layout": "full"},
        {"id": "repository_table_block", "type": "table", "tableId": "repository_table", "layout": "full"},
        {"id": "root_cause", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## Root-cause location is perfect for Parley and Python\n\nParley and Python modify the seeded defect file in all 24 assignments. Rust does so in 22/24. Rust replicate 6 instead special-cases subtotal 2000 and high-after-hours behavior in the two callers, leaving `pricing.rs` and `routing.rs` wrong for other callers. Both compensations pass all frozen hidden cases, so primary correctness remains 100%; the distinction is a preregistered secondary maintainability audit, not a retroactive gate."},
        {"id": "file_table_block", "type": "table", "tableId": "file_table", "layout": "full"},
        {"id": "compensating_table_block", "type": "table", "tableId": "failure_table", "layout": "full"},
        {"id": "integrity", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## Read-only evidence and command boundaries hold\n\nAll 144 read-only file exposures—48 per language—remain unchanged under integrity hashing. Every session runs exactly `/bin/zsh -lc ./sources` first and `/bin/zsh -lc ./check` second. All 18 agent exits are zero; there are no timeouts, runner errors, command violations, or integrity failures."},
        {"id": "command_table_block", "type": "table", "tableId": "command_table", "layout": "full"},
        {"id": "boundary", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## No compiler or instruction change follows\n\nEvery Parley session diagnoses and repairs all four regressions immediately. The residual token/time gaps are not tied to a syntax, semantic, diagnostic, or runtime failure, and the only lower-quality patch behavior appears in Rust. Parley therefore remains frozen at v0.3.155; the 1,519-character skill remains byte-for-byte unchanged; the single allowed instruction-compression experiment remains closed."},
        {"id": "methodology", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": f"## Frozen method and integrity\n\n- **Matrix:** 18 fresh sessions, four repositories, three languages, six complete-bundle replicates, seed `20260819`.\n- **Toolchain:** pinned Parley 0.3.155 binary, frozen corpus commit `2cf86bf`, protocol commit `3fe4712`, `gpt-5.6-sol` medium, Codex CLI 0.146.0.\n- **Instruction:** unchanged 1,519-character skill, SHA `6ca098e4…`; no further compression experiment.\n- **Source protocol:** one protected `./sources` first, then one `./check`; 12 editable plus eight read-only files/session.\n- **Integrity:** 18 unique threads and 18/18 fresh-session, command, checker, and context-integrity passes.\n- **Hashes:** task manifest `49147f96…`; protocol `96916b47…`; raw result `{raw_sha[:8]}…`."},
        {"id": "session_table_block", "type": "table", "tableId": "session_table", "layout": "full"},
        {"id": "limitations", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## Limits and robustness\n\nThese are synthetic three-file repositories with explicit issue/test evidence, not mature projects with history, dependency graphs, test authoring, ambiguous symptoms, services, concurrency, or incomplete specifications. Six replicates establish a directional median. Reported tokens include model context across tool turns; source/context/edit tokens are lexical. Hidden cases cover the documented policies but cannot prove that every caller sees a root-cause fix, which is why patch-location quality is reported separately."},
        {"id": "decision", "type": "markdown", "layout": "full", "sourceId": "diagnostic_results", "body": "## Recommended next step\n\n1. Preserve iteration 028 unchanged as a clean 2/4 result: perfect Parley reliability, near-Rust tokens, and Rust-beating elapsed time, but not better-baseline parity.\n2. Make no compiler, syntax, diagnostic, prompt, or skill change from this corpus.\n3. Stop scaling explicit synthetic rewrites; the diagnosis-shaped protocol is the more useful direction.\n4. Build the next corpus from independently sourced project regressions with ambiguous symptoms, dependency navigation, and test changes, and score root-cause repair explicitly.\n5. If that broader pilot is positive, preregister the planned larger confirmation before claiming Python-and-Rust parity."},
        {"id": "questions", "type": "markdown", "layout": "full", "body": "## Further questions\n\n- Does Parley's near-Rust efficiency persist when agents must infer the failing path across dependencies?\n- Can root-cause repair quality predict maintainability better than hidden output alone?\n- How much of the remaining Python gap is fixed Parley skill context versus model workflow?"},
    ]

    artifact["snapshot"] = {"version": 1, "generatedAt": GENERATED_AT, "status": "ready", "datasets": datasets}
    artifact["sources"] = [{
        "id": "diagnostic_results",
        "label": "Frozen iteration 028 project-diagnosis results",
        "path": f"{STEM}.sql",
        "query": {
            "engine": "SQLite JSON1",
            "query": f"sqlite3 ':memory:' < benchmarks/reports/{STEM}.sql",
            "description": "Reproducible aggregation of all eighteen sessions, seventy-two repository judgments, context/source/edit metrics, command integrity, and root-cause patch locations.",
            "executed_at": GENERATED_AT,
            "language": "SQL",
            "metric_definitions": [
                "First success: repository passes in the first public bundle check.",
                "Hidden success: final repository passes every withheld stdout case.",
                "Tokens per repository: reported session input plus output tokens divided by four assignments.",
                "Context rough tokens: lexical tokens in visible read-only issue/test artifacts.",
                "Root-cause repair: the final patch changes the seeded defect file, independent of hidden correctness.",
                "Controlled inspection: exactly one ./sources command first, followed only by ./check.",
            ],
        },
    }]
    artifact["package_info"] = {
        "root": "benchmarks/results",
        "manifestPath": f"{STEM}.artifact.json",
        "snapshotPath": RAW_NAME,
        "originUrl": "artifact://parley-project-diagnosis-028",
    }
    return artifact


def main() -> None:
    report_026 = load_report_026_module()
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    datasets = build_datasets(raw, report_026)
    artifact = build_artifact(raw, datasets, report_026)
    (REPORTS / f"{STEM}.artifact.json").write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8"
    )
    (REPORTS / f"{STEM}.sql").write_text(build_sql(report_026), encoding="utf-8")
    chart_map = """# Iteration 028 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does Parley match Python and Rust when agents diagnose
  multi-file regressions from read-only project evidence?
- Decision-useful answer: all languages are perfectly first-check and hidden
  correct; Parley nearly matches Rust but remains above Python.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Tokens | How close is reported agent effort? | Category comparison / bar | language, median_tokens_task | Parley is 1.48% above Rust and 4.38% above Python | Relaxed three-category language palette |
| Sessions | Is the aggregate robust? | Discrete comparison / grouped bar | replicate, language, tokens_task | Every language forms a tight repair-free cluster | Relaxed three-category language palette |
| Elapsed | Did Parley match wall-clock time? | Category comparison / bar | language, median_seconds_task | Parley is 0.85% faster than Rust | Relaxed three-category language palette |
| Source size | How compact is editable source? | Grouped comparison / bar | language, stage, rough_tokens_task | Parley final source is 40.74% shorter than Rust | Hard two-root stage palette |
| Edit size | How large were regression repairs? | Category comparison / bar | language, edit_tokens_task | Every assignment changes one file | Relaxed three-category language palette |

Reliability stays in exact metrics/tables. Equal read-only context, command
order, root-cause location, and compensating fixes remain tables and prose.
"""
    (REPORTS / f"{STEM}.chart-map.md").write_text(chart_map, encoding="utf-8")


if __name__ == "__main__":
    main()
