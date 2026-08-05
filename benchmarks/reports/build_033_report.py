#!/usr/bin/env python3
"""Build the canonical report artifact for agent-data diagnostic 033."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "results" / "agent_data_033.json"
STEM = "033-adaptive-agent-data-gate-not-met"
SOURCE_ID = "agent_data_033"
GENERATED_AT = "2026-08-05T03:12:31Z"
MANIFEST_SHA = "8dd47b32a3b5103cb22153d9a390ff8a4b7669e7fead3cea9a397ece2c19e08b"
RAW_SHA = "3d3068e1501782f9f5a2242f1bdb061d4dace25dc59d26a847d2fabb71f26b78"


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
          columns: list[tuple[str, str, str]], sort_field: str) -> dict:
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
        "defaultSort": {"field": sort_field, "direction": "asc"},
        "density": "dense" if dataset == "case_detail" else "spacious",
        "layout": "full",
        "sourceId": SOURCE_ID,
    }


def validate(raw: dict) -> None:
    assert raw["experiment_id"] == "agent-data-033"
    assert raw["corpus_manifest_sha256"] == MANIFEST_SHA
    assert hashlib.sha256(RAW.read_bytes()).hexdigest() == RAW_SHA
    assert len(raw["tokenizers"]) == 3
    by_name = {row["tokenizer"]: row for row in raw["tokenizers"]}
    assert set(by_name) == {
        "rough-regex-v1", "tiktoken:cl100k_base", "tiktoken:o200k_base"
    }
    for row in by_name.values():
        summary = row["summary"]
        assert summary["cases"] == 12
        assert summary["all_supported_round_trip"] is True
        assert summary["auto_never_increases_tokens"] is True
    assert by_name["tiktoken:cl100k_base"]["summary"]["toon_selected"] == 3
    assert by_name["tiktoken:o200k_base"]["summary"]["toon_selected"] == 3
    assert by_name["tiktoken:cl100k_base"]["summary"]["savings_percent_vs_compact_json"] == 4.5682
    assert by_name["tiktoken:o200k_base"]["summary"]["savings_percent_vs_compact_json"] == 4.5673


def build_datasets(raw: dict) -> dict[str, list[dict]]:
    by_name = {row["tokenizer"]: row for row in raw["tokenizers"]}
    short = {
        "rough-regex-v1": "Rough diagnostic",
        "tiktoken:cl100k_base": "cl100k_base",
        "tiktoken:o200k_base": "o200k_base",
    }
    summaries = []
    aggregate = []
    for name in ("rough-regex-v1", "tiktoken:cl100k_base", "tiktoken:o200k_base"):
        summary = by_name[name]["summary"]
        label = short[name]
        summaries.append({
            "tokenizer": label,
            "scope": "exploratory" if name == "rough-regex-v1" else "primary",
            "json_tokens": summary["compact_json_tokens"],
            "adaptive_tokens": summary["adaptive_tokens"],
            "saved_tokens": summary["savings_tokens"],
            "savings_percent": summary["savings_percent_vs_compact_json"],
            "toon_supported": summary["toon_supported"],
            "toon_selected": summary["toon_selected"],
            "fallbacks": summary["json_fallback_unsupported"] + summary["json_fallback_not_smaller"],
        })
        aggregate.extend([
            {
                "tokenizer": label,
                "representation": "Compact JSON",
                "tokens": summary["compact_json_tokens"],
                "saved_tokens": 0,
                "savings_percent": 0,
                "toon_selected": summary["toon_selected"],
            },
            {
                "tokenizer": label,
                "representation": "Adaptive",
                "tokens": summary["adaptive_tokens"],
                "saved_tokens": summary["savings_tokens"],
                "savings_percent": summary["savings_percent_vs_compact_json"],
                "toon_selected": summary["toon_selected"],
            },
        ])
    primary = by_name["tiktoken:o200k_base"]
    case_detail = []
    for row in primary["cases"]:
        case_detail.append({
            "case": row["id"],
            "family": row["family"],
            "origin": row["origin"],
            "json_tokens": row["json_tokens"],
            "toon_tokens": "—" if row["toon_tokens"] is None else row["toon_tokens"],
            "selected": row["selected_format"].upper(),
            "saved_tokens": row["savings_tokens"],
            "reason": row["selection_reason"].replace("_", " "),
        })
    gate_detail = [
        {"condition": "12/12 strict JSON inputs", "threshold": "All 12", "observed": "12/12", "result": "PASS"},
        {"condition": "Exact TOON round trip", "threshold": "Every supported case", "observed": "7/7", "result": "PASS"},
        {"condition": "Automatic mode never increases tokens", "threshold": "Every case and tokenizer", "observed": "36/36", "result": "PASS"},
        {"condition": "Adaptive coverage", "threshold": "≥3 TOON and ≥3 JSON", "observed": "3 TOON / 9 JSON", "result": "PASS"},
        {"condition": "Primary aggregate savings", "threshold": "≥5% on both", "observed": "4.5682% / 4.5673%", "result": "FAIL"},
    ]
    return {
        "headline": [{
            "cases": 12,
            "verified_candidates": 7,
            "primary_toon_selected": 3,
            "cl100k_savings": 4.5682,
            "o200k_savings": 4.5673,
            "gate_conditions": 4,
        }],
        "tokenizer_summary": summaries,
        "aggregate_tokens": aggregate,
        "case_detail": case_detail,
        "gate_detail": gate_detail,
    }


def build_artifact(raw: dict) -> dict:
    datasets = build_datasets(raw)
    source = {
        "id": SOURCE_ID,
        "label": "Frozen iteration 033 agent-data measurement",
        "path": f"{STEM}.sql",
        "query": {
            "engine": "Python 3 + tiktoken 0.13.0",
            "query": "python3 benchmarks/measure_agent_data.py --tokenizer rough --tokenizer cl100k_base --tokenizer o200k_base --output benchmarks/results/agent_data_033.json",
            "description": "Deterministic measurement of all 12 frozen JSON cases through compact JSON and Parley's exact-round-trip adaptive TOON selector.",
            "executed_at": GENERATED_AT,
            "language": "Python",
            "metric_definitions": [
                "Candidate tokens: tokens in compact JSON or the canonical safe-subset TOON representation under the named tokenizer.",
                "Adaptive tokens: TOON tokens only when TOON is supported, exactly round-trips, and is strictly smaller; compact JSON tokens otherwise.",
                "Savings percent: (compact JSON tokens minus adaptive tokens) divided by compact JSON tokens across all 12 cases.",
                "Supported candidate: a JSON value within parley-safe-subset-v1 whose encoded TOON decodes to the exact ordered JSON data model.",
            ],
        },
    }
    cards = [
        card("cases_card", "Frozen corpus", "cases", "Every predeclared JSON case is retained.", "cases"),
        card("verified_card", "Verified candidates", "verified_candidates", "TOON-supported cases passing exact round trip.", "of 7"),
        card("selected_card", "TOON selected", "primary_toon_selected", "Cases strictly smaller under each primary tokenizer.", "of 12"),
        card("cl_card", "cl100k savings", "cl100k_savings", "Aggregate adaptive savings versus compact JSON.", "%"),
        card("o_card", "o200k savings", "o200k_savings", "Aggregate adaptive savings versus compact JSON.", "%"),
        card("gate_card", "Frozen conditions", "gate_conditions", "All integrity and coverage checks pass; savings misses.", "of 5"),
    ]
    charts = [{
        "id": "aggregate_chart",
        "title": "Aggregate tokens by tokenizer and representation",
        "subtitle": "All 12 frozen cases; lower is better. Rough is exploratory; cl100k_base and o200k_base are primary.",
        "type": "bar",
        "intent": "comparison",
        "dataset": "aggregate_tokens",
        "encodings": {
            "x": {"field": "tokenizer", "type": "nominal", "label": "Tokenizer"},
            "y": {"field": "tokens", "type": "quantitative", "label": "Aggregate tokens", "format": "compact"},
            "color": {"field": "representation", "type": "nominal", "label": "Representation"},
        },
        "xAxisTitle": "Tokenizer",
        "yAxisTitle": "Aggregate tokens",
        "valueFormat": "compact",
        "question": "Does adaptive selection reduce total input representation tokens?",
        "rationale": "Grouped bars compare identical data and tokenizer denominators while keeping compact JSON as the explicit baseline.",
        "comparisonContext": {
            "unit": "tokens",
            "grain": "representation-tokenizer aggregate",
            "denominator": "all 12 frozen cases",
            "semanticFamily": "structured context tokens",
        },
        "layout": "full",
        "sourceId": SOURCE_ID,
    }]
    tables = [
        table("summary_table", "Tokenizer-level result", "All 12 cases; savings are relative to compact JSON under the same tokenizer.", "tokenizer_summary", [
            ("tokenizer", "Tokenizer", "text"), ("scope", "Role", "text"),
            ("json_tokens", "JSON tokens", "number"), ("adaptive_tokens", "Adaptive tokens", "number"),
            ("saved_tokens", "Saved", "number"), ("savings_percent", "Savings %", "number"),
            ("toon_supported", "TOON supported", "number"), ("toon_selected", "TOON selected", "number"),
            ("fallbacks", "JSON fallbacks", "number"),
        ], "tokenizer"),
        table("gate_table", "Frozen Stage A gate", "Four integrity/coverage conditions pass; the 5% primary-tokenizer threshold does not.", "gate_detail", [
            ("condition", "Condition", "text"), ("threshold", "Threshold", "text"),
            ("observed", "Observed", "text"), ("result", "Result", "text"),
        ], "condition"),
        table("case_table", "o200k_base case audit", "Every frozen case is shown; a zero saving means automatic compact-JSON fallback.", "case_detail", [
            ("case", "Case", "text"), ("family", "Shape", "text"), ("origin", "Origin", "text"),
            ("json_tokens", "JSON", "number"), ("toon_tokens", "TOON", "text"),
            ("selected", "Selected", "text"), ("saved_tokens", "Saved", "number"),
            ("reason", "Reason", "text"),
        ], "case"),
    ]
    blocks = [
        {"id": "title", "type": "markdown", "layout": "full", "body": "# Adaptive Agent Data Saves Tokens, but Misses the Frozen Gate — Iteration 033"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Technical summary\n\n**Parley's adaptive JSON/TOON layer is lossless and useful on the shapes TOON fits, but Stage A fails its preregistered aggregate gate.** All 12 JSON inputs parse, all 7 supported TOON candidates round-trip exactly, and automatic selection never adds tokens. Under each primary tokenizer, only 3/12 cases select TOON; aggregate savings are **4.5682%** with cl100k_base and **4.5673%** with o200k_base, below the frozen **5%** threshold. The decision is **4/5 conditions passed: preserve the result, keep JSON fallback, and do not tune the profile on this corpus.**"},
        {"id": "metric_strip", "type": "metric-strip", "layout": "full", "cardIds": [item["id"] for item in cards]},
        {"id": "aggregate_read", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Real tokenizers turn a large rough-count win into a narrow near miss\n\nThe rough diagnostic reports 13.6942% savings, but the two primary tokenizer views agree at about 4.57%. This is exactly why character counts and punctuation-heavy rough counters cannot support a model-cost claim. The paired bars keep the tokenizer denominator fixed: adaptive output is compared only with compact JSON encoded by the same tokenizer."},
        {"id": "aggregate_block", "type": "chart", "layout": "full", "chartId": "aggregate_chart"},
        {"id": "summary_table_block", "type": "table", "layout": "full", "tableId": "summary_table"},
        {"id": "shape_read", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Three record-heavy documents create the entire primary saving\n\nCompiler diagnostics save 34.43%, test results save 32.20%, and the 32-report progress manifest saves 15.07% under o200k_base. Four other values are safely encodable but remain JSON because TOON is not smaller; five heterogeneous shapes are outside the conservative profile. Even the package-registry pilot that looked strong under the rough counter falls back under both primary tokenizers. The implication is shape-aware selection, not universal TOON adoption."},
        {"id": "case_table_block", "type": "table", "layout": "full", "tableId": "case_table"},
        {"id": "scope", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Scope and definitions\n\nThe frozen corpus contains 12 documents spanning uniform records, nested objects, primitive arrays, non-uniform records, mixed nested arrays, packages, workflows, benchmark protocols, patch catalogs, and portable report data. Seven are repository artifacts and five are synthetic instances of real Parley contracts. **Supported** means the value fits `parley-safe-subset-v1` and decodes to the exact ordered JSON model. **Selected** adds one condition: TOON must use strictly fewer tokens than compact JSON under the current tokenizer."},
        {"id": "method", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Methodology keeps selection and meaning deterministic\n\nThe corpus and 5% threshold were committed at `87e6487` before the broad result was produced. One previously observed rough-token registry pilot was disclosed in the protocol. The measurement built compact JSON and canonical TOON candidates, decoded every TOON candidate, checked full JSON-model equality, counted with the deterministic rough tokenizer plus tiktoken 0.13.0 `cl100k_base` and `o200k_base`, and retained every fallback. The first sandboxed attempt could not download tokenizer tables and produced no result file; the same frozen command then completed with network access. No case was excluded or rerun selectively."},
        {"id": "gate_read", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The preregistered decision is a failed 4/5, not a rounded pass\n\nThe primary savings miss is 0.4318 percentage points for cl100k_base and 0.4327 points for o200k_base. Both real-tokenizer results clear the adaptive-coverage condition exactly—3 TOON selections and 9 JSON fallbacks—but neither clears 5%. Rounding to one decimal would hide the miss, so the gate uses the frozen full-precision values."},
        {"id": "gate_table_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "limits", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Limitations: compression is not comprehension\n\nThe corpus is one repository, five cases are synthetic, and tokenizer counts are representation measurements rather than complete agent-session costs. Automatic mode is guaranteed not to increase measured representation tokens by construction; that safety property is valuable but not an independent performance discovery. This stage does not test whether a model answers correctly from TOON, whether unfamiliar notation creates repair turns, or whether Parley source code beats Python or Rust."},
        {"id": "next", "type": "markdown", "layout": "full", "body": "## Recommended next step: run the 90 sessions without profile tuning\n\n1. Preserve this failed Stage A gate and leave the safe subset unchanged.\n2. Freeze five comprehension/coding tasks, exact model IDs, paired JSON/adaptive inputs, hidden scorers, and session-token accounting.\n3. Run the planned 90 fresh sessions with JSON output in both arms.\n4. Claim an agent benefit only if accuracy is non-inferior and total session tokens—including format repairs—are lower.\n5. Continue language work on external project usefulness; do not combine context-format savings with source-language benchmark scores."},
        {"id": "questions", "type": "markdown", "layout": "full", "body": "## Further questions\n\n- Do the three observed shape wins survive across multiple model families and real task prompts?\n- Does TOON input change exact-answer or code-modification accuracy even when output remains JSON?\n- Can future product data broaden the safe subset without adding ambiguity or a runtime dependency?\n- Where does Parley's complete session-token cost land on mature external backend and frontend repositories?"},
    ]
    manifest_source = {"id": source["id"], "label": source["label"], "path": source["path"]}
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "Adaptive Agent Data Saves Tokens, but Misses the Frozen Gate — Iteration 033",
            "description": "Preregistered representation diagnostic over 12 shape-diverse JSON documents and three tokenizers.",
            "generatedAt": GENERATED_AT,
            "cards": cards,
            "charts": charts,
            "tables": tables,
            "sources": [manifest_source],
            "blocks": blocks,
        },
        "snapshot": {
            "version": 1,
            "generatedAt": GENERATED_AT,
            "status": "ready",
            "datasets": datasets,
        },
        "sources": [source],
        "package_info": {
            "root": "benchmarks/results",
            "manifestPath": f"{STEM}.artifact.json",
            "snapshotPath": "agent_data_033.json",
            "originUrl": "artifact://parley-agent-data-033",
        },
    }


def build_sql() -> str:
    return """.mode list
