#!/usr/bin/env python3
"""Build the deterministic pre-corpus compact-context freeze for study 046."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import tiktoken


REPO = Path(__file__).resolve().parents[1]
OLD = REPO / "skill/parley/references/scaffolded-response-web-v0.5.6.md"
NEW = REPO / "skill/parley/references/scaffolded-response-web-v0.5.6-compact.md"
SPEC = REPO / "benchmarks/RESPONSE_CONTEXT_OPTIMIZATION_004.md"
DEFAULT_OUTPUT = REPO / "benchmarks/fullstack_agent_046_context.json"
PREREGISTRATION_COMMIT = "0497d96bea69ee4b74f316228ca8aef51cc2b3ae"
O200K = tiktoken.get_encoding("o200k_base")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(path: Path) -> dict[str, int | str]:
    payload = path.read_bytes()
    text = payload.decode("utf-8")
    return {
        "file": path.relative_to(REPO).as_posix(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "o200k_base_tokens": len(O200K.encode(text)),
    }


def build() -> dict[str, object]:
    old = metrics(OLD)
    new = metrics(NEW)
    assert old == {
        "file": "skill/parley/references/scaffolded-response-web-v0.5.6.md",
        "sha256": "58e1066e2c313c35617d96c5f8829e4ca14f6a77a60fdba0d8af7b19a2fab2b8",
        "bytes": 1281,
        "o200k_base_tokens": 313,
    }
    assert int(new["bytes"]) <= 550
    assert int(new["o200k_base_tokens"]) <= 128
    return {
        "schema_version": 1,
        "experiment_id": "046",
        "phase": "pre-corpus context freeze",
        "preregistered_on": "2026-08-13",
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "optimization_spec_file": SPEC.relative_to(REPO).as_posix(),
        "optimization_spec_sha256": digest(SPEC),
        "historical_context": old,
        "compact_context": new,
        "reduction": {
            "bytes": int(old["bytes"]) - int(new["bytes"]),
            "o200k_base_tokens": int(old["o200k_base_tokens"])
            - int(new["o200k_base_tokens"]),
            "token_percent": round(
                (1 - int(new["o200k_base_tokens"]) / int(old["o200k_base_tokens"]))
                * 100,
                4,
            ),
        },
        "future_manifest_policy": {
            "serialization": "json.dumps(value, separators=(',', ':')) + newline",
            "maximum_o200k_base_tokens": 135,
            "semantic_equivalence_required": True,
        },
        "corpus_selected_before_freeze": False,
        "measured_sessions_before_freeze": 0,
        "claim_boundary": (
            "Artifact reduction is established; complete session-token and elapsed "
            "effects require a new frozen corpus and cannot revise iteration 045."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
