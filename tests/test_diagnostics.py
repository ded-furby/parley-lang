"""Diagnostics tests: stable codes, JSON contract, catalog completeness."""

import json
import re
from pathlib import Path

from parley.diagnostics import ERROR_CATALOG, Diagnostic, explain, render_human, render_json

REPO = Path(__file__).resolve().parent.parent


def test_render_json_contract():
    out = json.loads(render_json([
        Diagnostic("P201", 'There is no "x" here.', file="m.par", line=3, col=9,
                   hint='Did you mean "y"?')]))
    assert out["ok"] is False
    d = out["diagnostics"][0]
    assert set(d) == {"code", "message", "file", "line", "col", "hint",
                      "replacement", "severity"}
    assert d["code"] == "P201" and d["line"] == 3


def test_render_json_ok():
    assert json.loads(render_json([]))["ok"] is True


def test_render_human_has_caret_and_hint():
    out = render_human(
        [Diagnostic("P201", 'no "x"', file="m.par", line=1, col=5, hint="try y")],
        {"m.par": "let x be 1\n"})
    assert "-->" in out and "^" in out and "hint:" in out


def test_explain_known_and_unknown():
    assert "Unknown field" in explain("P204")
    assert "p204" not in explain("p204") or "Unknown field" in explain("p204")
    assert "Unknown code" in explain("P999")


def test_every_emitted_code_is_in_the_catalog():
    """Grep the compiler sources for P-codes; each must have a catalog entry."""
    used = set()
    for f in ["parser.py", "checker.py", "cli.py"]:
        src = (REPO / "parley" / f).read_text()
        used |= set(re.findall(r'"(P\d{3})"', src))
    missing = used - set(ERROR_CATALOG)
    assert not missing, f"codes without catalog entries: {missing}"


def test_catalog_entries_are_complete():
    for code, entry in ERROR_CATALOG.items():
        assert entry.get("title") and entry.get("explain") and entry.get("fix"), code


def test_errors_doc_covers_every_code():
    doc = (REPO / "docs" / "ERRORS.md").read_text()
    for code in ERROR_CATALOG:
        assert code in doc, f"{code} missing from docs/ERRORS.md"
