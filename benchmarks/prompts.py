#!/usr/bin/env python3
"""Render language-neutral prompts for the Phase 1 benchmark corpus."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASKS_FILE = Path(__file__).with_name("tasks.json")
LANGUAGE_LABELS = {
    "parley": "Parley",
    "python": "Python",
    "rust": "Rust",
}


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
    return data


def select_tasks(tasks_data: dict[str, Any], task_id: str | None) -> list[dict[str, Any]]:
    tasks = tasks_data["tasks"]
    if task_id is None:
        return tasks
    for task in tasks:
        if task["id"] == task_id:
            return [task]
    raise ValueError(f"unknown task id: {task_id}")


def render_prompt(task: dict[str, Any], language: str) -> str:
    label = LANGUAGE_LABELS[language]
    lines = [
        f"# Benchmark task: {task['title']}",
        "",
        f"Target language: {label}",
        "",
        "Write a complete program that implements the behavior below.",
        "Do not inspect the reference implementation while answering.",
        "Return only source code for the requested language, with no prose.",
        "",
        "## Behavior",
        str(task["summary"]),
        "",
        "## Constraints",
    ]
    features = ", ".join(str(feature) for feature in task.get("features", []))
    if features:
        lines.append(f"- Exercise these concepts: {features}.")
    if task.get("interactive"):
        lines.append("- The program reads from standard input where needed.")
        fixture = task.get("stdin_fixture")
        if fixture:
            escaped = str(fixture).replace("\n", "\\n")
            lines.append(f"- The benchmark runner may use this stdin fixture: `{escaped}`.")
    else:
        lines.append("- The program must run without standard input.")
    if task.get("deterministic_run"):
        lines.append("- The reference behavior is deterministic for automated checks.")
    else:
        lines.append("- The task may use randomness; keep all other behavior deterministic.")
    lines.extend([
        "",
        "## Output",
        "Produce a working program in the target language.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def build_prompt_report(
    tasks_data: dict[str, Any],
    tasks: list[dict[str, Any]],
    language: str,
) -> dict[str, Any]:
    prompts = [
        {
            "task_id": task["id"],
            "title": task["title"],
            "language": language,
            "prompt": render_prompt(task, language),
        }
        for task in tasks
    ]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "language_version": tasks_data.get("language_version"),
        "language": language,
        "prompts": prompts,
        "totals": {"prompts": len(prompts)},
    }


def render_output(report: dict[str, Any], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(report, indent=2) + "\n"
    parts = [item["prompt"].rstrip() for item in report["prompts"]]
    return "\n---\n\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render benchmark prompts for agent runs.")
    parser.add_argument("--tasks", type=Path, default=TASKS_FILE, help="benchmark task manifest")
    parser.add_argument("--task", help="single task id to render; omit for all tasks")
    parser.add_argument("--language", choices=sorted(LANGUAGE_LABELS), required=True)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", type=Path, help="optional output file")
    args = parser.parse_args(argv)

    try:
        tasks_data = load_tasks(args.tasks)
        tasks = select_tasks(tasks_data, args.task)
        report = build_prompt_report(tasks_data, tasks, args.language)
    except (OSError, ValueError) as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 1

    rendered = render_output(report, args.format)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
