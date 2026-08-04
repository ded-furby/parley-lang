#!/usr/bin/env python3
"""Build the canonical report artifact and reproducibility notes for iteration 027."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW_NAME = "agent_repositories_027_protocol_v1_v0.3.155.json"
RAW = BENCHMARKS / "results" / RAW_NAME
STEM = "027-sixteen-repository-scale-regression"
GENERATED_AT = "2026-08-04T18:43:43Z"


def load_report_026_module():
    path = REPORTS / "build_026_report.py"
    spec = importlib.util.spec_from_file_location("parley_report_026", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load iteration-026 report builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_sql() -> str:
    sql = (REPORTS / "026-eight-repository-expansion-failed.sql").read_text()
    sql = sql.replace(
        "agent_repositories_026_protocol_v1_v0.3.155.json", RAW_NAME
    )
    sql = sql.replace(
        "SELECT 18 AS sessions, 144 AS assignments, 144 AS hidden_successes, 142 AS first_successes,",
        "SELECT 18 AS sessions, 288 AS assignments, 288 AS hidden_successes, 287 AS first_successes,",
    )
    sql = sql.replace(
        "1 AS repairs, 1 AS gate_conditions_passed, 2 AS changed_files_task, 144 AS exact_file_cases,",
        "1 AS repairs, 2 AS gate_conditions_passed, 1.9375 AS changed_files_task, 144 AS exact_file_cases,",
    )
    return sql


def build_artifact(raw: dict, datasets: dict[str, list[dict]], report_026) -> dict:
    artifact = report_026.build_artifact(raw, datasets)
    manifest = artifact["manifest"]
    manifest.update({
        "title": "Sixteen-Repository Scale Regression — Iteration 027",
        "description": "Preregistered 18-session size-sixteen repository comparison with controlled source inspection and hidden tests.",
        "generatedAt": GENERATED_AT,
    })
    cards = {card["id"]: card for card in manifest["cards"]}
    cards["hidden_card"]["metrics"][0]["unit"] = "of 288"
    cards["first_card"]["metrics"][0]["unit"] = "of 288"
    cards["files_card"]["description"] = "Median changed source files per repository; one helper already satisfied the new contract."
    cards["token_gap_card"]["description"] = "Parley median reported tokens per repository relative to Rust."
    cards["token_gap_card"]["metrics"][0]["label"] = "Token gap vs Rust"
    cards["elapsed_gap_card"]["description"] = "Parley median elapsed time per repository relative to Rust; negative is faster."
    cards["elapsed_gap_card"]["metrics"][0]["label"] = "Elapsed delta vs Rust"

    charts = {chart["id"]: chart for chart in manifest["charts"]}
    charts["token_chart"]["subtitle"] = "Six fresh sixteen-repository sessions per language; Parley is repair-free but above both baselines."
    charts["session_chart"]["subtitle"] = "Parley splits into one-edit and two-edit action clusters despite identical correctness."
    charts["session_chart"]["rationale"] = "All 18 values expose edit-action batching, baseline outliers, and the primary median without exclusions."
    charts["session_chart"]["comparisonContext"]["denominator"] = "sixteen repositories per session"
    charts["elapsed_chart"]["subtitle"] = "Parley is 6.72% faster than Rust but 37.22% slower than Python."
    charts["source_stage_chart"]["comparisonContext"]["denominator"] = "sixteen repositories per session"

    tables = {table["id"]: table for table in manifest["tables"]}
    tables["language_table"]["subtitle"] = "Primary frozen comparison over all 288 assignments."
    tables["repository_table"]["subtitle"] = "Six appearances per language/repository; 48 aggregate rows."
    tables["file_table"]["subtitle"] = "Each language faced 12 file-repository assignments and 48 hidden exact-file cases."
    tables["command_table"]["subtitle"] = "Every session ran one protected source dump first and preserved integrity/protocol compliance."
    tables["session_table"]["subtitle"] = "Eighteen unique threads; Python's one repaired row remains visible."
    failure_table = next(table for table in manifest["tables"] if table["id"] == "failure_table")
    failure_table["title"] = "First-check failure classification"
    failure_table["subtitle"] = "One Python indentation typo in one session; Parley and Rust are fully first-check clean."

    manifest["blocks"] = [
        {"id": "title", "type": "markdown", "layout": "full", "body": "# Sixteen-Repository Scale Regression — Iteration 027"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## Technical summary\n\n**Doubling the repository bundle preserves perfect Parley reliability and Rust-beating elapsed time, but token efficiency regresses sharply.** All 288 assignments finish hidden-correct. Parley is uniquely 96/96 first-check clean and uses 7.68k median reported tokens per repository versus Python's 5.05k and Rust's 5.65k. Its 8.01-second median is below Rust's 8.59 seconds but above Python's 5.84. The frozen strict gate finishes 2/4."},
        {"id": "scope", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## What the size-sixteen benchmark measures\n\nEach fresh session maintains sixteen two-file repositories spanning pricing, inventory, routing, exact files, support policy, rollout, reconciliation, text normalization, classification, payroll, and stateful allocation. Agents run protected `./sources` exactly once to inspect thirty-two editable files, edit through entrypoint/helper boundaries, then run only `./check`. **First success** is an untouched first-bundle-check pass; **hidden success** requires four withheld cases per repository; tokens and elapsed time divide session totals by sixteen; edit size counts inserted plus deleted rough lexical tokens."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [card["id"] for card in manifest["cards"]]},
        {"id": "reliability", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## Parley reliability is perfect at the largest tested bundle\n\nParley and Rust pass 96/96 repositories on the first check and all hidden cases. Python first-checks 95/96 after one indentation typo in one session, then repairs and finishes 96/96 hidden-correct. Parley therefore passes the correctness and first-check gate conditions without any repair sensitivity."},
        {"id": "language_table_block", "type": "table", "tableId": "language_table", "layout": "full"},
        {"id": "tokens", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## Token effort loses the size-eight Rust advantage\n\nParley's 7.68k median reported tokens per repository is **35.84% above Rust** and **52.10% above Python**. The size-eight result was 1.48% below Rust, so fixed-context amortization alone does not explain or sustain parity. All Parley runs are repair-free; the token condition fails without a correctness confound."},
        {"id": "token_chart_block", "type": "chart", "chartId": "token_chart", "layout": "full"},
        {"id": "session_note", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "**Edit-action batching explains part, but not all, of Parley's regression.** Three Parley sessions apply all changes in one edit action and cluster at 6.98–7.03k tokens/repository; three split the same 31 changed files into two edit actions and cluster at 8.32–8.39k. Every run makes one source call and one successful check. The one-action median is 7.00k—still roughly 24% above Rust's primary median and 39% above Python's—so removing the extra edit turn would not establish parity."},
        {"id": "session_chart_block", "type": "chart", "chartId": "session_chart", "layout": "full"},
        {"id": "elapsed", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## Elapsed time still beats Rust\n\nParley's median 8.01 seconds per repository is **6.72% faster than Rust's 8.59 seconds** and 37.22% slower than Python's 5.84 seconds. Shorter generated maintenance patches and compiler behavior may contribute, but this run does not isolate causal components. The frozen elapsed condition compares against faster Python and fails."},
        {"id": "elapsed_chart_block", "type": "chart", "chartId": "elapsed_chart", "layout": "full"},
        {"id": "source", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## Source compactness persists without token parity\n\nMedian final Parley source is 180 rough tokens per repository versus Python's 148 and Rust's 297. Parley remains **39.38% shorter than Rust**, and its median edit is 21.39% smaller. Relative to Python, Parley final source is 21.53% larger and its edit is 15.35% larger. Compact source alone is therefore insufficient to predict agent token effort."},
        {"id": "source_stage_chart_block", "type": "chart", "chartId": "source_stage_chart", "layout": "full"},
        {"id": "edit_note", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "**Changed-file scope is semantically consistent across languages.** 270/288 assignments change both files. All 18 tag-dedup assignments change only the entrypoint because the existing helper already performs the required lowercase normalization and needs no modification. The 1.9375 median files/repository is thus a shared task property, not a language shortcut."},
        {"id": "edit_chart_block", "type": "chart", "chartId": "edit_chart", "layout": "full"},
        {"id": "repository_table_block", "type": "table", "tableId": "repository_table", "layout": "full"},
        {"id": "file", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## Exact files and controlled inspection pass completely\n\nAcross filtered reports and priority digests, all 144 hidden exact-file cases match byte-for-byte: 48 per language. Every session runs `./sources` first and exactly once, followed only by one or two `./check` commands. All checker and source-printer integrity hashes remain intact."},
        {"id": "file_table_block", "type": "table", "tableId": "file_table", "layout": "full"},
        {"id": "command_table_block", "type": "table", "tableId": "command_table", "layout": "full"},
        {"id": "failure", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## The only first-check failure belongs to Python\n\nPython replicate 1 introduces an unexpected indent in the ledger entrypoint. The checker identifies line 3, the agent removes the indentation, and the second check plus all hidden cases pass. Parley has no parse, type, runtime, hidden, or draft-signature failure across 96 assignments; Rust is also fully first-check clean."},
        {"id": "failure_table_block", "type": "table", "tableId": "failure_table", "layout": "full"},
        {"id": "boundary", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## No compiler or instruction change follows\n\nThe failed token condition is not tied to a recurring Parley syntax or semantic defect: every Parley program passes immediately. The observed edit-action split is model workflow behavior, and instructing one patch would alter the benchmark rather than improve the language. Parley remains frozen at v0.3.155 and the 1,519-character skill remains byte-for-byte unchanged."},
        {"id": "methodology", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## Frozen method and integrity\n\n- **Matrix:** 18 fresh sessions, sixteen two-file repositories, three languages, six complete-bundle replicates, seed `20260817`.\n- **Toolchain:** Parley 0.3.155, frozen harness/corpus commit `6d10ee1`, protocol commit `cf2e3d3`, `gpt-5.6-sol` medium, Codex CLI 0.146.0.\n- **Instruction:** unchanged 1,519-character skill, SHA `6ca098e4…`; the compression experiment remains closed.\n- **Source protocol:** exactly one protected `./sources` command first, then only `./check`; thirty-two editable files per session.\n- **Integrity:** 18 unique threads; 18/18 fresh-session, source-order, checker-integrity, and command-protocol checks; no timeout, nonzero exit, or runner error.\n- **Hashes:** task manifest `4d48c171…`; protocol `c9d06a37…`; raw result `9955e67c…`."},
        {"id": "session_table_block", "type": "table", "tableId": "session_table", "layout": "full"},
        {"id": "limitations", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## Limits and robustness\n\nThese are synthetic two-file repositories, not mature codebases with history, test authoring, dependencies, services, concurrency, or ambiguous bugs. Six replicates establish a directional median, not a population estimate across models. Reported tokens include repeated model context across tool turns; source/edit tokens are lexical. The Parley distribution is exactly split by one versus two edit actions, and Rust has one high-token run, so workflow variance is material. All correctness, file, command, and integrity claims are exact."},
        {"id": "decision", "type": "markdown", "layout": "full", "sourceId": "repository_results", "body": "## Recommended next step\n\n1. Preserve iteration 027 unchanged as a failed 2/4 strict-parity result.\n2. Keep iteration 026 as the positive size-eight Rust-efficiency result; do not generalize it to larger bundles.\n3. Stop increasing synthetic bundle size: size sixteen worsens token effort despite perfect reliability.\n4. Make no compiler, syntax, diagnostic, prompt, or skill change from this corpus.\n5. Shift the next study to independently sourced, real repository maintenance episodes with test changes and dependency navigation, or run a larger size-eight confirmation only if the narrower Rust-parity claim is the decision target. Python-and-Rust parity remains unconfirmed."},
        {"id": "questions", "type": "markdown", "layout": "full", "body": "## Further questions\n\n- Does Parley's size-eight Rust advantage replicate over more sessions, models, and real repositories?\n- Why do half of the Parley sessions split a semantically identical large patch while Python and Rust usually use one edit action?\n- Can real projects expose diagnostic or semantic advantages that synthetic first-check-clean tasks cannot measure?"},
    ]

    artifact["snapshot"] = {
        "version": 1,
        "generatedAt": GENERATED_AT,
        "status": "ready",
        "datasets": datasets,
    }
    artifact["sources"] = [{
        "id": "repository_results",
        "label": "Frozen iteration 027 repository results",
        "path": f"{STEM}.sql",
        "query": {
            "engine": "SQLite JSON1",
            "query": f"sqlite3 ':memory:' < benchmarks/reports/{STEM}.sql",
            "description": "Reproducible aggregation of all eighteen size-sixteen sessions, command order, edit-action distribution, changed-file scope, exact file judgments, failures, and source/edit metrics.",
            "executed_at": GENERATED_AT,
            "language": "SQL",
            "metric_definitions": [
                "First success: repository passes in the first public bundle check.",
                "Hidden success: final repository passes every withheld stdout and file case.",
                "Tokens per repository: reported session input plus output tokens divided by sixteen assignments.",
                "Edit rough tokens: inserted plus deleted rough lexical tokens across seeded files.",
                "Changed files: seeded files whose final UTF-8 content differs from the initial repository.",
                "Controlled inspection: exactly one ./sources shell command first, followed only by ./check.",
            ],
        },
    }]
    artifact["package_info"] = {
        "root": "benchmarks/results",
        "manifestPath": f"{STEM}.artifact.json",
        "snapshotPath": RAW_NAME,
        "originUrl": "artifact://parley-repository-expansion-027",
    }
    return artifact


def main() -> None:
    report_026 = load_report_026_module()
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    datasets = report_026.build_datasets(raw)
    datasets["failure_detail"] = [{
        "language": "Python",
        "replicate": 1,
        "repository": "Add tolerance-aware ledger reconciliation",
        "phase": "Compile",
        "signature": "Unexpected indentation",
        "diagnostic": "IndentationError: unexpected indent (main.py, line 3)",
        "resolution": "Removed stray indentation; next check passed",
    }]
    artifact = build_artifact(raw, datasets, report_026)
    (REPORTS / f"{STEM}.artifact.json").write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8"
    )
    (REPORTS / f"{STEM}.sql").write_text(build_sql(), encoding="utf-8")
    chart_map = """# Iteration 027 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does a second independent expansion preserve Rust parity
  and close the Python gap at size sixteen?
