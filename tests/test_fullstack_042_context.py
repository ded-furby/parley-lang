import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
CONTEXT = REPO / "skill/parley/references/scaffolded-web-v0.5.3.md"
MANIFEST = REPO / "benchmarks/fullstack_agent_042_context.json"
BUILDER = REPO / "benchmarks/freeze_fullstack_agent_042_context.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v053_scaffolded_web_context_is_frozen_compact_and_complete():
    context = CONTEXT.read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["parley_version"] == "0.5.3"
    assert len(context.encode()) == manifest["context_bytes"] == 892
    assert sha256(CONTEXT) == manifest["context_sha256"] == (
        "f40a1030de6b3ed75f47183dee41d1ac3185dd87b747f779dab8835d4d63e8c4"
    )
    assert manifest["context_o200k_tokens"] == 222
    assert manifest["baseline"]["combined_o200k_tokens"] == 1164
    assert manifest["reduction"] == {
        "bytes": 3458,
        "o200k_tokens": 942,
        "o200k_percent": 80.9278,
    }
    for required in [
        "printed scaffold is authoritative",
        "smallest owning included",
        "HTTP and browser paths call one rule",
        "four-space blocks",
        "`times` or `multiplied by`",
        "`number from (a divided by b)`",
        "total—never add `otherwise`",
        "JavaScript `bigint`, `number`, and `boolean`",
        "Do not add I/O",
    ]:
        assert required in context
    for deliberately_omitted in ['"schema_version"', "loadParley", "web_request"]:
        assert deliberately_omitted not in context


def test_v053_context_freeze_is_deterministic_and_preserves_claim_boundary(tmp_path):
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
        "2fb41ea35931df100ff71ec3b8c2137fd89f93b5a95c5fb22474aa9465217f97"
    )
    manifest = json.loads(output.read_text(encoding="utf-8"))
    assert manifest["evidence_commit"] == (
        "c18f282da0d358165477daa093844d5ebb4adcda"
    )
    assert "before any iteration-042 task semantics" in manifest[
        "construction_boundary"
    ]
    assert "not a reliability or comparative token-efficiency result" in manifest[
        "claim_boundary"
    ]
