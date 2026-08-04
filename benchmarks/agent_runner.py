#!/usr/bin/env python3
"""Run fresh-context Codex pilots against held-out black-box tasks.

Every measured cell gets a new temporary workspace and a new ephemeral Codex
session. The agent sees one task, one public example, and a uniform ``./check``
command. Hidden cases stay in the parent runner and are evaluated only after
the agent exits.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = Path(__file__).with_name("agent_tasks.json")
DEFAULT_SKILL = REPO / "skill" / "parley" / "SKILL.md"
LANGUAGES = ("parley", "python", "rust")
EXTENSIONS = {"parley": ".par", "python": ".py", "rust": ".rs"}
MODEL_DEFAULT = "gpt-5.6-sol"
REASONING_DEFAULT = "medium"
CHECK_LOG = ".benchmark_attempts.jsonl"
ROUGH_TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_']*|\d+\.\d+|\d+|==|!=|<=|>=|[^\s]",
    re.ASCII,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def command_version(command: list[str], cwd: Path | None = None) -> str:
    try:
        proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    text = (proc.stdout or proc.stderr).strip().splitlines()
    return text[-1] if text else "unavailable"


def protocol_metadata(
    tasks_file: Path,
    skill_file: Path,
    codex_command: str,
    parley_command: str,
) -> dict[str, Any]:
    skill_text = skill_file.read_text(encoding="utf-8")
    return {
        "compiler_commit": command_version(["git", "rev-parse", "HEAD"], cwd=REPO),
        "parley_version": command_version([parley_command, "--version"]),
        "codex_cli_version": command_version([codex_command, "--version"]),
        "python_version": sys.version.split()[0],
        "rustc_version": command_version(["rustc", "--version"]),
        "task_manifest_sha256": hashlib.sha256(tasks_file.read_bytes()).hexdigest(),
        "parley_skill_sha256": hashlib.sha256(skill_file.read_bytes()).hexdigest(),
        "parley_skill_chars": len(skill_text),
    }


def load_tasks(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("agent task manifest must use schema_version 1")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("agent task manifest needs a non-empty tasks list")
    seen: set[str] = set()
    for task in tasks:
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id or task_id in seen:
            raise ValueError(f"invalid or duplicate task id: {task_id!r}")
        seen.add(task_id)
        seed_sources = task.get("seed_sources")
        seed_files = task.get("seed_files")
        if seed_sources is not None and seed_files is not None:
            raise ValueError(f"{task_id}: use seed_sources or seed_files, not both")
        if seed_sources is not None:
            if not isinstance(seed_sources, dict) or set(seed_sources) != set(LANGUAGES):
                raise ValueError(
                    f"{task_id}: seed_sources must contain exactly {list(LANGUAGES)}"
                )
            for language, source_text in seed_sources.items():
                if not isinstance(source_text, str) or not source_text.strip():
                    raise ValueError(
                        f"{task_id}: seed source for {language} must be non-empty text"
                    )
        if seed_files is not None:
            entrypoints = task.get("entrypoints")
            if not isinstance(seed_files, dict) or set(seed_files) != set(LANGUAGES):
                raise ValueError(
                    f"{task_id}: seed_files must contain exactly {list(LANGUAGES)}"
                )
            if not isinstance(entrypoints, dict) or set(entrypoints) != set(LANGUAGES):
                raise ValueError(
                    f"{task_id}: entrypoints must contain exactly {list(LANGUAGES)}"
                )
            for language in LANGUAGES:
                files = seed_files[language]
                if not isinstance(files, dict) or not files:
                    raise ValueError(f"{task_id}: {language} seed_files must be non-empty")
                for filename, source_text in files.items():
                    if not isinstance(filename, str) or not isinstance(source_text, str):
                        raise ValueError(
                            f"{task_id}: repository paths and contents must be strings"
                        )
                    candidate = PurePosixPath(filename)
                    if (
                        not filename
                        or candidate.is_absolute()
                        or ".." in candidate.parts
                        or any(part in {"", "."} for part in candidate.parts)
                        or any(part.startswith(".") for part in candidate.parts)
                    ):
                        raise ValueError(
                            f"{task_id}: unsafe repository source path: {filename!r}"
                        )
                    if not source_text.strip():
                        raise ValueError(
                            f"{task_id}: repository source {filename!r} must be non-empty"
                        )
                entrypoint = entrypoints[language]
                if not isinstance(entrypoint, str) or entrypoint not in files:
                    raise ValueError(
                        f"{task_id}: {language} entrypoint must name a seeded file"
                    )
        for case_group in ("public_cases", "hidden_cases"):
            cases = task.get(case_group)
            if not isinstance(cases, list) or not cases:
                raise ValueError(f"{task_id}: {case_group} must be non-empty")
            for case in cases:
                if not isinstance(case.get("stdin"), str) or not isinstance(case.get("stdout"), str):
                    raise ValueError(f"{task_id}: every case needs string stdin/stdout")
                expected_files = case.get("files", {})
                if not isinstance(expected_files, dict):
                    raise ValueError(f"{task_id}: case files must be a path-to-text object")
                for filename, content in expected_files.items():
                    if not isinstance(filename, str) or not isinstance(content, str):
                        raise ValueError(f"{task_id}: expected file paths and contents must be strings")
                    candidate = PurePosixPath(filename)
                    if (
                        not filename
                        or candidate.is_absolute()
                        or ".." in candidate.parts
                        or any(part in {"", "."} for part in candidate.parts)
                        or candidate.parts[0].startswith(".")
                        or candidate.parts[0] in {"check", "check_public.py", "prompt.md"}
                    ):
                        raise ValueError(f"{task_id}: unsafe expected file path: {filename!r}")
    return tasks


def source_name(language: str) -> str:
    return "solution" + EXTENSIONS[language]


def compile_candidate(
    language: str,
    source: Path,
    binary: Path,
    parley_command: str,
    timeout: int = 120,
) -> dict[str, Any]:
    if language == "parley":
        command = [parley_command, "build", source.name, "-o", str(binary)]
    elif language == "python":
        command = [sys.executable, "-m", "py_compile", source.name]
    elif language == "rust":
        command = ["rustc", "--edition=2021", source.name, "-O", "-o", str(binary)]
    else:
        raise ValueError(f"unknown language: {language}")
    try:
        proc = subprocess.run(
            command,
            cwd=source.parent,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "command": command,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "command": command,
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }


def run_cases(
    language: str,
    source: Path,
    binary: Path,
    cases: list[dict[str, str]],
    timeout: int = 10,
) -> list[dict[str, Any]]:
    command = [sys.executable, source.name] if language == "python" else [str(binary)]
    results = []
    for index, case in enumerate(cases, 1):
        expected_files = case.get("files", {})
        for filename in expected_files:
            output_path = source.parent / filename
            if output_path.is_file() or output_path.is_symlink():
                output_path.unlink()
        started = time.perf_counter()
        try:
            proc = subprocess.run(
                command,
                cwd=source.parent,
                input=case["stdin"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            actual_files = {
                filename: (
                    (source.parent / filename).read_text(encoding="utf-8")
                    if (source.parent / filename).is_file()
                    else None
                )
                for filename in expected_files
            }
            files_ok = all(actual_files[name] == content for name, content in expected_files.items())
            result = {
                "case": index,
                "ok": proc.returncode == 0 and proc.stdout == case["stdout"] and files_ok,
                "returncode": proc.returncode,
                "expected_stdout": case["stdout"],
                "actual_stdout": proc.stdout,
                "expected_files": expected_files,
                "actual_files": actual_files,
                "stderr": proc.stderr,
                "elapsed_seconds": round(time.perf_counter() - started, 4),
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            result = {
                "case": index,
                "ok": False,
                "returncode": None,
                "expected_stdout": case["stdout"],
                "actual_stdout": "",
                "expected_files": expected_files,
                "actual_files": {},
                "stderr": str(exc),
                "elapsed_seconds": round(time.perf_counter() - started, 4),
            }
        results.append(result)
    return results


def judge(
    language: str,
    source: Path,
    cases: list[dict[str, str]],
    parley_command: str,
) -> dict[str, Any]:
    binary = source.parent / ".benchmark_solution"
    compile_result = compile_candidate(language, source, binary, parley_command)
    case_results = (
        run_cases(language, source, binary, cases) if compile_result["ok"] else []
    )
    return {
        "ok": compile_result["ok"] and all(case["ok"] for case in case_results),
        "compile": compile_result,
        "cases": case_results,
    }


PUBLIC_CHECK_SCRIPT = r'''#!/usr/bin/env python3
import json
import subprocess
import sys
import time
from pathlib import Path

config = json.loads(Path(".benchmark_public.json").read_text())
source = Path(config["source"])
binary = Path(".benchmark_public_solution").resolve()
language = config["language"]

if language == "parley":
    compile_command = [config["parley_command"], "build", source.name, "-o", str(binary)]
elif language == "python":
    compile_command = [sys.executable, "-m", "py_compile", source.name]
else:
    compile_command = ["rustc", "--edition=2021", source.name, "-O", "-o", str(binary)]

started = time.perf_counter()
if not source.is_file():
    record = {"ok": False, "compile_ok": False, "source": "", "message": f"missing {source}"}
    Path(".benchmark_attempts.jsonl").open("a").write(json.dumps(record) + "\n")
    print(record["message"], file=sys.stderr)
    raise SystemExit(1)

compiled = subprocess.run(compile_command, capture_output=True, text=True, timeout=120)
case_results = []
if compiled.returncode == 0:
    run_command = [sys.executable, source.name] if language == "python" else [str(binary)]
    for index, case in enumerate(config["public_cases"], 1):
        expected_files = case.get("files", {})
        for filename in expected_files:
            output_path = Path(filename)
            if output_path.is_file() or output_path.is_symlink():
                output_path.unlink()
        proc = subprocess.run(
            run_command,
            input=case["stdin"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        actual_files = {
            filename: Path(filename).read_text(encoding="utf-8") if Path(filename).is_file() else None
            for filename in expected_files
        }
        files_ok = all(actual_files[name] == content for name, content in expected_files.items())
        case_results.append({
            "case": index,
            "ok": proc.returncode == 0 and proc.stdout == case["stdout"] and files_ok,
            "returncode": proc.returncode,
            "expected_stdout": case["stdout"],
            "actual_stdout": proc.stdout,
            "expected_files": expected_files,
            "actual_files": actual_files,
            "stderr": proc.stderr,
        })

ok = compiled.returncode == 0 and all(case["ok"] for case in case_results)
record = {
    "ok": ok,
    "compile_ok": compiled.returncode == 0,
    "compile_returncode": compiled.returncode,
    "compile_stdout": compiled.stdout,
    "compile_stderr": compiled.stderr,
    "cases": case_results,
    "source": source.read_text(),
    "elapsed_seconds": round(time.perf_counter() - started, 4),
}
with Path(".benchmark_attempts.jsonl").open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(record, sort_keys=True) + "\n")

if compiled.stdout:
    print(compiled.stdout, end="")
if compiled.stderr:
    print(compiled.stderr, end="", file=sys.stderr)
for case in case_results:
    if not case["ok"]:
        print(f"public case {case['case']} failed", file=sys.stderr)
        print(f"expected stdout: {case['expected_stdout']!r}", file=sys.stderr)
        print(f"actual stdout:   {case['actual_stdout']!r}", file=sys.stderr)
        for filename, expected in case.get("expected_files", {}).items():
            actual = case.get("actual_files", {}).get(filename)
            if actual != expected:
                print(f"expected file {filename}: {expected!r}", file=sys.stderr)
                print(f"actual file {filename}:   {actual!r}", file=sys.stderr)
        if case["stderr"]:
            print(f"stderr: {case['stderr']}", file=sys.stderr)
if ok:
    print(f"public checks passed for {source}")
raise SystemExit(0 if ok else 1)
'''


def write_workspace(
    workdir: Path,
    task: dict[str, Any],
    language: str,
    parley_command: str,
) -> dict[str, str]:
    config = {
        "language": language,
        "source": source_name(language),
        "parley_command": parley_command,
        "public_cases": task["public_cases"],
    }
    files = {
        ".benchmark_public.json": json.dumps(config, indent=2) + "\n",
        "check_public.py": PUBLIC_CHECK_SCRIPT,
        "check": "#!/bin/sh\nexec python3 check_public.py\n",
    }
    for name, content in files.items():
        path = workdir / name
        path.write_text(content, encoding="utf-8")
        if name in {"check", "check_public.py"}:
            path.chmod(0o755)
    return {name: hashlib.sha256(content.encode()).hexdigest() for name, content in files.items()}


def render_prompt(
    task: dict[str, Any],
    language: str,
    parley_skill: str,
) -> str:
    examples = []
    for index, case in enumerate(task["public_cases"], 1):
        examples.extend([
            f"Public example {index} input:",
            "```text",
            case["stdin"].rstrip("\n"),
            "```",
            f"Public example {index} output:",
            "```text",
            case["stdout"].rstrip("\n"),
            "```",
            "",
        ])
    label = {"parley": "Parley", "python": "Python", "rust": "Rust"}[language]
    lines = [
        "You are participating in a controlled coding benchmark in a fresh workspace.",
        f"Implement the task in {label} by creating `{source_name(language)}`.",
        "Work only inside the current directory. All information needed is in this prompt.",
        "Do not list, read, or inspect any existing workspace file, including checker/config files.",
        "Do not use the internet or modify checker/config files.",
        f"Your first tool action must create `{source_name(language)}`. Do not perform reconnaissance first.",
        "After creating or editing the solution, the only shell command permitted is exactly `./check`.",
        "Do not invoke a global language command.",
        "After writing the solution, run `./check`. If it fails, use its feedback to repair the",
        "program and run `./check` again. Continue until it passes or you cannot make progress.",
        "The final answer should briefly state whether the public check passed.",
        "",
        f"# Task: {task['title']}",
        "",
        task["statement"],
        "",
        *examples,
    ]
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
            "Use only the Python standard library. The checker compiles the file and runs the public cases.",
            "",
        ])
    else:
        lines.extend([
            "Use only the Rust standard library. The checker compiles with rustc edition 2021 and runs the public cases.",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def parse_codex_events(stdout: str) -> dict[str, Any]:
    thread_id = None
    usage = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0,
             "reasoning_output_tokens": 0}
    agent_messages = []
    command_events = []
    errors = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type")
        if event_type == "thread.started":
            thread_id = event.get("thread_id")
        elif event_type == "turn.completed":
            for key, value in (event.get("usage") or {}).items():
                if key in usage:
                    usage[key] += int(value or 0)
        elif event_type == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message":
                agent_messages.append(str(item.get("text", "")))
            elif item.get("type") == "command_execution":
                command_events.append(item)
            elif item.get("type") == "error":
                errors.append(str(item.get("message", "")))
    return {
        "thread_id": thread_id,
        "usage": usage,
        "agent_messages": agent_messages,
        "command_events": command_events,
        "errors": errors,
    }


_ALLOWED_CHECK_COMMAND = re.compile(
    r"^(?:/bin/(?:zsh|sh)\s+-lc\s+)?[\"']?\./check[\"']?$"
)
_ALLOWED_SOURCES_COMMAND = re.compile(
    r"^(?:/bin/(?:zsh|sh)\s+-lc\s+)?[\"']?\./sources[\"']?$"
)


def command_protocol(
    command_events: list[dict[str, Any]], *, allow_sources: bool = False
) -> dict[str, Any]:
    """Require shell activity to be exactly the supplied public checker."""
    commands = [str(event.get("command", "")).strip() for event in command_events]
    allowed = [_ALLOWED_CHECK_COMMAND]
    if allow_sources:
        allowed.append(_ALLOWED_SOURCES_COMMAND)
    violations = [
        command for command in commands
        if not any(pattern.fullmatch(command) for pattern in allowed)
    ]
    if allow_sources:
        source_commands = [
            command for command in commands if _ALLOWED_SOURCES_COMMAND.fullmatch(command)
        ]
        if len(source_commands) != 1:
            violations.append(
                f"expected exactly one ./sources command, observed {len(source_commands)}"
            )
        if commands and not _ALLOWED_SOURCES_COMMAND.fullmatch(commands[0]):
            violations.append("first shell command was not ./sources")
        if not any(_ALLOWED_CHECK_COMMAND.fullmatch(command) for command in commands):
            violations.append("no ./check command observed")
    return {
        "compliant": bool(commands) and not violations,
        "commands": commands,
        "violations": violations,
    }


def read_attempts(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def run_cell(
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
    task = cell["task"]
    language = cell["language"]
    replicate = cell["replicate"]
    workdir = Path(tempfile.mkdtemp(
        prefix=f"{task['id']}-{language}-r{replicate}-",
        dir=work_root,
    ))
    integrity = write_workspace(workdir, task, language, parley_command)
    prompt = render_prompt(task, language, parley_skill)
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
    command_compliance = command_protocol(parsed["command_events"])
    source = workdir / source_name(language)
    hidden = (
        judge(language, source, task["hidden_cases"], parley_command)
        if source.is_file()
        else {"ok": False, "compile": {"ok": False, "stderr": "solution file missing"}, "cases": []}
    )
    attempts = read_attempts(workdir / CHECK_LOG)
    integrity_ok = all(
        (workdir / name).is_file()
        and hashlib.sha256((workdir / name).read_bytes()).hexdigest() == digest
        for name, digest in integrity.items()
    )
    source_text = source.read_text(encoding="utf-8") if source.is_file() else ""
    usage = parsed["usage"]
    return {
        "schema_version": 1,
        "recorded_at": utc_now(),
        "task_id": task["id"],
        "task_title": task["title"],
        "language": language,
        "replicate": replicate,
        "model": model,
        "reasoning_effort": reasoning,
        "fresh_ephemeral_session": True,
        "workdir": str(workdir),
        "thread_id": parsed["thread_id"],
        "agent_returncode": returncode,
        "agent_timed_out": timed_out,
        "elapsed_seconds": elapsed,
        "check_integrity_ok": integrity_ok,
        "command_protocol_compliant": command_compliance["compliant"],
        "command_protocol_violations": command_compliance["violations"],
        "public_check_attempts": len(attempts),
        "first_public_check_success": bool(attempts and attempts[0].get("ok")),
        "final_public_check_success": bool(attempts and attempts[-1].get("ok")),
        "repair_turns": max(len(attempts) - 1, 0),
        "hidden_success": bool(hidden["ok"]),
        "usage": usage,
        "total_tokens": usage["input_tokens"] + usage["output_tokens"],
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_chars": len(prompt),
        "source_text": source_text,
        "source_chars": len(source_text),
        "source_lines": len(source_text.splitlines()),
        "source_rough_tokens": len(ROUGH_TOKEN_RE.findall(source_text)),
        "public_attempts": attempts,
        "hidden_judgment": hidden,
        "agent_messages": parsed["agent_messages"],
        "agent_errors": parsed["errors"],
        "command_events": parsed["command_events"],
        "codex_stdout": stdout,
        "codex_stderr": stderr,
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_language: dict[str, Any] = {}
    for language in LANGUAGES:
        rows = [row for row in results if row["language"] == language]
        if not rows:
            continue
        successes = sum(bool(row["hidden_success"]) for row in rows)
        first_public = sum(bool(row["first_public_check_success"]) for row in rows)
        protocol_compliant = sum(bool(row.get("command_protocol_compliant")) for row in rows)
        token_values = [int(row["total_tokens"]) for row in rows]
        elapsed_values = [float(row["elapsed_seconds"]) for row in rows]
        attempt_values = [int(row["public_check_attempts"]) for row in rows]
        input_values = [int(row.get("usage", {}).get("input_tokens", 0)) for row in rows]
        cached_values = [int(row.get("usage", {}).get("cached_input_tokens", 0)) for row in rows]
        uncached_values = [
            max(input_tokens - cached_tokens, 0)
            for input_tokens, cached_tokens in zip(input_values, cached_values)
        ]
        output_values = [int(row.get("usage", {}).get("output_tokens", 0)) for row in rows]
        by_language[language] = {
            "runs": len(rows),
            "hidden_successes": successes,
            "hidden_success_rate": round(successes / len(rows), 4),
            "first_public_check_successes": first_public,
            "first_public_check_success_rate": round(first_public / len(rows), 4),
            "command_protocol_compliant_runs": protocol_compliant,
            "command_protocol_compliance_rate": round(protocol_compliant / len(rows), 4),
            "median_public_check_attempts": statistics.median(attempt_values),
            "median_total_tokens": statistics.median(token_values),
            "total_tokens": sum(token_values),
            "median_input_tokens": statistics.median(input_values),
            "median_cached_input_tokens": statistics.median(cached_values),
            "median_uncached_input_tokens": statistics.median(uncached_values),
            "median_output_tokens": statistics.median(output_values),
            "median_prompt_chars": statistics.median(
                int(row.get("prompt_chars", 0)) for row in rows
            ),
            "median_source_lines": statistics.median(
                int(row.get("source_lines", 0)) for row in rows
            ),
            "median_source_rough_tokens": statistics.median(
                int(row.get("source_rough_tokens", 0)) for row in rows
            ),
            "median_elapsed_seconds": round(statistics.median(elapsed_values), 4),
        }
    per_task = []
    for task_id in sorted({row["task_id"] for row in results}):
        for language in LANGUAGES:
            rows = [row for row in results if row["task_id"] == task_id and row["language"] == language]
            if rows:
                per_task.append({
                    "task_id": task_id,
                    "language": language,
                    "runs": len(rows),
                    "hidden_successes": sum(bool(row["hidden_success"]) for row in rows),
                    "first_public_check_successes": sum(bool(row["first_public_check_success"]) for row in rows),
                    "median_total_tokens": statistics.median(int(row["total_tokens"]) for row in rows),
                })
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "runs": len(results),
        "by_language": by_language,
        "per_task": per_task,
    }


def rejudge_report(
    report: dict[str, Any],
    task_map: dict[str, dict[str, Any]],
    parley_command: str,
    note: str,
) -> dict[str, Any]:
    for row in report.get("results", []):
        task_id = str(row.get("task_id", ""))
        language = str(row.get("language", ""))
        task = task_map.get(task_id)
        workdir = Path(str(row.get("workdir", "")))
        source = workdir / source_name(language) if language in EXTENSIONS else workdir
        if task is None or language not in EXTENSIONS or not source.is_file():
            row["hidden_success"] = False
            row["hidden_judgment"] = {
                "ok": False,
                "compile": {"ok": False, "stderr": "cannot rejudge missing task or source"},
                "cases": [],
            }
            continue
        hidden = judge(language, source, task["hidden_cases"], parley_command)
        row["hidden_success"] = bool(hidden["ok"])
        row["hidden_judgment"] = hidden
        source_text = source.read_text(encoding="utf-8")
        row["source_chars"] = len(source_text)
        row["source_lines"] = len(source_text.splitlines())
        row["source_rough_tokens"] = len(ROUGH_TOKEN_RE.findall(source_text))
    report["generated_at"] = utc_now()
    protocol = report.setdefault("protocol", {})
    rejudgments = protocol.setdefault("rejudgments", [])
    if not any(item.get("note") == note for item in rejudgments):
        rejudgments.append({"at": utc_now(), "note": note})
    report["summary"] = summarize(report.get("results", []))
    return report


def parse_csv(value: str, allowed: set[str]) -> list[str]:
    values = [item.strip() for item in value.split(",") if item.strip()]
    unknown = [item for item in values if item not in allowed]
    if not values or unknown:
        raise ValueError(f"invalid selection {unknown or values}; allowed: {', '.join(sorted(allowed))}")
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run fresh Codex sessions on held-out tasks.")
    parser.add_argument("--tasks-file", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--tasks", help="comma-separated task ids; default: all")
    parser.add_argument("--languages", default=",".join(LANGUAGES))
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--reasoning", default=REASONING_DEFAULT)
    parser.add_argument("--codex-command", default=shutil.which("codex") or "codex")
    parser.add_argument("--parley-command", required=True)
    parser.add_argument("--parley-skill", type=Path, default=DEFAULT_SKILL)
    parser.add_argument("--timeout", type=int, default=480)
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260729)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--rejudge-report", type=Path,
                        help="re-run hidden judgments for a saved report without new agent calls")
    parser.add_argument("--rejudge-note", default="Hidden cases rejudged from the current manifest.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        all_tasks = load_tasks(args.tasks_file)
        task_map = {task["id"]: task for task in all_tasks}
        task_ids = (
            parse_csv(args.tasks, set(task_map)) if args.tasks else list(task_map)
        )
        languages = parse_csv(args.languages, set(LANGUAGES))
        if args.replicates < 1 or args.max_workers < 1:
            raise ValueError("replicates and max-workers must be positive")
        parley_skill = args.parley_skill.read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"agent benchmark error: {exc}", file=sys.stderr)
        return 1

    if args.rejudge_report:
        try:
            report = json.loads(args.rejudge_report.read_text(encoding="utf-8"))
            report = rejudge_report(report, task_map, args.parley_command, args.rejudge_note)
            metadata = protocol_metadata(
                args.tasks_file, args.parley_skill, args.codex_command, args.parley_command
            )
            for key, value in metadata.items():
                report["protocol"].setdefault(key, value)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"agent benchmark rejudge error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(report["summary"], indent=2))
        print(f"rejudged {len(report.get('results', []))} runs into {args.output}")
        return 0

    work_root = args.work_root or Path(tempfile.mkdtemp(prefix="parley-agent-pilot-"))
    work_root.mkdir(parents=True, exist_ok=True)
    cells = [
        {"task": task_map[task_id], "language": language, "replicate": replicate}
        for replicate in range(1, args.replicates + 1)
        for task_id in task_ids
        for language in languages
    ]
    random.Random(args.seed).shuffle(cells)
    print(
        f"running {len(cells)} fresh sessions with {args.model} ({args.reasoning}); "
        f"work root: {work_root}",
        flush=True,
    )

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {
            pool.submit(
                run_cell,
                cell,
                codex_command=args.codex_command,
                model=args.model,
                reasoning=args.reasoning,
                parley_command=args.parley_command,
                parley_skill=parley_skill,
                timeout=args.timeout,
                work_root=work_root,
            ): cell
            for cell in cells
        }
        for future in concurrent.futures.as_completed(futures):
            cell = futures[future]
            try:
                row = future.result()
            except Exception as exc:  # preserve the rest of a paid pilot if one cell fails
                row = {
                    "schema_version": 1,
                    "recorded_at": utc_now(),
                    "task_id": cell["task"]["id"],
                    "language": cell["language"],
                    "replicate": cell["replicate"],
                    "model": args.model,
                    "runner_error": repr(exc),
                    "hidden_success": False,
                    "first_public_check_success": False,
                    "public_check_attempts": 0,
                    "total_tokens": 0,
                    "elapsed_seconds": 0,
                }
            results.append(row)
            print(
                f"completed {row['task_id']} {row['language']} r{row['replicate']}: "
                f"hidden={'PASS' if row.get('hidden_success') else 'FAIL'} "
                f"checks={row.get('public_check_attempts', 0)} "
                f"tokens={row.get('total_tokens', 0)}",
                flush=True,
            )

    results.sort(key=lambda row: (row["task_id"], row["language"], row["replicate"]))
    report = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "protocol": {
            "model": args.model,
            "reasoning_effort": args.reasoning,
            "replicates": args.replicates,
            "seed": args.seed,
            "fresh_ephemeral_sessions": True,
            "user_config_ignored": True,
            "internet_for_agent_tools": False,
            "parley_skill_included_and_metered": True,
            "hidden_cases_withheld_until_final_judgment": True,
            "workspace_inspection_prohibited": True,
            "only_shell_command_permitted": "./check",
            "task_ids": task_ids,
            "languages": languages,
            "work_root": str(work_root),
            **protocol_metadata(
                args.tasks_file, args.parley_skill, args.codex_command, args.parley_command
            ),
        },
        "summary": summarize(results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2), flush=True)
    print(f"wrote {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
