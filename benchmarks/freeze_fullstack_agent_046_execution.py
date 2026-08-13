#!/usr/bin/env python3
"""Build protocol revision 2 from frozen revision 1 and validated inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .freeze_fullstack_agent_046_protocol import build as build_revision_1
except ImportError:
    from freeze_fullstack_agent_046_protocol import build as build_revision_1


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_046_protocol.json"
REVISION_1_COMMIT = "47448a84b3663ff2aef1d17cf92cca26bc4d7891"
REVISION_1_SHA256 = "e283312020be0d0efb7784abf11be0215cc67ca3938c7295e3dc8e06223d0265"
HARNESS_COMMIT = "3f716d448cd5f64f0ce008d03a5a27e24eef1f63"
HARNESS_TREE = "4fa77808aeaa2f33f2e35307c0ce0653ba135efe"
EXECUTION_FILES = (
    "benchmarks/run_fullstack_agent_046.py",
    "benchmarks/fullstack_agent_046_scaffolds.py",
    "benchmarks/fullstack_agent_046_logic.py",
    "benchmarks/fullstack_agent_046_guard.py",
    "benchmarks/prepare_fullstack_agent_046.py",
    "benchmarks/smoke_fullstack_agent_046.py",
    "benchmarks/json_evidence.py",
    "benchmarks/agent_check_transport.py",
    "benchmarks/agent_runner.py",
    "benchmarks/exact_build_freeze.py",
    "benchmarks/scratch_space.py",
    "benchmarks/fullstack_046/rust/Cargo.toml",
    "benchmarks/fullstack_046/rust/Cargo.lock",
    "benchmarks/fullstack_046/rust/src/lib.rs",
    "benchmarks/fullstack_035/python/requirements.txt",
    "benchmarks/fullstack_035/python/requirements.lock.txt",
    "benchmarks/fullstack_035/typescript/package.json",
    "benchmarks/fullstack_035/typescript/package-lock.json",
    "benchmarks/fullstack_035/typescript/tsconfig.json",
    "skill/parley/references/scaffolded-response-web-v0.5.6-compact.md",
    "benchmarks/FULLSTACK_AGENT_046_EXECUTION_FREEZE.md",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict[str, object]:
    protocol = build_revision_1()
    revision_1_bytes = (json.dumps(protocol, indent=2) + "\n").encode()
    assert hashlib.sha256(revision_1_bytes).hexdigest() == REVISION_1_SHA256
    protocol["protocol_revision"] = 2
    protocol["execution_freeze"] = {
        "description": (
            "Validated compact-context response-control harness, JSON-native evidence "
            "boundary, transparent proxy, scratch lifecycle, and exact-build inputs "
            "frozen before the first measured cell; semantic and gate inputs are unchanged."
        ),
        "measured_sessions_before_freeze": 0,
        "protocol_revision_1_commit": REVISION_1_COMMIT,
        "protocol_revision_1_sha256": REVISION_1_SHA256,
        "harness_commit": HARNESS_COMMIT,
        "harness_tree": HARNESS_TREE,
        "calibrated_max_workspace_bytes": 161_226_830,
        "calibrated_per_worker_headroom_multiple": 13.320,
        "parley_context_o200k_tokens": 124,
        "parley_prompt_delta_vs_python_o200k_tokens": 109,
        "parley_manifest_o200k_token_range": [124, 132],
        "reference_cells_passed": 16,
        "seed_cells_built": 16,
        "seed_cells_correct": 0,
        "maintenance_root_boundaries_passed": 8,
        "named_reference_case_executions": 144,
        "json_evidence_controls": {
            "empty_header_pairs_live_to_persisted": True,
            "custom_header_pairs_live_to_persisted": True,
            "duplicate_header_pairs_live_to_persisted": True,
            "broker_attempt_live_to_persisted": True,
            "required_shape": "list[list[str, str]]",
        },
        "files": [
            {"file": relative, "sha256": digest(REPO / relative)}
            for relative in EXECUTION_FILES
        ],
        "provenance_schema": 1,
        "journal_attempts_per_cell": 1,
        "public_attempt_storage": (
            "JSON-native atomic files outside the workspace, reread during cell "
            "finalization and result aggregation."
        ),
        "scratch_preflight": (
            "17,179,869,184 bytes free required before journal initialization and each "
            "scheduling refill, with work/journal/attempt roots proven disjoint."
        ),
        "workspace_cleanup": (
            "Write a separate immutable cleanup record after the complete finished "
            "journal; retain pre-cleanup bytes and removal, absence, or failure status."
        ),
        "bounded_scheduler": (
            "At most four cells active; capacity or cleanup failure stops refills and "
            "permanently journals every unstarted cell as failed without an agent session."
        ),
        "response_proxy": (
            "Identical transparent parent-owned loopback proxy for every language; typed "
            "negative and zero-domain values reach the application handler."
        ),
        "application_header_judgment": (
            "Compare the complete normalized multiset of JSON-native non-server, "
            "non-hop-by-hop response-header pairs; missing, extra, wrong, or duplicate "
            "application headers fail."
        ),
        "exact_build_integrity": (
            "Check every protected/read-only file before and immediately after each exact "
            "build command; any mutation fails the build and cell."
        ),
        "resume_policy": (
            "A started cell without a finished record becomes a permanent interruption "
            "failure; only never-started cells may execute."
        ),
    }
    return protocol


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
