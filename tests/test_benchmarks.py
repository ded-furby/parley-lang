import hashlib
import json
import os
import py_compile
import shutil
import subprocess
import sys

import pytest

from conftest import REPO
from benchmarks.agent_runner import (
    command_protocol,
    load_tasks,
    rejudge_report,
    render_prompt,
    summarize,
)
from benchmarks.bundle_runner import (
    build_bundle_plan,
    load_protocol,
    render_bundle_prompt,
    summarize_bundle_results,
    write_bundle_workspace,
)

BENCHMARKS = REPO / "benchmarks"


def run_measure(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BENCHMARKS / "measure.py"), *args],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def run_prompts(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BENCHMARKS / "prompts.py"), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=120,
    )


def run_runlog(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BENCHMARKS / "runlog.py"), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_benchmark_tasks_reference_existing_examples():
    manifest = json.loads((BENCHMARKS / "tasks.json").read_text())
    tasks = manifest["tasks"]
    assert len(tasks) == 10
    assert {task["id"] for task in tasks} == {
        "hello",
        "fizzbuzz",
        "records",
        "enums_match",
        "lists_and_maps",
        "higher_order",
        "file_stats",
        "calculator",
        "guessing_game",
        "todo",
    }
    for task in tasks:
        assert (REPO / task["source"]).is_file()
        assert (BENCHMARKS / "python" / f"{task['id']}.py").is_file()
        assert (BENCHMARKS / "rust" / f"{task['id']}.rs").is_file()


def test_benchmark_manifest_records_all_reference_sources():
    manifest = json.loads((BENCHMARKS / "tasks.json").read_text())
    assert "still required" not in manifest["description"]

    for task in manifest["tasks"]:
        references = task["references"]
        assert references == {
            "parley": f"examples/{task['id']}.par",
            "python": f"benchmarks/python/{task['id']}.py",
            "rust": f"benchmarks/rust/{task['id']}.rs",
        }
        for source in references.values():
            assert (REPO / source).is_file()


def test_benchmark_measure_json_without_check(tmp_path):
    output = tmp_path / "metrics.json"
    proc = run_measure("--no-check", "--format", "json", "--output", str(output))
    assert proc.returncode == 0, proc.stderr

    report = json.loads(proc.stdout)
    assert output.is_file()
    assert report["totals"]["tasks"] == 10
    assert report["totals"]["checked_ok"] == 0
    assert set(report["totals"]["languages"]) == {"parley", "python", "rust"}
    assert report["totals"]["by_language"]["parley"]["rough_tokens"] > 0
    assert report["totals"]["by_language"]["python"]["rough_tokens"] > 0
    assert report["totals"]["by_language"]["rust"]["rough_tokens"] > 0
    assert all(row["checks"]["parley"] == {"skipped": True} for row in report["tasks"])


def test_benchmark_measure_checks_examples(tmp_path):
    output = tmp_path / "checked.json"
    proc = run_measure("--format", "json", "--output", str(output))
    assert proc.returncode == 0, proc.stderr

    report = json.loads(proc.stdout)
    assert report["totals"]["tasks"] == 10
    assert report["totals"]["checked_ok"] == 10
    assert all(row["checks"]["parley"]["ok"] for row in report["tasks"])


def test_benchmark_measure_llm_tokenizer_counts_with_tiktoken(tmp_path):
    fake_tiktoken = tmp_path / "tiktoken.py"
    fake_tiktoken.write_text(
        "class Encoding:\n"
        "    def encode(self, text):\n"
        "        return [part for part in text.split() if part]\n"
        "def get_encoding(name):\n"
        "    return Encoding()\n"
    )
    output = tmp_path / "tokenized.json"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tmp_path) + os.pathsep + env.get("PYTHONPATH", "")

    proc = run_measure(
        "--no-check",
        "--format",
        "json",
        "--llm-tokenizer",
        "cl100k_base",
        "--output",
        str(output),
        env=env,
    )
    assert proc.returncode == 0, proc.stderr

    report = json.loads(proc.stdout)
    assert report["method"]["llm_tokenizer"] == "tiktoken:cl100k_base"
    assert report["totals"]["by_language"]["parley"]["llm_tokens"] > 0
    assert report["totals"]["by_language"]["python"]["llm_tokens"] > 0
    assert report["totals"]["by_language"]["rust"]["llm_tokens"] > 0
    assert all("llm_tokens" in row["metrics"]["parley"] for row in report["tasks"])


