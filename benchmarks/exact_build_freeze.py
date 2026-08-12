#!/usr/bin/env python3
"""Run exact build commands while proving declared read-only files stay frozen."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import time
from typing import Any, Iterable, Sequence


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"read-only path must stay below the workspace: {value!r}")
    return path


def snapshot_read_only(root: Path, names: Iterable[str]) -> dict[str, dict[str, Any]]:
    """Capture hashes and file identity, rejecting missing files and symlinks."""

    root = root.resolve(strict=True)
    result: dict[str, dict[str, Any]] = {}
    for raw_name in sorted(set(names)):
        relative = _relative_path(raw_name)
        path = root.joinpath(*relative.parts)
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise ValueError(f"read-only input must be a regular non-symlink file: {raw_name}")
        if root not in path.resolve(strict=True).parents:
            raise ValueError(f"read-only input resolves outside workspace: {raw_name}")
        result[raw_name] = {
            "sha256": sha256(path),
            "bytes": info.st_size,
            "mode": stat.S_IMODE(info.st_mode),
            "device": info.st_dev,
            "inode": info.st_ino,
        }
    return result


def snapshot_changes(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return content/type changes while ignoring stable-file inode replacement."""

    result = {}
    for name in sorted(set(before) | set(after)):
        old = before.get(name)
        new = after.get(name)
        comparable_old = None if old is None else {
            key: old[key] for key in ("sha256", "bytes", "mode")
        }
        comparable_new = None if new is None else {
            key: new[key] for key in ("sha256", "bytes", "mode")
        }
        if comparable_old != comparable_new:
            result[name] = {"before": old, "after": new}
    return result


def run_frozen_builds(
    root: Path,
    read_only_files: Sequence[str],
    commands: Sequence[Sequence[str]],
    *,
    environment: dict[str, str] | None = None,
    timeout_seconds: float = 600,
) -> dict[str, Any]:
    """Execute commands in order and hash frozen inputs after every command."""

    if not commands:
        raise ValueError("at least one exact build command is required")
    root = root.resolve(strict=True)
    initial = snapshot_read_only(root, read_only_files)
    previous = initial
    results = []
    merged_environment = {**os.environ, **(environment or {})}

    for raw_command in commands:
        command = [str(part) for part in raw_command]
        if not command or not command[0]:
            raise ValueError("build commands must be nonempty argv arrays")
        started = time.perf_counter()
        timed_out = False
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                env=merged_environment,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            returncode = completed.returncode
            stdout = completed.stdout[-4000:]
            stderr = completed.stderr[-4000:]
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            returncode = None
            timeout_stdout = exc.stdout or ""
            timeout_stderr = exc.stderr or ""
            if isinstance(timeout_stdout, bytes):
                timeout_stdout = timeout_stdout.decode(errors="replace")
            if isinstance(timeout_stderr, bytes):
                timeout_stderr = timeout_stderr.decode(errors="replace")
            stdout = timeout_stdout[-4000:]
            stderr = timeout_stderr[-4000:]

        try:
            current = snapshot_read_only(root, read_only_files)
            changes = snapshot_changes(previous, current)
            snapshot_error = ""
        except (FileNotFoundError, OSError, ValueError) as exc:
            current = {}
            changes = {"<snapshot>": {"before": previous, "after": None}}
            snapshot_error = str(exc)

        result = {
            "command": command,
            "returncode": returncode,
            "timed_out": timed_out,
            "elapsed_seconds": round(time.perf_counter() - started, 4),
            "stdout_tail": stdout,
            "stderr_tail": stderr,
            "read_only_after": current,
            "read_only_changes": changes,
            "snapshot_error": snapshot_error,
            "ok": returncode == 0 and not timed_out and not changes and not snapshot_error,
        }
        results.append(result)
        previous = current
        if not result["ok"]:
            break

    final = previous
    total_changes = snapshot_changes(initial, final) if final else results[-1]["read_only_changes"]
    return {
        "schema_version": 1,
        "root": str(root),
        "read_only_files": list(read_only_files),
        "read_only_before": initial,
        "read_only_after": final,
        "read_only_changes": total_changes,
        "commands": results,
        "completed_commands": len(results),
        "expected_commands": len(commands),
        "ok": len(results) == len(commands) and all(row["ok"] for row in results) and not total_changes,
    }
