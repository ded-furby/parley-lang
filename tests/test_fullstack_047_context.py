import hashlib
import json
from pathlib import Path
import subprocess
import sys

import tiktoken


REPO = Path(__file__).resolve().parents[1]
BENCHMARKS = REPO / "benchmarks"
CONTEXT = REPO / "skill/parley/references/scaffolded-path-response-web-v0.5.7-compact.md"
ARTIFACT = BENCHMARKS / "fullstack_agent_047_context.json"
BUILDER = BENCHMARKS / "build_fullstack_agent_047_context.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fullstack_047_context_is_compact_complete_and_pre_corpus():
    text = CONTEXT.read_text(encoding="utf-8")
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert len(CONTEXT.read_bytes()) <= 800
    assert len(tiktoken.get_encoding("o200k_base").encode(text)) <= 190
    for required in (
        "exact typed status/headers/body record",
        "Never set framing/hop headers",
        "extended `web_request` with `path_parameters` last",
        "request's path_parameters",
        "Exact routes win",
        "captures are already decoded",
        "never combine `not` with another comparator",
        "number from (a divided by b)",
    ):
        assert required in text
    assert artifact["experiment_id"] == "047"
    assert artifact["phase"] == "pre-corpus context freeze"
    assert artifact["corpus_selected_before_freeze"] is False
    assert artifact["measured_sessions_before_freeze"] == 0
    assert artifact["context"]["sha256"] == sha256(CONTEXT)


def test_fullstack_047_context_builder_is_deterministic(tmp_path):
    output = tmp_path / "context.json"
    completed = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == ARTIFACT.read_bytes()
