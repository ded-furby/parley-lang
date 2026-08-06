"""Parser tests: every construct parses, and parse errors speak English."""

import pytest

import parley.ast_nodes as A
from parley.diagnostics import ParleyError
from parley.parser import load_program, parse, parse_program


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


def test_map_values_expression_parse():
    prog = parse("to main:\n    say values of scores\n")
    expr = prog.funcs[0].body[0].value
    assert isinstance(expr, A.PrefixOp)
    assert expr.op == "values"
    assert isinstance(expr.value, A.Var)
    assert expr.value.name == "scores"


def test_text_replacement_expression_parse():
    prog = parse('to main:\n    say "a-b-a" replacing "-" with ":"\n')
    expr = prog.funcs[0].body[0].value
    assert isinstance(expr, A.ReplacingWith)
    assert isinstance(expr.value, A.Str)
    assert isinstance(expr.old, A.Str)
    assert isinstance(expr.new, A.Str)


@pytest.mark.parametrize("src,expected_hint", [
    # A value position says "a value" instead of listing every way to spell one.
    ('to main:\n    let y be\n', "Expected a value."),
    ('to main:\n    say 1 plus\n', "Expected a value."),
    # Layout expectations outrank operator continuations.
    ('to main:\n    sort_number xs\n', "Expected the end of the line or 'with'."),
])
def test_parse_hint_is_short_and_useful(src, expected_hint):
    with pytest.raises(ParleyError) as ei:
        parse(src)
    assert ei.value.diagnostics[0].hint.startswith(expected_hint)


@pytest.mark.parametrize("src", [
    'to main:\n    let n be some "x"\n    say "name: {n otherwise "unknown"}"\n',
    'to main:\n    let n be some "x"\n    say "name: {n otherwise "?"}"\n',
])
def test_nested_quote_inside_interpolation_names_the_real_mistake(src):
    with pytest.raises(ParleyError) as ei:
        parse(src)
    assert "Escape quotes inside" in ei.value.diagnostics[0].hint


def test_parse_hint_never_leaks_internal_terminal_names():
    with pytest.raises(ParleyError) as ei:
        parse("to f with x as number\n    give back x\n")
    hint = ei.value.diagnostics[0].hint
    assert "param and" not in hint


def test_parse_error_names_the_line_end_not_whitespace():
    with pytest.raises(ParleyError) as ei:
        parse("to main:\n    if yes\n        say 1\n")
    assert "the end of the line" in ei.value.diagnostics[0].message


def test_top_level_statements_become_main():
    prog = parse('say "hi"\nlet n be 2\nsay "{n}"\n')
    assert [f.name for f in prog.funcs] == ["main"]
    main = prog.funcs[0]
    assert main.implicit_main is True
    assert main.params == [] and main.ret is None
    assert len(main.body) == 3


def test_explicit_main_is_not_marked_implicit():
    prog = parse('to main:\n    say "hi"\n')
    assert prog.funcs[0].implicit_main is False


def test_top_level_statements_coexist_with_functions():
    prog = parse('to twice with n as number giving number:\n'
                 '    give back n times 2\n'
                 'say (twice with 3)\n')
    assert sorted(f.name for f in prog.funcs) == ["main", "twice"]


def test_program_inputs_parse_as_expressions():
    prog = parse('to main:\n    say the arguments\n    say the input\n')
    body = prog.funcs[0].body
    assert isinstance(body[0].value, A.TheArguments)
    assert isinstance(body[1].value, A.TheInput)


def test_maybe_item_parses_as_a_safe_item_access():
    prog = parse('to main:\n    say maybe item 1 of xs\n')
    expr = prog.funcs[0].body[0].value
    assert isinstance(expr, A.ItemOf)
    assert expr.safe is True
    plain = parse('to main:\n    say item 1 of xs\n').funcs[0].body[0].value
    assert plain.safe is False


def test_sorted_by_field_expression_parse():
    prog = parse('to main:\n    say sorted people by age\n')
    expr = prog.funcs[0].body[0].value
    assert isinstance(expr, A.SortedBy)
    assert expr.field_name == "age"
    assert isinstance(expr.value, A.Var)


def test_sort_by_statement_desugars_to_assignment():
    prog = parse('to main:\n    sort people by age\n')
    stmt = prog.funcs[0].body[0]
    assert isinstance(stmt, A.SetVar)
    assert stmt.target.base == "people"
    assert isinstance(stmt.value, A.SortedBy)
    assert stmt.value.field_name == "age"


