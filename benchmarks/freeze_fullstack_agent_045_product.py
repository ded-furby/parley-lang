#!/usr/bin/env python3
"""Build the deterministic pre-corpus Parley v0.5.6 freeze for iteration 045."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO / "benchmarks/fullstack_agent_045_product.json"
PRODUCT_COMMIT = "6bae1149d101d5a483f31f55905083e0a939c1da"
PRODUCT_TREE = "525b23b0191cb5f16a9cc4b5281d9b9af912898c"
CONTEXT_COMMIT = "1a73fc7ea7d60f5235d5cd3173eba858a6a384b7"
CONTEXT_TREE = "b704aff898c299d0d15f549f30078753ae35e7b9"
PRODUCT_FILES = (
    "parley/web.py",
    "parley/cli.py",
    "parley/diagnostics.py",
    "parley/__init__.py",
    "pyproject.toml",
)
VERIFICATION_FILES = (
    "tests/test_web.py",
    "tests/test_web_response_control_003.py",
)
PRODUCT_PROTOCOL = "benchmarks/WEB_RESPONSE_CONTROL_003.md"
USER_REFERENCE = "docs/WEB_RESPONSE_CONTROL.md"
AGENT_REFERENCE = "skill/parley/references/web-v0.5.6.md"
CONTEXT = "skill/parley/references/scaffolded-response-web-v0.5.6.md"
CONTEXT_FREEZE = "benchmarks/fullstack_agent_045_context.json"


def git_blob(commit: str, relative: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=REPO,
        capture_output=True,
        check=True,
    )
    return completed.stdout


def git_tree(commit: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", f"{commit}^{{tree}}"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build() -> dict[str, object]:
    assert git_tree(PRODUCT_COMMIT) == PRODUCT_TREE
    assert git_tree(CONTEXT_COMMIT) == CONTEXT_TREE
    init = git_blob(PRODUCT_COMMIT, "parley/__init__.py").decode()
    package = git_blob(PRODUCT_COMMIT, "pyproject.toml").decode()
    protocol_blob = git_blob(PRODUCT_COMMIT, PRODUCT_PROTOCOL)
    protocol = protocol_blob.decode()
    normalized_protocol = " ".join(protocol.split())
    context_blob = git_blob(CONTEXT_COMMIT, CONTEXT)
    context_freeze_blob = git_blob(CONTEXT_COMMIT, CONTEXT_FREEZE)
    context_freeze = json.loads(context_freeze_blob)
    assert '__version__ = "0.5.6"' in init
    assert 'version = "0.5.6"' in package
    assert "643/643" in protocol
    assert "No post-v0.5.5 agent comparison has yet been run" in normalized_protocol
    assert context_freeze["context_o200k_tokens"] == 313
    assert context_freeze["product_commit"] == PRODUCT_COMMIT
    return {
        "schema_version": 1,
        "experiment_id": "045-product-freeze",
        "frozen_on": "2026-08-13",
        "parley_version": "0.5.6",
        "product_commit": PRODUCT_COMMIT,
        "product_tree": PRODUCT_TREE,
        "context_commit": CONTEXT_COMMIT,
        "context_tree": CONTEXT_TREE,
        "product_files": {
            relative: sha256(git_blob(PRODUCT_COMMIT, relative))
            for relative in PRODUCT_FILES
        },
        "verification_files": {
            relative: sha256(git_blob(PRODUCT_COMMIT, relative))
            for relative in VERIFICATION_FILES
        },
        "product_evidence": {
            "protocol_file": PRODUCT_PROTOCOL,
            "protocol_sha256": sha256(protocol_blob),
            "dedicated_tests_passed": 14,
            "full_tests_before_version_advance": 643,
            "full_tests_after_version_advance": 643,
            "release_wheel": "parley_lang-0.5.6-py3-none-any.whl",
            "release_wheel_bytes": 143349,
            "release_wheel_sha256": (
                "f3fa31b3fb7ff23faa5f13b54d32c3f26a8cc65daed28cdbb21458263314a458"
            ),
            "accepted": True,
        },
        "agent_context": {
            "file": CONTEXT,
            "sha256": sha256(context_blob),
            "bytes": len(context_blob),
            "o200k_base_tokens": context_freeze["context_o200k_tokens"],
            "freeze_file": CONTEXT_FREEZE,
            "freeze_sha256": sha256(context_freeze_blob),
            "baseline_reduction_percent": context_freeze["reduction"][
                "o200k_percent"
            ],
        },
        "references": {
            relative: sha256(git_blob(PRODUCT_COMMIT, relative))
            for relative in (USER_REFERENCE, AGENT_REFERENCE)
        },
        "frozen_capabilities": [
            "opt-in checked status/header/body response envelopes",
            "request-dependent statuses from 200 through 599",
            "bounded normalized application response headers",
            "rejection of invalid, duplicate, control-bearing, framing, and hop-by-hop headers",
            "bodyless 204, 205, and 304 semantics plus GET-equivalent HEAD metadata",
            "unchanged static success-status routes and both strict JSON backends",
        ],
        "construction_boundary": (
            "The v0.5.6 product, verification, and 313-token context are frozen "
            "before any iteration-045 task domain, route, field, formula, case, "
            "scaffold, reference implementation, threshold, prompt, or model output "
            "is selected."
        ),
        "claim_boundary": (
            "This freeze records an accepted generic product capability and static "
            "context budget. It does not reinterpret iteration 044, measure successor "
            "agent behavior, prove framework parity, or establish universal superiority."
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
