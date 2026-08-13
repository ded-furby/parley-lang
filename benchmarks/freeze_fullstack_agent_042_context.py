#!/usr/bin/env python3
"""Build the deterministic pre-corpus context freeze for iteration 042."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import tiktoken


REPO = Path(__file__).resolve().parents[1]
CONTEXT = REPO / "skill/parley/references/scaffolded-web-v0.5.3.md"
BASELINE_CORE = REPO / "skill/parley/references/core-v0.5.2.md"
BASELINE_WEB = REPO / "skill/parley/references/web-v0.5.2.md"
ATTRIBUTION = REPO / "benchmarks/fullstack_agent_041_token_attribution.json"
DEFAULT_OUTPUT = REPO / "benchmarks/fullstack_agent_042_context.json"
EVIDENCE_COMMIT = "c18f282da0d358165477daa093844d5ebb4adcda"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict[str, object]:
    encoder = tiktoken.get_encoding("o200k_base")
    context = CONTEXT.read_text(encoding="utf-8")
    baseline = BASELINE_CORE.read_text(encoding="utf-8") + BASELINE_WEB.read_text(
        encoding="utf-8"
    )
    attribution = json.loads(ATTRIBUTION.read_text(encoding="utf-8"))
    assert attribution["raw_sha256"] == (
        "37c27539e9003a7a28bc82b58bdc70fd9f0538a1dd5dc0ab6aa5ff6a6ffff65d"
    )
    context_tokens = len(encoder.encode(context))
    baseline_tokens = len(encoder.encode(baseline))
    assert baseline_tokens == 1164
    return {
        "schema_version": 1,
        "experiment_id": "042-context-freeze",
        "parley_version": "0.5.3",
        "frozen_on": "2026-08-13",
        "evidence_commit": EVIDENCE_COMMIT,
        "evidence_artifact": str(ATTRIBUTION.relative_to(REPO)),
        "evidence_sha256": sha256(ATTRIBUTION),
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
        "preserved_rules": [
            "supplied scaffold is authoritative",
            "edit the smallest owning included logic function",
            "one pure rule serves HTTP and browser paths",
            "multiplication uses times or multiplied by",
            "number from divided decimal is total truncation without otherwise",
            "browser scalar number/decimal/yesno maps to bigint/number/boolean",
        ],
        "deliberate_omissions": [
            "manifest example already printed by the scaffold",
            "handler signatures already printed by the scaffold",
            "record and request boilerplate already printed by the scaffold",
            "JavaScript loader example already implemented by the scaffold",
            "general CLI, collection, JSON, stdlib, and input syntax outside this surface",
        ],
        "construction_boundary": (
            "The context is frozen before any iteration-042 task semantics, cases, "
            "scaffolds, reference implementations, thresholds, or agent output exist."
        ),
        "claim_boundary": (
            "This is a context product and static budget result, not a reliability or "
            "comparative token-efficiency result. It requires validation on a new "
            "disjoint population and does not change iteration 041."
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
