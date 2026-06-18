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

    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"runlog error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
