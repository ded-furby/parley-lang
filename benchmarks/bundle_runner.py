#!/usr/bin/env python3
"""Run fresh Codex sessions that solve predeclared bundles of held-out tasks.

The workload-scale protocol keeps the task population fixed while changing how
many unrelated programs share one fresh agent session. Every session gets one
public checker command; hidden cases remain in this parent process.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import hashlib
import json
import os
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

try:
    from .agent_runner import (
        CHECK_LOG,
        DEFAULT_SKILL,
        EXTENSIONS,
        LANGUAGES,
        ROUGH_TOKEN_RE,
        command_protocol,
        judge,
        load_tasks,
        parse_codex_events,
        protocol_metadata,
        read_attempts,
        utc_now,
    )
except ImportError:  # direct ``python3 benchmarks/bundle_runner.py`` execution
    from agent_runner import (
        CHECK_LOG,
        DEFAULT_SKILL,
        EXTENSIONS,
        LANGUAGES,
        ROUGH_TOKEN_RE,
        command_protocol,
        judge,
        load_tasks,
        parse_codex_events,
        protocol_metadata,
        read_attempts,
        utc_now,
    )


REPO = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = Path(__file__).with_name("bundle_protocol_017.json")


def bundle_source_name(task_id: str, language: str) -> str:
    return task_id + EXTENSIONS[language]


def load_protocol(path: Path) -> dict[str, Any]:
    protocol = json.loads(path.read_text(encoding="utf-8"))
    if protocol.get("schema_version") != 1:
        raise ValueError("bundle protocol must use schema_version 1")
    config = protocol.get("frozen_config")
    if not isinstance(config, dict):
        raise ValueError("bundle protocol needs frozen_config")
    required = {
        "tasks_file",
        "parley_version",
        "parley_skill_sha256",
        "parley_skill_chars",
        "bundle_sizes",
        "replicates",
        "languages",
        "model",
        "reasoning",
        "seed",
        "timeout_seconds",
        "max_workers",
    }
    missing = required - set(config)
    if missing:
        raise ValueError(f"bundle protocol missing frozen config: {sorted(missing)}")
    if config["languages"] != list(LANGUAGES):
        raise ValueError(f"bundle protocol languages must be {list(LANGUAGES)}")
    sizes = config["bundle_sizes"]
    if not isinstance(sizes, list) or not sizes or any(
        not isinstance(size, int) or size < 1 for size in sizes
    ):
        raise ValueError("bundle_sizes must be a non-empty list of positive integers")
    for field in ("replicates", "seed", "timeout_seconds", "max_workers"):
        if not isinstance(config[field], int) or config[field] < 1:
            raise ValueError(f"{field} must be a positive integer")
    return protocol


def build_bundle_plan(
    tasks: list[dict[str, Any]],
    bundle_sizes: list[int],
    replicates: int,
    seed: int,
) -> list[dict[str, Any]]:
    if any(len(tasks) % size for size in bundle_sizes):
        raise ValueError("every bundle size must divide the task count exactly")
    plan = []
    for replicate in range(1, replicates + 1):
        for bundle_size in bundle_sizes:
            ordered = list(tasks)
            random.Random(seed + replicate * 10_007 + bundle_size * 1_009).shuffle(ordered)
            for index in range(0, len(ordered), bundle_size):
                task_group = ordered[index:index + bundle_size]
                plan.append({
                    "replicate": replicate,
                    "bundle_size": bundle_size,
                    "bundle_index": index // bundle_size + 1,
                    "bundle_id": f"s{bundle_size}-b{index // bundle_size + 1}",
                    "tasks": task_group,
                    "task_ids": [task["id"] for task in task_group],
                })
    return plan


BUNDLE_CHECK_SCRIPT = r'''#!/usr/bin/env python3
import json
import subprocess
import sys
import time
from pathlib import Path

config = json.loads(Path(".benchmark_public.json").read_text())
language = config["language"]
started = time.perf_counter()
task_results = {}
sources = {}

for task in config["tasks"]:
    task_id = task["id"]
    repo = Path(task.get("repo", "."))
    source = repo / task["source"]
    binary = Path(f".benchmark_public_{task_id}").resolve()
    if source.is_file():
        sources[task_id] = {
            filename: (repo / filename).read_text()
            for filename in task.get("editable_files", [task["source"]])
        }
    else:
        sources[task_id] = ""
        task_results[task_id] = {
            "ok": False,
            "compile_ok": False,
            "compile_returncode": None,
            "compile_stdout": "",
            "compile_stderr": f"missing {source}",
            "cases": [],
        }
        continue

    if language == "parley":
        compile_command = [config["parley_command"], "build", task["source"], "-o", str(binary)]
    elif language == "python":
        compile_command = [sys.executable, "-m", "py_compile", task["source"]]
    else:
        compile_command = ["rustc", "--edition=2021", task["source"], "-O", "-o", str(binary)]

    compiled = subprocess.run(compile_command, cwd=repo, capture_output=True, text=True, timeout=120)
    case_results = []
    if compiled.returncode == 0:
        run_command = [sys.executable, source.name] if language == "python" else [str(binary)]
        for case_index, case in enumerate(task["public_cases"], 1):
            expected_files = case.get("files", {})
            for filename in expected_files:
                output_path = repo / filename
                if output_path.is_file() or output_path.is_symlink():
                    output_path.unlink()
            proc = subprocess.run(
                run_command,
                input=case["stdin"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=repo,
            )
            actual_files = {
                filename: (repo / filename).read_text(encoding="utf-8") if (repo / filename).is_file() else None
                for filename in expected_files
            }
            files_ok = all(actual_files[name] == content for name, content in expected_files.items())
            case_results.append({
                "case": case_index,
                "ok": proc.returncode == 0 and proc.stdout == case["stdout"] and files_ok,
                "returncode": proc.returncode,
                "expected_stdout": case["stdout"],
                "actual_stdout": proc.stdout,
                "expected_files": expected_files,
                "actual_files": actual_files,
                "stderr": proc.stderr,
            })
    task_results[task_id] = {
        "ok": compiled.returncode == 0 and all(case["ok"] for case in case_results),
        "compile_ok": compiled.returncode == 0,
        "compile_returncode": compiled.returncode,
        "compile_stdout": compiled.stdout,
        "compile_stderr": compiled.stderr,
        "cases": case_results,
    }

ok = all(result["ok"] for result in task_results.values()) and len(task_results) == len(config["tasks"])
record = {
    "ok": ok,
    "tasks": task_results,
    "sources": sources,
    "elapsed_seconds": round(time.perf_counter() - started, 4),
}
with Path(".benchmark_attempts.jsonl").open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(record, sort_keys=True) + "\n")

for task_id, result in task_results.items():
    if result["ok"]:
        print(f"{task_id}: public checks passed")
        continue
    print(f"{task_id}: public checks failed", file=sys.stderr)
    if result["compile_stderr"]:
        print(result["compile_stderr"], end="", file=sys.stderr)
    for case in result["cases"]:
        if not case["ok"]:
            print(f"case {case['case']} expected {case['expected_stdout']!r}", file=sys.stderr)
            print(f"case {case['case']} actual   {case['actual_stdout']!r}", file=sys.stderr)
            for filename, expected in case.get("expected_files", {}).items():
                actual = case.get("actual_files", {}).get(filename)
                if actual != expected:
                    print(f"case {case['case']} file {filename} expected {expected!r}", file=sys.stderr)
                    print(f"case {case['case']} file {filename} actual   {actual!r}", file=sys.stderr)
            if case["stderr"]:
                print(case["stderr"], end="", file=sys.stderr)

raise SystemExit(0 if ok else 1)
'''


BUNDLE_SOURCE_SCRIPT = r'''#!/usr/bin/env python3
import json
from pathlib import Path

config = json.loads(Path(".benchmark_public.json").read_text())
for task in config["tasks"]:
    repo = Path(task.get("repo", "."))
    read_only = set(task.get("read_only_files", []))
    for filename in task.get("visible_files", task.get("editable_files", [])):
        path = repo / filename
        marker = " [read-only]" if filename in read_only else ""
        print(f"===== {task['id']}/{filename}{marker} =====")
        text = path.read_text(encoding="utf-8")
        print(text, end="" if text.endswith("\n") else "\n")
'''


def write_bundle_workspace(
    workdir: Path,
    tasks: list[dict[str, Any]],
    language: str,
    parley_command: str,
) -> dict[str, str]:
    task_configs = []
    repository_mode = any(task.get("seed_files") is not None for task in tasks)
    for task in tasks:
        if task.get("seed_files") is not None:
            editable_files = sorted(task["seed_files"][language])
            read_only_files = sorted(task.get("context_files", {}).get(language, {}))
            task_configs.append({
                "id": task["id"],
                "repo": task["id"],
                "source": task["entrypoints"][language],
                "editable_files": editable_files,
                "read_only_files": read_only_files,
                "visible_files": sorted([*editable_files, *read_only_files]),
                "public_cases": task["public_cases"],
            })
        else:
            task_configs.append({
                "id": task["id"],
                "repo": ".",
                "source": bundle_source_name(task["id"], language),
                "editable_files": [bundle_source_name(task["id"], language)],
                "public_cases": task["public_cases"],
            })
    config = {
        "language": language,
        "parley_command": parley_command,
        "tasks": task_configs,
    }
    files = {
        ".benchmark_public.json": json.dumps(config, indent=2) + "\n",
        "check_public.py": BUNDLE_CHECK_SCRIPT,
        "check": "#!/bin/sh\nexec python3 check_public.py\n",
    }
    if repository_mode:
        files.update({
            "print_sources.py": BUNDLE_SOURCE_SCRIPT,
            "sources": "#!/bin/sh\nexec python3 print_sources.py\n",
        })
    for name, content in files.items():
        path = workdir / name
        path.write_text(content, encoding="utf-8")
        if name in {"check", "check_public.py", "sources", "print_sources.py"}:
            path.chmod(0o755)
    for task in tasks:
        if task.get("seed_files") is not None:
            repo = workdir / task["id"]
            for filename, content in task["seed_files"][language].items():
                path = repo / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            for filename, content in task.get("context_files", {}).get(language, {}).items():
                path = repo / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            continue
        seed_sources = task.get("seed_sources")
        if seed_sources is not None:
            (workdir / bundle_source_name(task["id"], language)).write_text(
                seed_sources[language], encoding="utf-8"
            )
    integrity = {
        name: hashlib.sha256(content.encode()).hexdigest()
        for name, content in files.items()
    }
    for task in tasks:
        for filename, content in task.get("context_files", {}).get(language, {}).items():
            integrity[f"{task['id']}/{filename}"] = hashlib.sha256(
                content.encode()
            ).hexdigest()
    return integrity


def render_bundle_prompt(
    tasks: list[dict[str, Any]],
    language: str,
    parley_skill: str,
) -> str:
    label = {"parley": "Parley", "python": "Python", "rust": "Rust"}[language]
    filenames = [bundle_source_name(task["id"], language) for task in tasks]
    repository_tasks = [task for task in tasks if task.get("seed_files") is not None]
    has_repository_context = any(task.get("context_files") for task in repository_tasks)
    formatted_names = ", ".join(f"`{name}`" for name in filenames)
    seeded = [task for task in tasks if task.get("seed_sources") is not None]
    unseeded = [task for task in tasks if task.get("seed_sources") is None]
    inspection_rule = (
        "For repository tasks, inspect editable code only through `./sources`; "
        "for inline seeded tasks, the exact starting source is reproduced below."
    )
    context_rules: list[str] = []
    if repository_tasks and len(repository_tasks) == len(tasks):
        work_summary = (
            f"Maintain {len(tasks)} independent {label} repositories: "
            + ", ".join(f"`{task['id']}/`" for task in tasks) + "."
        )
        if has_repository_context:
            first_action = (
                "Your first shell action must be exactly `./sources`; it prints editable source and declared read-only project context. "
                "Do not perform other reconnaissance."
            )
            inspection_rule = (
                "Inspect editable code and declared project context only through `./sources`."
            )
            context_rules = [
                "Files marked `[read-only]` are integrity-checked project evidence; do not modify them."
            ]
        else:
            first_action = (
                "Your first shell action must be exactly `./sources`; it prints every editable source file. "
                "Do not perform other reconnaissance."
            )
        unit_rule = "Each repository is independent and must solve only its named task."
        shell_rule = (
            "The only shell commands permitted are exactly `./sources` once and `./check`."
        )
    elif seeded and not unseeded:
        work_summary = (
            f"Update {len(tasks)} independent {label} programs in place: {formatted_names}."
        )
        first_action = (
            "Your first tool action must edit one or more listed solution files. "
            "Do not perform reconnaissance first."
        )
        unit_rule = "Each file is a separate program and must solve only its named task."
        shell_rule = (
            "After creating or editing solutions, the only shell command permitted is exactly `./check`."
        )
    elif unseeded and not seeded:
        work_summary = (
            f"Implement {len(tasks)} independent tasks in {label} by creating: {formatted_names}."
        )
        first_action = (
            "Your first tool action must create one or more listed solution files. "
            "Do not perform reconnaissance first."
        )
        unit_rule = "Each file is a separate program and must solve only its named task."
        shell_rule = (
            "After creating or editing solutions, the only shell command permitted is exactly `./check`."
        )
    else:
        work_summary = (
            f"Complete {len(tasks)} independent {label} tasks in these files: {formatted_names}."
        )
        first_action = (
            "Your first tool action must create or edit one or more listed solution files. "
            "Do not perform reconnaissance first."
        )
        unit_rule = "Each file is a separate program and must solve only its named task."
        shell_rule = (
            "After creating or editing solutions, the only shell command permitted is exactly `./check`."
        )
    lines = [
        "You are participating in a controlled coding benchmark in a fresh workspace.",
        work_summary,
        unit_rule,
        "Work only inside the current directory. All information needed is in this prompt.",
        "Do not list, read, or inspect any existing workspace file, including checker/config files.",
        inspection_rule,
        *context_rules,
        "Do not use the internet or modify checker/config files.",
        first_action,
        shell_rule,
        "Do not invoke a global language command.",
        "Complete every listed task, then run `./check`. If it fails, use its feedback to repair",
        "the failing program or programs and run `./check` again. Continue until every public",
        "check passes or you cannot make progress.",
        "The final answer should briefly state whether the complete public bundle passed.",
        "",
    ]
    for task_index, task in enumerate(tasks, 1):
        lines.extend([
            f"# Task {task_index}: {task['title']}",
            "",
            (
                f"Repository: `{task['id']}/`; entrypoint: "
                f"`{task['id']}/{task['entrypoints'][language]}`"
                if task.get("seed_files") is not None
                else f"Target file: `{bundle_source_name(task['id'], language)}`"
            ),
            "",
            task["statement"],
            "",
        ])
        if task.get("show_public_examples", True):
            for case_index, case in enumerate(task["public_cases"], 1):
                lines.extend([
                    f"Public example {case_index} input:",
                    "```text",
                    case["stdin"].rstrip("\n"),
                    "```",
                    f"Public example {case_index} output:",
                    "```text",
                    case["stdout"].rstrip("\n"),
                    "```",
                    "",
                ])
        if task.get("seed_sources") is not None:
            lines.extend([
                "Starting source (already present in the target file):",
                f"```{language}",
                task["seed_sources"][language].rstrip("\n"),
                "```",
                "",
            ])
    if language == "parley":
        lines.extend([
            "# Parley language instructions",
            "",
            "The following is the compact core Parley skill shipped with the tested compiler.",
            "Rare-feature reference files are intentionally excluded unless the task needs them.",
            "Its tokens are included in this run's measured input cost.",
            "",
            parley_skill.rstrip(),
            "",
        ])
    elif language == "python":
        lines.extend([
            "Use only the Python standard library. The checker compiles every file and runs its public cases.",
            "",
        ])
    else:
        lines.extend([
            "Use only the Rust standard library. The checker compiles every file with rustc edition 2021 and runs its public cases.",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def rough_token_edit_count(before: str, after: str) -> int:
    """Count inserted and deleted rough tokens in a seed-to-final edit."""
    before_tokens = ROUGH_TOKEN_RE.findall(before)
    after_tokens = ROUGH_TOKEN_RE.findall(after)
    matcher = difflib.SequenceMatcher(a=before_tokens, b=after_tokens, autojunk=False)
    return sum(
        (i2 - i1) + (j2 - j1)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    )


def run_bundle_cell(
    cell: dict[str, Any],
    *,
    codex_command: str,
    model: str,
    reasoning: str,
    parley_command: str,
    parley_skill: str,
    timeout: int,
    work_root: Path,
) -> dict[str, Any]:
    tasks = cell["tasks"]
    language = cell["language"]
    task_count = len(tasks)
    workdir = Path(tempfile.mkdtemp(
        prefix=f"bundle-{cell['bundle_id']}-{language}-r{cell['replicate']}-",
        dir=work_root,
    ))
    integrity = write_bundle_workspace(workdir, tasks, language, parley_command)
    prompt = render_bundle_prompt(tasks, language, parley_skill)
    (workdir / "prompt.md").write_text(prompt, encoding="utf-8")

    command = [
        codex_command,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--disable", "plugins",
        "--disable", "apps",
        "--disable", "browser_use",
        "--disable", "computer_use",
        "--disable", "multi_agent",
        "--skip-git-repo-check",
        "-s", "workspace-write",
        "-m", model,
        "-c", f'model_reasoning_effort="{reasoning}"',
        "-c", 'approval_policy="never"',
        "-c", 'shell_environment_policy.inherit="all"',
        "--json",
        "-C", str(workdir),
        prompt,
    ]
    started = time.perf_counter()
    timed_out = False
    agent_env = dict(os.environ)
    parley_bin_dir = str(Path(parley_command).resolve().parent)
    agent_env["PATH"] = parley_bin_dir + os.pathsep + agent_env.get("PATH", "")
    try:
        proc = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=agent_env,
        )
        returncode = proc.returncode
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    elapsed = round(time.perf_counter() - started, 4)

    parsed = parse_codex_events(stdout)
    repository_mode = all(task.get("seed_files") is not None for task in tasks)
    compliance = command_protocol(
        parsed["command_events"], allow_sources=repository_mode
    )
    attempts = read_attempts(workdir / CHECK_LOG)
    first_tasks = attempts[0].get("tasks", {}) if attempts else {}
    final_tasks = attempts[-1].get("tasks", {}) if attempts else {}
    integrity_ok = all(
        (workdir / name).is_file()
        and hashlib.sha256((workdir / name).read_bytes()).hexdigest() == digest
        for name, digest in integrity.items()
    )

    task_results = {}
    source_texts = {}
    seed_source_texts = {}
    for task in tasks:
        task_id = task["id"]
        if task.get("seed_files") is not None:
            repo = workdir / task_id
            source = repo / task["entrypoints"][language]
            seed_files = task["seed_files"][language]
            declared_context_files = task.get("context_files", {}).get(language, {})
            source_files = {
                filename: (repo / filename).read_text(encoding="utf-8")
                if (repo / filename).is_file() else ""
                for filename in sorted(seed_files)
            }
            seed_source_files = dict(sorted(seed_files.items()))
            context_source_files = dict(sorted(declared_context_files.items()))
        else:
            source = workdir / bundle_source_name(task_id, language)
            source_files = {
                bundle_source_name(task_id, language):
                source.read_text(encoding="utf-8") if source.is_file() else ""
            }
            seed_text = task.get("seed_sources", {}).get(language, "")
            seed_source_files = {
                bundle_source_name(task_id, language): seed_text
            } if seed_text else {}
            context_source_files = {}
        source_text = "\n".join(source_files.values())
        seed_source_text = "\n".join(seed_source_files.values())
        context_source_text = "\n".join(context_source_files.values())
        source_texts[task_id] = source_text
        seed_source_texts[task_id] = seed_source_text
        hidden = (
            judge(language, source, task["hidden_cases"], parley_command)
            if source.is_file()
            else {"ok": False, "compile": {"ok": False, "stderr": "solution file missing"}, "cases": []}
        )
        task_results[task_id] = {
            "task_title": task["title"],
            "source_name": (
                f"{task_id}/{task['entrypoints'][language]}"
                if task.get("seed_files") is not None
                else bundle_source_name(task_id, language)
            ),
            "source_text": source_text,
            "source_files": source_files,
            "source_chars": len(source_text),
            "source_lines": len(source_text.splitlines()),
            "source_rough_tokens": len(ROUGH_TOKEN_RE.findall(source_text)),
            "seed_source_text": seed_source_text,
            "seed_source_files": seed_source_files,
            "seed_source_chars": len(seed_source_text),
            "seed_source_lines": len(seed_source_text.splitlines()),
            "seed_source_rough_tokens": len(ROUGH_TOKEN_RE.findall(seed_source_text)),
            "context_source_files": context_source_files,
            "context_source_text": context_source_text,
            "context_source_chars": len(context_source_text),
            "context_source_lines": len(context_source_text.splitlines()),
            "context_source_rough_tokens": len(
                ROUGH_TOKEN_RE.findall(context_source_text)
            ),
            "source_edit_rough_tokens": sum(
                rough_token_edit_count(
                    seed_source_files.get(filename, ""), source_files.get(filename, "")
                )
                for filename in set(seed_source_files) | set(source_files)
            ),
            "changed_files": sorted(
                filename for filename in set(seed_source_files) | set(source_files)
                if seed_source_files.get(filename, "") != source_files.get(filename, "")
            ),
            "first_public_check_success": bool(first_tasks.get(task_id, {}).get("ok")),
            "final_public_check_success": bool(final_tasks.get(task_id, {}).get("ok")),
            "hidden_success": bool(hidden["ok"]),
            "hidden_judgment": hidden,
        }

    usage = parsed["usage"]
    total_tokens = usage["input_tokens"] + usage["output_tokens"]
    hidden_task_successes = sum(result["hidden_success"] for result in task_results.values())
    first_task_successes = sum(
        result["first_public_check_success"] for result in task_results.values()
    )
    source_chars = sum(result["source_chars"] for result in task_results.values())
    source_lines = sum(result["source_lines"] for result in task_results.values())
    source_rough_tokens = sum(
        result["source_rough_tokens"] for result in task_results.values()
    )
    seed_source_rough_tokens = sum(
        result["seed_source_rough_tokens"] for result in task_results.values()
    )
    context_source_chars = sum(
        result["context_source_chars"] for result in task_results.values()
    )
    context_source_lines = sum(
        result["context_source_lines"] for result in task_results.values()
    )
    context_source_rough_tokens = sum(
        result["context_source_rough_tokens"] for result in task_results.values()
    )
    source_edit_rough_tokens = sum(
        result["source_edit_rough_tokens"] for result in task_results.values()
    )
    changed_files = sum(len(result["changed_files"]) for result in task_results.values())
    return {
        "schema_version": 1,
        "recorded_at": utc_now(),
        "bundle_id": cell["bundle_id"],
        "bundle_size": cell["bundle_size"],
        "bundle_index": cell["bundle_index"],
        "task_ids": [task["id"] for task in tasks],
        "task_count": task_count,
        "language": language,
        "replicate": cell["replicate"],
        "model": model,
        "reasoning_effort": reasoning,
        "fresh_ephemeral_session": True,
        "workdir": str(workdir),
        "thread_id": parsed["thread_id"],
        "agent_returncode": returncode,
        "agent_timed_out": timed_out,
        "elapsed_seconds": elapsed,
        "elapsed_seconds_per_task": round(elapsed / task_count, 6),
        "check_integrity_ok": integrity_ok,
        "command_protocol_compliant": compliance["compliant"],
        "command_protocol_violations": compliance["violations"],
        "public_check_attempts": len(attempts),
        "first_bundle_check_success": bool(attempts and attempts[0].get("ok")),
        "final_bundle_check_success": bool(attempts and attempts[-1].get("ok")),
        "first_public_task_successes": first_task_successes,
        "repair_turns": max(len(attempts) - 1, 0),
        "hidden_task_successes": hidden_task_successes,
        "hidden_bundle_success": hidden_task_successes == task_count,
        "usage": usage,
        "total_tokens": total_tokens,
        "total_tokens_per_task": round(total_tokens / task_count, 6),
        "input_tokens_per_task": round(usage["input_tokens"] / task_count, 6),
        "output_tokens_per_task": round(usage["output_tokens"] / task_count, 6),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_chars": len(prompt),
        "prompt_chars_per_task": round(len(prompt) / task_count, 6),
        "source_texts": source_texts,
        "seed_source_texts": seed_source_texts,
        "source_chars": source_chars,
        "source_lines": source_lines,
        "source_rough_tokens": source_rough_tokens,
        "source_chars_per_task": round(source_chars / task_count, 6),
        "source_lines_per_task": round(source_lines / task_count, 6),
        "source_rough_tokens_per_task": round(source_rough_tokens / task_count, 6),
        "seed_source_rough_tokens": seed_source_rough_tokens,
        "seed_source_rough_tokens_per_task": round(
            seed_source_rough_tokens / task_count, 6
        ),
        "context_source_chars": context_source_chars,
        "context_source_lines": context_source_lines,
        "context_source_rough_tokens": context_source_rough_tokens,
        "context_source_chars_per_task": round(context_source_chars / task_count, 6),
        "context_source_lines_per_task": round(context_source_lines / task_count, 6),
        "context_source_rough_tokens_per_task": round(
            context_source_rough_tokens / task_count, 6
        ),
        "source_edit_rough_tokens": source_edit_rough_tokens,
        "source_edit_rough_tokens_per_task": round(
            source_edit_rough_tokens / task_count, 6
        ),
        "changed_files": changed_files,
        "changed_files_per_task": round(changed_files / task_count, 6),
        "task_results": task_results,
        "public_attempts": attempts,
        "agent_messages": parsed["agent_messages"],
        "agent_errors": parsed["errors"],
        "command_events": parsed["command_events"],
        "codex_stdout": stdout,
        "codex_stderr": stderr,
    }


def _median(rows: list[dict[str, Any]], field: str) -> float:
    return statistics.median(float(row.get(field, 0)) for row in rows)


def summarize_bundle_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_scale = []
    scales = sorted({int(row["bundle_size"]) for row in results})
    for bundle_size in scales:
        for language in LANGUAGES:
            rows = [
                row for row in results
                if row.get("language") == language and row.get("bundle_size") == bundle_size
            ]
            if not rows:
                continue
            assigned_tasks = sum(int(row.get("task_count", 0)) for row in rows)
            hidden_tasks = sum(int(row.get("hidden_task_successes", 0)) for row in rows)
            first_tasks = sum(int(row.get("first_public_task_successes", 0)) for row in rows)
            hidden_bundles = sum(bool(row.get("hidden_bundle_success")) for row in rows)
            first_bundles = sum(bool(row.get("first_bundle_check_success")) for row in rows)
            compliant = sum(bool(row.get("command_protocol_compliant")) for row in rows)
            input_per_task = [
                float(row.get("usage", {}).get("input_tokens", 0)) / row["task_count"]
                for row in rows
            ]
            output_per_task = [
                float(row.get("usage", {}).get("output_tokens", 0)) / row["task_count"]
                for row in rows
            ]
            by_scale.append({
                "bundle_size": bundle_size,
                "language": language,
                "sessions": len(rows),
                "assigned_tasks": assigned_tasks,
                "hidden_task_successes": hidden_tasks,
                "hidden_task_success_rate": round(hidden_tasks / assigned_tasks, 4),
                "hidden_bundle_successes": hidden_bundles,
                "hidden_bundle_success_rate": round(hidden_bundles / len(rows), 4),
                "first_public_task_successes": first_tasks,
                "first_public_task_success_rate": round(first_tasks / assigned_tasks, 4),
                "first_bundle_check_successes": first_bundles,
                "first_bundle_check_success_rate": round(first_bundles / len(rows), 4),
                "command_protocol_compliant_sessions": compliant,
                "command_protocol_compliance_rate": round(compliant / len(rows), 4),
                "repair_turns": sum(int(row.get("repair_turns", 0)) for row in rows),
                "median_total_tokens_per_session": _median(rows, "total_tokens"),
                "median_total_tokens_per_task": _median(rows, "total_tokens_per_task"),
                "weighted_total_tokens_per_task": round(
                    sum(int(row.get("total_tokens", 0)) for row in rows) / assigned_tasks,
                    4,
                ),
                "median_input_tokens_per_task": statistics.median(input_per_task),
                "median_output_tokens_per_task": statistics.median(output_per_task),
                "median_elapsed_seconds_per_session": round(_median(rows, "elapsed_seconds"), 4),
                "median_elapsed_seconds_per_task": round(_median(rows, "elapsed_seconds_per_task"), 4),
                "median_prompt_chars_per_task": _median(rows, "prompt_chars_per_task"),
                "median_source_rough_tokens_per_task": _median(rows, "source_rough_tokens_per_task"),
                "median_seed_source_rough_tokens_per_task": _median(
                    rows, "seed_source_rough_tokens_per_task"
                ),
                "median_source_edit_rough_tokens_per_task": _median(
                    rows, "source_edit_rough_tokens_per_task"
                ),
                "median_changed_files_per_task": _median(rows, "changed_files_per_task"),
            })

    primary_scale = max(scales) if scales else None
    scale_rows = {
        row["language"]: row
        for row in by_scale
        if row["bundle_size"] == primary_scale
    }
    strict_gate = {"scale": primary_scale, "passed": False, "conditions": {}}
    if set(scale_rows) == set(LANGUAGES):
        parley = scale_rows["parley"]
        python = scale_rows["python"]
        rust = scale_rows["rust"]
        conditions = {
            "correctness": (
                parley["hidden_task_success_rate"] == 1.0
                and parley["hidden_task_success_rate"] >= python["hidden_task_success_rate"]
                and parley["hidden_task_success_rate"] >= rust["hidden_task_success_rate"]
            ),
            "tokens": parley["median_total_tokens_per_task"] <= min(
                python["median_total_tokens_per_task"], rust["median_total_tokens_per_task"]
            ),
            "elapsed": parley["median_elapsed_seconds_per_task"] <= min(
                python["median_elapsed_seconds_per_task"], rust["median_elapsed_seconds_per_task"]
            ),
            "first_check": parley["first_public_task_success_rate"] >= max(
                python["first_public_task_success_rate"], rust["first_public_task_success_rate"]
            ),
        }
        strict_gate = {
            "scale": primary_scale,
            "passed": all(conditions.values()),
            "conditions": conditions,
        }
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "sessions": len(results),
        "assigned_tasks": sum(int(row.get("task_count", 0)) for row in results),
        "by_scale": by_scale,
        "strict_gate": strict_gate,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run fresh Codex sessions on task bundles.")
    parser.add_argument("--protocol-file", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--codex-command", default=shutil.which("codex") or "codex")
    parser.add_argument("--parley-command", required=True)
    parser.add_argument("--parley-skill", type=Path, default=DEFAULT_SKILL)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        preregistration = load_protocol(args.protocol_file)
        config = preregistration["frozen_config"]
        tasks_file = REPO / config["tasks_file"]
        tasks = load_tasks(tasks_file)
        if any(len(tasks) % size for size in config["bundle_sizes"]):
            raise ValueError("every frozen bundle size must divide the frozen task count")
        parley_skill = args.parley_skill.read_text(encoding="utf-8")
        preflight_metadata = protocol_metadata(
            tasks_file,
            args.parley_skill,
            args.codex_command,
            args.parley_command,
        )
        for field in ("parley_version", "parley_skill_sha256", "parley_skill_chars"):
            if preflight_metadata[field] != config[field]:
                raise ValueError(
                    f"frozen {field} mismatch: expected {config[field]!r}, "
                    f"got {preflight_metadata[field]!r}"
                )
        plan = build_bundle_plan(
            tasks,
            config["bundle_sizes"],
            config["replicates"],
            config["seed"],
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"bundle benchmark error: {exc}", file=sys.stderr)
        return 1

    cells = [
        {**bundle, "language": language}
        for bundle in plan
        for language in config["languages"]
    ]
    random.Random(config["seed"]).shuffle(cells)
    work_root = args.work_root or Path(tempfile.mkdtemp(prefix="parley-agent-bundles-"))
    work_root.mkdir(parents=True, exist_ok=True)
    print(
        f"running {len(cells)} fresh sessions / "
        f"{sum(cell['bundle_size'] for cell in cells)} assigned tasks with "
        f"{config['model']} ({config['reasoning']}); work root: {work_root}",
        flush=True,
    )

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=config["max_workers"]) as pool:
        futures = {
            pool.submit(
                run_bundle_cell,
                cell,
                codex_command=args.codex_command,
                model=config["model"],
                reasoning=config["reasoning"],
                parley_command=args.parley_command,
                parley_skill=parley_skill,
                timeout=config["timeout_seconds"],
                work_root=work_root,
            ): cell
            for cell in cells
        }
        for future in concurrent.futures.as_completed(futures):
            cell = futures[future]
            try:
                row = future.result()
            except Exception as exc:  # preserve the rest of an expensive matrix
                row = {
                    "schema_version": 1,
                    "recorded_at": utc_now(),
                    "bundle_id": cell["bundle_id"],
                    "bundle_size": cell["bundle_size"],
                    "bundle_index": cell["bundle_index"],
                    "task_ids": cell["task_ids"],
                    "task_count": cell["bundle_size"],
                    "language": cell["language"],
                    "replicate": cell["replicate"],
                    "model": config["model"],
                    "runner_error": repr(exc),
                    "hidden_task_successes": 0,
                    "hidden_bundle_success": False,
                    "first_public_task_successes": 0,
                    "first_bundle_check_success": False,
                    "command_protocol_compliant": False,
                    "repair_turns": 0,
                    "total_tokens": 0,
                    "total_tokens_per_task": 0,
                    "elapsed_seconds": 0,
                    "elapsed_seconds_per_task": 0,
                }
            results.append(row)
            print(
                f"completed {row['bundle_id']} {row['language']} r{row['replicate']} "
                f"({row['task_count']} tasks): hidden="
                f"{row.get('hidden_task_successes', 0)}/{row['task_count']} "
                f"checks={row.get('public_check_attempts', 0)} "
                f"tokens/task={row.get('total_tokens_per_task', 0):.1f}",
                flush=True,
            )

    results.sort(key=lambda row: (
        row["bundle_size"], row["replicate"], row["bundle_index"], row["language"]
    ))
    metadata = preflight_metadata
    metadata.update({
        "protocol_version": "bundle-v1",
        "protocol_file_sha256": hashlib.sha256(args.protocol_file.read_bytes()).hexdigest(),
        "protocol_file": str(args.protocol_file),
        "bundle_sizes": config["bundle_sizes"],
        "replicates": config["replicates"],
        "seed": config["seed"],
        "fresh_session_per_cell": True,
        "hidden_cases_withheld_from_agents": True,
    })
    report = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "preregistration": preregistration,
        "protocol": metadata,
        "bundle_plan": [
            {
                "replicate": bundle["replicate"],
                "bundle_size": bundle["bundle_size"],
                "bundle_index": bundle["bundle_index"],
                "bundle_id": bundle["bundle_id"],
                "task_ids": bundle["task_ids"],
            }
            for bundle in plan
        ],
        "summary": summarize_bundle_results(results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
