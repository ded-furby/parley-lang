#!/usr/bin/env python3
"""Build the deterministic pre-corpus response-web context freeze for 045."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import tiktoken


REPO = Path(__file__).resolve().parents[1]
CONTEXT = REPO / "skill/parley/references/scaffolded-response-web-v0.5.6.md"
BASELINE_CORE = REPO / "skill/parley/references/core-v0.5.2.md"
BASELINE_WEB = REPO / "skill/parley/references/web-v0.5.2.md"
PRODUCT_PROTOCOL = REPO / "benchmarks/WEB_RESPONSE_CONTROL_003.md"
DEFAULT_OUTPUT = REPO / "benchmarks/fullstack_agent_045_context.json"
PRODUCT_COMMIT = "6bae1149d101d5a483f31f55905083e0a939c1da"
PRODUCT_TREE = "525b23b0191cb5f16a9cc4b5281d9b9af912898c"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict[str, object]:
    encoder = tiktoken.get_encoding("o200k_base")
    context = CONTEXT.read_text(encoding="utf-8")
    baseline = BASELINE_CORE.read_text(encoding="utf-8") + BASELINE_WEB.read_text(
        encoding="utf-8"
    )
    context_tokens = len(encoder.encode(context))
    baseline_tokens = len(encoder.encode(baseline))
    assert len(context.encode()) == 1281
    assert context_tokens == 313
    assert baseline_tokens == 1164
    return {
        "schema_version": 1,
        "experiment_id": "045-context-freeze",
        "parley_version": "0.5.6",
        "frozen_on": "2026-08-13",
        "product_commit": PRODUCT_COMMIT,
        "product_tree": PRODUCT_TREE,
        "product_protocol": str(PRODUCT_PROTOCOL.relative_to(REPO)),
        "product_protocol_sha256": sha256(PRODUCT_PROTOCOL),
        "context_file": str(CONTEXT.relative_to(REPO)),
        "context_sha256": sha256(CONTEXT),
        "context_bytes": len(context.encode()),
        "context_o200k_tokens": context_tokens,
        "baseline": {
            "version": "0.5.2",
            "files": [
                str(BASELINE_CORE.relative_to(REPO)),
                str(BASELINE_WEB.relative_to(REPO)),
            ],
            "combined_sha256": hashlib.sha256(baseline.encode()).hexdigest(),
            "combined_bytes": len(baseline.encode()),
            "combined_o200k_tokens": baseline_tokens,
        },
        "reduction": {
            "bytes": len(baseline.encode()) - len(context.encode()),
            "o200k_tokens": baseline_tokens - context_tokens,
            "o200k_percent": round((1 - context_tokens / baseline_tokens) * 100, 4),
        },
        "increment_from_v053_card": {
            "previous_o200k_tokens": 222,
            "added_o200k_tokens": context_tokens - 222,
            "reason": (
                "Adds the exact dynamic response manifest/record contract, header "
                "map operations, request-header lookup, and safe status/header boundary."
            ),
        },
        "preserved_rules": [
            "printed scaffold is authoritative",
            "make the smallest owning change and keep shared rules pure",
            "dynamic response record matches the three manifest fields exactly",
            "request and response header map operations use checked Parley syntax",
            "dynamic statuses stay within 200 through 599",
            "server-owned framing and hop-by-hop headers remain forbidden",
            "browser scalar number/decimal/yesno maps to bigint/number/boolean",
            "only the supplied checker may run",
        ],
        "construction_boundary": (
            "The response-web card is frozen after v0.5.6 and before any "
            "iteration-045 task domain, route, field, formula, case, scaffold, "
            "reference implementation, threshold, or model output exists."
        ),
        "claim_boundary": (
            "This is a static context budget and coverage result, not evidence of "
            "agent correctness, lower complete-session tokens, or universal superiority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
