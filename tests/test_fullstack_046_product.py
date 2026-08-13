import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
PRODUCT = BENCHMARKS / "fullstack_agent_046_product.json"
BUILDER = BENCHMARKS / "freeze_fullstack_agent_046_product.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_046_product_freezes_before_corpus():
    product = json.loads(PRODUCT.read_text(encoding="utf-8"))
    assert product["schema_version"] == 1
    assert product["experiment_id"] == "046"
    assert product["phase"] == "pre-corpus product and evidence freeze"
    assert product["parley"]["version"] == "0.5.6"
    assert product["context"]["o200k_base_tokens"] == 124
    assert product["corpus_selected_before_freeze"] is False
    assert product["measured_sessions_before_freeze"] == 0
    assert product["iteration_045_boundary"] == {
        "result_commit": "61fe34729f6361846cf418183cc3fa240c09516c",
        "result_tree": "47bc7ddd46b9cff8aa1192ff9156f10c0bc29415",
        "status": "invalid; frozen gate failed",
        "selective_rerun": False,
        "same_corpus_reuse": False,
    }
    for item in product["files"].values():
        assert sha256(REPO / item["file"]) == item["sha256"]
    frozen_paths = set(
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
    for name in (
        "fullstack_agent_046_tasks.json",
        "fullstack_agent_046_cases.json",
        "fullstack_agent_046_protocol.json",
        "fullstack_agent_046_scaffolds.py",
        "fullstack_agent_046_logic.py",
        "fullstack_agent_046_raw.json",
        "fullstack_agent_046_audit.json",
    ):
        assert f"benchmarks/{name}" not in frozen_paths


def test_fullstack_046_product_builder_is_deterministic(tmp_path):
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
