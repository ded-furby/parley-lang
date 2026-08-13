import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
PRODUCT = REPO / "benchmarks/fullstack_agent_044_product.json"
BUILDER = REPO / "benchmarks/freeze_fullstack_agent_044_product.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_044_product_is_frozen_before_corpus():
    assert sha256(PRODUCT) == (
        "181e26d1204765f3e14a1a24dfe9d82a545d271b3da900785716e509e1551e89"
    )
    product = json.loads(PRODUCT.read_text(encoding="utf-8"))

    assert product["parley_version"] == "0.5.5"
    assert product["evidence_commit"] == (
        "a098996847927c4eb622e2af8d0b7ebee81011c6"
    )
    assert product["evidence_tree"] == "be8be51158157fc33b6b0e00e5ce62e6478d94fe"
    assert product["agent_context"]["sha256"] == (
        "f40a1030de6b3ed75f47183dee41d1ac3185dd87b747f779dab8835d4d63e8c4"
    )
    assert product["agent_context"]["o200k_base_tokens"] == 222
    assert product["build_evidence"]["improvement_percent"] == 70.5496
    assert product["build_evidence"]["regression_tests_passed"] == 609
    assert product["build_evidence"]["accepted"] is True
    assert "before any iteration-044 task names" in product["construction_boundary"]
    assert "not change iteration 043" in product["claim_boundary"]


def test_fullstack_044_product_builder_is_deterministic(tmp_path):
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
