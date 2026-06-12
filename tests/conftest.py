import subprocess
import sys
from pathlib import Path

import pytest

from parley.checker import check_program
from parley.diagnostics import ParleyError
from parley.emit_rust import emit_program
from parley.parser import parse

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"


def check_text(src: str):
    """parse + check; returns diagnostics list (empty = clean)."""
    return check_program(parse(src))


def emit_text(src: str) -> str:
    """parse + check (must be clean) + emit; returns Rust source."""
    program = parse(src)
    diags = check_program(program)
    assert not diags, f"unexpected diagnostics: {[(d.code, d.message) for d in diags]}"
    rust, _ = emit_program(program)
    return rust


def diag_codes(src: str) -> list[str]:
    try:
        return [d.code for d in check_text(src)]
    except ParleyError as e:
        return [d.code for d in e.diagnostics]


@pytest.fixture(scope="session")
def workdir(tmp_path_factory) -> Path:
    """One shared directory for all compile-and-run tests, so the cargo
    target cache in .parley-build/ is reused across the session."""
    return tmp_path_factory.mktemp("parley-e2e")


def run_cli(args, cwd: Path, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "parley.cli", *args],
        cwd=cwd, input=stdin, capture_output=True, text=True, timeout=300)


def run_program(workdir: Path, name: str, source: str, stdin: str = "",
                expect_ok: bool = True) -> subprocess.CompletedProcess:
    f = workdir / f"{name}.par"
    f.write_text(source)
    proc = run_cli(["run", f.name], cwd=workdir, stdin=stdin)
    if expect_ok:
        assert proc.returncode == 0, f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    return proc