def test_plain_sort_statement_is_unchanged():
    prog = parse('to main:\n    sort xs\n')
    stmt = prog.funcs[0].body[0]
    assert isinstance(stmt.value, A.PrefixOp)
    assert stmt.value.op == "sorted"


@pytest.mark.parametrize("name", ["setting", "files", "input", "time", "arguments"])
def test_new_phrase_words_are_still_usable_as_names(name):
    # A one-word operator keyword would break existing programs: the historical
    # 029 corpus binds `let setting be …`. Every phrase added for program input
    # is therefore multi-word (`the setting`, `files in`, `the current time`).
    prog = parse(f'to main:\n    let {name} be 1\n    say {name}\n')
    assert prog.funcs[0].body[0].name == name


def test_by_is_still_usable_as_a_name():
    prog = parse('to main:\n    let by be 5\n    say by\n')
    assert prog.funcs[0].body[0].name == "by"


def test_otherwise_fallback_expression_parse():
    prog = parse('to main:\n    say number from "5" otherwise 0\n')
    expr = prog.funcs[0].body[0].value
    assert isinstance(expr, A.Otherwise)
    assert isinstance(expr.value, A.PrefixOp)
    assert expr.value.op == "number_from"
    assert isinstance(expr.fallback, A.Num)


def test_otherwise_binds_tighter_than_comparison():
    prog = parse('to main:\n    say ask for a number "" otherwise 0 is more than 5\n')
    expr = prog.funcs[0].body[0].value
    assert isinstance(expr, A.Compare)
    assert isinstance(expr.left, A.Otherwise)


def test_otherwise_keeps_if_otherwise_block():
    prog = parse('to main:\n    if yes:\n        say "a"\n    otherwise:\n        say "b"\n')
    stmt = prog.funcs[0].body[0]
    assert isinstance(stmt, A.If)
    assert stmt.otherwise is not None


def test_text_position_expression_parse():
    prog = parse('to main:\n    say position of "b" in "abc"\n')
    expr = prog.funcs[0].body[0].value
    assert isinstance(expr, A.PositionOf)
    assert isinstance(expr.needle, A.Str)
    assert isinstance(expr.value, A.Str)


def test_modulo_is_a_contextual_multiplicative_operator():
    prog = parse(
        "to main:\n"
        "    let modulo be 9\n"
        "    say modulo\n"
        "    say 2 plus 10 modulo 4 times 3\n"
    )
    assert isinstance(prog.funcs[0].body[1].value, A.Var)
    expr = prog.funcs[0].body[2].value
    assert isinstance(expr, A.BinOp)
    assert expr.op == "+"
    assert isinstance(expr.right, A.BinOp)
    assert expr.right.op == "*"
    assert isinstance(expr.right.left, A.BinOp)
    assert expr.right.left.op == "%"


def test_position_is_contextual_in_loop_and_item_index():
    prog = parse(
        "to main:\n"
        "    let values be a list of 10, 20\n"
        "    for each position from 1 to length of values:\n"
        "        say item position of values\n"
    )
    loop = prog.funcs[0].body[1]
    assert isinstance(loop, A.ForRange)
    assert loop.var == "position"
    item = loop.body[0].value
    assert isinstance(item, A.ItemOf)
    assert isinstance(item.index, A.Var)
    assert item.index.name == "position"

    mutation_prog = parse(
        "to main:\n"
        "    let values be a list of 10, 20\n"
        "    let position be 2\n"
        "    set item position of values to 30\n"
        "    remove item position of values\n"
    )
    assert isinstance(mutation_prog.funcs[0].body[2], A.SetItem)
    assert isinstance(mutation_prog.funcs[0].body[3], A.RemoveItem)


def test_number_is_contextual_in_value_names_and_stays_a_type():
    prog = parse(
        "a reading has number as number\n"
        "to number with value as number giving number:\n"
        "    give back value\n"
        "to double with number as number giving number:\n"
        "    give back number times 2\n"
        "to main:\n"
        "    for each number from 1 to 2:\n"
        "        say number\n"
    )
    assert prog.records[0].fields[0][0] == "number"
    assert isinstance(prog.records[0].fields[0][1], A.TNum)
    assert prog.funcs[0].name == "number"
    assert prog.funcs[1].params[0].name == "number"
    assert isinstance(prog.funcs[1].params[0].type, A.TNum)
    assert prog.funcs[2].body[0].var == "number"


