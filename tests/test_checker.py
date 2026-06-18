"""Checker tests: every class of mistake gets the right P-code and a useful hint."""

import pytest

from conftest import check_text, diag_codes

MAIN = "to main:\n{body}\n"


def in_main(*lines: str) -> str:
    return MAIN.format(body="\n".join("    " + l for l in lines))


CASES = [
    # (name, source, expected code, fragment expected in message+hint)
    ("unknown_var", in_main("let count be 1", "say cuont"), "P201", 'Did you mean "count"'),
    ("unknown_function", in_main("gret with 1"), "P202", "gret"),
    ("did_you_mean_function",
     "to greet with n as number:\n    say n\nto main:\n    gret with 1\n",
     "P202", 'Did you mean "greet"'),
    ("wrong_arity",
     "to greet with n as number:\n    say n\nto main:\n    greet with 1, 2\n",
     "P203", "takes 1 argument"),
    ("unknown_field",
     "a p has x as number\nto main:\n    let v be a p with x 1\n    say v's y\n",
     "P204", "not a field"),
    ("unknown_type",
     "to f with q as persn:\n    say 1\nto main:\n    say 2\n",
     "P205", "no type called"),
    ("missing_field",
     "a p has x as number, y as number\nto main:\n    let v be a p with x 1\n",
     "P206", "missing: y"),
    ("duplicate_function",
     "to f:\n    say 1\nto f:\n    say 2\nto main:\n    say 3\n",
     "P207", "two definitions"),
    ("duplicate_variant",
     "a m is one of x, y\na k is one of y, z\nto main:\n    say 1\n",
     "P207", "Variant names are global"),
    ("when_not_exhaustive",
     "a m is one of x, y, z\nto main:\n    let v be x\n    when v:\n        is x:\n            say 1\n",
     "P208", "does not cover"),
    ("when_number_needs_otherwise",
     in_main("when 5:", "    is 5:", "        say 1"), "P208", "otherwise"),
    ("reserved_name", in_main("let item be 5"), "P209", "vocabulary"),
    ("redeclared", in_main("let x be 1", "let x be 2"), "P209", "already exists"),
    ("no_main", "to helper:\n    say 1\n", "P210", "to main"),
    ("main_with_params", "to main with n as number:\n    say n\n", "P210", "no parameters"),
    ("set_unknown", in_main("set y to 1"), "P211", "no variable"),
    ("set_wrong_type", in_main('let x be 1', 'set x to "hi"'), "P301", "needs number"),
    ("list_mix", in_main('let l be a list of 1, "two"'), "P301", "mixes"),
    ("plus_text_number", in_main('say 1 plus "a"'), "P302", "interpolation"),
    ("if_not_bool", in_main("if 5:", "    say 1"), "P303", "yes or no"),
    ("fail_needs_text", in_main("fail 5"), "P301", "needs text"),
    ("missing_give_back",
     "to f giving number:\n    if yes:\n        give back 1\nto main:\n    say (f)\n",
     "P304", "not every path"),
    ("give_back_wrong_type",
     'to f giving number:\n    give back "hi"\nto main:\n    say (f)\n',
     "P301", "needs number"),
    ("changing_needs_var",
     "to bump with changing n as number:\n    set n to n plus 1\nto main:\n    bump with 5\n",
     "P305", "must be a variable"),
    ("item_of_number", in_main("let x be 5", "say item 1 of x"), "P306", "lists and maps"),
    ("foreach_over_map",
     in_main("let m be a map from text to number", "for each k in m:", "    say k"),
     "P306", "keys of"),
    ("value_of_plain", in_main("let x be 5", "say value of x"), "P307", "maybe"),
    ("bare_nothing", in_main("let x be nothing"), "P308", "type"),
    ("map_decimal_keys", in_main("let m be a map from decimal to number"), "P309", "number or text"),
    ("give_back_in_attempt",
     "to f giving number:\n    attempt:\n        give back 1\n    if it failed:\n        say 1\n    give back 2\nto main:\n    say (f)\n",
     "P310", "attempt"),
    ("stop_outside_loop", in_main("stop"), "P311", "loop"),
    ("compare_maybe_with_plain",
     in_main('let m be number from "5"', "if m is 5:", "    say 1"),
     "P301", "maybe"),
]


@pytest.mark.parametrize("name,src,code,fragment", CASES, ids=[c[0] for c in CASES])
def test_checker_case(name, src, code, fragment):
    diags = check_text(src)
    codes = [d.code for d in diags]
    assert code in codes, f"{name}: expected {code}, got {[(d.code, d.message) for d in diags]}"
    blob = " ".join((d.message + " " + (d.hint or "")) for d in diags if d.code == code)
    assert fragment.lower() in blob.lower(), f"{name}: fragment {fragment!r} not in {blob!r}"


