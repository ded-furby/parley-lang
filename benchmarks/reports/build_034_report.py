#!/usr/bin/env python3
"""Build the canonical report artifact for agent-data confirmation 034."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "results" / "agent_data_confirmation_034.json"
STEM = "034-verified-toon-context-efficiency-win"
SOURCE_ID = "agent_data_confirmation_034"
RAW_SHA = "69906633e6ad762b69188aea489023f81602845b1feeae920e237457be0deb2f"
PROTOCOL_SHA = "a50cbe7952fd2d62c5c28f0a1a3a9adee3c8d74bc4f37342e51e07c2fd83d951"
TASKS_SHA = "9fa1588f06cc46a1e46984b67301e1aafccc46f8efaf19fc8104a743e553bfdc"
TASK_LABELS = {
    "aggregate-test-totals": "Aggregation",
    "exact-diagnostic-lookup": "Exact lookup",
    "filtered-slow-suites": "Filtering",
    "rollback-targets": "Rollback reasoning",
    "symbol-rename-plan": "Rename planning",
}


def card(card_id: str, label: str, field: str, description: str, unit: str = "") -> dict:
    metric = {"field": field, "label": label, "format": "number"}
    if unit:
        metric["unit"] = unit
    return {
        "id": card_id,
        "description": description,
        "dataset": "headline",
        "metrics": [metric],
        "sourceId": SOURCE_ID,
    }


def table(table_id: str, title: str, subtitle: str, dataset: str,
          columns: list[tuple[str, str, str]], sort_field: str,
          direction: str = "asc") -> dict:
    rendered = []
    for field, label, kind in columns:
        column = {"field": field, "label": label}
        if kind == "text":
            column["type"] = "text"
        else:
            column["format"] = kind
        rendered.append(column)
    return {
        "id": table_id,
        "title": title,
        "subtitle": subtitle,
        "dataset": dataset,
        "columns": rendered,
        "defaultSort": {"field": sort_field, "direction": direction},
        "density": "dense" if dataset in {"pair_detail", "task_summary"} else "spacious",
        "layout": "full",
        "sourceId": SOURCE_ID,
    }


def validate(raw: dict) -> None:
    assert raw["experiment_id"] == "agent-data-confirmation-034"
    assert raw["protocol_sha256"] == PROTOCOL_SHA
    assert raw["tasks_sha256"] == TASKS_SHA
    assert hashlib.sha256(RAW.read_bytes()).hexdigest() == RAW_SHA
    rows = raw["results"]
    summary = raw["summary"]
    assert len(rows) == 90 and summary["sessions"] == 90
    assert summary["unique_threads"] == 90
    assert len({row["thread_id"] for row in rows}) == 90
    assert all(row["returncode"] == 0 and not row["timed_out"] for row in rows)
    assert all(row["command_count"] == 0 and not row["agent_errors"] for row in rows)
    assert all(row["parse_success"] and row["exact_success"] for row in rows)
    assert summary["gate"]["passed"] is True
    assert summary["gate"]["conditions_passed"] == 5
    assert len(summary["pairs"]) == 45
    assert all(pair["input_token_delta"] < 0 and pair["total_token_delta"] < 0
               for pair in summary["pairs"])


def build_datasets(raw: dict) -> dict[str, list[dict]]:
    summary = raw["summary"]
    by_rep = {row["representation"]: row for row in summary["by_representation"]}
    json_row, toon_row = by_rep["json"], by_rep["toon"]
    input_saved = json_row["input_tokens"] - toon_row["input_tokens"]
    total_saved = json_row["total_tokens"] - toon_row["total_tokens"]
    input_percent = round(100.0 * input_saved / json_row["input_tokens"], 4)
    total_percent = round(100.0 * total_saved / json_row["total_tokens"], 4)
    representation_summary = []
    for name, row in (("Compact JSON", json_row), ("Verified TOON", toon_row)):
        representation_summary.append({
            "representation": name,
            "sessions": row["sessions"],
            "exact": row["exact_successes"],
            "parsed": row["parse_successes"],
            "tool_free": row["tool_free_sessions"],
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "total_tokens": row["total_tokens"],
            "median_total": row["median_total_tokens"],
            "median_seconds": row["median_elapsed_seconds"],
        })
    config_rows = []
    for row in summary["by_agent_config_and_representation"]:
        config_rows.append({
            "agent_config": row["agent_config"],
            "representation": "Compact JSON" if row["representation"] == "json" else "Verified TOON",
            "sessions": row["sessions"],
            "exact": row["exact_successes"],
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "total_tokens": row["total_tokens"],
            "median_total": row["median_total_tokens"],
            "median_seconds": row["median_elapsed_seconds"],
        })
    task_summary = []
    task_savings = []
    for task_id, label in TASK_LABELS.items():
        cuts = {
            representation: [
                row for row in raw["results"]
                if row["task_id"] == task_id and row["representation"] == representation
            ]
            for representation in ("json", "toon")
        }
        json_total = sum(row["total_tokens"] for row in cuts["json"])
        toon_total = sum(row["total_tokens"] for row in cuts["toon"])
        json_input = sum(row["usage"]["input_tokens"] for row in cuts["json"])
        toon_input = sum(row["usage"]["input_tokens"] for row in cuts["toon"])
        saved = json_total - toon_total
        saved_percent = round(100.0 * saved / json_total, 4)
        context = raw["context_contracts"][task_id]
        task_summary.append({
            "task": label,
            "family": next(row["task_family"] for row in raw["results"] if row["task_id"] == task_id),
            "json_correct": sum(row["exact_success"] for row in cuts["json"]),
            "toon_correct": sum(row["exact_success"] for row in cuts["toon"]),
            "json_input": json_input,
            "toon_input": toon_input,
            "json_total": json_total,
            "toon_total": toon_total,
            "saved_tokens": saved,
            "saved_percent": saved_percent,
            "json_context_chars": context["json_chars"],
            "toon_context_chars": context["toon_chars"],
        })
        task_savings.append({
            "task": label,
            "saved_percent": saved_percent,
            "saved_tokens": saved,
            "json_total": json_total,
            "toon_total": toon_total,
            "pairs": 9,
        })
    pair_detail = [{
        "agent_config": row["agent_config"],
        "replicate": row["replicate"],
        "task": TASK_LABELS[row["task_id"]],
        "json_correct": "yes" if row["json_correct"] else "no",
        "toon_correct": "yes" if row["toon_correct"] else "no",
        "input_saved": -row["input_token_delta"],
        "total_saved": -row["total_token_delta"],
    } for row in summary["pairs"]]
    gate_detail = [
        {"condition": "Execution integrity", "threshold": "90 unique, zero timeout/error/tool calls", "observed": "90/90 clean", "result": "PASS"},
        {"condition": "Accuracy non-inferior", "threshold": "No worse than -2 overall / -1 per config", "observed": "45/45 vs 45/45", "result": "PASS"},
        {"condition": "Response parse non-inferior", "threshold": "TOON parsed ≥ JSON", "observed": "45/45 vs 45/45", "result": "PASS"},
        {"condition": "Input tokens lower", "threshold": "TOON sum < JSON sum", "observed": f"{toon_row['input_tokens']:,} < {json_row['input_tokens']:,}", "result": "PASS"},
        {"condition": "Total tokens lower", "threshold": "TOON sum < JSON sum", "observed": f"{toon_row['total_tokens']:,} < {json_row['total_tokens']:,}", "result": "PASS"},
    ]
    return {
        "headline": [{
            "sessions": 90,
            "exact_successes": 90,
            "paired_token_wins": 45,
            "input_saved": input_saved,
            "input_savings_percent": input_percent,
            "total_saved": total_saved,
            "total_savings_percent": total_percent,
            "gate_conditions": 5,
        }],
        "representation_summary": representation_summary,
        "config_summary": config_rows,
        "task_summary": task_summary,
        "task_savings": task_savings,
        "pair_detail": pair_detail,
        "gate_detail": gate_detail,
    }


def build_artifact(raw: dict) -> dict:
    generated_at = raw["generated_at"]
    datasets = build_datasets(raw)
    source = {
        "id": SOURCE_ID,
        "label": "Frozen iteration 034 paired agent confirmation",
        "path": f"{STEM}.sql",
        "query": {
            "engine": "Codex CLI 0.146.0 + Python 3",
            "query": "python3 benchmarks/agent_data_runner.py --protocol benchmarks/agent_data_protocol_034.json --output benchmarks/results/agent_data_confirmation_034.json",
            "description": "All 90 fresh session transcripts, schema-constrained responses, token usage records, elapsed times, command events, exact hidden judgments, and paired JSON/TOON aggregates.",
            "executed_at": generated_at,
            "language": "Python",
            "metric_definitions": [
                "Exact success: the parsed top-level answer equals the frozen hidden answer, including required array ordering and exact strings.",
                "Input tokens: Codex turn.completed input_tokens summed across the 45 sessions in each representation arm.",
                "Total tokens: Codex input_tokens plus output_tokens; reasoning_output_tokens remain separately preserved in every raw session.",
                "Paired token win: TOON total_tokens are strictly below JSON total_tokens for the same task, agent configuration, and replicate.",
                "Accuracy non-inferiority: TOON loses no more than two exact successes overall and no more than one within any agent configuration.",
            ],
        },
    }
    cards = [
        card("sessions_card", "Fresh sessions", "sessions", "Every frozen matrix cell ran once.", "sessions"),
        card("exact_card", "Exact answers", "exact_successes", "Both arms match every hidden expected answer.", "of 90"),
        card("pairs_card", "Paired token wins", "paired_token_wins", "TOON uses fewer total tokens in every matched pair.", "of 45"),
        card("input_card", "Input tokens saved", "input_saved", "Summed Codex input reduction across 45 TOON sessions.", "tokens"),
        card("input_percent_card", "Input reduction", "input_savings_percent", "Full-session input savings, including fixed agent context.", "%"),
        card("total_card", "Total tokens saved", "total_saved", "Input plus output reduction across the complete paired study.", "tokens"),
        card("total_percent_card", "Total reduction", "total_savings_percent", "Complete session-token reduction versus compact JSON.", "%"),
        card("gate_card", "Frozen conditions", "gate_conditions", "Every preregistered integrity, quality, and token gate passes.", "of 5"),
    ]
    charts = [
        {
            "id": "config_chart",
            "title": "Total session tokens by agent configuration",
            "subtitle": "15 fresh sessions per representation/configuration; lower is better.",
            "type": "bar", "intent": "comparison", "dataset": "config_summary",
            "encodings": {
                "x": {"field": "agent_config", "type": "nominal", "label": "Agent configuration"},
                "y": {"field": "total_tokens", "type": "quantitative", "label": "Total tokens", "format": "compact"},
                "color": {"field": "representation", "type": "nominal", "label": "Representation"},
            },
            "xAxisTitle": "Agent configuration", "yAxisTitle": "Total tokens",
            "valueFormat": "compact", "layout": "full", "sourceId": SOURCE_ID,
            "question": "Is the token reduction consistent across frozen agent configurations?",
            "rationale": "Grouped bars preserve configuration and representation denominators while exposing whether one configuration drives the aggregate.",
            "comparisonContext": {"unit": "input plus output tokens", "grain": "configuration-representation aggregate", "denominator": "15 sessions per bar", "semanticFamily": "complete agent-session tokens"},
        },
        {
            "id": "task_chart",
            "title": "Total token savings by task family",
            "subtitle": "Nine paired sessions per task; positive percent means verified TOON used fewer full-session tokens.",
            "type": "bar", "intent": "comparison", "dataset": "task_savings",
            "encodings": {
                "x": {"field": "task", "type": "nominal", "label": "Task family"},
                "y": {"field": "saved_percent", "type": "quantitative", "label": "Total tokens saved", "format": "number"},
            },
            "xAxisTitle": "Task family", "yAxisTitle": "Savings (%)",
            "valueFormat": "number", "layout": "full", "sourceId": SOURCE_ID,
            "question": "Which task families convert compact context into the largest complete-session saving?",
            "rationale": "A single-series category comparison shows the treatment effect by task without implying an unsupported trend.",
            "comparisonContext": {"unit": "percent of compact-JSON total tokens", "grain": "task aggregate", "denominator": "nine JSON and nine TOON sessions per task", "semanticFamily": "paired total-token savings"},
        },
    ]
    tables = [
        table("gate_table", "Frozen five-part confirmation gate", "All conditions were defined and committed before the 90 measured task sessions.", "gate_detail", [
            ("condition", "Condition", "text"), ("threshold", "Frozen threshold", "text"),
            ("observed", "Observed", "text"), ("result", "Result", "text"),
        ], "condition"),
        table("representation_table", "Representation-level result", "45 fresh sessions per arm over identical JSON data models and answer schemas.", "representation_summary", [
            ("representation", "Representation", "text"), ("sessions", "Sessions", "number"),
            ("exact", "Exact", "number"), ("parsed", "Parsed", "number"),
            ("tool_free", "Tool-free", "number"), ("input_tokens", "Input tokens", "number"),
            ("output_tokens", "Output tokens", "number"), ("total_tokens", "Total tokens", "number"),
            ("median_total", "Median/session", "number"), ("median_seconds", "Median seconds", "number"),
        ], "representation"),
        table("config_table", "Agent-configuration audit", "Each row retains 15 fresh sessions; model and reasoning differences remain visible.", "config_summary", [
            ("agent_config", "Agent config", "text"), ("representation", "Representation", "text"),
            ("sessions", "Sessions", "number"), ("exact", "Exact", "number"),
            ("input_tokens", "Input tokens", "number"), ("output_tokens", "Output tokens", "number"),
            ("total_tokens", "Total tokens", "number"), ("median_total", "Median/session", "number"),
            ("median_seconds", "Median seconds", "number"),
        ], "agent_config"),
        table("task_table", "Task-level paired audit", "Each task has nine JSON and nine TOON sessions; all 18 answers per task are exact.", "task_summary", [
            ("task", "Task", "text"), ("family", "Family", "text"),
            ("json_correct", "JSON exact", "number"), ("toon_correct", "TOON exact", "number"),
            ("json_context_chars", "JSON chars", "number"), ("toon_context_chars", "TOON chars", "number"),
            ("json_total", "JSON total", "number"), ("toon_total", "TOON total", "number"),
            ("saved_tokens", "Saved", "number"), ("saved_percent", "Saved %", "number"),
        ], "task"),
        table("pair_table", "Complete 45-pair token audit", "Positive saved values mean TOON used fewer tokens for the identical task/configuration/replicate pair.", "pair_detail", [
            ("agent_config", "Agent config", "text"), ("replicate", "Rep", "number"),
            ("task", "Task", "text"), ("json_correct", "JSON correct", "text"),
            ("toon_correct", "TOON correct", "text"), ("input_saved", "Input saved", "number"),
            ("total_saved", "Total saved", "number"),
        ], "agent_config"),
    ]
    blocks = [
        {"id": "title", "type": "markdown", "layout": "full", "body": "# Verified TOON Context Is Cheaper Without Accuracy Loss — Iteration 034"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Technical summary\n\n**Verified TOON input passes the complete preregistered confirmation on record-heavy agent tasks.** Compact JSON and TOON both achieve **45/45 exact answers**, **45/45 valid schema-constrained JSON responses**, and zero tool calls. TOON reduces summed input tokens from **576,761 to 570,369** and complete input-plus-output tokens from **580,332 to 573,910**. All **45/45 matched pairs** use fewer total tokens, so the frozen gate passes **5/5**. This is evidence for Parley's adaptive input layer on these shapes and two model IDs—not proof that TOON should replace JSON or that Parley is already the best general-purpose language."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [item["id"] for item in cards]},
        {"id": "quality", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Meaning survives every representation change\n\nEvery lookup, filter, aggregation, rollback selection, and rename plan is exact in both arms across sol-low, sol-medium, and terra-medium. All 90 output files parse against the same per-task JSON schema; no session invokes a command, times out, returns nonzero, or reports an agent error. The accuracy margin is therefore unused: TOON ties JSON overall and within every configuration."},
        {"id": "gate_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "token_result", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The full agent session is 1.1066% cheaper, consistently\n\nTOON saves **6,392 input tokens (1.1083%)** and **6,422 total tokens (1.1066%)** across 45 sessions. Median total tokens fall from 12,817 to 12,738. The absolute percentage is smaller than the context-only reduction because roughly 12k fixed agent/system tokens surround each task, but the direction is unusually consistent: every matched pair saves between 49 and 265 total tokens."},
        {"id": "config_chart_block", "type": "chart", "layout": "full", "chartId": "config_chart"},
        {"id": "representation_table_block", "type": "table", "layout": "full", "tableId": "representation_table"},
        {"id": "config_table_block", "type": "table", "layout": "full", "tableId": "config_table"},
        {"id": "task_result", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Larger reasoning contexts create the largest complete-session gains\n\nRollback reasoning saves 2,290 total tokens (1.911%) and rename planning saves 1,711 (1.465%). Exact lookup saves 1.093%; filtering and aggregation save 0.549% and 0.466%. All task families remain 9/9 exact per arm. The difference follows useful context volume rather than a correctness tradeoff: TOON removes repeated record keys, while fixed session overhead remains unchanged."},
        {"id": "task_chart_block", "type": "chart", "layout": "full", "chartId": "task_chart"},
        {"id": "task_table_block", "type": "table", "layout": "full", "tableId": "task_table"},
        {"id": "pairs", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## All 45 matched pairs point in the same token direction\n\nPairing holds task, agent configuration, and replicate fixed. Input-token deltas range from 55 to 267 saved; complete-token deltas range from 49 to 265 saved. The complete audit below prevents the aggregate from hiding one configuration, task, or replicate that became more expensive."},
        {"id": "pair_table_block", "type": "table", "layout": "full", "tableId": "pair_table"},
        {"id": "scope", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Scope, population, and metric definitions\n\nThe population is five frozen record-heavy contexts where canonical TOON is exact and character-smaller: compiler diagnostics, test results used for two tasks, deployment history, and a symbol index. Each task appears under compact JSON and TOON for three configurations and three repetitions, giving 45 pairs and 90 fresh sessions. **Exact** means the hidden answer matches after JSON parsing. **Total tokens** means the Codex-reported input plus output tokens for the full session, not context tokens alone."},
        {"id": "method", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The protocol was committed before task output\n\nCommit `ca82a5b` freezes protocol SHA `a50cbe79…`, task SHA `9fa1588f…`, context hashes, seed `340260805`, 180-second timeout, concurrency six, prompts, hidden answers, output schemas, runner, exact scorer, token definitions, and five all-required gates. Cells were shuffled once, each used an ephemeral task with tools disabled, and all ran exactly once. Unrelated `ready` prompts checked model/schema availability before the freeze; no benchmark context or answer was exposed."},
        {"id": "limits", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Limits: two models, selected shapes, and no elapsed win\n\nThe matrix has three configurations but only two model IDs; sol-low is a reasoning-budget sensitivity, not an independent third model. Tasks are exact-answer and intentionally use the uniform records where Stage A said TOON helps, so this does not generalize to prose, deep heterogeneous JSON, agent-generated TOON, or arbitrary coding repositories. Median elapsed time is **9.9798 seconds for TOON versus 9.4193 for JSON** and varies by configuration; elapsed was not a frozen gate, concurrency adds noise, and this run supports no speed claim. Cached-input totals also differ by randomized execution, although every matched reported input-token delta remains negative."},
        {"id": "decision", "type": "markdown", "layout": "full", "body": "## Decision: ship adaptive input packing, keep JSON as the contract\n\n1. Keep `parley data` automatic: use TOON only after exact round trip and real-token savings; keep JSON fallback for every other shape.\n2. Keep model output, tool diagnostics, public APIs, and stored source-of-truth data as JSON.\n3. Do not expand the TOON profile from these sessions; future forms need independent product pressure and a new corpus.\n4. Replicate on at least one external model family and longer real coding contexts before using broad marketing language.\n5. Continue the source-language thesis separately on mature backend and frontend projects; never add this 1.1066% context result to Parley/Python/Rust source scores."},
        {"id": "questions", "type": "markdown", "layout": "full", "body": "## Further questions\n\n- Does the 45/45 paired token direction repeat with external model families and larger context windows?\n- At what context size does removing repeated keys materially change full-session cost after fixed agent overhead?\n- Does non-inferior accuracy persist on ambiguous real repository tasks rather than exact-answer fixtures?\n- Which backend and frontend product capability should Parley dogfood next without introducing benchmark-shaped syntax?"},
    ]
    manifest_source = {"id": source["id"], "label": source["label"], "path": source["path"]}
    return {
        "surface": "report",
        "manifest": {
            "version": 1, "surface": "report",
            "title": "Verified TOON Context Is Cheaper Without Accuracy Loss — Iteration 034",
            "description": "Preregistered 90-session paired compact-JSON versus verified-TOON agent confirmation.",
            "generatedAt": generated_at,
            "cards": cards, "charts": charts, "tables": tables,
            "sources": [manifest_source], "blocks": blocks,
        },
        "snapshot": {"version": 1, "generatedAt": generated_at, "status": "ready", "datasets": datasets},
        "sources": [source],
        "package_info": {"root": "benchmarks/results", "manifestPath": f"{STEM}.artifact.json", "snapshotPath": "agent_data_confirmation_034.json", "originUrl": "artifact://parley-agent-data-confirmation-034"},
    }


def build_sql() -> str:
    return """.mode list
