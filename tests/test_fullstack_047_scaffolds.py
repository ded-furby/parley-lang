import json
from pathlib import Path
import subprocess

import tiktoken

from benchmarks.fullstack_agent_047_scaffolds import (
    LANGUAGES,
    ROOT_FILES,
    load_task_map,
    scaffold_files,
)


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
CASES = json.loads(
    (BENCHMARKS / "fullstack_agent_047_cases.json").read_text()
)["tasks"]
O200K = tiktoken.get_encoding("o200k_base")


def test_fullstack_047_scaffolds_are_symmetric_path_aware_and_compact():
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
                assert changed

        manifest_text = scaffold_files(task, "parley", "seed")[
            "parley.web.json"
        ].text
        manifest = json.loads(manifest_text)
        assert manifest_text == json.dumps(manifest, separators=(",", ":")) + "\n"
        assert len(O200K.encode(manifest_text)) <= 180
        assert [row["path"] for row in manifest["routes"]] == [
            task["parameter_route"], task["exact_route"], task["status_route"],
        ]
        assert manifest["routes"][0]["response"] == manifest["routes"][1]["response"] == {
            "status_field": "status", "headers_field": "headers", "body_field": "body",
        }
        main = scaffold_files(task, "parley", "seed")["main.par"].text
        assert "path_parameters as map from text to text" in main
        assert "(number from capture) otherwise 0" in main


def test_fullstack_047_python_and_browser_reference_scores_match_oracle(tmp_path):
    for task in load_task_map().values():
        files = scaffold_files(task, "python", "reference")
        namespace = {}
        exec(compile(files["logic.py"].text, "logic.py", "exec"), namespace)
        score = namespace["score"]
        for case in CASES[task["id"]]:
            if case["target"] == "browser":
                assert score(*case["args"]) == case["expected"]

        browser = tmp_path / f"{task['id']}.mjs"
        browser.write_text(files["browser.js"].text)
        case = next(
            row for row in CASES[task["id"]] if row["id"].endswith("browser_primary")
        )
        script = (
            f"import{{loadParley}}from{json.dumps(browser.as_uri())};"
            f"const p=await loadParley();console.log(String(p[{json.dumps(task['browser_export'])}]"
            f"(...{json.dumps(case['args'])})));"
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "--eval", script],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        assert int(completed.stdout) == case["expected"]


def test_fullstack_047_maintenance_defects_are_exact_and_root_local():
    tasks = load_task_map()
    band = tasks["aviary_band_lookup_repair"]
    gate = tasks["canal_gate_lookup_repair"]
    patterns = {
        "parley": ('item "band_code"', "let capture be request's path\n"),
        "python": ("params.get('band_code'", "capture=request.url.path"),
        "typescript": ("params['band_code']", "capture=rawPath"),
        "rust": ('params.get("band_code")', "capture=raw_path.to_string()"),
    }
    for language, (band_defect, gate_defect) in patterns.items():
        root = ROOT_FILES[language][0]
        band_seed = scaffold_files(band, language, "seed")[root].text
        band_reference = scaffold_files(band, language, "reference")[root].text
        gate_seed = scaffold_files(gate, language, "seed")[root].text
        gate_reference = scaffold_files(gate, language, "reference")[root].text
        assert band_defect in band_seed and band_defect not in band_reference
        assert gate_defect in gate_seed and gate_defect not in gate_reference
        assert band_seed != band_reference
        assert gate_seed != gate_reference


def test_fullstack_047_rust_dependency_lock_is_canonical():
    manifest = (BENCHMARKS / "fullstack_047/rust/Cargo.toml").read_text()
    lock = (BENCHMARKS / "fullstack_047/rust/Cargo.lock").read_text()
    assert 'name = "fullstack-agent-047"' in manifest
    assert 'name = "fullstack-agent-047"' in lock
    completed = subprocess.run(
        ["cargo", "metadata", "--locked", "--offline", "--format-version", "1"],
        cwd=BENCHMARKS / "fullstack_047/rust",
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
