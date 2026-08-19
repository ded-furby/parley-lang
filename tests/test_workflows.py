import json

from conftest import REPO, run_cli


def test_workflow_list_shows_bundled_starters(tmp_path):
    proc = run_cli(["workflow", "list"], cwd=tmp_path)

    assert proc.returncode == 0, proc.stderr
    assert "clean-text" in proc.stdout
    assert "log-summary" in proc.stdout
    assert "checklist-report" in proc.stdout


def test_workflow_new_refuses_path_shaped_names(tmp_path):
    # "../sneaky" used to scaffold outside the working directory because only
    # the final path component was validated.
    for bad in ("../sneaky", "a/b", "..", "."):
        proc = run_cli(["workflow", "new", bad], cwd=tmp_path)
        assert proc.returncode == 1
        assert "bare product name" in proc.stderr
    assert list(tmp_path.iterdir()) == []
    assert not (tmp_path.parent / "sneaky").exists()


def test_workflow_new_scaffolds_manifest_source_and_sample(tmp_path):
    proc = run_cli(
        ["workflow", "new", "release-report", "--template", "checklist-report"],
        cwd=tmp_path,
    )

    assert proc.returncode == 0, proc.stderr
    root = tmp_path / "release-report"
    assert (root / "main.par").is_file()
    assert (root / "input.txt").is_file()
    assert (root / "tests" / "sample" / "input.txt").is_file()
    assert (root / "tests" / "sample" / "expected.txt").is_file()
    manifest = json.loads((root / "workflow.json").read_text())
    assert manifest == {
        "schema_version": 2,
        "name": "release-report",
        "template": "checklist-report",
        "entrypoint": "main.par",
        "inputs": [
            {"name": "source", "description": "Text file to process"},
        ],
        "tests": [
            {
                "name": "sample",
                "inputs": {"source": "tests/sample/input.txt"},
                "expected_output": "tests/sample/expected.txt",
            },
        ],
    }

    checked = run_cli(["check", "release-report/main.par", "--json"], cwd=tmp_path)
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["ok"] is True

    manifest["entrypoint"] = "../outside.par"
    (root / "workflow.json").write_text(json.dumps(manifest))
    escaped = run_cli(
        [
            "workflow", "run", "release-report",
            "--input", "source=release-report/input.txt",
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
        tested = run_cli(["workflow", "test", name], cwd=tmp_path)
        assert tested.returncode == 0, tested.stderr
        assert "All 1 workflow fixtures passed." in tested.stdout


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
            "--input", f"source={source}",
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
            "--input", f"source={source}",
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
            "--input", "source=missing.txt",
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
            "--input", f"source={source}",
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
            "--input", f"source={source}",
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
            "--input", f"source={source}",
            "--output", str(alias),
            "--force",
        ],
        cwd=tmp_path,
    )

    assert proc.returncode == 1
    assert "must be different files" in proc.stderr
    assert source.read_text() == "keep me"


def test_schema_one_workflow_remains_backward_compatible(tmp_path):
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "main.par").write_text(
        'include "std/workflow"\n\n'
        "to main:\n"
        '    let input_path be ask "Input: "\n'
        '    let output_path be ask "Output: "\n'
        "    let source be (workflow_read_required_text with input_path)\n"
        "    workflow_write_output with output_path, source\n"
    )
    (root / "workflow.json").write_text(json.dumps({
        "schema_version": 1,
        "name": "legacy",
        "entrypoint": "main.par",
    }))
    (tmp_path / "source.txt").write_text("legacy works")

    proc = run_cli([
        "workflow", "run", "legacy",
        "--input", "source.txt",
        "--output", "output.txt",
    ], cwd=tmp_path)

    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "output.txt").read_text() == "legacy works"