def test_benchmark_prompt_renders_language_neutral_task():
    proc = run_prompts("--task", "hello", "--language", "parley")
    assert proc.returncode == 0, proc.stderr

    assert "# Benchmark task: Hello and interpolation" in proc.stdout
    assert "Target language: Parley" in proc.stdout
    assert "Print a greeting and a simple arithmetic result using interpolation." in proc.stdout
    assert "Do not inspect the reference implementation" in proc.stdout
    assert "examples/hello.par" not in proc.stdout


def test_benchmark_prompt_json_lists_all_tasks():
    proc = run_prompts("--language", "python", "--format", "json")
    assert proc.returncode == 0, proc.stderr

    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == 1
    assert payload["language"] == "python"
    assert payload["totals"]["prompts"] == 10
    assert payload["prompts"][0]["task_id"] == "hello"
    assert "Target language: Python" in payload["prompts"][0]["prompt"]


def test_runlog_append_captures_attempt_artifacts(tmp_path):
    source = tmp_path / "answer.par"
    prompt = tmp_path / "prompt.md"
    diagnostics = tmp_path / "diagnostics.json"
    stdout = tmp_path / "stdout.txt"
    stderr = tmp_path / "stderr.txt"
    source.write_text("to main:\n    say \"Hello\"\n")
    prompt.write_text("Write hello in Parley.\n")
    diagnostics.write_text('{"ok": true, "diagnostics": []}\n')
    stdout.write_text("Hello\n")
    stderr.write_text("")

    log = tmp_path / "runs.jsonl"
    proc = run_runlog(
        "append",
        "--log",
        str(log),
        "--task",
        "hello",
        "--language",
        "parley",
        "--model",
        "test-model",
        "--attempt",
        "1",
        "--status",
        "first_run_success",
        "--prompt-file",
        str(prompt),
        "--source-file",
        str(source),
        "--diagnostics-file",
        str(diagnostics),
        "--stdout-file",
        str(stdout),
        "--stderr-file",
        str(stderr),
        "--elapsed-seconds",
        "1.25",
    )
    assert proc.returncode == 0, proc.stderr

    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["schema_version"] == 1
    assert row["task_id"] == "hello"
    assert row["language"] == "parley"
    assert row["model"] == "test-model"
    assert row["attempt"] == 1
    assert row["status"] == "first_run_success"
    assert row["elapsed_seconds"] == 1.25
    assert row["artifacts"]["prompt_text"] == "Write hello in Parley.\n"
    assert row["artifacts"]["source_text"].startswith("to main:")
    assert row["artifacts"]["diagnostics_json"]["ok"] is True
    assert row["artifacts"]["stdout"] == "Hello\n"
    assert row["artifacts"]["stderr"] == ""


