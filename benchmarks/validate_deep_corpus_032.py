#!/usr/bin/env python3
"""Validate iteration 032 seeds, reference fixes, judgments, and symmetry."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

try:
    from .agent_runner import LANGUAGES, judge, load_tasks
except ImportError:
    from agent_runner import LANGUAGES, judge, load_tasks


BENCHMARKS = Path(__file__).resolve().parent
TASKS = BENCHMARKS / "agent_tasks_deep_confirmation_032.json"
FIXES = BENCHMARKS / "deep_reference_fixes_032.json"


def materialize(root: Path, files: dict[str, str]) -> None:
    for filename, content in files.items():
        path = root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parley-command", default="parley")
    args = parser.parse_args()

    task_list = load_tasks(TASKS)
    manifest = json.loads(TASKS.read_text(encoding="utf-8"))
    reference = json.loads(FIXES.read_text(encoding="utf-8"))["fixes"]
    roots = manifest["predeclared_analysis"]["root_cause_files"]
    results = []

    for task in task_list:
        task_id = task["id"]
        for language in LANGUAGES:
            assert task["context_files"][language] == task["context_files"]["parley"]
            expected_root = roots[task_id][language]
            assert set(reference[task_id][language]) == {expected_root}
            with tempfile.TemporaryDirectory(prefix=f"parley-032-{task_id}-{language}-") as name:
                repo = Path(name)
                materialize(repo, task["seed_files"][language])
                entrypoint = repo / task["entrypoints"][language]
                seeded = judge(
                    language,
                    entrypoint,
                    task["public_cases"] + task["hidden_cases"],
                    args.parley_command,
                )
                materialize(repo, reference[task_id][language])
                shutil.rmtree(repo / "__pycache__", ignore_errors=True)
                fixed = judge(
                    language,
                    entrypoint,
                    task["public_cases"] + task["hidden_cases"],
                    args.parley_command,
                )
                if seeded["ok"]:
                    raise AssertionError(f"{task_id}/{language}: seeded defect passes every case")
                if not fixed["ok"]:
                    raise AssertionError(
                        f"{task_id}/{language}: reference fix failed: "
                        f"{json.dumps(fixed, indent=2)}"
                    )
                results.append({
                    "task": task_id,
                    "language": language,
                    "seed_compile": seeded["compile"]["ok"],
                    "seed_case_successes": sum(case["ok"] for case in seeded["cases"]),
                    "cases": len(seeded["cases"]),
                    "fixed_case_successes": sum(case["ok"] for case in fixed["cases"]),
                    "root": expected_root,
                })

    print(json.dumps({
        "ok": True,
        "tasks": len(task_list),
        "language_cells": len(results),
        "all_reference_cases": sum(row["fixed_case_successes"] for row in results),
        "results": results,
    }, indent=2))


if __name__ == "__main__":
    main()
