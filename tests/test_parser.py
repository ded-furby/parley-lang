"""Parser tests: every construct parses, and parse errors speak English."""

import pytest

import parley.ast_nodes as A
from parley.diagnostics import ParleyError
from parley.parser import load_program, parse


def test_all_constructs_parse():
    src = '''
a mood is one of happy, grumpy

a person has name as text, age as number

to greet with someone as person:
    say "Hello, {someone's name}!"

to bump with changing n as number:
    set n to n plus 1

to main:
    let bob be a person with name "Bob", age 42
    greet with bob
    let nums be a list of 3, 1, 2
    add 9 to nums
    remove item 1 of nums
    for each n in sorted nums:
        say n times 10
    let scores be a map from text to number
    set item "math" of scores to 95
    let empty be an empty list of text
    repeat 2 times:
        say "hi"
    while no:
        stop
    for each i from 1 to 3:
        skip
    when 5:
        is 5:
            say "five"
        otherwise:
            say "not five"
    attempt:
        say 1 divided by 0
    if it failed:
        say the error
    assert yes, "manual assert"
    fail "manual failure"
    let parts be "a,b" split by ","
    say parts joined with "-"
    say 2 to the power of 8
    say remainder of 7 divided by 3
    write "x" to file "f.txt"
    append "y" to file "f.txt"
    let m be read file "f.txt"
    let r be a random number from 1 to 6
    let answer be ask "ok? "
    let num be ask for a number "n: "
    give back
'''
    prog = parse(src)
    assert [r.name for r in prog.records] == ["person"]
    assert [e.name for e in prog.enums] == ["mood"]
    assert [f.name for f in prog.funcs] == ["greet", "bump", "main"]
    main = prog.funcs[2]
    assert len(main.body) > 20
    assert any(isinstance(st, A.Assert) for st in main.body)
    assert any(isinstance(st, A.Fail) for st in main.body)


def test_interpolation_parts():
    prog = parse('to main:\n    say "a {1 plus 2} b"\n')
    say = prog.funcs[0].body[0]
    parts = say.value.parts
    assert parts[0] == "a "
    assert isinstance(parts[1], A.BinOp)
    assert parts[2] == " b"


def test_interpolation_with_escaped_quotes():
    prog = parse('to main:\n    say "x {keys of m joined with \\", \\"} y"\n')
    say = prog.funcs[0].body[0]
    inner = [p for p in say.value.parts if not isinstance(p, str)]
    assert len(inner) == 1
    assert isinstance(inner[0], A.JoinedWith)


def test_possessive_chains():
    prog = parse("to main:\n    say box's corner's x\n")
    say = prog.funcs[0].body[0]
    fg = say.value
    assert isinstance(fg, A.FieldGet) and fg.field_name == "x"
    assert isinstance(fg.obj, A.FieldGet) and fg.obj.field_name == "corner"


def test_missing_colon_is_friendly():
    with pytest.raises(ParleyError) as ei:
        parse("to main\n    say 1\n")
    d = ei.value.diagnostics[0]
    assert d.code == "P101"
    assert "':'" in (d.hint or "")


def test_stray_brace_in_string():
    with pytest.raises(ParleyError) as ei:
        parse('to main:\n    say "oops }"\n')
    assert ei.value.diagnostics[0].code == "P104"


def test_unclosed_interpolation():
    with pytest.raises(ParleyError) as ei:
        parse('to main:\n    say "hi {name"\n')
    assert ei.value.diagnostics[0].code == "P104"


def test_bad_indentation():
    with pytest.raises(ParleyError) as ei:
        parse("to main:\n    say 1\n      say 2\n   say 3\n")
    assert ei.value.diagnostics[0].code in ("P101", "P103")


def test_comments_anywhere():
    src = (
        "note: top comment\n"
        "# hash comment\n"
        "to main:\n"
        "    say 1  # trailing\n"
        "    note: full-line note\n"
        "    say 2\n"
    )
    prog = parse(src)
    assert len(prog.funcs[0].body) == 2


def test_multiword_phrases_allow_extra_spaces():
    prog = parse("to main:\n    say 5 is  more  than 3\n")
    cmp_ = prog.funcs[0].body[0].value
    assert isinstance(cmp_, A.Compare) and cmp_.op == ">"


def test_includes(tmp_path):
    (tmp_path / "util.par").write_text(
        "to double with n as number giving number:\n    give back n times 2\n")
    (tmp_path / "main.par").write_text(
        'include "util.par"\n\nto main:\n    say (double with 21)\n')
    text, srcmap = load_program(tmp_path / "main.par")
    prog = parse(text)
    assert [f.name for f in prog.funcs] == ["double", "main"]
    # line 1 of the combined text comes from util.par
    assert srcmap.loc(1)[0].endswith("util.par")


