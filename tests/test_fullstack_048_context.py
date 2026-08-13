import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "benchmarks/build_fullstack_agent_048_context.py"
FREEZE = REPO / "benchmarks/fullstack_agent_048_context.json"
CONTEXT = REPO / "skill/parley/references/scaffolded-query-response-web-v0.5.8-compact.md"
PRODUCT_COMMIT = "8d040c55fcc4ad502bdc6449c363035a42d0dceb"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_048_context_freeze_is_pre_corpus_and_compact():
    payload = json.loads(FREEZE.read_text())
    assert payload["experiment_id"] == "048"
    assert payload["product"]["commit"] == PRODUCT_COMMIT
    assert payload["context"] == {
        "file": "skill/parley/references/scaffolded-query-response-web-v0.5.8-compact.md",
        "sha256": "f7cadc7bfe839a5174bc1064fbed3a021ab9251386b57173bdf6e69b75ed7a92",
        "bytes": 921,
        "o200k_base_tokens": 217,
    }
    assert payload["corpus_selected_before_freeze"] is False
    assert payload["measured_sessions_before_freeze"] == 0
    assert payload["maximum_o200k_base_tokens"] == 225


def test_fullstack_048_context_contains_required_safe_forms():
    text = CONTEXT.read_text()
    for phrase in (
        "edit the smallest owner",
        "path_parameters` sixth",
        "query_parameters as map from text to list of text` seventh/last",
        "request's query_parameters",
        "otherwise a list of text",
        "Never set framing/hop headers",
        "never combine `not` with another comparator",
    ):
        assert phrase in text


def test_fullstack_048_context_builder_is_deterministic(tmp_path):
    output = tmp_path / "context.json"
    completed = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == FREEZE.read_bytes()


def test_fullstack_048_context_has_no_corpus_at_product_commit():
    paths = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", PRODUCT_COMMIT],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "fullstack_agent_048_tasks.json" not in paths
    assert "fullstack_agent_048_cases.json" not in paths
    assert "fullstack_agent_048_protocol.json" not in paths
    assert sha256(CONTEXT) == (
        "f7cadc7bfe839a5174bc1064fbed3a021ab9251386b57173bdf6e69b75ed7a92"
    )
