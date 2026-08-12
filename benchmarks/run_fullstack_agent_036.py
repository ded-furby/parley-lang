#!/usr/bin/env python3
"""Validate and run preregistered fresh-agent full-stack study 036."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import http.client
import json
import os
import random
import re
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

try:
    from .agent_runner import parse_codex_events, utc_now
    from .fullstack_agent_036_scaffolds import (
        LANGUAGES,
        ROOT_FILES,
        ScaffoldFile,
        load_task_map,
        scaffold_files,
    )
except ImportError:
    from agent_runner import parse_codex_events, utc_now
    from fullstack_agent_036_scaffolds import (
        LANGUAGES,
        ROOT_FILES,
        ScaffoldFile,
        load_task_map,
        scaffold_files,
    )


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
PROTOCOL_PATH = BENCHMARKS / "fullstack_agent_036_protocol.json"
CASES_PATH = BENCHMARKS / "fullstack_agent_036_cases.json"
SKILL_PATH = REPO / "skill/parley/SKILL.md"
WEB_REFERENCE_PATH = REPO / "docs/WEB.md"
ATTEMPT_LOG = ".benchmark_attempts.jsonl"
PYTHON_RUNTIME = Path(
    os.environ.get(
        "FULLSTACK_036_PYTHON",
        "/private/tmp/parley-fullstack-036-python/bin/python",
    )
)
TS_DEPENDENCY_ROOT = Path(
    os.environ.get("FULLSTACK_036_TYPESCRIPT", "/private/tmp/parley-fullstack-036-typescript")
)
TS_COMPILER = TS_DEPENDENCY_ROOT / "node_modules/.bin/tsc"
TS_MODULES = TS_DEPENDENCY_ROOT / "node_modules"
ROUGH_TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_']*|\d+\.\d+|\d+|==|!=|<=|>=|[^\s]",
    re.ASCII,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def load_protocol(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    protocol = json.loads(path.read_text(encoding="utf-8"))
    if protocol.get("schema_version") != 1 or protocol.get("experiment_id") != "036":
        raise ValueError("full-stack agent protocol must be schema 1 / experiment 036")
    frozen = protocol["frozen_product"]
    for file_key, sha_key in (
        ("tasks_file", "tasks_sha256"),
        ("cases_file", "cases_sha256"),
        ("parley_skill_file", "parley_skill_sha256"),
        ("parley_web_reference_file", "parley_web_reference_sha256"),
    ):
        path_value = REPO / frozen[file_key]
        if digest(path_value) != frozen[sha_key]:
            raise ValueError(f"frozen hash mismatch for {frozen[file_key]}")
    config = protocol["frozen_config"]
    if tuple(config["languages"]) != LANGUAGES:
        raise ValueError(f"languages must be {list(LANGUAGES)}")
    configurations = config["agent_configurations"]
    if not configurations or len({row["id"] for row in configurations}) != len(configurations):
        raise ValueError("agent configurations must be non-empty with unique ids")
    for row in configurations:
        if set(row) != {"id", "model", "reasoning"} or not all(row.values()):
            raise ValueError("invalid agent configuration")
    for field in (
        "replicates_per_task_language_configuration",
        "seed",
        "timeout_seconds",
        "max_workers",
    ):
        if not isinstance(config[field], int) or config[field] < 1:
            raise ValueError(f"{field} must be a positive integer")
    return protocol


def load_cases() -> dict[str, list[dict[str, Any]]]:
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or payload.get("experiment_id") != "036":
        raise ValueError("full-stack cases must be schema 1 / experiment 036")
    return payload["tasks"]


def validate_corpus() -> dict[str, Any]:
    protocol = load_protocol()
    task_map = load_task_map()
    cases = load_cases()
    if set(task_map) != set(cases):
        raise ValueError("task and case ids differ")
    total_public = total_hidden = 0
    for task_id, task in task_map.items():
        rows = cases[task_id]
        ids = [row.get("id") for row in rows]
        if len(ids) != len(set(ids)) or any(not value for value in ids):
            raise ValueError(f"{task_id}: case ids must be non-empty and unique")
        public = [row["id"] for row in rows if row.get("visibility") == "public"]
        hidden = [row["id"] for row in rows if row.get("visibility") == "hidden"]
        if public != task["public_case_ids"] or hidden != task["hidden_case_ids"]:
            raise ValueError(f"{task_id}: case visibility lists do not match task manifest")
        if len(public) != 3 or len(hidden) != 5:
            raise ValueError(f"{task_id}: expected three public and five hidden cases")
        if not any(row.get("target") == "browser" for row in rows):
            raise ValueError(f"{task_id}: no browser case")
        if task["kind"] == "maintenance" and not task.get("root_cause_role"):
            raise ValueError(f"{task_id}: maintenance task needs a root cause role")
        total_public += len(public)
        total_hidden += len(hidden)
    config = protocol["frozen_config"]
    expected_sessions = (
        len(task_map)
        * len(LANGUAGES)
        * len(config["agent_configurations"])
        * config["replicates_per_task_language_configuration"]
    )
    matrix = protocol["matrix"]
    if matrix["fresh_sessions"] != expected_sessions:
        raise ValueError("frozen matrix session count is inconsistent")
    if matrix["public_case_executions"] != expected_sessions * 3:
        raise ValueError("public execution count is inconsistent")
    if matrix["hidden_case_executions"] != expected_sessions * 5:
        raise ValueError("hidden execution count is inconsistent")
    return {
        "tasks": len(task_map),
        "cases": total_public + total_hidden,
        "public_cases": total_public,
        "hidden_cases": total_hidden,
        "sessions": expected_sessions,
    }


def build_plan(
    tasks: list[dict[str, Any]],
    languages: list[str],
    configurations: list[dict[str, str]],
    replicates: int,
    seed: int,
) -> list[dict[str, Any]]:
    cells = [
        {
            "task": task,
            "task_id": task["id"],
            "task_kind": task["kind"],
            "language": language,
            "configuration": configuration,
            "configuration_id": configuration["id"],
            "replicate": replicate,
        }
        for task in tasks
        for language in languages
        for configuration in configurations
        for replicate in range(1, replicates + 1)
    ]
    random.Random(seed).shuffle(cells)
    return cells


def _write_files(workspace: Path, files: dict[str, ScaffoldFile]) -> None:
    for name, spec in files.items():
        path = workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(spec.text, encoding="utf-8")


def _source_manifest(files: dict[str, ScaffoldFile]) -> dict[str, Any]:
    return {
        "visible_files": sorted(files),
        "editable_files": sorted(name for name, spec in files.items() if spec.editable),
        "read_only_files": sorted(name for name, spec in files.items() if not spec.editable),
    }


def write_workspace(
    workspace: Path,
    task: dict[str, Any],
    language: str,
    parley_command: str,
    *,
    variant: str = "seed",
) -> dict[str, Any]:
    files = scaffold_files(task, language, variant)
    _write_files(workspace, files)
    manifest = _source_manifest(files)
    protected = {
        ".benchmark_source.json": json.dumps(manifest, indent=2) + "\n",
        ".benchmark_config.json": json.dumps(
            {
                "task_id": task["id"],
                "language": language,
                "parley_command": str(Path(parley_command).resolve()),
            },
            indent=2,
        )
        + "\n",
        "print_sources.py": _source_script(),
        "sources": "#!/bin/sh\nexec python3 print_sources.py\n",
        "check": (
            "#!/bin/sh\nexec python3 "
            f"{Path(__file__).resolve()} internal-check --workspace . --visibility public\n"
        ),
    }
    for name, text in protected.items():
        path = workspace / name
        path.write_text(text, encoding="utf-8")
        if name in {"sources", "check", "print_sources.py"}:
            path.chmod(0o755)
    if language == "typescript":
        modules = workspace / "node_modules"
        if modules.exists() or modules.is_symlink():
            modules.unlink()
        modules.symlink_to(TS_MODULES, target_is_directory=True)
    return {
        "source": manifest,
        "protected_hashes": {
            name: hashlib.sha256(text.encode()).hexdigest()
            for name, text in protected.items()
        },
        "seed_hashes": {
            name: hashlib.sha256(spec.text.encode()).hexdigest()
            for name, spec in files.items()
        },
    }


def _source_script() -> str:
    return '''#!/usr/bin/env python3
import json
from pathlib import Path
config = json.loads(Path(".benchmark_source.json").read_text())
read_only = set(config["read_only_files"])
for name in config["visible_files"]:
    marker = " [read-only]" if name in read_only else " [editable]"
    print(f"===== {name}{marker} =====")
    text = Path(name).read_text(encoding="utf-8")
    print(text, end="" if text.endswith("\\n") else "\\n")
'''


def _reset(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def build_application(
    workspace: Path,
    language: str,
    parley_command: str,
) -> dict[str, Any]:
    output = workspace / ".benchmark_build"
    _reset(output)
    started = time.perf_counter()
    env = {**os.environ, "CARGO_NET_OFFLINE": "true"}
    try:
        if language == "parley":
            run(
                [parley_command, "web", "build", str(workspace), "-o", str(output / "bundle")],
                cwd=workspace,
                env=env,
                timeout=300,
            )
        elif language == "python":
            if not PYTHON_RUNTIME.is_file():
                raise RuntimeError(f"missing frozen Python runtime: {PYTHON_RUNTIME}")
            run(
                [str(PYTHON_RUNTIME), "-m", "py_compile", "app.py", "logic.py"],
                cwd=workspace,
            )
            run(["node", "--check", "browser.js"], cwd=workspace)
        elif language == "typescript":
            if not TS_COMPILER.is_file() or not TS_MODULES.is_dir():
                raise RuntimeError("missing frozen TypeScript dependency installation")
            run(
                [str(TS_COMPILER), "-p", "tsconfig.json", "--outDir", str(output / "dist")],
                cwd=workspace,
            )
        elif language == "rust":
            rust_env = {**env, "CARGO_TARGET_DIR": str(output / "target")}
            run(["cargo", "build", "--release"], cwd=workspace, env=rust_env, timeout=600)
            run(
                ["cargo", "build", "--release", "--lib", "--target", "wasm32-unknown-unknown"],
                cwd=workspace,
                env=rust_env,
                timeout=600,
            )
        else:
            raise ValueError(f"unsupported language: {language}")
        return {
            "ok": True,
            "error": "",
            "elapsed_seconds": round(time.perf_counter() - started, 4),
        }
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "error": str(exc),
            "elapsed_seconds": round(time.perf_counter() - started, 4),
        }


def allocate_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def server_spec(workspace: Path, language: str, port: int) -> tuple[list[str], dict[str, str], Path]:
    output = workspace / ".benchmark_build"
    env = {**os.environ, "PARLEY_WEB_PORT": str(port)}
    if language == "parley":
        return [str(output / "bundle/server")], env, output / "bundle"
    if language == "python":
        return [str(PYTHON_RUNTIME), "app.py"], env, workspace
    if language == "typescript":
        env["FULLSTACK_036_BROWSER"] = str(output / "dist/logic.js")
        return ["node", str(output / "dist/server.js")], env, workspace
    env["FULLSTACK_036_WASM"] = str(
        output / "target/wasm32-unknown-unknown/release/fullstack_agent_036.wasm"
    )
    return [str(output / "target/release/fullstack-agent-036")], env, workspace


def request(port: int, case: dict[str, Any]) -> dict[str, Any]:
    headers: dict[str, str] = {}
    body: bytes | None = None
    if "json" in case:
        body = json.dumps(case["json"], separators=(",", ":")).encode()
        headers["content-type"] = "application/json"
    elif "raw_body" in case:
        body = case["raw_body"].encode()
        headers["content-type"] = case.get("content_type", "application/octet-stream")
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request(case["method"], case["path"], body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        content_type = response.getheader("content-type", "")
    finally:
        connection.close()
    actual: dict[str, Any] = {
        "status": response.status,
        "content_type": content_type,
        "body": raw.decode("utf-8", errors="replace")[:1000],
    }
    try:
        actual["json"] = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    passed = actual["status"] == case["expected_status"]
    if "expected_json" in case:
        passed = passed and actual.get("json") == case["expected_json"]
    if "expected_error" in case:
        passed = passed and actual.get("json", {}).get("error") == case["expected_error"]
    actual["pass"] = passed
    return actual


def browser_value(port: int, export: str, args: list[Any]) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{port}/", wait_until="domcontentloaded")
            value = page.evaluate(
                """async ({name, args}) => {
                    const module = await import(`/parley.js?run=${Date.now()}`);
                    const api = await module.loadParley();
                    const result = await api[name](...args);
                    return typeof result === "bigint" ? Number(result) : result;
                }""",
                {"name": export, "args": args},
            )
            browser.close()
        return {
            "ok": True,
            "value": value,
            "error": "",
            "elapsed_seconds": round(time.perf_counter() - started, 4),
        }
    except Exception as exc:
        return {
            "ok": False,
            "value": None,
            "error": str(exc),
            "elapsed_seconds": round(time.perf_counter() - started, 4),
        }


def start_server(workspace: Path, language: str, task: dict[str, Any]) -> tuple[subprocess.Popen[str], int]:
    port = allocate_port()
    command, env, cwd = server_spec(workspace, language, port)
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 30
    status_case = {
        "method": "GET",
        "path": task["status_route"],
        "expected_status": 200,
        "expected_json": {"service": task["service"], "ready": True},
    }
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(f"server exited early\nstdout:\n{stdout}\nstderr:\n{stderr}")
        try:
            if request(port, status_case)["pass"]:
                return process, port
        except OSError:
            time.sleep(0.02)
    stop_server(process)
    raise RuntimeError(f"{language} server did not become ready")


def stop_server(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def evaluate_application(
    workspace: Path,
    task: dict[str, Any],
    language: str,
    cases: list[dict[str, Any]],
    parley_command: str,
) -> dict[str, Any]:
    build = build_application(workspace, language, parley_command)
    if not build["ok"]:
        return {"ok": False, "build": build, "cases": [], "cross_target": None}
    process: subprocess.Popen[str] | None = None
    try:
        process, port = start_server(workspace, language, task)
        rows = []
        for case in cases:
            if case["target"] == "http":
                actual = request(port, case)
            else:
                actual = browser_value(port, case["export"], case["args"])
                actual["pass"] = actual["ok"] and actual["value"] == case["expected"]
            rows.append({"id": case["id"], "target": case["target"], **actual})
        public_post = next(
            (
                case
                for case in cases
                if case["target"] == "http"
                and case.get("expected_status") == 200
                and case.get("method") == "POST"
            ),
            None,
        )
        cross_target = None
        if public_post is not None:
            args = [public_post["json"][name] for name in task["request_fields"]]
            cross_target = browser_value(port, task["browser_export"], args)
            expected = public_post["expected_json"][task["shared_result_field"]]
            cross_target["expected"] = expected
            cross_target["pass"] = cross_target["ok"] and cross_target["value"] == expected
        passed = all(row["pass"] for row in rows) and (
            cross_target is None or cross_target["pass"]
        )
        return {"ok": passed, "build": build, "cases": rows, "cross_target": cross_target}
    except Exception as exc:
        return {
            "ok": False,
            "build": build,
            "cases": [],
            "cross_target": None,
            "runtime_error": str(exc),
        }
    finally:
        if process is not None:
            stop_server(process)


def source_snapshot(workspace: Path) -> dict[str, Any]:
    config = json.loads((workspace / ".benchmark_source.json").read_text())
    files = {}
    for name in config["editable_files"]:
        path = workspace / name
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        files[name] = {
            "text": text,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "bytes": len(text.encode()),
            "lines": len(text.splitlines()),
            "rough_tokens": len(ROUGH_TOKEN_RE.findall(text)),
        }
    return {"editable_files": files}


def internal_check(workspace: Path, visibility: str) -> int:
    config = json.loads((workspace / ".benchmark_config.json").read_text())
    task = load_task_map()[config["task_id"]]
    rows = [
        case
        for case in load_cases()[task["id"]]
        if case["visibility"] == visibility
    ]
    result = evaluate_application(
        workspace,
        task,
        config["language"],
        rows,
        config["parley_command"],
    )
    record = {**result, "source": source_snapshot(workspace)}
    with (workspace / ATTEMPT_LOG).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    if result["ok"]:
        print(f"public full-stack checks passed for {task['id']}")
        return 0
    print(f"public full-stack checks failed for {task['id']}", file=sys.stderr)
    if not result["build"]["ok"]:
        print(result["build"]["error"], file=sys.stderr)
    for row in result.get("cases", []):
        if not row["pass"]:
            print(f"{row['id']} failed: {json.dumps(row, sort_keys=True)}", file=sys.stderr)
    cross = result.get("cross_target")
    if cross and not cross["pass"]:
        print(f"public browser/HTTP agreement failed: {json.dumps(cross, sort_keys=True)}", file=sys.stderr)
    if result.get("runtime_error"):
        print(result["runtime_error"], file=sys.stderr)
    return 1


def render_prompt(
    task: dict[str, Any],
    cases: list[dict[str, Any]],
    language: str,
    skill: str,
    web_reference: str,
) -> str:
    labels = {
        "parley": "Parley",
        "python": "Python",
        "typescript": "TypeScript",
        "rust": "Rust",
    }
    public = [row for row in cases if row["visibility"] == "public"]
    lines = [
        "You are participating in a controlled coding benchmark in a fresh workspace.",
        f"Complete one {labels[language]} full-stack assignment using the supplied scaffold.",
        "Work only inside the current directory. Do not use the internet or inspect protected benchmark files.",
        "Your first shell command must be exactly `./sources`; run it once to see all editable and read-only files.",
        "After that, the only shell command permitted is exactly `./check`.",
        "You may edit only files marked editable. Do not modify checker, source-printer, config, lock, or read-only files.",
        "Run `./check` after editing. Use its public feedback to repair the application until it passes or you cannot progress.",
        "Your final response should briefly state whether the complete public full-stack check passed.",
        "",
        f"# {task['title']}",
        "",
        task["statement"],
        "",
        f"HTTP: `GET {task['status_route']}` and `POST {task['post_route']}`.",
        f"Browser export: `{task['browser_export']}`; shared response field: `{task['shared_result_field']}`.",
        "",
        "Public cases:",
        "```json",
        json.dumps(public, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    if language == "parley":
        lines.extend(
            [
                "# Frozen Parley skill",
                "",
                skill.rstrip(),
                "",
                "# Frozen Parley typed-web reference",
                "",
                web_reference.rstrip(),
                "",
            ]
        )
    else:
        stack = {
            "python": "Use the supplied FastAPI/Pydantic application and browser JavaScript module.",
            "typescript": "Use the supplied Hono/Zod TypeScript application; one logic module serves native and browser paths.",
            "rust": "Use the supplied Axum/Serde Rust application; the library is also compiled to WebAssembly.",
        }[language]
        lines.extend([stack, "Dependencies are already installed and must not be changed.", ""])
    return "\n".join(lines).rstrip() + "\n"


_ALLOWED_SOURCE = re.compile(r"^(?:/bin/(?:zsh|sh)\s+-lc\s+)?[\"']?\./sources[\"']?$")
_ALLOWED_CHECK = re.compile(r"^(?:/bin/(?:zsh|sh)\s+-lc\s+)?[\"']?\./check[\"']?$")


def command_protocol(events: list[dict[str, Any]]) -> dict[str, Any]:
    commands = [str(event.get("command", "")).strip() for event in events]
    violations = [
        command
        for command in commands
        if not _ALLOWED_SOURCE.fullmatch(command) and not _ALLOWED_CHECK.fullmatch(command)
    ]
    source_count = sum(bool(_ALLOWED_SOURCE.fullmatch(command)) for command in commands)
    check_count = sum(bool(_ALLOWED_CHECK.fullmatch(command)) for command in commands)
    if source_count != 1:
        violations.append(f"expected exactly one ./sources, observed {source_count}")
    if commands and not _ALLOWED_SOURCE.fullmatch(commands[0]):
        violations.append("first shell command was not ./sources")
    if check_count < 1:
        violations.append("no ./check command observed")
    return {"compliant": bool(commands) and not violations, "commands": commands, "violations": violations}


def _read_attempts(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _integrity(workspace: Path, hashes: dict[str, str]) -> bool:
    return all(
        (workspace / name).is_file() and digest(workspace / name) == expected
        for name, expected in hashes.items()
    )


def run_cell(
    cell: dict[str, Any],
    *,
    codex_command: str,
    parley_command: str,
    work_root: Path,
    timeout: int,
) -> dict[str, Any]:
    task = cell["task"]
    language = cell["language"]
    config = cell["configuration"]
    workspace = Path(
        tempfile.mkdtemp(
            prefix=f"036-{task['id']}-{language}-{config['id']}-r{cell['replicate']}-",
            dir=work_root,
        )
    )
    written = write_workspace(workspace, task, language, parley_command)
    prompt = render_prompt(
        task,
        load_cases()[task["id"]],
        language,
        SKILL_PATH.read_text(),
        WEB_REFERENCE_PATH.read_text(),
    )
    (workspace / "prompt.md").write_text(prompt, encoding="utf-8")
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
        "-m", config["model"],
        "-c", f'model_reasoning_effort="{config["reasoning"]}"',
        "-c", 'approval_policy="never"',
        "-c", 'shell_environment_policy.inherit="all"',
        "--json",
        "-C", str(workspace),
        prompt,
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
            env={**os.environ, "PATH": str(Path(parley_command).resolve().parent) + os.pathsep + os.environ.get("PATH", "")},
        )
        returncode, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    elapsed = round(time.perf_counter() - started, 4)
    parsed = parse_codex_events(stdout)
    compliance = command_protocol(parsed["command_events"])
    attempts = _read_attempts(workspace / ATTEMPT_LOG)
    hidden_cases = [row for row in load_cases()[task["id"]] if row["visibility"] == "hidden"]
    hidden = evaluate_application(workspace, task, language, hidden_cases, parley_command)
    final = source_snapshot(workspace)
    seed_files = written["source"]["editable_files"]
    changed = sorted(
        name
        for name in seed_files
        if final["editable_files"].get(name, {}).get("sha256") != written["seed_hashes"][name]
    )
    expected_root = list(ROOT_FILES[language]) if task["kind"] == "maintenance" else []
    usage = parsed["usage"]
    return {
        "schema_version": 1,
        "recorded_at": utc_now(),
        "task_id": task["id"],
        "task_kind": task["kind"],
        "language": language,
        "configuration_id": config["id"],
        "model": config["model"],
        "reasoning": config["reasoning"],
        "replicate": cell["replicate"],
        "fresh_ephemeral_session": True,
        "thread_id": parsed["thread_id"],
        "agent_returncode": returncode,
        "agent_timed_out": timed_out,
        "elapsed_seconds": elapsed,
        "checker_integrity_ok": _integrity(workspace, written["protected_hashes"]),
        "command_protocol": compliance,
        "public_attempts": attempts,
        "public_check_attempts": len(attempts),
        "first_public_check_success": bool(attempts and attempts[0].get("ok")),
        "final_public_check_success": bool(attempts and attempts[-1].get("ok")),
        "repair_turns": max(len(attempts) - 1, 0),
        "hidden_success": bool(hidden["ok"]),
        "hidden_judgment": hidden,
        "usage": usage,
        "total_tokens": usage["input_tokens"] + usage["output_tokens"],
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_chars": len(prompt),
        "source": final,
        "changed_files": changed,
        "expected_root_files": expected_root,
        "exact_root": task["kind"] != "maintenance" or changed == expected_root,
        "agent_messages": parsed["agent_messages"],
        "agent_errors": parsed["errors"],
        "command_events": parsed["command_events"],
        "codex_stdout": stdout,
        "codex_stderr": stderr,
        "workdir": str(workspace),
    }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return {
        "sessions": len(rows),
        "hidden_successes": sum(bool(row.get("hidden_success")) for row in rows),
        "hidden_success_rate": sum(bool(row.get("hidden_success")) for row in rows) / len(rows),
        "first_check_successes": sum(bool(row.get("first_public_check_success")) for row in rows),
        "first_check_success_rate": sum(bool(row.get("first_public_check_success")) for row in rows) / len(rows),
        "exact_root_successes": sum(bool(row.get("exact_root")) for row in rows),
        "exact_root_rate": sum(bool(row.get("exact_root")) for row in rows) / len(rows),
        "median_total_tokens": statistics.median(float(row.get("total_tokens", 0)) for row in rows),
        "median_elapsed_seconds": statistics.median(float(row.get("elapsed_seconds", 0)) for row in rows),
        "repair_turns": sum(int(row.get("repair_turns", 0)) for row in rows),
    }


def summarize(results: list[dict[str, Any]], protocol: dict[str, Any]) -> dict[str, Any]:
    by_language = {language: _aggregate([row for row in results if row["language"] == language]) for language in LANGUAGES}
    by_configuration = {
        config["id"]: {
            language: _aggregate([row for row in results if row["configuration_id"] == config["id"] and row["language"] == language])
            for language in LANGUAGES
        }
        for config in protocol["frozen_config"]["agent_configurations"]
    }
    by_kind = {
        kind: {
            language: _aggregate([row for row in results if row["task_kind"] == kind and row["language"] == language])
            for language in LANGUAGES
        }
        for kind in ("implementation", "maintenance")
    }
    expected = protocol["matrix"]["fresh_sessions"]
    thread_ids = [row.get("thread_id") for row in results]
    integrity = (
        len(results) == expected
        and all(thread_ids)
        and len(set(thread_ids)) == expected
        and all(row.get("checker_integrity_ok") for row in results)
        and all(row.get("command_protocol", {}).get("compliant") for row in results)
        and all(not row.get("runner_error") for row in results)
    )
    baselines = [by_language[name] for name in LANGUAGES if name != "parley"]
    parley = by_language["parley"]
    correctness = parley["hidden_success_rate"] == 1.0 and all(
        parley["hidden_success_rate"] >= row["hidden_success_rate"] for row in baselines
    )
    correctness = correctness and all(
        by_configuration[config]["parley"]["hidden_success_rate"]
        >= max(by_configuration[config][name]["hidden_success_rate"] for name in LANGUAGES if name != "parley")
        for config in by_configuration
    ) and all(
        by_kind[kind]["parley"]["hidden_success_rate"]
        >= max(by_kind[kind][name]["hidden_success_rate"] for name in LANGUAGES if name != "parley")
        for kind in by_kind
    )
    first_check = parley["first_check_success_rate"] >= max(row["first_check_success_rate"] for row in baselines)
    first_check = first_check and all(
        by_kind[kind]["parley"]["first_check_success_rate"]
        >= max(by_kind[kind][name]["first_check_success_rate"] for name in LANGUAGES if name != "parley")
        for kind in by_kind
    )
    tokens = parley["median_total_tokens"] <= min(row["median_total_tokens"] for row in baselines)
    tokens = tokens and all(
        by_configuration[config]["parley"]["median_total_tokens"]
        <= min(by_configuration[config][name]["median_total_tokens"] for name in LANGUAGES if name != "parley")
        for config in by_configuration
    )
    elapsed = parley["median_elapsed_seconds"] <= min(row["median_elapsed_seconds"] for row in baselines)
    elapsed = elapsed and all(
        by_configuration[config]["parley"]["median_elapsed_seconds"]
        <= min(by_configuration[config][name]["median_elapsed_seconds"] for name in LANGUAGES if name != "parley")
        for config in by_configuration
    )
    maintenance = by_kind["maintenance"]
    maintainability = maintenance["parley"]["exact_root_rate"] == 1.0 and all(
        maintenance["parley"]["exact_root_rate"] >= maintenance[name]["exact_root_rate"]
        for name in LANGUAGES if name != "parley"
    )
    conditions = {
        "execution_integrity": integrity,
        "correctness": correctness,
        "first_check": first_check,
        "tokens": tokens,
        "elapsed": elapsed,
        "maintainability": maintainability,
    }
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "by_language": by_language,
        "by_configuration": by_configuration,
        "by_kind": by_kind,
        "primary_gate": {"conditions": conditions, "passed": all(conditions.values())},
    }


def validate_references(parley_command: str, work_root: Path) -> dict[str, Any]:
    task_map = load_task_map()
    cases = load_cases()
    rows = []
    for task in task_map.values():
        for language in LANGUAGES:
            reference_dir = Path(tempfile.mkdtemp(prefix=f"036-ref-{task['id']}-{language}-", dir=work_root))
            write_workspace(reference_dir, task, language, parley_command, variant="reference")
            reference = evaluate_application(reference_dir, task, language, cases[task["id"]], parley_command)
            if not reference["ok"]:
                raise RuntimeError(f"reference failed: {task['id']} {language}: {json.dumps(reference)}")
            seed_dir = Path(tempfile.mkdtemp(prefix=f"036-seed-{task['id']}-{language}-", dir=work_root))
            seed_written = write_workspace(seed_dir, task, language, parley_command, variant="seed")
            public = [row for row in cases[task["id"]] if row["visibility"] == "public"]
            seed = evaluate_application(seed_dir, task, language, public, parley_command)
            if not seed["build"]["ok"] or seed["ok"]:
                raise RuntimeError(f"seed boundary failed: {task['id']} {language}: {json.dumps(seed)}")
            root_ok = True
            if task["kind"] == "maintenance":
                reference_snapshot = source_snapshot(reference_dir)["editable_files"]
                changed = sorted(
                    name
                    for name in seed_written["source"]["editable_files"]
                    if reference_snapshot[name]["sha256"] != seed_written["seed_hashes"][name]
                )
                root_ok = changed == list(ROOT_FILES[language])
                if not root_ok:
                    raise RuntimeError(f"root boundary failed: {task['id']} {language}: {changed}")
            rows.append(
                {
                    "task_id": task["id"],
                    "task_kind": task["kind"],
                    "language": language,
                    "reference_cases": len(reference["cases"]),
                    "reference_pass": reference["ok"],
                    "seed_build_pass": seed["build"]["ok"],
                    "seed_public_pass": seed["ok"],
                    "root_boundary_pass": root_ok,
                }
            )
            print(f"validated {task['id']} {language}", flush=True)
    return {
        "schema_version": 1,
        "experiment_id": "036",
        "generated_at": utc_now(),
        "protocol_sha256": digest(PROTOCOL_PATH),
        "cells": rows,
        "reference_cells_passed": sum(row["reference_pass"] for row in rows),
        "seed_cells_built": sum(row["seed_build_pass"] for row in rows),
        "seed_cells_correct": sum(row["seed_public_pass"] for row in rows),
        "maintenance_root_boundaries_passed": sum(
            row["root_boundary_pass"] for row in rows if row["task_kind"] == "maintenance"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-corpus")
    validate = subparsers.add_parser("validate-references")
    validate.add_argument("--parley-command", required=True)
    validate.add_argument("--work-root", type=Path)
    validate.add_argument("--output", type=Path)
    internal = subparsers.add_parser("internal-check")
    internal.add_argument("--workspace", type=Path, required=True)
    internal.add_argument("--visibility", choices=("public", "hidden"), required=True)
    execute = subparsers.add_parser("run")
    execute.add_argument("--parley-command", required=True)
    execute.add_argument("--codex-command", default=shutil.which("codex") or "codex")
    execute.add_argument("--work-root", type=Path)
    execute.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "validate-corpus":
        print(json.dumps(validate_corpus(), indent=2))
        return 0
    if args.command == "internal-check":
        return internal_check(args.workspace.resolve(), args.visibility)
    if args.command == "validate-references":
        validate_corpus()
        work_root = args.work_root or Path(tempfile.mkdtemp(prefix="parley-fullstack-036-validation-"))
        work_root.mkdir(parents=True, exist_ok=True)
        result = validate_references(args.parley_command, work_root)
        rendered = json.dumps(result, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0

    protocol = load_protocol()
    validate_corpus()
    config = protocol["frozen_config"]
    tasks = list(load_task_map().values())
    plan = build_plan(
        tasks,
        config["languages"],
        config["agent_configurations"],
        config["replicates_per_task_language_configuration"],
        config["seed"],
    )
    work_root = args.work_root or Path(tempfile.mkdtemp(prefix="parley-fullstack-agent-036-"))
    work_root.mkdir(parents=True, exist_ok=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=config["max_workers"]) as pool:
        futures = {
            pool.submit(
                run_cell,
                cell,
                codex_command=args.codex_command,
                parley_command=args.parley_command,
                work_root=work_root,
                timeout=config["timeout_seconds"],
            ): cell
            for cell in plan
        }
        for future in concurrent.futures.as_completed(futures):
            cell = futures[future]
            try:
                row = future.result()
            except Exception as exc:
                row = {
                    "task_id": cell["task_id"],
                    "task_kind": cell["task_kind"],
                    "language": cell["language"],
                    "configuration_id": cell["configuration_id"],
                    "replicate": cell["replicate"],
                    "runner_error": repr(exc),
                    "hidden_success": False,
                    "first_public_check_success": False,
                    "exact_root": False,
                    "total_tokens": 0,
                    "elapsed_seconds": 0,
                }
            results.append(row)
            print(
                f"completed {row['task_id']} {row['language']} {row['configuration_id']} "
                f"r{row['replicate']}: hidden={row.get('hidden_success', False)}",
                flush=True,
            )
    results.sort(key=lambda row: (row["task_id"], row["language"], row["configuration_id"], row["replicate"]))
    report = {
        "schema_version": 1,
        "experiment_id": "036",
        "generated_at": utc_now(),
        "protocol": protocol,
        "protocol_sha256": digest(PROTOCOL_PATH),
        "runner_sha256": digest(Path(__file__)),
        "plan": [
            {
                key: cell[key]
                for key in ("task_id", "task_kind", "language", "configuration_id", "replicate")
            }
            for cell in plan
        ],
        "summary": summarize(results, protocol),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
