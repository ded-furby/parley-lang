import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
PRODUCT = REPO / "benchmarks/fullstack_agent_045_product.json"
BUILDER = REPO / "benchmarks/freeze_fullstack_agent_045_product.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_045_product_is_frozen_before_corpus():
    assert sha256(PRODUCT) == (
        "49e1ee43ce014e3888a193442e426269f7bdf19b0403ab29a2b3a40505596216"
    )
    product = json.loads(PRODUCT.read_text(encoding="utf-8"))
    assert product["parley_version"] == "0.5.6"
    assert product["product_commit"] == (
        "6bae1149d101d5a483f31f55905083e0a939c1da"
    )
    assert product["product_tree"] == "525b23b0191cb5f16a9cc4b5281d9b9af912898c"
    assert product["context_commit"] == (
        "1a73fc7ea7d60f5235d5cd3173eba858a6a384b7"
    )
    assert product["agent_context"]["o200k_base_tokens"] == 313
    assert product["agent_context"]["freeze_sha256"] == (
        "746f1af9c788c5a441657c500f89a276f7402bdb0bb806433a58af4553eb24ab"
    )
    assert product["product_evidence"]["accepted"] is True
    assert product["product_evidence"]["full_tests_after_version_advance"] == 643
    assert "before any iteration-045 task domain" in product[
        "construction_boundary"
    ]
    assert "does not reinterpret iteration 044" in product["claim_boundary"]


def test_fullstack_045_product_builder_is_deterministic(tmp_path):
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