.separator |
CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/agent_data_confirmation_034.json'));
CREATE TEMP VIEW representation_summary AS
SELECT json_extract(item.value, '$.representation') AS representation,
       json_extract(item.value, '$.sessions') AS sessions,
       json_extract(item.value, '$.exact_successes') AS exact_successes,
       json_extract(item.value, '$.parse_successes') AS parse_successes,
       json_extract(item.value, '$.input_tokens') AS input_tokens,
       json_extract(item.value, '$.output_tokens') AS output_tokens,
       json_extract(item.value, '$.total_tokens') AS total_tokens,
       json_extract(item.value, '$.median_total_tokens') AS median_total_tokens,
       json_extract(item.value, '$.median_elapsed_seconds') AS median_elapsed_seconds
FROM raw, json_each(json_extract(raw.document, '$.summary.by_representation')) AS item;
SELECT * FROM representation_summary ORDER BY representation;
SELECT 'gate', json_extract(document, '$.summary.gate.passed'), json_extract(document, '$.summary.gate.conditions_passed') FROM raw;
"""


def build_chart_map() -> str:
    return """# Iteration 034 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does exact-round-trip TOON preserve task accuracy while
  lowering complete agent-session tokens versus compact JSON?
- Decision-useful answer: yes on this frozen record-heavy corpus and two model
  IDs; 90/90 exact, 45/45 paired token wins, and the gate passes 5/5.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Configurations | Is the reduction consistent across agent configurations? | Comparison / grouped bar | agent_config, representation, total_tokens | All three configurations preserve exact accuracy and lower total TOON tokens | Hard two-root cap for the meaningful representation grouping |
| Tasks | Which task contexts create the largest full-session saving? | Comparison / bar | task, saved_percent | Every task saves; rollback and rename planning save most | Single-root preferred; task identity is already on the axis |

Both visuals use bars because both questions are discrete category comparisons;
one needs a representation grouping and the other is a single paired effect.
Exact gates, configurations, tasks, and all 45 pairs remain in audit tables.
"""


def main() -> None:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    validate(raw)
    artifact = build_artifact(raw)
    (REPORTS / f"{STEM}.artifact.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / f"{STEM}.sql").write_text(build_sql(), encoding="utf-8")
    (REPORTS / f"{STEM}.chart-map.md").write_text(build_chart_map(), encoding="utf-8")
    print(json.dumps({
        "artifact": str(REPORTS / f"{STEM}.artifact.json"),
        "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "datasets": {key: len(value) for key, value in artifact["snapshot"]["datasets"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()
