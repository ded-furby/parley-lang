#!/usr/bin/env python3
"""Run fresh paired JSON/TOON comprehension sessions for iteration 034."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = REPO / "benchmarks" / "agent_data_protocol_034.json"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from benchmarks.agent_runner import parse_codex_events, utc_now  # noqa: E402
from parley.agent_data import (  # noqa: E402
    compact_json,
    json_model_equal,
    load_json_file,
    toon_decode,
    toon_encode,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_protocol(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    protocol = json.loads(path.read_text(encoding="utf-8"))
    if protocol.get("schema_version") != 1:
        raise ValueError("agent-data protocol must use schema_version 1")
    config = protocol.get("frozen_config")
    if not isinstance(config, dict):
        raise ValueError("agent-data protocol needs frozen_config")
    required = {
        "tasks_file", "tasks_sha256", "representations", "agent_configs",
        "replicates", "seed", "timeout_seconds", "max_workers",
    }
    missing = required - set(config)
    if missing:
        raise ValueError(f"agent-data protocol is missing: {sorted(missing)}")
    if config["representations"] != ["json", "toon"]:
        raise ValueError("representations must be frozen as json then toon")
    tasks_path = REPO / config["tasks_file"]
    if sha256(tasks_path) != config["tasks_sha256"]:
        raise ValueError("task manifest hash does not match the frozen protocol")
    manifest = json.loads(tasks_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("agent-data tasks must use schema_version 1")
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 5:
        raise ValueError("iteration 034 requires exactly five tasks")
    seen: set[str] = set()
    context_hashes = config.get("context_sha256")
    if not isinstance(context_hashes, dict):
        raise ValueError("agent-data protocol needs frozen context hashes")
    for task in tasks:
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id or task_id in seen:
            raise ValueError(f"invalid or duplicate task id: {task_id!r}")
        seen.add(task_id)
        context_path = (REPO / task["context_path"]).resolve()
        if not context_path.is_relative_to(REPO) or not context_path.is_file():
            raise ValueError(f"{task_id}: context is missing or outside the repository")
        relative_context = context_path.relative_to(REPO).as_posix()
        if context_hashes.get(relative_context) != sha256(context_path):
            raise ValueError(f"{task_id}: context hash does not match the frozen protocol")
        if not isinstance(task.get("question"), str) or not task["question"].strip():
            raise ValueError(f"{task_id}: question must be non-empty text")
        if not isinstance(task.get("answer_schema"), dict):
            raise ValueError(f"{task_id}: answer_schema must be an object")
    configs = config["agent_configs"]
    if not isinstance(configs, list) or len(configs) != 3:
        raise ValueError("iteration 034 requires exactly three agent configs")
    if len({item.get("id") for item in configs}) != 3:
        raise ValueError("agent config ids must be unique")
    for item in configs:
        if not all(isinstance(item.get(key), str) and item[key] for key in ("id", "model", "reasoning")):
            raise ValueError("agent configs need id, model, and reasoning")
    for field in ("replicates", "seed", "timeout_seconds", "max_workers"):
        if not isinstance(config[field], int) or config[field] < 1:
            raise ValueError(f"{field} must be a positive integer")
    return protocol, tasks


def build_contexts(tasks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    contexts = {}
    for task in tasks:
        path = REPO / task["context_path"]
        value, raw = load_json_file(path)
        json_text = compact_json(value)
        toon_text = toon_encode(value)
        decoded = toon_decode(toon_text)
        if not json_model_equal(value, decoded):
            raise ValueError(f"{task['id']}: TOON does not exactly round-trip")
        if len(toon_text) >= len(json_text):
            raise ValueError(f"{task['id']}: frozen TOON context is not character-smaller")
        contexts[task["id"]] = {
            "json": json_text,
            "toon": toon_text,
            "semantic_sha256": hashlib.sha256(raw).hexdigest(),
            "json_sha256": hashlib.sha256(json_text.encode()).hexdigest(),
            "toon_sha256": hashlib.sha256(toon_text.encode()).hexdigest(),
            "json_chars": len(json_text),
            "toon_chars": len(toon_text),
        }
    return contexts


def build_plan(protocol: dict[str, Any], tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    config = protocol["frozen_config"]
    plan = []
    for agent in config["agent_configs"]:
        for replicate in range(1, config["replicates"] + 1):
            for task in tasks:
                for representation in config["representations"]:
                    plan.append({
                        "agent_config": agent,
                        "replicate": replicate,
                        "task": task,
                        "representation": representation,
                    })
    random.Random(config["seed"]).shuffle(plan)
    for sequence, cell in enumerate(plan, 1):
        cell["sequence"] = sequence
    if len(plan) != config.get("sessions"):
        raise ValueError(
            f"frozen matrix declares {config.get('sessions')} sessions but builds {len(plan)}"
        )
    return plan


def response_schema(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {"answer": task["answer_schema"]},
        "required": ["answer"],
        "additionalProperties": False,
    }


def render_prompt(task: dict[str, Any], representation: str, context: str) -> str:
    label = "compact JSON" if representation == "json" else "TOON 4.1"
    fence = "json" if representation == "json" else "toon"
    return f"""Answer one structured-data comprehension task.

