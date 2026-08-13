#!/usr/bin/env python3
"""Validate and run preregistered fresh-agent full-stack study 041."""

from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import hashlib
import http.client
import importlib.metadata
import json
import os
import platform
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

import tiktoken

try:
    from .agent_check_transport import CLIENT_FILE, CHECK_FILE, ParentCheckBroker
    from .agent_runner import parse_codex_events, utc_now
    from .exact_build_freeze import snapshot_changes, snapshot_read_only
    from .fullstack_agent_041_guard import DomainGuard
    from .scratch_space import (
        ScratchBudget,
        ScratchCapacityError,
        cleanup_finished_workspace,
        preflight_scratch_space,
    )
    from .fullstack_agent_041_scaffolds import (
        LANGUAGES,
        ROOT_FILES,
        ScaffoldFile,
        load_task_map,
        scaffold_files,
    )
except ImportError:
    from agent_check_transport import CLIENT_FILE, CHECK_FILE, ParentCheckBroker
    from agent_runner import parse_codex_events, utc_now
    from exact_build_freeze import snapshot_changes, snapshot_read_only
    from fullstack_agent_041_guard import DomainGuard
    from scratch_space import (
        ScratchBudget,
        ScratchCapacityError,
        cleanup_finished_workspace,
        preflight_scratch_space,
    )
    from fullstack_agent_041_scaffolds import (
        LANGUAGES,
        ROOT_FILES,
        ScaffoldFile,
        load_task_map,
        scaffold_files,
    )


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
PROTOCOL_PATH = BENCHMARKS / "fullstack_agent_041_protocol.json"
CASES_PATH = BENCHMARKS / "fullstack_agent_041_cases.json"
SKILL_PATH = REPO / "skill/parley/references/core-v0.5.2.md"
WEB_REFERENCE_PATH = REPO / "skill/parley/references/web-v0.5.2.md"
GENERATED_PARTS = {".benchmark_build", ".parley-build", "__pycache__"}
FROZEN_PARLEY_COMMIT = "2e44bb092012eba3e9864da9c3e8a1588c2f3fb3"
FROZEN_PARLEY_TREE = "5781929c21e76ebeeab2feb733cd2ff4207a039e"
FROZEN_PARLEY_VERSION = "parley 0.5.2"
PYTHON_RUNTIME = Path(
    os.environ.get(
        "FULLSTACK_041_PYTHON",
        "/private/tmp/parley-fullstack-041-python/bin/python",
    )
)
TS_DEPENDENCY_ROOT = Path(
    os.environ.get("FULLSTACK_041_TYPESCRIPT", "/private/tmp/parley-fullstack-041-typescript")
)
TS_COMPILER = TS_DEPENDENCY_ROOT / "node_modules/.bin/tsc"
TS_MODULES = TS_DEPENDENCY_ROOT / "node_modules"
ROUGH_TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_']*|\d+\.\d+|\d+|==|!=|<=|>=|[^\s]",
    re.ASCII,
)
O200K = tiktoken.get_encoding("o200k_base")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_digest(root: Path) -> str:
    checksum = hashlib.sha256()
    for path in sorted(
        candidate
        for candidate in root.rglob("*")
        if candidate.is_file()
        and "__pycache__" not in candidate.parts
        and candidate.suffix != ".pyc"
    ):
        checksum.update(path.relative_to(root).as_posix().encode())
        checksum.update(b"\0")
        checksum.update(path.read_bytes())
        checksum.update(b"\0")
    return checksum.hexdigest()


def frozen_source_archive_sha256() -> str:
    archive = subprocess.run(
        ["git", "archive", "--format=tar", FROZEN_PARLEY_COMMIT],
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout
    return hashlib.sha256(archive).hexdigest()


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
    if protocol.get("schema_version") != 1 or protocol.get("experiment_id") != "041":
        raise ValueError("full-stack agent protocol must be schema 1 / experiment 041")
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
    transport = protocol["validated_transport"]
    for file_key, sha_key in (
        ("transport_file", "transport_sha256"),
        ("terra_smoke_file", "terra_smoke_sha256"),
        ("sol_smoke_file", "sol_smoke_sha256"),
    ):
        path_value = REPO / transport[file_key]
        if digest(path_value) != transport[sha_key]:
            raise ValueError(f"validated transport hash mismatch for {transport[file_key]}")
    exact_build = protocol["validated_exact_build_freeze"]
    for file_key, sha_key in (
        ("validator_file", "validator_sha256"),
        ("smoke_file", "smoke_sha256"),
        ("evidence_file", "evidence_sha256"),
    ):
        path_value = REPO / exact_build[file_key]
        if digest(path_value) != exact_build[sha_key]:
            raise ValueError(f"validated exact-build hash mismatch for {exact_build[file_key]}")
    scratch = protocol["scratch_space_control"]
    for file_key, sha_key in (
        ("implementation_file", "implementation_sha256"),
        ("policy_file", "policy_sha256"),
    ):
        path_value = REPO / scratch[file_key]
        if digest(path_value) != scratch[sha_key]:
            raise ValueError(f"scratch-control hash mismatch for {scratch[file_key]}")
    if scratch["required_free_bytes"] != (
        scratch["reserve_bytes"]
        + scratch["max_workers"] * scratch["per_worker_bytes"]
    ):
        raise ValueError("scratch-control budget arithmetic is inconsistent")
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
        "max_public_check_attempts",
    ):
        if not isinstance(config[field], int) or config[field] < 1:
            raise ValueError(f"{field} must be a positive integer")
    execution = protocol.get("execution_freeze")
    if execution is not None:
        files = execution.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("execution freeze must name every transitive harness file")
        for item in files:
            if set(item) != {"file", "sha256"}:
                raise ValueError("invalid execution-freeze file record")
            if digest(REPO / item["file"]) != item["sha256"]:
                raise ValueError(f"execution freeze mismatch for {item['file']}")
    return protocol


