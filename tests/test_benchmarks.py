import hashlib
import json
import os
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import benchmarks.run_fullstack_agent_036 as fullstack_036_runner
import benchmarks.run_fullstack_agent_038 as fullstack_038_runner
import benchmarks.run_fullstack_agent_039 as fullstack_039_runner
from conftest import REPO
from benchmarks.agent_runner import (
    command_protocol,
    load_tasks,
    rejudge_report,
    render_prompt,
    run_cases,
    summarize,
)
from benchmarks.agent_check_transport import (
    ParentCheckBroker,
    fifo_identity,
)
from benchmarks.bundle_runner import (
    build_bundle_plan,
    load_protocol,
    render_bundle_prompt,
    rough_token_edit_count,
    summarize_bundle_results,
    write_bundle_workspace,
)
from benchmarks.fullstack_agent_036_scaffolds import (
    LANGUAGES as FULLSTACK_036_LANGUAGES,
    ROOT_FILES as FULLSTACK_036_ROOT_FILES,
    load_task_map as load_fullstack_036_task_map,
    scaffold_files as fullstack_036_scaffold_files,
)
from benchmarks.fullstack_agent_037_guard import invalid_numeric_domain
from benchmarks.fullstack_agent_037_scaffolds import (
    LANGUAGES as FULLSTACK_037_LANGUAGES,
    ROOT_FILES as FULLSTACK_037_ROOT_FILES,
    load_task_map as load_fullstack_037_task_map,
    scaffold_files as fullstack_037_scaffold_files,
)
from benchmarks.fullstack_agent_038_guard import (
    invalid_numeric_domain as invalid_numeric_domain_038,
)
from benchmarks.fullstack_agent_038_scaffolds import (
    LANGUAGES as FULLSTACK_038_LANGUAGES,
    ROOT_FILES as FULLSTACK_038_ROOT_FILES,
    load_task_map as load_fullstack_038_task_map,
    scaffold_files as fullstack_038_scaffold_files,
)
from benchmarks.fullstack_agent_039_guard import (
    invalid_numeric_domain as invalid_numeric_domain_039,
)
from benchmarks.fullstack_agent_039_scaffolds import (
    LANGUAGES as FULLSTACK_039_LANGUAGES,
    ROOT_FILES as FULLSTACK_039_ROOT_FILES,
    load_task_map as load_fullstack_039_task_map,
    scaffold_files as fullstack_039_scaffold_files,
)
from benchmarks.run_fullstack_agent_037 import (
    _integrity as fullstack_037_integrity,
    build_plan as build_fullstack_037_plan,
    command_protocol as fullstack_037_command_protocol,
    validate_corpus as validate_fullstack_037_corpus,
    workspace_paths as fullstack_037_workspace_paths,
)
from benchmarks.run_fullstack_agent_038 import (
    build_plan as build_fullstack_038_plan,
    command_protocol as fullstack_038_command_protocol,
    validate_corpus as validate_fullstack_038_corpus,
)
from benchmarks.run_fullstack_agent_039 import (
    build_plan as build_fullstack_039_plan,
    command_protocol as fullstack_039_command_protocol,
    validate_corpus as validate_fullstack_039_corpus,
)
from benchmarks.run_fullstack_agent_036 import (
    FROZEN_PARLEY_COMMIT,
    FROZEN_PARLEY_TREE,
    FROZEN_PARLEY_VERSION,
    _integrity as fullstack_036_integrity,
    atomic_write_json as atomic_write_fullstack_036_json,
    build_plan as build_fullstack_036_plan,
    command_protocol as fullstack_036_command_protocol,
    digest as fullstack_036_digest,
    initialize_journal as initialize_fullstack_036_journal,
    load_cases as load_fullstack_036_cases,
    load_provenance as load_fullstack_036_provenance,
    load_protocol as load_fullstack_036_protocol,
    render_prompt as render_fullstack_036_prompt,
    rough_token_edit_count as fullstack_036_edit_tokens,
    source_metrics as fullstack_036_source_metrics,
    summarize as summarize_fullstack_036,
    validate_corpus as validate_fullstack_036_corpus,
    workspace_paths as fullstack_036_workspace_paths,
    write_workspace as write_fullstack_036_workspace,
)

BENCHMARKS = REPO / "benchmarks"

# The agent-facing skill that protocols 017-030 were frozen against, preserved
# byte-for-byte. Those protocols record its SHA, so they must keep checking the
# artifact their sessions actually ran with — not whatever SKILL.md says today.
FROZEN_SKILL = REPO / "skill" / "parley" / "references" / "core-v0.3.149.md"


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