def test_runlog_summarize_aggregates_repair_turns(tmp_path):
    log = tmp_path / "runs.jsonl"
    rows = [
        {
            "schema_version": 1,
            "task_id": "hello",
            "language": "parley",
            "model": "agent-a",
            "attempt": 1,
            "repair_turn": 0,
            "status": "check_failed",
            "elapsed_seconds": 0.5,
        },
        {
            "schema_version": 1,
            "task_id": "hello",
            "language": "parley",
            "model": "agent-a",
            "attempt": 2,
            "repair_turn": 1,
            "status": "first_run_success",
            "elapsed_seconds": 0.7,
        },
        {
            "schema_version": 1,
            "task_id": "hello",
            "language": "python",
            "model": "agent-a",
            "attempt": 1,
            "repair_turn": 0,
            "status": "first_run_success",
            "elapsed_seconds": 0.2,
        },
    ]
    log.write_text("".join(json.dumps(row) + "\n" for row in rows))

    proc = run_runlog("summarize", "--log", str(log), "--format", "json")
    assert proc.returncode == 0, proc.stderr

    summary = json.loads(proc.stdout)
    assert summary["schema_version"] == 1
    assert summary["totals"]["records"] == 3
    assert summary["totals"]["groups"] == 2
    assert summary["totals"]["successes"] == 2
    assert summary["totals"]["first_run_successes"] == 1
    parley = next(group for group in summary["groups"] if group["language"] == "parley")
    assert parley["task_id"] == "hello"
    assert parley["model"] == "agent-a"
    assert parley["attempts"] == 2
    assert parley["success"] is True
    assert parley["first_run_success"] is False
    assert parley["repair_turns_to_success"] == 1
    assert parley["elapsed_seconds"] == 1.2
    python = next(group for group in summary["groups"] if group["language"] == "python")
    assert python["first_run_success"] is True
    assert python["repair_turns_to_success"] == 0


def test_python_reference_sources_compile():
    for path in sorted((BENCHMARKS / "python").glob("*.py")):
        py_compile.compile(str(path), doraise=True)