.separator |
CREATE TEMP TABLE raw(document TEXT NOT NULL);
INSERT INTO raw VALUES (readfile('benchmarks/results/agent_data_033.json'));
CREATE TEMP VIEW tokenizer_summary AS
SELECT json_extract(item.value, '$.tokenizer') AS tokenizer,
       json_extract(item.value, '$.summary.compact_json_tokens') AS json_tokens,
       json_extract(item.value, '$.summary.adaptive_tokens') AS adaptive_tokens,
       json_extract(item.value, '$.summary.savings_tokens') AS saved_tokens,
       json_extract(item.value, '$.summary.savings_percent_vs_compact_json') AS savings_percent,
       json_extract(item.value, '$.summary.toon_supported') AS toon_supported,
       json_extract(item.value, '$.summary.toon_selected') AS toon_selected
FROM raw, json_each(json_extract(raw.document, '$.tokenizers')) AS item;
SELECT * FROM tokenizer_summary ORDER BY tokenizer;
"""


def build_chart_map() -> str:
    return """# Iteration 033 report notes

- Audience: technical
- Delivery: one canonical artifact compiled to self-contained HTML
- Primary question: does verified adaptive TOON save at least 5% under both
  frozen primary tokenizers without changing the JSON model?
- Decision-useful answer: integrity and adaptive coverage pass, but primary
  savings are about 4.57%; the frozen Stage A gate finishes 4/5 and fails.

## Chart map

| Section | Question | Family / type | Fields | Supported claim | Palette policy |
| --- | --- | --- | --- | --- | --- |
| Aggregate tokens | Does adaptive selection reduce identical corpus tokens? | Comparison / grouped bar | tokenizer, representation, tokens | Savings are large under rough counting but narrowly below 5% under both primary tokenizers | Hard two-root cap; representation is the meaningful grouping |

Exact gate values and all 12 case decisions remain in audit tables. One grouped
chart is sufficient because every quantitative section compares the same two
representations; additional charts would repeat the relationship rather than
answer a new question.
"""


def main() -> None:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    validate(raw)
    artifact = build_artifact(raw)
    (REPORTS / f"{STEM}.artifact.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (REPORTS / f"{STEM}.sql").write_text(build_sql(), encoding="utf-8")
    (REPORTS / f"{STEM}.chart-map.md").write_text(build_chart_map(), encoding="utf-8")
    print(json.dumps({
        "artifact": str(REPORTS / f"{STEM}.artifact.json"),
        "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "datasets": {key: len(value) for key, value in artifact["snapshot"]["datasets"].items()},
    }, indent=2))


if __name__ == "__main__":
    main()