def load_provenance(path: Path, parley_command: str) -> dict[str, Any]:
    provenance = json.loads(path.read_text(encoding="utf-8"))
    if provenance.get("schema_version") != 1 or provenance.get("experiment_id") != "041":
        raise ValueError("Parley provenance must be schema 1 / experiment 041")
    parley = provenance.get("parley", {})
    expected = {
        "source_commit": FROZEN_PARLEY_COMMIT,
        "source_tree": FROZEN_PARLEY_TREE,
        "reported_version": FROZEN_PARLEY_VERSION,
    }
    for field, value in expected.items():
        if parley.get(field) != value:
            raise ValueError(
                f"frozen Parley provenance mismatch for {field}: "
                f"{parley.get(field)!r} != {value!r}"
            )
    if parley.get("source_archive_sha256") != frozen_source_archive_sha256():
        raise ValueError("frozen Parley source archive hash mismatch")
    source_root = Path(parley.get("source_root", ""))
    package_root = Path(parley.get("package_root", ""))
    for field, root in (
        ("source_tree_sha256", source_root),
        ("package_tree_sha256", package_root),
        ("site_packages_tree_sha256", Path(parley.get("site_packages_root", ""))),
    ):
        if not root.is_dir() or parley.get(field) != tree_digest(root):
            raise ValueError(f"frozen Parley tree mismatch for {field}")
    executable = Path(parley_command).resolve()
    if Path(parley.get("executable", "")).resolve() != executable:
        raise ValueError("--parley-command does not match the frozen provenance executable")
    if not executable.is_file() or digest(executable) != parley.get("executable_sha256"):
        raise ValueError("frozen Parley executable hash mismatch")
    version = run(
        [str(executable), "--version"], cwd=executable.parent.parent
    ).stdout.strip()
    if version != FROZEN_PARLEY_VERSION:
        raise ValueError(f"frozen Parley version mismatch: {version!r}")
    environment = provenance.get("environment", {})
    if Path(environment.get("python_runtime", "")).absolute() != PYTHON_RUNTIME.absolute():
        raise ValueError("Python runtime does not match provenance")
    if Path(environment.get("typescript_modules", "")).resolve() != TS_MODULES.resolve():
        raise ValueError("TypeScript dependency root does not match provenance")
    lock_checks = (
        ("python_requirements_lock_sha256", BENCHMARKS / "fullstack_035/python/requirements.lock.txt"),
        ("typescript_lock_sha256", BENCHMARKS / "fullstack_035/typescript/package-lock.json"),
        ("rust_manifest_sha256", BENCHMARKS / "fullstack_041/rust/Cargo.toml"),
        ("rust_lock_sha256", BENCHMARKS / "fullstack_041/rust/Cargo.lock"),
    )
    for field, lock_path in lock_checks:
        if environment.get(field) != digest(lock_path):
            raise ValueError(f"dependency lock mismatch for {lock_path}")
    artifact_checks = (
        (
            "host_python_executable_sha256",
            Path(environment.get("host_python_executable", "")),
        ),
        ("python_runtime_executable_sha256", PYTHON_RUNTIME.resolve()),
        ("typescript_compiler_sha256", TS_COMPILER.resolve()),
        (
            "browser_executable_sha256",
            Path(environment.get("browser_executable", "")),
        ),
    )
    for field, artifact in artifact_checks:
        if not artifact.is_file() or environment.get(field) != digest(artifact):
            raise ValueError(f"environment artifact mismatch for {field}")

    def actual_version(command: list[str]) -> str:
        completed = run(command, cwd=REPO)
        return (completed.stdout or completed.stderr).strip().splitlines()[-1]

    version_checks = (
        ("python_runtime_version", [str(PYTHON_RUNTIME), "--version"]),
        ("typescript_version", [str(TS_COMPILER), "--version"]),
        ("node_version", ["node", "--version"]),
        ("npm_version", ["npm", "--version"]),
        ("rustc_version", ["rustc", "--version"]),
        ("cargo_version", ["cargo", "--version"]),
    )
    for field, command in version_checks:
        if environment.get(field) != actual_version(command):
            raise ValueError(f"environment version mismatch for {field}")
    python_freeze = run(
        [str(PYTHON_RUNTIME), "-m", "pip", "freeze", "--all"], cwd=REPO
    ).stdout
    if environment.get("python_pip_freeze") != python_freeze:
        raise ValueError("frozen Python package environment mismatch")
    python_site_packages = Path(environment.get("python_site_packages", ""))
    if (
        not python_site_packages.is_dir()
        or environment.get("python_site_packages_tree_sha256")
        != tree_digest(python_site_packages)
    ):
        raise ValueError("frozen Python site-packages tree mismatch")
    npm_tree = run(["npm", "ls", "--all", "--json"], cwd=TS_DEPENDENCY_ROOT).stdout
    if environment.get("typescript_npm_tree_sha256") != hashlib.sha256(npm_tree.encode()).hexdigest():
        raise ValueError("frozen TypeScript package environment mismatch")
    if environment.get("typescript_modules_tree_sha256") != tree_digest(TS_MODULES):
        raise ValueError("frozen TypeScript module tree mismatch")
    parley_python = executable.parent / "python"
    parley_freeze = run(
        [str(parley_python), "-m", "pip", "freeze", "--all"], cwd=REPO
    ).stdout
    if parley.get("pip_freeze") != parley_freeze:
        raise ValueError("frozen Parley package environment mismatch")
    if environment.get("playwright_version") != importlib.metadata.version("playwright"):
        raise ValueError("Playwright package version mismatch")
    if environment.get("platform") != platform.platform() or environment.get("machine") != platform.machine():
        raise ValueError("host platform differs from provenance")
    return provenance


def load_cases() -> dict[str, list[dict[str, Any]]]:
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or payload.get("experiment_id") != "041":
        raise ValueError("full-stack cases must be schema 1 / experiment 041")
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
        if len(public) != 4 or len(hidden) != 5:
            raise ValueError(f"{task_id}: expected four public and five hidden cases")
        public_rows = [row for row in rows if row.get("visibility") == "public"]
        hidden_rows = [row for row in rows if row.get("visibility") == "hidden"]
        if sum(row.get("target") == "browser" for row in public_rows) != 1:
            raise ValueError(f"{task_id}: expected one public browser case")
        if sum(row.get("target") == "browser" for row in hidden_rows) != 2:
            raise ValueError(f"{task_id}: expected two hidden browser cases")
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
    if matrix["frozen_public_case_executions_across_first_checks"] != expected_sessions * 4:
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
    for index, cell in enumerate(cells, 1):
        cell["plan_index"] = index
        cell["cell_id"] = cell_id(cell)
    return cells


def cell_id(cell: dict[str, Any]) -> str:
    return (
        f"{cell['task_id']}__{cell['language']}__"
        f"{cell['configuration_id']}__r{cell['replicate']}"
    )


def source_metrics(text: str) -> dict[str, Any]:
    encoded = text.encode()
    return {
        "text": text,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "bytes": len(encoded),
        "lines": len(text.splitlines()),
        "rough_tokens": len(ROUGH_TOKEN_RE.findall(text)),
        "o200k_base_tokens": len(O200K.encode(text)),
    }


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


def _ignored_workspace_path(relative: str) -> bool:
    parts = Path(relative).parts
    return (
        "node_modules" in parts
        or any(part in GENERATED_PARTS for part in parts)
    )


