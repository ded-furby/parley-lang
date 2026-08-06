"""Checker tests: every class of mistake gets the right P-code and a useful hint."""

import pytest

from conftest import check_text, diag_codes
from parley.checker import check_program
from parley.parser import parse

MAIN = "to main:\n{body}\n"


def in_main(*lines: str) -> str:
    return MAIN.format(body="\n".join("    " + l for l in lines))


CASES = [
    # (name, source, expected code, fragment expected in message+hint)
    ("unknown_var", in_main("let count be 1", "say cuont"), "P201", 'Did you mean "count"'),
    ("python_true_literal", in_main("if true:", "    say 1"), "P201", "uses `yes`"),
    ("python_false_literal", in_main("if false:", "    say 1"), "P201", "uses `no`"),
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
    ("set_wrong_type", in_main('let x be 1', 'set x to "hi"'), "P301", "needs number"),
    ("list_mix", in_main('let l be a list of 1, "two"'), "P301", "mixes"),
    ("if_not_bool", in_main("if 5:", "    say 1"), "P303", "yes or no"),
    ("assert_needs_bool", in_main("assert 5"), "P303", "yes or no"),
    ("assert_message_needs_text", in_main('assert yes, 5'), "P301", "needs text"),
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
    ("values_of_number", in_main("let x be 5", "say values of x"), "P306", "values of"),
    ("foreach_over_map",
     in_main("let m be a map from text to number", "for each k in m:", "    say k"),
     "P306", "keys of"),
    ("value_of_plain", in_main("let x be 5", "say value of x"), "P307", "maybe"),
    ("bare_nothing", in_main("let x be nothing"), "P308", "type"),
    ("map_decimal_keys", in_main("let m be a map from decimal to number"), "P309", "number or text"),
    ("give_back_in_attempt",
     "to f giving number:\n    attempt:\n        give back 1\n    if it failed:\n        say 1\n    give back 2\nto main:\n    say (f)\n",
     "P310", "attempt"),
    ("compare_maybe_with_plain",
     in_main('let m be number from "5"', "if m is 5:", "    say 1"),
     "P301", "maybe"),
    ("replace_target_needs_text", in_main('say 5 replacing "x" with "y"'), "P301", "needs text"),
    ("replace_old_needs_text", in_main('say "abc" replacing 1 with "x"'), "P301", "needs text"),
    ("replace_new_needs_text", in_main('say "abc" replacing "a" with 1'), "P301", "needs text"),
    ("position_needle_needs_text", in_main('say position of 1 in "abc"'), "P301", "needs text"),
    ("position_text_needs_text", in_main('say position of "a" in 5'), "P301", "needs text"),
    ("count_needle_needs_text", in_main('say count of 1 in "abc"'), "P301", "needs text"),
    ("count_text_needs_text", in_main('say count of "a" in 5'), "P301", "needs text"),
    ("top_level_and_explicit_main", 'say "a"\nto main:\n    say "b"\n',
     "P212", "already has a `main`"),
    ("maybe_item_on_a_number",
     in_main("let n be 5", "say maybe item 1 of n"), "P306", "maybe item"),
    ("sort_by_on_scalar_list", in_main("let xs be a list of 1, 2", "sort xs by age"),
     "P316", "list of records"),
    ("sort_by_unordered_field",
     'a p has tags as list of text\nto main:\n    let ps be an empty list of p\n    sort ps by tags\n',
     "P316", "ordered field"),
    ("sort_by_unknown_field",
     'a p has n as text\nto main:\n    let ps be an empty list of p\n    sort ps by nam\n',
     "P204", "not a field"),
    ("otherwise_on_plain_value", in_main("say 5 otherwise 1"), "P315", "already number"),
    ("otherwise_fallback_type",
     in_main('let n be number from "5"', 'say n otherwise "zero"'), "P301", "fallback"),
    ("otherwise_cannot_narrow_decimal",
     in_main("let d be some 3", "say d otherwise 1.5"), "P301", "fallback"),
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
        "    assert v's x is 3, \"x should be three\"\n"
        "    say (double with v's x)\n"
    )
    assert check_text(src) == []


def test_position_is_a_contextual_identifier_without_shadowing_search():
    mutation_src = in_main(
        "let values be a list of 10, 20",
        "let position be 2",
        "set item position of values to 30",
        "remove item position of values",
        'say position of "b" in "abc"',
    )
    loop_src = in_main(
        "let values be a list of 10, 20",
        "for each position from 1 to length of values:",
        "    say item position of values",
        'say position of "b" in "abc"',
    )
    assert check_text(mutation_src) == []
    assert check_text(loop_src) == []


