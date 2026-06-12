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
