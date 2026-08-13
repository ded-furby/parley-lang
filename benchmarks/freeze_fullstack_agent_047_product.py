#!/usr/bin/env python3
"""Freeze Parley v0.5.7 and evidence inputs before study-047 corpus selection."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO / "benchmarks/fullstack_agent_047_product.json"
PRODUCT_COMMIT = "c9e8c9bea770c9243ac244663c28209bb18264df"
PRODUCT_TREE = "c749b23a61ec360cd4ad33d5fd93dc700a278927"
CONTEXT_COMMIT = "0791f128b90437b4970cf5c414e8674a6f508889"
CONTEXT_TREE = "22a1dd59a3a407b7dc8a0520acbdfeb5aa0d6b04"
PREVIOUS_RESULT_COMMIT = "3310b7b08ce26e49d695ca327624cef22abeb68d"
PREVIOUS_RESULT_TREE = "d2b944b13190dfc8bb5394654b6428b0904f80f9"
PRODUCT_FILES = (
    "parley/web.py",
    "parley/cli.py",
    "parley/diagnostics.py",
    "parley/__init__.py",
    "pyproject.toml",
    "benchmarks/WEB_PATH_PARAMETERS_004.md",
    "benchmarks/WEB_PATH_PARAMETERS_004_RESULT.md",
    "docs/WEB_PATH_PARAMETERS.md",
    "skill/parley/references/web-v0.5.7.md",
    "tests/test_web_path_parameters_004.py",
)
CONTEXT_FILES = (
    "skill/parley/references/scaffolded-path-response-web-v0.5.7-compact.md",
    "benchmarks/fullstack_agent_047_context.json",
    "benchmarks/build_fullstack_agent_047_context.py",
)
EVIDENCE_FILE = "benchmarks/json_evidence.py"
PREVIOUS_STUDY_FILES = (
    "benchmarks/fullstack_agent_046_tasks.json",
    "benchmarks/fullstack_agent_046_cases.json",
    "benchmarks/fullstack_agent_046_protocol.json",
    "benchmarks/fullstack_agent_046_raw.json",
    "benchmarks/fullstack_agent_046_audit.json",
    "benchmarks/FULLSTACK_AGENT_046_RESULT.md",
)
EXPECTED_PRODUCT_DIGESTS = {
    "parley/web.py": "3ccc181a93f47356da04ce6f624062d2e7584b1ce5db58bd0a4f79bb9857cdfd",
    "parley/cli.py": "e8c3faf4973a1f59967eca61d3cf1cf1560cfad63363e5d70bb73c62be7d5f28",
    "parley/diagnostics.py": "ce639286cd3582b2d34293f9f451e8d988adf592b37addaa44bc9f5691b5117f",
    "parley/__init__.py": "ed63eafd1e9c6a64064364846b0246112e957e3620545b96f98a2d45cf68d150",
    "pyproject.toml": "410b6f5da1f4246f1949a80a40d8926c9cc5db69219f714cd14d654be7992273",
    "benchmarks/WEB_PATH_PARAMETERS_004.md": "d27d2f3ab39dd4ec3578f362ee7a3d4cf347526cc5039d7ac0159f29b398a531",
    "benchmarks/WEB_PATH_PARAMETERS_004_RESULT.md": "73b739ab1b067be36f7adff190406f4fe9d9747f9500f4bf723a7457315a26b0",
    "docs/WEB_PATH_PARAMETERS.md": "bc01befe0f6cf7739c000674c115da9e13b22e69867fc3e162ce16573609e2cd",
    "skill/parley/references/web-v0.5.7.md": "b98288c8a5e237c4dba8dfefb9c8291f766f9edc03290c4dd04fc5645ea90b11",
    "tests/test_web_path_parameters_004.py": "8fb5fe57979bcfdd261fb6e64b0fac8b433e893fcc5e8bf7ba98cb95a3001097",
}
EXPECTED_CONTEXT_DIGESTS = {
    "skill/parley/references/scaffolded-path-response-web-v0.5.7-compact.md": "b3d0473cdc4e17741bebe1c24441f337abc7579bd59783b1cd94e645bb698f23",
    "benchmarks/fullstack_agent_047_context.json": "857bfc8b06428cc6fe2038175d9758e481b6eb4bff90f77a4040a70e0a8fa7ae",
    "benchmarks/build_fullstack_agent_047_context.py": "66d3e209ea6b16c21b7259cd8ecf394839d5926f9855351b817b16fa83f4a855",
}
EXPECTED_PREVIOUS_DIGESTS = {
    "benchmarks/fullstack_agent_046_tasks.json": "37588deca94b4e24dc633a705487db6a637380ff3c9a19475bdf69ef92e69091",
    "benchmarks/fullstack_agent_046_cases.json": "8774d5804d45a6bb44aee24910dea0bf1c29046fbe87aadd100524edf448603c",
    "benchmarks/fullstack_agent_046_protocol.json": "5a19c535425fdb996d2741dbebebc67f7f0b1ada09ad8603c8868e836eaa936d",
    "benchmarks/fullstack_agent_046_raw.json": "0117effbc633affb6d79d14e8f1b713634ca3c5c263537e1ba2207b7ccaf2d07",
    "benchmarks/fullstack_agent_046_audit.json": "5251e814218fc7b502e9e05c2fc6a13da6d3cdabe41906a9eb024e1b0e3ccbad",
    "benchmarks/FULLSTACK_AGENT_046_RESULT.md": "d4341b1e697e4d8ad284fa0f939e04ed4785e6847ccf5f3ad733ef947637cde0",
}


def git(*args: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, check=True, text=not binary
    )
    return completed.stdout if binary else completed.stdout.strip()


def git_blob(commit: str, relative: str) -> bytes:
    value = git("show", f"{commit}:{relative}", binary=True)
    assert isinstance(value, bytes)
    return value


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digests(commit: str, paths: tuple[str, ...]) -> dict[str, str]:
    return {path: sha256(git_blob(commit, path)) for path in paths}


def build() -> dict[str, object]:
    assert git("rev-parse", f"{PRODUCT_COMMIT}^{{tree}}") == PRODUCT_TREE
    assert git("rev-parse", f"{CONTEXT_COMMIT}^{{tree}}") == CONTEXT_TREE
    assert git("rev-parse", f"{PREVIOUS_RESULT_COMMIT}^{{tree}}") == PREVIOUS_RESULT_TREE
    assert '__version__ = "0.5.7"' in git_blob(
        PRODUCT_COMMIT, "parley/__init__.py"
    ).decode()
    assert 'version = "0.5.7"' in git_blob(PRODUCT_COMMIT, "pyproject.toml").decode()

    product_digests = digests(PRODUCT_COMMIT, PRODUCT_FILES)
    context_digests = digests(CONTEXT_COMMIT, CONTEXT_FILES)
    previous_digests = digests(PREVIOUS_RESULT_COMMIT, PREVIOUS_STUDY_FILES)
    evidence_digest = sha256(git_blob(CONTEXT_COMMIT, EVIDENCE_FILE))
    assert product_digests == EXPECTED_PRODUCT_DIGESTS
    assert context_digests == EXPECTED_CONTEXT_DIGESTS
    assert previous_digests == EXPECTED_PREVIOUS_DIGESTS
    assert evidence_digest == "dad9f4144e0dfa1c21d29e4362f116abd38c5181664a82dbb161b3358e70689c"

    context = json.loads(git_blob(CONTEXT_COMMIT, CONTEXT_FILES[1]))
    assert context["context"]["o200k_base_tokens"] == 176
    assert context["corpus_selected_before_freeze"] is False
    forbidden = (
        "fullstack_agent_047_tasks.json",
        "fullstack_agent_047_cases.json",
        "fullstack_agent_047_protocol.json",
        "fullstack_agent_047_scaffolds.py",
        "fullstack_agent_047_logic.py",
        "fullstack_agent_047_raw.json",
        "fullstack_agent_047_audit.json",
    )
    frozen_paths = set(
        str(git("ls-tree", "-r", "--name-only", CONTEXT_COMMIT)).splitlines()
    )
    assert not any(f"benchmarks/{name}" in frozen_paths for name in forbidden)

    return {
        "schema_version": 1,
        "experiment_id": "047",
        "phase": "pre-corpus product and evidence freeze",
        "frozen_on": "2026-08-13",
        "parley": {
            "version": "0.5.7",
            "product_commit": PRODUCT_COMMIT,
            "product_tree": PRODUCT_TREE,
            "accepted_product_gate": "21 dedicated and 727 complete tests passed",
            "wheel_sha256": "553bfb8ffe003edb9e38d057c6617f7f9abbb634bdb1838a4402c18776daa7e1",
        },
        "context": {
            "commit": CONTEXT_COMMIT,
            "tree": CONTEXT_TREE,
            "bytes": context["context"]["bytes"],
            "o200k_base_tokens": context["context"]["o200k_base_tokens"],
            "maximum_tokens": context["maximum_o200k_base_tokens"],
        },
        "files": {
            "product": product_digests,
            "context": context_digests,
            "evidence": {EVIDENCE_FILE: evidence_digest},
        },
        "evidence_boundary": {
            "json_native_header_pairs": True,
            "non_finite_json_rejected": True,
            "route_path_and_path_parameters_must_match_live_and_persisted_evidence": True,
        },
        "previous_study_boundary": {
            "experiment_id": "046",
            "result_commit": PREVIOUS_RESULT_COMMIT,
            "result_tree": PREVIOUS_RESULT_TREE,
            "status": "valid; strict gate failed on elapsed time",
            "selective_rerun": False,
            "same_corpus_reuse": False,
            "files": previous_digests,
        },
        "pre_corpus_anchor_commit": CONTEXT_COMMIT,
        "corpus_selected_before_freeze": False,
        "measured_sessions_before_freeze": 0,
        "next_step": (
            "Select and freeze new path-routing task semantics disjoint from all "
            "previous measured corpora before building scaffolds or prompts."
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
    result = build()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