def test_number_is_a_contextual_value_identifier_but_not_a_type_name():
    value_src = (
        "a reading has number as number\n"
        "to double with number as number giving number:\n"
        "    give back number times 2\n"
        "to local_value giving number:\n"
        "    let number be 7\n"
        "    give back number\n"
        "to main:\n"
        "    let item_value be a reading with number 3\n"
        "    say item_value's number\n"
        "    say (double with 4)\n"
        "    for each number from 1 to 2:\n"
        "        say number\n"
    )
    function_src = (
        "to number with value as number giving number:\n"
        "    give back value\n"
        "to main:\n"
        "    say (number with 9)\n"
    )
    assert check_text(value_src) == []
    assert check_text(function_src) == []

    record_src = "a number has value as number\nto main:\n    say 1\n"
    kind_src = "a number is one of present\nto main:\n    say 1\n"
    variant_src = "a state is one of number\nto main:\n    say 1\n"
    assert "P209" in diag_codes(record_src)
    assert "P209" in diag_codes(kind_src)
    assert "P209" in diag_codes(variant_src)


def test_modulo_reuses_whole_number_remainder_types_contextually():
    assert check_text(in_main("let modulo be 5", "say modulo", "say 10 modulo 3")) == []
    diags = check_text(in_main("say 10.5 modulo 3"))
    assert [diag.code for diag in diags] == ["P302"]
    assert "whole numbers" in (diags[0].message + " " + (diags[0].hint or ""))


def test_compact_range_agent_idioms_are_clean():
    src = (
        "to record_range with low as number, high as number, changing pieces as list of text:\n"
        "    add \"{low}-{high}\" to pieces\n"
        "to main:\n"
        "    let values be a list of 1, 2, 3, 5\n"
        "    let pieces be an empty list of text\n"
        "    let cursor be 1\n"
        "    let count be length of values\n"
        "    while cursor is at most count:\n"
        "        let run_end be cursor\n"
        "        let extending be yes\n"
        "        while extending and run_end is less than count:\n"
        "            let current_value be item run_end of values\n"
        "            let next_index be run_end plus 1\n"
        "            let next_value be item next_index of values\n"
        "            if next_value is current_value plus 1:\n"
        "                set run_end to next_index\n"
        "            otherwise:\n"
        "                set extending to no\n"
        "        let low be item cursor of values\n"
        "        let high be item run_end of values\n"
        "        record_range with low, high, pieces\n"
        "        set cursor to run_end plus 1\n"
    )
    assert check_text(src) == []


def test_natural_helper_call_infers_mutated_list_parameter():
    src = (
        "to append_pair with low as number and high as number and parts as list of text:\n"
        "    add \"{low}-{high}\" to parts\n"
        "to main:\n"
        "    let parts be an empty list of text\n"
        "    append_pair with 1 and 3 and parts\n"
        "    say parts joined with \",\"\n"
    )
    program = parse(src)
    assert check_program(program) == []
    assert program.funcs[0].params[2].changing


def test_map_values_typecheck_cleanly():
    src = in_main(
        "let scores be a map from text to number",
        'set item "ada" of scores to 36',
        'set item "grace" of scores to 42',
        "let vals be values of scores",
        "say sum of vals",
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


def test_text_replacement_expression_is_clean():
    assert check_text(in_main('say "one fish" replacing "one" with "two"')) == []


def test_text_position_expression_is_maybe_number():
    assert check_text(in_main('let found be position of "fish" in "one fish"', "say found")) == []


def test_text_count_expression_is_number():
    assert check_text(in_main('let n be count of "a" in "banana"', "say n plus 1")) == []


def test_text_item_expression_is_clean():
    assert check_text(in_main('let ch be item 2 of "éc"', "say ch")) == []


def test_block_scoping_let_dies_with_block():
    src = in_main("if yes:", "    let x be 1", "say x")
    assert "P201" in diag_codes(src)


def test_loop_var_scoped():
    src = in_main("for each i from 1 to 3:", "    say i", "say i")
    assert "P201" in diag_codes(src)


def test_loop_variables_can_be_changed_inside_their_iteration():
    src = in_main(
        "for each i from 1 to 2:",
        "    set i to i plus 10",
        "    say i",
        "let values be a list of 3, 4",
        "for each value in values:",
        "    set value to value times 2",
        "    say value",
    )
    assert check_text(src) == []


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


def test_set_can_introduce_a_variable_and_stop_can_leave_main():
    src = in_main(
        "set count to 1",
        "set count to count plus 1",
        "if count is 2:",
        "    stop",
        "print count",
    )

    assert check_text(src) == []


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
