#!/usr/bin/env python3
"""Build the revision-2 execution freeze for full-stack study 044."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TEMPLATE = BENCHMARKS / "fullstack_agent_042_protocol.json"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_044_protocol.json"
def sha256(relative: str) -> str:
    return hashlib.sha256((REPO / relative).read_bytes()).hexdigest()


def build() -> dict:
    protocol = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    protocol["protocol_revision"] = 2
    protocol["experiment_id"] = "044"
    protocol["title"] = "Independent dependency-free-build full-stack implementation and maintenance study"
    protocol["description"] = (
        "A preregistered 96-session comparison of four unseen server-plus-browser "
        "assignments in Parley, Python, TypeScript, and Rust using parent-owned "
        "public evaluation and exact-build read-only validation."
    )
    protocol["frozen_product"] = {
        "parley_version": "parley 0.5.5",
        "product_commit": "a098996847927c4eb622e2af8d0b7ebee81011c6",
        "product_tree": "be8be51158157fc33b6b0e00e5ce62e6478d94fe",
        "corpus_commit": "cef46dcdf70183e2c64e235bf9699184ba166eb5",
        "corpus_tree": "1e576531260707d4ffc1efed3f0f72d092bd8e03",
        "tasks_file": "benchmarks/fullstack_agent_044_tasks.json",
        "tasks_sha256": sha256("benchmarks/fullstack_agent_044_tasks.json"),
        "cases_file": "benchmarks/fullstack_agent_044_cases.json",
        "cases_sha256": sha256("benchmarks/fullstack_agent_044_cases.json"),
        "parley_context_file": "skill/parley/references/scaffolded-web-v0.5.3.md",
        "parley_context_sha256": sha256("skill/parley/references/scaffolded-web-v0.5.3.md"),
        "parley_context_bytes": 892,
        "parley_context_o200k_tokens": 222,
        "product_freeze_file": "benchmarks/fullstack_agent_044_product.json",
        "product_freeze_sha256": sha256("benchmarks/fullstack_agent_044_product.json"),
        "build_analysis_file": "benchmarks/web_build_latency_002_analysis.json",
        "build_analysis_sha256": sha256("benchmarks/web_build_latency_002_analysis.json"),
        "frozen_build_improvement_percent": 70.5496,
    }
    protocol["frozen_config"]["seed"] = 440260813
    protocol["language_stacks"]["parley"] = {
        "version": "0.5.5",
        "stack": "Generated native HTTP/JSON server with dependency-free strict typed-route codecs and generated browser WebAssembly bindings",
        "agent_context": "Frozen 222-token v0.5.3 scaffold-aware card used alone and included in measured input tokens.",
    }
    protocol["scaffold_protocol"]["rust_lockfile"] = (
        "Generate Cargo.lock canonically from the final fullstack-agent-044 "
        "manifest. Run cargo build --locked --offline --release and the exact "
        "wasm32 release build under immediate post-command hash checks before "
        "the execution freeze, and preserve that reviewed hash in every measured workspace."
    )
    protocol["session_protocol"]["runner"] = (
        "A new iteration-044 runner creates one isolated workspace, one external "
        "attempt directory, one immutable journal entry, and one ephemeral Codex "
        "thread per cell; it must not modify historical runners."
    )
    execution_files = [
        "benchmarks/run_fullstack_agent_044.py",
        "benchmarks/fullstack_agent_044_scaffolds.py",
        "benchmarks/fullstack_agent_044_logic.py",
        "benchmarks/fullstack_agent_044_guard.py",
        "benchmarks/prepare_fullstack_agent_044.py",
        "benchmarks/agent_check_transport.py",
        "benchmarks/agent_runner.py",
        "benchmarks/exact_build_freeze.py",
        "benchmarks/scratch_space.py",
        "benchmarks/fullstack_agent_036_scaffolds.py",
        "benchmarks/fullstack_044/rust/Cargo.toml",
        "benchmarks/fullstack_044/rust/Cargo.lock",
        "benchmarks/fullstack_044/rust/src/lib.rs",
        "benchmarks/fullstack_035/python/requirements.txt",
        "benchmarks/fullstack_035/python/requirements.lock.txt",
        "benchmarks/fullstack_035/typescript/package.json",
        "benchmarks/fullstack_035/typescript/package-lock.json",
        "benchmarks/fullstack_035/typescript/tsconfig.json",
        "benchmarks/FULLSTACK_AGENT_044_EXECUTION_FREEZE.md",
    ]
    protocol["execution_freeze"] = {
        "description": (
            "Post-protocol harness, scratch lifecycle, v0.5.5 compact-context "
            "integration, and exact-build execution-integrity controls frozen "
            "before the first measured cell; task, case, model, metric, threshold, "
            "gate, compiler, context, and stack semantics are unchanged."
        ),
        "measured_sessions_before_freeze": 0,
        "harness_commit": "b1690b5719830647a1ed3850956967c8455cde77",
        "calibrated_max_workspace_bytes": 161_169_608,
        "calibrated_per_worker_headroom_multiple": 13.324,
        "parley_prompt_delta_vs_python_o200k_tokens": 207,
        "files": [
            {"file": relative, "sha256": sha256(relative)}
            for relative in execution_files
        ],
        "provenance_schema": 1,
        "journal_attempts_per_cell": 1,
        "public_attempt_storage": (
            "Atomic JSON files outside the agent workspace, revalidated during "
            "cell finalization and result aggregation."
        ),
        "scratch_preflight": (
            "17,179,869,184 bytes free required before journal initialization and "
            "every scheduling refill with work/journal/attempt roots proven "
            "disjoint; observed capacity is evidence rather than resume identity."
        ),
        "workspace_cleanup": (
            "A separate immutable cleanup record is written only after the complete "
            "finished journal; it retains pre-cleanup workspace bytes and proves "
            "removal, absence, or a permanent cleanup failure."
        ),
        "bounded_scheduler": (
            "At most four cells are active and no later cell is queued; a run-level "
            "capacity or cleanup failure stops refills and permanently journals all "
            "unstarted cells as failed without creating agent sessions."
        ),
        "numeric_domain_guard": (
            "Identical parent-owned proxy for all languages; rejects only negative "
            "numeric values before forwarding other traffic."
        ),
        "exact_build_integrity": (
            "Every protected/read-only file is checked before and immediately after "
            "each exact build command; any mutation fails the build and cell."
        ),
        "resume_policy": (
            "A started cell without a finished record becomes a permanent "
            "interruption failure; finished evidence is reconciled with cleanup "
            "evidence; only never-started cells may execute."
        ),
    }
    protocol["secondary_analysis"][-2] = (
        "Compare studies 036–043 only as motivation and mechanism history. Do "
        "not combine their task results, tokens, or timing with 044."
    )
    protocol["implementation_rule"] = (
        "Scaffolds, reference applications, dependency preparation, and the "
        "runner are implemented only after this protocol commit. Their exact "
        "hashes and clean-room reference evidence must be committed in a final "
        "pre-measurement execution freeze. No measured session may start before "
        "that checkpoint."
    )
    protocol["change_rule"] = (
        "From corpus commit cef46dcdf70183e2c64e235bf9699184ba166eb5 onward, "
        "no task, case, expected value, language semantics, compiler, context, "
        "metric, threshold, model, reasoning setting, replicate count, or primary "
        "gate may change based on scaffolds, reference code, validation, smoke "
        "checks, or measured output. An objective harness defect may be corrected "
        "only before measured execution in a documented zero-session amendment "
        "preserving old commits and semantic hashes. Scratch calibration may only "
        "increase the preregistered budget before the first measured session."
    )
    protocol["stop_rule"] = (
        "Run every frozen cell once, preserve and publish the complete result "
        "whether positive, mixed, negative, or invalid, and make no same-corpus "
        "optimization or rerun. Any later language or product change requires an "
        "independently frozen corpus outside iteration 044."
    )
    return protocol


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