@pytest.mark.skipif(shutil.which("rustc") is None, reason="rustc not installed")
def test_rust_reference_sources_compile(tmp_path):
    for path in sorted((BENCHMARKS / "rust").glob("*.rs")):
        output = tmp_path / path.stem
        proc = subprocess.run(
            ["rustc", "--edition", "2021", str(path), "-o", str(output)],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert proc.returncode == 0, f"{path.name}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"


def test_agent_tasks_are_held_out_and_have_public_and_hidden_cases():
    tasks = load_tasks(BENCHMARKS / "agent_tasks.json")

    assert {task["id"] for task in tasks} == {
        "inventory_totals",
        "compact_ranges",
        "bracket_report",
    }
    seed_ids = {task["id"] for task in json.loads((BENCHMARKS / "tasks.json").read_text())["tasks"]}
    assert not ({task["id"] for task in tasks} & seed_ids)
    assert all(task["public_cases"] and task["hidden_cases"] for task in tasks)


def test_broad_agent_tasks_are_predeclared_and_cross_domain():
    manifest = json.loads((BENCHMARKS / "agent_tasks_broad.json").read_text())
    tasks = load_tasks(BENCHMARKS / "agent_tasks_broad.json")

    assert len(tasks) == 8
    assert {task["category"] for task in tasks} == {
        "text processing",
        "numeric stream",
        "stateful aggregation",
        "sequence transformation",
    }
    assert all(
        sum(task["category"] == category for task in tasks) == 2
        for category in {task["category"] for task in tasks}
    )
    prior_ids = {
        task["id"]
        for filename in ("tasks.json", "agent_tasks.json")
        for task in json.loads((BENCHMARKS / filename).read_text())["tasks"]
    }
    assert not ({task["id"] for task in tasks} & prior_ids)
    analysis = manifest["predeclared_analysis"]
    assert analysis["matrix"] == "8 tasks x 3 languages x 2 replicates = 48 fresh sessions"
    assert analysis["seed"] == 20260730
    assert "one task or transcript" in analysis["change_rule"]
    for task in tasks:
        assert len(task["public_cases"]) == 1
        assert len(task["hidden_cases"]) >= 4


def test_bundle_protocol_predeclares_complete_scale_matrix():
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_017.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(
        tasks,
        config["bundle_sizes"],
        config["replicates"],
        config["seed"],
    )

    assert config["bundle_sizes"] == [1, 2, 4, 8]
    assert config["parley_version"] == "parley 0.3.151"
    assert config["parley_skill_chars"] == 1_519
    assert config["parley_skill_sha256"] == hashlib.sha256(
        (REPO / "skill" / "parley" / "SKILL.md").read_bytes()
    ).hexdigest()
    assert len(plan) == 30
    assert sum(bundle["bundle_size"] for bundle in plan) == 64
    for replicate in (1, 2):
        for size in (1, 2, 4, 8):
            groups = [
                bundle for bundle in plan
                if bundle["replicate"] == replicate and bundle["bundle_size"] == size
            ]
            assert len(groups) == 8 // size
            assert sorted(task_id for bundle in groups for task_id in bundle["task_ids"]) == sorted(
                task["id"] for task in tasks
            )
    assert protocol["matrix"] == {
        "fresh_sessions": 90,
        "judged_task_solutions": 192,
        "sessions_per_language": 30,
        "task_solutions_per_language": 64,
        "derivation": "For each replicate and language: 8 one-task + 4 two-task + 2 four-task + 1 eight-task sessions.",
    }
    assert "No further instruction-compression" in protocol["instruction_rule"]


def test_bundle_protocol_018_is_an_exact_matrix_replication():
    prior = load_protocol(BENCHMARKS / "bundle_protocol_017.json")
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_018.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(
        tasks,
        config["bundle_sizes"],
        config["replicates"],
        config["seed"],
    )

    assert protocol["experiment_id"] == "018"
    assert config["parley_version"] == "parley 0.3.152"
    assert config["compiler_commit"] == "b94964ab64d85e099bf65f23280331cd3398af01"
    for frozen_field in (
        "tasks_file", "parley_skill_sha256", "parley_skill_chars",
        "bundle_sizes", "replicates", "languages", "model", "reasoning",
        "seed", "timeout_seconds", "max_workers",
    ):
        assert config[frozen_field] == prior["frozen_config"][frozen_field]
    assert protocol["matrix"] == prior["matrix"]
    assert protocol["primary_gate"] == prior["primary_gate"]
    assert [bundle["task_ids"] for bundle in plan] == [
        bundle["task_ids"] for bundle in build_bundle_plan(
            tasks,
            prior["frozen_config"]["bundle_sizes"],
            prior["frozen_config"]["replicates"],
            prior["frozen_config"]["seed"],
        )
    ]
    assert "Unsupported modulo is intentionally unchanged" in protocol["feature_boundary"]
    assert "No further instruction-compression" in protocol["instruction_rule"]


def test_bundle_prompt_injects_skill_once_and_never_hidden_cases():
    tasks = load_tasks(BENCHMARKS / "agent_tasks_broad.json")[:2]
    prompt = render_bundle_prompt(tasks, "parley", "PARLEY-SKILL-SENTINEL")

    assert prompt.count("PARLEY-SKILL-SENTINEL") == 1
    assert "stable_word_deduplication.par" in prompt
    assert "run_length_encoding.par" in prompt
    assert "the only shell command permitted is exactly `./check`" in prompt
    assert tasks[0]["hidden_cases"][3]["stdin"] not in prompt
    assert tasks[1]["hidden_cases"][3]["stdin"] not in prompt
    python = render_bundle_prompt(tasks, "python", "PARLEY-SKILL-SENTINEL")
    assert "PARLEY-SKILL-SENTINEL" not in python


def test_bundle_workspace_checker_compiles_all_python_sources(tmp_path):
    tasks = [
        {
            "id": "echo_one",
            "public_cases": [{"stdin": "alpha\n", "stdout": "alpha\n"}],
        },
        {
            "id": "echo_two",
            "public_cases": [{"stdin": "beta\n", "stdout": "beta\n"}],
        },
    ]
    integrity = write_bundle_workspace(tmp_path, tasks, "python", "unused")
    (tmp_path / "echo_one.py").write_text("print(input())\n")
    (tmp_path / "echo_two.py").write_text("print(input())\n")

    proc = subprocess.run(
        [str(tmp_path / "check")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr
    record = json.loads((tmp_path / ".benchmark_attempts.jsonl").read_text())
    assert record["ok"] is True
    assert set(record["tasks"]) == {"echo_one", "echo_two"}
    assert all(record["tasks"][task_id]["ok"] for task_id in record["tasks"])
    assert all(
        hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest
        for name, digest in integrity.items()
    )


def test_bundle_summary_applies_strict_scale_gate():
    rows = []
    for language, tokens, elapsed, first in (
        ("parley", 800, 8, 8),
        ("python", 880, 10, 7),
        ("rust", 960, 12, 8),
    ):
        rows.append({
            "bundle_size": 8,
            "task_count": 8,
            "language": language,
            "hidden_task_successes": 8,
            "hidden_bundle_success": True,
            "first_public_task_successes": first,
            "first_bundle_check_success": first == 8,
            "command_protocol_compliant": True,
            "repair_turns": 0 if first == 8 else 1,
            "total_tokens": tokens,
            "total_tokens_per_task": tokens / 8,
            "elapsed_seconds": elapsed,
            "elapsed_seconds_per_task": elapsed / 8,
            "prompt_chars_per_task": 100,
            "source_rough_tokens_per_task": 20,
            "usage": {"input_tokens": tokens - 80, "output_tokens": 80},
        })

    summary = summarize_bundle_results(rows)

    assert summary["sessions"] == 3
    assert summary["assigned_tasks"] == 24
    assert summary["strict_gate"] == {
        "scale": 8,
        "passed": True,
        "conditions": {
            "correctness": True,
            "tokens": True,
            "elapsed": True,
            "first_check": True,
        },
    }


def test_agent_prompt_includes_current_skill_only_for_parley():
    task = load_tasks(BENCHMARKS / "agent_tasks.json")[0]
    skill = "PARLEY-SKILL-SENTINEL"

    parley = render_prompt(task, "parley", skill)
    python = render_prompt(task, "python", skill)

    assert "PARLEY-SKILL-SENTINEL" in parley
    assert "PARLEY-SKILL-SENTINEL" not in python
    assert "run `./check`" in parley
    assert "Do not invoke a global language command" in parley
    assert "Do not list, read, or inspect any existing workspace file" in parley
    assert "the only shell command permitted is exactly `./check`" in parley
    assert task["hidden_cases"][1]["stdin"] not in parley


def test_agent_command_protocol_allows_only_exact_public_check():
    compliant = command_protocol([{"command": "/bin/zsh -lc ./check"}])
    assert compliant == {
        "compliant": True,
        "commands": ["/bin/zsh -lc ./check"],
        "violations": [],
    }

    exploratory = command_protocol([
        {"command": "/bin/zsh -lc 'ls -la'"},
        {"command": "/bin/zsh -lc ./check"},
    ])
    assert exploratory["compliant"] is False
    assert exploratory["violations"] == ["/bin/zsh -lc 'ls -la'"]


def test_parley_core_skill_restores_proven_reliability_contract():
    skill = (REPO / "skill" / "parley" / "SKILL.md").read_text()

    assert len(skill) == 1_519
    assert hashlib.sha256(skill.encode()).hexdigest() == (
        "6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c"
    )
    for required in [
        "to valid with line as text giving yesno:",
        'let count_input be ask for a number ""',
        "if count_input is nothing:",
        "let count be value of count_input",
        "if (valid with line):",
        "an empty list of text",
        'Literal braces are `"{{"` / `"}}"`',
        "Parenthesize expression calls",
        "Use only `./check`",
        "`let x be value` creates",
        "`set x to value` mutates or creates",
        "Numeric input uses `ask for a number`",
        "`x as number`",
        "`say` emits one full line",
        "`line split by \"\"`",
        "`map contains key`",
        "sorted `keys of map`",
        "`yesno`/`yes`/`no`",
        "references/core-v0.3.144.md",
    ]:
        assert required in skill


def test_parley_previous_core_skill_is_preserved_unchanged():
    reference = (
        REPO / "skill" / "parley" / "references" / "core-v0.3.144.md"
    ).read_text()

    assert len(reference) == 3_280
    assert hashlib.sha256(reference.encode()).hexdigest() == (
        "f2683bdc7e78e98b55f101d38f42ee32646d423e7e51ac4370f952e1c0430284"
    )


def test_parley_failed_micro_core_is_preserved_unchanged():
    reference = (
        REPO / "skill" / "parley" / "references" / "core-v0.3.145.md"
    ).read_text()

    assert len(reference) == 1_557
    assert hashlib.sha256(reference.encode()).hexdigest() == (
        "d8ca4eaf0889c200b4b14427756c884cc648702a58331cfb1fe17b5d7b2634b1"
    )


def test_parley_partial_recovery_core_is_preserved_unchanged():
    reference = (
        REPO / "skill" / "parley" / "references" / "core-v0.3.146.md"
    ).read_text()

    assert len(reference) == 1_371
    assert hashlib.sha256(reference.encode()).hexdigest() == (
        "c49d14eb2702981a9c1641f79a38239b59916e671392193bcff47424d3511e1f"
    )


def test_parley_conversion_recovery_core_is_preserved_unchanged():
    reference = (
        REPO / "skill" / "parley" / "references" / "core-v0.3.147.md"
    ).read_text()

    assert len(reference) == 1_519
    assert hashlib.sha256(reference.encode()).hexdigest() == (
        "6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c"
    )


def test_parley_reliability_core_is_preserved_unchanged():
    reference = (
        REPO / "skill" / "parley" / "references" / "core-v0.3.149.md"
    ).read_text()

    assert len(reference) == 1_519
    assert hashlib.sha256(reference.encode()).hexdigest() == (
        "6ca098e4c86161b8f688534a2d0de11f11f28ee55f92d713872378a942f6f20c"
    )


def test_parley_extended_skill_reference_preserves_rare_tooling():
    reference = (
        REPO / "skill" / "parley" / "references" / "extended-reference.md"
    ).read_text()

    assert "parley-lsp" in reference
    assert "parley package check-registry" in reference
    assert "maybe_linear_regression_number" in reference


def test_agent_summary_aggregates_fresh_run_results():
    rows = [
        {
            "task_id": "inventory_totals",
            "language": "parley",
            "hidden_success": True,
            "first_public_check_success": False,
            "public_check_attempts": 2,
            "total_tokens": 120,
            "elapsed_seconds": 3.0,
        },
        {
            "task_id": "inventory_totals",
            "language": "parley",
            "hidden_success": False,
            "first_public_check_success": True,
            "public_check_attempts": 1,
            "total_tokens": 80,
            "elapsed_seconds": 1.0,
        },
        {
            "task_id": "inventory_totals",
            "language": "python",
            "hidden_success": True,
            "first_public_check_success": True,
            "public_check_attempts": 1,
            "total_tokens": 50,
            "elapsed_seconds": 0.5,
        },
    ]

    summary = summarize(rows)

    assert summary["runs"] == 3
    assert summary["by_language"]["parley"]["hidden_success_rate"] == 0.5
    assert summary["by_language"]["parley"]["median_public_check_attempts"] == 1.5
    assert summary["by_language"]["parley"]["median_total_tokens"] == 100
    assert summary["by_language"]["python"]["hidden_success_rate"] == 1.0


def test_agent_report_can_be_rejudged_without_rerunning_agent(tmp_path):
    task = load_tasks(BENCHMARKS / "agent_tasks.json")[0]
    source = tmp_path / "solution.py"
    source.write_text(
        "import sys\n"
        "lines = sys.stdin.buffer\n"
        "n = int(lines.readline())\n"
        "totals = {}\n"
        "for _ in range(n):\n"
        "    name, change = lines.readline().split()\n"
        "    totals[name] = totals.get(name, 0) + int(change)\n"
        "for name in sorted(totals):\n"
        "    print(name.decode(), totals[name])\n"
    )
    report = {
        "protocol": {},
        "results": [{
            "task_id": task["id"],
            "language": "python",
            "workdir": str(tmp_path),
            "hidden_success": False,
            "first_public_check_success": True,
            "public_check_attempts": 1,
            "total_tokens": 10,
            "elapsed_seconds": 1,
        }],
    }

    rejudged = rejudge_report(report, {task["id"]: task}, "unused", "oracle fix")

    assert rejudged["results"][0]["hidden_success"] is True
    assert rejudged["summary"]["by_language"]["python"]["hidden_success_rate"] == 1.0
    assert rejudged["protocol"]["rejudgments"][0]["note"] == "oracle fix"