- Decision-useful answer: reliability remains perfect and Parley stays faster
  than Rust, but token effort regresses above both baselines.

## Required-structure mapping

Scope and metric definitions precede visual evidence. Technical summary,
findings, method, limitations/robustness, recommended next step, and further
questions retain the technical-report order.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Tokens | How close is reported agent effort? | Category comparison / bar | language, median_tokens_task | Parley is 35.84% above Rust and 52.10% above Python | Relaxed three-category language palette |
| Session distribution | Is the aggregate robust? | Discrete comparison / grouped bar | replicate, language, tokens_task | Parley splits by one versus two edit actions | Relaxed three-category language palette |
| Elapsed | Did Parley match wall-clock time? | Category comparison / bar | language, median_seconds_task | Parley is 6.72% faster than Rust, 37.22% slower than Python | Relaxed three-category language palette |
| Source size | How compact are seed and final repositories? | Grouped comparison / bar | language, stage, rough_tokens_task | Parley final source is 39.38% shorter than Rust | Hard two-root stage palette |
| Edit size | How large were maintenance patches? | Category comparison / bar | language, edit_tokens_task | Parley edits are 21.39% smaller than Rust | Relaxed three-category language palette |

Reliability stays in metrics/tables because differences are exact counts.
Failure classification, command order, changed-file scope, and exact-file
judgments remain tables.
"""
    (REPORTS / f"{STEM}.chart-map.md").write_text(chart_map, encoding="utf-8")


if __name__ == "__main__":
    main()
