#!/usr/bin/env python3
"""Build the preregistered protocol for full-stack study 045."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TEMPLATE = BENCHMARKS / "fullstack_agent_044_protocol.json"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_045_protocol.json"


def sha256(relative: str) -> str:
    return hashlib.sha256((REPO / relative).read_bytes()).hexdigest()


def build() -> dict:
    protocol = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    protocol["protocol_revision"] = 1
    protocol["experiment_id"] = "045"
    protocol["title"] = (
        "Independent typed response-control implementation and maintenance study"
    )
    protocol["description"] = (
        "A preregistered 96-session comparison of four unseen authenticated, "
        "validated, conflict-aware, or creation-oriented server-plus-browser "
        "assignments in Parley, Python, TypeScript, and Rust."
    )
    protocol["frozen_product"] = {
        "parley_version": "parley 0.5.6",
        "product_commit": "6bae1149d101d5a483f31f55905083e0a939c1da",
        "product_tree": "525b23b0191cb5f16a9cc4b5281d9b9af912898c",
        "corpus_commit": "3f3a5943532cd63a151ec8221715f75ab352a931",
        "corpus_tree": "faeb773d4a867abcbab47bc5468f2e20293b09e1",
        "tasks_file": "benchmarks/fullstack_agent_045_tasks.json",
        "tasks_sha256": sha256("benchmarks/fullstack_agent_045_tasks.json"),
        "cases_file": "benchmarks/fullstack_agent_045_cases.json",
        "cases_sha256": sha256("benchmarks/fullstack_agent_045_cases.json"),
        "parley_context_file": (
            "skill/parley/references/scaffolded-response-web-v0.5.6.md"
        ),
        "parley_context_sha256": sha256(
            "skill/parley/references/scaffolded-response-web-v0.5.6.md"
        ),
        "parley_context_bytes": 1281,
        "parley_context_o200k_tokens": 313,
        "context_freeze_file": "benchmarks/fullstack_agent_045_context.json",
        "context_freeze_sha256": sha256(
            "benchmarks/fullstack_agent_045_context.json"
        ),
        "product_freeze_file": "benchmarks/fullstack_agent_045_product.json",
        "product_freeze_sha256": sha256(
            "benchmarks/fullstack_agent_045_product.json"
        ),
        "response_protocol_file": "benchmarks/WEB_RESPONSE_CONTROL_003.md",
        "response_protocol_sha256": sha256(
            "benchmarks/WEB_RESPONSE_CONTROL_003.md"
        ),
        "frozen_response_control_tests": 14,
        "frozen_full_regression_tests": 643,
    }
    protocol["frozen_config"]["seed"] = 450260813
    protocol["language_stacks"]["parley"] = {
        "version": "0.5.6",
        "stack": (
            "Generated native HTTP/JSON server with checked dynamic response "
            "envelopes, dependency-free strict route codecs, and generated browser "
            "WebAssembly bindings"
        ),
        "agent_context": (
            "Frozen 313-token v0.5.6 scaffolded response-web card used alone and "
            "included in measured input tokens."
        ),
    }
    protocol["scaffold_protocol"]["editable"] = (
        "All task-specific application logic, typed request/body/response envelope "
        "declarations, authorization/validation/conflict handlers, browser rule "
        "modules, and application manifests required by that language."
    )
    protocol["scaffold_protocol"]["reference_validation"] = (
        "Before any agent session, an isolated reference application for every "
        "task/language must run the exact measured build commands under post-command "
        "hash checks, preserve all protected/read-only inputs, and pass every public "
        "and hidden HTTP status/JSON/custom-header plus browser case. Seeded maintenance "
        "applications must build with stable hashes, fail their public response-control "
        "case, and pass after changing only the predeclared route-handler root file."
    )
    protocol["scaffold_protocol"]["rust_lockfile"] = (
        "Generate Cargo.lock canonically from the final fullstack-agent-045 manifest. "
        "Run cargo build --locked --offline --release and the exact wasm32 release "
        "build under immediate post-command hash checks before execution freeze, and "
        "preserve that reviewed hash in every measured workspace."
    )
    protocol["session_protocol"]["runner"] = (
        "A new iteration-045 runner creates one isolated workspace, one external "
        "attempt directory, one immutable journal entry, and one ephemeral Codex "
        "thread per cell; it must not modify historical runners."
    )
    protocol["session_protocol"]["public_feedback"] = (
        "Each ./check request is evaluated by the parent outside the sandbox. It "
        "records build output and exact public HTTP status/JSON/custom-header plus "
        "real-Chromium verdicts, then returns only bounded public feedback."
    )
    protocol["session_protocol"]["hidden_judgment"] = (
        "After the agent exits, the parent separately rebuilds final source and "
        "executes all withheld HTTP status/JSON/custom-header and browser cases. "
        "Hidden inputs and values never enter the workspace or public transport."
    )
    protocol["session_protocol"]["domain_judgment"] = (
        "The parent validates JSON syntax and declared JSON types but does not "
        "pre-reject negative integers or zero-capacity combinations. Those typed "
        "values must reach every language handler and receive the frozen 422 envelope."
    )
    protocol["execution_freeze"] = {
        "status": "pending post-protocol harness implementation",
        "measured_sessions_before_freeze": 0,
        "required_revision": 2,
        "requirements": [
            "bind every new and transitive execution file by SHA-256",
            "validate 16 task/language reference applications in clean rooms",
            "validate all 144 named public/hidden cases including exact custom headers",
            "prove both route-handler maintenance roots with built negative controls",
            "calibrate peak workspace use within the frozen scratch allowance",
            "pass parent-owned FIFO, HTTP, custom-header, and Chromium orchestration smoke",
        ],
        "prohibition": (
            "No measured session may start until revision 2 is committed with zero "
            "measured sessions and all requirements passing."
        ),
    }
    protocol["metrics"]["correctness"] = (
        "Exact hidden HTTP status/JSON/error/custom application headers and real-browser "
        "scalar results, overall and by task, kind, language, model, and replicate."
    )
    protocol["metrics"]["cross_target"] = (
        "Authorized/domain-valid HTTP/browser equality for the shared scalar plus "
        "successful Chromium execution; status/header branches remain separately exact."
    )
    protocol["primary_gate"]["correctness"] = (
        "Parley must pass 100% of hidden HTTP status/JSON/custom-header and browser "
        "cases, and its assignment success rate must be no lower than every baseline "
        "overall, within each agent configuration, and within implementation and "
        "maintenance tasks."
    )
    protocol["secondary_analysis"][-2] = (
        "Compare studies 036–044 only as motivation and mechanism history. Do not "
        "combine their task results, tokens, or timing with 045."
    )
    protocol["interpretation_boundary"] = [
        "The study covers four small synthetic response-control plus browser contracts, two model IDs, one reasoning setting, and one frozen toolchain environment.",
        "Stack scaffolds test application work, not framework discovery, dependency selection, deployment, sustained load, databases, accessibility, or production operations.",
        "Bearer/API-key comparisons test typed authorization decisions and headers, not identity-provider, credential-storage, cryptographic, session, or policy-system security.",
        "Framework source and compiler implementations are infrastructure. Application-facing context is preserved, while complete session tokens remain primary cost.",
        "A deterministic scalar ES-module export in real Chromium is a cross-target check, not a general user-interface evaluation.",
        "Synthetic route-handler defects measure only the declared boundary behaviors and do not estimate production-defect distributions.",
        "Even a fully passing gate cannot prove universal language superiority; it supports only the frozen comparative claim.",
        "A failed strict gate remains useful evidence and cannot be repaired by same-corpus language, context, prompt, task, runner, threshold, or metric tuning.",
    ]
    protocol["implementation_rule"] = (
        "Scaffolds, reference applications, dependency preparation, and the runner "
        "are implemented only after this protocol commit. Their exact hashes and "
        "clean-room evidence must be committed in revision 2 before measurement."
    )
    protocol["change_rule"] = (
        "From corpus commit 3f3a5943532cd63a151ec8221715f75ab352a931 onward, "
        "no task, case, expected value/status/header, language semantics, compiler, "
        "context, metric, threshold, model, reasoning setting, replicate count, or "
        "primary gate may change based on scaffolds, reference validation, smoke "
        "checks, or measured output. An objective harness defect may be corrected "
        "only before measurement in a documented zero-session amendment preserving "
        "old commits and semantic hashes. Scratch budgets may increase but not decrease."
    )
    protocol["stop_rule"] = (
        "Run every frozen cell once, preserve and publish the complete result whether "
        "positive, mixed, negative, or invalid, and make no same-corpus optimization "
        "or rerun. Any later product change requires a corpus outside iteration 045."
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