def test_clean_program_no_diags():
    src = (
        "a p has x as number\n"
        "to double with n as number giving number:\n"
        "    give back n times 2\n"
        "to crash giving number:\n"
        "    fail \"not a number\"\n"
        "to main:\n"
        "    let v be a p with x 3\n"
        "    say (double with v's x)\n"
    )
    assert check_text(src) == []


def test_some_constructs_maybe_values_cleanly():
    src = (
        "to find giving maybe number:\n"
        "    give back some 5\n"
        "to main:\n"
        "    let message be some \"ready\"\n"
        "    if message is not nothing:\n"
        "        say value of message\n"
        "    say (find)\n"
    )
    assert check_text(src) == []


def test_zero_arg_function_used_as_value():
    src = (
        "to roll giving number:\n"
        "    give back a random number from 1 to 6\n"
        "to main:\n"
        "    let d be roll\n"
        "    say d plus (roll)\n"
    )
    assert check_text(src) == []


def test_block_scoping_let_dies_with_block():
    src = in_main("if yes:", "    let x be 1", "say x")
    assert "P201" in diag_codes(src)


def test_loop_var_scoped():
    src = in_main("for each i from 1 to 3:", "    say i", "say i")
    assert "P201" in diag_codes(src)


# ------------------------------------------------------------------ v0.2: when patterns + function values

RANGE_AND_FUNC_CASES = [
    ("range_over_text",
     in_main('when "hi":', '    is 1 to 5:', "        say 1", "    otherwise:", "        say 2"),
     "P312", "numeric"),
    ("range_empty",
     in_main("when 5:", "    is 9 to 2:", "        say 1", "    otherwise:", "        say 2"),
     "P312", "empty"),
    ("range_dec_end_on_number",
     in_main("when 5:", "    is 1 to 2.5:", "        say 1", "    otherwise:", "        say 2"),
     "P312", "whole numbers"),
    ("the_function_unknown", in_main("let f be the function nope"), "P202", "no function"),
    ("the_function_on_changing",
     "to bump with changing n as number:\n    set n to n plus 1\n"
     "to main:\n    let f be the function bump\n",
     "P313", "changing parameter"),
    ("the_function_on_main", in_main("let f be the function main"), "P313", "main"),
    ("say_function_value",
     "to double with x as number giving number:\n    give back x times 2\n"
     "to main:\n    let f be the function double\n    say f\n",
     "P301", "function value"),
    ("fn_value_wrong_arity",
     "to double with x as number giving number:\n    give back x times 2\n"
     "to main:\n    let f be the function double\n    say (f with 1, 2)\n",
     "P203", "takes 1 argument"),
    ("fn_value_wrong_arg_type",
     "to double with x as number giving number:\n    give back x times 2\n"
     "to main:\n    let f be the function double\n    say (f with \"hi\")\n",
     "P301", "needs number"),
    ("function_value_compare",
     "to double with x as number giving number:\n    give back x times 2\n"
     "to main:\n    let f be the function double\n    let g be the function double\n"
     "    if f is g:\n        say 1\n",
     "P301", "cannot be compared"),
    ("closure_changes_capture",
     "to main:\n    let offset be 7\n"
     "    let bump be a function giving number:\n"
     "        set offset to offset plus 1\n"
     "        give back offset\n",
     "P314", "cannot change"),
]


@pytest.mark.parametrize("name,src,code,fragment", RANGE_AND_FUNC_CASES,
                         ids=[c[0] for c in RANGE_AND_FUNC_CASES])
def test_range_and_func_diagnostics(name, src, code, fragment):
    diags = check_text(src)
    assert any(d.code == code for d in diags), \
        f"expected {code}, got {[(d.code, d.message) for d in diags]}"
    blob = " ".join((d.message + " " + (d.hint or "")) for d in diags if d.code == code)
    assert fragment in blob


def test_function_value_round_trip_is_clean():
    src = (
        "to double with x as number giving number:\n"
        "    give back x times 2\n"
        "to apply_twice with f as (function taking number giving number), x as number giving number:\n"
        "    give back (f with (f with x))\n"
        "to main:\n"
        "    let d be the function double\n"
        "    say (apply_twice with d, 5)\n"
        "    let fs be a list of the function double\n"
        "    for each f in fs:\n"
        "        say (f with 1)\n"
    )
    assert check_text(src) == []


def test_closure_capture_round_trip_is_clean():
    src = (
        "to apply with f as (function taking number giving number), x as number giving number:\n"
        "    give back (f with x)\n"
        "to main:\n"
        "    let offset be 7\n"
        "    let add_offset be a function taking x as number giving number:\n"
        "        give back x plus offset\n"
        "    say (apply with add_offset, 5)\n"
    )
    assert check_text(src) == []


def test_when_multi_value_covers_enum():
    src = (
        "a mood is one of happy, grumpy, sleepy\n"
        "to main:\n"
        "    let m be happy\n"
        "    when m:\n"
        "        is happy, sleepy:\n"
        "            say 1\n"
        "        is grumpy:\n"
        "            say 2\n"
    )
    assert check_text(src) == []
