#!/usr/bin/env python3
"""Freeze the study-046 product/evidence boundary before corpus selection."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_046_product.json"
PRODUCT_COMMIT = "6bae1149d101d5a483f31f55905083e0a939c1da"
PRODUCT_TREE = "525b23b0191cb5f16a9cc4b5281d9b9af912898c"
CONTEXT_COMMIT = "2b55413953d1f8f17478875f1742f22e802b4c3a"
CONTEXT_TREE = "0f01b7cb3423d90447af207543910020464caeaf"
EVIDENCE_COMMIT = "df2c1944b29081064789b6005ffcc12cf0f52823"
EVIDENCE_TREE = "d4dda528c5d00b972c4f02e63d62f2ee1014b553"
ITERATION_045_RESULT_COMMIT = "61fe34729f6361846cf418183cc3fa240c09516c"
ITERATION_045_RESULT_TREE = "47bc7ddd46b9cff8aa1192ff9156f10c0bc29415"
EXPECTED_FILE_DIGESTS = {
    "context_freeze": "32ba3aaf03c0d397ac9e0e845443bd2c2c9240e2f5102d844278f00d6fa07fee",
    "compact_context": "12515da0f10ab5c3312edcb21b233d786f20bc4c444598acd26e589109b84580",
    "evidence_implementation": "dad9f4144e0dfa1c21d29e4362f116abd38c5181664a82dbb161b3358e70689c",
    "iteration_045_raw": "521f706074526ec34a34d6cbba98ce4db427d1490433e8188b23094a7313e7f9",
    "iteration_045_audit": "26c8b3ed87a68b50411c8f0232db9d848d6faab3aebf34f496596b66f2122f07",
    "iteration_045_report": "a8653c7e0ace7698192154892175a0fe603c70d6c108256ea7a768b9da850239",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def build() -> dict[str, object]:
    assert git("show", "-s", "--format=%T", PRODUCT_COMMIT) == PRODUCT_TREE
    assert git("show", "-s", "--format=%T", CONTEXT_COMMIT) == CONTEXT_TREE
    assert git("show", "-s", "--format=%T", EVIDENCE_COMMIT) == EVIDENCE_TREE
    assert (
        git("show", "-s", "--format=%T", ITERATION_045_RESULT_COMMIT)
        == ITERATION_045_RESULT_TREE
    )
    assert not git("diff", "--name-only", PRODUCT_COMMIT, "--", "parley", "pyproject.toml")
    forbidden = (
        "fullstack_agent_046_tasks.json",
        "fullstack_agent_046_cases.json",
        "fullstack_agent_046_protocol.json",
        "fullstack_agent_046_scaffolds.py",
        "fullstack_agent_046_logic.py",
        "fullstack_agent_046_raw.json",
        "fullstack_agent_046_audit.json",
    )
    frozen_paths = set(git("ls-tree", "-r", "--name-only", CONTEXT_COMMIT).splitlines())
    assert not any(f"benchmarks/{name}" in frozen_paths for name in forbidden)
    files = {
        "context_freeze": BENCHMARKS / "fullstack_agent_046_context.json",
        "compact_context": REPO
        / "skill/parley/references/scaffolded-response-web-v0.5.6-compact.md",
        "evidence_implementation": BENCHMARKS / "json_evidence.py",
        "iteration_045_raw": BENCHMARKS / "fullstack_agent_045_raw.json",
        "iteration_045_audit": BENCHMARKS / "fullstack_agent_045_audit.json",
        "iteration_045_report": BENCHMARKS / "FULLSTACK_AGENT_045_RESULT.md",
    }
    actual_digests = {name: digest(path) for name, path in files.items()}
    assert actual_digests == EXPECTED_FILE_DIGESTS
    return {
        "schema_version": 1,
        "experiment_id": "046",
        "phase": "pre-corpus product and evidence freeze",
        "frozen_on": "2026-08-13",
        "parley": {
            "version": "0.5.6",
            "product_commit": PRODUCT_COMMIT,
            "product_tree": PRODUCT_TREE,
        },
        "context": {
            "commit": CONTEXT_COMMIT,
            "tree": CONTEXT_TREE,
            "o200k_base_tokens": 124,
            "maximum_tokens": 128,
        },
        "evidence_boundary": {
            "json_native_commit": EVIDENCE_COMMIT,
            "json_native_tree": EVIDENCE_TREE,
            "required_header_pair_shape": "list[list[str, str]]",
            "required_pre_measurement_controls": [
                "empty header pairs survive live-to-persisted equality",
                "custom header pairs survive live-to-persisted equality",
                "duplicate header pairs survive live-to-persisted equality",
                "non-finite JSON evidence is rejected",
            ],
        },
        "iteration_045_boundary": {
            "result_commit": ITERATION_045_RESULT_COMMIT,
            "result_tree": ITERATION_045_RESULT_TREE,
            "status": "invalid; frozen gate failed",
            "selective_rerun": False,
            "same_corpus_reuse": False,
        },
        "files": {
            name: {
                "file": path.relative_to(REPO).as_posix(),
                "sha256": actual_digests[name],
            }
            for name, path in files.items()
        },
        "pre_corpus_anchor_commit": CONTEXT_COMMIT,
        "corpus_selected_before_freeze": False,
        "measured_sessions_before_freeze": 0,
        "next_step": (
            "Select and freeze new response-control task semantics that are disjoint "
            "from iterations 036-045 before any scaffold or model output."
        ),
        "claim_boundary": (
            "No language superiority or session-efficiency claim follows from this "
            "product/evidence freeze."
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