Rules:
- Use only the supplied context. It contains everything needed.
- Do not use shell commands, tools, web search, or outside knowledge.
- Return one JSON object with exactly one top-level key named `answer`.
- Preserve requested ordering and exact strings.

Context format: {label}
Task: {task['question']}

Context:
```{fence}
{context}
```
"""


def run_cell(cell: dict[str, Any], contexts: dict[str, dict[str, Any]],
             codex_command: str, timeout: int, work_root: Path) -> dict[str, Any]:
    task = cell["task"]
    agent = cell["agent_config"]
    representation = cell["representation"]
    context = contexts[task["id"]][representation]
    prompt = render_prompt(task, representation, context)
    workdir = Path(tempfile.mkdtemp(
        prefix=f"agent-data-{cell['sequence']:03d}-{task['id']}-{representation}-",
        dir=work_root,
    ))
    schema_path = workdir / "response.schema.json"
    response_path = workdir / "response.json"
    schema_path.write_text(
        json.dumps(response_schema(task), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    command = [
        codex_command, "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
        "--disable", "plugins", "--disable", "apps", "--disable", "browser_use",
        "--disable", "computer_use", "--disable", "multi_agent",
        "--skip-git-repo-check", "-s", "read-only", "-m", agent["model"],
        "-c", f'model_reasoning_effort="{agent["reasoning"]}"',
        "-c", 'approval_policy="never"', "--output-schema", str(schema_path),
        "--output-last-message", str(response_path), "--json", "-C", str(workdir), prompt,
    ]
    started = time.perf_counter()
    timed_out = False
    try:
        proc = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=dict(os.environ),
        )
        returncode, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    elapsed = round(time.perf_counter() - started, 4)
    parsed_events = parse_codex_events(stdout)
    response_text = response_path.read_text(encoding="utf-8") if response_path.is_file() else ""
    response_value = None
    parse_error = None
    try:
        response_value = json.loads(response_text)
    except json.JSONDecodeError as exc:
        parse_error = str(exc)
    answer = response_value.get("answer") if isinstance(response_value, dict) else None
    exact = parse_error is None and answer == task["expected_answer"]
    usage = parsed_events["usage"]
    return {
        "schema_version": 1,
        "recorded_at": utc_now(),
        "sequence": cell["sequence"],
        "task_id": task["id"],
        "task_family": task["family"],
        "representation": representation,
        "replicate": cell["replicate"],
        "agent_config": agent["id"],
        "model": agent["model"],
        "reasoning": agent["reasoning"],
        "fresh_ephemeral_session": True,
        "thread_id": parsed_events["thread_id"],
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": elapsed,
        "parse_success": parse_error is None,
        "parse_error": parse_error,
        "exact_success": exact,
        "expected_answer": task["expected_answer"],
        "actual_answer": answer,
        "response_text": response_text,
        "usage": usage,
        "total_tokens": usage["input_tokens"] + usage["output_tokens"],
        "prompt_chars": len(prompt),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "context_chars": len(context),
        "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
        "semantic_sha256": contexts[task["id"]]["semantic_sha256"],
        "command_count": len(parsed_events["command_events"]),
        "command_events": parsed_events["command_events"],
        "agent_errors": parsed_events["errors"],
        "agent_messages": parsed_events["agent_messages"],
        "codex_stdout": stdout,
        "codex_stderr": stderr,
    }


def aggregate(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    values = sorted({row[field] for row in rows})
    result = []
    for value in values:
        group = [row for row in rows if row[field] == value]
        result.append({
            field: value,
            "sessions": len(group),
            "exact_successes": sum(row["exact_success"] for row in group),
            "parse_successes": sum(row["parse_success"] for row in group),
            "zero_returncodes": sum(row["returncode"] == 0 for row in group),
            "tool_free_sessions": sum(row["command_count"] == 0 for row in group),
            "input_tokens": sum(row["usage"]["input_tokens"] for row in group),
            "cached_input_tokens": sum(row["usage"]["cached_input_tokens"] for row in group),
            "output_tokens": sum(row["usage"]["output_tokens"] for row in group),
            "total_tokens": sum(row["total_tokens"] for row in group),
            "median_total_tokens": statistics.median(row["total_tokens"] for row in group),
            "median_elapsed_seconds": statistics.median(row["elapsed_seconds"] for row in group),
        })
    return result


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_representation = aggregate(rows, "representation")
    reps = {row["representation"]: row for row in by_representation}
    json_row, toon_row = reps["json"], reps["toon"]
    config_detail = []
    for config in sorted({row["agent_config"] for row in rows}):
        for representation in ("json", "toon"):
            group = [
                row for row in rows
                if row["agent_config"] == config and row["representation"] == representation
            ]
            summary = aggregate(group, "representation")[0]
            summary["agent_config"] = config
            config_detail.append(summary)
    pairs = []
    for config in sorted({row["agent_config"] for row in rows}):
        for replicate in sorted({row["replicate"] for row in rows}):
            for task_id in sorted({row["task_id"] for row in rows}):
                pair_rows = [
                    row for row in rows
                    if row["agent_config"] == config
                    and row["replicate"] == replicate
                    and row["task_id"] == task_id
                ]
                if len(pair_rows) != 2:
                    continue
                pair = {row["representation"]: row for row in pair_rows}
                pairs.append({
                    "agent_config": config,
                    "replicate": replicate,
                    "task_id": task_id,
                    "json_correct": pair["json"]["exact_success"],
                    "toon_correct": pair["toon"]["exact_success"],
                    "input_token_delta": pair["toon"]["usage"]["input_tokens"] - pair["json"]["usage"]["input_tokens"],
                    "total_token_delta": pair["toon"]["total_tokens"] - pair["json"]["total_tokens"],
                })
    config_noninferior = True
    for config in sorted({row["agent_config"] for row in rows}):
        cut = {row["representation"]: row for row in config_detail if row["agent_config"] == config}
        config_noninferior = config_noninferior and (
            cut["toon"]["exact_successes"] >= cut["json"]["exact_successes"] - 1
        )
    thread_ids = [row["thread_id"] for row in rows if row["thread_id"]]
    conditions = {
        "execution_integrity": (
            len(rows) == 90
            and len(thread_ids) == 90
            and len(set(thread_ids)) == 90
            and all(row["returncode"] == 0 and not row["timed_out"] for row in rows)
            and all(row["command_count"] == 0 and not row["agent_errors"] for row in rows)
        ),
        "accuracy_noninferior": (
            toon_row["exact_successes"] >= json_row["exact_successes"] - 2
            and config_noninferior
        ),
        "parse_noninferior": toon_row["parse_successes"] >= json_row["parse_successes"],
        "input_tokens_lower": toon_row["input_tokens"] < json_row["input_tokens"],
        "total_tokens_lower": toon_row["total_tokens"] < json_row["total_tokens"],
    }
    return {
        "sessions": len(rows),
        "unique_threads": len(set(thread_ids)),
        "by_representation": by_representation,
        "by_agent_config_and_representation": config_detail,
        "by_task": aggregate(rows, "task_id"),
        "pairs": pairs,
        "gate": {
            "conditions": conditions,
            "passed": all(conditions.values()),
            "conditions_passed": sum(conditions.values()),
            "conditions_total": len(conditions),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--work-root", type=Path, default=Path(tempfile.gettempdir()))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError(f"output already exists: {args.output}")
        protocol, tasks = load_protocol(args.protocol)
        contexts = build_contexts(tasks)
        plan = build_plan(protocol, tasks)
        config = protocol["frozen_config"]
        rows: list[dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=config["max_workers"]) as pool:
            future_map = {
                pool.submit(
                    run_cell, cell, contexts, args.codex_command,
                    config["timeout_seconds"], args.work_root,
                ): cell
                for cell in plan
            }
            for completed, future in enumerate(concurrent.futures.as_completed(future_map), 1):
                row = future.result()
                rows.append(row)
                print(
                    f"[{completed:02d}/90] {row['agent_config']} r{row['replicate']} "
                    f"{row['task_id']} {row['representation']}: "
                    f"{'correct' if row['exact_success'] else 'wrong'} "
                    f"{row['total_tokens']} tokens",
                    flush=True,
                )
        rows.sort(key=lambda row: row["sequence"])
        report = {
            "schema_version": 1,
            "experiment_id": protocol["experiment_id"],
            "generated_at": utc_now(),
            "protocol_path": args.protocol.resolve().relative_to(REPO).as_posix(),
            "protocol_sha256": sha256(args.protocol),
            "tasks_path": protocol["frozen_config"]["tasks_file"],
            "tasks_sha256": protocol["frozen_config"]["tasks_sha256"],
            "context_contracts": contexts,
            "protocol": protocol,
            "results": rows,
            "summary": summarize(rows),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"agent-data runner error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2), flush=True)
    print(f"wrote {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
