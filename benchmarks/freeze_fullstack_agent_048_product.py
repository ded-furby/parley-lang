#!/usr/bin/env python3
"""Freeze Parley v0.5.8 and evidence inputs before study-048 corpus selection."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO / "benchmarks/fullstack_agent_048_product.json"
PRODUCT_COMMIT = "8d040c55fcc4ad502bdc6449c363035a42d0dceb"
PRODUCT_TREE = "2eed6a33517c6a31311348314093aaa1ef66d2be"
CONTEXT_COMMIT = "b7e65e3441d4dbaeeeea1ee5da165cae84dadf01"
CONTEXT_TREE = "ff6694876095edf7b7ab24a1c428fe668c78889b"
PRODUCT_FILES = {
    "parley/web.py": "d0bbe5cfcf774c7bb79ab7949a2705dd9df52fa408b7fb370ab3cf4af16ddf29",
    "parley/cli.py": "ce53c588510924c847b812f6115973fdb9dadbaff291fe2465dd4ed10f438872",
    "parley/diagnostics.py": "506f91ce3b8c9207ea3022edab49f99677aed196efabb714674e42ec384ee5d0",
    "parley/__init__.py": "bb87a6127b4425c1877fd377b61952ce29839215c9c3a65acd0efeffa12b1b5d",
    "pyproject.toml": "65ac4e0610964af8d25adf567587b1694b54fa43f3b18b0ed73d73f29ffd7401",
    "benchmarks/WEB_QUERY_PARAMETERS_005.md": "8c4d96512af3759d635d410b4b7372e268e80af5d90a94a00b895c6c9c1a64c3",
    "benchmarks/WEB_QUERY_PARAMETERS_005_RESULT.md": "79de0a0a042c88dc7d5b08d5704f1bc727030d2de27b69ece69257db9115d5c4",
    "docs/WEB_QUERY_PARAMETERS.md": "16da1feffc852af5c60bddf29377f435cd51f8ff31d61e6d9dd017181128c0b3",
    "skill/parley/references/web-v0.5.8.md": "9b05892f00cffa11bc84f7eff18ec7dedfd7c9c42b41ca1ae0cdbd799f49670e",
    "tests/test_web_query_parameters_005.py": "20567ef654be3ee081af5ca43b33869d630eede2d1c8373bee5c8490e2734fb0",
}
CONTEXT_FILES = {
    "skill/parley/references/scaffolded-query-response-web-v0.5.8-compact.md": "f7cadc7bfe839a5174bc1064fbed3a021ab9251386b57173bdf6e69b75ed7a92",
    "benchmarks/fullstack_agent_048_context.json": "36f85d7bcfb9d2f5e91cdb4ae8223b7a639b2ecf6a341eb538f321bcd1569f33",
    "benchmarks/build_fullstack_agent_048_context.py": "05e7cc412e549d8a33e2cbd8904096fd4a699ac3282d3f1860da76f16d354bb9",
}
PREVIOUS_FILES = {
    "benchmarks/fullstack_agent_047_raw.json": "f04515b84abfbb2a3fe0477c7d0d5c5de9eba8a6f4de3eba2cf062886e779d28",
    "benchmarks/fullstack_agent_047_audit.json": "0fc04897b4ba3a5e24c35b1b7d6235f1cde5835c005004a1f5a0fb2053182f5a",
    "benchmarks/FULLSTACK_AGENT_047_RESULT.md": "f62e5de9d6e98c45c3b80788276c3e3f03782efcde2ec644404f920733ec182b",
    "benchmarks/fullstack_agent_047_attribution.json": "a9ee9b9961c408cef70ccd6bec6bfa23995abdea5fdf761080988c957f420865",
    "benchmarks/FULLSTACK_AGENT_047_ATTRIBUTION.md": "b68a27c86423b917186dab13e0664cdd75183916bc32a4dd924564a6a1382746",
}
EVIDENCE_FILE = "benchmarks/json_evidence.py"
EVIDENCE_SHA256 = "dad9f4144e0dfa1c21d29e4362f116abd38c5181664a82dbb161b3358e70689c"


def git(*args: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, check=True, text=not binary
    )
    return completed.stdout if binary else completed.stdout.strip()


def git_blob(commit: str, relative: str) -> bytes:
    value = git("show", f"{commit}:{relative}", binary=True)
    assert isinstance(value, bytes)
    return value


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def verify_files(commit: str, expected: dict[str, str]) -> dict[str, str]:
    actual = {path: digest(git_blob(commit, path)) for path in expected}
    assert actual == expected
    return actual


def build() -> dict[str, object]:
    assert git("rev-parse", f"{PRODUCT_COMMIT}^{{tree}}") == PRODUCT_TREE
    assert git("rev-parse", f"{CONTEXT_COMMIT}^{{tree}}") == CONTEXT_TREE
    product = verify_files(PRODUCT_COMMIT, PRODUCT_FILES)
    context_files = verify_files(CONTEXT_COMMIT, CONTEXT_FILES)
    previous = verify_files(PRODUCT_COMMIT, PREVIOUS_FILES)
    evidence = digest(git_blob(PRODUCT_COMMIT, EVIDENCE_FILE))
    assert evidence == EVIDENCE_SHA256
    assert '__version__ = "0.5.8"' in git_blob(
        PRODUCT_COMMIT, "parley/__init__.py"
    ).decode()
    assert 'version = "0.5.8"' in git_blob(PRODUCT_COMMIT, "pyproject.toml").decode()

    context = json.loads(git_blob(CONTEXT_COMMIT, "benchmarks/fullstack_agent_048_context.json"))
    assert context["context"]["o200k_base_tokens"] == 217
    assert context["corpus_selected_before_freeze"] is False
    forbidden = (
        "fullstack_agent_048_tasks.json",
        "fullstack_agent_048_cases.json",
        "fullstack_agent_048_protocol.json",
        "fullstack_agent_048_scaffolds.py",
        "fullstack_agent_048_raw.json",
    )
    frozen_paths = set(str(git("ls-tree", "-r", "--name-only", CONTEXT_COMMIT)).splitlines())
    assert not any(f"benchmarks/{name}" in frozen_paths for name in forbidden)

    return {
        "schema_version": 1,
        "experiment_id": "048",
        "phase": "pre-corpus product and evidence freeze",
        "frozen_on": "2026-08-13",
        "parley": {
            "version": "0.5.8",
            "product_commit": PRODUCT_COMMIT,
            "product_tree": PRODUCT_TREE,
            "accepted_product_gate": "9 dedicated and 767 complete tests passed",
            "wheel_sha256": "044af3f790226b1bef82709c0f7c6d84121180476d96da1539eee2e69d141a67",
        },
        "context": {
            "commit": CONTEXT_COMMIT,
            "tree": CONTEXT_TREE,
            "bytes": context["context"]["bytes"],
            "o200k_base_tokens": context["context"]["o200k_base_tokens"],
            "maximum_tokens": context["maximum_o200k_base_tokens"],
        },
        "files": {
            "product": product,
            "context": context_files,
            "evidence": {EVIDENCE_FILE: evidence},
        },
        "evidence_boundary": {
            "json_native_header_pairs": True,
            "non_finite_json_rejected": True,
            "route_path_path_parameters_and_query_parameters_must_match_live_and_persisted_evidence": True,
        },
        "previous_study_boundary": {
            "experiment_id": "047",
            "result_commit": PRODUCT_COMMIT,
            "result_tree": PRODUCT_TREE,
            "status": "valid; strict gate failed on tokens and elapsed time",
            "selective_rerun": False,
            "same_corpus_reuse": False,
            "files": previous,
        },
        "pre_corpus_anchor_commit": CONTEXT_COMMIT,
        "corpus_selected_before_freeze": False,
        "measured_sessions_before_freeze": 0,
        "next_step": (
            "Select and freeze new query-routing semantics disjoint from all previous "
            "measured corpora before building scaffolds or prompts."
        ),
        "claim_boundary": (
            "This checkpoint establishes reproducibility only; it does not establish "
            "agent efficiency, broad framework parity, or universal superiority."
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
