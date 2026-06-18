import json

from conftest import REPO, run_cli
from parley import __version__


def test_doctor_json_reports_ready_toolchain(workdir):
    proc = run_cli(["doctor", "--json"], cwd=workdir)

    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["ok"] is True
    assert report["version"] == __version__

    checks = {check["name"]: check for check in report["checks"]}
    assert checks["parley"]["ok"] is True
    assert checks["python"]["ok"] is True
    assert checks["cargo"]["ok"] is True
    assert checks["stdlib"]["ok"] is True
    assert checks["packages"]["ok"] is True
    for package in ["std/math", "std/text", "std/list", "std/map"]:
        assert package in checks["stdlib"]["detail"]


def test_benchmark_measure_command_writes_json_report(tmp_path):
    output = tmp_path / "metrics.json"
    proc = run_cli([
        "benchmark",
        "measure",
        "--no-check",
        "--format",
        "json",
        "--output",
        str(output),
    ], cwd=REPO)

    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert output.is_file()
    assert report["totals"]["tasks"] == 10
    assert set(report["totals"]["languages"]) == {"parley", "python", "rust"}
    assert report["totals"]["checked_ok"] == 0


def test_benchmark_summarize_command_reads_run_log(tmp_path):
    log = tmp_path / "runs.jsonl"
    log.write_text(json.dumps({
        "schema_version": 1,
        "task_id": "hello",
        "language": "parley",
        "model": "test-agent",
        "attempt": 1,
        "repair_turn": 0,
        "status": "first_run_success",
        "elapsed_seconds": 0.3,
    }) + "\n")

    proc = run_cli([
        "benchmark",
        "summarize",
        "--log",
        str(log),
        "--format",
        "json",
    ], cwd=REPO)

    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)
    assert summary["totals"]["records"] == 1
    assert summary["groups"][0]["task_id"] == "hello"
    assert summary["groups"][0]["success"] is True
