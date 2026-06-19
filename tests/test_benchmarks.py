import json
import os
import py_compile
import shutil
import subprocess
import sys

import pytest

from conftest import REPO

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
