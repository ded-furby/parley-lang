import hashlib
import json
from pathlib import Path

from benchmarks.fullstack_agent_042_guard import invalid_numeric_domain
from benchmarks.fullstack_agent_042_scaffolds import (
    LANGUAGES,
    ROOT_FILES,
    load_task_map,
    scaffold_files,
)
from benchmarks.run_fullstack_agent_042 import (
    CONTEXT_PATH,
    O200K,
    build_plan,
    command_protocol,
    ensure_cleanup_record,
    ensure_run_manifest,
    journal_paths,
    load_cases,
    render_prompt,
    validate_corpus,
)


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"


def test_fullstack_042_scaffolds_plan_and_validation_preserve_boundaries():
    tasks = load_task_map()
    protocol = json.loads(
        (BENCHMARKS / "fullstack_agent_042_protocol.json").read_text()
    )
    config = protocol["frozen_config"]

    assert validate_corpus() == {
        "tasks": 4,
        "cases": 36,
        "public_cases": 16,
        "hidden_cases": 20,
        "sessions": 96,
    }
    plan = build_plan(
        list(tasks.values()),
        config["languages"],
        config["agent_configurations"],
        config["replicates_per_task_language_configuration"],
        config["seed"],
    )
    assert len(plan) == len({row["cell_id"] for row in plan}) == 96
    assert all(
        sum(row["language"] == language for row in plan) == 24
        for language in LANGUAGES
    )

    for task in tasks.values():
        for language in LANGUAGES:
            seed = scaffold_files(task, language, "seed")
            reference = scaffold_files(task, language, "reference")
            assert set(seed) == set(reference)
            assert all(spec.text.endswith("\n") for spec in seed.values())
            assert seed["CONTRACT.md"].editable is False
            changed = sorted(
                name for name in seed if seed[name].text != reference[name].text
            )
            if task["kind"] == "maintenance":
                assert changed == list(ROOT_FILES[language])
            else:
                assert changed

    rust_manifest = (BENCHMARKS / "fullstack_042/rust/Cargo.toml").read_text()
    rust_lock = (BENCHMARKS / "fullstack_042/rust/Cargo.lock").read_text()
    assert 'name = "fullstack-agent-042"' in rust_manifest
    assert 'name = "fullstack-agent-042"' in rust_lock

    validation = json.loads(
        (BENCHMARKS / "fullstack_agent_042_validation.json").read_text()
    )
    assert validation["protocol_sha256"] == hashlib.sha256(
        (BENCHMARKS / "fullstack_agent_042_protocol.json").read_bytes()
    ).hexdigest()
    assert validation["reference_cells_passed"] == 16
    assert validation["seed_cells_built"] == 16
    assert validation["seed_cells_correct"] == 0
    assert validation["maintenance_root_boundaries_passed"] == 8
    assert len(validation["cells"]) == 16
    assert all(cell["reference_cases"] == 9 for cell in validation["cells"])
    assert all(cell["reference_post_build_integrity"] for cell in validation["cells"])
    assert all(cell["seed_post_build_integrity"] for cell in validation["cells"])
    assert validation["peak_validation_workspace_bytes"] == max(
        max(cell["reference_workspace_bytes"], cell["seed_workspace_bytes"])
        for cell in validation["cells"]
    )
    assert validation["peak_validation_workspace_bytes"] < 2 * 1024**3


