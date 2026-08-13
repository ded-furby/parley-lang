#!/usr/bin/env python3
"""Build the deterministic pre-corpus Parley v0.5.4 freeze for iteration 043."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO / "benchmarks/fullstack_agent_043_product.json"
EVIDENCE_COMMIT = "bf0f85aa33dbd6d52c17260d85a04155d11518c2"
EVIDENCE_TREE = "9f3149e3f742167982e8c48212ac26830870e4bb"
PRODUCT_FILES = (
    "parley/web.py",
    "parley/cli.py",
    "parley/__init__.py",
    "pyproject.toml",
)
CONTEXT = "skill/parley/references/scaffolded-web-v0.5.3.md"
BUILD_BASELINE = "benchmarks/web_build_latency_001_baseline.json"
BUILD_CANDIDATE = "benchmarks/web_build_latency_001_candidate.json"
BUILD_ANALYSIS = "benchmarks/web_build_latency_001_analysis.json"


def git_blob(relative: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{EVIDENCE_COMMIT}:{relative}"],
        cwd=REPO,
        capture_output=True,
        check=True,
    )
    return completed.stdout


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build() -> dict[str, object]:
    tree = subprocess.run(
        ["git", "rev-parse", f"{EVIDENCE_COMMIT}^{{tree}}"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert tree == EVIDENCE_TREE
    init = git_blob("parley/__init__.py").decode()
    package = git_blob("pyproject.toml").decode()
    assert '__version__ = "0.5.4"' in init
    assert 'version = "0.5.4"' in package
    context = git_blob(CONTEXT)
    analysis_blob = git_blob(BUILD_ANALYSIS)
    analysis = json.loads(analysis_blob)
    assert analysis["acceptance"]["accepted"] is True
    assert analysis["overall"]["latency_improvement_percent"] == 31.5904
    assert analysis["verification"]["regression_tests_passed"] == 585
    return {
        "schema_version": 1,
        "experiment_id": "043-product-freeze",
        "frozen_on": "2026-08-13",
        "parley_version": "0.5.4",
        "evidence_commit": EVIDENCE_COMMIT,
        "evidence_tree": EVIDENCE_TREE,
        "product_files": {
            relative: sha256(git_blob(relative)) for relative in PRODUCT_FILES
        },
        "agent_context": {
            "file": CONTEXT,
            "sha256": sha256(context),
            "bytes": len(context),
            "o200k_base_tokens": 222,
            "status": "unchanged from the independently token-winning 042 freeze",
        },
        "build_evidence": {
            "baseline_file": BUILD_BASELINE,
            "baseline_sha256": sha256(git_blob(BUILD_BASELINE)),
            "candidate_file": BUILD_CANDIDATE,
            "candidate_sha256": sha256(git_blob(BUILD_CANDIDATE)),
            "analysis_file": BUILD_ANALYSIS,
            "analysis_sha256": sha256(analysis_blob),
            "baseline_median_seconds": analysis["overall"][
                "baseline_median_of_fixture_medians_seconds"
            ],
            "candidate_median_seconds": analysis["overall"][
                "candidate_median_of_fixture_medians_seconds"
            ],
            "improvement_percent": analysis["overall"][
                "latency_improvement_percent"
            ],
            "regression_tests_passed": analysis["verification"][
                "regression_tests_passed"
            ],
            "accepted": analysis["acceptance"]["accepted"],
        },
        "frozen_decisions": [
            "keep the 222-token scaffold-aware context unchanged",
            "use manual strict Serde traits at ordinary typed route boundaries",
            "retain Serde derives for programs with explicit from-json or as-json expressions",
            "preserve strict unknown, duplicate, missing, wrong-type, optional, and enum behavior",
            "preserve the six-condition all-strata gate and once-run execution controls",
        ],
        "construction_boundary": (
            "This v0.5.4 product and its evidence commit are frozen before any "
            "iteration-043 task names, domains, routes, fields, formulas, fixtures, "
            "defects, scaffolds, thresholds, prompts, or model output are selected."
        ),
        "claim_boundary": (
            "The 31.5904% result is a local cold-build product benchmark. It does "
            "not change iteration 042 or establish future agent reliability, strict "
            "efficiency parity, production suitability, or universal superiority."
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
