import json
from pathlib import Path
import subprocess

import tiktoken

from benchmarks.fullstack_agent_046_scaffolds import (
    LANGUAGES,
    ROOT_FILES,
    load_task_map,
    scaffold_files,
)


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
CASES = json.loads(
    (BENCHMARKS / "fullstack_agent_046_cases.json").read_text()
)["tasks"]
O200K = tiktoken.get_encoding("o200k_base")


def test_fullstack_046_scaffolds_are_symmetric_and_compact():
    tasks = load_task_map()
    assert tuple(LANGUAGES) == ("parley", "python", "typescript", "rust")
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
                assert ROOT_FILES[language][0] in changed
                assert changed

        manifest_text = scaffold_files(task, "parley", "seed")[
            "parley.web.json"
        ].text
        manifest = json.loads(manifest_text)
        assert manifest_text == json.dumps(manifest, separators=(",", ":")) + "\n"
        assert len(O200K.encode(manifest_text)) <= 135
        assert manifest["routes"][1]["response"] == {
            "status_field": "status", "headers_field": "headers", "body_field": "body",
        }


def test_fullstack_046_python_and_browser_reference_scores_match_oracle(tmp_path):
    for task in load_task_map().values():
        files = scaffold_files(task, "python", "reference")
        namespace = {}
        logic = files["logic.py"].text
        score_source = logic[logic.index("def score("):logic.index("def calculate(")]
        exec(compile(score_source, "score.py", "exec"), namespace)
        score = namespace["score"]
        for case in CASES[task["id"]]:
            if case["target"] != "browser":
                continue
            assert score(*case["args"]) == case["expected"]

        browser = tmp_path / f"{task['id']}.mjs"
        browser.write_text(files["browser.js"].text)
        args = CASES[task["id"]][3]["args"]
        script = (
            f"import{{loadParley}}from{json.dumps(browser.as_uri())};"
            f"const p=await loadParley();console.log(String(p[{json.dumps(task['browser_export'])}]"
            f"(...{json.dumps(args)})));"
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        assert int(completed.stdout) == CASES[task["id"]][3]["expected"]


def test_fullstack_046_maintenance_defects_are_exact_and_root_local():
    tasks = load_task_map()
    archive = tasks["archive_transfer_repair"]
    beacon = tasks["beacon_enrollment_repair"]
    patterns = {
        "parley": ("x-transfer-state", "status 201"),
        "python": ("'x-transfer-state'", "outcome(body,201"),
        "typescript": ("'x-transfer-state'", "response(body,201"),
        "rust": ('("x-transfer-state"', "json_response(body,201"),
    }
    for language, (archive_defect, beacon_defect) in patterns.items():
        archive_seed = scaffold_files(archive, language, "seed")[
            ROOT_FILES[language][0]
        ].text
        archive_reference = scaffold_files(archive, language, "reference")[
            ROOT_FILES[language][0]
        ].text
        beacon_seed = scaffold_files(beacon, language, "seed")[
            ROOT_FILES[language][0]
        ].text
        beacon_reference = scaffold_files(beacon, language, "reference")[
            ROOT_FILES[language][0]
        ].text
        assert archive_defect in archive_seed
        assert archive_defect not in archive_reference
        assert "x-transfer-phase" in archive_reference
        assert beacon_defect in beacon_seed
        assert beacon_seed != beacon_reference


def test_fullstack_046_rust_dependency_lock_is_canonical():
    manifest = (BENCHMARKS / "fullstack_046/rust/Cargo.toml").read_text()
    lock = (BENCHMARKS / "fullstack_046/rust/Cargo.lock").read_text()
    assert 'name = "fullstack-agent-046"' in manifest
    assert 'name = "fullstack-agent-046"' in lock
    completed = subprocess.run(
        ["cargo", "metadata", "--locked", "--offline", "--format-version", "1"],
        cwd=BENCHMARKS / "fullstack_046/rust",
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
