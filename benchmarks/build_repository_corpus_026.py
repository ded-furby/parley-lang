#!/usr/bin/env python3
"""Build the frozen iteration-026 repository corpus from reviewed inputs."""

from __future__ import annotations

import json
from pathlib import Path


BENCHMARKS = Path(__file__).resolve().parent
BASE = BENCHMARKS / "agent_tasks_repositories_025.json"
ADDITIONS = BENCHMARKS / "agent_tasks_repositories_additions_026.json"
OUTPUT = BENCHMARKS / "agent_tasks_repositories_026.json"


def load_manifest(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError(f"{path.name} must use schema_version 1")
    if not isinstance(payload.get("tasks"), list) or not payload["tasks"]:
        raise ValueError(f"{path.name} must contain tasks")
    return payload


def main() -> None:
    base = load_manifest(BASE)
    additions = load_manifest(ADDITIONS)
    tasks = [*base["tasks"], *additions["tasks"]]
    task_ids = [task["id"] for task in tasks]
    if len(tasks) != 8 or len(task_ids) != len(set(task_ids)):
        raise ValueError("iteration 026 requires eight unique repository tasks")

    payload = {
        "schema_version": 1,
        "description": (
            "Eight two-file repository-maintenance tasks for an independently "
            "expanded size-eight comparison under the iteration-025 source protocol."
        ),
        "predeclared_analysis": {
            "experiment_id": "026",
            "matrix": (
                "8 repositories x 3 languages x 6 complete-bundle replicates = "
                "18 fresh sessions and 144 hidden-judged assignments"
            ),
            "seed": 20260815,
            "scope": (
                "Repository-shaped maintenance under the unchanged protected "
                "./sources-then-./check protocol. The first four repositories are "
                "preserved exactly from 025 and the final four are unrelated additions."
            ),
            "primary_question": (
                "Does fixed-context amortization across eight repositories close the "
                "remaining Parley efficiency gap while preserving hidden correctness "
                "and first-check reliability against Python and Rust?"
            ),
            "change_rule": (
                "Preserve all output. No language change may follow one repository, "
                "transcript, session, or token gap. Proposals require recurrence across "
                "unrelated new repositories and independent sessions, then general "
                "usefulness, semantic consistency, and maintainability."
            ),
            "instruction_rule": (
                "Use the unchanged 1,519-character Parley skill. The one allowed "
                "instruction-compression experiment remains closed."
            ),
        },
        "tasks": tasks,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
