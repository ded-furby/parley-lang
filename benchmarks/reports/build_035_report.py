#!/usr/bin/env python3
"""Build the canonical technical report artifact for full-stack comparison 035."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPORTS = Path(__file__).resolve().parent
BENCHMARKS = REPORTS.parent
RAW = BENCHMARKS / "results" / "fullstack_035_v0.4.0.json"
PROTOCOL = BENCHMARKS / "fullstack_035_protocol.json"
STEM = "035-release-radar-fullstack-compactness-proof"
SOURCE_ID = "fullstack_evidence_035"
GENERATED_AT = "2026-08-05T06:16:46.495593Z"
RAW_SHA = "e12345fbf7dcc103d93a6895080579253cd4b75cfc417a49204ff15429356925"
PROTOCOL_SHA = "5e6c25908b323498b89f5ff5a2b489256a7332b1fc79fd9cb3ddd5d1abd0cfb6"
CASES_SHA = "ed1b8ffb9d568e366b3c99104df9f492f79da9eefcaae272f910c2b20628bdbe"
LANGUAGE_LABELS = {
    "parley": "Parley",
    "python": "Python",
    "typescript": "TypeScript",
    "rust": "Rust",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(raw: dict, protocol: dict) -> None:
    assert sha(RAW) == RAW_SHA
    assert sha(PROTOCOL) == PROTOCOL_SHA
    assert raw["experiment_id"] == "035"
    assert raw["protocol_sha256"] == PROTOCOL_SHA
    assert raw["cases_sha256"] == CASES_SHA
    assert raw["protocol_commit"] == "01bc7c3"
    assert raw["frozen_product_commit"] == "e5470b6"
    assert raw["measurement_commit"] == "fa15f1e64dd5647823af7c674d736c9fe5b111aa"
    assert raw["dirty_paths_before_run"] == []
    assert protocol["protocol_revision"] == 2
    assert protocol["frozen_product"]["cases_sha256"] == CASES_SHA
    assert all(value["all_pass"] and value["passed"] == value["total"] == 15
               for value in raw["correctness"].values())
    assert all(len(raw["build"][language]["values"]) == 5 for language in LANGUAGE_LABELS)
    assert all(len(raw["startup"][language]["values"]) == 5 for language in LANGUAGE_LABELS)
    assert all(len(raw["load"][language]["rounds"]) == 5 for language in LANGUAGE_LABELS)
    assert raw["gates"] == {
        "all_languages_correct": True,
        "parley_primary_compactness": True,
        "parley_cross_target_reuse": True,
        "overall_fullstack_compactness_proof": True,
    }
    assert raw["source"]["parley"]["totals"]["o200k_base"] == 684


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
          direction: str = "asc", density: str = "spacious") -> dict:
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
        "density": density,
        "layout": "full",
        "sourceId": SOURCE_ID,
    }


def datasets(raw: dict) -> dict[str, list[dict]]:
    parley_tokens = raw["source"]["parley"]["totals"]["o200k_base"]
    comparison = []
    performance = []
    correctness = []
    source_files = []
    for language, label in LANGUAGE_LABELS.items():
        source = raw["source"][language]
        tokens = source["totals"]["o200k_base"]
        savings = 0.0 if language == "parley" else round(100.0 * (1.0 - parley_tokens / tokens), 4)
        correctness_row = raw["correctness"][language]
        reuse = raw["cross_target_reuse"][language]
        comparison.append({
            "language": label,
            "authored_tokens": tokens,
            "cl100k_tokens": source["totals"]["cl100k_base"],
            "bytes": source["totals"]["bytes"],
            "lines": source["totals"]["lines"],
            "parley_savings_percent": savings,
            "correctness": f"{correctness_row['passed']}/{correctness_row['total']}",
            "browser_target": reuse["browser_target"],
            "single_rule": "yes" if reuse["single_authored_rule"] else "no",
        })
        build = raw["build"][language]
        startup = raw["startup"][language]
        load_rows = raw["load"][language]["rounds"]
        artifacts = raw["artifacts"][language]
        performance.append({
            "language": label,
            "build_median_seconds": build["median"],
            "build_min_seconds": build["min"],
            "build_max_seconds": build["max"],
            "startup_median_ms": round(startup["median"] * 1000.0, 3),
            "startup_min_ms": round(startup["min"] * 1000.0, 3),
            "startup_max_ms": round(startup["max"] * 1000.0, 3),
            "requests_per_second": raw["load"][language]["median_requests_per_second"],
            "load_min_rps": min(row["requests_per_second"] for row in load_rows),
            "load_max_rps": max(row["requests_per_second"] for row in load_rows),
            "owned_output_bytes": artifacts["owned_output_bytes"],
            "deploy_closure_bytes": artifacts["deploy_closure_bytes"],
        })
        correctness.append({
            "language": label,
            "http_cases": 14,
            "browser_cases": 1,
            "passed": correctness_row["passed"],
            "total": correctness_row["total"],
            "console_errors": len(correctness_row["browser"]["console_errors"]),
            "result": "PASS" if correctness_row["all_pass"] else "FAIL",
        })
        for row in source["files"]:
            source_files.append({
                "language": label,
                "file": row["path"],
                "o200k_tokens": row["o200k_base"],
                "cl100k_tokens": row["cl100k_base"],
                "bytes": row["bytes"],
                "lines": row["lines"],
                "sha256": row["sha256"],
            })
    gates = [
        {
            "condition": "Complete behavior",
            "threshold": "All four languages pass all 15 frozen cases",
            "observed": "60/60 checks; 4/4 real browser flows",
            "result": "PASS",
        },
        {
            "condition": "Primary compactness",
            "threshold": "Parley o200k tokens ≤ the smallest correct baseline",
            "observed": "684 vs Python 1,147",
            "result": "PASS",
        },
        {
            "condition": "Cross-target reuse",
            "threshold": "One Parley readiness_score source for native + browser",
            "observed": "One checked definition compiled to native + WASM",
            "result": "PASS",
        },
    ]
    return {
        "headline": [{
            "behavior_checks": 60,
            "parley_tokens": 684,
            "closest_baseline_savings": 40.3662,
            "parley_requests_per_second": 9312.259,
            "gate_conditions": 3,
        }],
        "comparison": comparison,
        "performance": performance,
        "correctness": correctness,
        "source_files": source_files,
        "gates": gates,
    }


def build(raw: dict) -> dict:
    data = datasets(raw)
    source = {
        "id": SOURCE_ID,
        "label": "Frozen iteration 035 protocol and complete four-language result",
        "path": "fullstack_035_v0.4.0.json",
        "query": {
            "engine": "Python 3.14, tiktoken 0.13.0, Playwright 1.58.0, SQLite audit",
            "query": "python3 benchmarks/run_fullstack_035.py --output benchmarks/results/fullstack_035_v0.4.0.json && python3 benchmarks/reports/build_035_report.py",
            "sql": "WITH raw AS (SELECT json(readfile('benchmarks/results/fullstack_035_v0.4.0.json')) AS body) SELECT language, json_extract(body, '$.source.' || language || '.totals.o200k_base') AS authored_tokens FROM raw, (SELECT 'parley' language UNION ALL SELECT 'python' UNION ALL SELECT 'typescript' UNION ALL SELECT 'rust');",
            "description": "The revision-2 frozen protocol, exact 14-HTTP-plus-browser case matrix, per-file tokenizer counts and hashes, five clean-build rounds, five startup rounds, five 500-request load rounds, artifact sizes, and complete browser/server judgments.",
            "executed_at": GENERATED_AT,
            "language": "Python and SQLite",
            "filters": [
                "Frozen Parley product commit e5470b6 and amended protocol commit 01bc7c3.",
                "Four correct implementations committed at fa15f1e before measurement.",
                "Shared index.html, style.css, and app.js excluded from authored source and artifact closure.",
                "Dependency downloads excluded; five clean output builds with warm dependency caches.",
                "Load: 25 warmups then 500 sequential POST requests per language per round, five rounds, concurrency one.",
            ],
            "metric_definitions": [
                "Complete behavior: 14 frozen HTTP cases plus one real headless-Chrome form flow per language.",
                "Authored tokens: tiktoken 0.13.0 o200k_base count for each preregistered UTF-8 application source/configuration file, summed per language.",
                "Parley savings: 100 × (1 - Parley authored tokens / comparison-language authored tokens).",
                "Clean build: wall time after deleting only the language's explicit build output; dependency caches remain warm.",
                "Startup: monotonic time from process spawn until the first exact status-endpoint response.",
                "Sequential request rate: 500 correct ready-case POST responses divided by elapsed seconds, after 25 warmups, concurrency one.",
                "Deploy closure: language-owned runnable output plus production dependencies, excluding the byte-identical shared UI.",
            ],
            "tables_used": [
                "benchmarks/results/fullstack_035_v0.4.0.json",
                "benchmarks/fullstack_035_protocol.json",
                "benchmarks/fullstack_035_cases.json",
            ],
        },
    }
    cards = [
        card("behavior_card", "Behavior checks", "behavior_checks", "All four language arms pass every HTTP and browser case.", "of 60"),
        card("token_card", "Parley source", "parley_tokens", "Primary o200k authored-source measure.", "tokens"),
        card("saving_card", "Closest-baseline reduction", "closest_baseline_savings", "Parley versus Python, the smallest correct baseline.", "%"),
        card("load_card", "Parley local rate", "parley_requests_per_second", "Median of five sequential localhost rounds.", "req/s"),
        card("gate_card", "Frozen conditions", "gate_conditions", "Correctness, compactness, and native/browser reuse.", "of 3"),
    ]
    charts = [
        {
            "id": "token_chart",
            "title": "Application-authored tokens by language",
            "subtitle": "o200k_base tokens over preregistered source and configuration files; lower is better.",
            "type": "bar",
            "intent": "comparison",
            "dataset": "comparison",
            "encodings": {
                "x": {"field": "language", "type": "nominal", "label": "Language"},
                "y": {"field": "authored_tokens", "type": "quantitative", "label": "Authored tokens", "format": "number"},
                "tooltip": [
                    {"field": "cl100k_tokens", "type": "quantitative", "label": "cl100k tokens"},
                    {"field": "bytes", "type": "quantitative", "label": "UTF-8 bytes"},
                    {"field": "lines", "type": "quantitative", "label": "Physical lines"},
                    {"field": "correctness", "type": "text", "label": "Correctness"},
                ],
            },
            "xAxisTitle": "Language",
            "yAxisTitle": "o200k_base tokens",
            "valueFormat": "number",
            "layout": "full",
            "sourceId": SOURCE_ID,
            "question": "Which fully correct implementation has the smallest author-owned application surface?",
            "rationale": "A sorted single-measure bar chart exposes the compactness ranking without adding an artificial series or trend.",
            "comparisonContext": {
                "unit": "o200k_base tokens",
                "grain": "language implementation",
                "denominator": "all preregistered authored app/config files; shared UI and generated/dependency code excluded",
                "semanticFamily": "application-source compactness",
            },
            "palette": {"kind": "sequential", "name": "blue"},
            "labels": {"values": "all"},
            "settings": {"sort": "ascending", "showValues": True},
        },
        {
            "id": "load_chart",
            "title": "Sequential local request rate by language",
            "subtitle": "Median of five rounds; 500 correct POSTs after 25 warmups, concurrency one; higher is better.",
            "type": "bar",
            "intent": "comparison",
            "dataset": "performance",
            "encodings": {
                "x": {"field": "language", "type": "nominal", "label": "Language"},
                "y": {"field": "requests_per_second", "type": "quantitative", "label": "Requests per second", "format": "compact"},
                "tooltip": [
                    {"field": "load_min_rps", "type": "quantitative", "label": "Minimum round"},
                    {"field": "load_max_rps", "type": "quantitative", "label": "Maximum round"},
                    {"field": "startup_median_ms", "type": "quantitative", "label": "Median startup ms"},
                ],
            },
            "xAxisTitle": "Language",
            "yAxisTitle": "Requests per second",
            "valueFormat": "compact",
            "layout": "full",
            "sourceId": SOURCE_ID,
            "question": "Does the compact generated Parley server remain locally competitive on the frozen route?",
            "rationale": "A single-measure category comparison makes the descriptive throughput ordering explicit while preserving exact ranges in the adjacent table.",
            "comparisonContext": {
                "unit": "correct responses per second",
                "grain": "language median",
                "denominator": "five 500-request sequential rounds per language",
                "semanticFamily": "localhost HTTP microbenchmark",
            },
            "palette": {"kind": "sequential", "name": "blue"},
            "labels": {"values": "all"},
            "settings": {"sort": "descending", "showValues": True},
        },
    ]
    tables = [
        table("gate_table", "Frozen compactness proof gate", "All three conditions must pass; runtime cannot rescue a failed behavior or source result.", "gates", [
            ("condition", "Condition", "text"),
            ("threshold", "Frozen threshold", "text"),
            ("observed", "Observed", "text"),
            ("result", "Result", "text"),
        ], "condition"),
        table("comparison_table", "Source and browser-target comparison", "All four implementations pass 15/15; the percentage is Parley's reduction versus that row.", "comparison", [
            ("language", "Language", "text"),
            ("correctness", "Correct", "text"),
            ("authored_tokens", "o200k", "number"),
            ("cl100k_tokens", "cl100k", "number"),
            ("bytes", "Bytes", "number"),
            ("lines", "Lines", "number"),
            ("parley_savings_percent", "Parley saves %", "number"),
            ("browser_target", "Browser target", "text"),
            ("single_rule", "One rule", "text"),
        ], "authored_tokens"),
        table("performance_table", "Complete descriptive runtime/build summary", "Five clean builds, five startups, and five 500-request rounds per language on one Apple Silicon machine.", "performance", [
            ("language", "Language", "text"),
            ("build_median_seconds", "Build median s", "number"),
            ("build_min_seconds", "Build min s", "number"),
            ("build_max_seconds", "Build max s", "number"),
            ("startup_median_ms", "Startup ms", "number"),
            ("requests_per_second", "Median req/s", "number"),
            ("load_min_rps", "Min req/s", "number"),
            ("load_max_rps", "Max req/s", "number"),
            ("owned_output_bytes", "Owned output B", "number"),
            ("deploy_closure_bytes", "Deploy closure B", "number"),
        ], "requests_per_second", "desc", "dense"),
        table("correctness_table", "Four-language behavior audit", "Fourteen HTTP cases plus one real browser flow per implementation.", "correctness", [
            ("language", "Language", "text"),
            ("http_cases", "HTTP", "number"),
            ("browser_cases", "Browser", "number"),
            ("passed", "Passed", "number"),
            ("total", "Total", "number"),
            ("console_errors", "Console errors", "number"),
            ("result", "Result", "text"),
        ], "language"),
        table("file_table", "Per-file tokenizer and hash audit", "Every counted file is listed; lockfiles, generated output, shared UI, dependencies, and harness files are excluded.", "source_files", [
            ("language", "Language", "text"),
            ("file", "Counted file", "text"),
            ("o200k_tokens", "o200k", "number"),
            ("cl100k_tokens", "cl100k", "number"),
            ("bytes", "Bytes", "number"),
            ("lines", "Lines", "number"),
            ("sha256", "SHA-256", "text"),
        ], "language", density="dense"),
    ]
    blocks = [
        {"id": "title", "type": "markdown", "layout": "full", "body": "# Release Radar Full-Stack Compactness Proof — Iteration 035"},
        {"id": "summary", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Technical summary\n\n**Parley passes the frozen Release Radar full-stack compactness proof.** Parley, Python, TypeScript, and Rust each pass **15/15** exact HTTP/browser cases. Parley uses **684 o200k application-authored tokens**, **40.3662% fewer than Python's 1,147**, the smallest correct baseline; TypeScript uses 1,366 and Rust 1,949. The cl100k sensitivity keeps the same order. One checked Parley `readiness_score` definition powers both the native API and browser WASM. The complete gate therefore passes **3/3**. This proves a compactness win for one bounded full-stack product—not that Parley is generally best, and not yet that fresh agents spend fewer session tokens."},
        {"id": "metrics", "type": "metric-strip", "layout": "full", "cardIds": [item["id"] for item in cards]},
        {"id": "behavior", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## All four stacks reproduce the complete behavior\n\nEach server returns the same five successful assessment/status cases, rejects malformed, unknown, missing, mistyped, and wrong-media JSON as frozen, serves the shared UI safely, and rejects encoded traversal. Real Chrome then loads each browser scorer, computes 100 locally, receives 100 from the backend, renders the Ready verdict, and shows three passing gates with zero console errors. Correctness does not trade off against compactness."},
        {"id": "gate_block", "type": "table", "layout": "full", "tableId": "gate_table"},
        {"id": "correctness_block", "type": "table", "layout": "full", "tableId": "correctness_table"},
        {"id": "compactness", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Parley is 40.37% smaller than the nearest correct baseline\n\nThe primary o200k count is **684 Parley tokens versus 1,147 Python, 1,366 TypeScript, and 1,949 Rust**. Parley is therefore 40.3662% below Python, 49.9268% below TypeScript, and 64.9051% below Rust. The independent cl100k count is 680, 1,140, 1,360, and 1,919 respectively, so tokenizer choice does not reverse the ranking. This is an amortized application-surface result: language/runtime/framework implementation source is excluded for every arm."},
        {"id": "token_chart_block", "type": "chart", "layout": "full", "chartId": "token_chart"},
        {"id": "comparison_block", "type": "table", "layout": "full", "tableId": "comparison_table"},
        {"id": "files", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The counting boundary is fully inspectable\n\nParley counts `main.par` and `parley.web.json`. Python counts its API, handwritten browser supplement, and dependency declaration. TypeScript counts both TypeScript modules, package manifest, and compiler configuration. Rust counts both Rust modules and Cargo manifest; its browser loader is embedded in counted Rust source. Every included file's exact bytes, lines, two tokenizer counts, and SHA-256 appear below."},
        {"id": "file_block", "type": "table", "layout": "full", "tableId": "file_table"},
        {"id": "runtime", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## The compact Parley server is locally competitive, not universally faster\n\nParley sustains a **9,312 req/s median**, 5.8681% below Rust's 9,893 but 70.9723% above TypeScript's 5,447 and 154.1748% above Python's 3,664 on this single-threaded localhost test. Parley starts in 16.116 ms, close to Rust's 15.552 ms. Its 8.760-second median clean native-plus-WASM build is 55.6065% below Rust's 19.732 seconds but much slower than Python bytecode or TypeScript transpilation. These execution/build differences are descriptive because the stacks have different concurrency and deployment models."},
        {"id": "load_chart_block", "type": "chart", "layout": "full", "chartId": "load_chart"},
        {"id": "performance_block", "type": "table", "layout": "full", "tableId": "performance_table"},
        {"id": "scope", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Scope and metric definitions\n\nThe population is one release-readiness product with two typed JSON routes, strict failure handling, static assets, and a five-argument browser scoring rule. **Behavior** is 14 frozen HTTP cases plus one real Chrome flow per language. **Authored tokens** are the per-file tiktoken 0.13.0 o200k counts summed over preregistered language-owned application/configuration files. The shared 15,190-byte UI, generated output, dependency source, lockfiles, runtimes, compiler internals, and harness are excluded. Timing uses five deterministically rotated rounds on one Apple Silicon machine."},
        {"id": "method", "type": "markdown", "layout": "full", "body": "## Product, protocol, baselines, and measurement were frozen in that order\n\nProduct commit `e5470b6` froze Parley v0.4.0 before comparison work. Protocol commit `bafeca5` preregistered the task; revision-2 commit `01bc7c3` transparently corrected one pre-measurement 415 error-code transcription after a stopped smoke and changed nothing else. Baseline/harness commit `fa15f1e` passed 60/60 checks and was pushed before the full run. The measured worktree was clean. Dependency downloads were excluded; source files, locks, protocol, cases, raw result, and report transformations remain preserved with hashes."},
        {"id": "limits", "type": "markdown", "layout": "full", "sourceId": SOURCE_ID, "body": "## Limits: one application, source tokens—not agent sessions\n\nThis is one intentionally useful but narrow application, not a representative sample of every backend/frontend task. Framework selection affects baseline size. Counting application source excludes ecosystem implementation cost for every language and therefore cannot compare total engineering complexity. Source tokenizer counts measure representation compactness; they do **not** measure how many Codex tokens a fresh agent needs to build or maintain the app. The local sequential new-connection microbenchmark has five rounds but no independent machines, concurrency sweep, TLS, reverse proxy, database, sustained load, or confidence claim. Python bytecode, TypeScript transpilation, and native compilation are not equivalent build products; artifact closure sizes are likewise descriptive."},
        {"id": "decision", "type": "markdown", "layout": "full", "body": "## Next: expose v0.4.0, then test unseen agent work\n\n1. Ship the typed web/WASM surface as an experimental v0.4.0 preview and dogfood Release Radar for real Parley releases.\n2. Freeze a new set of unseen full-stack implementation and maintenance tasks, then run fresh Codex sessions across all four languages; measure exact behavior, repair rate, session tokens, elapsed time, and maintainability.\n3. Add browser strings, records, and asynchronous HTTP only when Release Radar or another real product needs them; do not tune syntax from this report.\n4. Harden the native server with production evidence—concurrency, graceful shutdown, proxy semantics, observability, and sustained-load tests—before making deployment-performance claims.\n5. Recruit external builders and preserve their failures as product evidence; adoption needs tooling, packages, debugging, and trust, not one benchmark win."},
        {"id": "questions", "type": "markdown", "layout": "full", "body": "## Further questions\n\n- Does the 40.37% authored-token advantage persist across unseen CRUD, authentication, streaming, database, and browser-state products?\n- Do fresh agents spend fewer full-session tokens with Parley once exploration, repairs, and framework discovery are included?\n- Which missing browser or server capability recurs across independent product attempts strongly enough to justify a general language change?\n- How do all four servers behave under sustained concurrency, TLS termination, proxy headers, slow clients, and larger typed payloads?"},
    ]
    manifest_source = {"id": SOURCE_ID, "label": source["label"], "path": source["path"]}
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": "Release Radar Full-Stack Compactness Proof — Iteration 035",
            "description": "Preregistered product-level Parley, Python, TypeScript, and Rust comparison.",
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
            "datasets": data,
        },
        "sources": [source],
        "package_info": {
            "root": "benchmarks/results",
            "manifestPath": f"{STEM}.artifact.json",
            "snapshotPath": "fullstack_035_v0.4.0.json",
            "originUrl": "artifact://parley-fullstack-035",
        },
    }


def main() -> int:
    raw = json.loads(RAW.read_text())
    protocol = json.loads(PROTOCOL.read_text())
    validate(raw, protocol)
    artifact = build(raw)
    output = REPORTS / f"{STEM}.artifact.json"
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