def test_schema_two_named_inputs_are_ordered_and_validated(tmp_path):
    root = tmp_path / "combiner"
    root.mkdir()
    (root / "main.par").write_text(
        'include "std/workflow"\n\n'
        "to main:\n"
        '    let left_path be ask "Left: "\n'
        '    let right_path be ask "Right: "\n'
        '    let output_path be ask "Output: "\n'
        "    let left be (workflow_read_required_text with left_path)\n"
        "    let right be (workflow_read_required_text with right_path)\n"
        '    workflow_write_output with output_path, "{left}|{right}"\n'
    )
    (root / "workflow.json").write_text(json.dumps({
        "schema_version": 2,
        "name": "combiner",
        "entrypoint": "main.par",
        "inputs": [{"name": "left"}, {"name": "right"}],
    }))
    (tmp_path / "left.txt").write_text("L")
    (tmp_path / "right.txt").write_text("R")

    proc = run_cli([
        "workflow", "run", "combiner",
        "--input", "right=right.txt",
        "--input", "left=left.txt",
        "--output", "combined.txt",
    ], cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "combined.txt").read_text() == "L|R"

    missing = run_cli([
        "workflow", "run", "combiner",
        "--input", "left=left.txt",
        "--output", "unused.txt",
    ], cwd=tmp_path)
    assert missing.returncode == 1
    assert "missing workflow inputs: right" in missing.stderr

    unknown = run_cli([
        "workflow", "run", "combiner",
        "--input", "left=left.txt",
        "--input", "extra=right.txt",
        "--output", "unused.txt",
    ], cwd=tmp_path)
    assert unknown.returncode == 1
    assert "unknown workflow input: extra" in unknown.stderr


def test_workflow_test_reports_exact_output_difference(tmp_path):
    created = run_cli([
        "workflow", "new", "fixture-check", "--template", "clean-text",
    ], cwd=tmp_path)
    assert created.returncode == 0, created.stderr
    expected = tmp_path / "fixture-check" / "tests" / "sample" / "expected.txt"
    expected.write_text("wrong\n")

    proc = run_cli(["workflow", "test", "fixture-check"], cwd=tmp_path)

    assert proc.returncode == 1
    assert "FAIL sample: output differs" in proc.stdout
    assert "--- tests/sample/expected.txt" in proc.stdout
    assert "+first useful line" in proc.stdout


def test_every_catalog_workflow_fixture_passes(tmp_path):
    catalog = REPO / "parley" / "workflows" / "catalog"
    for name in ("release-steward", "log-summary", "checklist-report"):
        proc = run_cli(["workflow", "test", str(catalog / name)], cwd=tmp_path)
        assert proc.returncode == 0, proc.stderr

    assert "PASS ready release" in run_cli(
        ["workflow", "test", str(catalog / "release-steward")],
        cwd=tmp_path,
    ).stdout


def test_catalog_workflows_install_test_and_verify(tmp_path):
    names = ("release-steward", "log-summary", "checklist-report")
    for name in names:
        installed = run_cli(["workflow", "install", name], cwd=tmp_path)
        assert installed.returncode == 0, installed.stderr
        assert f"Installed workflow {name} 1.0.0" in installed.stdout
        assert (tmp_path / "parley_workflows" / name / "workflow.json").is_file()

        tested = run_cli(["workflow", "test", name], cwd=tmp_path)
        assert tested.returncode == 0, tested.stderr

    lock = json.loads((tmp_path / "parley.workflows.lock.json").read_text())
    assert lock["schema_version"] == 1
    assert set(lock["workflows"]) == set(names)
    for metadata in lock["workflows"].values():
        assert metadata["version"] == "1.0.0"
        assert len(metadata["sha256"]) == 64

    verified = run_cli(["workflow", "verify"], cwd=tmp_path)
    assert verified.returncode == 0, verified.stderr
    assert "Verified 3 installed workflows." in verified.stdout

    refused = run_cli(["workflow", "install", "release-steward"], cwd=tmp_path)
    assert refused.returncode == 1
    assert "already installed" in refused.stderr

    main = tmp_path / "parley_workflows" / "log-summary" / "main.par"
    main.write_text(main.read_text() + "\nnote: local drift\n")
    drift = run_cli(["workflow", "verify"], cwd=tmp_path)
    assert drift.returncode == 1
    assert "log-summary: checksum mismatch" in drift.stderr
