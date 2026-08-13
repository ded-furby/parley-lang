import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
CONTEXT = REPO / "skill/parley/references/scaffolded-response-web-v0.5.6.md"
MANIFEST = REPO / "benchmarks/fullstack_agent_045_context.json"
BUILDER = REPO / "benchmarks/freeze_fullstack_agent_045_context.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v056_response_web_context_is_compact_and_complete():
    context = CONTEXT.read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["parley_version"] == "0.5.6"
    assert manifest["product_commit"] == (
        "6bae1149d101d5a483f31f55905083e0a939c1da"
    )
    assert len(context.encode()) == manifest["context_bytes"] == 1281
    assert sha256(CONTEXT) == manifest["context_sha256"] == (
        "58e1066e2c313c35617d96c5f8829e4ca14f6a77a60fdba0d8af7b19a2fab2b8"
    )
    assert manifest["context_o200k_tokens"] == 313
    assert manifest["baseline"]["combined_o200k_tokens"] == 1164
    assert manifest["reduction"] == {
        "bytes": 3069,
        "o200k_tokens": 851,
        "o200k_percent": 73.11,
    }
    assert manifest["increment_from_v053_card"]["added_o200k_tokens"] == 91
    for required in [
        "printed scaffold is authoritative",
        '"response":{"status_field":"status"',
        "exactly a record",
        "map from text to text",
        'maybe item "authorization"',
        "200--599",
        "server-owned framing or hop-by-hop",
        "Do not add I/O",
        "extra checker runs",
    ]:
        assert required in context


def test_v056_response_context_freeze_is_deterministic(tmp_path):
    output = tmp_path / "context.json"
    completed = subprocess.run(
        [sys.executable, str(BUILDER), "--output", str(output)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == MANIFEST.read_bytes()
    assert sha256(MANIFEST) == (
        "746f1af9c788c5a441657c500f89a276f7402bdb0bb806433a58af4553eb24ab"
    )
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert "before any iteration-045 task domain" in manifest[
        "construction_boundary"
    ]
    assert "not evidence of agent correctness" in manifest["claim_boundary"]
