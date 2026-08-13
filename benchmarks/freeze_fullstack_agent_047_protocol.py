#!/usr/bin/env python3
"""Build revision 1 of the preregistered full-stack study-047 protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
TEMPLATE = BENCHMARKS / "fullstack_agent_046_protocol.json"
DEFAULT_OUTPUT = BENCHMARKS / "fullstack_agent_047_protocol.json"


def sha256(relative: str) -> str:
    return hashlib.sha256((REPO / relative).read_bytes()).hexdigest()


def build() -> dict:
    protocol = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    protocol["protocol_revision"] = 1
    protocol["experiment_id"] = "047"
    protocol["title"] = "Independent compact-context typed path-routing pilot"
    protocol["description"] = (
        "A frozen 32-session comparison of four unseen exact/parameterized routing "
        "and browser assignments in Parley, Python, TypeScript, and Rust, using the "
        "pre-corpus 176-token Parley v0.5.7 path-response card."
    )
    protocol["frozen_product"] = {
        "parley_version": "parley 0.5.7",
        "product_commit": "c9e8c9bea770c9243ac244663c28209bb18264df",
        "product_tree": "c749b23a61ec360cd4ad33d5fd93dc700a278927",
        "product_boundary_commit": "f1959a5247db7444c161340110ec1782faa3d2b7",
        "corpus_commit": "32017e311379d007481c7c52a06f652a76830aea",
        "corpus_tree": "135a7735e726403b140e3dfed0f9945d2ff1851b",
        "tasks_file": "benchmarks/fullstack_agent_047_tasks.json",
        "tasks_sha256": sha256("benchmarks/fullstack_agent_047_tasks.json"),
        "cases_file": "benchmarks/fullstack_agent_047_cases.json",
        "cases_sha256": sha256("benchmarks/fullstack_agent_047_cases.json"),
        "parley_context_file": (
            "skill/parley/references/scaffolded-path-response-web-v0.5.7-compact.md"
        ),
        "parley_context_sha256": sha256(
            "skill/parley/references/scaffolded-path-response-web-v0.5.7-compact.md"
        ),
        "parley_context_bytes": 760,
        "parley_context_o200k_tokens": 176,
        "context_freeze_file": "benchmarks/fullstack_agent_047_context.json",
        "context_freeze_sha256": sha256("benchmarks/fullstack_agent_047_context.json"),
        "product_freeze_file": "benchmarks/fullstack_agent_047_product.json",
        "product_freeze_sha256": sha256("benchmarks/fullstack_agent_047_product.json"),
        "json_evidence_file": "benchmarks/json_evidence.py",
        "json_evidence_sha256": sha256("benchmarks/json_evidence.py"),
        "path_protocol_file": "benchmarks/WEB_PATH_PARAMETERS_004.md",
        "path_protocol_sha256": sha256("benchmarks/WEB_PATH_PARAMETERS_004.md"),
        "path_result_file": "benchmarks/WEB_PATH_PARAMETERS_004_RESULT.md",
        "path_result_sha256": sha256("benchmarks/WEB_PATH_PARAMETERS_004_RESULT.md"),
        "frozen_path_parameter_tests": 21,
        "frozen_full_regression_tests": 727,
    }
    protocol["frozen_config"] = {
        "languages": ["parley", "python", "typescript", "rust"],
        "agent_configurations": [
            {"id": "sol-medium", "model": "gpt-5.6-sol", "reasoning": "medium"}
        ],
        "replicates_per_task_language_configuration": 2,
        "seed": 470260813,
        "timeout_seconds": 900,
        "max_workers": 4,
        "max_public_check_attempts": 8,
        "fresh_session_per_cell": True,
        "public_check_command": "./check",
        "source_command": "./sources",
        "source_command_count": 1,
        "internet": "disabled",
        "selective_reruns": "forbidden",
    }
    protocol["matrix"] = {
        "tasks": 4,
        "implementation_tasks": 2,
        "maintenance_tasks": 2,
        "languages": 4,
        "agent_configurations": 1,
        "replicates": 2,
        "fresh_sessions": 32,
        "sessions_per_language": 8,
        "sessions_per_task_kind_and_language": 4,
        "public_cases_per_assignment": 5,
        "public_http_cases_per_assignment": 4,
        "public_browser_cases_per_assignment": 1,
        "hidden_cases_per_assignment": 5,
        "hidden_http_cases_per_assignment": 3,
        "hidden_browser_cases_per_assignment": 2,
        "frozen_public_case_executions_across_first_checks": 160,
        "hidden_case_executions": 160,
        "derivation": "4 tasks x 4 languages x 1 agent configuration x 2 replicates",
    }
    protocol["language_stacks"]["parley"] = {
        "version": "0.5.7",
        "stack": (
            "Generated native HTTP/JSON server with checked whole-segment path "
            "parameters, dynamic response envelopes, and generated browser WebAssembly"
        ),
        "agent_context": (
            "Frozen 176-token v0.5.7 compact path-response card used alone and included "
            "in measured input tokens."
        ),
    }
    protocol["scaffold_protocol"]["editable"] = (
        "Task-specific route handlers, response records, browser score modules, and "
        "application manifests required by each language."
    )
    protocol["scaffold_protocol"]["reference_validation"] = (
        "Before measurement, isolated reference applications for all 16 task/language "
        "pairs must run the exact measured builds under post-command hash checks and "
        "pass all 160 named public/hidden HTTP path/status/JSON/header and browser cases. "
        "Every maintenance seed must build, fail its public parameterized case, and pass "
        "after changing only the predeclared route-handler root file."
    )
    protocol["scaffold_protocol"]["rust_lockfile"] = (
        "Generate Cargo.lock canonically from the final study-047 manifest. Run native "
        "and wasm32 release builds locked and offline under immediate post-command hash "
        "checks, then preserve the reviewed lock hash in every Rust workspace."
    )
    protocol["session_protocol"]["runner"] = (
        "A new iteration-047 runner creates one isolated workspace, external attempt "
        "directory, immutable journal entry, and fresh ephemeral Codex thread per cell."
    )
    protocol["session_protocol"]["command_policy"] = (
        "The first shell command must be exactly ./sources and occur once. Every later "
        "shell command must be exactly ./check. At least one and at most eight ./check "
        "commands are permitted."
    )
    protocol["session_protocol"]["public_feedback"] = (
        "Each ./check request is evaluated by the parent and records build output plus "
        "all public HTTP path/status/JSON/custom-header and real-Chromium verdicts, then "
        "returns only bounded public feedback."
    )
    protocol["session_protocol"]["public_execution_requirement"] = (
        "Every completed public attempt must execute all five public cases, including "
        "four HTTP cases and the browser case. A build failure may short-circuit cases "
        "but remains a failed attempt; zero semantic execution cannot pass."
    )
    protocol["session_protocol"]["hidden_judgment"] = (
        "After the agent exits, the parent separately rebuilds and executes all withheld "
        "HTTP path/status/JSON/custom-header and browser cases. Hidden inputs and values "
        "never enter the workspace or public transport."
    )
    protocol["session_protocol"]["domain_judgment"] = (
        "The parent sends frozen raw paths without pre-decoding or validating captured "
        "segments. Routing, exact priority, once-decoding, safety rejection, authorization, "
        "and positive-decimal validation are application-stack responsibilities."
    )
    protocol["execution_freeze"] = {
        "status": "pending post-protocol harness implementation",
        "measured_sessions_before_freeze": 0,
        "required_revision": 2,
        "requirements": [
            "bind every new and transitive execution file by SHA-256",
            "validate 16 task/language reference applications in clean rooms",
            "validate all 160 named public/hidden cases including decoded captures",
            "prove all eight language-specific maintenance roots with built negative controls",
            "calibrate peak workspace use within the frozen scratch allowance",
            "pass parent-owned FIFO, HTTP, header, malformed-path, and Chromium smoke",
            "prove live-to-persisted JSON equality for paths, path parameters, and headers",
        ],
        "prohibition": (
            "No measured session may start until revision 2 is committed with zero "
            "measured sessions and every requirement passing."
        ),
    }
    protocol["metrics"]["correctness"] = (
        "Exact hidden HTTP route/status/JSON/error/custom-header and real-browser results, "
        "overall and by task, kind, language, and replicate."
    )
    protocol["metrics"]["first_check"] = (
        "Whether the first parent-owned public build and all five public cases pass, with "
        "HTTP and browser execution counts retained."
    )
    protocol["metrics"]["cross_target"] = (
        "Valid decoded path integer/browser equality for the shared score plus successful "
        "Chromium execution; routing, invalid-path, authorization, and header branches "
        "remain separately exact."
    )
    protocol["primary_gate"] = {
        "execution_integrity": (
            "All 32 cells must finish exactly once with unique thread IDs, one journal "
            "start/finish, compliant commands, durable evidence, intact protected inputs, "
            "required HTTP/browser execution, and no runner, scratch, or cleanup error."
        ),
        "correctness": (
            "Parley must pass 100% of hidden HTTP and browser cases, and its assignment "
            "success rate must be no lower than every baseline overall and within both "
            "implementation and maintenance tasks."
        ),
        "first_check": (
            "Parley's first-public-check assignment success rate must be no lower than "
            "the highest baseline rate overall and within each task kind."
        ),
        "tokens": (
            "Parley's median complete input-plus-output tokens per assignment must be no "
            "higher than the lowest baseline median overall."
        ),
        "elapsed": (
            "Parley's median complete-session elapsed seconds must be no higher than the "
            "lowest baseline median overall."
        ),
        "maintainability": (
            "Every hidden-correct Parley maintenance assignment must change exactly its "
            "predeclared root file set, and its exact-root rate must be no lower than every "
            "baseline."
        ),
        "verdict": (
            "All six conditions must hold for strict unseen path-routing agent parity and "
            "efficiency. Report every condition independently when the gate fails."
        ),
    }
    protocol["secondary_analysis"] = [
        "Report complete distributions and paired task/replicate cells; never replace the primary result with a successful or repair-free subset.",
        "Report implementation and maintenance separately, including exact repair-root quality and public/hidden disagreement classes.",
        "Report public-attempt and semantic case counts so build-only feedback cannot appear as a passing check.",
        "Report frozen context, manifest, scaffold, final-source, and complete-session token counts without substituting source size for session cost.",
        "Compare study 046 only as mechanism history; never pool its tasks, tokens, or timing with study 047.",
        "Treat two replicates as pilot evidence: show paired observations and avoid population-level certainty claims.",
    ]
    protocol["interpretation_boundary"] = [
        "The study covers four small synthetic path-routing plus browser contracts, one model ID, one reasoning setting, two replicates, and one frozen toolchain environment.",
        "Scaffolds test application work, not dependency discovery, deployment, load, databases, accessibility, or production operations.",
        "Header comparisons test deterministic request decisions, not general identity or policy-system security.",
        "A deterministic scalar export in real Chromium is a cross-target check, not a general user-interface evaluation.",
        "Synthetic route-handler defects cover only the declared capture-use failures and do not estimate production-defect distributions.",
        "Even a fully passing gate cannot prove universal language superiority; it supports only the frozen comparative claim.",
        "A failed strict gate cannot be repaired by same-corpus language, context, prompt, task, runner, threshold, or metric tuning.",
    ]
    protocol["implementation_rule"] = (
        "Corpus semantics were frozen before this revision. Scaffold generation, "
        "dependency preparation, clean-room validation, orchestration evidence, and every "
        "transitive execution hash must be committed in revision 2 before measurement."
    )
    protocol["change_rule"] = (
        "Task semantics have been immutable since corpus commit "
        "32017e311379d007481c7c52a06f652a76830aea. From revision 1 onward, no context, "
        "metric, threshold, model, reasoning setting, replicate count, or primary gate may "
        "change based on validation or output. An objective harness defect may be corrected "
        "only before measurement in a documented zero-session amendment preserving semantic "
        "hashes. Scratch budgets may increase but not decrease."
    )
    protocol["stop_rule"] = (
        "Run every frozen cell once and publish the complete positive, mixed, negative, or "
        "invalid result without same-corpus optimization or rerun. Any later product change "
        "requires a corpus outside iteration 047."
    )
    return protocol


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
