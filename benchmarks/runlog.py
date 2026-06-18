#!/usr/bin/env python3
"""Record benchmark generation and repair attempts as JSONL.

Each appended row captures the generated source plus the tool feedback used for
that attempt. This gives the research protocol an auditable trail without
requiring a specific agent runner yet.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_text(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.read_text(encoding="utf-8")


def read_json(path: Path | None) -> Any:
    if path is None:
        return None
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if text.strip() else None


def compact_artifacts(args: argparse.Namespace) -> dict[str, Any]:
    artifacts = {
        "prompt_text": read_text(args.prompt_file),
        "source_text": read_text(args.source_file),
        "diagnostics_json": read_json(args.diagnostics_file),
        "stdout": read_text(args.stdout_file),
        "stderr": read_text(args.stderr_file),
        "patch_text": read_text(args.patch_file),
    }
    return {key: value for key, value in artifacts.items() if value is not None}


def cmd_append(args: argparse.Namespace) -> int:
    row = {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "task_id": args.task,
        "language": args.language,
        "model": args.model,
        "attempt": args.attempt,
        "status": args.status,
        "elapsed_seconds": args.elapsed_seconds,
        "repair_turn": args.repair_turn,
        "artifacts": compact_artifacts(args),
    }
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(str(args.log))
    return 0


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: each JSONL row must be an object")
        rows.append(row)
    return rows


def is_success_status(status: str) -> bool:
    return status == "success" or status.endswith("_success")


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("task_id", "")),
            str(row.get("language", "")),
            str(row.get("model", "")),
        )
        grouped[key].append(row)

    groups = []
    for key, items in sorted(grouped.items()):
        task_id, language, model = key
        ordered = sorted(
            items,
            key=lambda row: (
                int(row.get("attempt") or 0),
                int(row.get("repair_turn") or 0),
            ),
        )
        successes = [row for row in ordered if is_success_status(str(row.get("status", "")))]
        first_success = successes[0] if successes else None
        first_row = ordered[0] if ordered else {}
        elapsed = sum(float(row.get("elapsed_seconds") or 0.0) for row in ordered)
        group = {
            "task_id": task_id,
            "language": language,
            "model": model,
            "records": len(ordered),
            "attempts": max((int(row.get("attempt") or 0) for row in ordered), default=0),
            "success": first_success is not None,
            "first_check_success": str(first_row.get("status", "")) == "first_check_success",
            "first_run_success": str(first_row.get("status", "")) == "first_run_success",
            "repair_turns_to_success": (
                int(first_success.get("repair_turn") or 0) if first_success is not None else None
            ),
            "final_status": str(ordered[-1].get("status", "")) if ordered else "",
            "elapsed_seconds": round(elapsed, 4),
        }
        groups.append(group)

    by_language: dict[str, dict[str, int]] = {}
    for group in groups:
        language = group["language"]
        bucket = by_language.setdefault(
            language,
            {"groups": 0, "successes": 0, "first_run_successes": 0},
        )
        bucket["groups"] += 1
        bucket["successes"] += 1 if group["success"] else 0
        bucket["first_run_successes"] += 1 if group["first_run_success"] else 0

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "totals": {
            "records": len(rows),
            "groups": len(groups),
            "successes": sum(1 for group in groups if group["success"]),
            "first_run_successes": sum(1 for group in groups if group["first_run_success"]),
        },
        "by_language": by_language,
        "groups": groups,
    }


def print_summary_table(summary: dict[str, Any]) -> None:
    print("task             lang    model        attempts  success  repair_turns  final_status")
    print("---------------  ------  -----------  --------  -------  ------------  ------------")
    for group in summary["groups"]:
        repair_turns = group["repair_turns_to_success"]
        print(
            f"{group['task_id']:<15}  "
            f"{group['language']:<6}  "
            f"{group['model']:<11}  "
            f"{group['attempts']:>8}  "
            f"{'yes' if group['success'] else 'no':<7}  "
            f"{'-' if repair_turns is None else repair_turns!s:>12}  "
            f"{group['final_status']}"
        )


def cmd_summarize(args: argparse.Namespace) -> int:
    summary = summarize_rows(read_jsonl(args.log))
    if args.format == "json":
        print(json.dumps(summary, indent=2))
    else:
        print_summary_table(summary)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record benchmark attempts as JSONL.")
    sub = parser.add_subparsers(dest="command", required=True)

    append = sub.add_parser("append", help="append one generated attempt")
    append.add_argument("--log", type=Path, required=True, help="JSONL log path")
    append.add_argument("--task", required=True, help="task id from benchmarks/tasks.json")
    append.add_argument("--language", required=True, choices=["parley", "python", "rust"])
    append.add_argument("--model", required=True, help="agent/model name")
    append.add_argument("--attempt", type=int, required=True, help="1-based attempt number")
    append.add_argument("--status", required=True, help="attempt outcome label")
    append.add_argument("--elapsed-seconds", type=float, default=None)
    append.add_argument("--repair-turn", type=int, default=0)
    append.add_argument("--prompt-file", type=Path)
    append.add_argument("--source-file", type=Path)
    append.add_argument("--diagnostics-file", type=Path)
    append.add_argument("--stdout-file", type=Path)
    append.add_argument("--stderr-file", type=Path)
    append.add_argument("--patch-file", type=Path)
    append.set_defaults(fn=cmd_append)

    summarize = sub.add_parser("summarize", help="summarize generated attempts")
    summarize.add_argument("--log", type=Path, required=True, help="JSONL log path")
    summarize.add_argument("--format", choices=["table", "json"], default="table")
    summarize.set_defaults(fn=cmd_summarize)

    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"runlog error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