def test_include_cycle(tmp_path):
    (tmp_path / "a.par").write_text('include "b.par"\n')
    (tmp_path / "b.par").write_text('include "a.par"\n')
    with pytest.raises(ParleyError) as ei:
        load_program(tmp_path / "a.par")
    assert ei.value.diagnostics[0].code == "P105"


def test_include_missing(tmp_path):
    (tmp_path / "main.par").write_text('include "nope.par"\nto main:\n    say 1\n')
    with pytest.raises(ParleyError) as ei:
        load_program(tmp_path / "main.par")
    assert ei.value.diagnostics[0].code == "P105"


def test_include_package_from_parley_modules(tmp_path):
    package = tmp_path / "parley_modules" / "mathkit"
    package.mkdir(parents=True)
    (package / "main.par").write_text(
        "to double with n as number giving number:\n    give back n times 2\n")
    (tmp_path / "main.par").write_text(
        'include "mathkit"\n\nto main:\n    say (double with 21)\n')

    text, srcmap = load_program(tmp_path / "main.par")
    prog = parse(text)

    assert [f.name for f in prog.funcs] == ["double", "main"]
    assert srcmap.loc(1)[0].endswith("parley_modules/mathkit/main.par")


def test_include_package_from_parley_path(tmp_path, monkeypatch):
    package_root = tmp_path / "shared_packages"
    package = package_root / "strings"
    package.mkdir(parents=True)
    (package / "main.par").write_text(
        'to shout with t as text giving text:\n    give back uppercase of t\n')
    (tmp_path / "main.par").write_text(
        'include "strings"\n\nto main:\n    say (shout with "hello")\n')
    monkeypatch.setenv("PARLEY_PATH", str(package_root))

    text, srcmap = load_program(tmp_path / "main.par")
    prog = parse(text)

    assert [f.name for f in prog.funcs] == ["shout", "main"]
    assert srcmap.loc(1)[0].endswith("shared_packages/strings/main.par")


def test_include_bundled_std_package(tmp_path):
    (tmp_path / "main.par").write_text(
        'include "std/math"\n\nto main:\n    say (clamped with 12, 1, 10)\n')

    text, srcmap = load_program(tmp_path / "main.par")
    prog = parse(text)

    assert "clamped" in [f.name for f in prog.funcs]
    assert srcmap.loc(1)[0].endswith("stdlib/std/math.par")


# ------------------------------------------------------------------ v0.2: when patterns + function values

def test_rich_when_patterns_parse():
    src = (
        "to main:\n"
        "    when 5:\n"
        "        is 1, 2 or 3:\n"
        "            say \"small\"\n"
        "        is 10 to 20:\n"
        "            say \"teens\"\n"
        "        is -5 to -1:\n"
        "            say \"negative\"\n"
        "        otherwise:\n"
        "            say \"other\"\n"
    )
    prog = parse(src)
    when = prog.funcs[0].body[0]
    assert isinstance(when, A.When)
    assert [len(pats) for pats, _ in when.arms] == [3, 1, 1]
    rng = when.arms[1][0][0]
    assert rng.kind == "range"
    lo, hi = rng.value
    assert (lo.value, hi.value) == (10, 20)
    neg = when.arms[2][0][0]
    assert [p.value for p in neg.value] == [-5, -1]


def test_function_types_and_refs_parse():
    src = (
        "to apply with f as (function taking number giving number), x as number giving number:\n"
        "    give back (f with x)\n"
        "to main:\n"
        "    say 1\n"
    )
    prog = parse(src)
    fty = prog.funcs[0].params[0].type
    assert isinstance(fty, A.TFunc)
    assert len(fty.params) == 1 and isinstance(fty.params[0], A.TNum)
    assert isinstance(fty.ret, A.TNum)

    ref = parse("to main:\n    let f be the function helper\n").funcs[0].body[0].value
    assert isinstance(ref, A.FuncRef) and ref.name == "helper"


def test_function_type_without_args_or_return():
    src = (
        "to run_it with f as (function), g as (function giving number):\n"
        "    say 1\n"
        "to main:\n"
        "    say 2\n"
    )
    p0, p1 = parse(src).funcs[0].params
    assert isinstance(p0.type, A.TFunc) and p0.type.params == [] and p0.type.ret is None
    assert isinstance(p1.type, A.TFunc) and isinstance(p1.type.ret, A.TNum)


def test_anonymous_function_literal_parse_shape():
    prog = parse(
        "to main:\n"
        "    let offset be 7\n"
        "    let add_offset be a function taking x as number giving number:\n"
        "        give back x plus offset\n"
    )
    closure = prog.funcs[0].body[1].value
    assert type(closure).__name__ == "Closure"
    assert [p.name for p in closure.params] == ["x"]
    assert isinstance(closure.params[0].type, A.TNum)
    assert isinstance(closure.ret, A.TNum)
    assert len(closure.body) == 1