def test_fullstack_042_orchestration_and_guards_cover_frozen_paths():
    smoke = json.loads(
        (BENCHMARKS / "fullstack_agent_042_orchestration_smoke.json").read_text()
    )
    assert smoke["experiment_id"] == "042"
    assert smoke["task_id"] == "radio_archive_build"
    assert smoke["protocol_sha256"] == hashlib.sha256(
        (BENCHMARKS / "fullstack_agent_042_protocol.json").read_bytes()
    ).hexdigest()
    assert smoke["commands"] == [
        {"command": "./sources", "returncode": 0},
        {"command": "./check", "returncode": 1},
    ]
    assert smoke["public"]["case_count"] == 4
    assert smoke["hidden"]["case_count"] == 5
    assert smoke["public"]["browser_cases"] == 1
    assert smoke["hidden"]["browser_cases"] == 2
    assert smoke["pass"] is True

    task = load_task_map()["radio_archive_build"]
    assert invalid_numeric_domain(
        task,
        b'{"spoken_segments":-1,"music_segments":2,"language_tracks":2,"live_broadcast":false}',
    )
    assert not invalid_numeric_domain(task, b'{"spoken_segments":"-1"}')
    assert command_protocol(
        [{"command": "./sources"}, {"command": "./check"}]
    )["compliant"] is True
    assert command_protocol(
        [{"command": "./sources"}] + [{"command": "./check"}] * 13
    )["compliant"] is False


def test_fullstack_042_prompt_uses_only_the_frozen_compact_context():
    context = CONTEXT_PATH.read_text(encoding="utf-8")
    cases = load_cases()
    for task in load_task_map().values():
        parley_prompt = render_prompt(task, cases[task["id"]], "parley", context)
        python_prompt = render_prompt(task, cases[task["id"]], "python", context)
        assert context.rstrip() in parley_prompt
        assert "# Frozen Parley scaffolded-web context" in parley_prompt
        assert "# Frozen Parley typed-web reference" not in parley_prompt
        assert len(parley_prompt) - len(python_prompt) == 793
        assert len(O200K.encode(parley_prompt)) - len(O200K.encode(python_prompt)) == 207


def test_fullstack_042_finished_journal_precedes_bounded_cleanup(tmp_path):
    work = tmp_path / "work"
    journals = tmp_path / "journals"
    workspace = work / "cell-workspace"
    workspace.mkdir(parents=True)
    journals.mkdir()
    cell = {"cell_id": "cell-001"}
    row = {"cell_id": "cell-001", "workdir": str(workspace)}
    _, finished = journal_paths(journals, cell["cell_id"])
    finished.write_text(json.dumps({"status": "finished", "result": row}))

    record = ensure_cleanup_record(
        cell,
        row,
        journal_root=journals,
        work_root=work,
    )

    assert record["status"] == "removed"
    assert record["workspace_bytes"] == 0
    assert finished.is_file()
    assert not workspace.exists()
    assert ensure_cleanup_record(
        cell,
        row,
        journal_root=journals,
        work_root=work,
    ) == record


def test_fullstack_042_cleanup_failure_is_immutable_evidence(tmp_path):
    work = tmp_path / "work"
    journals = tmp_path / "journals"
    workspace = work / "nested" / "cell-workspace"
    workspace.mkdir(parents=True)
    (workspace / "retained.txt").write_text("retained")
    journals.mkdir()
    cell = {"cell_id": "cell-002"}
    row = {"cell_id": "cell-002", "workdir": str(workspace)}
    _, finished = journal_paths(journals, cell["cell_id"])
    finished.write_text(json.dumps({"status": "finished", "result": row}))

    record = ensure_cleanup_record(
        cell,
        row,
        journal_root=journals,
        work_root=work,
    )

    assert record["status"] == "failed"
    assert record["workspace_bytes"] == len("retained")
    assert workspace.is_dir()
    assert ensure_cleanup_record(
        cell,
        row,
        journal_root=journals,
        work_root=work,
    ) == record


def test_fullstack_042_resume_identity_excludes_observed_free_space(tmp_path):
    journals = tmp_path / "journals"
    journals.mkdir()
    identity = {
        "protocol_sha256": "protocol",
        "scratch_control": {
            "work_root": "/tmp/work",
            "required_free_bytes": 16,
        },
    }
    initial = {"status": "pass", "filesystem_free_bytes": 32}
    resumed = {"status": "pass", "filesystem_free_bytes": 24}

    path = ensure_run_manifest(
        journals,
        identity,
        resume=False,
        scratch_preflight=initial,
    )
    assert ensure_run_manifest(
        journals,
        identity,
        resume=True,
        scratch_preflight=resumed,
    ) == path
    assert json.loads(path.read_text())["initial_scratch_preflight"] == initial
