#!/usr/bin/env python3
"""Measure frozen JSON corpus under Parley's verified adaptive packer.

This script measures representation only. It cannot establish that a model
understands TOON as accurately as JSON; the paired agent protocol is a separate
stage in AGENT_DATA_PROTOCOL_033.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = REPO / "benchmarks" / "agent_data_corpus.json"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from parley.agent_data import AgentDataError, compare_value, load_json_file  # noqa: E402


def _load_corpus(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AgentDataError(f"cannot read corpus manifest {path}: {exc}") from exc
    if data.get("schema_version") != 1:
        raise AgentDataError("agent-data corpus must use schema_version 1")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise AgentDataError("agent-data corpus needs a non-empty cases list")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise AgentDataError("every agent-data case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise AgentDataError(f"invalid or duplicate agent-data case id: {case_id!r}")
        seen.add(case_id)
        relative = case.get("path")
        if not isinstance(relative, str) or not relative:
            raise AgentDataError(f"{case_id}: path must be non-empty text")
        resolved = (REPO / relative).resolve()
        if not resolved.is_relative_to(REPO) or not resolved.is_file():
            raise AgentDataError(f"{case_id}: corpus path is missing or outside the repository")
    return data, raw


def measure(corpus_path: Path, tokenizers: list[str]) -> dict[str, Any]:
    corpus, manifest_bytes = _load_corpus(corpus_path)
    loaded: list[tuple[dict[str, Any], Any, bytes]] = []
    corpus_digest = hashlib.sha256()
    corpus_digest.update(manifest_bytes)
    for case in corpus["cases"]:
        path = REPO / case["path"]
        value, raw = load_json_file(path)
        loaded.append((case, value, raw))
        corpus_digest.update(case["id"].encode("utf-8"))
        corpus_digest.update(hashlib.sha256(raw).digest())

    tokenizer_reports: list[dict[str, Any]] = []
    for tokenizer in tokenizers:
        rows: list[dict[str, Any]] = []
        total_json = 0
        total_selected = 0
        supported = 0
        selected_toon = 0
        fallback_unsupported = 0
        fallback_not_smaller = 0
        for case, value, raw in loaded:
            comparison = compare_value(value, tokenizer=tokenizer, source_bytes=raw)
            json_tokens = comparison["candidates"]["json"]["tokens"]
            toon = comparison["candidates"]["toon"]
            selected_tokens = (
                toon["tokens"] if comparison["selected_format"] == "toon" else json_tokens
            )
            total_json += json_tokens
            total_selected += selected_tokens
            if toon["supported"]:
                supported += 1
            if comparison["selected_format"] == "toon":
                selected_toon += 1
            elif comparison["selection_reason"] == "toon_unsupported":
                fallback_unsupported += 1
            else:
                fallback_not_smaller += 1
            rows.append({
                "id": case["id"],
                "family": case["family"],
                "origin": case["origin"],
                "path": case["path"],
                "input_sha256": comparison["input_sha256"],
                "json_tokens": json_tokens,
                "toon_supported": toon["supported"],
                "toon_tokens": toon.get("tokens"),
                "toon_reason": toon.get("reason"),
                "selected_format": comparison["selected_format"],
                "selection_reason": comparison["selection_reason"],
                "selected_tokens": selected_tokens,
                "savings_tokens": json_tokens - selected_tokens,
            })
        saved = total_json - total_selected
        tokenizer_reports.append({
            "tokenizer": rows and compare_value(
                loaded[0][1], tokenizer=tokenizer
            )["tokenizer"],
            "summary": {
                "cases": len(rows),
                "toon_supported": supported,
                "toon_selected": selected_toon,
                "json_fallback_unsupported": fallback_unsupported,
                "json_fallback_not_smaller": fallback_not_smaller,
                "compact_json_tokens": total_json,
                "adaptive_tokens": total_selected,
                "savings_tokens": saved,
                "savings_percent_vs_compact_json": round(
                    100.0 * saved / total_json if total_json else 0.0, 4
                ),
                "all_supported_round_trip": all(
                    not row["toon_supported"]
                    or row["selection_reason"] in {"strictly_fewer_tokens", "json_not_larger"}
                    for row in rows
                ),
                "auto_never_increases_tokens": all(
                    row["selected_tokens"] <= row["json_tokens"] for row in rows
                ),
            },
            "cases": rows,
        })
    return {
        "schema_version": 1,
        "experiment_id": corpus["experiment_id"],
        "measurement_scope": "representation-only-not-model-accuracy",
        "corpus_manifest": corpus_path.resolve().relative_to(REPO).as_posix(),
        "corpus_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "corpus_content_sha256": corpus_digest.hexdigest(),
        "tokenizers": tokenizer_reports,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument(
        "--tokenizer",
        action="append",
        dest="tokenizers",
        help="rough or a tiktoken encoding; may repeat (default: rough)",
    )
    parser.add_argument("--output", type=Path, help="write deterministic JSON to this file")
    parser.add_argument("--force", action="store_true", help="replace an existing output file")
    args = parser.parse_args(argv)
    try:
        result = measure(args.corpus, args.tokenizers or ["rough"])
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            output = args.output.resolve()
            if output.exists() and not args.force:
                raise AgentDataError(f"output already exists: {args.output}; pass --force")
            if not output.parent.is_dir():
                raise AgentDataError(f"output directory does not exist: {output.parent}")
            output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except (AgentDataError, OSError) as exc:
        print(f"agent-data measurement error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
