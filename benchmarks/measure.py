#!/usr/bin/env python3
"""Measure the Parley seed benchmark corpus.

This is a Phase 1 harness for repository readiness. It records source-size
metrics and, by default, verifies each Parley task with `parley check --json`.
The `rough_tokens` value is a stable regex count for comparisons inside this
repo; it is not an LLM tokenizer and should not be used as a paper result.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
TASKS_FILE = Path(__file__).with_name("tasks.json")
DEFAULT_OUTPUT = Path(__file__).with_name("results") / "parley_seed_metrics.json"

ROUGH_TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_']*|\d+\.\d+|\d+|==|!=|<=|>=|[^\s]",
    re.ASCII,
)
WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_']*|\d+(?:\.\d+)?", re.ASCII)


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def load_tasks(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("tasks.json must use schema_version 1")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks.json must contain a non-empty tasks list")

    seen: set[str] = set()
    for task in tasks:
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("each task needs a non-empty string id")
        if task_id in seen:
            raise ValueError(f"duplicate task id: {task_id}")
        seen.add(task_id)

        source = task.get("source")
        if not isinstance(source, str) or not source:
            raise ValueError(f"{task_id}: source must be a non-empty string")
        if not (REPO / source).is_file():
            raise ValueError(f"{task_id}: source does not exist: {source}")

    return data


def source_metrics(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    return {
        "bytes": len(text.encode("utf-8")),
        "chars": len(text),
        "lines": len(lines),
        "nonblank_lines": sum(1 for line in lines if line.strip()),
        "words": len(WORD_RE.findall(text)),
        "rough_tokens": len(ROUGH_TOKEN_RE.findall(text)),
    }


def run_check(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "parley.cli", "check", str(path), "--json"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=60,
    )
    elapsed = round(time.perf_counter() - started, 4)

    payload: dict[str, Any]
    try:
        loaded = json.loads(proc.stdout)
        payload = loaded if isinstance(loaded, dict) else {}
    except json.JSONDecodeError:
        payload = {}

    diagnostics = payload.get("diagnostics", [])
    if not isinstance(diagnostics, list):
        diagnostics = []

    return {
        "ok": proc.returncode == 0 and payload.get("ok") is True,
        "returncode": proc.returncode,
        "elapsed_seconds": elapsed,
        "diagnostics_count": len(diagnostics),
        "codes": sorted(
            {
                str(d.get("code"))
                for d in diagnostics
                if isinstance(d, dict) and d.get("code")
            }
        ),
        "stdout_bytes": len(proc.stdout.encode("utf-8")),
        "stderr_bytes": len(proc.stderr.encode("utf-8")),
    }


def build_report(tasks_data: dict[str, Any], include_check: bool) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for task in tasks_data["tasks"]:
        source = REPO / task["source"]
        row = {
            "id": task["id"],
            "title": task["title"],
            "source": task["source"],
            "interactive": bool(task.get("interactive", False)),
            "deterministic_run": bool(task.get("deterministic_run", False)),
            "features": list(task.get("features", [])),
            "metrics": source_metrics(source),
        }
        if include_check:
            row["check"] = run_check(source)
        else:
            row["check"] = {"skipped": True}
        rows.append(row)

    totals = {
        "tasks": len(rows),
        "bytes": sum(row["metrics"]["bytes"] for row in rows),
        "lines": sum(row["metrics"]["lines"] for row in rows),
        "nonblank_lines": sum(row["metrics"]["nonblank_lines"] for row in rows),
        "rough_tokens": sum(row["metrics"]["rough_tokens"] for row in rows),
        "checked_ok": (
            sum(1 for row in rows if row["check"].get("ok") is True)
            if include_check
            else 0
        ),
    }

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "language_version": tasks_data.get("language_version"),
        "method": {
            "source_metrics": "UTF-8 bytes, characters, lines, nonblank lines, words, and regex rough_tokens.",
            "rough_tokens": "Regex token count for stable repo-local tracking, not an LLM tokenizer.",
            "check": "Runs `python -m parley.cli check <source> --json` from the repository root unless --no-check is used.",
        },
        "tasks": rows,
        "totals": totals,
    }


def print_table(report: dict[str, Any]) -> None:
    print("id               lines  rough_tokens  check  source")
    print("---------------  -----  ------------  -----  -----------------------------")
    for row in report["tasks"]:
        check = "skip" if row["check"].get("skipped") else ("ok" if row["check"].get("ok") else "fail")
        print(
            f"{row['id']:<15}  "
            f"{row['metrics']['lines']:>5}  "
            f"{row['metrics']['rough_tokens']:>12}  "
            f"{check:<5}  "
            f"{row['source']}"
        )
    totals = report["totals"]
    print("---------------  -----  ------------  -----  -----------------------------")
    print(
        f"{'total':<15}  "
        f"{totals['lines']:>5}  "
        f"{totals['rough_tokens']:>12}  "
        f"{totals['checked_ok']}/{totals['tasks']:<3}  "
        "Parley seed corpus"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure the Parley seed benchmark corpus.")
    parser.add_argument("--tasks", type=Path, default=TASKS_FILE, help="benchmark task manifest")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON report path")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="stdout format")
    parser.add_argument("--no-check", action="store_true", help="skip parley check --json verification")
    args = parser.parse_args(argv)

    try:
        tasks_data = load_tasks(args.tasks)
        report = build_report(tasks_data, include_check=not args.no_check)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print_table(report)
        print(f"\nWrote {rel(args.output) if args.output.resolve().is_relative_to(REPO) else args.output}")

    if not args.no_check and report["totals"]["checked_ok"] != report["totals"]["tasks"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
