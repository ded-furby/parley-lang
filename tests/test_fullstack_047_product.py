import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
PRODUCT = BENCHMARKS / "fullstack_agent_047_product.json"
BUILDER = BENCHMARKS / "freeze_fullstack_agent_047_product.py"


def git_blob(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout


def test_fullstack_047_product_freezes_exact_pre_corpus_boundary():
    product = json.loads(PRODUCT.read_text(encoding="utf-8"))
    assert product["schema_version"] == 1
    assert product["experiment_id"] == "047"
    assert product["phase"] == "pre-corpus product and evidence freeze"
    assert product["parley"]["version"] == "0.5.7"
    assert product["context"]["o200k_base_tokens"] == 176
    assert product["corpus_selected_before_freeze"] is False
    assert product["measured_sessions_before_freeze"] == 0
    assert product["previous_study_boundary"]["status"] == (
        "valid; strict gate failed on elapsed time"
    )
    assert product["previous_study_boundary"]["same_corpus_reuse"] is False
    for group in ("product", "context", "evidence"):
        commit = (
            product["parley"]["product_commit"]
            if group == "product"
            else product["context"]["commit"]
        )
        for path, expected in product["files"][group].items():
            assert hashlib.sha256(git_blob(commit, path)).hexdigest() == expected

    paths = set(
        subprocess.run(
            [
                "git",
                "ls-tree",
                "-r",
                "--name-only",
                product["pre_corpus_anchor_commit"],
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
    )
    assert not any(path.startswith("benchmarks/fullstack_agent_047_tasks") for path in paths)
    assert "benchmarks/fullstack_agent_047_raw.json" not in paths


def test_fullstack_047_product_builder_is_deterministic(tmp_path):
    output = tmp_path / "product.json"
    completed = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == PRODUCT.read_bytes()
