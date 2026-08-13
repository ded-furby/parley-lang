#!/usr/bin/env python3
"""Build the deterministic pre-corpus v0.5.8 context freeze for study 048."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import tiktoken


REPO = Path(__file__).resolve().parents[1]
CONTEXT = REPO / "skill/parley/references/scaffolded-query-response-web-v0.5.8-compact.md"
PRODUCT_RESULT = REPO / "benchmarks/WEB_QUERY_PARAMETERS_005_RESULT.md"
DEFAULT_OUTPUT = REPO / "benchmarks/fullstack_agent_048_context.json"
PRODUCT_COMMIT = "8d040c55fcc4ad502bdc6449c363035a42d0dceb"
PRODUCT_TREE = "2eed6a33517c6a31311348314093aaa1ef66d2be"
O200K = tiktoken.get_encoding("o200k_base")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.strip()


def metrics(path: Path) -> dict[str, int | str]:
    payload = path.read_bytes()
    return {
        "file": path.relative_to(REPO).as_posix(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "o200k_base_tokens": len(O200K.encode(payload.decode("utf-8"))),
    }


def build() -> dict[str, object]:
    product_commit = git("rev-parse", PRODUCT_COMMIT)
    product_tree = git("show", "-s", "--format=%T", product_commit)
    assert product_commit == PRODUCT_COMMIT
    assert product_tree == PRODUCT_TREE
    context = metrics(CONTEXT)
    assert int(context["bytes"]) <= 950
    assert int(context["o200k_base_tokens"]) <= 225
    forbidden = (
        "fullstack_agent_048_tasks.json",
        "fullstack_agent_048_cases.json",
        "fullstack_agent_048_protocol.json",
        "fullstack_agent_048_scaffolds.py",
        "fullstack_agent_048_raw.json",
    )
    paths = set(git("ls-tree", "-r", "--name-only", product_commit).splitlines())
    assert not any(f"benchmarks/{name}" in paths for name in forbidden)
    return {
        "schema_version": 1,
        "experiment_id": "048",
        "phase": "pre-corpus context freeze",
        "frozen_on": "2026-08-13",
        "product": {
            "version": "0.5.8",
            "commit": product_commit,
            "tree": product_tree,
            "query_parameter_result": {
                "file": PRODUCT_RESULT.relative_to(REPO).as_posix(),
                "sha256": digest(PRODUCT_RESULT),
            },
        },
        "context": context,
        "maximum_o200k_base_tokens": 225,
        "corpus_selected_before_freeze": False,
        "measured_sessions_before_freeze": 0,
        "claim_boundary": (
            "This freezes compact v0.5.8 instructions before task selection; it "
            "does not establish session efficiency or universal superiority."
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
