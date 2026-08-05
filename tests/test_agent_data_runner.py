from copy import deepcopy
from pathlib import Path

from benchmarks.agent_data_runner import (
    build_contexts,
    build_plan,
    load_protocol,
    render_prompt,
    summarize,
)


REPO = Path(__file__).resolve().parent.parent
PROTOCOL = REPO / "benchmarks" / "agent_data_protocol_034.json"


def test_confirmation_protocol_builds_the_frozen_ninety_session_matrix():
    protocol, tasks = load_protocol(PROTOCOL)
    plan = build_plan(protocol, tasks)

    assert len(tasks) == 5
    assert len(plan) == 90
    cells = {
        (
            cell["agent_config"]["id"], cell["replicate"],
            cell["task"]["id"], cell["representation"],
        )
        for cell in plan
    }
    assert len(cells) == 90
    assert [cell["sequence"] for cell in plan] == list(range(1, 91))
    assert build_plan(protocol, tasks)[0]["task"]["id"] == plan[0]["task"]["id"]


def test_every_confirmation_context_is_smaller_and_exactly_round_trips():
    _, tasks = load_protocol(PROTOCOL)
    contexts = build_contexts(tasks)

    assert set(contexts) == {task["id"] for task in tasks}
    for context in contexts.values():
        assert context["toon_chars"] < context["json_chars"]
        assert len(context["semantic_sha256"]) == 64
        assert len(context["json_sha256"]) == 64
        assert len(context["toon_sha256"]) == 64


def test_prompt_contains_the_treatment_but_never_the_hidden_answer():
    _, tasks = load_protocol(PROTOCOL)
    task = tasks[0]

    prompt = render_prompt(task, "toon", "code: P228")

    assert "Context format: TOON 4.1" in prompt
    assert task["question"] in prompt
    assert "code: P228" in prompt
    assert task["expected_answer"]["repair"] not in prompt


def _successful_rows():
    rows = []
    sequence = 0
    for config in ("sol-low", "sol-medium", "terra-medium"):
        for replicate in range(1, 4):
            for task_id in ("lookup", "filter", "aggregate", "rollback", "rename"):
                for representation in ("json", "toon"):
                    sequence += 1
                    input_tokens = 1000 if representation == "json" else 950
                    rows.append({
                        "sequence": sequence,
                        "thread_id": f"thread-{sequence}",
                        "task_id": task_id,
                        "agent_config": config,
                        "representation": representation,
                        "replicate": replicate,
                        "returncode": 0,
                        "timed_out": False,
                        "parse_success": True,
                        "exact_success": True,
                        "command_count": 0,
                        "agent_errors": [],
                        "usage": {
                            "input_tokens": input_tokens,
                            "cached_input_tokens": 0,
                            "output_tokens": 20,
                            "reasoning_output_tokens": 0,
                        },
                        "total_tokens": input_tokens + 20,
                        "elapsed_seconds": 1.0,
                    })
    return rows


def test_summary_applies_all_frozen_gate_conditions():
    rows = _successful_rows()
    summary = summarize(rows)

    assert summary["sessions"] == 90
    assert summary["unique_threads"] == 90
    assert summary["gate"]["passed"] is True
    assert summary["gate"]["conditions_passed"] == 5
    assert len(summary["pairs"]) == 45

    regressed = deepcopy(rows)
    failures = [
        row for row in regressed
        if row["agent_config"] == "sol-low" and row["representation"] == "toon"
    ][:3]
    for row in failures:
        row["exact_success"] = False
    failed = summarize(regressed)
    assert failed["gate"]["conditions"]["accuracy_noninferior"] is False
    assert failed["gate"]["passed"] is False
