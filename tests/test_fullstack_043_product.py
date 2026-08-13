import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
PRODUCT = REPO / "benchmarks/fullstack_agent_043_product.json"
BUILDER = REPO / "benchmarks/freeze_fullstack_agent_043_product.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_043_product_is_frozen_before_corpus():
    assert sha256(PRODUCT) == (
        "1ca7bb4fe501eda55991af61cabb715c5c5c53e202df976ef051809576635ed0"
    )
    product = json.loads(PRODUCT.read_text(encoding="utf-8"))

    assert product["parley_version"] == "0.5.4"
    assert product["evidence_commit"] == (
        "bf0f85aa33dbd6d52c17260d85a04155d11518c2"
    )
    assert product["evidence_tree"] == "9f3149e3f742167982e8c48212ac26830870e4bb"
    assert product["agent_context"]["sha256"] == (
        "f40a1030de6b3ed75f47183dee41d1ac3185dd87b747f779dab8835d4d63e8c4"
    )
    assert product["agent_context"]["o200k_base_tokens"] == 222
    assert product["build_evidence"]["improvement_percent"] == 31.5904
    assert product["build_evidence"]["regression_tests_passed"] == 585
    assert product["build_evidence"]["accepted"] is True
    assert "before any iteration-043 task names" in product["construction_boundary"]
    assert "not change iteration 042" in product["claim_boundary"]


def test_fullstack_043_product_builder_is_deterministic(tmp_path):
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
