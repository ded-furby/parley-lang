#!/usr/bin/env python3
"""Build the revision-1 preregistration for full-stack study 044."""

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
    protocol["protocol_revision"] = 1
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
    protocol.pop("execution_freeze", None)
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
