import json

from conftest import run_cli


def test_workflow_list_shows_bundled_starters(tmp_path):
    proc = run_cli(["workflow", "list"], cwd=tmp_path)

    assert proc.returncode == 0, proc.stderr
    assert "clean-text" in proc.stdout
    assert "log-summary" in proc.stdout
    assert "checklist-report" in proc.stdout


def test_workflow_new_scaffolds_manifest_source_and_sample(tmp_path):
    proc = run_cli(
        ["workflow", "new", "release-report", "--template", "checklist-report"],
        cwd=tmp_path,
    )

    assert proc.returncode == 0, proc.stderr
    root = tmp_path / "release-report"
    assert (root / "main.par").is_file()
    assert (root / "input.txt").is_file()
    manifest = json.loads((root / "workflow.json").read_text())
    assert manifest == {
        "schema_version": 1,
        "name": "release-report",
        "template": "checklist-report",
        "entrypoint": "main.par",
    }

    checked = run_cli(["check", "release-report/main.par", "--json"], cwd=tmp_path)
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["ok"] is True

    manifest["entrypoint"] = "../outside.par"
    (root / "workflow.json").write_text(json.dumps(manifest))
    escaped = run_cli(
        [
            "workflow", "run", "release-report",
            "--input", "release-report/input.txt",
            "--output", "result.txt",
        ],
        cwd=tmp_path,
    )
    assert escaped.returncode == 1
    assert "entrypoint must stay inside" in escaped.stderr


def test_every_workflow_template_type_checks(tmp_path):
    for template in ("clean-text", "log-summary", "checklist-report"):
        name = f"sample-{template}"
        created = run_cli(
            ["workflow", "new", name, "--template", template], cwd=tmp_path)
        assert created.returncode == 0, created.stderr
        checked = run_cli(["check", f"{name}/main.par", "--json"], cwd=tmp_path)
        assert checked.returncode == 0, checked.stderr


def test_workflow_run_executes_clean_text_end_to_end(tmp_path):
    created = run_cli(
        ["workflow", "new", "cleaner", "--template", "clean-text"], cwd=tmp_path)
    assert created.returncode == 0, created.stderr
    source = tmp_path / "messy.txt"
    output = tmp_path / "clean.txt"
    source.write_text("  alpha  \n\n beta\r\n   \n")

    proc = run_cli(
        [
            "workflow", "run", "cleaner",
            "--input", str(source),
            "--output", str(output),
        ],
        cwd=tmp_path,
    )

    assert proc.returncode == 0, proc.stderr
    assert output.read_text() == "alpha\nbeta"
    assert "workflow complete: wrote 2 lines" in proc.stdout

    source.write_text(" replacement ")
    forced = run_cli(
        [
            "workflow", "run", "cleaner",
            "--input", str(source),
            "--output", str(output),
            "--force",
        ],
        cwd=tmp_path,
    )
    assert forced.returncode == 0, forced.stderr
    assert output.read_text() == "replacement"


def test_workflow_run_refuses_missing_input_and_existing_output(tmp_path):
    created = run_cli(
        ["workflow", "new", "safe-run", "--template", "clean-text"], cwd=tmp_path)
    assert created.returncode == 0, created.stderr
    output = tmp_path / "existing.txt"
    output.write_text("keep me")

    missing = run_cli(
        [
            "workflow", "run", "safe-run",
            "--input", "missing.txt",
            "--output", "new.txt",
        ],
        cwd=tmp_path,
    )
    assert missing.returncode == 1
    assert "input file does not exist" in missing.stderr

    source = tmp_path / "source.txt"
    source.write_text("hello")
    existing = run_cli(
        [
            "workflow", "run", "safe-run",
            "--input", str(source),
            "--output", str(output),
        ],
        cwd=tmp_path,
    )
    assert existing.returncode == 1
    assert "output already exists" in existing.stderr
    assert output.read_text() == "keep me"


def test_workflow_run_never_overwrites_its_input(tmp_path):
    created = run_cli(
        ["workflow", "new", "same-file", "--template", "clean-text"], cwd=tmp_path)
    assert created.returncode == 0, created.stderr
    source = tmp_path / "source.txt"
    source.write_text("keep me")

    proc = run_cli(
        [
            "workflow", "run", "same-file",
            "--input", str(source),
            "--output", str(source),
            "--force",
        ],
        cwd=tmp_path,
    )

    assert proc.returncode == 1
    assert "must be different files" in proc.stderr
    assert source.read_text() == "keep me"


def test_workflow_run_detects_hard_link_to_input(tmp_path):
    created = run_cli(
        ["workflow", "new", "hard-link", "--template", "clean-text"], cwd=tmp_path)
    assert created.returncode == 0, created.stderr
    source = tmp_path / "source.txt"
    alias = tmp_path / "alias.txt"
    source.write_text("keep me")
    alias.hardlink_to(source)

    proc = run_cli(
        [
            "workflow", "run", "hard-link",
            "--input", str(source),
            "--output", str(alias),
            "--force",
        ],
        cwd=tmp_path,
    )

    assert proc.returncode == 1
    assert "must be different files" in proc.stderr
    assert source.read_text() == "keep me"
