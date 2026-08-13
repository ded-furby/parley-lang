import hashlib
from pathlib import Path
import subprocess

from parley import __version__


REPO = Path(__file__).resolve().parents[1]
PROTOCOL = REPO / "benchmarks/WEB_PATH_PARAMETERS_004.md"
BASELINE_COMMIT = "bed8fde8f9e0c2f603d2f6a764619c676d123f2a"
BASELINE_TREE = "6e3b0c94227d25d3a4c47e5015270a4a4de52d75"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_web_path_parameters_004_is_preimplementation_freeze():
    assert __version__ == "0.5.6"
    assert git("show", "-s", "--format=%T", BASELINE_COMMIT) == BASELINE_TREE
    assert git("diff", "--name-only", BASELINE_COMMIT, "--", "parley") == ""
    assert "path_parameters" not in (REPO / "parley/web.py").read_text()
    assert "P725" not in (REPO / "parley/diagnostics.py").read_text()


def test_web_path_parameters_004_freezes_complete_gate():
    protocol = PROTOCOL.read_text(encoding="utf-8")
    for boundary in (
        "Exact routes take priority",
        "Two templates for the same method are rejected",
        "sixth and final field",
        "stable diagnostic P725",
        "percent-decoded exactly once as UTF-8",
        "invalid_path_parameter",
        "without invoking handler logic",
        "historical frozen references remain byte-for-byte unchanged",
        "universal language superiority",
    ):
        assert boundary in protocol
    assert len(protocol.split("## Preregistered verification gate", 1)[1].splitlines()) > 20


def test_web_path_parameters_004_protocol_hash_is_frozen():
    assert hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() == (
        "d27d2f3ab39dd4ec3578f362ee7a3d4cf347526cc5039d7ac0159f29b398a531"
    )