def test_parenthesized_position_search_remains_a_valid_item_index():
    prog = parse(
        'to main:\n'
        '    let positions be a list of 7, 8\n'
        '    say item (position of "b" in "abc") of positions\n'
    )
    item = prog.funcs[0].body[1].value
    assert isinstance(item, A.ItemOf)
    assert isinstance(item.index, A.PositionOf)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "to add compact run:\n    say 1\n",
            "Function names are one identifier",
        ),
        (
            "to valid with line as text giving yesno:\n    give back yes\n"
            "to main:\n    if valid with \"x\":\n        say \"yes\"\n",
            "call used as a condition needs parentheses",
        ),
        (
            "to record with changing values as list of number:\n    add 1 to values\n"
            "to main:\n    let values be an empty list of number\n"
            "    record with changing values\n",
            "plain variable at the call site",
        ),
        (
            "to main:\n    if 1 is equal to 1:\n        say 1\n",
            "Equality is written `is`",
        ),
        (
            "to main:\n    let quantity_text be \"2\"\n"
            "    let value be number from text quantity_text\n",
            "`number from quantity_text`",
        ),
        (
            "to double with value as number returns number:\n"
            "    give back value times 2\n"
            "to main:\n    say 1\n",
            "`giving TYPE`",
        ),
        (
            "to double giving number:\n    give 2\n"
            "to main:\n    say 1\n",
            "`give back value`",
        ),
    ],
)
def test_common_agent_parse_mistakes_have_exact_repair_hints(source, expected):
    with pytest.raises(ParleyError) as exc:
        parse(source)
    assert expected in (exc.value.diagnostics[0].hint or "")


def test_agent_natural_aliases_parse_to_canonical_nodes():
    prog = parse(
        "to helper giving number:\n"
        "    return 2\n"
        "to main:\n"
        "    set answer to number from \"2\"\n"
        "    if answer has a value:\n"
        "        print value of answer\n"
        "    if answer has no value:\n"
        "        stop\n"
        "    set names to a list of \"b\", \"a\"\n"
        "    sort names\n"
        "    repeat 3 - 1 times:\n"
        "        print item 1 of names\n"
    )

    helper, main = prog.funcs
    assert isinstance(helper.body[0], A.Give)
    assert isinstance(main.body[0], A.SetVar)
    assert isinstance(main.body[1], A.If)
    assert isinstance(main.body[1].arms[0][0], A.Compare)
    assert isinstance(main.body[4], A.SetVar)
    assert isinstance(main.body[4].value, A.PrefixOp)
    assert isinstance(main.body[5], A.Repeat)
    assert isinstance(main.body[5].count, A.BinOp)


def test_natural_and_separates_function_parameters():
    prog = parse(
        "to append_pair with low as number and high as number and parts as list of text:\n"
        "    add \"{low}-{high}\" to parts\n"
        "to main:\n"
        "    say \"ready\"\n"
    )
    params = prog.funcs[0].params
    assert [param.name for param in params] == ["low", "high", "parts"]
    assert all(param.natural_separator for param in params)


def test_text_count_expression_parse():
    prog = parse('to main:\n    say count of "a" in "banana"\n')
    expr = prog.funcs[0].body[0].value
    assert isinstance(expr, A.CountOf)
    assert isinstance(expr.needle, A.Str)
    assert isinstance(expr.value, A.Str)


def test_text_item_expression_parse():
    prog = parse('to main:\n    say item 2 of "éc"\n')
    expr = prog.funcs[0].body[0].value
    assert isinstance(expr, A.ItemOf)
    assert isinstance(expr.index, A.Num)
    assert isinstance(expr.container, A.Str)


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


def test_included_file_may_not_hold_top_level_statements(tmp_path):
    (tmp_path / "util.par").write_text(
        'say "loose"\nto double with n as number giving number:\n'
        '    give back n times 2\n')
    (tmp_path / "main.par").write_text(
        'include "util.par"\n\nsay (double with 21)\n')
    with pytest.raises(ParleyError) as ei:
        parse_program(tmp_path / "main.par")
    diag = ei.value.diagnostics[0]
    assert diag.code == "P213"
    assert diag.file.endswith("util.par")


def test_entrypoint_top_level_statements_survive_includes(tmp_path):
    (tmp_path / "util.par").write_text(
        'to double with n as number giving number:\n    give back n times 2\n')
    (tmp_path / "main.par").write_text(
        'include "util.par"\n\nsay (double with 21)\n')
    prog, _ = parse_program(tmp_path / "main.par")
    assert sorted(f.name for f in prog.funcs) == ["double", "main"]
    assert next(f for f in prog.funcs if f.name == "main").implicit_main


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