def test_parent_check_broker_round_trips_without_tcp_and_preserves_attempt(tmp_path):
    workspace = tmp_path / "workspace"
    attempt_root = tmp_path / "attempts"
    evaluations = []

    def evaluate(number, request_id):
        evaluations.append((number, request_id))
        return {
            "ok": True,
            "stdout": "public parent check passed\n",
            "stderr": "",
            "judgment": {"cases": 3, "browser": True},
        }

    broker = ParentCheckBroker(workspace, evaluate, attempt_root=attempt_root)
    installed = broker.install()
    broker.start()
    completed = subprocess.run(
        ["./check"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=10,
    )
    broker.stop()

    assert completed.returncode == 0
    assert completed.stdout == "public parent check passed\n"
    assert completed.stderr == ""
    assert len(evaluations) == len(broker.attempts) == 1
    assert len(evaluations[0][1]) == 32
    assert broker.attempts[0]["judgment"] == {"cases": 3, "browser": True}
    assert json.loads((attempt_root / "attempt-001.json").read_text())["ok"] is True
    assert broker.integrity()["ok"] is True
    assert Path(installed["request_fifo"]).is_fifo()
    assert Path(installed["response_fifo"]).is_fifo()


def test_parent_check_broker_returns_evaluator_failures_and_detects_fifo_replacement(
    tmp_path,
):
    workspace = tmp_path / "workspace"

    def evaluate(number, request_id):
        raise RuntimeError("controlled evaluator failure")

    broker = ParentCheckBroker(workspace, evaluate)
    broker.install()
    broker.start()
    completed = subprocess.run(
        ["./check"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=10,
    )
    broker.stop()

    assert completed.returncode == 1
    assert "controlled evaluator failure" in completed.stderr
    assert broker.attempts[0]["ok"] is False
    assert "evaluator_error" in broker.attempts[0]

    request = workspace / ".benchmark_check_request"
    original = fifo_identity(request)
    request.unlink()
    os.mkfifo(request, mode=0o600)
    assert fifo_identity(request).inode != original.inode
    assert broker.integrity()["ok"] is False


def test_parent_check_transport_smokes_cover_both_model_strata():
    expected = {
        "agent_check_transport_smoke.json": "gpt-5.6-terra",
        "agent_check_transport_smoke_sol.json": "gpt-5.6-sol",
    }

    for filename, model in expected.items():
        result = json.loads((BENCHMARKS / filename).read_text())
        assert result["ok"] is True
        assert result["model"] == model
        assert result["reasoning"] == "medium"
        assert result["network_policy"].endswith("network_access=false")
        assert result["agent_returncode"] == 0
        assert result["command_protocol"]["compliant"] is True
        assert len(result["parent_attempts"]) == 1
        assert result["parent_attempts"][0]["ok"] is True
        assert result["parent_attempts"][0]["http"] == {
            "status": 200,
            "json": {"service": "parent-check-transport", "ready": True},
        }
        assert result["parent_attempts"][0]["browser"] == {
            "text": "42",
            "title": "Transport smoke",
        }
        assert result["protected_integrity_ok"] is True
        assert result["transport_integrity"]["ok"] is True


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


def test_arithmetic_vocabulary_corpus_is_independent_and_unprimed():
    path = BENCHMARKS / "agent_tasks_arithmetic_vocabulary.json"
    manifest = json.loads(path.read_text())
    tasks = load_tasks(path)
    prior_ids = {
        task["id"]
        for filename in ("tasks.json", "agent_tasks.json", "agent_tasks_broad.json")
        for task in json.loads((BENCHMARKS / filename).read_text())["tasks"]
    }

    assert len(tasks) == 6
    assert len({task["category"] for task in tasks}) == 6
    assert not ({task["id"] for task in tasks} & prior_ids)
    assert manifest["predeclared_analysis"]["matrix"] == (
        "6 tasks x 3 languages x 2 replicates = 36 fresh sessions"
    )
    forbidden = ("modulo", "remainder", "percent", "%")
    visible = " ".join(
        [task["title"] + " " + task["statement"] for task in tasks]
        + [case["stdin"] + case["stdout"] for task in tasks
           for group in ("public_cases", "hidden_cases") for case in task[group]]
    ).lower()
    assert all(word not in visible for word in forbidden)
    assert all(len(task["hidden_cases"]) == 4 for task in tasks)


def test_application_corpus_is_new_cross_domain_and_has_real_file_judgment():
    path = BENCHMARKS / "agent_tasks_application_023.json"
    manifest = json.loads(path.read_text())
    tasks = load_tasks(path)
    prior_ids = {
        task["id"]
        for filename in (
            "tasks.json",
            "agent_tasks.json",
            "agent_tasks_broad.json",
            "agent_tasks_arithmetic_vocabulary.json",
            "agent_tasks_broad_021.json",
        )
        for task in json.loads((BENCHMARKS / filename).read_text())["tasks"]
    }

    assert len(tasks) == 8
    assert len({task["category"] for task in tasks}) == 8
    assert not ({task["id"] for task in tasks} & prior_ids)
    assert all(len(task["public_cases"]) == 1 for task in tasks)
    assert all(len(task["hidden_cases"]) == 4 for task in tasks)
    file_task = next(task for task in tasks if task["id"] == "file_backed_notes")
    assert all(
        set(case["files"]) == {"file_backed_notes.txt"}
        for group in ("public_cases", "hidden_cases")
        for case in file_task[group]
    )
    analysis = manifest["predeclared_analysis"]
    assert analysis["matrix"] == (
        "8 tasks x 3 languages x 6 complete-bundle replicates = "
        "18 fresh sessions and 144 hidden-judged assignments"
    )
    assert analysis["seed"] == 20260809
    assert "one allowed instruction-compression experiment remains closed" in (
        analysis["instruction_rule"]
    )


def test_vocabulary_protocol_019_freezes_evidence_gate():
    protocol = json.loads((BENCHMARKS / "vocabulary_protocol_019.json").read_text())
    config = protocol["frozen_config"]

    assert protocol["experiment_id"] == "019"
    assert config["parley_version"] == "parley 0.3.152"
    assert config["compiler_commit"] == "de63314467b3738988a4b64ef986de297f5d1e58"
    assert config["languages"] == ["parley", "python", "rust"]
    assert config["replicates"] == 2
    assert config["seed"] == 20260805
    assert protocol["matrix"]["fresh_sessions"] == 36
    assert "At least two unrelated task families" in protocol["primary_analysis"]["evidence_gate"]
    assert "general usefulness" in protocol["primary_analysis"]["eligibility_is_not_adoption"].lower()
    assert "No further instruction-compression" in protocol["instruction_rule"]


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
        FROZEN_SKILL.read_bytes()
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


def test_bundle_protocol_020_concentrates_ten_replicates_at_size_eight():
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_020.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(
        tasks,
        config["bundle_sizes"],
        config["replicates"],
        config["seed"],
    )

    assert protocol["experiment_id"] == "020"
    assert config["parley_version"] == "parley 0.3.153"
    assert config["compiler_commit"] == "736a474c9752050bb82942565ac5bd09cd3662e4"
    assert config["bundle_sizes"] == [8]
    assert config["replicates"] == 10
    assert len(plan) == 10
    assert sum(bundle["bundle_size"] for bundle in plan) == 80
    assert all(bundle["bundle_size"] == 8 for bundle in plan)
    assert all(sorted(bundle["task_ids"]) == sorted(task["id"] for task in tasks) for bundle in plan)
    assert protocol["matrix"] == {
        "fresh_sessions": 30,
        "judged_task_solutions": 240,
        "sessions_per_language": 10,
        "task_solutions_per_language": 80,
        "derivation": "10 complete eight-task bundles x 3 languages",
    }
    assert protocol["primary_gate"]["scale"] == 8
    assert "No further instruction-compression" in protocol["instruction_rule"]


def test_bundle_protocol_023_freezes_new_application_matrix():
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_023.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(tasks, config["bundle_sizes"], config["replicates"], config["seed"])

    assert protocol["experiment_id"] == "023"
    assert config["parley_version"] == "parley 0.3.155"
    assert config["compiler_commit"] == "8f4a66885f3e0837f1595d72cf38ada5b8112f97"
    assert config["task_manifest_sha256"] == hashlib.sha256(
        (BENCHMARKS / "agent_tasks_application_023.json").read_bytes()
    ).hexdigest()
    assert config["parley_skill_sha256"] == hashlib.sha256(
        FROZEN_SKILL.read_bytes()
    ).hexdigest()
    assert config["bundle_sizes"] == [8]
    assert config["replicates"] == 6
    assert len(plan) == 6
    assert sum(bundle["bundle_size"] for bundle in plan) == 48
    assert protocol["matrix"]["fresh_sessions"] == 18
    assert protocol["matrix"]["judged_task_solutions"] == 144
    assert protocol["matrix"]["hidden_cases_per_language"] == 192
    assert "one allowed instruction-compression experiment is closed" in protocol["instruction_rule"]
    assert "no same-corpus syntax change" in protocol["stop_rule"]


def test_bundle_protocol_024_freezes_seeded_maintenance_matrix():
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_024.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(tasks, config["bundle_sizes"], config["replicates"], config["seed"])

    assert protocol["experiment_id"] == "024"
    assert config["parley_version"] == "parley 0.3.155"
    assert config["harness_commit"] == "cb4e3d4b5f3dd1a7ffc788622d93dcb5e1fffee8"
    assert config["task_manifest_sha256"] == hashlib.sha256(
        (BENCHMARKS / "agent_tasks_maintenance_024.json").read_bytes()
    ).hexdigest()
    assert config["parley_skill_sha256"] == hashlib.sha256(
        FROZEN_SKILL.read_bytes()
    ).hexdigest()
    assert config["bundle_sizes"] == [4]
    assert config["replicates"] == 6
    assert len(plan) == 6
    assert sum(bundle["bundle_size"] for bundle in plan) == 24
    assert protocol["matrix"]["fresh_sessions"] == 18
    assert protocol["matrix"]["judged_task_solutions"] == 72
    assert any(
        "cannot count as independent language-feature recurrence" in boundary
        for boundary in protocol["interpretation_boundary"]
    )
    assert "one allowed instruction-compression experiment is closed" in protocol["instruction_rule"]
    assert "without selective reruns" in protocol["stop_rule"]


def test_bundle_protocol_025_freezes_repository_matrix():
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_025.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(tasks, config["bundle_sizes"], config["replicates"], config["seed"])

    assert protocol["experiment_id"] == "025"
    assert config["parley_version"] == "parley 0.3.155"
    assert config["harness_commit"] == "814a05b63a9bdd9e8f3d9e5ff85cb016a3f1531d"
    assert config["task_manifest_sha256"] == hashlib.sha256(
        (BENCHMARKS / "agent_tasks_repositories_025.json").read_bytes()
    ).hexdigest()
    assert config["parley_skill_sha256"] == hashlib.sha256(
        FROZEN_SKILL.read_bytes()
    ).hexdigest()
    assert config["bundle_sizes"] == [4]
    assert config["replicates"] == 6
    assert len(plan) == 6
    assert sum(bundle["bundle_size"] for bundle in plan) == 24
    assert protocol["matrix"]["fresh_sessions"] == 18
    assert protocol["matrix"]["judged_repository_assignments"] == 72
    assert protocol["matrix"]["editable_seed_files_per_session"] == 8
    assert protocol["source_protocol"]["first_shell_command"] == "./sources"
    assert protocol["source_protocol"]["source_command_count"] == 1
    assert "one allowed instruction-compression experiment is closed" in protocol["instruction_rule"]
    assert "without selective reruns" in protocol["stop_rule"]


def test_bundle_protocol_026_freezes_eight_repository_matrix():
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_026.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(tasks, config["bundle_sizes"], config["replicates"], config["seed"])

    assert protocol["experiment_id"] == "026"
    assert config["parley_version"] == "parley 0.3.155"
    assert config["harness_commit"] == "74c0f67c3531719c491da4e7613a5f2c9e8f8e4e"
    assert config["task_manifest_sha256"] == hashlib.sha256(
        (BENCHMARKS / "agent_tasks_repositories_026.json").read_bytes()
    ).hexdigest()
    assert config["parley_skill_sha256"] == hashlib.sha256(
        FROZEN_SKILL.read_bytes()
    ).hexdigest()
    assert config["bundle_sizes"] == [8]
    assert config["replicates"] == 6
    assert len(plan) == 6
    assert sum(bundle["bundle_size"] for bundle in plan) == 48
    assert all(len(bundle["task_ids"]) == 8 for bundle in plan)
    assert protocol["matrix"]["fresh_sessions"] == 18
    assert protocol["matrix"]["judged_repository_assignments"] == 144
    assert protocol["matrix"]["editable_seed_files_per_session"] == 16
    assert protocol["matrix"]["hidden_cases_per_language"] == 192
    assert protocol["source_protocol"]["first_shell_command"] == "./sources"
    assert protocol["source_protocol"]["source_command_count"] == 1
    assert "one allowed instruction-compression experiment is closed" in protocol["instruction_rule"]
    assert "without selective reruns" in protocol["stop_rule"]


def test_bundle_protocol_027_freezes_sixteen_repository_matrix():
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_027.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(tasks, config["bundle_sizes"], config["replicates"], config["seed"])

    assert protocol["experiment_id"] == "027"
    assert config["parley_version"] == "parley 0.3.155"
    assert config["harness_commit"] == "6d10ee11961f6bffc9f6208e763637ed8c3e5b1c"
    assert config["task_manifest_sha256"] == hashlib.sha256(
        (BENCHMARKS / "agent_tasks_repositories_027.json").read_bytes()
    ).hexdigest()
    assert config["parley_skill_sha256"] == hashlib.sha256(
        FROZEN_SKILL.read_bytes()
    ).hexdigest()
    assert config["bundle_sizes"] == [16]
    assert config["replicates"] == 6
    assert len(plan) == 6
    assert sum(bundle["bundle_size"] for bundle in plan) == 96
    assert all(len(bundle["task_ids"]) == 16 for bundle in plan)
    assert protocol["matrix"]["fresh_sessions"] == 18
    assert protocol["matrix"]["judged_repository_assignments"] == 288
    assert protocol["matrix"]["editable_seed_files_per_session"] == 32
    assert protocol["matrix"]["hidden_cases_per_language"] == 384
    assert protocol["matrix"]["exact_hidden_file_cases_per_language"] == 48
    assert protocol["source_protocol"]["first_shell_command"] == "./sources"
    assert protocol["source_protocol"]["source_command_count"] == 1
    assert "one allowed instruction-compression experiment is closed" in protocol["instruction_rule"]
    assert "without selective reruns" in protocol["stop_rule"]


def test_bundle_protocol_028_freezes_project_diagnostic_matrix():
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_028.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(
        tasks, config["bundle_sizes"], config["replicates"], config["seed"]
    )

    assert protocol["experiment_id"] == "028"
    assert config["parley_version"] == "parley 0.3.155"
    assert config["harness_commit"] == "2cf86bf"
    assert config["task_manifest_sha256"] == hashlib.sha256(
        (BENCHMARKS / "agent_tasks_diagnostic_028.json").read_bytes()
    ).hexdigest()
    assert config["parley_skill_sha256"] == hashlib.sha256(
        FROZEN_SKILL.read_bytes()
    ).hexdigest()
    assert config["bundle_sizes"] == [4]
    assert config["replicates"] == 6
    assert len(plan) == 6
    assert sum(bundle["bundle_size"] for bundle in plan) == 24
    assert all(len(bundle["task_ids"]) == 4 for bundle in plan)
    assert protocol["matrix"]["fresh_sessions"] == 18
    assert protocol["matrix"]["judged_repository_assignments"] == 72
    assert protocol["matrix"]["editable_seed_files_per_session"] == 12
    assert protocol["matrix"]["read_only_context_files_per_session"] == 8
    assert protocol["matrix"]["visible_files_per_session"] == 20
    assert protocol["matrix"]["hidden_cases_per_language"] == 96
    assert protocol["matrix"]["exact_hidden_file_cases_per_language"] == 0
    assert protocol["source_protocol"]["first_shell_command"] == "./sources"
    assert protocol["source_protocol"]["source_command_count"] == 1
    assert "omitted from every agent prompt" in protocol["source_protocol"][
        "public_examples"
    ]
    assert "one allowed instruction-compression experiment is closed" in protocol[
        "instruction_rule"
    ]
    assert "without selective reruns" in protocol["stop_rule"]


def test_bundle_protocol_029_freezes_historical_diagnostic_matrix():
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_029.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(
        tasks, config["bundle_sizes"], config["replicates"], config["seed"]
    )

    assert protocol["experiment_id"] == "029"
    assert config["parley_version"] == "parley 0.3.155"
    assert config["harness_commit"] == "9c03ef56a718d0cff9dca6a29492440d77224fb6"
    assert config["task_manifest_sha256"] == hashlib.sha256(
        (BENCHMARKS / "agent_tasks_historical_029.json").read_bytes()
    ).hexdigest()
    assert config["parley_skill_sha256"] == hashlib.sha256(
        FROZEN_SKILL.read_bytes()
    ).hexdigest()
    assert config["bundle_sizes"] == [8]
    assert config["replicates"] == 6
    assert len(plan) == 6
    assert sum(bundle["bundle_size"] for bundle in plan) == 48
    assert all(len(bundle["task_ids"]) == 8 for bundle in plan)
    assert protocol["matrix"]["fresh_sessions"] == 18
    assert protocol["matrix"]["judged_repository_assignments"] == 144
    assert protocol["matrix"]["editable_seed_files_per_session"] == 24
    assert protocol["matrix"]["read_only_context_files_per_session"] == 16
    assert protocol["matrix"]["visible_files_per_session"] == 40
    assert protocol["matrix"]["read_only_context_rough_tokens_per_session"] == 710
    assert protocol["matrix"]["hidden_cases_per_language"] == 192
    assert protocol["matrix"]["root_cause_assignments_per_language"] == 48
    assert len(protocol["historical_grounding"]) == 4
    assert protocol["source_protocol"]["first_shell_command"] == "./sources"
    assert protocol["source_protocol"]["source_command_count"] == 1
    assert "All 48 Parley assignments" in protocol["maintainability_gate"][
        "root_cause"
    ]
    assert "one allowed instruction-compression experiment is closed" in protocol[
        "instruction_rule"
    ]
    assert "without selective reruns" in protocol["stop_rule"]


def test_bundle_protocol_030_freezes_ninety_session_scale_curve():
    protocol = load_protocol(BENCHMARKS / "bundle_protocol_030.json")
    config = protocol["frozen_config"]
    tasks = load_tasks(REPO / config["tasks_file"])
    plan = build_bundle_plan(
        tasks, config["bundle_sizes"], config["replicates"], config["seed"]
    )

    assert protocol["experiment_id"] == "030"
    assert config["parley_version"] == "parley 0.3.155"
    assert config["harness_commit"] == "59ff991d3d924ffbd2c295b5df0e01a5c3735142"
    assert config["task_manifest_sha256"] == hashlib.sha256(
        (BENCHMARKS / "agent_tasks_historical_029.json").read_bytes()
    ).hexdigest()
    assert config["parley_skill_sha256"] == hashlib.sha256(
        FROZEN_SKILL.read_bytes()
    ).hexdigest()
    assert config["bundle_sizes"] == [1, 2, 4, 8]
    assert config["replicates"] == 2
    assert len(plan) == 30
    assert sum(bundle["bundle_size"] for bundle in plan) == 64
    counts = {
        size: sum(bundle["bundle_size"] == size for bundle in plan)
        for size in config["bundle_sizes"]
    }
    assert counts == {1: 16, 2: 8, 4: 4, 8: 2}
    for size in config["bundle_sizes"]:
        exposures = [
            task_id
            for bundle in plan
            if bundle["bundle_size"] == size
            for task_id in bundle["task_ids"]
        ]
        assert len(exposures) == 16
        assert all(exposures.count(task["id"]) == 2 for task in tasks)
    assert protocol["matrix"]["fresh_sessions"] == 90
    assert protocol["matrix"]["judged_repository_assignments"] == 192
    assert protocol["matrix"]["repository_assignments_per_language"] == 64
    assert protocol["matrix"]["root_cause_assignments_per_language"] == 64
    assert protocol["primary_gate"]["scale"] == 8
    assert "two replicates" in protocol["primary_gate"]["verdict"]
    assert protocol["source_protocol"]["first_shell_command"] == "./sources"
    assert "one allowed instruction-compression experiment is closed" in protocol[
        "instruction_rule"
    ]
    assert "without selective reruns" in protocol["stop_rule"]


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


def test_bundle_prompt_embeds_seed_and_requires_edit_first():
    task = {
        "id": "maintain_echo",
        "title": "Maintain echo",
        "statement": "Print the input with a suffix.",
        "public_cases": [{"stdin": "a\n", "stdout": "a!\n"}],
        "hidden_cases": [{"stdin": "b\n", "stdout": "b!\n"}],
        "seed_sources": {
            "parley": 'to main:\n    say ask ""\n',
            "python": "print(input())\n",
            "rust": "fn main() {}\n",
        },
    }

    prompt = render_bundle_prompt([task], "python", "unused")

    assert "Update 1 independent Python programs in place" in prompt
    assert "first tool action must edit" in prompt
    assert "print(input())" in prompt
    assert task["hidden_cases"][0]["stdin"] not in prompt


def test_seeded_bundle_workspace_and_edit_metric(tmp_path):
    tasks = [{
        "id": "maintain_echo",
        "public_cases": [{"stdin": "alpha\n", "stdout": "alpha\n"}],
        "seed_sources": {
            "parley": 'to main:\n    say ask ""\n',
            "python": "print(input())\n",
            "rust": "fn main() {}\n",
        },
    }]

    integrity = write_bundle_workspace(tmp_path, tasks, "python", "unused")

    assert (tmp_path / "maintain_echo.py").read_text() == "print(input())\n"
    assert "maintain_echo.py" not in integrity
    assert rough_token_edit_count("print(input())\n", "print(input() + '!')\n") > 0


def test_repository_bundle_prints_sources_and_compiles_python(tmp_path):
    tasks = [{
        "id": "echo_repo",
        "title": "Echo repository",
        "statement": "Print the helper result.",
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "seed_files": {
            "parley": {"main.par": 'to main:\n    say "x"\n', "helper.par": 'to helper giving text:\n    give back "x"\n'},
            "python": {"main.py": "from helper import value\nprint(value(input()))\n", "helper.py": "def value(text):\n    return text\n"},
            "rust": {"main.rs": "fn main() {}\n", "helper.rs": "pub fn value() {}\n"},
        },
        "public_cases": [{"stdin": "alpha\n", "stdout": "alpha\n"}],
        "hidden_cases": [{"stdin": "beta\n", "stdout": "beta\n"}],
    }]

    integrity = write_bundle_workspace(tmp_path, tasks, "python", "unused")
    sources = subprocess.run(
        [str(tmp_path / "sources")], cwd=tmp_path, capture_output=True, text=True, timeout=30
    )
    checked = subprocess.run(
        [str(tmp_path / "check")], cwd=tmp_path, capture_output=True, text=True, timeout=30
    )

    assert sources.returncode == 0
    assert "===== echo_repo/helper.py =====" in sources.stdout
    assert "===== echo_repo/main.py =====" in sources.stdout
    assert ".benchmark_public.json" not in sources.stdout
    assert checked.returncode == 0, checked.stderr
    assert "echo_repo/main.py" not in integrity
    assert "sources" in integrity and "print_sources.py" in integrity


def test_repository_context_files_are_visible_read_only_and_integrity_hashed(tmp_path):
    task = {
        "id": "context_repo",
        "title": "Context repository",
        "statement": "Repair the implementation from the issue and regression evidence.",
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "seed_files": {
            "parley": {"main.par": 'to main:\n    say "old"\n'},
            "python": {"main.py": "print(input())\n"},
            "rust": {"main.rs": "fn main() {}\n"},
        },
        "context_files": {
            "parley": {"tests/regression.txt": "input: old\nexpected: new\n"},
            "python": {"tests/regression.txt": "input: old\nexpected: new\n"},
            "rust": {"tests/regression.txt": "input: old\nexpected: new\n"},
        },
        "public_cases": [{"stdin": "alpha\n", "stdout": "alpha\n"}],
        "hidden_cases": [{"stdin": "beta\n", "stdout": "beta\n"}],
    }

    integrity = write_bundle_workspace(tmp_path, [task], "python", "unused")
    sources = subprocess.run(
        [str(tmp_path / "sources")], cwd=tmp_path, capture_output=True, text=True, timeout=30
    )
    config = json.loads((tmp_path / ".benchmark_public.json").read_text())
    prompt = render_bundle_prompt([task], "python", "unused")

    assert sources.returncode == 0
    assert "===== context_repo/main.py =====" in sources.stdout
    assert "===== context_repo/tests/regression.txt [read-only] =====" in sources.stdout
    assert config["tasks"][0]["editable_files"] == ["main.py"]
    assert config["tasks"][0]["read_only_files"] == ["tests/regression.txt"]
    assert config["tasks"][0]["visible_files"] == ["main.py", "tests/regression.txt"]
    assert "declared read-only project context" in prompt
    assert "Files marked `[read-only]`" in prompt
    context_path = tmp_path / "context_repo" / "tests" / "regression.txt"
    assert "context_repo/tests/regression.txt" in integrity
    assert hashlib.sha256(context_path.read_bytes()).hexdigest() == integrity[
        "context_repo/tests/regression.txt"
    ]
    context_path.write_text("tampered\n")
    assert hashlib.sha256(context_path.read_bytes()).hexdigest() != integrity[
        "context_repo/tests/regression.txt"
    ]


def test_repository_without_context_preserves_source_output_and_prompt_contract(tmp_path):
    task = {
        "id": "plain_repo",
        "title": "Plain repository",
        "statement": "Echo input.",
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "seed_files": {
            "parley": {"main.par": 'to main:\n    say "x"\n'},
            "python": {"main.py": "print(input())\n"},
            "rust": {"main.rs": "fn main() {}\n"},
        },
        "public_cases": [{"stdin": "a\n", "stdout": "a\n"}],
        "hidden_cases": [{"stdin": "b\n", "stdout": "b\n"}],
    }

    write_bundle_workspace(tmp_path, [task], "python", "unused")
    sources = subprocess.run(
        [str(tmp_path / "sources")], cwd=tmp_path, capture_output=True, text=True, timeout=30
    )
    prompt = render_bundle_prompt([task], "python", "unused")

    assert "===== plain_repo/main.py =====" in sources.stdout
    assert "[editable]" not in sources.stdout
    assert "[read-only]" not in sources.stdout
    assert "it prints every editable source file" in prompt
    assert "Files marked `[read-only]`" not in prompt


def test_repository_prompt_can_defer_examples_to_read_only_project_evidence():
    task = {
        "id": "diagnostic_repo",
        "title": "Diagnostic repository",
        "statement": "Fix the regression described by the project evidence.",
        "show_public_examples": False,
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "seed_files": {
            "parley": {"main.par": 'to main:\n    say "broken"\n'},
            "python": {"main.py": "print('broken')\n"},
            "rust": {"main.rs": "fn main() {}\n"},
        },
        "context_files": {
            "parley": {"ISSUE.md": "Expected fixed output.\n"},
            "python": {"ISSUE.md": "Expected fixed output.\n"},
            "rust": {"ISSUE.md": "Expected fixed output.\n"},
        },
        "public_cases": [{"stdin": "secret-public-input\n", "stdout": "fixed\n"}],
        "hidden_cases": [{"stdin": "hidden\n", "stdout": "fixed\n"}],
    }

    prompt = render_bundle_prompt([task], "python", "unused")

    assert "secret-public-input" not in prompt
    assert "Public example" not in prompt
    assert "Fix the regression described by the project evidence." in prompt
    assert "declared read-only project context" in prompt


def test_repository_prompt_and_command_protocol_are_controlled():
    task = {
        "id": "echo_repo",
        "title": "Echo repository",
        "statement": "Print the helper result.",
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "seed_files": {
            "parley": {"main.par": 'to main:\n    say "x"\n'},
            "python": {"main.py": "print(input())\n"},
            "rust": {"main.rs": "fn main() {}\n"},
        },
        "public_cases": [{"stdin": "a\n", "stdout": "a\n"}],
        "hidden_cases": [{"stdin": "b\n", "stdout": "b\n"}],
    }
    prompt = render_bundle_prompt([task], "python", "unused")
    events = [
        {"command": "/bin/zsh -lc ./sources"},
        {"command": "/bin/zsh -lc ./check"},
    ]

    assert "Maintain 1 independent Python repositories" in prompt
    assert "first shell action must be exactly `./sources`" in prompt
    assert "Repository: `echo_repo/`; entrypoint: `echo_repo/main.py`" in prompt
    assert command_protocol(events, allow_sources=True)["compliant"] is True
    assert command_protocol(list(reversed(events)), allow_sources=True)["compliant"] is False


def _maintenance_024_oracle(task_id: str, stdin: str) -> tuple[str, dict[str, str]]:
    lines = iter(stdin.splitlines())
    if task_id == "invoice_net_extension":
        customer = next(lines)
        totals = {}
        subtotal = 0
        for _ in range(int(next(lines))):
            category, quantity, price = next(lines).split("|")
            amount = int(quantity) * int(price)
            subtotal += amount
            totals[category] = totals.get(category, 0) + amount
        categories = ",".join(f"{key}:{totals[key]}" for key in sorted(totals))
        discount = subtotal // 10 if subtotal >= 2000 else 0
        return (
            f"{customer}|{subtotal}|{categories}|discount={discount}|net={subtotal - discount}\n",
            {},
        )
    if task_id == "wildcard_policy_extension":
        policies = [tuple(next(lines).split("|")) for _ in range(int(next(lines)))]
        decisions = []
        allowed = 0
        denied = 0
        for _ in range(int(next(lines))):
            user, *request = next(lines).split("|")
            matched = any(
                all(policy == "*" or policy == value for policy, value in zip(rule, request))
                for rule in policies
            )
            decisions.append(f"{user}:{'allow' if matched else 'deny'}")
            allowed += int(matched)
            denied += int(not matched)
        decisions.append(f"allowed={allowed},denied={denied}")
        return "\n".join(decisions) + "\n", {}
    if task_id == "shipment_cancellation_extension":
        states = {}
        for _ in range(int(next(lines))):
            shipment_id, state = next(lines).split("|")
            states[shipment_id] = state
        transitions = {
            ("created", "pack"): "packed",
            ("packed", "ship"): "shipped",
            ("shipped", "deliver"): "delivered",
            ("created", "cancel"): "cancelled",
            ("packed", "cancel"): "cancelled",
        }
        invalid = 0
        for _ in range(int(next(lines))):
            shipment_id, action = next(lines).split("|")
            next_state = transitions.get((states.get(shipment_id), action))
            if next_state is None:
                invalid += 1
            else:
                states[shipment_id] = next_state
        summary = ",".join(f"{key}:{states[key]}" for key in sorted(states))
        return f"{summary}|invalid={invalid}\n", {}
    if task_id == "notes_index_extension":
        title = next(lines)
        notes = [next(lines) for _ in range(int(next(lines)))]
        note_file = title + "\n" + "".join(note + "\n" for note in notes)
        index_file = "".join(
            f"{index}|{note}\n"
            for index, note in enumerate(notes, 1)
            if note
        )
        stdout = f"{title}|{len(notes)}|{sum(bool(note) for note in notes)}|{sum(map(len, notes))}\n"
        return stdout, {
            "file_backed_notes.txt": note_file,
            "file_backed_notes_index.txt": index_file,
        }
    raise AssertionError(f"unknown task {task_id}")


def test_maintenance_024_cases_match_independent_oracle():
    tasks = load_tasks(BENCHMARKS / "agent_tasks_maintenance_024.json")

    for task in tasks:
        for case in task["public_cases"] + task["hidden_cases"]:
            stdout, files = _maintenance_024_oracle(task["id"], case["stdin"])
            assert case["stdout"] == stdout
            assert case.get("files", {}) == files


def test_maintenance_024_seeds_are_preserved_023_hidden_correct_sources(tmp_path):
    tasks = load_tasks(BENCHMARKS / "agent_tasks_maintenance_024.json")
    prior = json.loads(
        (BENCHMARKS / "results" / "agent_application_023_protocol_v1_v0.3.155.json")
        .read_text()
    )
    parley = shutil.which("parley")
    assert parley is not None

    for task in tasks:
        provenance = task["seed_source_provenance"]
        for language in ("parley", "python", "rust"):
            replicate = provenance[f"{language}_replicate"]
            row = next(
                row for row in prior["results"]
                if row["language"] == language and row["replicate"] == replicate
            )
            prior_task = row["task_results"][provenance["source_task"]]
            assert prior_task["hidden_success"] is True
            assert task["seed_sources"][language] == prior_task["source_text"]

    for language in ("parley", "python", "rust"):
        workdir = tmp_path / language
        workdir.mkdir()
        write_bundle_workspace(workdir, tasks, language, parley)
        proc = subprocess.run(
            [str(workdir / "check")], cwd=workdir, capture_output=True, text=True, timeout=60
        )
        assert proc.returncode == 1
        record = json.loads((workdir / ".benchmark_attempts.jsonl").read_text())
        assert all(result["compile_ok"] for result in record["tasks"].values())
        assert not any(result["ok"] for result in record["tasks"].values())


def _repositories_025_oracle(task_id: str, stdin: str) -> tuple[str, dict[str, str]]:
    lines = iter(stdin.splitlines())
    if task_id == "delivery_quote_repo":
        distance = int(next(lines))
        base = int(next(lines))
        per_km = int(next(lines))
        service = next(lines)
        quote = base + distance * per_km
        if service == "express":
            quote += 300
        if distance > 100:
            quote += 500
        return f"quote={quote}|service={service}\n", {}
    if task_id == "inventory_reservation_repo":
        stock = int(next(lines))
        demand = int(next(lines))
        reserved = int(next(lines))
        mode = next(lines)
        available = stock if mode == "urgent" else max(stock - reserved, 0)
        fulfilled = min(demand, available)
        return (
            f"fulfilled={fulfilled}|backorder={demand - fulfilled}|remaining={available - fulfilled}\n",
            {},
        )
    if task_id == "incident_routing_repo":
        decisions = []
        counts = {"email": 0, "chat": 0, "pager": 0}
        for _ in range(int(next(lines))):
            team, severity, after_hours = next(lines).split("|")
            if severity == "low":
                channel = "email"
            elif severity == "high" and after_hours == "no":
                channel = "chat"
            else:
                channel = "pager"
            counts[channel] += 1
            decisions.append(f"{team}:{channel}")
        decisions.append(
            f"email={counts['email']},chat={counts['chat']},pager={counts['pager']}"
        )
        return "\n".join(decisions) + "\n", {}
    if task_id == "filtered_report_repo":
        title = next(lines)
        count = int(next(lines))
        minimum = int(next(lines))
        entries = [next(lines) for _ in range(count)]
        accepted = [
            (index, entry) for index, entry in enumerate(entries, 1)
            if len(entry) >= minimum
        ]
        contents = title + "\n" + "".join(
            f"{index}|{entry}\n" for index, entry in accepted
        )
        return (
            f"saved={len(accepted)}|skipped={count - len(accepted)}|characters={sum(len(entry) for _, entry in accepted)}\n",
            {"filtered_report.txt": contents},
        )
    raise AssertionError(f"unknown task {task_id}")


def test_repositories_025_cases_match_independent_oracle():
    tasks = load_tasks(BENCHMARKS / "agent_tasks_repositories_025.json")

    for task in tasks:
        for case in task["public_cases"] + task["hidden_cases"]:
            stdout, files = _repositories_025_oracle(task["id"], case["stdin"])
            assert case["stdout"] == stdout
            assert case.get("files", {}) == files


def test_repositories_025_seeds_pass_old_contract_and_fail_every_new_public_case(tmp_path):
    tasks = load_tasks(BENCHMARKS / "agent_tasks_repositories_025.json")
    seed_tasks = [{**task, "public_cases": task["seed_cases"]} for task in tasks]
    parley = shutil.which("parley")
    assert parley is not None

    for language in ("parley", "python", "rust"):
        seed_dir = tmp_path / f"{language}-seed"
        seed_dir.mkdir()
        write_bundle_workspace(seed_dir, seed_tasks, language, parley)
        seed_proc = subprocess.run(
            [str(seed_dir / "check")], cwd=seed_dir, capture_output=True, text=True, timeout=60
        )
        assert seed_proc.returncode == 0, seed_proc.stderr

        new_dir = tmp_path / f"{language}-new"
        new_dir.mkdir()
        write_bundle_workspace(new_dir, tasks, language, parley)
        new_proc = subprocess.run(
            [str(new_dir / "check")], cwd=new_dir, capture_output=True, text=True, timeout=60
        )
        assert new_proc.returncode == 1
        record = json.loads((new_dir / ".benchmark_attempts.jsonl").read_text())
        assert all(result["compile_ok"] for result in record["tasks"].values())
        assert not any(result["ok"] for result in record["tasks"].values())


def _repositories_026_additions_oracle(
    task_id: str, stdin: str
) -> tuple[str, dict[str, str]]:
    lines = iter(stdin.splitlines())
    if task_id == "support_sla_repo":
        priority = next(lines)
        tier = next(lines)
        after_hours = next(lines)
        minutes = {"normal": 480, "high": 120, "critical": 30}[priority]
        if tier == "premium":
            minutes = max(minutes - 30, 15)
        if after_hours == "yes":
            minutes += 60
        return f"due_minutes={minutes}|tier={tier}\n", {}
    if task_id == "feature_rollout_repo":
        decisions = []
        allowed = 0
        count = int(next(lines))
        for _ in range(count):
            user, plan, country = next(lines).split("|")
            eligible = plan == "enterprise" or (plan == "pro" and country != "blocked")
            decision = "allow" if eligible else "deny"
            allowed += eligible
            decisions.append(f"{user}:{decision}")
        decisions.append(f"allowed={allowed},denied={count - allowed}")
        return "\n".join(decisions) + "\n", {}
    if task_id == "ledger_reconciliation_repo":
        tolerance = int(next(lines))
        count = int(next(lines))
        output = []
        matched = 0
        variance = 0
        for _ in range(count):
            entry_id, expected, actual = next(lines).split("|")
            difference = abs(int(expected) - int(actual))
            variance += difference
            if difference <= tolerance:
                matched += 1
                output.append(f"{entry_id}:match")
            else:
                output.append(f"{entry_id}:diff={difference}")
        output.append(
            f"matched={matched},unmatched={count - matched},variance={variance}"
        )
        return "\n".join(output) + "\n", {}
    if task_id == "priority_digest_repo":
        title = next(lines)
        count = int(next(lines))
        minimum = int(next(lines))
        accepted = []
        for index in range(1, count + 1):
            priority, text = next(lines).split("|", 1)
            if int(priority) >= minimum:
                accepted.append((index, int(priority), text))
        contents = title + "\n" + "".join(
            f"{index}|{priority}|{text}\n"
            for index, priority, text in accepted
        )
        return (
            f"saved={len(accepted)}|skipped={count - len(accepted)}|characters={sum(len(text) for _, _, text in accepted)}\n",
            {"priority_digest.txt": contents},
        )
    raise AssertionError(f"unknown task {task_id}")


def test_repositories_026_addition_cases_match_independent_oracle():
    tasks = load_tasks(BENCHMARKS / "agent_tasks_repositories_additions_026.json")

    for task in tasks:
        for case in task["public_cases"] + task["hidden_cases"]:
            stdout, files = _repositories_026_additions_oracle(task["id"], case["stdin"])
            assert case["stdout"] == stdout
            assert case.get("files", {}) == files


def test_repositories_026_addition_seeds_pass_old_contract_and_fail_new_public(tmp_path):
    tasks = load_tasks(BENCHMARKS / "agent_tasks_repositories_additions_026.json")
    seed_tasks = [{**task, "public_cases": task["seed_cases"]} for task in tasks]
    parley = shutil.which("parley")
    assert parley is not None

    for language in ("parley", "python", "rust"):
        seed_dir = tmp_path / f"{language}-026-seed"
        seed_dir.mkdir()
        write_bundle_workspace(seed_dir, seed_tasks, language, parley)
        seed_proc = subprocess.run(
            [str(seed_dir / "check")], cwd=seed_dir, capture_output=True, text=True, timeout=60
        )
        assert seed_proc.returncode == 0, seed_proc.stderr

        new_dir = tmp_path / f"{language}-026-new"
        new_dir.mkdir()
        write_bundle_workspace(new_dir, tasks, language, parley)
        new_proc = subprocess.run(
            [str(new_dir / "check")], cwd=new_dir, capture_output=True, text=True, timeout=60
        )
        assert new_proc.returncode == 1
        record = json.loads((new_dir / ".benchmark_attempts.jsonl").read_text())
        assert all(result["compile_ok"] for result in record["tasks"].values())
        assert not any(result["ok"] for result in record["tasks"].values())


def test_repositories_026_combines_preserved_and_unrelated_tasks():
    base = json.loads((BENCHMARKS / "agent_tasks_repositories_025.json").read_text())
    additions = json.loads(
        (BENCHMARKS / "agent_tasks_repositories_additions_026.json").read_text()
    )
    combined = json.loads((BENCHMARKS / "agent_tasks_repositories_026.json").read_text())

    assert len(combined["tasks"]) == 8
    assert combined["tasks"][:4] == base["tasks"]
    assert combined["tasks"][4:] == additions["tasks"]
    assert len({task["id"] for task in combined["tasks"]}) == 8
    assert combined["predeclared_analysis"]["matrix"].startswith("8 repositories")


def _repositories_027_additions_oracle(
    task_id: str, stdin: str
) -> tuple[str, dict[str, str]]:
    lines = iter(stdin.splitlines())
    if task_id == "shipping_manifest_repo":
        count = int(next(lines))
        output = []
        total = 0
        fragile_count = 0
        for _ in range(count):
            item_id, weight, fragile = next(lines).split("|")
            cost = int(weight) * 5 + (100 if fragile == "yes" else 0)
            total += cost
            fragile_count += fragile == "yes"
            output.append(f"{item_id}:cost={cost}")
        output.append(f"total={total}|fragile={fragile_count}")
        return "\n".join(output) + "\n", {}
    if task_id == "account_lockout_repo":
        count = int(next(lines))
        output = []
        locked = 0
        for _ in range(count):
            user, attempts, role = next(lines).split("|")
            is_locked = int(attempts) >= (10 if role == "admin" else 5)
            locked += is_locked
            output.append(f"{user}:{'locked' if is_locked else 'open'}")
        output.append(f"locked={locked},open={count - locked}")
        return "\n".join(output) + "\n", {}
    if task_id == "sensor_band_repo":
        low = int(next(lines))
        high = int(next(lines))
        count = int(next(lines))
        output = []
        counts = {"low": 0, "normal": 0, "high": 0}
        for _ in range(count):
            sensor, reading = next(lines).split("|")
            value = int(reading)
            band = "low" if value < low else "high" if value > high else "normal"
            counts[band] += 1
            output.append(f"{sensor}:{band}")
        output.append(
            f"low={counts['low']},normal={counts['normal']},high={counts['high']}"
        )
        return "\n".join(output) + "\n", {}
    if task_id == "tag_dedup_repo":
        count = int(next(lines))
        output = []
        seen = set()
        duplicates = 0
        for _ in range(count):
            tag = next(lines).lower()
            if tag in seen:
                duplicates += 1
            else:
                seen.add(tag)
                output.append(tag)
        output.append(f"unique={len(seen)},duplicates={duplicates}")
        return "\n".join(output) + "\n", {}
    if task_id == "timesheet_pay_repo":
        count = int(next(lines))
        output = []
        total = 0
        for _ in range(count):
            employee, hours, rate = next(lines).split("|")
            hours_value = int(hours)
            rate_value = int(rate)
            pay = min(hours_value, 40) * rate_value
            if hours_value > 40:
                pay += (hours_value - 40) * rate_value * 2
            total += pay
            output.append(f"{employee}:pay={pay}")
        output.append(f"total={total}")
        return "\n".join(output) + "\n", {}
    if task_id == "score_band_repo":
        pass_mark = int(next(lines))
        excellence_mark = int(next(lines))
        count = int(next(lines))
        output = []
        counts = {"excellent": 0, "pass": 0, "retry": 0}
        for _ in range(count):
            user, score = next(lines).split("|")
            value = int(score)
            band = (
                "excellent" if value >= excellence_mark
                else "pass" if value >= pass_mark
                else "retry"
            )
            counts[band] += 1
            output.append(f"{user}:{band}")
        output.append(
            f"excellent={counts['excellent']},pass={counts['pass']},retry={counts['retry']}"
        )
        return "\n".join(output) + "\n", {}
    if task_id == "delivery_batch_repo":
        capacity = int(next(lines))
        count = int(next(lines))
        output = []
        used = 0
        deferred = 0
        for _ in range(count):
            item_id, units = next(lines).split("|")
            units_value = int(units)
            if used + units_value <= capacity:
                used += units_value
                output.append(f"{item_id}:accept")
            else:
                deferred += 1
                output.append(f"{item_id}:defer")
        output.append(f"used={used},deferred={deferred}")
        return "\n".join(output) + "\n", {}
    if task_id == "path_sanitizer_repo":
        count = int(next(lines))
        output = []
        characters = 0
        for _ in range(count):
            owner, name = next(lines).split("|", 1)
            slug = name.lower().replace(" ", "-")
            characters += len(slug)
            output.append(f"{owner}:{slug}")
        output.append(f"entries={count},characters={characters}")
        return "\n".join(output) + "\n", {}
    raise AssertionError(f"unknown task {task_id}")


def test_repositories_027_addition_cases_match_independent_oracle():
    tasks = load_tasks(BENCHMARKS / "agent_tasks_repositories_additions_027.json")

    for task in tasks:
        for case in task["public_cases"] + task["hidden_cases"]:
            stdout, files = _repositories_027_additions_oracle(task["id"], case["stdin"])
            assert case["stdout"] == stdout
            assert case.get("files", {}) == files


def test_repositories_027_addition_seeds_pass_old_contract_and_fail_new_public(tmp_path):
    tasks = load_tasks(BENCHMARKS / "agent_tasks_repositories_additions_027.json")
    seed_tasks = [{**task, "public_cases": task["seed_cases"]} for task in tasks]
    parley = shutil.which("parley")
    assert parley is not None

    for language in ("parley", "python", "rust"):
        seed_dir = tmp_path / f"{language}-027-seed"
        seed_dir.mkdir()
        write_bundle_workspace(seed_dir, seed_tasks, language, parley)
        seed_proc = subprocess.run(
            [str(seed_dir / "check")], cwd=seed_dir, capture_output=True, text=True, timeout=90
        )
        assert seed_proc.returncode == 0, seed_proc.stderr

        new_dir = tmp_path / f"{language}-027-new"
        new_dir.mkdir()
        write_bundle_workspace(new_dir, tasks, language, parley)
        new_proc = subprocess.run(
            [str(new_dir / "check")], cwd=new_dir, capture_output=True, text=True, timeout=90
        )
        assert new_proc.returncode == 1
        record = json.loads((new_dir / ".benchmark_attempts.jsonl").read_text())
        assert all(result["compile_ok"] for result in record["tasks"].values())
        assert not any(result["ok"] for result in record["tasks"].values())


def test_repositories_027_combines_preserved_and_unrelated_tasks():
    base = json.loads((BENCHMARKS / "agent_tasks_repositories_026.json").read_text())
    additions = json.loads(
        (BENCHMARKS / "agent_tasks_repositories_additions_027.json").read_text()
    )
    combined = json.loads((BENCHMARKS / "agent_tasks_repositories_027.json").read_text())

    assert len(combined["tasks"]) == 16
    assert combined["tasks"][:8] == base["tasks"]
    assert combined["tasks"][8:] == additions["tasks"]
    assert len({task["id"] for task in combined["tasks"]}) == 16
    assert combined["predeclared_analysis"]["matrix"].startswith("16 repositories")


def _diagnostic_028_oracle(task_id: str, stdin: str) -> str:
    lines = iter(stdin.splitlines())
    if task_id == "invoice_boundary_project":
        subtotal = int(next(lines))
        discount = subtotal // 10 if subtotal >= 2000 else 0
        return f"subtotal={subtotal}|discount={discount}|net={subtotal - discount}\n"
    if task_id == "after_hours_routing_project":
        count = int(next(lines))
        output = []
        counts = {"email": 0, "chat": 0, "pager": 0}
        for _ in range(count):
            team, severity, after_hours = next(lines).split("|")
            channel = (
                "email" if severity == "low"
                else "pager" if severity == "critical" or after_hours == "yes"
                else "chat"
            )
            counts[channel] += 1
            output.append(f"{team}:{channel}")
        output.append(
            f"email={counts['email']},chat={counts['chat']},pager={counts['pager']}"
        )
        return "\n".join(output) + "\n"
    if task_id == "normalized_tag_project":
        count = int(next(lines))
        output = []
        seen = set()
        duplicates = 0
        for _ in range(count):
            tag = next(lines).lower()
            if tag in seen:
                duplicates += 1
            else:
                seen.add(tag)
                output.append(tag)
        output.append(f"unique={len(seen)},duplicates={duplicates}")
        return "\n".join(output) + "\n"
    if task_id == "capacity_state_project":
        capacity = int(next(lines))
        count = int(next(lines))
        output = []
        used = 0
        deferred = 0
        for _ in range(count):
            item_id, units_text = next(lines).split("|")
            units = int(units_text)
            if used + units <= capacity:
                used += units
                output.append(f"{item_id}:accept")
            else:
                deferred += 1
                output.append(f"{item_id}:defer")
        output.append(f"used={used},deferred={deferred}")
        return "\n".join(output) + "\n"
    raise AssertionError(f"unknown task {task_id}")


def test_diagnostic_028_cases_match_independent_oracle():
    tasks = load_tasks(BENCHMARKS / "agent_tasks_diagnostic_028.json")

    assert len(tasks) == 4
    for task in tasks:
        assert len(task["public_cases"]) == 1
        assert len(task["hidden_cases"]) == 4
        for case in task["public_cases"] + task["hidden_cases"]:
            assert case["stdout"] == _diagnostic_028_oracle(task["id"], case["stdin"])
            assert case.get("files", {}) == {}


def test_diagnostic_028_context_and_prompt_are_language_symmetric():
    tasks = load_tasks(BENCHMARKS / "agent_tasks_diagnostic_028.json")

    for task in tasks:
        assert task["show_public_examples"] is False
        assert all(
            len(task["seed_files"][language]) == 3
            for language in ("parley", "python", "rust")
        )
        assert all(
            len(task["context_files"][language]) == 2
            for language in ("parley", "python", "rust")
        )
        assert task["context_files"]["parley"] == task["context_files"]["python"]
        assert task["context_files"]["python"] == task["context_files"]["rust"]

    for language in ("parley", "python", "rust"):
        prompt = render_bundle_prompt(tasks, language, "unchanged Parley skill")
        assert "Public example" not in prompt
        for task in tasks:
            for case in task["public_cases"]:
                assert case["stdin"] not in prompt
                assert case["stdout"] not in prompt


def test_diagnostic_028_seeds_compile_and_fail_each_public_regression(tmp_path):
    tasks = load_tasks(BENCHMARKS / "agent_tasks_diagnostic_028.json")
    parley = shutil.which("parley")
    assert parley is not None

    for language in ("parley", "python", "rust"):
        workdir = tmp_path / f"{language}-028-seed"
        workdir.mkdir()
        integrity = write_bundle_workspace(workdir, tasks, language, parley)
        proc = subprocess.run(
            [str(workdir / "check")],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=90,
        )
        assert proc.returncode == 1
        record = json.loads((workdir / ".benchmark_attempts.jsonl").read_text())
        assert all(result["compile_ok"] for result in record["tasks"].values())
        assert not any(result["ok"] for result in record["tasks"].values())
        expected_context = {
            f"{task['id']}/{filename}"
            for task in tasks
            for filename in task["context_files"][language]
        }
        assert expected_context <= set(integrity)


def _historical_029_oracle(task_id: str, stdin: str) -> str:
    lines = iter(stdin.splitlines())
    if task_id == "config_recovery_project":
        count = int(next(lines))
        visibility = "tree"
        audit = "off"
        unknown = 0
        for _ in range(count):
            key, setting = next(lines).split("|", 1)
            if key == "visibility":
                visibility = setting
            elif key == "audit":
                audit = setting
            else:
                unknown += 1
        return f"visibility={visibility}|audit={audit}|unknown={unknown}\n"
    if task_id == "aliased_identity_cache_project":
        count = int(next(lines))
        output = []
        seen = set()
        duplicates = 0
        uncached = 0
        for _ in range(count):
            kind, source_field, _response_field, value = next(lines).split("|", 3)
            if source_field != "id":
                uncached += 1
                output.append("uncached")
                continue
            key = f"{kind}:{value}"
            if key in seen:
                duplicates += 1
                output.append(f"duplicate={key}")
            else:
                seen.add(key)
                output.append(f"stored={key}")
        output.append(
            f"entries={len(seen)}|duplicates={duplicates}|uncached={uncached}"
        )
        return "\n".join(output) + "\n"
    if task_id == "fsm_rollback_project":
        count = int(next(lines))
        output = []
        processed = 0
        terminated = False
        rejected = 0
        for _ in range(count):
            action, token = next(lines).split("|", 1)
            if action == "accept":
                if terminated:
                    rejected += 1
                    output.append("reject")
                else:
                    processed += 1
                    terminated = token == "stop"
                    output.append("accept")
            else:
                processed = max(processed - 1, 0)
                if token == "stop":
                    terminated = False
                output.append("rollback")
        state = "yes" if terminated else "no"
        output.append(
            f"processed={processed}|terminated={state}|rejected={rejected}"
        )
        return "\n".join(output) + "\n"
    if task_id == "cancellation_lock_project":
        original_lock = next(lines) == "yes"
        count = int(next(lines))
        output = []
        restored = 0
        failed = 0
        for _ in range(count):
            resource, old_value, new_value = next(lines).split("|", 2)
            if original_lock:
                restored += 1
                output.append(f"{resource}:{old_value}")
            else:
                failed += 1
                output.append(f"{resource}:{new_value}")
        output.append(f"restored={restored}|failed={failed}")
        return "\n".join(output) + "\n"
    raise AssertionError(f"unknown task {task_id}")


def test_historical_029_addition_cases_match_independent_oracle():
    tasks = load_tasks(BENCHMARKS / "agent_tasks_historical_additions_029.json")

    assert len(tasks) == 4
    for task in tasks:
        assert len(task["public_cases"]) == 1
        assert len(task["hidden_cases"]) == 4
        for case in task["public_cases"] + task["hidden_cases"]:
            assert case["stdout"] == _historical_029_oracle(
                task["id"], case["stdin"]
            )
            assert case.get("files", {}) == {}


def test_historical_029_addition_seeds_compile_and_fail_public_regressions(tmp_path):
    tasks = load_tasks(BENCHMARKS / "agent_tasks_historical_additions_029.json")
    parley = shutil.which("parley")
    assert parley is not None

    for language in ("parley", "python", "rust"):
        workdir = tmp_path / f"{language}-029-seed"
        workdir.mkdir()
        write_bundle_workspace(workdir, tasks, language, parley)
        proc = subprocess.run(
            [str(workdir / "check")],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert proc.returncode == 1
        record = json.loads((workdir / ".benchmark_attempts.jsonl").read_text())
        assert all(result["compile_ok"] for result in record["tasks"].values())
        assert not any(result["ok"] for result in record["tasks"].values())


def test_historical_029_context_and_provenance_are_language_symmetric():
    tasks = load_tasks(BENCHMARKS / "agent_tasks_historical_additions_029.json")
    urls = set()

    for task in tasks:
        assert task["show_public_examples"] is False
        assert all(
            len(task["seed_files"][language]) == 3
            for language in ("parley", "python", "rust")
        )
        assert all(
            len(task["context_files"][language]) == 2
            for language in ("parley", "python", "rust")
        )
        assert task["context_files"]["parley"] == task["context_files"]["python"]
        assert task["context_files"]["python"] == task["context_files"]["rust"]
        provenance = task["historical_inspiration"]
        assert provenance["url"].startswith("https://github.com/")
        assert provenance["adaptation"] == (
            "deterministic cross-language fixture; no upstream source copied"
        )
        urls.add(provenance["url"])
    assert len(urls) == 4

    for language in ("parley", "python", "rust"):
        prompt = render_bundle_prompt(tasks, language, "unchanged Parley skill")
        assert "Public example" not in prompt
        for task in tasks:
            assert task["public_cases"][0]["stdin"] not in prompt
            assert task["public_cases"][0]["stdout"] not in prompt


def test_historical_029_combines_preserved_028_and_new_tasks():
    base = json.loads((BENCHMARKS / "agent_tasks_diagnostic_028.json").read_text())
    additions = json.loads(
        (BENCHMARKS / "agent_tasks_historical_additions_029.json").read_text()
    )
    combined = json.loads((BENCHMARKS / "agent_tasks_historical_029.json").read_text())

    assert len(combined["tasks"]) == 8
    assert combined["tasks"][:4] == base["tasks"]
    assert combined["tasks"][4:] == additions["tasks"]
    assert len({task["id"] for task in combined["tasks"]}) == 8
    roots = combined["predeclared_analysis"]["root_cause_files"]
    assert set(roots) == {task["id"] for task in combined["tasks"]}
    for task in combined["tasks"]:
        for language in ("parley", "python", "rust"):
            assert roots[task["id"]][language] in task["seed_files"][language]


def test_repository_manifest_rejects_unsafe_seed_file_path(tmp_path):
    manifest = tmp_path / "tasks.json"
    task = {
        "id": "unsafe_repo",
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "seed_files": {
            "parley": {"main.par": "to main:\n    say 1\n"},
            "python": {"main.py": "print(1)\n", "../escape.py": "print(2)\n"},
            "rust": {"main.rs": "fn main() {}\n"},
        },
        "public_cases": [{"stdin": "", "stdout": ""}],
        "hidden_cases": [{"stdin": "", "stdout": ""}],
    }
    manifest.write_text(json.dumps({"schema_version": 1, "tasks": [task]}))

    with pytest.raises(ValueError, match="unsafe repository source path"):
        load_tasks(manifest)


@pytest.mark.parametrize(
    ("context_files", "message"),
    [
        (
            {
                "parley": {"main.par": "conflict\n"},
                "python": {"main.py": "conflict\n"},
                "rust": {"main.rs": "conflict\n"},
            },
            "context files overlap editable files",
        ),
        (
            {
                "parley": {"../escape.txt": "no\n"},
                "python": {"../escape.txt": "no\n"},
                "rust": {"../escape.txt": "no\n"},
            },
            "unsafe repository context path",
        ),
    ],
)
def test_repository_manifest_rejects_unsafe_context_files(tmp_path, context_files, message):
    manifest = tmp_path / "tasks.json"
    task = {
        "id": "unsafe_context_repo",
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "seed_files": {
            "parley": {"main.par": 'to main:\n    say "x"\n'},
            "python": {"main.py": "print('x')\n"},
            "rust": {"main.rs": "fn main() {}\n"},
        },
        "context_files": context_files,
        "public_cases": [{"stdin": "", "stdout": ""}],
        "hidden_cases": [{"stdin": "", "stdout": ""}],
    }
    manifest.write_text(json.dumps({"schema_version": 1, "tasks": [task]}))

    with pytest.raises(ValueError, match=message):
        load_tasks(manifest)


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


def test_task_manifest_expected_files_are_path_safe(tmp_path):
    manifest = tmp_path / "tasks.json"
    payload = {
        "schema_version": 1,
        "tasks": [{
            "id": "unsafe_file",
            "public_cases": [{"stdin": "", "stdout": "", "files": {"../escape.txt": "no"}}],
            "hidden_cases": [{"stdin": "", "stdout": ""}],
        }],
    }
    manifest.write_text(json.dumps(payload))

    with pytest.raises(ValueError, match="unsafe expected file path"):
        load_tasks(manifest)


def test_case_judgment_requires_exact_expected_file_and_cleans_previous_case(tmp_path):
    source = tmp_path / "writer.py"
    source.write_text(
        "from pathlib import Path\n"
        "value = input()\n"
        "if value != 'skip':\n"
        "    Path('result.txt').write_text(value + '\\n')\n"
        "print(value)\n"
    )
    cases = [
        {"stdin": "first\n", "stdout": "first\n", "files": {"result.txt": "first\n"}},
        {"stdin": "skip\n", "stdout": "skip\n", "files": {"result.txt": "first\n"}},
    ]

    results = run_cases("python", source, tmp_path / "unused", cases)

    assert results[0]["ok"] is True
    assert results[0]["actual_files"] == {"result.txt": "first\n"}
    assert results[1]["ok"] is False
    assert results[1]["actual_files"] == {"result.txt": None}


def test_bundle_workspace_checker_enforces_expected_files(tmp_path):
    tasks = [{
        "id": "write_note",
        "public_cases": [{
            "stdin": "hello\n",
            "stdout": "saved\n",
            "files": {"note.txt": "hello\n"},
        }],
    }]
    write_bundle_workspace(tmp_path, tasks, "python", "unused")
    (tmp_path / "write_note.py").write_text(
        "from pathlib import Path\n"
        "Path('note.txt').write_text(input() + '\\n')\n"
        "print('saved')\n"
    )

    proc = subprocess.run(
        [str(tmp_path / "check")], cwd=tmp_path, capture_output=True, text=True, timeout=30
    )

    assert proc.returncode == 0, proc.stderr
    record = json.loads((tmp_path / ".benchmark_attempts.jsonl").read_text())
    case = record["tasks"]["write_note"]["cases"][0]
    assert case["expected_files"] == {"note.txt": "hello\n"}
    assert case["actual_files"] == {"note.txt": "hello\n"}


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


def test_deep_confirmation_032_is_symmetric_and_independent():
    manifest = json.loads(
        (BENCHMARKS / "agent_tasks_deep_confirmation_032.json").read_text())
    analysis = manifest["predeclared_analysis"]

    assert analysis["experiment_id"] == "032"
    assert "No task mechanism" in analysis["independence_rule"]
    assert "unchanged 1,519-character Parley skill" in analysis["instruction_rule"]
    assert len(manifest["tasks"]) == 4
    assert {task["id"] for task in manifest["tasks"]} == {
        "quoted_environment_project",
        "retry_after_precedence_project",
        "webhook_raw_body_project",
        "stable_pagination_project",
    }
    for task in manifest["tasks"]:
        assert task["show_public_examples"] is False
        assert len(task["public_cases"]) == 1
        assert len(task["hidden_cases"]) == 4
        assert task["context_files"]["parley"] == task["context_files"]["python"]
        assert task["context_files"]["parley"] == task["context_files"]["rust"]
        for language in ("parley", "python", "rust"):
            assert len(task["seed_files"][language]) == 5
            assert len(task["context_files"][language]) == 3
            assert analysis["root_cause_files"][task["id"]][language]


def test_deep_confirmation_032_protocol_is_frozen_to_product_checkpoint():
    protocol_path = BENCHMARKS / "bundle_protocol_032.json"
    protocol = load_protocol(protocol_path)
    frozen = protocol["frozen_config"]

    assert protocol["experiment_id"] == "032"
    assert frozen["tasks_file"] == "benchmarks/agent_tasks_deep_confirmation_032.json"
    assert frozen["task_manifest_sha256"] == hashlib.sha256(
        (BENCHMARKS / "agent_tasks_deep_confirmation_032.json").read_bytes()
    ).hexdigest()
    assert frozen["parley_version"] == "parley 0.3.158"
    assert frozen["corpus_commit"] == "d435ecd"
    assert frozen["bundle_sizes"] == [4]
    assert frozen["replicates"] == 6
    assert protocol["matrix"]["fresh_sessions"] == 18
    assert protocol["matrix"]["judged_repository_assignments"] == 72
    assert "No task mechanism" in protocol["interpretation_boundary"][2]
    assert "closed" in protocol["instruction_rule"]


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

    assert len(skill) == 2_328
    assert hashlib.sha256(skill.encode()).hexdigest() == (
        "73973a54dcd50aaee245833f4879278ec23a62e50430ffe24964db6fb2fe9743"
    )
    # v0.4.1 teaches the two token-cutting shapes: top-level statements
    # instead of a `to main:` wrapper, and one-line maybe fallbacks.
    example = skill.split("```parley\n", 1)[1].split("```", 1)[0]
    assert "to main:" not in example
    for required in [
        "to valid with line as text giving yesno:",
        'let count be ask for a number "" otherwise 0',
        "Top-level statements are the program body",
        "`m otherwise default`",
        "`the arguments` and `the input`",
        "JSON is typed",
        "a type variable",
        "if (valid with line):",
        "an empty list of text",
        'Literal braces are `"{{"` / `"}}"`',
        "Parenthesize expression calls",
        "Use only `./check`",
        "`let x be value` creates",
        "`set x to value` mutates or creates",
        "`ask for a number`",
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


def test_parley_v050_core_is_preserved_unchanged():
    reference = (
        REPO / "skill" / "parley" / "references" / "core-v0.5.0.md"
    ).read_text()

    assert len(reference) == 2_328
    assert hashlib.sha256(reference.encode()).hexdigest() == (
        "73973a54dcd50aaee245833f4879278ec23a62e50430ffe24964db6fb2fe9743"
    )


def test_parley_v051_evaluated_core_is_preserved_unchanged():
    reference = (
        REPO / "skill" / "parley" / "references" / "core-v0.5.1.md"
    ).read_text()

    assert len(reference.encode()) == 2_330
    assert hashlib.sha256(reference.encode()).hexdigest() == (
        "73973a54dcd50aaee245833f4879278ec23a62e50430ffe24964db6fb2fe9743"
    )


def test_parley_v051_web_reference_is_compact_and_complete():
    reference = (
        REPO / "skill" / "parley" / "references" / "web-v0.5.1.md"
    ).read_text()

    assert len(reference.encode()) == 2_038
    assert hashlib.sha256(reference.encode()).hexdigest() == (
        "825bfc00a281b5fd602bc93e0dd4d264b7e0c0c70bc1288a21de6604653af38b"
    )
    for required in [
        '"schema_version": 1',
        "to status giving status_response:",
        "to create with body as create_request giving create_response:",
        "to inspect with request as web_request giving inspect_response:",
        "to update with request as web_request, body as update_request",
        "a web_request has method as text",
        "Records reject",
        "unknown or missing required fields",
        "Browser exports are deterministic scalar functions",
        "`number from (a divided by b)`",
        "`multiplied by`",
        "loadParley",
    ]:
        assert required in reference


def test_parley_v052_context_is_smaller_and_closes_039_guidance_gaps():
    core = (
        REPO / "skill" / "parley" / "references" / "core-v0.5.2.md"
    ).read_text()
    reference = (
        REPO / "skill" / "parley" / "references" / "web-v0.5.2.md"
    ).read_text()

    assert len(core.encode()) == 2_268
    assert hashlib.sha256(core.encode()).hexdigest() == (
        "05d4a2f3582f9014fc3dd97228b483f30cee968acd9183fda453ab6e54da1bec"
    )
    assert len(reference.encode()) == 2_082
    assert hashlib.sha256(reference.encode()).hexdigest() == (
        "74e3aa40fee867b4f8b970de374d2fdee53a254dab557efd3661fded22ede837"
    )
    assert len(core.encode()) + len(reference.encode()) == 4_350
    assert (
        len(fullstack_039_runner.O200K.encode(core))
        + len(fullstack_039_runner.O200K.encode(reference))
    ) == 1_164
    for required in [
        "`number from decimal`",
        "never add `otherwise`",
        "smallest owning module",
        "leave correct callers/entrypoints",
    ]:
        assert required in core
    for required in [
        "`number from (a divided by b)` truncates and is total",
        "never add `otherwise`",
        "Keep each rule in one pure included function",
        "thin browser wrappers",
        "do not edit correct callers",
        '"schema_version": 1',
        "to update with request as web_request, body as update_request",
        "Browser exports are deterministic scalar functions",
        "loadParley",
    ]:
        assert required in reference


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


def _fullstack_037_oracle(task_id, values):
    if task_id == "rail_connection_build":
        ready = (
            values["arrival_minute"]
            + values["delay_minutes"]
            + (7 if values["platform_change"] else 3)
        )
        margin = values["departure_minute"] - ready
        return {
            "ready_minute": ready,
            "margin_minutes": margin,
            "wait_minutes": max(margin, 0),
            "outcome": "make" if margin >= 0 else "miss",
        }
    if task_id == "orchard_irrigation_build":
        raw = values["dryness_points"] * values["tree_rows"] * 2
        credit = values["tree_rows"] * 5 if values["rain_expected"] else 0
        scheduled = max(raw - credit, 0)
        return {
            "raw_liters": raw,
            "rain_credit_liters": credit,
            "scheduled_liters": scheduled,
            "pump_cycles": (scheduled + 39) // 40,
            "mode": "idle" if scheduled == 0 else "active",
        }
    if task_id == "tiered_meter_repair":
        standard = min(values["consumed_units"], values["included_units"])
        excess = max(values["consumed_units"] - values["included_units"], 0)
        rate = 7 if values["peak_window"] else 4
        return {
            "standard_units": standard,
            "excess_units": excess,
            "excess_rate": rate,
            "usage_points": standard * 2 + excess * rate,
            "band": "included" if excess == 0 else "excess",
        }
    if task_id == "timeline_bucket_repair":
        offset = max(values["timestamp_second"] - values["origin_second"], 0)
        index = offset // values["bucket_seconds"]
        start = values["origin_second"] + index * values["bucket_seconds"]
        position = offset - index * values["bucket_seconds"]
        return {
            "offset_seconds": offset,
            "bucket_index": index,
            "bucket_start_second": start,
            "position_second": position,
            "location": "boundary" if position == 0 else "inside",
        }
    raise AssertionError(f"unknown 037 task: {task_id}")


def test_fullstack_037_corpus_is_independent_balanced_and_oracle_checked():
    task_document = json.loads(
        (BENCHMARKS / "fullstack_agent_037_tasks.json").read_text()
    )
    case_document = json.loads(
        (BENCHMARKS / "fullstack_agent_037_cases.json").read_text()
    )
    previous_tasks = json.loads(
        (BENCHMARKS / "fullstack_agent_036_tasks.json").read_text()
    )["tasks"]
    previous_cases = json.loads(
        (BENCHMARKS / "fullstack_agent_036_cases.json").read_text()
    )["tasks"]
    tasks = task_document["tasks"]

    assert task_document["experiment_id"] == case_document["experiment_id"] == "037"
    assert len(tasks) == 4
    assert [task["kind"] for task in tasks].count("implementation") == 2
    assert [task["kind"] for task in tasks].count("maintenance") == 2
    assert {task["id"] for task in tasks} == set(case_document["tasks"])

    old_ids = {task["id"] for task in previous_tasks}
    old_request_fields = {
        field for task in previous_tasks for field in task["request_fields"]
    }
    old_response_fields = {
        field for task in previous_tasks for field in task["response_fields"]
    }
    old_routes = {
        route
        for task in previous_tasks
        for route in (task["status_route"], task["post_route"])
    }
    old_exports = {task["browser_export"] for task in previous_tasks}
    old_case_ids = {
        case["id"] for cases in previous_cases.values() for case in cases
    }
    assert old_ids.isdisjoint(task["id"] for task in tasks)
    assert old_request_fields.isdisjoint(
        field for task in tasks for field in task["request_fields"]
    )
    assert old_response_fields.isdisjoint(
        field for task in tasks for field in task["response_fields"]
    )
    assert old_routes.isdisjoint(
        route for task in tasks for route in (task["status_route"], task["post_route"])
    )
    assert old_exports.isdisjoint(task["browser_export"] for task in tasks)

    all_case_ids = []
    for task in tasks:
        cases = case_document["tasks"][task["id"]]
        public = [case for case in cases if case["visibility"] == "public"]
        hidden = [case for case in cases if case["visibility"] == "hidden"]
        all_case_ids.extend(case["id"] for case in cases)

        assert len(cases) == 9
        assert len(public) == 4 and len(hidden) == 5
        assert sum(case["target"] == "browser" for case in public) == 1
        assert sum(case["target"] == "browser" for case in hidden) == 2
        assert task["public_case_ids"] == [case["id"] for case in public]
        assert task["hidden_case_ids"] == [case["id"] for case in hidden]

        field_order = list(task["request_fields"])
        for case in cases:
            if case["target"] == "browser":
                values = dict(zip(field_order, case["args"], strict=True))
                result = _fullstack_037_oracle(task["id"], values)
                assert case["export"] == task["browser_export"]
                assert case["expected"] == result[task["shared_result_field"]]
            elif case["method"] == "GET":
                assert case["path"] == task["status_route"]
                assert case["expected_json"] == {
                    "service": task["service"],
                    "ready": True,
                }
            elif case["expected_status"] == 200:
                assert case["path"] == task["post_route"]
                assert case["expected_json"] == _fullstack_037_oracle(
                    task["id"], case["json"]
                )
            else:
                assert case["expected_error"] in {
                    "invalid_json",
                    "json_content_type_required",
                }

    assert len(all_case_ids) == len(set(all_case_ids)) == 36
    assert old_case_ids.isdisjoint(all_case_ids)


def test_fullstack_037_protocol_freezes_matrix_product_and_transport():
    protocol = json.loads(
        (BENCHMARKS / "fullstack_agent_037_protocol.json").read_text()
    )
    product = protocol["frozen_product"]
    transport = protocol["validated_transport"]
    config = protocol["frozen_config"]
    matrix = protocol["matrix"]

    assert protocol["experiment_id"] == "037"
    assert protocol["protocol_revision"] == 2
    assert product["product_commit"] == "02cd809f35dfa9f93468e59cfc8a38d97abb41ee"
    assert product["corpus_commit"] == "b3ddad835758ee077a35ec318322b5149a25b88f"
    for file_key, hash_key in (
        ("tasks_file", "tasks_sha256"),
        ("cases_file", "cases_sha256"),
        ("parley_skill_file", "parley_skill_sha256"),
        ("parley_web_reference_file", "parley_web_reference_sha256"),
    ):
        assert hashlib.sha256((REPO / product[file_key]).read_bytes()).hexdigest() == product[
            hash_key
        ]
    for file_key, hash_key in (
        ("transport_file", "transport_sha256"),
        ("terra_smoke_file", "terra_smoke_sha256"),
        ("sol_smoke_file", "sol_smoke_sha256"),
    ):
        assert hashlib.sha256((REPO / transport[file_key]).read_bytes()).hexdigest() == transport[
            hash_key
        ]

    assert config["languages"] == ["parley", "python", "typescript", "rust"]
    assert [item["id"] for item in config["agent_configurations"]] == [
        "sol-medium",
        "terra-medium",
    ]
    assert config["replicates_per_task_language_configuration"] == 3
    assert config["max_public_check_attempts"] == 12
    assert matrix["fresh_sessions"] == 96
    assert matrix["frozen_public_case_executions_across_first_checks"] == 384
    assert matrix["hidden_case_executions"] == 480
    assert "real-Chromium" in protocol["session_protocol"]["public_feedback"]
    assert any(
        "cannot prove universal language superiority" in boundary
        for boundary in protocol["interpretation_boundary"]
    )
    assert "no same-corpus optimization or rerun" in protocol["stop_rule"]
    execution = protocol["execution_freeze"]
    assert execution["measured_sessions_before_freeze"] == 0
    assert execution["harness_commit"] == "10664d592d2655bd528374c7f77c4d3226b0d1b7"
    assert len(execution["files"]) == 16
    for item in execution["files"]:
        assert hashlib.sha256((REPO / item["file"]).read_bytes()).hexdigest() == item[
            "sha256"
        ]


def test_fullstack_037_scaffolds_and_plan_preserve_frozen_boundaries():
    tasks = load_fullstack_037_task_map()
    protocol = json.loads(
        (BENCHMARKS / "fullstack_agent_037_protocol.json").read_text()
    )
    config = protocol["frozen_config"]

    assert validate_fullstack_037_corpus() == {
        "tasks": 4,
        "cases": 36,
        "public_cases": 16,
        "hidden_cases": 20,
        "sessions": 96,
    }
    plan = build_fullstack_037_plan(
        list(tasks.values()),
        config["languages"],
        config["agent_configurations"],
        config["replicates_per_task_language_configuration"],
        config["seed"],
    )
    assert len(plan) == len({row["cell_id"] for row in plan}) == 96
    assert all(
        sum(row["language"] == language for row in plan) == 24
        for language in FULLSTACK_037_LANGUAGES
    )

    for task in tasks.values():
        for language in FULLSTACK_037_LANGUAGES:
            seed = fullstack_037_scaffold_files(task, language, "seed")
            reference = fullstack_037_scaffold_files(task, language, "reference")
            assert set(seed) == set(reference)
            assert all(spec.text.endswith("\n") for spec in seed.values())
            assert seed["CONTRACT.md"].editable is False
            changed = sorted(
                name for name in seed if seed[name].text != reference[name].text
            )
            if task["kind"] == "maintenance":
                assert changed == list(FULLSTACK_037_ROOT_FILES[language])
            else:
                assert changed

    rust_manifest = (BENCHMARKS / "fullstack_037/rust/Cargo.toml").read_text()
    rust_lock = (BENCHMARKS / "fullstack_037/rust/Cargo.lock").read_text()
    assert 'name = "fullstack-agent-037"' in rust_manifest
    assert 'name = "fullstack-agent-037"' in rust_lock
    assert 'name = "release-radar-035"' not in rust_lock

    validation = json.loads(
        (BENCHMARKS / "fullstack_agent_037_validation.json").read_text()
    )
    assert validation["reference_cells_passed"] == 16
    assert validation["seed_cells_built"] == 16
    assert validation["seed_cells_correct"] == 0
    assert validation["maintenance_root_boundaries_passed"] == 8
    assert len(validation["cells"]) == 16
    assert all(cell["reference_cases"] == 9 for cell in validation["cells"])


def test_fullstack_037_numeric_guard_and_command_limit_are_exact():
    tasks = load_fullstack_037_task_map()
    timeline = tasks["timeline_bucket_repair"]
    rail = tasks["rail_connection_build"]

    assert invalid_numeric_domain(
        timeline,
        b'{"timestamp_second":1060,"origin_second":1000,"bucket_seconds":0}',
    )
    assert not invalid_numeric_domain(
        timeline,
        b'{"timestamp_second":1060,"origin_second":1000,"bucket_seconds":30}',
    )
    assert invalid_numeric_domain(
        rail,
        b'{"arrival_minute":-1,"delay_minutes":0,"departure_minute":2,"platform_change":false}',
    )
    assert not invalid_numeric_domain(rail, b'{"arrival_minute":"-1"}')

    compliant = fullstack_037_command_protocol(
        [
            {"command": "/bin/zsh -lc ./sources"},
            {"command": "/bin/zsh -lc ./check"},
        ]
    )
    assert compliant["compliant"] is True
    excessive = fullstack_037_command_protocol(
        [{"command": "./sources"}] + [{"command": "./check"}] * 13
    )
    assert excessive["compliant"] is False
    assert "public check limit exceeded" in excessive["violations"][-1]


def test_fullstack_037_integrity_rejects_symlinks_and_added_empty_directories(
    tmp_path,
):
    protected = tmp_path / "protected.txt"
    protected.write_text("frozen\n")
    expected = {"protected.txt": hashlib.sha256(protected.read_bytes()).hexdigest()}
    initial = fullstack_037_workspace_paths(tmp_path)
    assert fullstack_037_integrity(tmp_path, expected) is True

    target = tmp_path / "same-content.txt"
    target.write_text("frozen\n")
    protected.unlink()
    protected.symlink_to(target)
    assert fullstack_037_integrity(tmp_path, expected) is False

    added = tmp_path / "unexpected-empty"
    added.mkdir()
    assert "unexpected-empty/" in set(fullstack_037_workspace_paths(tmp_path)) - set(
        initial
    )


def test_fullstack_036_corpus_hashes_matrix_and_case_visibility_are_frozen():
    summary = validate_fullstack_036_corpus()

    assert summary == {
        "tasks": 4,
        "cases": 32,
        "public_cases": 12,
        "hidden_cases": 20,
        "sessions": 96,
    }
    protocol = load_fullstack_036_protocol()
    assert protocol["protocol_revision"] == 2
    assert protocol["frozen_product"]["product_commit"] == "02cd809"
    assert protocol["frozen_product"]["corpus_commit"].startswith("0d26bb9")
    assert protocol["matrix"]["fresh_sessions"] == 96
    execution = protocol["execution_freeze"]
    assert execution["measured_sessions_before_amendment"] == 0
    for file_key, sha_key in (
        ("runner_file", "runner_sha256"),
        ("scaffolds_file", "scaffolds_sha256"),
        ("preparer_file", "preparer_sha256"),
        ("amendment_file", "amendment_sha256"),
    ):
        assert fullstack_036_digest(REPO / execution[file_key]) == execution[sha_key]


def test_fullstack_036_plan_is_deterministic_complete_and_balanced():
    protocol = load_fullstack_036_protocol()
    config = protocol["frozen_config"]
    tasks = list(load_fullstack_036_task_map().values())
    args = (
        tasks,
        config["languages"],
        config["agent_configurations"],
        config["replicates_per_task_language_configuration"],
        config["seed"],
    )

    first = build_fullstack_036_plan(*args)
    second = build_fullstack_036_plan(*args)

    assert [row["task_id"] for row in first] == [row["task_id"] for row in second]
    assert len(first) == 96
    keys = {
        (row["task_id"], row["language"], row["configuration_id"], row["replicate"])
        for row in first
    }
    assert len(keys) == 96
    assert {row["language"] for row in first} == set(FULLSTACK_036_LANGUAGES)
    assert all(
        sum(row["language"] == language for row in first) == 24
        for language in FULLSTACK_036_LANGUAGES
    )


def test_fullstack_036_scaffolds_preserve_maintenance_root_boundaries():
    tasks = load_fullstack_036_task_map()
    for task in tasks.values():
        for language in FULLSTACK_036_LANGUAGES:
            seed = fullstack_036_scaffold_files(task, language, "seed")
            reference = fullstack_036_scaffold_files(task, language, "reference")
            assert set(seed) == set(reference)
            assert all(value.text.endswith("\n") for value in seed.values())
            assert "CONTRACT.md" in seed and seed["CONTRACT.md"].editable is False
            if task["kind"] == "maintenance":
                changed = sorted(
                    name for name in seed if seed[name].text != reference[name].text
                )
                assert changed == list(FULLSTACK_036_ROOT_FILES[language])


def test_fullstack_036_prompt_exposes_public_cases_and_withholds_hidden_values():
    task = load_fullstack_036_task_map()["shipping_quote_build"]
    cases = load_fullstack_036_cases()[task["id"]]
    prompt = render_fullstack_036_prompt(
        task,
        cases,
        "parley",
        "FROZEN SKILL",
        "FROZEN WEB REFERENCE",
    )

    assert "Your first shell command must be exactly `./sources`" in prompt
    assert "shipping_economy" in prompt
    assert "shipping_browser_tracked" not in prompt
    assert "FROZEN SKILL" in prompt
    assert "FROZEN WEB REFERENCE" in prompt

    python_prompt = render_fullstack_036_prompt(
        task,
        cases,
        "python",
        "FROZEN SKILL",
        "FROZEN WEB REFERENCE",
    )
    assert "FROZEN SKILL" not in python_prompt
    assert "FROZEN WEB REFERENCE" not in python_prompt
    assert "FastAPI/Pydantic" in python_prompt


def test_fullstack_036_command_protocol_requires_one_sources_then_checks():
    compliant = fullstack_036_command_protocol([
        {"command": "./sources"},
        {"command": "./check"},
        {"command": "./check"},
    ])
    assert compliant["compliant"] is True

    repeated = fullstack_036_command_protocol([
        {"command": "./sources"},
        {"command": "./sources"},
        {"command": "./check"},
    ])
    assert repeated["compliant"] is False
    assert "expected exactly one ./sources, observed 2" in repeated["violations"]

    reconnaissance = fullstack_036_command_protocol([
        {"command": "ls"},
        {"command": "./sources"},
        {"command": "./check"},
    ])
    assert reconnaissance["compliant"] is False
    assert "ls" in reconnaissance["violations"]
    assert "first shell command was not ./sources" in reconnaissance["violations"]


def test_fullstack_036_source_metrics_include_o200k_and_seed_edit_size():
    before = "to total with x Int -> Int:\n    return x + 1\n"
    after = "to total with x Int -> Int:\n    return x + 2\n"

    metrics = fullstack_036_source_metrics(after)

    assert metrics["bytes"] == len(after.encode())
    assert metrics["rough_tokens"] > 0
    assert metrics["o200k_base_tokens"] > 0
    assert fullstack_036_edit_tokens(before, after) == 2


def test_fullstack_036_workspace_tracks_read_only_hashes_and_added_files(tmp_path):
    task = load_fullstack_036_task_map()["shipping_quote_build"]
    written = write_fullstack_036_workspace(tmp_path, task, "parley", "/tmp/parley")
    initial = fullstack_036_workspace_paths(tmp_path)

    assert written["read_only_hashes"]
    assert fullstack_036_integrity(tmp_path, written["read_only_hashes"]) is True

    (tmp_path / "extra.par").write_text("to evade:\n    return 1\n")
    assert sorted(set(fullstack_036_workspace_paths(tmp_path)) - set(initial)) == ["extra.par"]

    read_only = next(iter(written["read_only_hashes"]))
    (tmp_path / read_only).write_text("tampered\n")
    assert fullstack_036_integrity(tmp_path, written["read_only_hashes"]) is False


def test_fullstack_036_provenance_binds_exact_release_and_executable(
    tmp_path, monkeypatch
):
    executable = tmp_path / "parley"
    executable.write_text("#!/bin/sh\necho parley 0.5.0\n")
    executable.chmod(0o755)
    parley_python = tmp_path / "python"
    parley_python.write_text("parley python\n")
    python_runtime = tmp_path / "runtime-python"
    python_runtime.write_text("python runtime\n")
    typescript_root = tmp_path / "typescript"
    typescript_modules = typescript_root / "node_modules"
    typescript_modules.mkdir(parents=True)
    typescript_compiler = typescript_modules / ".bin/tsc"
    typescript_compiler.parent.mkdir()
    typescript_compiler.write_text("typescript compiler\n")
    host_python = tmp_path / "host-python"
    host_python.write_text("host python\n")
    browser = tmp_path / "chromium"
    browser.write_text("chromium\n")
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "pyproject.toml").write_text("[project]\nname='parley'\n")
    package_root = tmp_path / "package"
    package_root.mkdir()
    (package_root / "__init__.py").write_text("VERSION = '0.5.0'\n")
    parley_site_packages = tmp_path / "parley-site-packages"
    parley_site_packages.mkdir()
    (parley_site_packages / "parley.dist-info").write_text("frozen\n")
    python_site_packages = tmp_path / "python-site-packages"
    python_site_packages.mkdir()
    (python_site_packages / "fastapi.dist-info").write_text("frozen\n")
    monkeypatch.setattr(fullstack_036_runner, "PYTHON_RUNTIME", python_runtime)
    monkeypatch.setattr(fullstack_036_runner, "TS_DEPENDENCY_ROOT", typescript_root)
    monkeypatch.setattr(fullstack_036_runner, "TS_MODULES", typescript_modules)
    monkeypatch.setattr(fullstack_036_runner, "TS_COMPILER", typescript_compiler)
    monkeypatch.setattr(
        fullstack_036_runner,
        "frozen_source_archive_sha256",
        lambda: "archive-sha",
    )

    versions = {
        str(executable): FROZEN_PARLEY_VERSION,
        str(python_runtime): "Python test",
        str(typescript_compiler): "Version test",
        "node": "vtest",
        "npm": "10.test",
        "rustc": "rustc test",
        "cargo": "cargo test",
    }

    def fake_run(command, **kwargs):
        if "freeze" in command:
            stdout = "frozen==1\n"
        elif command[:3] == ["npm", "ls", "--all"]:
            stdout = "{}\n"
        else:
            stdout = versions[str(command[0])] + "\n"
        return subprocess.CompletedProcess(command, 0, stdout, "")

    monkeypatch.setattr(fullstack_036_runner, "run", fake_run)
    provenance = {
        "schema_version": 1,
        "experiment_id": "036",
        "parley": {
            "source_commit": FROZEN_PARLEY_COMMIT,
            "source_tree": FROZEN_PARLEY_TREE,
            "reported_version": FROZEN_PARLEY_VERSION,
            "source_archive_sha256": "archive-sha",
            "source_root": str(source_root),
            "source_tree_sha256": fullstack_036_runner.tree_digest(source_root),
            "package_root": str(package_root),
            "package_tree_sha256": fullstack_036_runner.tree_digest(package_root),
            "site_packages_root": str(parley_site_packages),
            "site_packages_tree_sha256": fullstack_036_runner.tree_digest(
                parley_site_packages
            ),
            "executable": str(executable.resolve()),
            "executable_sha256": fullstack_036_digest(executable),
            "pip_freeze": "frozen==1\n",
        },
        "environment": {
            "platform": fullstack_036_runner.platform.platform(),
            "machine": fullstack_036_runner.platform.machine(),
            "host_python_executable": str(host_python),
            "host_python_executable_sha256": fullstack_036_digest(host_python),
            "python_runtime": str(python_runtime),
            "python_runtime_version": "Python test",
            "python_runtime_executable_sha256": fullstack_036_digest(python_runtime),
            "python_pip_freeze": "frozen==1\n",
            "python_site_packages": str(python_site_packages),
            "python_site_packages_tree_sha256": fullstack_036_runner.tree_digest(
                python_site_packages
            ),
            "typescript_modules": str(typescript_modules),
            "typescript_version": "Version test",
            "typescript_compiler_sha256": fullstack_036_digest(typescript_compiler),
            "typescript_npm_tree_sha256": hashlib.sha256(b"{}\n").hexdigest(),
            "typescript_modules_tree_sha256": fullstack_036_runner.tree_digest(
                typescript_modules
            ),
            "node_version": "vtest",
            "npm_version": "10.test",
            "rustc_version": "rustc test",
            "cargo_version": "cargo test",
            "playwright_version": fullstack_036_runner.importlib.metadata.version(
                "playwright"
            ),
            "browser_executable": str(browser),
            "browser_executable_sha256": fullstack_036_digest(browser),
            "python_requirements_lock_sha256": fullstack_036_digest(
                BENCHMARKS / "fullstack_035/python/requirements.lock.txt"
            ),
            "typescript_lock_sha256": fullstack_036_digest(
                BENCHMARKS / "fullstack_035/typescript/package-lock.json"
            ),
            "rust_lock_sha256": fullstack_036_digest(
                BENCHMARKS / "fullstack_035/rust/Cargo.lock"
            ),
        },
    }
    path = tmp_path / "provenance.json"
    path.write_text(json.dumps(provenance))

    assert load_fullstack_036_provenance(path, str(executable)) == provenance

    provenance["parley"]["source_commit"] = "wrong"
    path.write_text(json.dumps(provenance))
    with pytest.raises(ValueError, match="source_commit"):
        load_fullstack_036_provenance(path, str(executable))


def test_fullstack_036_resume_marks_started_cell_failed_without_rerun(tmp_path):
    protocol = load_fullstack_036_protocol()
    config = protocol["frozen_config"]
    plan = build_fullstack_036_plan(
        list(load_fullstack_036_task_map().values()),
        config["languages"],
        config["agent_configurations"],
        config["replicates_per_task_language_configuration"],
        config["seed"],
    )[:1]
    cell = plan[0]
    journal = tmp_path / "journal"
    journal.mkdir()
    started = journal / f"{cell['cell_id']}.started.json"
    atomic_write_fullstack_036_json(
        started,
        {
            "schema_version": 1,
            "experiment_id": "036",
            "status": "started",
            "cell": {
                key: cell[key]
                for key in (
                    "cell_id",
                    "plan_index",
                    "task_id",
                    "task_kind",
                    "language",
                    "configuration_id",
                    "replicate",
                )
            },
        },
    )

    completed, pending = initialize_fullstack_036_journal(plan, journal, resume=True)

    assert pending == []
    assert len(completed) == 1
    assert completed[0]["interrupted_before_completion"] is True
    assert completed[0]["journal_attempt"] == 1
    assert (journal / f"{cell['cell_id']}.finished.json").is_file()


def _fullstack_036_passing_rows():
    protocol = load_fullstack_036_protocol()
    rows = []
    values = {
        "parley": (100, 1.0),
        "python": (120, 2.0),
        "typescript": (130, 2.5),
        "rust": (140, 3.0),
    }
    for task in load_fullstack_036_task_map().values():
        for language in FULLSTACK_036_LANGUAGES:
            for configuration in protocol["frozen_config"]["agent_configurations"]:
                for replicate in range(1, 4):
                    tokens, elapsed = values[language]
                    cell_id = f"{task['id']}__{language}__{configuration['id']}__r{replicate}"
                    rows.append({
                        "cell_id": cell_id,
                        "plan_index": len(rows) + 1,
                        "task_id": task["id"],
                        "task_kind": task["kind"],
                        "language": language,
                        "configuration_id": configuration["id"],
                        "replicate": replicate,
                        "thread_id": (
                            f"{task['id']}-{language}-{configuration['id']}-{replicate}"
                        ),
                        "checker_integrity_ok": True,
                        "read_only_integrity_ok": True,
                        "symlink_integrity_ok": True,
                        "workspace_integrity_ok": True,
                        "unexpected_files": [],
                        "command_protocol": {"compliant": True},
                        "fresh_ephemeral_session": True,
                        "journal_attempt": 1,
                        "agent_returncode": 0,
                        "agent_timed_out": False,
                        "agent_errors": [],
                        "hidden_success": True,
                        "first_public_check_success": True,
                        "exact_root": True,
                        "total_tokens": tokens,
                        "elapsed_seconds": elapsed,
                        "repair_turns": 0,
                    })
    return rows


def test_fullstack_036_summary_applies_all_six_preregistered_conditions():
    protocol = load_fullstack_036_protocol()
    rows = _fullstack_036_passing_rows()

    passing = summarize_fullstack_036(rows, protocol)
    assert passing["primary_gate"]["passed"] is True
    assert passing["primary_gate"]["conditions"] == {
        "execution_integrity": True,
        "correctness": True,
        "first_check": True,
        "tokens": True,
        "elapsed": True,
        "maintainability": True,
    }

    for row in rows:
        if row["language"] == "parley":
            row["total_tokens"] = 200
    failed = summarize_fullstack_036(rows, protocol)
    assert failed["primary_gate"]["conditions"]["tokens"] is False
    assert failed["primary_gate"]["passed"] is False


def test_fullstack_036_root_rate_uses_only_hidden_correct_maintenance_rows():
    protocol = load_fullstack_036_protocol()
    rows = _fullstack_036_passing_rows()
    excluded = next(
        row
        for row in rows
        if row["language"] == "parley" and row["task_kind"] == "maintenance"
    )
    excluded["hidden_success"] = False
    excluded["exact_root"] = False

    summary = summarize_fullstack_036(rows, protocol)
    maintenance = summary["by_kind"]["maintenance"]["parley"]

    assert maintenance["hidden_correct_maintenance_rows"] == 11
    assert maintenance["exact_root_successes"] == 11
    assert maintenance["exact_root_rate"] == 1.0
    assert summary["primary_gate"]["conditions"]["maintainability"] is True
    assert summary["primary_gate"]["conditions"]["correctness"] is False


def test_fullstack_036_reference_validation_artifact_is_complete():
    validation = json.loads(
        (BENCHMARKS / "fullstack_agent_036_validation.json").read_text()
    )
    assert len(validation["cells"]) == 16
    assert validation["reference_cells_passed"] == 16
    assert validation["seed_cells_built"] == 16
    assert validation["seed_cells_correct"] == 0
    assert validation["maintenance_root_boundaries_passed"] == 8
    assert all(row["reference_cases"] == 8 for row in validation["cells"])


def test_fullstack_036_raw_result_and_canonical_report_preserve_invalid_run():
    raw_path = BENCHMARKS / "results/fullstack_agent_036_raw.json"
    raw = json.loads(raw_path.read_text())

    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == (
        "bb644554d9cf135198e31330c6a8d6a2e5876de6633a487335679947aaced096"
    )
    assert len(raw["results"]) == 96
    assert len({row["cell_id"] for row in raw["results"]}) == 96
    assert len({row["thread_id"] for row in raw["results"]}) == 96
    assert all(row["journal_attempt"] == 1 for row in raw["results"])
    assert raw["summary"]["primary_gate"]["passed"] is False
    assert raw["summary"]["primary_gate"]["conditions"] == {
        "execution_integrity": False,
        "correctness": True,
        "first_check": True,
        "tokens": False,
        "elapsed": False,
        "maintainability": True,
    }

    attempts = [
        attempt
        for row in raw["results"]
        for attempt in row["public_attempts"]
    ]
    assert len(attempts) == 179
    assert all(attempt["build"]["ok"] for attempt in attempts)
    assert all(
        attempt.get("runtime_error") == "[Errno 1] Operation not permitted"
        for attempt in attempts
    )
    assert all(not attempt["cases"] for attempt in attempts)
    assert sum(len(row["hidden_judgment"]["cases"]) for row in raw["results"]) == 480

    rust = [row for row in raw["results"] if row["language"] == "rust"]
    assert len(rust) == 24
    assert all(not row["read_only_integrity_ok"] for row in rust)
    assert all(row["checker_integrity_ok"] for row in rust)
    assert all(
        row["read_only_integrity_ok"]
        for row in raw["results"]
        if row["language"] != "rust"
    )

    report_path = BENCHMARKS / "reports/036-unseen-fullstack-study-invalid.artifact.json"
    report = json.loads(report_path.read_text())
    assert report["surface"] == "report"
    assert report["manifest"]["title"] == "Unseen Full-Stack Agent Study — Iteration 036"
    assert report["snapshot"]["status"] == "ready"
    assert len(report["snapshot"]["datasets"]["languages"]) == 4
    assert len(report["snapshot"]["datasets"]["configurations"]) == 8
    first_check = next(
        row
        for row in report["snapshot"]["datasets"]["gates"]
        if row["condition"] == "First public check"
    )
    assert first_check["raw_result"] == "PASS"
    assert first_check["interpretation"] == "NOT INTERPRETABLE"


def test_fullstack_036_report_builder_is_deterministic():
    report = BENCHMARKS / "reports/036-unseen-fullstack-study-invalid.artifact.json"
    before = hashlib.sha256(report.read_bytes()).hexdigest()

    completed = subprocess.run(
        [sys.executable, str(BENCHMARKS / "reports/build_036_report.py")],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert hashlib.sha256(report.read_bytes()).hexdigest() == before


def test_fullstack_037_raw_result_and_canonical_report_preserve_invalid_run():
    raw_path = BENCHMARKS / "results/fullstack_agent_037_raw.json"
    raw = json.loads(raw_path.read_text())

    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == (
        "541d43b74cf9939d8a6bfc5ce7761dda74825b3d4eb8e8482fa6ef698014549f"
    )
    assert len(raw["results"]) == 96
    assert len({row["cell_id"] for row in raw["results"]}) == 96
    assert len({row["thread_id"] for row in raw["results"]}) == 96
    assert all(row["journal_attempt"] == 1 for row in raw["results"])
    assert raw["summary"]["primary_gate"] == {
        "conditions": {
            "execution_integrity": False,
            "correctness": True,
            "first_check": False,
            "tokens": False,
            "elapsed": False,
            "maintainability": True,
        },
        "passed": False,
    }

    attempts = [
        attempt
        for row in raw["results"]
        for attempt in row["public_attempts"]
    ]
    assert len(attempts) == 104
    assert sum(attempt["ok"] for attempt in attempts) == 97
    assert sum(len(attempt["cases"]) for attempt in attempts) == 392
    assert sum(
        case["target"] == "browser"
        for attempt in attempts
        for case in attempt["cases"]
    ) == 98
    assert all(row["public_execution_ok"] for row in raw["results"])
    assert all(row["final_public_check_success"] for row in raw["results"])
    assert sum(len(row["hidden_judgment"]["cases"]) for row in raw["results"]) == 480

    rust = [row for row in raw["results"] if row["language"] == "rust"]
    assert len(rust) == 24
    assert all(not row["read_only_integrity_ok"] for row in rust)
    assert all(not row["workspace_integrity_ok"] for row in rust)
    assert all(
        row["workspace_integrity_ok"]
        for row in raw["results"]
        if row["language"] != "rust"
    )
    assert {
        row["cell_id"] for row in raw["results"] if not row["hidden_success"]
    } == {
        "orchard_irrigation_build__rust__terra-medium__r2",
        "orchard_irrigation_build__rust__terra-medium__r3",
    }

    report_path = BENCHMARKS / "reports/037-unseen-fullstack-study-invalid.artifact.json"
    report = json.loads(report_path.read_text())
    assert report["surface"] == "report"
    assert report["manifest"]["title"] == "Unseen Full-Stack Agent Study — Iteration 037"
    assert report["snapshot"]["status"] == "ready"
    assert len(report["snapshot"]["datasets"]["languages"]) == 4
    assert len(report["snapshot"]["datasets"]["configurations"]) == 8
    assert len(report["snapshot"]["datasets"]["hidden_failures"]) == 2
    assert [row["result"] for row in report["snapshot"]["datasets"]["gates"]] == [
        "FAIL", "PASS", "FAIL", "FAIL", "FAIL", "PASS"
    ]


def test_fullstack_037_report_builder_is_deterministic():
    report = BENCHMARKS / "reports/037-unseen-fullstack-study-invalid.artifact.json"
    before = hashlib.sha256(report.read_bytes()).hexdigest()

    completed = subprocess.run(
        [sys.executable, str(BENCHMARKS / "reports/build_037_report.py")],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert hashlib.sha256(report.read_bytes()).hexdigest() == before


def test_fullstack_038_raw_audit_and_report_preserve_valid_negative_result():
    raw_path = BENCHMARKS / "results/fullstack_agent_038_raw.json"
    raw = json.loads(raw_path.read_text())
    audit_path = BENCHMARKS / "fullstack_agent_038_audit.json"
    audit = json.loads(audit_path.read_text())

    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == (
        "84a7f30e534098b4fcc864aa08ac601cfe5b6a19d2b22c9350390bde8381a49f"
    )
    assert hashlib.sha256(audit_path.read_bytes()).hexdigest() == (
        "12f86034bdb7ce1a7bb4dd67b05347961d66a0c53db5fd655b726caf483b7a02"
    )
    assert len(raw["results"]) == 96
    assert len({row["cell_id"] for row in raw["results"]}) == 96
    assert len({row["thread_id"] for row in raw["results"]}) == 96
    assert all(row["journal_attempt"] == 1 for row in raw["results"])
    assert raw["summary"]["primary_gate"] == {
        "conditions": {
            "execution_integrity": True,
            "correctness": True,
            "first_check": False,
            "tokens": False,
            "elapsed": False,
            "maintainability": True,
        },
        "passed": False,
    }
    assert all(row["hidden_success"] for row in raw["results"])
    assert all(row["workspace_integrity_ok"] for row in raw["results"])
    assert all(row["post_build_integrity_ok"] for row in raw["results"])
    assert all(row["final_public_check_success"] for row in raw["results"])

    assert audit["audit_pass"] is True
    assert audit["external_evidence_verified"] is True
    assert audit["matrix"]["journal_pairs_verified"] == 96
    assert audit["matrix"]["attempt_files_verified"] == 104
    assert audit["exact_build"] == {
        "commands": 297,
        "stable_hash_checks": 297,
        "successful_commands": 290,
        "failed_commands_with_stable_hashes": 7,
    }
    assert audit["first_failure_classes"] == {
        "decimal_to_number": 5,
        "unsupported_multiplied_by": 1,
    }
    assert audit["primary_gate"] == raw["summary"]["primary_gate"]

    report_path = (
        BENCHMARKS
        / "reports/038-unseen-fullstack-study-gate-not-met.artifact.json"
    )
    report = json.loads(report_path.read_text())
    assert report["surface"] == "report"
    assert report["manifest"]["title"] == (
        "Unseen Full-Stack Agent Study — Iteration 038"
    )
    assert report["snapshot"]["status"] == "ready"
    assert len(report["snapshot"]["datasets"]["languages"]) == 4
    assert len(report["snapshot"]["datasets"]["configurations"]) == 8
    assert len(report["snapshot"]["datasets"]["failure_classes"]) == 2
    assert [row["result"] for row in report["snapshot"]["datasets"]["gates"]] == [
        "PASS", "PASS", "FAIL", "FAIL", "FAIL", "PASS"
    ]


def test_fullstack_038_report_builder_is_deterministic():
    report = (
        BENCHMARKS
        / "reports/038-unseen-fullstack-study-gate-not-met.artifact.json"
    )
    before = hashlib.sha256(report.read_bytes()).hexdigest()

    completed = subprocess.run(
        [sys.executable, str(BENCHMARKS / "reports/build_038_report.py")],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert hashlib.sha256(report.read_bytes()).hexdigest() == before


def test_fullstack_039_raw_and_independent_audit_preserve_valid_negative_result():
    raw_path = BENCHMARKS / "results/fullstack_agent_039_raw.json"
    raw = json.loads(raw_path.read_text())
    audit_path = BENCHMARKS / "fullstack_agent_039_audit.json"
    audit = json.loads(audit_path.read_text())

    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == (
        "28ecc96591b4f0bc3561f302e271f392c30439767d220c5a9e5ba73f0b47a3c3"
    )
    assert hashlib.sha256(audit_path.read_bytes()).hexdigest() == (
        "bf2270b79cc238d58dc864a6241a3ed982b31dc5f6ccf632bac72be9d71a1fd6"
    )
    assert len(raw["results"]) == 96
    assert len({row["cell_id"] for row in raw["results"]}) == 96
    assert len({row["thread_id"] for row in raw["results"]}) == 96
    assert all(row["journal_attempt"] == 1 for row in raw["results"])
    assert raw["summary"]["primary_gate"] == {
        "conditions": {
            "execution_integrity": True,
            "correctness": True,
            "first_check": False,
            "tokens": False,
            "elapsed": False,
            "maintainability": False,
        },
        "passed": False,
    }
    assert all(
        row["hidden_success"]
        for row in raw["results"]
        if row["language"] != "rust"
    )
    assert sum(row["hidden_success"] for row in raw["results"]) == 95
    assert all(row["workspace_integrity_ok"] for row in raw["results"])
    assert all(row["post_build_integrity_ok"] for row in raw["results"])
    assert all(row["final_public_check_success"] for row in raw["results"])

    assert audit["audit_pass"] is True
    assert audit["external_evidence_verified"] is True
    assert audit["matrix"]["journal_pairs_verified"] == 96
    assert audit["matrix"]["attempt_files_verified"] == 99
    assert audit["exact_build"] == {
        "commands": 291,
        "stable_hash_checks": 291,
        "successful_commands": 288,
        "failed_commands_with_stable_hashes": 3,
    }
    assert audit["first_failure_classes"] == {
        "redundant_fallback_after_total_conversion": 3,
    }
    assert audit["hidden_failure_cells"] == [
        "event_credit_repair__rust__sol-medium__r1"
    ]
    assert len(audit["parley_off_root_maintenance_cells"]) == 6
    assert audit["primary_gate"] == raw["summary"]["primary_gate"]

    report_path = (
        BENCHMARKS
        / "reports/039-independent-fullstack-study-gate-not-met.artifact.json"
    )
    report = json.loads(report_path.read_text())
    assert report["surface"] == "report"
    assert report["manifest"]["title"] == (
        "Independent Full-Stack Agent Study — Iteration 039"
    )
    assert report["snapshot"]["status"] == "ready"
    assert len(report["snapshot"]["datasets"]["languages"]) == 4
    assert len(report["snapshot"]["datasets"]["configurations"]) == 8
    assert len(report["snapshot"]["datasets"]["failure_classes"]) == 3
    assert [row["result"] for row in report["snapshot"]["datasets"]["gates"]] == [
        "PASS", "PASS", "FAIL", "FAIL", "FAIL", "FAIL"
    ]


def test_fullstack_039_report_builder_is_deterministic():
    report = (
        BENCHMARKS
        / "reports/039-independent-fullstack-study-gate-not-met.artifact.json"
    )
    before = hashlib.sha256(report.read_bytes()).hexdigest()

    completed = subprocess.run(
        [sys.executable, str(BENCHMARKS / "reports/build_039_report.py")],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert hashlib.sha256(report.read_bytes()).hexdigest() == before


def _fullstack_040_oracle(task_id, value):
    if task_id == "museum_rotation_build":
        collection = value["permanent_pieces"] + value["borrowed_pieces"]
        viewing = value["permanent_pieces"] * 9 + value["borrowed_pieces"] * 14
        late = value["room_count"] * 20 if value["late_opening"] else 0
        program = viewing + late
        blocks = (program + 59) // 60 if program else 0
        labels = value["borrowed_pieces"] * 5 + value["room_count"] * 4
        index = program + blocks * 7 + labels
        mode = (
            "loan_focus"
            if value["borrowed_pieces"] > value["permanent_pieces"]
            else "blended"
            if value["borrowed_pieces"] > 0
            else "permanent"
        )
        return {
            "collection_size": collection,
            "viewing_minutes": viewing,
            "late_minutes": late,
            "program_minutes": program,
            "tour_blocks": blocks,
            "label_points": labels,
            "rotation_index": index,
            "exhibit_mode": mode,
        }
    if task_id == "harbor_signal_build":
        vessels = value["freight_arrivals"] + value["service_boats"]
        base = value["channel_crews"] * 6
        fog = value["channel_crews"] * 2 if value["fog_alert"] else 0
        active = max(base - fog, 0)
        unsignaled = max(vessels - active, 0)
        crew = min(vessels, active) * 3
        state = (
            "clear"
            if unsignaled == 0
            else "fog_hold"
            if value["fog_alert"]
            else "congested"
        )
        return {
            "vessel_count": vessels,
            "base_beacons": base,
            "fog_beacons": fog,
            "active_beacons": active,
            "unsignaled_vessels": unsignaled,
            "crew_load": crew,
            "signal_index": unsignaled * 11 + crew,
            "harbor_state": state,
        }
    if task_id == "rooftop_battery_repair":
        gap = max(value["household_units"] - value["solar_units"], 0)
        protected = min(value["stored_units"], 4) if value["reserve_enabled"] else 0
        ceiling = max(value["stored_units"] - protected, 0)
        delivery = min(gap, ceiling)
        utility = max(gap - delivery, 0)
        balance = max(value["stored_units"] - delivery, 0)
        state = "self_powered" if gap == 0 else "battery" if utility == 0 else "grid"
        return {
            "energy_gap": gap,
            "protected_units": protected,
            "discharge_ceiling": ceiling,
            "battery_delivery": delivery,
            "utility_units": utility,
            "storage_balance": balance,
            "reserve_margin": max(balance - protected, 0),
            "supply_state": state,
        }
    if task_id == "bookmobile_loading_repair":
        sound = max(value["requested_crates"] - value["damaged_crates"], 0)
        deck = value["truck_count"] * 16
        lift = value["truck_count"] * 2 if value["lift_assist"] else 0
        slots = deck + lift
        deferred = max(sound - slots, 0)
        boarded = min(sound, slots)
        state = "deferred" if deferred > 0 else "loaded" if boarded > 0 else "idle"
        return {
            "sound_crates": sound,
            "deck_slots": deck,
            "lift_slots": lift,
            "loading_slots": slots,
            "deferred_crates": deferred,
            "boarded_crates": boarded,
            "empty_slots": max(slots - boarded, 0),
            "loading_state": state,
        }
    raise AssertionError(f"unknown 040 task: {task_id}")


def test_fullstack_040_corpus_is_independent_complete_and_oracle_checked():
    task_document = json.loads(
        (BENCHMARKS / "fullstack_agent_040_tasks.json").read_text()
    )
    case_document = json.loads(
        (BENCHMARKS / "fullstack_agent_040_cases.json").read_text()
    )

    assert task_document["schema_version"] == case_document["schema_version"] == 1
    assert task_document["experiment_id"] == case_document["experiment_id"] == "040"
    tasks = task_document["tasks"]
    assert [task["kind"] for task in tasks] == [
        "implementation",
        "implementation",
        "maintenance",
        "maintenance",
    ]
    assert set(case_document["tasks"]) == {task["id"] for task in tasks}

    prior_tasks = []
    prior_cases = []
    for experiment in ("036", "037", "038", "039"):
        prior_tasks.extend(
            json.loads(
                (BENCHMARKS / f"fullstack_agent_{experiment}_tasks.json").read_text()
            )["tasks"]
        )
        prior_cases.extend(
            case
            for cases in json.loads(
                (BENCHMARKS / f"fullstack_agent_{experiment}_cases.json").read_text()
            )["tasks"].values()
            for case in cases
        )

    def fields(rows, name):
        return {field for row in rows for field in row[name]}

    assert {task["id"] for task in tasks}.isdisjoint(
        task["id"] for task in prior_tasks
    )
    assert fields(tasks, "request_fields").isdisjoint(
        fields(prior_tasks, "request_fields")
    )
    assert fields(tasks, "response_fields").isdisjoint(
        fields(prior_tasks, "response_fields")
    )
    assert {task["status_route"] for task in tasks}.isdisjoint(
        task["status_route"] for task in prior_tasks
    )
    assert {task["post_route"] for task in tasks}.isdisjoint(
        task["post_route"] for task in prior_tasks
    )
    assert {task["browser_export"] for task in tasks}.isdisjoint(
        task["browser_export"] for task in prior_tasks
    )

    all_case_ids = []
    for task in tasks:
        assert task["shared_result_field"] in task["response_fields"]
        if task["kind"] == "maintenance":
            assert task["root_cause_role"] == "application_logic"
            assert task["predeclared_defect"]

        cases = case_document["tasks"][task["id"]]
        public = [case for case in cases if case["visibility"] == "public"]
        hidden = [case for case in cases if case["visibility"] == "hidden"]
        assert len(cases) == 9
        assert len(public) == 4 and len(hidden) == 5
        assert sum(case["target"] == "browser" for case in public) == 1
        assert sum(case["target"] == "browser" for case in hidden) == 2
        assert task["public_case_ids"] == [case["id"] for case in public]
        assert task["hidden_case_ids"] == [case["id"] for case in hidden]
        all_case_ids.extend(case["id"] for case in cases)

        field_order = list(task["request_fields"])
        for case in cases:
            if case["target"] == "browser":
                assert case["export"] == task["browser_export"]
                assert len(case["args"]) == len(field_order)
                values = dict(zip(field_order, case["args"], strict=True))
                result = _fullstack_040_oracle(task["id"], values)
                assert case["expected"] == result[task["shared_result_field"]]
            elif case["method"] == "GET":
                assert case["path"] == task["status_route"]
                assert case["expected_json"] == {
                    "service": task["service"],
                    "ready": True,
                }
            elif case["expected_status"] == 200:
                assert case["path"] == task["post_route"]
                assert set(case["json"]) == set(task["request_fields"])
                assert case["expected_json"] == _fullstack_040_oracle(
                    task["id"], case["json"]
                )
            else:
                assert case["expected_error"] in {
                    "invalid_json",
                    "json_content_type_required",
                    "body_too_large",
                }

    assert len(all_case_ids) == len(set(all_case_ids)) == 36
    assert set(all_case_ids).isdisjoint(case["id"] for case in prior_cases)


def test_exact_build_freeze_detects_read_only_mutation(tmp_path):
    from benchmarks.exact_build_freeze import run_frozen_builds

    frozen = tmp_path / "frozen.txt"
    frozen.write_text("before\n")
    result = run_frozen_builds(
        tmp_path,
        ["frozen.txt"],
        [[
            sys.executable,
            "-c",
            "from pathlib import Path; Path('frozen.txt').write_text('after\\n')",
        ]],
    )

    assert result["ok"] is False
    assert result["completed_commands"] == 1
    assert result["commands"][0]["returncode"] == 0
    assert set(result["read_only_changes"]) == {"frozen.txt"}
    assert result["read_only_changes"]["frozen.txt"]["before"]["sha256"] != (
        result["read_only_changes"]["frozen.txt"]["after"]["sha256"]
    )


def test_exact_build_freeze_rejects_symlinked_input(tmp_path):
    from benchmarks.exact_build_freeze import snapshot_read_only

    target = tmp_path / "target.txt"
    target.write_text("value\n")
    (tmp_path / "frozen.txt").symlink_to(target)

    with pytest.raises(ValueError, match="regular non-symlink"):
        snapshot_read_only(tmp_path, ["frozen.txt"])


def test_exact_build_freeze_038_smoke_proves_positive_and_negative_controls():
    artifact = json.loads(
        (BENCHMARKS / "exact_build_freeze_038_smoke.json").read_text()
    )
    fixture = BENCHMARKS / "fullstack_038/rust_smoke"

    assert artifact["experiment_id"] == "038-execution-mechanism"
    assert artifact["task_semantics_frozen"] is False
    assert artifact["fixture"] == {
        "path": "benchmarks/fullstack_038/rust_smoke",
        "cargo_toml_sha256": hashlib.sha256(
            (fixture / "Cargo.toml").read_bytes()
        ).hexdigest(),
        "cargo_lock_sha256": hashlib.sha256(
            (fixture / "Cargo.lock").read_bytes()
        ).hexdigest(),
        "lib_sha256": hashlib.sha256(
            (fixture / "src/lib.rs").read_bytes()
        ).hexdigest(),
        "main_sha256": hashlib.sha256(
            (fixture / "src/main.rs").read_bytes()
        ).hexdigest(),
    }
    assert artifact["gate"] == {
        "canonical_exact_build_passes": True,
        "metadata_false_negative_reproduced": True,
        "exact_build_detects_noncanonical_lock": True,
        "passed": True,
    }
    assert artifact["canonical_exact_build"]["ok"] is True
    assert artifact["canonical_exact_build"]["read_only_changes"] == {}
    assert len(artifact["canonical_exact_build"]["commands"]) == 2
    assert all(
        row["returncode"] == 0 and row["read_only_changes"] == {}
        for row in artifact["canonical_exact_build"]["commands"]
    )
    assert artifact["noncanonical_metadata_probe"]["ok"] is True
    assert artifact["noncanonical_metadata_probe"]["lock_unchanged"] is True
    negative = artifact["noncanonical_exact_build"]
    assert negative["ok"] is False
    assert negative["commands"][0]["returncode"] == 0
    assert set(negative["read_only_changes"]) == {"Cargo.lock"}


def _fullstack_038_oracle(task_id, value):
    if task_id == "ferry_manifest_build":
        travellers = value["adult_count"] + value["youth_count"]
        passenger = value["adult_count"] * 1100 + value["youth_count"] * 650
        vehicle = value["vehicle_count"] * 2400
        peak = (
            travellers * 125 + value["vehicle_count"] * 350
            if value["peak_departure"]
            else 0
        )
        if value["vehicle_count"] > 0 and travellers > 0:
            mode = "mixed"
        elif value["vehicle_count"] > 0:
            mode = "vehicle"
        else:
            mode = "foot"
        return {
            "traveller_total": travellers,
            "passenger_charge_cents": passenger,
            "vehicle_charge_cents": vehicle,
            "peak_charge_cents": peak,
            "manifest_charge_cents": passenger + vehicle + peak,
            "boarding_load": travellers + value["vehicle_count"] * 3,
            "travel_mode": mode,
        }
    if task_id == "archive_retention_build":
        pages = value["document_count"] * value["pages_each"]
        base = value["requested_years"] * 12
        retained = max(base, 84) if value["legal_hold"] else base
        batches = 0 if pages == 0 else (pages + 199) // 200
        return {
            "page_total": pages,
            "base_months": base,
            "retained_months": retained,
            "review_batches": batches,
            "retention_score": retained + batches * 3,
            "retention_class": "held" if value["legal_hold"] else "standard",
        }
    if task_id == "loyalty_stamps_repair":
        base = value["purchase_count"] * value["stamps_each"]
        bonus = value["purchase_count"] if value["double_day"] else 0
        spendable = max(base + bonus - value["claimed_stamps"], 0)
        rewards = spendable // 10
        return {
            "base_stamps": base,
            "bonus_stamps": bonus,
            "spendable_stamps": spendable,
            "reward_count": rewards,
            "leftover_stamps": spendable % 10,
            "reward_stage": "ready" if rewards > 0 else "collecting",
        }
    if task_id == "cold_storage_repair":
        corrected = value["measured_degrees"] + (2 if value["door_open"] else 0)
        gap = abs(corrected - value["target_degrees"])
        excess = max(
            corrected - value["target_degrees"] - value["allowed_drift"], 0
        )
        steps = 0 if excess == 0 else (excess + 2) // 3
        safe = gap <= value["allowed_drift"]
        condition = (
            "stable"
            if safe
            else "cooling"
            if corrected > value["target_degrees"]
            else "warming"
        )
        return {
            "corrected_degrees": corrected,
            "temperature_gap": gap,
            "excess_heat": excess,
            "cooling_steps": steps,
            "safe_flag": safe,
            "storage_condition": condition,
        }
    raise AssertionError(f"unknown 038 task: {task_id}")


def test_fullstack_038_corpus_is_independent_complete_and_oracle_checked():
    task_path = BENCHMARKS / "fullstack_agent_038_tasks.json"
    case_path = BENCHMARKS / "fullstack_agent_038_cases.json"
    task_document = json.loads(task_path.read_text())
    case_document = json.loads(case_path.read_text())

    assert task_document["schema_version"] == 1
    assert task_document["experiment_id"] == "038"
    assert case_document["schema_version"] == 1
    assert case_document["experiment_id"] == "038"
    tasks = task_document["tasks"]
    assert len(tasks) == 4
    assert [task["kind"] for task in tasks] == [
        "implementation",
        "implementation",
        "maintenance",
        "maintenance",
    ]
    assert set(case_document["tasks"]) == {task["id"] for task in tasks}

    prior_tasks = []
    prior_cases = []
    for experiment in ("036", "037"):
        old_tasks = json.loads(
            (BENCHMARKS / f"fullstack_agent_{experiment}_tasks.json").read_text()
        )["tasks"]
        old_cases = json.loads(
            (BENCHMARKS / f"fullstack_agent_{experiment}_cases.json").read_text()
        )["tasks"]
        prior_tasks.extend(old_tasks)
        prior_cases.extend(case for cases in old_cases.values() for case in cases)

    def fields(rows, name):
        return {field for row in rows for field in row[name]}

    assert {task["id"] for task in tasks}.isdisjoint(
        task["id"] for task in prior_tasks
    )
    assert fields(tasks, "request_fields").isdisjoint(
        fields(prior_tasks, "request_fields")
    )
    assert fields(tasks, "response_fields").isdisjoint(
        fields(prior_tasks, "response_fields")
    )
    assert {task["post_route"] for task in tasks}.isdisjoint(
        task["post_route"] for task in prior_tasks
    )
    assert {task["browser_export"] for task in tasks}.isdisjoint(
        task["browser_export"] for task in prior_tasks
    )

    all_case_ids = []
    for task in tasks:
        cases = case_document["tasks"][task["id"]]
        public = [case for case in cases if case["visibility"] == "public"]
        hidden = [case for case in cases if case["visibility"] == "hidden"]
        all_case_ids.extend(case["id"] for case in cases)

        assert len(cases) == 9
        assert len(public) == 4 and len(hidden) == 5
        assert sum(case["target"] == "browser" for case in public) == 1
        assert sum(case["target"] == "browser" for case in hidden) == 2
        assert task["public_case_ids"] == [case["id"] for case in public]
        assert task["hidden_case_ids"] == [case["id"] for case in hidden]

        field_order = list(task["request_fields"])
        for case in cases:
            if case["target"] == "browser":
                values = dict(zip(field_order, case["args"], strict=True))
                result = _fullstack_038_oracle(task["id"], values)
                assert case["export"] == task["browser_export"]
                assert case["expected"] == result[task["shared_result_field"]]
            elif case["method"] == "GET":
                assert case["path"] == task["status_route"]
                assert case["expected_json"] == {
                    "service": task["service"],
                    "ready": True,
                }
            elif case["expected_status"] == 200:
                assert case["path"] == task["post_route"]
                assert case["expected_json"] == _fullstack_038_oracle(
                    task["id"], case["json"]
                )
            else:
                assert case["expected_error"] in {
                    "invalid_json",
                    "json_content_type_required",
                }

    assert len(all_case_ids) == len(set(all_case_ids)) == 36
    assert set(all_case_ids).isdisjoint(case["id"] for case in prior_cases)
    assert all(
        task["predeclared_defect"] and task["root_cause_role"] == "application_logic"
        for task in tasks
        if task["kind"] == "maintenance"
    )


def test_fullstack_038_protocol_freezes_product_matrix_and_execution_controls():
    protocol = json.loads(
        (BENCHMARKS / "fullstack_agent_038_protocol.json").read_text()
    )
    product = protocol["frozen_product"]
    transport = protocol["validated_transport"]
    exact_build = protocol["validated_exact_build_freeze"]
    config = protocol["frozen_config"]
    matrix = protocol["matrix"]

    assert protocol["experiment_id"] == "038"
    assert protocol["protocol_revision"] == 2
    assert product["product_commit"] == "02cd809f35dfa9f93468e59cfc8a38d97abb41ee"
    assert product["corpus_commit"] == "b08401e6972822ed211cf33e089b9a59602ea23d"
    for file_key, hash_key in (
        ("tasks_file", "tasks_sha256"),
        ("cases_file", "cases_sha256"),
        ("parley_skill_file", "parley_skill_sha256"),
        ("parley_web_reference_file", "parley_web_reference_sha256"),
    ):
        assert hashlib.sha256((REPO / product[file_key]).read_bytes()).hexdigest() == (
            product[hash_key]
        )
    for file_key, hash_key in (
        ("transport_file", "transport_sha256"),
        ("terra_smoke_file", "terra_smoke_sha256"),
        ("sol_smoke_file", "sol_smoke_sha256"),
    ):
        assert hashlib.sha256((REPO / transport[file_key]).read_bytes()).hexdigest() == (
            transport[hash_key]
        )
    for file_key, hash_key in (
        ("validator_file", "validator_sha256"),
        ("smoke_file", "smoke_sha256"),
        ("evidence_file", "evidence_sha256"),
    ):
        assert hashlib.sha256((REPO / exact_build[file_key]).read_bytes()).hexdigest() == (
            exact_build[hash_key]
        )
    assert exact_build["mechanism_commit"] == (
        "6e50439dd2f47cae4c7bb4d5356bae7cf5dd0937"
    )
    assert exact_build["canonical_lock_sha256"] == hashlib.sha256(
        (BENCHMARKS / "fullstack_038/rust_smoke/Cargo.lock").read_bytes()
    ).hexdigest()

    assert config["languages"] == ["parley", "python", "typescript", "rust"]
    assert [item["id"] for item in config["agent_configurations"]] == [
        "sol-medium",
        "terra-medium",
    ]
    assert config["replicates_per_task_language_configuration"] == 3
    assert config["max_public_check_attempts"] == 12
    assert matrix["fresh_sessions"] == 96
    assert matrix["frozen_public_case_executions_across_first_checks"] == 384
    assert matrix["hidden_case_executions"] == 480
    assert "post-command hash checks" in protocol["scaffold_protocol"][
        "reference_validation"
    ]
    assert "post-build hashes" in protocol["primary_gate"]["execution_integrity"]
    assert any(
        "cannot prove universal language superiority" in boundary
        for boundary in protocol["interpretation_boundary"]
    )
    assert "no same-corpus optimization or rerun" in protocol["stop_rule"]
    execution = protocol["execution_freeze"]
    assert execution["measured_sessions_before_freeze"] == 0
    assert execution["harness_commit"] == (
        "0cc6426afe6755896395bbfd251f60d5b60affc9"
    )
    assert len(execution["files"]) == 18
    assert {item["file"] for item in execution["files"]} >= {
        "benchmarks/run_fullstack_agent_038.py",
        "benchmarks/fullstack_agent_038_logic.py",
        "benchmarks/exact_build_freeze.py",
        "benchmarks/fullstack_038/rust/Cargo.lock",
        "benchmarks/FULLSTACK_AGENT_038_EXECUTION_FREEZE.md",
    }
    for item in execution["files"]:
        assert hashlib.sha256((REPO / item["file"]).read_bytes()).hexdigest() == (
            item["sha256"]
        )


def test_fullstack_038_scaffolds_plan_and_validation_preserve_frozen_boundaries():
    tasks = load_fullstack_038_task_map()
    protocol = json.loads(
        (BENCHMARKS / "fullstack_agent_038_protocol.json").read_text()
    )
    config = protocol["frozen_config"]

    assert validate_fullstack_038_corpus() == {
        "tasks": 4,
        "cases": 36,
        "public_cases": 16,
        "hidden_cases": 20,
        "sessions": 96,
    }
    plan = build_fullstack_038_plan(
        list(tasks.values()),
        config["languages"],
        config["agent_configurations"],
        config["replicates_per_task_language_configuration"],
        config["seed"],
    )
    assert len(plan) == len({row["cell_id"] for row in plan}) == 96
    assert all(
        sum(row["language"] == language for row in plan) == 24
        for language in FULLSTACK_038_LANGUAGES
    )

    for task in tasks.values():
        for language in FULLSTACK_038_LANGUAGES:
            seed = fullstack_038_scaffold_files(task, language, "seed")
            reference = fullstack_038_scaffold_files(task, language, "reference")
            assert set(seed) == set(reference)
            assert all(spec.text.endswith("\n") for spec in seed.values())
            assert seed["CONTRACT.md"].editable is False
            changed = sorted(
                name for name in seed if seed[name].text != reference[name].text
            )
            if task["kind"] == "maintenance":
                assert changed == list(FULLSTACK_038_ROOT_FILES[language])
            else:
                assert changed

    rust_manifest = (BENCHMARKS / "fullstack_038/rust/Cargo.toml").read_text()
    rust_lock = (BENCHMARKS / "fullstack_038/rust/Cargo.lock").read_text()
    assert 'name = "fullstack-agent-038"' in rust_manifest
    assert 'name = "fullstack-agent-038"' in rust_lock
    assert 'name = "fullstack-agent-037"' not in rust_lock

    validation = json.loads(
        (BENCHMARKS / "fullstack_agent_038_validation.json").read_text()
    )
    assert validation["protocol_sha256"] == hashlib.sha256(
        (BENCHMARKS / "fullstack_agent_038_protocol.json").read_bytes()
    ).hexdigest()
    assert validation["reference_cells_passed"] == 16
    assert validation["seed_cells_built"] == 16
    assert validation["seed_cells_correct"] == 0
    assert validation["maintenance_root_boundaries_passed"] == 8
    assert len(validation["cells"]) == 16
    assert all(cell["reference_cases"] == 9 for cell in validation["cells"])
    assert all(cell["reference_post_build_integrity"] for cell in validation["cells"])
    assert all(cell["seed_post_build_integrity"] for cell in validation["cells"])
    expected_commands = {"parley": 1, "python": 2, "typescript": 1, "rust": 2}
    assert all(
        cell["reference_exact_build_commands"] == expected_commands[cell["language"]]
        and cell["seed_exact_build_commands"] == expected_commands[cell["language"]]
        for cell in validation["cells"]
    )


def test_fullstack_038_orchestration_smoke_covers_parent_and_hidden_paths():
    smoke = json.loads(
        (BENCHMARKS / "fullstack_agent_038_orchestration_smoke.json").read_text()
    )

    assert smoke["experiment_id"] == "038"
    assert smoke["purpose"] == "non-model end-to-end orchestration smoke"
    assert smoke["protocol_sha256"] == hashlib.sha256(
        (BENCHMARKS / "fullstack_agent_038_protocol.json").read_bytes()
    ).hexdigest()
    assert smoke["commands"] == [
        {"command": "./sources", "returncode": 0},
        {"command": "./check", "returncode": 1},
    ]
    assert smoke["attempt_count"] == 1
    assert smoke["public"] == {
        "semantic_pass": False,
        "build_pass": True,
        "post_build_integrity": True,
        "exact_build_commands": 2,
        "case_count": 4,
        "http_cases": 3,
        "browser_cases": 1,
        "cross_target_executed": True,
    }
    assert smoke["hidden"] == {
        "semantic_pass": False,
        "build_pass": True,
        "post_build_integrity": True,
        "exact_build_commands": 2,
        "case_count": 5,
        "http_cases": 3,
        "browser_cases": 2,
        "cross_target_executed": True,
    }
    assert smoke["protected_integrity"] is True
    assert smoke["read_only_integrity"] is True
    assert smoke["transport_integrity"] is True
    assert smoke["unexpected_files"] == []
    assert smoke["pass"] is True


def test_fullstack_038_numeric_guard_and_command_limit_are_exact():
    task = load_fullstack_038_task_map()["ferry_manifest_build"]
    assert invalid_numeric_domain_038(
        task,
        b'{"adult_count":-1,"youth_count":0,"vehicle_count":0,"peak_departure":false}',
    )
    assert not invalid_numeric_domain_038(task, b'{"adult_count":"-1"}')
    assert fullstack_038_command_protocol(
        [{"command": "./sources"}, {"command": "./check"}]
    )["compliant"] is True
    assert fullstack_038_command_protocol(
        [{"command": "./sources"}] + [{"command": "./check"}] * 13
    )["compliant"] is False


def test_fullstack_038_runner_checks_hashes_immediately_after_build(
    tmp_path, monkeypatch
):
    lock = tmp_path / "Cargo.lock"
    lock.write_text("frozen\n")
    expected = hashlib.sha256(lock.read_bytes()).hexdigest()

    def mutating_build(command, *, cwd, env=None, timeout=300):
        lock.write_text("canonicalized\n")

    monkeypatch.setattr(fullstack_038_runner, "run", mutating_build)
    result = fullstack_038_runner.build_application(
        tmp_path,
        "rust",
        "/unused/parley",
        {"Cargo.lock": expected},
    )

    assert result["ok"] is False
    assert result["protected_read_only_ok"] is False
    assert len(result["protected_read_only_checks"]) == 1
    assert set(result["protected_read_only_checks"][0]["changes"]) == {"Cargo.lock"}


def test_fullstack_039_protocol_preregisters_independent_compact_context_study():
    protocol = json.loads(
        (BENCHMARKS / "fullstack_agent_039_protocol.json").read_text()
    )
    product = protocol["frozen_product"]

    assert protocol["experiment_id"] == "039"
    assert protocol["protocol_revision"] == 2
    assert product["parley_version"] == "parley 0.5.1"
    assert product["product_commit"] == "b08952cfb69e10f406af082d899d8556fa75ef15"
    assert product["product_tree"] == "0f424ad0b03ba724011b8f2ecb05c5a7c277cafc"
    assert product["corpus_commit"] == "1db9d08ebd73c987e54204d63b7ba37ed9d1eaf4"
    for file_key, hash_key in (
        ("tasks_file", "tasks_sha256"),
        ("cases_file", "cases_sha256"),
        ("parley_skill_file", "parley_skill_sha256"),
        ("parley_web_reference_file", "parley_web_reference_sha256"),
    ):
        assert hashlib.sha256((REPO / product[file_key]).read_bytes()).hexdigest() == (
            product[hash_key]
        )
    assert product["combined_parley_context_bytes"] == 4_368
    assert product["combined_parley_context_o200k_tokens"] == 1_168
    assert product["combined_parley_context_bytes"] < product[
        "prior_038_combined_context_bytes"
    ]
    assert product["combined_parley_context_o200k_tokens"] < product[
        "prior_038_combined_context_o200k_tokens"
    ]

    tasks = json.loads((REPO / product["tasks_file"]).read_text())["tasks"]
    cases = json.loads((REPO / product["cases_file"]).read_text())["tasks"]
    assert [task["kind"] for task in tasks] == [
        "implementation", "implementation", "maintenance", "maintenance"
    ]
    assert "multiplied by" not in " ".join(task["statement"] for task in tasks)
    assert set(cases) == {task["id"] for task in tasks}
    assert all(len(rows) == 9 for rows in cases.values())
    assert sum(
        case["visibility"] == "public"
        for rows in cases.values()
        for case in rows
    ) == 16
    assert sum(
        case["visibility"] == "hidden"
        for rows in cases.values()
        for case in rows
    ) == 20
    assert sum(
        case["target"] == "browser"
        for rows in cases.values()
        for case in rows
    ) == 12
    assert protocol["matrix"]["fresh_sessions"] == 96
    assert protocol["frozen_config"]["selective_reruns"] == "forbidden"
    execution = protocol["execution_freeze"]
    assert execution["measured_sessions_before_freeze"] == 0
    assert execution["harness_commit"] == (
        "a93a8cc942712b9d19304b8739fcea73bb49cb75"
    )
    assert len(execution["files"]) == 18
    for item in execution["files"]:
        assert hashlib.sha256((REPO / item["file"]).read_bytes()).hexdigest() == (
            item["sha256"]
        )
    assert set(protocol["primary_gate"]) == {
        "execution_integrity",
        "correctness",
        "first_check",
        "tokens",
        "elapsed",
        "maintainability",
        "verdict",
    }


def test_fullstack_039_scaffolds_plan_and_validation_preserve_boundaries():
    tasks = load_fullstack_039_task_map()
    protocol = json.loads(
        (BENCHMARKS / "fullstack_agent_039_protocol.json").read_text()
    )
    config = protocol["frozen_config"]

    assert validate_fullstack_039_corpus() == {
        "tasks": 4,
        "cases": 36,
        "public_cases": 16,
        "hidden_cases": 20,
        "sessions": 96,
    }
    plan = build_fullstack_039_plan(
        list(tasks.values()),
        config["languages"],
        config["agent_configurations"],
        config["replicates_per_task_language_configuration"],
        config["seed"],
    )
    assert len(plan) == len({row["cell_id"] for row in plan}) == 96
    assert all(
        sum(row["language"] == language for row in plan) == 24
        for language in FULLSTACK_039_LANGUAGES
    )

    for task in tasks.values():
        for language in FULLSTACK_039_LANGUAGES:
            seed = fullstack_039_scaffold_files(task, language, "seed")
            reference = fullstack_039_scaffold_files(task, language, "reference")
            assert set(seed) == set(reference)
            assert all(spec.text.endswith("\n") for spec in seed.values())
            assert seed["CONTRACT.md"].editable is False
            changed = sorted(
                name for name in seed if seed[name].text != reference[name].text
            )
            if task["kind"] == "maintenance":
                assert changed == list(FULLSTACK_039_ROOT_FILES[language])
            else:
                assert changed

    rust_manifest = (BENCHMARKS / "fullstack_039/rust/Cargo.toml").read_text()
    rust_lock = (BENCHMARKS / "fullstack_039/rust/Cargo.lock").read_text()
    assert 'name = "fullstack-agent-039"' in rust_manifest
    assert 'name = "fullstack-agent-039"' in rust_lock
    assert 'name = "fullstack-agent-038"' not in rust_lock

    validation = json.loads(
        (BENCHMARKS / "fullstack_agent_039_validation.json").read_text()
    )
    assert validation["protocol_sha256"] == hashlib.sha256(
        (BENCHMARKS / "fullstack_agent_039_protocol.json").read_bytes()
    ).hexdigest()
    assert validation["reference_cells_passed"] == 16
    assert validation["seed_cells_built"] == 16
    assert validation["seed_cells_correct"] == 0
    assert validation["maintenance_root_boundaries_passed"] == 8
    assert len(validation["cells"]) == 16
    assert all(cell["reference_cases"] == 9 for cell in validation["cells"])
    assert all(cell["reference_post_build_integrity"] for cell in validation["cells"])
    assert all(cell["seed_post_build_integrity"] for cell in validation["cells"])
    expected_commands = {"parley": 1, "python": 2, "typescript": 1, "rust": 2}
    assert all(
        cell["reference_exact_build_commands"] == expected_commands[cell["language"]]
        and cell["seed_exact_build_commands"] == expected_commands[cell["language"]]
        for cell in validation["cells"]
    )


def test_fullstack_039_orchestration_smoke_covers_parent_and_hidden_paths():
    smoke = json.loads(
        (BENCHMARKS / "fullstack_agent_039_orchestration_smoke.json").read_text()
    )

    assert smoke["experiment_id"] == "039"
    assert smoke["task_id"] == "festival_power_build"
    assert smoke["protocol_sha256"] == hashlib.sha256(
        (BENCHMARKS / "fullstack_agent_039_protocol.json").read_bytes()
    ).hexdigest()
    assert smoke["commands"] == [
        {"command": "./sources", "returncode": 0},
        {"command": "./check", "returncode": 1},
    ]
    assert smoke["attempt_count"] == 1
    assert smoke["public"] == {
        "semantic_pass": False,
        "build_pass": True,
        "post_build_integrity": True,
        "exact_build_commands": 2,
        "case_count": 4,
        "http_cases": 3,
        "browser_cases": 1,
        "cross_target_executed": True,
    }
    assert smoke["hidden"] == {
        "semantic_pass": False,
        "build_pass": True,
        "post_build_integrity": True,
        "exact_build_commands": 2,
        "case_count": 5,
        "http_cases": 3,
        "browser_cases": 2,
        "cross_target_executed": True,
    }
    assert smoke["protected_integrity"] is True
    assert smoke["read_only_integrity"] is True
    assert smoke["transport_integrity"] is True
    assert smoke["unexpected_files"] == []
    assert smoke["pass"] is True


def test_fullstack_039_numeric_guard_command_limit_and_post_build_checks():
    task = load_fullstack_039_task_map()["festival_power_build"]
    assert invalid_numeric_domain_039(
        task,
        b'{"speaker_towers":-1,"watts_each":600,"light_rigs":2,"weather_cover":false}',
    )
    assert not invalid_numeric_domain_039(task, b'{"speaker_towers":"-1"}')
    assert fullstack_039_command_protocol(
        [{"command": "./sources"}, {"command": "./check"}]
    )["compliant"] is True
    assert fullstack_039_command_protocol(
        [{"command": "./sources"}] + [{"command": "./check"}] * 13
    )["compliant"] is False


def test_fullstack_039_runner_checks_hashes_immediately_after_build(
    tmp_path, monkeypatch
):
    lock = tmp_path / "Cargo.lock"
    lock.write_text("frozen\n")
    expected = hashlib.sha256(lock.read_bytes()).hexdigest()

    def mutating_build(command, *, cwd, env=None, timeout=300):
        lock.write_text("canonicalized\n")

    monkeypatch.setattr(fullstack_039_runner, "run", mutating_build)
    result = fullstack_039_runner.build_application(
        tmp_path,
        "rust",
        "/unused/parley",
        {"Cargo.lock": expected},
    )

    assert result["ok"] is False
    assert result["protected_read_only_ok"] is False
    assert len(result["protected_read_only_checks"]) == 1
    assert set(result["protected_read_only_checks"][0]["changes"]) == {"Cargo.lock"}