def workspace_paths(workspace: Path) -> list[str]:
    paths: list[str] = []
    for root, directories, filenames in os.walk(workspace, followlinks=False):
        root_path = Path(root)
        kept_directories = []
        for directory in directories:
            path = root_path / directory
            relative = path.relative_to(workspace).as_posix()
            if path.is_symlink():
                if not _ignored_workspace_path(relative):
                    paths.append(relative)
            elif not _ignored_workspace_path(relative):
                kept_directories.append(directory)
                paths.append(relative + "/")
        directories[:] = kept_directories
        for filename in filenames:
            relative = (root_path / filename).relative_to(workspace).as_posix()
            if not _ignored_workspace_path(relative):
                paths.append(relative)
    return sorted(paths)


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
    }
    for name, text in protected.items():
        path = workspace / name
        path.write_text(text, encoding="utf-8")
        if name in {"sources", "print_sources.py"}:
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
        "seed_source": {
            name: source_metrics(spec.text)
            for name, spec in files.items()
            if spec.editable
        },
        "read_only_hashes": {
            name: hashlib.sha256(spec.text.encode()).hexdigest()
            for name, spec in files.items()
            if not spec.editable
        },
        "symlinks": (
            {"node_modules": str(TS_MODULES.resolve())}
            if language == "typescript"
            else {}
        ),
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
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def build_application(
    workspace: Path,
    language: str,
    parley_command: str,
    frozen_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    output = workspace / ".benchmark_build"
    _reset(output)
    started = time.perf_counter()
    env = {**os.environ, "CARGO_NET_OFFLINE": "true"}
    build_checks: list[dict[str, Any]] = []

    def exact_run(
        command: list[str],
        *,
        cwd: Path = workspace,
        command_env: dict[str, str] | None = None,
        timeout: int = 300,
    ) -> None:
        before = snapshot_read_only(workspace, (frozen_hashes or {}).keys())
        preexisting = {
            name: {"expected": expected, "actual": before[name]["sha256"]}
            for name, expected in sorted((frozen_hashes or {}).items())
            if before[name]["sha256"] != expected
        }
        if preexisting:
            raise RuntimeError(
                "protected/read-only hashes differ before exact build: "
                + json.dumps(preexisting, sort_keys=True)
            )
        command_error = ""
        try:
            run(command, cwd=cwd, env=command_env, timeout=timeout)
        except Exception as exc:
            command_error = str(exc)
            raise
        finally:
            after = snapshot_read_only(workspace, (frozen_hashes or {}).keys())
            changes = snapshot_changes(before, after)
            build_checks.append(
                {
                    "command": command,
                    "protected_read_only_files": len(before),
                    "changes": changes,
                    "command_error": command_error,
                    "hashes_ok": not changes,
                    "ok": not command_error and not changes,
                }
            )
            if changes and not command_error:
                raise RuntimeError(
                    "exact build changed protected/read-only inputs: "
                    + json.dumps(changes, sort_keys=True)
                )
    try:
        if language == "parley":
            _reset(workspace / ".parley-build")
            exact_run(
                [parley_command, "web", "build", str(workspace), "-o", str(output / "bundle")],
                command_env=env,
                timeout=300,
            )
        elif language == "python":
            if not PYTHON_RUNTIME.is_file():
                raise RuntimeError(f"missing frozen Python runtime: {PYTHON_RUNTIME}")
            exact_run(
                [str(PYTHON_RUNTIME), "-m", "py_compile", "app.py", "logic.py"],
            )
            exact_run(["node", "--check", "browser.js"])
        elif language == "typescript":
            if not TS_COMPILER.is_file() or not TS_MODULES.is_dir():
                raise RuntimeError("missing frozen TypeScript dependency installation")
            exact_run(
                [str(TS_COMPILER), "-p", "tsconfig.json", "--outDir", str(output / "dist")],
            )
        elif language == "rust":
            rust_env = {**env, "CARGO_TARGET_DIR": str(output / "target")}
            exact_run(
                ["cargo", "build", "--locked", "--offline", "--release"],
                command_env=rust_env,
                timeout=600,
            )
            exact_run(
                ["cargo", "build", "--locked", "--offline", "--release", "--lib", "--target", "wasm32-unknown-unknown"],
                command_env=rust_env,
                timeout=600,
            )
        else:
            raise ValueError(f"unsupported language: {language}")
        return {
            "ok": True,
            "error": "",
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            "protected_read_only_checks": build_checks,
            "protected_read_only_ok": all(row["hashes_ok"] for row in build_checks),
        }
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "error": str(exc),
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            "protected_read_only_checks": build_checks,
            "protected_read_only_ok": bool(build_checks) and all(
                row["hashes_ok"] for row in build_checks
            ),
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
        env["FULLSTACK_041_BROWSER"] = str(output / "dist/logic.js")
        return ["node", str(output / "dist/server.js")], env, workspace
    env["FULLSTACK_041_WASM"] = str(
        output / "target/wasm32-unknown-unknown/release/fullstack_agent_041.wasm"
    )
    return [str(output / "target/release/fullstack-agent-041")], env, workspace


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


class RunningServer:
    def __init__(self, process: subprocess.Popen[str], guard: DomainGuard):
        self.process = process
        self.guard = guard


def start_server(workspace: Path, language: str, task: dict[str, Any]) -> tuple[RunningServer, int]:
    upstream_port = allocate_port()
    public_port = allocate_port()
    command, env, cwd = server_spec(workspace, language, upstream_port)
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
    upstream_ready = False
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(f"server exited early\nstdout:\n{stdout}\nstderr:\n{stderr}")
        try:
            if request(upstream_port, status_case)["pass"]:
                upstream_ready = True
                break
        except OSError:
            time.sleep(0.02)
    if not upstream_ready:
        stop_process(process)
        raise RuntimeError(f"{language} server did not become ready")
    guard = DomainGuard(task, upstream_port, public_port)
    try:
        guard.start()
        if not request(public_port, status_case)["pass"]:
            raise RuntimeError("numeric-domain guard status probe failed")
        return RunningServer(process, guard), public_port
    except Exception:
        guard.stop()
        stop_process(process)
        raise


def stop_process(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def stop_server(server: RunningServer) -> None:
    server.guard.stop()
    stop_process(server.process)


def evaluate_application(
    workspace: Path,
    task: dict[str, Any],
    language: str,
    cases: list[dict[str, Any]],
    parley_command: str,
    frozen_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    build = build_application(workspace, language, parley_command, frozen_hashes)
    if not build["ok"]:
        return {"ok": False, "build": build, "cases": [], "cross_target": None}
    server: RunningServer | None = None
    try:
        server, port = start_server(workspace, language, task)
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
        if server is not None:
            stop_server(server)


def parent_public_evaluation(
    workspace: Path,
    task: dict[str, Any],
    language: str,
    parley_command: str,
    frozen_hashes: dict[str, str],
) -> dict[str, Any]:
    public_cases = [
        case
        for case in load_cases()[task["id"]]
        if case["visibility"] == "public"
    ]
    result = evaluate_application(
        workspace, task, language, public_cases, parley_command, frozen_hashes
    )
    stdout = ""
    errors: list[str] = []
    if result["ok"]:
        stdout = f"public HTTP and Chromium checks passed for {task['id']}\n"
    else:
        if not result["build"]["ok"]:
            errors.append(result["build"]["error"])
        for row in result.get("cases", []):
            if not row["pass"]:
                errors.append(f"{row['id']} failed: {json.dumps(row, sort_keys=True)}")
        cross = result.get("cross_target")
        if cross and not cross["pass"]:
            errors.append(
                "public browser/HTTP agreement failed: "
                + json.dumps(cross, sort_keys=True)
            )
        if result.get("runtime_error"):
            errors.append(result["runtime_error"])
        if not errors:
            errors.append(f"public checks failed for {task['id']}")
    return {
        **result,
        "source": source_snapshot(workspace),
        "stdout": stdout,
        "stderr": "\n".join(errors) + ("\n" if errors else ""),
    }


def source_snapshot(workspace: Path) -> dict[str, Any]:
    config = json.loads((workspace / ".benchmark_source.json").read_text())
    files = {}
    for name in config["editable_files"]:
        path = workspace / name
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        files[name] = {"exists": path.is_file(), **source_metrics(text)}
    return {
        "editable_files": files,
        "totals": {
            metric: sum(int(row[metric]) for row in files.values())
            for metric in ("bytes", "lines", "rough_tokens", "o200k_base_tokens")
        },
    }


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
    maximum = load_protocol()["frozen_config"]["max_public_check_attempts"]
    if check_count > maximum:
        violations.append(f"public check limit exceeded: {check_count} > {maximum}")
    return {"compliant": bool(commands) and not violations, "commands": commands, "violations": violations}


def _integrity(workspace: Path, hashes: dict[str, str]) -> bool:
    return all(
        (workspace / name).is_file()
        and not (workspace / name).is_symlink()
        and digest(workspace / name) == expected
        for name, expected in hashes.items()
    )


def _symlink_integrity(workspace: Path, symlinks: dict[str, str]) -> bool:
    return all(
        (workspace / name).is_symlink()
        and str((workspace / name).resolve()) == expected
        for name, expected in symlinks.items()
    )


def source_edits(
    seed: dict[str, dict[str, Any]],
    final: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    per_file = {
        name: {
            "changed": seed.get(name, {}).get("sha256") != final.get(name, {}).get("sha256"),
            "rough_token_edit_count": rough_token_edit_count(
                str(seed.get(name, {}).get("text", "")),
                str(final.get(name, {}).get("text", "")),
            ),
        }
        for name in sorted(set(seed) | set(final))
    }
    return {
        "files": per_file,
        "rough_token_edit_count": sum(
            int(row["rough_token_edit_count"]) for row in per_file.values()
        ),
    }


def command_path(command: str) -> Path:
    resolved = shutil.which(command) if os.sep not in command else command
    if not resolved:
        raise ValueError(f"command not found: {command}")
    path = Path(resolved).resolve()
    if not path.is_file():
        raise ValueError(f"command is not a file: {path}")
    return path


def repository_state() -> dict[str, Any]:
    def git(*args: str) -> str:
        return run(["git", *args], cwd=REPO).stdout.strip()

    return {
        "commit": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "branch": git("branch", "--show-current"),
        "status_porcelain": git("status", "--porcelain=v1", "--untracked-files=all"),
    }


def execution_environment(codex_command: str) -> dict[str, Any]:
    codex = command_path(codex_command)
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "tiktoken": importlib.metadata.version("tiktoken"),
        "playwright": importlib.metadata.version("playwright"),
        "codex_executable": str(codex),
        "codex_executable_sha256": digest(codex),
        "codex_version": run([str(codex), "--version"], cwd=REPO).stdout.strip(),
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def journal_paths(journal_root: Path, identifier: str) -> tuple[Path, Path]:
    return (
        journal_root / f"{identifier}.started.json",
        journal_root / f"{identifier}.finished.json",
    )


def cleanup_path(journal_root: Path, identifier: str) -> Path:
    return journal_root / f"{identifier}.cleanup.json"


def directory_size_bytes(root: Path) -> int:
    """Measure retained regular-file bytes without following symlinks."""

    total = 0
    for current_root, directory_names, file_names in os.walk(root, followlinks=False):
        current = Path(current_root)
        directory_names[:] = [
            name for name in directory_names if not (current / name).is_symlink()
        ]
        for name in file_names:
            path = current / name
            if not path.is_symlink():
                total += path.stat().st_size
    return total


def _cell_workspace_candidates(cell: dict[str, Any], work_root: Path) -> list[Path]:
    prefix = (
        f"041-{cell['task_id']}-{cell['language']}-"
        f"{cell['configuration_id']}-r{cell['replicate']}-"
    )
    return sorted(path for path in work_root.glob(f"{prefix}*") if path.is_dir())


def ensure_cleanup_record(
    cell: dict[str, Any],
    row: dict[str, Any],
    *,
    journal_root: Path,
    work_root: Path,
) -> dict[str, Any]:
    """Create or verify immutable cleanup evidence for one finished cell."""

    _, finished = journal_paths(journal_root, cell["cell_id"])
    path = cleanup_path(journal_root, cell["cell_id"])
    if path.is_file():
        record = json.loads(path.read_text(encoding="utf-8"))
        if (
            record.get("cell_id") != cell["cell_id"]
            or record.get("status") not in {"removed", "not_created", "failed"}
            or record.get("finished_record") != str(finished.resolve())
        ):
            raise RuntimeError(f"invalid cleanup evidence: {path}")
        workdir = row.get("workdir")
        if record["status"] == "removed" and workdir and Path(workdir).exists():
            raise RuntimeError(f"cleaned workspace still exists: {workdir}")
        if record["status"] == "not_created" and workdir:
            raise RuntimeError(f"cleanup claims no workspace for {workdir}")
        if record["status"] == "failed" and not record.get("error"):
            raise RuntimeError(f"cleanup failure lacks an error: {path}")
        return record
    if path.exists():
        raise RuntimeError(f"cleanup evidence is not a regular file: {path}")
    workdir = row.get("workdir")
    if workdir:
        if not Path(workdir).exists():
            raise RuntimeError(
                f"finished workspace disappeared without cleanup evidence: {workdir}"
            )
        try:
            workspace_bytes = directory_size_bytes(Path(workdir))
            record = cleanup_finished_workspace(work_root, Path(workdir), finished)
            record["workspace_bytes"] = workspace_bytes
        except Exception as exc:
            record = {
                "schema_version": 1,
                "status": "failed",
                "work_root": str(work_root.resolve()),
                "workspace": str(Path(workdir).resolve()),
                "workspace_bytes": locals().get("workspace_bytes", 0),
                "finished_record": str(finished.resolve()),
                "error": repr(exc),
            }
    else:
        record = {
            "schema_version": 1,
            "status": "not_created",
            "work_root": str(work_root.resolve()),
            "workspace": None,
            "workspace_bytes": 0,
            "finished_record": str(finished.resolve()),
        }
    record["cell_id"] = cell["cell_id"]
    record["recorded_at"] = utc_now()
    atomic_write_json(path, record)
    return record


def failure_row(
    cell: dict[str, Any],
    error: str,
    *,
    interrupted_before_completion: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "recorded_at": utc_now(),
        "cell_id": cell["cell_id"],
        "plan_index": cell["plan_index"],
        "task_id": cell["task_id"],
        "task_kind": cell["task_kind"],
        "language": cell["language"],
        "configuration_id": cell["configuration_id"],
        "model": cell["configuration"]["model"],
        "reasoning": cell["configuration"]["reasoning"],
        "replicate": cell["replicate"],
        "runner_error": error,
        "interrupted_before_completion": interrupted_before_completion,
        "thread_id": None,
        "checker_integrity_ok": False,
        "read_only_integrity_ok": False,
        "symlink_integrity_ok": False,
        "transport_integrity_ok": False,
        "attempt_record_integrity_ok": False,
        "public_execution_ok": False,
        "editable_file_integrity_ok": False,
        "workspace_integrity_ok": False,
        "unexpected_files": [],
        "command_protocol": {"compliant": False, "commands": [], "violations": [error]},
        "hidden_success": False,
        "first_public_check_success": False,
        "root_quality_eligible": False,
        "exact_root": False,
        "usage": {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "uncached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
        },
        "total_tokens": 0,
        "elapsed_seconds": 0,
        "repair_turns": 0,
    }


def execute_journaled_cell(
    cell: dict[str, Any],
    *,
    journal_root: Path,
    codex_command: str,
    parley_command: str,
    work_root: Path,
    attempt_root: Path,
    timeout: int,
) -> dict[str, Any]:
    started_path, finished_path = journal_paths(journal_root, cell["cell_id"])
    if started_path.exists() or finished_path.exists():
        raise RuntimeError(f"cell already journaled: {cell['cell_id']}")
    atomic_write_json(
        started_path,
        {
            "schema_version": 1,
            "experiment_id": "041",
            "status": "started",
            "agent_session_started": True,
            "recorded_at": utc_now(),
            "cell": {
                key: cell[key]
                for key in (
                    "cell_id",
                    "plan_index",
                    "task_id",
                    "task_kind",
                    "language",
                    "configuration_id",
                    "replicate",
                )
            },
        },
    )
    try:
        row = run_cell(
            cell,
            codex_command=codex_command,
            parley_command=parley_command,
            work_root=work_root,
            attempt_root=attempt_root / cell["cell_id"],
            timeout=timeout,
        )
    except Exception as exc:
        row = failure_row(cell, repr(exc))
        candidates = _cell_workspace_candidates(cell, work_root)
        if len(candidates) == 1:
            row["workdir"] = str(candidates[0])
    row["journal_attempt"] = 1
    row["agent_session_started"] = True
    atomic_write_json(
        finished_path,
        {
            "schema_version": 1,
            "experiment_id": "041",
            "status": "finished",
            "recorded_at": utc_now(),
            "result": row,
        },
    )
    cleanup = ensure_cleanup_record(
        cell,
        row,
        journal_root=journal_root,
        work_root=work_root,
    )
    if cleanup["status"] == "failed":
        raise RuntimeError(
            f"workspace cleanup failed for {cell['cell_id']}: {cleanup['error']}"
        )
    return row


def initialize_journal(
    plan: list[dict[str, Any]],
    journal_root: Path,
    *,
    resume: bool,
    work_root: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    identifiers = {cell["cell_id"] for cell in plan}
    if not resume:
        if journal_root.exists() and any(journal_root.iterdir()):
            raise RuntimeError(f"fresh run refuses non-empty journal: {journal_root}")
        journal_root.mkdir(parents=True, exist_ok=True)
        return [], plan
    if not journal_root.is_dir():
        raise RuntimeError(f"resume journal does not exist: {journal_root}")
    expected_names = {
        name
        for identifier in identifiers
        for name in (
            f"{identifier}.started.json",
            f"{identifier}.finished.json",
            f"{identifier}.cleanup.json",
        )
    } | {"run_manifest.json", "run_failure.json"}
    unknown = sorted(path.name for path in journal_root.glob("*.json") if path.name not in expected_names)
    if unknown:
        raise RuntimeError(f"journal contains unknown records: {unknown}")
    completed: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    for cell in plan:
        started_path, finished_path = journal_paths(journal_root, cell["cell_id"])
        if finished_path.is_file():
            if not started_path.is_file():
                raise RuntimeError(f"finished journal has no start record: {finished_path}")
            started_payload = json.loads(started_path.read_text(encoding="utf-8"))
            payload = json.loads(finished_path.read_text(encoding="utf-8"))
            row = payload.get("result", {})
            expected_cell = {
                key: cell[key]
                for key in (
                    "cell_id",
                    "plan_index",
                    "task_id",
                    "task_kind",
                    "language",
                    "configuration_id",
                    "replicate",
                )
            }
            if (
                started_payload.get("status") != "started"
                or started_payload.get("cell") != expected_cell
                or payload.get("status") != "finished"
                or row.get("cell_id") != cell["cell_id"]
                or row.get("plan_index") != cell["plan_index"]
                or row.get("journal_attempt") != 1
            ):
                raise RuntimeError(f"invalid finished journal: {finished_path}")
            if work_root is None:
                raise RuntimeError("resume requires a work root for cleanup verification")
            ensure_cleanup_record(
                cell,
                row,
                journal_root=journal_root,
                work_root=work_root,
            )
            completed.append(row)
        elif started_path.is_file():
            started_payload = json.loads(started_path.read_text(encoding="utf-8"))
            expected_cell = {
                key: cell[key]
                for key in (
                    "cell_id",
                    "plan_index",
                    "task_id",
                    "task_kind",
                    "language",
                    "configuration_id",
                    "replicate",
                )
            }
            if (
                started_payload.get("status") != "started"
                or started_payload.get("cell") != expected_cell
            ):
                raise RuntimeError(f"invalid started journal: {started_path}")
            row = failure_row(
                cell,
                "process interrupted after cell start; selective rerun forbidden",
                interrupted_before_completion=True,
            )
            row["journal_attempt"] = 1
            row["agent_session_started"] = True
            atomic_write_json(
                finished_path,
                {
                    "schema_version": 1,
                    "experiment_id": "041",
                    "status": "finished",
                    "recorded_at": utc_now(),
                    "result": row,
                },
            )
            if work_root is None:
                raise RuntimeError("resume requires a work root for cleanup verification")
            ensure_cleanup_record(
                cell,
                row,
                journal_root=journal_root,
                work_root=work_root,
            )
            completed.append(row)
        else:
            pending.append(cell)
    return completed, pending


def ensure_run_manifest(
    journal_root: Path,
    identity: dict[str, Any],
    *,
    resume: bool,
    scratch_preflight: dict[str, Any],
) -> Path:
    path = journal_root / "run_manifest.json"
    if resume:
        if not path.is_file():
            raise RuntimeError("resume journal is missing run_manifest.json")
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("identity") != identity:
            raise RuntimeError("resume environment differs from the frozen run manifest")
        initial = existing.get("initial_scratch_preflight", {})
        if initial.get("status") != "pass":
            raise RuntimeError("run manifest lacks a passing initial scratch preflight")
    else:
        if path.exists():
            raise RuntimeError(f"fresh run refuses existing manifest: {path}")
        atomic_write_json(
            path,
            {
                "schema_version": 1,
                "experiment_id": "041",
                "created_at": utc_now(),
                "identity": identity,
                "initial_scratch_preflight": scratch_preflight,
            },
        )
    return path


def record_run_failure(
    journal_root: Path,
    *,
    category: str,
    error: str,
    evidence: dict[str, Any] | None = None,
) -> Path:
    """Persist the first run-level integrity failure without overwriting it."""

    path = journal_root / "run_failure.json"
    if path.is_file():
        return path
    if path.exists():
        raise RuntimeError(f"run failure evidence is not a regular file: {path}")
    atomic_write_json(
        path,
        {
            "schema_version": 1,
            "experiment_id": "041",
            "recorded_at": utc_now(),
            "category": category,
            "error": error,
            "evidence": evidence,
        },
    )
    return path


def seal_unstarted_cell(
    cell: dict[str, Any],
    *,
    journal_root: Path,
    work_root: Path,
    error: str,
) -> dict[str, Any]:
    """Record a permanent failed outcome without starting an agent session."""

    started, finished = journal_paths(journal_root, cell["cell_id"])
    if started.exists() or finished.exists():
        raise RuntimeError(f"cannot seal already-journaled cell: {cell['cell_id']}")
    cell_identity = {
        key: cell[key]
        for key in (
            "cell_id",
            "plan_index",
            "task_id",
            "task_kind",
            "language",
            "configuration_id",
            "replicate",
        )
    }
    atomic_write_json(
        started,
        {
            "schema_version": 1,
            "experiment_id": "041",
            "status": "started",
            "agent_session_started": False,
            "recorded_at": utc_now(),
            "cell": cell_identity,
        },
    )
    row = failure_row(cell, error)
    row["journal_attempt"] = 1
    row["agent_session_started"] = False
    atomic_write_json(
        finished,
        {
            "schema_version": 1,
            "experiment_id": "041",
            "status": "finished",
            "recorded_at": utc_now(),
            "result": row,
        },
    )
    cleanup = ensure_cleanup_record(
        cell,
        row,
        journal_root=journal_root,
        work_root=work_root,
    )
    if cleanup["status"] != "not_created":
        raise RuntimeError(f"sealed cell has unexpected cleanup state: {cleanup}")
    return row


def scratch_snapshot(
    work_root: Path,
    budget: ScratchBudget,
    *,
    phase: str,
) -> dict[str, Any]:
    usage = shutil.disk_usage(work_root)
    required = budget.required_free_bytes
    return {
        "schema_version": 1,
        "phase": phase,
        "status": "pass" if usage.free >= required else "fail",
        "work_root": str(work_root.resolve()),
        "max_workers": budget.max_workers,
        "reserve_bytes": budget.reserve_bytes,
        "per_worker_bytes": budget.per_worker_bytes,
        "required_free_bytes": required,
        "filesystem_total_bytes": usage.total,
        "filesystem_used_bytes": usage.used,
        "filesystem_free_bytes": usage.free,
        "headroom_bytes": usage.free - required,
    }


def journal_manifest(plan: list[dict[str, Any]], journal_root: Path) -> list[dict[str, Any]]:
    rows = []
    for cell in plan:
        started, finished = journal_paths(journal_root, cell["cell_id"])
        cleanup = cleanup_path(journal_root, cell["cell_id"])
        cleanup_record = json.loads(cleanup.read_text(encoding="utf-8"))
        rows.append(
            {
                "cell_id": cell["cell_id"],
                "started_file": str(started),
                "started_sha256": digest(started),
                "finished_file": str(finished),
                "finished_sha256": digest(finished),
                "cleanup_file": str(cleanup),
                "cleanup_sha256": digest(cleanup),
                "cleanup": cleanup_record,
            }
        )
    return rows


def run_cell(
    cell: dict[str, Any],
    *,
    codex_command: str,
    parley_command: str,
    work_root: Path,
    attempt_root: Path,
    timeout: int,
) -> dict[str, Any]:
    load_protocol()
    task = cell["task"]
    language = cell["language"]
    config = cell["configuration"]
    workspace = Path(
        tempfile.mkdtemp(
            prefix=f"041-{task['id']}-{language}-{config['id']}-r{cell['replicate']}-",
            dir=work_root,
        )
    )
    written = write_workspace(workspace, task, language, parley_command)
    if attempt_root.exists():
        raise RuntimeError(f"parent attempt directory already exists: {attempt_root}")
    broker = ParentCheckBroker(
        workspace,
        lambda number, request_id: parent_public_evaluation(
            workspace,
            task,
            language,
            parley_command,
            {**written["protected_hashes"], **written["read_only_hashes"]},
        ),
        attempt_root=attempt_root,
        max_attempts=load_protocol()["frozen_config"]["max_public_check_attempts"],
    )
    broker.install()
    written["protected_hashes"][CLIENT_FILE] = digest(workspace / CLIENT_FILE)
    written["protected_hashes"][CHECK_FILE] = digest(workspace / CHECK_FILE)
    prompt = render_prompt(
        task,
        load_cases()[task["id"]],
        language,
        SKILL_PATH.read_text(),
        WEB_REFERENCE_PATH.read_text(),
    )
    (workspace / "prompt.md").write_text(prompt, encoding="utf-8")
    written["protected_hashes"]["prompt.md"] = hashlib.sha256(prompt.encode()).hexdigest()
    frozen_build_hashes = {
        **written["protected_hashes"],
        **written["read_only_hashes"],
    }
    initial_paths = workspace_paths(workspace)
    command = [
        codex_command,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
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
        "-c", "sandbox_workspace_write.network_access=false",
        "--json",
        "-C", str(workspace),
        prompt,
    ]
    broker.start()
    started = time.perf_counter()
    timed_out = False
    broker_error = ""
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
    finally:
        try:
            broker.stop(timeout=900)
        except Exception as exc:
            broker_error = repr(exc)
    elapsed = round(time.perf_counter() - started, 4)
    parsed = parse_codex_events(stdout)
    compliance = command_protocol(parsed["command_events"])
    attempts = list(broker.attempts)
    attempt_files = sorted(attempt_root.glob("attempt-*.json"))
    attempt_record_integrity = (
        len(attempt_files) == len(attempts)
        and all(
            json.loads(path.read_text(encoding="utf-8")) == attempt
            for path, attempt in zip(attempt_files, attempts, strict=True)
        )
    )
    public_execution_ok = bool(
        attempts
        and any(len(attempt.get("cases", [])) == 4 for attempt in attempts)
        and all(
            not attempt.get("build", {}).get("ok")
            or (
                len(attempt.get("cases", [])) == 4
                and sum(case.get("target") == "http" for case in attempt["cases"]) == 3
                and sum(case.get("target") == "browser" for case in attempt["cases"]) == 1
            )
            for attempt in attempts
        )
    )
    hidden_cases = [row for row in load_cases()[task["id"]] if row["visibility"] == "hidden"]
    hidden = evaluate_application(
        workspace,
        task,
        language,
        hidden_cases,
        parley_command,
        frozen_build_hashes,
    )
    final = source_snapshot(workspace)
    unexpected_files = sorted(set(workspace_paths(workspace)) - set(initial_paths))
    protected_integrity = _integrity(workspace, written["protected_hashes"])
    read_only_integrity = _integrity(workspace, written["read_only_hashes"])
    symlink_integrity = _symlink_integrity(workspace, written["symlinks"])
    editable_file_integrity = all(
        (workspace / name).is_file() and not (workspace / name).is_symlink()
        for name in written["source"]["editable_files"]
    )
    transport_integrity = broker.integrity()
    transport_integrity_ok = bool(
        transport_integrity["ok"]
        and not transport_integrity["protocol_errors"]
        and not broker_error
    )
    workspace_integrity = (
        protected_integrity
        and read_only_integrity
        and symlink_integrity
        and editable_file_integrity
        and transport_integrity_ok
        and attempt_record_integrity
        and not broker_error
        and not unexpected_files
    )
    post_build_integrity = bool(
        attempts
        and all(
            attempt.get("build", {}).get("protected_read_only_ok")
            for attempt in attempts
        )
        and hidden.get("build", {}).get("protected_read_only_ok")
    )
    workspace_integrity = workspace_integrity and post_build_integrity
    seed_files = written["source"]["editable_files"]
    changed = sorted(
        name
        for name in seed_files
        if final["editable_files"].get(name, {}).get("sha256") != written["seed_hashes"][name]
    )
    expected_root = list(ROOT_FILES[language]) if task["kind"] == "maintenance" else []
    edits = source_edits(written["seed_source"], final["editable_files"])
    root_eligible = task["kind"] == "maintenance" and bool(hidden["ok"])
    exact_root = bool(
        root_eligible
        and changed == expected_root
        and workspace_integrity
    )
    usage = {
        **parsed["usage"],
        "uncached_input_tokens": max(
            int(parsed["usage"]["input_tokens"])
            - int(parsed["usage"]["cached_input_tokens"]),
            0,
        ),
    }
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
        "cell_id": cell["cell_id"],
        "plan_index": cell["plan_index"],
        "checker_integrity_ok": protected_integrity,
        "read_only_integrity_ok": read_only_integrity,
        "symlink_integrity_ok": symlink_integrity,
        "transport_integrity": transport_integrity,
        "transport_integrity_ok": transport_integrity_ok,
        "attempt_record_integrity_ok": attempt_record_integrity,
        "public_execution_ok": public_execution_ok,
        "post_build_integrity_ok": post_build_integrity,
        "editable_file_integrity_ok": editable_file_integrity,
        "parent_attempt_records": [
            {"file": str(path), "sha256": digest(path)} for path in attempt_files
        ],
        "broker_error": broker_error,
        "workspace_integrity_ok": workspace_integrity,
        "unexpected_files": unexpected_files,
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
        "seed_source": {
            "editable_files": written["seed_source"],
            "totals": {
                metric: sum(int(row[metric]) for row in written["seed_source"].values())
                for metric in ("bytes", "lines", "rough_tokens", "o200k_base_tokens")
            },
        },
        "source_edits": edits,
        "changed_files": changed,
        "expected_root_files": expected_root,
        "root_quality_eligible": root_eligible,
        "exact_root": exact_root,
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
    root_rows = [
        row
        for row in rows
        if row.get("task_kind") == "maintenance" and row.get("hidden_success")
    ]
    root_successes = sum(bool(row.get("exact_root")) for row in root_rows)
    return {
        "sessions": len(rows),
        "hidden_successes": sum(bool(row.get("hidden_success")) for row in rows),
        "hidden_success_rate": sum(bool(row.get("hidden_success")) for row in rows) / len(rows),
        "first_check_successes": sum(bool(row.get("first_public_check_success")) for row in rows),
        "first_check_success_rate": sum(bool(row.get("first_public_check_success")) for row in rows) / len(rows),
        "hidden_correct_maintenance_rows": len(root_rows),
        "exact_root_successes": root_successes,
        "exact_root_rate": root_successes / len(root_rows) if root_rows else 0.0,
        "median_total_tokens": statistics.median(float(row.get("total_tokens", 0)) for row in rows),
        "median_elapsed_seconds": statistics.median(float(row.get("elapsed_seconds", 0)) for row in rows),
        "repair_turns": sum(int(row.get("repair_turns", 0)) for row in rows),
    }


def persisted_attempts_ok(row: dict[str, Any]) -> bool:
    records = row.get("parent_attempt_records", [])
    attempts = row.get("public_attempts", [])
    if len(records) != len(attempts):
        return False
    for record, attempt in zip(records, attempts, strict=True):
        path = Path(record.get("file", ""))
        if (
            not path.is_file()
            or record.get("sha256") != digest(path)
            or json.loads(path.read_text(encoding="utf-8")) != attempt
        ):
            return False
    return True


def summarize(
    results: list[dict[str, Any]],
    protocol: dict[str, Any],
    *,
    execution_context_ok: bool = True,
) -> dict[str, Any]:
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
        execution_context_ok
        and
        len(results) == expected
        and len({row.get("cell_id") for row in results}) == expected
        and all(thread_ids)
        and len(set(thread_ids)) == expected
        and all(row.get("checker_integrity_ok") for row in results)
        and all(row.get("read_only_integrity_ok") for row in results)
        and all(row.get("symlink_integrity_ok") for row in results)
        and all(row.get("transport_integrity_ok") for row in results)
        and all(row.get("attempt_record_integrity_ok") for row in results)
        and all(persisted_attempts_ok(row) for row in results)
        and all(row.get("public_execution_ok") for row in results)
        and all(row.get("post_build_integrity_ok") for row in results)
        and all(row.get("editable_file_integrity_ok") for row in results)
        and all(row.get("workspace_integrity_ok") for row in results)
        and all(not row.get("unexpected_files") for row in results)
        and all(row.get("command_protocol", {}).get("compliant") for row in results)
        and all(not row.get("runner_error") for row in results)
        and all(row.get("fresh_ephemeral_session") for row in results)
        and all(row.get("agent_session_started") is True for row in results)
        and all(row.get("journal_attempt") == 1 for row in results)
        and all(row.get("agent_returncode") == 0 for row in results)
        and all(not row.get("agent_timed_out") for row in results)
        and all(not row.get("agent_errors") for row in results)
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


def validate_references(
    parley_command: str,
    work_root: Path,
    provenance_path: Path | None = None,
) -> dict[str, Any]:
    task_map = load_task_map()
    cases = load_cases()
    rows = []
    for task in task_map.values():
        for language in LANGUAGES:
            reference_dir = Path(tempfile.mkdtemp(prefix=f"041-ref-{task['id']}-{language}-", dir=work_root))
            reference_written = write_workspace(
                reference_dir, task, language, parley_command, variant="reference"
            )
            reference_hashes = {
                **reference_written["protected_hashes"],
                **reference_written["read_only_hashes"],
            }
            reference = evaluate_application(
                reference_dir,
                task,
                language,
                cases[task["id"]],
                parley_command,
                reference_hashes,
            )
            if not reference["ok"]:
                raise RuntimeError(f"reference failed: {task['id']} {language}: {json.dumps(reference)}")
            seed_dir = Path(tempfile.mkdtemp(prefix=f"041-seed-{task['id']}-{language}-", dir=work_root))
            seed_written = write_workspace(seed_dir, task, language, parley_command, variant="seed")
            public = [row for row in cases[task["id"]] if row["visibility"] == "public"]
            seed = evaluate_application(
                seed_dir,
                task,
                language,
                public,
                parley_command,
                {
                    **seed_written["protected_hashes"],
                    **seed_written["read_only_hashes"],
                },
            )
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
                    "reference_post_build_integrity": reference["build"][
                        "protected_read_only_ok"
                    ],
                    "seed_post_build_integrity": seed["build"][
                        "protected_read_only_ok"
                    ],
                    "reference_exact_build_commands": len(
                        reference["build"]["protected_read_only_checks"]
                    ),
                    "seed_exact_build_commands": len(
                        seed["build"]["protected_read_only_checks"]
                    ),
                }
            )
            print(f"validated {task['id']} {language}", flush=True)
    return {
        "schema_version": 1,
        "experiment_id": "041",
        "generated_at": utc_now(),
        "protocol_sha256": digest(PROTOCOL_PATH),
        "provenance_file": str(provenance_path.resolve()) if provenance_path else None,
        "provenance_sha256": digest(provenance_path) if provenance_path else None,
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
    validate.add_argument("--provenance", type=Path, required=True)
    validate.add_argument("--work-root", type=Path)
    validate.add_argument("--output", type=Path)
    execute = subparsers.add_parser("run")
    execute.add_argument("--parley-command", required=True)
    execute.add_argument("--provenance", type=Path, required=True)
    execute.add_argument("--codex-command", default=shutil.which("codex") or "codex")
    execute.add_argument("--work-root", type=Path, required=True)
    execute.add_argument("--journal-root", type=Path, required=True)
    execute.add_argument("--attempt-root", type=Path, required=True)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "validate-corpus":
        print(json.dumps(validate_corpus(), indent=2))
        return 0
    if args.command == "validate-references":
        validate_corpus()
        load_provenance(args.provenance, args.parley_command)
        work_root = args.work_root or Path(tempfile.mkdtemp(prefix="parley-fullstack-041-validation-"))
        work_root.mkdir(parents=True, exist_ok=True)
        result = validate_references(args.parley_command, work_root, args.provenance)
        rendered = json.dumps(result, indent=2) + "\n"
        if args.output:
            atomic_write_json(args.output, result)
        print(rendered, end="")
        return 0

    if args.output.exists():
        raise RuntimeError(f"measured output already exists; refusing rerun: {args.output}")
    protocol = load_protocol()
    validate_corpus()
    provenance = load_provenance(args.provenance, args.parley_command)
    repo_state = repository_state()
    if repo_state["status_porcelain"]:
        raise RuntimeError(
            "measured execution requires a clean repository; commit the frozen harness first:\n"
            + repo_state["status_porcelain"]
        )
    executor = execution_environment(args.codex_command)
    config = protocol["frozen_config"]
    tasks = list(load_task_map().values())
    plan = build_plan(
        tasks,
        config["languages"],
        config["agent_configurations"],
        config["replicates_per_task_language_configuration"],
        config["seed"],
    )
    work_root = args.work_root
    work_root.mkdir(parents=True, exist_ok=True)
    if args.resume:
        if not args.journal_root.is_dir():
            raise RuntimeError(f"resume journal root does not exist: {args.journal_root}")
        if not args.attempt_root.is_dir():
            raise RuntimeError(f"resume attempt root does not exist: {args.attempt_root}")
    else:
        if args.journal_root.exists() and (
            not args.journal_root.is_dir() or any(args.journal_root.iterdir())
        ):
            raise RuntimeError(f"fresh run refuses non-empty journal root: {args.journal_root}")
        args.journal_root.mkdir(parents=True, exist_ok=True)
        if args.attempt_root.exists() and (
            not args.attempt_root.is_dir() or any(args.attempt_root.iterdir())
        ):
            raise RuntimeError(f"fresh run refuses non-empty attempt root: {args.attempt_root}")
        args.attempt_root.mkdir(parents=True, exist_ok=True)
    scratch = protocol["scratch_space_control"]
    if scratch["max_workers"] != config["max_workers"]:
        raise RuntimeError("scratch worker budget differs from frozen executor workers")
    scratch_budget = ScratchBudget(
        max_workers=scratch["max_workers"],
        reserve_bytes=scratch["reserve_bytes"],
        per_worker_bytes=scratch["per_worker_bytes"],
    )
    scratch_preflight = preflight_scratch_space(
        work_root,
        scratch_budget,
        evidence_roots=[args.journal_root, args.attempt_root],
    )
    scratch_preflight["phase"] = "resume_preflight" if args.resume else "initial_preflight"
    scratch_checks = [scratch_preflight]
    scratch_identity = {
        key: scratch_preflight[key]
        for key in (
            "work_root",
            "evidence_roots",
            "max_workers",
            "reserve_bytes",
            "per_worker_bytes",
            "required_free_bytes",
        )
    }
    run_identity = {
        "protocol_sha256": digest(PROTOCOL_PATH),
        "runner_sha256": digest(Path(__file__)),
        "preparer_sha256": digest(BENCHMARKS / "prepare_fullstack_agent_041.py"),
        "scaffolds_sha256": digest(BENCHMARKS / "fullstack_agent_041_scaffolds.py"),
        "transport_sha256": digest(BENCHMARKS / "agent_check_transport.py"),
        "guard_sha256": digest(BENCHMARKS / "fullstack_agent_041_guard.py"),
        "provenance_sha256": digest(args.provenance),
        "attempt_root": str(args.attempt_root.resolve()),
        "repository": repo_state,
        "execution_environment": executor,
        "scratch_control": scratch_identity,
        "plan_cell_ids": [cell["cell_id"] for cell in plan],
    }
    if args.resume:
        run_manifest_path = ensure_run_manifest(
            args.journal_root,
            run_identity,
            resume=True,
            scratch_preflight=scratch_preflight,
        )
        results, pending = initialize_journal(
            plan, args.journal_root, resume=True, work_root=work_root
        )
    else:
        results, pending = initialize_journal(
            plan, args.journal_root, resume=False, work_root=work_root
        )
        run_manifest_path = ensure_run_manifest(
            args.journal_root,
            run_identity,
            resume=False,
            scratch_preflight=scratch_preflight,
        )
    manifest_payload = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    initial_scratch_preflight = manifest_payload["initial_scratch_preflight"]
    run_failure_path = args.journal_root / "run_failure.json"
    lifecycle_failure = ""
    if run_failure_path.is_file():
        previous_failure = json.loads(run_failure_path.read_text(encoding="utf-8"))
        lifecycle_failure = previous_failure.get("error", "prior run-level integrity failure")
    failed_cleanup_cells = [
        row["cell_id"]
        for row in results
        if cleanup_path(args.journal_root, row["cell_id"]).is_file()
        and json.loads(
            cleanup_path(args.journal_root, row["cell_id"]).read_text(encoding="utf-8")
        ).get("status")
        == "failed"
    ]
    if failed_cleanup_cells and not lifecycle_failure:
        lifecycle_failure = f"prior cleanup failure for cells: {failed_cleanup_cells}"
        run_failure_path = record_run_failure(
            args.journal_root,
            category="cell_lifecycle",
            error=lifecycle_failure,
            evidence={"cell_ids": failed_cleanup_cells},
        )

    unscheduled = list(pending)
    with concurrent.futures.ThreadPoolExecutor(max_workers=config["max_workers"]) as pool:
        futures: dict[concurrent.futures.Future[dict[str, Any]], dict[str, Any]] = {}

        def submit_available(limit: int) -> None:
            for _ in range(min(limit, len(unscheduled))):
                cell = unscheduled.pop(0)
                future = pool.submit(
                    execute_journaled_cell,
                    cell,
                    journal_root=args.journal_root,
                    codex_command=args.codex_command,
                    parley_command=args.parley_command,
                    work_root=work_root,
                    attempt_root=args.attempt_root,
                    timeout=config["timeout_seconds"],
                )
                futures[future] = cell

        if not lifecycle_failure:
            submit_available(config["max_workers"])
        while futures:
            done, _ = concurrent.futures.wait(
                futures,
                return_when=concurrent.futures.FIRST_COMPLETED,
            )
            completed_batch: list[dict[str, Any]] = []
            for future in sorted(done, key=lambda item: futures[item]["plan_index"]):
                cell = futures.pop(future)
                try:
                    row = future.result()
                except Exception as exc:
                    started, finished = journal_paths(args.journal_root, cell["cell_id"])
                    if not finished.is_file():
                        agent_session_was_started = started.is_file()
                        if not agent_session_was_started:
                            atomic_write_json(
                                started,
                                {
                                    "schema_version": 1,
                                    "experiment_id": "041",
                                    "status": "started",
                                    "agent_session_started": False,
                                    "recorded_at": utc_now(),
                                    "cell": {
                                        key: cell[key]
                                        for key in (
                                            "cell_id",
                                            "plan_index",
                                            "task_id",
                                            "task_kind",
                                            "language",
                                            "configuration_id",
                                            "replicate",
                                        )
                                    },
                                },
                            )
                        row = failure_row(cell, repr(exc))
                        row["journal_attempt"] = 1
                        row["agent_session_started"] = agent_session_was_started
                        atomic_write_json(
                            finished,
                            {
                                "schema_version": 1,
                                "experiment_id": "041",
                                "status": "finished",
                                "recorded_at": utc_now(),
                                "result": row,
                            },
                        )
                        ensure_cleanup_record(
                            cell,
                            row,
                            journal_root=args.journal_root,
                            work_root=work_root,
                        )
                    else:
                        row = json.loads(finished.read_text(encoding="utf-8"))["result"]
                    lifecycle_failure = lifecycle_failure or repr(exc)
                    run_failure_path = record_run_failure(
                        args.journal_root,
                        category="cell_lifecycle",
                        error=lifecycle_failure,
                        evidence={"cell_id": cell["cell_id"]},
                    )
                completed_batch.append(row)
            for row in completed_batch:
                results.append(row)
                print(
                    f"completed {row['task_id']} {row['language']} {row['configuration_id']} "
                    f"r{row['replicate']}: hidden={row.get('hidden_success', False)}",
                    flush=True,
                )
            if not lifecycle_failure and unscheduled:
                try:
                    renewed = preflight_scratch_space(
                        work_root,
                        scratch_budget,
                        evidence_roots=[args.journal_root, args.attempt_root],
                    )
                    renewed["phase"] = "renewed_before_scheduling"
                    scratch_checks.append(renewed)
                except ScratchCapacityError as exc:
                    failed_check = scratch_snapshot(
                        work_root,
                        scratch_budget,
                        phase="renewed_before_scheduling",
                    )
                    scratch_checks.append(failed_check)
                    lifecycle_failure = repr(exc)
                    run_failure_path = record_run_failure(
                        args.journal_root,
                        category="scratch_capacity",
                        error=lifecycle_failure,
                        evidence=failed_check,
                    )
            if not lifecycle_failure:
                submit_available(len(completed_batch))

    if lifecycle_failure:
        halt_error = f"agent session not started after run-level integrity failure: {lifecycle_failure}"
        for cell in unscheduled:
            results.append(
                seal_unstarted_cell(
                    cell,
                    journal_root=args.journal_root,
                    work_root=work_root,
                    error=halt_error,
                )
            )
        unscheduled.clear()
    results.sort(key=lambda row: int(row["plan_index"]))
    if len(results) != len(plan) or len({row["cell_id"] for row in results}) != len(plan):
        raise RuntimeError("journal did not produce exactly one result for every frozen cell")
    repo_state_after = repository_state()
    provenance_after_error = ""
    try:
        load_provenance(args.provenance, args.parley_command)
    except Exception as exc:
        provenance_after_error = repr(exc)
    journal = journal_manifest(plan, args.journal_root)
    cleanup_records = [entry["cleanup"] for entry in journal]
    scratch_final = scratch_snapshot(work_root, scratch_budget, phase="final")
    scratch_integrity_ok = (
        not lifecycle_failure
        and all(check["status"] == "pass" for check in scratch_checks)
        and scratch_final["status"] == "pass"
        and all(record["status"] in {"removed", "not_created"} for record in cleanup_records)
    )
    execution_context_ok = (
        repo_state_after["commit"] == repo_state["commit"]
        and repo_state_after["tree"] == repo_state["tree"]
        and repo_state_after["branch"] == repo_state["branch"]
        and not repo_state_after["status_porcelain"]
        and not provenance_after_error
        and scratch_integrity_ok
    )
    run_failure_payload = (
        json.loads(run_failure_path.read_text(encoding="utf-8"))
        if run_failure_path.is_file()
        else None
    )
    workspace_sizes = [int(record.get("workspace_bytes", 0)) for record in cleanup_records]
    report = {
        "schema_version": 1,
        "experiment_id": "041",
        "generated_at": utc_now(),
        "protocol": protocol,
        "protocol_sha256": digest(PROTOCOL_PATH),
        "runner_sha256": digest(Path(__file__)),
        "preparer_sha256": digest(BENCHMARKS / "prepare_fullstack_agent_041.py"),
        "scaffolds_sha256": digest(BENCHMARKS / "fullstack_agent_041_scaffolds.py"),
        "transport_sha256": digest(BENCHMARKS / "agent_check_transport.py"),
        "guard_sha256": digest(BENCHMARKS / "fullstack_agent_041_guard.py"),
        "provenance": provenance,
        "provenance_file": str(args.provenance.resolve()),
        "provenance_sha256": digest(args.provenance),
        "provenance_after_execution_error": provenance_after_error,
        "repository": repo_state,
        "repository_after": repo_state_after,
        "execution_environment": executor,
        "scratch_preflight": initial_scratch_preflight,
        "scratch_capacity_checks": scratch_checks,
        "scratch_final": scratch_final,
        "scratch_summary": {
            "integrity_ok": scratch_integrity_ok,
            "cleanup_records": len(cleanup_records),
            "cleanup_failures": sum(record["status"] == "failed" for record in cleanup_records),
            "peak_cell_workspace_bytes": max(workspace_sizes, default=0),
            "peak_per_worker_workspace_bytes": max(workspace_sizes, default=0),
            "retained_workspace_bytes_after_cleanup": sum(
                size
                for size, record in zip(workspace_sizes, cleanup_records, strict=True)
                if record["status"] == "failed"
            ),
        },
        "journal_root": str(args.journal_root.resolve()),
        "attempt_root": str(args.attempt_root.resolve()),
        "run_manifest_file": str(run_manifest_path.resolve()),
        "run_manifest_sha256": digest(run_manifest_path),
        "run_failure_file": str(run_failure_path.resolve()) if run_failure_payload else None,
        "run_failure_sha256": digest(run_failure_path) if run_failure_payload else None,
        "run_failure": run_failure_payload,
        "journal": journal,
        "plan": [
            {
                key: cell[key]
                for key in (
                    "cell_id",
                    "plan_index",
                    "task_id",
                    "task_kind",
                    "language",
                    "configuration_id",
                    "replicate",
                )
            }
            for cell in plan
        ],
        "summary": summarize(
            results,
            protocol,
            execution_context_ok=execution_context_ok,
        ),
        "results": results,
    }
    atomic_write_json(args.output, report)
    print(json.dumps(report["summary"], indent=2))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
