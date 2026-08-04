#!/usr/bin/env python3
"""Build the frozen iteration-027 size-sixteen corpus from reviewed inputs."""

from __future__ import annotations

import json
from pathlib import Path


BENCHMARKS = Path(__file__).resolve().parent
BASE = BENCHMARKS / "agent_tasks_repositories_026.json"
ADDITIONS = BENCHMARKS / "agent_tasks_repositories_additions_027.json"
OUTPUT = BENCHMARKS / "agent_tasks_repositories_027.json"


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
    if len(tasks) != 16 or len(task_ids) != len(set(task_ids)):
        raise ValueError("iteration 027 requires sixteen unique repository tasks")

    payload = {
        "schema_version": 1,
        "description": (
            "Sixteen two-file repository-maintenance tasks for a second "
            "independent workload expansion under the unchanged source protocol."
        ),
        "predeclared_analysis": {
            "experiment_id": "027",
            "matrix": (
                "16 repositories x 3 languages x 6 complete-bundle replicates = "
                "18 fresh sessions and 288 hidden-judged assignments"
            ),
            "seed": 20260817,
            "scope": (
                "Repository-shaped maintenance under the unchanged protected "
                "./sources-then-./check protocol. The first eight repositories are "
                "preserved exactly from 026 and the final eight are unrelated additions."
            ),
            "primary_question": (
                "Does a second independent expansion preserve Rust efficiency parity "
                "and close the remaining Python gap while maintaining hidden correctness "
                "and first-check reliability?"
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
