"""End-to-end tests: every example and every feature compiled by rustc and run
as a real native binary, with stdout asserted."""

import json
import shutil

import pytest

from conftest import EXAMPLES, run_cli, run_program

pytestmark = pytest.mark.skipif(
    shutil.which("cargo") is None, reason="cargo not installed")


# ------------------------------------------------------------------ examples

def test_hello(workdir):
    proc = run_cli(["run", str(EXAMPLES / "hello.par")], cwd=workdir)
    assert proc.returncode == 0
    assert proc.stdout == "Hello, world!\nTwo plus two is 4.\n"


def test_fizzbuzz(workdir):
    proc = run_cli(["run", str(EXAMPLES / "fizzbuzz.par")], cwd=workdir)
    lines = proc.stdout.splitlines()
    assert lines[:5] == ["1", "2", "Fizz", "4", "Buzz"]
    assert lines[14] == "FizzBuzz"
    assert len(lines) == 20


def test_records(workdir):
    proc = run_cli(["run", str(EXAMPLES / "records.par")], cwd=workdir)
    assert proc.stdout == (
        "area: 12\n"
        "origin moved to x 10\n"
        "frame's corner is still at x 0\n")


def test_lists_and_maps(workdir):
    proc = run_cli(["run", str(EXAMPLES / "lists_and_maps.par")], cwd=workdir)
    assert proc.stdout == (
        "I have 5 primes; their sum is 28\n"
        "item 3 is 5\n"
        "7 is in the list\n"
        "1 < 2 < 8 < 9\n"
        "ada is 36\n"
        "people: ada, alan\n")


def test_enums_match(workdir):
    proc = run_cli(["run", str(EXAMPLES / "enums_match.par")], cwd=workdir)
    assert proc.stdout == (
        "the cat is grumpy\n"
        "approach with snacks\n"
        "feed it first\n")


def test_guessing_game(workdir):
    stdin = "".join(f"{n}\n" for n in range(1, 11)) + "x\n"
    proc = run_cli(["run", str(EXAMPLES / "guessing_game.par")],
                   cwd=workdir, stdin=stdin)
    assert proc.returncode == 0
    assert "You got it in" in proc.stdout


def test_calculator_adds(workdir):
    proc = run_cli(["run", str(EXAMPLES / "calculator.par")],
                   cwd=workdir, stdin="3.5\n4\n+\n")
    assert proc.stdout.endswith("7.5\n")


def test_calculator_divide_by_zero_is_caught(workdir):
    proc = run_cli(["run", str(EXAMPLES / "calculator.par")],
                   cwd=workdir, stdin="1\n0\n/\n")
    assert proc.returncode == 0
    assert "Cannot divide by zero." in proc.stdout


def test_file_stats(workdir):
    proc = run_cli(["run", str(EXAMPLES / "file_stats.par")], cwd=workdir)
    assert proc.stdout == (
        "the file has 3 lines\n"
        "found it: the lazy dog\n")
    assert (workdir / "parley_demo.txt").exists()


def test_todo(workdir):
    stdin = "add buy milk\nadd walk dog\nlist\ndone 1\nlist\ndone 9\nquit\n"
    proc = run_cli(["run", str(EXAMPLES / "todo.par")], cwd=workdir, stdin=stdin)
    out = proc.stdout
    assert "1. buy milk" in out and "2. walk dog" in out
    assert "done!" in out
    assert "Cannot remove item 9 — the list has 1 item(s)." in out
    assert out.rstrip().endswith("bye")


# ------------------------------------------------------------------ features

def test_text_toolbox(workdir):
    src = '''to main:
    let s be "  The Quick Fox  "
    let t be trimmed s
    say lowercase of t
    say uppercase of t
    say length of t
    say reversed "stressed"
    say t replacing "Quick" with "Quiet"
    say position of "Quick" in t
    say position of "Cat" in t
    say position of "c" in "écart"
    say count of "o" in t
    say count of "aa" in "aaaa"
    say count of "" in "éc"
    say item 1 of t
    say item 2 of "éc"
    if t starts with "The" and t ends with "Fox":
        say "framed"
    say "quick" contains "ick"
'''
    proc = run_program(workdir, "text_toolbox", src)
    assert proc.stdout == (
        "the quick fox\nTHE QUICK FOX\n13\ndesserts\nThe Quiet Fox\n5\nnothing\n2\n1\n2\n3\nT\nc\nframed\nyes\n")


def test_math_toolbox(workdir):
    src = '''to main:
    say 2 to the power of 10
    say absolute of -7
    say floor of 3.9
    say ceiling of 3.1
    say rounded 2.5
    say square root of 144
    say 7 % 3
    say -4 minus -6
'''
    proc = run_program(workdir, "math_toolbox", src)
    assert proc.stdout == "1024\n7\n3\n4\n3\n12\n1\n2\n"


def test_maybe_flow(workdir):
    src = '''to main:
    let good be number from "42"
    let bad be number from "forty-two"
    say good
    say bad
    if bad is nothing:
        say "bad is nothing"
    if good is not nothing:
        say value of good plus 1
'''
    proc = run_program(workdir, "maybe_flow", src)
    assert proc.stdout == "42\nnothing\nbad is nothing\n43\n"


def test_some_constructs_maybe_values(workdir):
    src = '''to find with needle as number giving maybe number:
    if needle is 5:
        give back some needle
    give back nothing

to main:
    let message be some "ready"
    if message is not nothing:
        say value of message
    say (find with 5)
    say (find with 9)
'''
    proc = run_program(workdir, "some_maybe", src)
    assert proc.stdout == "ready\n5\nnothing\n"


def test_map_operations(workdir):
    src = '''to main:
    let m be a map from number to text
    set item 1 of m to "one"
    set item 2 of m to "two"
    let names be values of m
    say names joined with "|"
    say length of m
    remove item 1 of m
    say length of m
    say m contains 2
    say m contains 1
    let scores be a map from text to number
    set item "grace" of scores to 42
    set item "ada" of scores to 36
    let values be values of scores
    say sum of values
'''
    proc = run_program(workdir, "map_ops", src)
    assert proc.stdout == "one|two\n2\n1\nyes\nno\n78\n"


def test_uncaught_error_is_english_and_exit_1(workdir):
    src = '''to main:
    let xs be a list of 1
    say item 5 of xs
'''
    proc = run_program(workdir, "boom", src, expect_ok=False)
    assert proc.returncode == 1
    assert "The program stopped: There is no item 5 — the list has 1 item(s)." in proc.stderr


def test_text_item_out_of_range_is_english(workdir):
    src = '''to main:
    say item 3 of "éc"
'''
    proc = run_program(workdir, "text_boom", src, expect_ok=False)
    assert proc.returncode == 1
    assert "The program stopped: There is no character 3 — the text has 2 character(s)." in proc.stderr


def test_attempt_catches_and_continues(workdir):
    src = '''to main:
    let xs be a list of 1
    attempt:
        say item 5 of xs
    if it failed:
        say "caught: {the error}"
    say "still alive"
'''
    proc = run_program(workdir, "catcher", src)
    assert proc.stdout == (
        "caught: There is no item 5 — the list has 1 item(s).\n"
        "still alive\n")


def test_fail_statement_can_be_caught(workdir):
    src = '''to main:
    attempt:
        fail "custom failure"
    if it failed:
        say "caught: {the error}"
    say "still alive"
'''
    proc = run_program(workdir, "fail_caught", src)
    assert proc.stdout == "caught: custom failure\nstill alive\n"


def test_uncaught_fail_statement_stops_in_english(workdir):
    proc = run_program(
        workdir,
        "fail_uncaught",
        'to main:\n    fail "custom failure"\n',
        expect_ok=False,
    )

    assert proc.returncode == 1
    assert "The program stopped: custom failure" in proc.stderr


def test_assert_statement_passes_when_condition_is_yes(workdir):
    src = '''to main:
    let count be 3
    assert count is 3, "count changed"
    say "ok"
'''
    proc = run_program(workdir, "assert_passes", src)
    assert proc.stdout == "ok\n"


def test_assert_statement_can_be_caught(workdir):
    src = '''to main:
    attempt:
        assert no, "custom assertion"
    if it failed:
        say "caught: {the error}"
'''
    proc = run_program(workdir, "assert_caught", src)
    assert proc.stdout == "caught: custom assertion\n"


def test_value_semantics_copy_on_assign(workdir):
    src = '''to main:
    let first_list be a list of 1, 2
    let second_list be first_list
    add 3 to second_list
    say length of first_list
    say length of second_list
'''
    proc = run_program(workdir, "valuesem", src)
    assert proc.stdout == "2\n3\n"


def test_recursion(workdir):
    src = '''to fact with n as number giving number:
    if n is at most 1:
        give back 1
    give back n times (fact with n minus 1)

to main:
    say (fact with 10)
'''
    proc = run_program(workdir, "recursion", src)
    assert proc.stdout == "3628800\n"


def test_includes_run(workdir):
    (workdir / "mathlib.par").write_text(
        "to triple with n as number giving number:\n    give back n times 3\n")
    src = 'include "mathlib.par"\n\nto main:\n    say (triple with 14)\n'
    proc = run_program(workdir, "with_include", src)
    assert proc.stdout == "42\n"


def test_include_error_points_at_right_file(workdir):
    (workdir / "buggy.par").write_text(
        "to broken giving number:\n    give back missing_var\n")
    f = workdir / "uses_buggy.par"
    f.write_text('include "buggy.par"\n\nto main:\n    say (broken)\n')
    proc = run_cli(["check", f.name, "--json"], cwd=workdir)
    data = json.loads(proc.stdout)
    assert data["ok"] is False
    d = data["diagnostics"][0]
    assert d["file"].endswith("buggy.par")
    assert d["line"] == 2


def test_bundled_std_packages_run(workdir):
    src = '''include "std/math"
include "std/text"

to main:
    say (clamped with 12, 1, 10)
    say (clamped_decimal with 12.5, 1.5, 10.5)
    say (clamped_decimal with 0.5, 1.5, 10.5)
    say (between_decimal with 2.5, 1.5, 3.5)
    say (between_decimal with 4.5, 1.5, 3.5)
    say (percent_of_decimal with 12.5, 50.0)
    say (factorial with 0)
    say (factorial with 5)
    attempt:
        say (factorial with -1)
    if it failed:
        say "factorial error: {the error}"
    say (greatest_common_divisor with 54, 24)
    say (greatest_common_divisor with -54, 24)
    say (greatest_common_divisor with 0, 0)
    say (least_common_multiple with 6, 8)
    say (least_common_multiple with -6, 8)
    say (least_common_multiple with 0, 8)
    say (combination_count with 5, 2)
    say (combination_count with 5, 8)
    attempt:
        say (combination_count with -1, 2)
    if it failed:
        say "combination error: {the error}"
    say (permutation_count with 5, 2)
    say (permutation_count with 5, 0)
    say (permutation_count with 5, 8)
    attempt:
        say (permutation_count with 5, -1)
    if it failed:
        say "permutation error: {the error}"
    say (integer_square_root with 0)
    say (integer_square_root with 15)
    say (integer_square_root with 16)
    attempt:
        say (integer_square_root with -1)
    if it failed:
        say "integer square root error: {the error}"
    say (is_perfect_square with 16)
    say (is_perfect_square with 18)
    say (is_perfect_square with -4)
    say (is_blank with "   ")
    say (repeated_text with "ha", 3)
    say (line_count with "")
    say (line_count with "one\\ntwo\\nthree")
    say (nonempty_line_count with "one\\n\\n  \\ntwo")
    say (word_count with "  one  two three  ")
    let words be (words_of with "  one  two three  ")
    say length of words
    say words joined with "|"
    let no_words be (words_of with "   ")
    say length of no_words
    say (word_count with "one\\ttwo\\n three\\r\\nfour")
    let whitespace_words be (words_of with "one\\ttwo\\n three\\r\\nfour")
    say length of whitespace_words
    say whitespace_words joined with "|"
    let no_whitespace_words be (words_of with "\\t\\n\\r ")
    say length of no_whitespace_words
    let lines be (nonempty_lines with " one \\n\\n  two\\n  ")
    say length of lines
    say lines joined with "|"
    let raw_lines be (lines_of with "one\\n\\n  two\\n")
    say length of raw_lines
    say raw_lines joined with "|"
    let universal_lines be (split_lines with "one\\r\\ntwo\\rthree\\n")
    say length of universal_lines
    say universal_lines joined with "|"
    let trailing_universal_lines be (split_lines with "one\\n\\n")
    say length of trailing_universal_lines
    say trailing_universal_lines joined with "|"
    let no_split_lines be (split_lines with "")
    say length of no_split_lines
    let no_raw_lines be (lines_of with "")
    say length of no_raw_lines
    let no_lines be (nonempty_lines with "")
    say length of no_lines
    say (maybe_character with "éc", 1)
    say (maybe_character with "éc", 2)
    say (maybe_character with "éc", 3)
    say (maybe_character with "éc", 0)
    say (text_slice with "crème", 2, 4)
    say (text_slice with "crème", 0, 2)
    say (text_slice with "crème", 4, 99)
    say (text_slice with "crème", 4, 2)
    say (text_slice with "", 1, 1)
    say (reversed_text with "Parley")
    say (reversed_text with "éclair")
    say (reversed_text with "")
    let partitioned be (partition_text with "key=value=tail", "=")
    say length of partitioned
    say partitioned joined with "|"
    let missing_partition be (partition_text with "no match", ":")
    say missing_partition joined with "|"
    let unicode_partition be (partition_text with "éclair", "c")
    say unicode_partition joined with "|"
    let right_partitioned be (rpartition_text with "key=value=tail", "=")
    say right_partitioned joined with "|"
    let missing_right_partition be (rpartition_text with "no match", ":")
    say missing_right_partition joined with "|"
    let unicode_right_partition be (rpartition_text with "éclair", "c")
    say unicode_right_partition joined with "|"
    say (replaced_text with "one fish two fish", "fish", "cat", 1)
    say (replaced_text with "aaaa", "aa", "b", 1)
    say (replaced_text with "aaaa", "aa", "b", 9)
    say (replaced_text with "abc", "", "x", 3)
    say (replaced_text with "abc", "z", "x", 2)
    say (replaced_text with "é-é-é", "é", "e", 2)
    let split_limited be (split_text with "a,b,c,d", ",", 2)
    say length of split_limited
    say split_limited joined with "|"
    let split_all be (split_text with "a,b,c", ",", 9)
    say split_all joined with "|"
    let split_missing be (split_text with "abc", ",", 2)
    say split_missing joined with "|"
    let split_empty_sep be (split_text with "abc", "", 2)
    say split_empty_sep joined with "|"
    let split_zero be (split_text with "a,b", ",", 0)
    say split_zero joined with "|"
    let split_unicode be (split_text with "é::clair::fin", "::", 1)
    say split_unicode joined with "|"
    let right_split_limited be (rsplit_text with "a,b,c,d", ",", 2)
    say length of right_split_limited
    say right_split_limited joined with "|"
    let right_split_all be (rsplit_text with "a,b,c", ",", 9)
    say right_split_all joined with "|"
    let right_split_missing be (rsplit_text with "abc", ",", 2)
    say right_split_missing joined with "|"
    let right_split_empty_sep be (rsplit_text with "abc", "", 2)
    say right_split_empty_sep joined with "|"
    let right_split_zero be (rsplit_text with "a,b", ",", 0)
    say right_split_zero joined with "|"
    let right_split_unicode be (rsplit_text with "é::clair::fin", "::", 1)
    say right_split_unicode joined with "|"
    say (last_position with "=", "key=value=tail")
    say (last_position with "aa", "aaaa")
    say (last_position with ":", "no match")
    say (last_position with "", "abc")
    say (last_position with "c", "éclair")
    say (position_or_zero with "=", "key=value=tail")
    say (position_or_zero with ":", "no match")
    say (position_or_zero with "", "abc")
    say (position_or_zero with "c", "éclair")
    say (last_position_or_zero with "=", "key=value=tail")
    say (last_position_or_zero with ":", "no match")
    say (last_position_or_zero with "", "abc")
    say (last_position_or_zero with "c", "éclair")
    say (without_prefix with "parley-lang", "parley-")
    say (without_prefix with "parley-lang", "rust-")
    say (without_prefix with "parley-lang", "")
    say (without_suffix with "notes.par", ".par")
    say (without_suffix with "notes.par", ".txt")
    say (without_suffix with "notes.par", "")
    say (has_prefix with "parley-lang", "parley-")
    say (has_prefix with "parley-lang", "rust-")
    say (has_prefix with "parley-lang", "")
    say (has_suffix with "notes.par", ".par")
    say (has_suffix with "notes.par", ".txt")
    say (has_suffix with "notes.par", "")
    say (is_whitespace with " ")
    say (is_whitespace with "\\t")
    say (is_whitespace with "x")
    say (is_digit with "12345")
    say (is_digit with "12a")
    say (is_digit with "")
    say (is_alpha with "Parley")
    say (is_alpha with "Parley3")
    say (is_alpha with "")
    say (is_alphanumeric with "Parley3")
    say (is_alphanumeric with "Parley-3")
    say (is_alphanumeric with "")
    say (is_identifier with "parley_3")
    say (is_identifier with "_hidden")
    say (is_identifier with "3parley")
    say (is_identifier with "parley-name")
    say (is_identifier with "")
    say (is_ascii with "Parley 123!")
    say (is_ascii with "\\tline\\n")
    say (is_ascii with "café")
    say (is_ascii with "")
    say (is_printable with "Parley 123!")
    say (is_printable with "with space")
    say (is_printable with "café")
    say (is_printable with "\\tline\\n")
    say (is_printable with "")
    say (is_space with " \\t\\n")
    say (is_space with "   ")
    say (is_space with "")
    say (is_space with " a ")
    say (is_lowercase with "parley")
    say (is_lowercase with "Parley")
    say (is_lowercase with "")
    say (is_uppercase with "PARLEY")
    say (is_uppercase with "PARLEY3")
    say (is_uppercase with "Parley")
    say (swap_case with "Parley 3")
    say (swap_case with "")
    say (title_cased with "parley language")
    say (title_cased with "mIxEd   CASE")
    say (title_cased with "")
    say (is_titlecase with "Parley Language")
    say (is_titlecase with "Parley language")
    say (is_titlecase with "123")
    say (is_titlecase with "")
    say (capitalized with "pARLEY")
    say (capitalized with "mIxEd CASE")
    say (capitalized with "x")
    say (capitalized with "")
    say (left_trimmed with "  left  ")
    say (right_trimmed with "  right  ")
    say (left_trimmed with "\\t\\nboth")
    say (right_trimmed with "both\\t\\n")
    say (left_trimmed with "   ")
    say (right_trimmed with "   ")
    say (padded_left with "7", 3, "0")
    say (padded_right with "go", 5, ".")
    say (padded_left with "wide", 2, "0")
    say (padded_right with "stay", 4, ".")
    say (padded_left with "x", 4, "")
    say (padded_right with "x", 4, "ab")
    say (zero_filled with "42", 5)
    say (zero_filled with "-42", 5)
    say (zero_filled with "+7", 3)
    say (zero_filled with "wide", 2)
    say (zero_filled with "", 3)
    say (tabs_expanded with "a\tb", 4)
    say (tabs_expanded with "ab\tc", 4)
    say (tabs_expanded with "\tstart", 4)
    say (tabs_expanded with "a\tb", 0)
    say (tabs_expanded with "é\tc", 4)
    say (padded_center with "go", 5, ".")
    say (padded_center with "go", 6, ".")
    say (padded_center with "wide", 2, ".")
    say (padded_center with "x", 4, "")
    say (padded_center with "x", 4, "ab")
'''
    proc = run_program(workdir, "bundled_std", src)
    assert proc.stdout == (
        "10\n10.5\n1.5\nyes\nno\n25\n1\n120\nfactorial error: factorial needs a non-negative number\n6\n6\n0\n24\n24\n0\n10\n0\ncombination error: combination_count needs non-negative numbers\n20\n1\n0\npermutation error: permutation_count needs non-negative numbers\n0\n3\n4\ninteger square root error: integer_square_root needs a non-negative number\nyes\nno\nno\nyes\nhahaha\n0\n3\n2\n3\n"
        "3\none|two|three\n0\n4\n4\none|two|three|four\n0\n2\none|two\n4\none||  two|\n3\none|two|three\n2\none|\n0\n0\n0\né\nc\nnothing\nnothing\n"
        "rèm\ncr\nme\n\n\nyelraP\nrialcé\n\n3\nkey|=|value=tail\nno match||\né|c|lair\nkey=value|=|tail\n||no match\né|c|lair\none cat two fish\nbaa\nbb\nabc\nabc\ne-e-é\n3\na|b|c,d\na|b|c\nabc\nabc\na,b\né|clair::fin\n3\na,b|c|d\na|b|c\nabc\nabc\na,b\né::clair|fin\n10\n3\nnothing\n4\n2\n4\n0\n1\n2\n10\n0\n4\n2\nlang\nparley-lang\nparley-lang\nnotes\nnotes.par\nnotes.par\nyes\nno\nyes\nyes\nno\nyes\n"
        "yes\nyes\nno\nyes\nno\nno\nyes\nno\nno\nyes\nno\nno\nyes\nyes\nno\nno\nno\nyes\nyes\nno\nyes\nyes\nyes\nyes\nno\nyes\nyes\nyes\nno\nno\nyes\nno\nno\nyes\nno\nno\npARLEY 3\n\nParley Language\nMixed   Case\n\nyes\nno\nno\nno\nParley\nMixed case\nX\n\nleft  \n  right\nboth\nboth\n\n\n"
        "007\ngo...\nwide\nstay\nx\nxababab\n00042\n-0042\n+07\nwide\n000\na   b\nab  c\n    start\nab\né   c\n.go..\n..go..\nwide\nx\nabxab\n")


def test_bundled_std_math_is_close_helper_runs(workdir):
    src = '''include "std/math"

to main:
    say (is_close with 1.0, 1.001, 0.01, 0.0)
    say (is_close with 1.0, 1.2, 0.01, 0.0)
    say (is_close with 0.0, 0.001, 0.0, 0.01)
    say (is_close with -10.0, -10.4, 0.05, 0.0)
    attempt:
        say (is_close with 1.0, 1.0, -0.1, 0.0)
    if it failed:
        say "close error: {the error}"
'''
    proc = run_program(workdir, "bundled_std_math_is_close", src)
    assert proc.stdout == "yes\nno\nyes\nyes\nclose error: is_close tolerances must be non-negative\n"


def test_bundled_std_math_hypotenuse_helper_runs(workdir):
    src = '''include "std/math"

to main:
    say (hypotenuse with 3.0, 4.0)
    say (hypotenuse with -5.0, 12.0)
    say (is_close with (hypotenuse with 1.5, 2.0), 2.5, 0.0, 0.000001)
'''
    proc = run_program(workdir, "bundled_std_math_hypotenuse", src)
    assert proc.stdout == "5\n13\nyes\n"


def test_bundled_std_list_package_runs(workdir):
    src = '''include "std/list"

to main:
    let nums be a list of 4, 2, 4, 8
    say (first_number with nums)
    say (last_number with nums)
    say (average_number with nums)
    say (product_number with nums)
    say (sum_number with nums)
    say (count_number with nums, 4)
    say (contains_number with nums, 2)
    say (contains_number with nums, 9)
    say (index_number with nums, 8)
    say (index_number with nums, 9)
    let empty_nums be an empty list of number
    say (product_number with empty_nums)
    say (sum_number with empty_nums)
    say (maybe_first_number with nums)
    say (maybe_last_number with nums)
    say (maybe_item_number with nums, 2)
    say (maybe_item_number with nums, 0)
    say (maybe_item_number with nums, 99)
    say (maybe_first_number with empty_nums)
    say (maybe_last_number with empty_nums)
    say (maybe_smallest_number with nums)
    say (maybe_largest_number with nums)
    say (maybe_average_number with nums)
    say (maybe_smallest_number with empty_nums)
    say (maybe_largest_number with empty_nums)
    say (maybe_average_number with empty_nums)
    let mid_nums be (list_slice_number with nums, 2, 3)
    say length of mid_nums
    say item 1 of mid_nums
    say item 2 of mid_nums
    let clamped_nums be (list_slice_number with nums, 0, 2)
    say length of clamped_nums
    say item 2 of clamped_nums
    let no_nums be (list_slice_number with nums, 4, 2)
    say length of no_nums
    let more_nums be a list of 10, 12
    extend_number with nums, more_nums
    say length of nums
    say item 5 of nums
    insert_number with nums, 1, 99
    insert_number with nums, 4, 77
    insert_number with nums, 99, 55
    say item 1 of nums
    say item 4 of nums
    say item 9 of nums
    say (pop_number with nums, 4)
    say length of nums
    say item 4 of nums
    say (pop_number with nums, 99)
    say length of nums
    say (remove_number with nums, 4)
    say length of nums
    say item 2 of nums
    say (remove_number with nums, 123)
    say length of nums
    sort_number with nums
    say item 1 of nums
    say item 7 of nums
    reverse_number with nums
    say item 1 of nums
    say item 7 of nums
    clear_number with nums
    say length of nums
    let words be a list of "red", "blue", "red"
    say (first_text with words)
    say (last_text with words)
    say (count_text with words, "red")
    say (contains_text with words, "blue")
    say (contains_text with words, "green")
    say (index_text with words, "green")
    let empty_words be an empty list of text
    say (maybe_first_text with words)
    say (maybe_last_text with words)
    say (maybe_item_text with words, 2)
    say (maybe_item_text with words, 99)
    say (maybe_first_text with empty_words)
    say (maybe_last_text with empty_words)
    say (maybe_smallest_text with words)
    say (maybe_largest_text with words)
    say (maybe_smallest_text with empty_words)
    say (maybe_largest_text with empty_words)
    let word_slice be (list_slice_text with words, 2, 99)
    say word_slice joined with "|"
    let no_word_slice be (list_slice_text with words, 3, 2)
    say length of no_word_slice
    let more_words be a list of "green"
    extend_text with words, more_words
    say length of words
    say item 4 of words
    insert_text with words, 2, "amber"
    insert_text with words, 99, "violet"
    say words joined with "|"
    say (pop_text with words, 3)
    say words joined with "|"
    say (pop_text with words, 0)
    say (remove_text with words, "red")
    say words joined with "|"
    say (remove_text with words, "missing")
    sort_text with words
    say words joined with "|"
    reverse_text with words
    say words joined with "|"
    clear_text with words
    say length of words
    let decimals be a list of 1.5, 2.5, 2.0
    say (first_decimal with decimals)
    say (last_decimal with decimals)
    say (average_decimal with decimals)
    say (product_decimal with decimals)
    say (sum_decimal with decimals)
    say (count_decimal with decimals, 2.5)
    say (contains_decimal with decimals, 1.5)
    say (contains_decimal with decimals, 9.0)
    say (index_decimal with decimals, 2.0)
    say (index_decimal with decimals, 9.0)
    let empty_decimals be an empty list of decimal
    say (product_decimal with empty_decimals)
    say (sum_decimal with empty_decimals)
    say (maybe_first_decimal with decimals)
    say (maybe_last_decimal with decimals)
    say (maybe_item_decimal with decimals, 2)
    say (maybe_item_decimal with decimals, -1)
    say (maybe_first_decimal with empty_decimals)
    say (maybe_last_decimal with empty_decimals)
    say (maybe_smallest_decimal with decimals)
    say (maybe_largest_decimal with decimals)
    say (maybe_average_decimal with decimals)
    say (maybe_smallest_decimal with empty_decimals)
    say (maybe_largest_decimal with empty_decimals)
    say (maybe_average_decimal with empty_decimals)
    let decimal_slice be (list_slice_decimal with decimals, 0, 2)
    say length of decimal_slice
    say item 1 of decimal_slice
    say item 2 of decimal_slice
    let more_decimals be a list of 9.5
    extend_decimal with decimals, more_decimals
    say length of decimals
    say item 4 of decimals
    insert_decimal with decimals, 2, 7.5
    insert_decimal with decimals, 0, 0.5
    say length of decimals
    say item 1 of decimals
    say item 3 of decimals
    say (pop_decimal with decimals, 6)
    say length of decimals
    say (pop_decimal with decimals, -1)
    say (remove_decimal with decimals, 7.5)
    say length of decimals
    say item 3 of decimals
    say (remove_decimal with decimals, 99.0)
    sort_decimal with decimals
    say item 1 of decimals
    say item 4 of decimals
    reverse_decimal with decimals
    say item 1 of decimals
    say item 4 of decimals
    clear_decimal with decimals
    say length of decimals
    let flags be a list of yes, no, yes
    say (first_yesno with flags)
    say (last_yesno with flags)
    say (maybe_first_yesno with flags)
    say (maybe_last_yesno with flags)
    say (all_yes with flags)
    say (any_yes with flags)
    say (count_yes with flags)
    say (count_no with flags)
    say (count_yesno with flags, yes)
    say (count_yesno with flags, no)
    say (contains_yesno with flags, yes)
    say (contains_yesno with flags, no)
    say (index_yes with flags)
    say (index_no with flags)
    say (index_yesno with flags, yes)
    say (index_yesno with flags, no)
    say (maybe_item_yesno with flags, 1)
    say (maybe_item_yesno with flags, 2)
    say (maybe_item_yesno with flags, 9)
    let flag_slice be (list_slice_yesno with flags, 2, 99)
    say length of flag_slice
    say item 1 of flag_slice
    say item 2 of flag_slice
    let more_flags be a list of no
    extend_yesno with flags, more_flags
    say length of flags
    say item 4 of flags
    insert_yesno with flags, 1, no
    insert_yesno with flags, 99, yes
    say length of flags
    say item 1 of flags
    say item 6 of flags
    say (pop_yesno with flags, 2)
    say length of flags
    say (pop_yesno with flags, 99)
    say (remove_yesno with flags, no)
    say length of flags
    say (remove_yesno with flags, yes)
    say (remove_yesno with flags, yes)
    clear_yesno with flags
    say length of flags
    let empty_flags be an empty list of yesno
    say (all_yes with empty_flags)
    say (any_yes with empty_flags)
    say (count_yesno with empty_flags, yes)
    say (count_yesno with empty_flags, no)
    say (index_yes with empty_flags)
    say (index_no with empty_flags)
    say (index_yesno with empty_flags, yes)
    say (index_yesno with empty_flags, no)
    say (maybe_first_yesno with empty_flags)
    say (maybe_last_yesno with empty_flags)
    let order_flags be a list of yes, no, no
    reverse_yesno with order_flags
    say item 1 of order_flags
    say item 2 of order_flags
    say item 3 of order_flags
    reverse_yesno with empty_flags
    say length of empty_flags
    let sortable_flags be a list of yes, no, yes, no
    sort_yesno with sortable_flags
    say item 1 of sortable_flags
    say item 2 of sortable_flags
    say item 3 of sortable_flags
    say item 4 of sortable_flags
    sort_yesno with empty_flags
    say length of empty_flags
    let copy_nums_source be a list of 5, 6
    let copied_nums be (copy_number with copy_nums_source)
    add 7 to copy_nums_source
    say length of copied_nums
    say item 1 of copied_nums
    say item 2 of copied_nums
    say length of copy_nums_source
    let copy_words_source be a list of "alpha", "beta"
    let copied_words be (copy_text with copy_words_source)
    add "gamma" to copy_words_source
    say copied_words joined with "|"
    say length of copy_words_source
    let copy_decimals_source be a list of 1.25, 2.75
    let copied_decimals be (copy_decimal with copy_decimals_source)
    add 3.5 to copy_decimals_source
    say length of copied_decimals
    say item 2 of copied_decimals
    say length of copy_decimals_source
    let copy_flags_source be a list of yes, no
    let copied_flags be (copy_yesno with copy_flags_source)
    add yes to copy_flags_source
    say length of copied_flags
    say item 1 of copied_flags
    say item 2 of copied_flags
    say length of copy_flags_source
'''
    proc = run_program(workdir, "bundled_std_list", src)
    assert proc.stdout == (
        "4\n8\n4.5\n256\n18\n2\nyes\nno\n4\nnothing\n1\n0\n4\n8\n2\nnothing\nnothing\n"
        "nothing\nnothing\n"
        "2\n8\n4.5\nnothing\nnothing\nnothing\n"
        "2\n2\n4\n2\n2\n0\n6\n10\n99\n77\n55\n77\n8\n4\nnothing\n8\nyes\n7\n2\nno\n7\n2\n99\n99\n2\n0\n"
        "red\nred\n2\nyes\nno\nnothing\nred\nred\nblue\nnothing\nnothing\nnothing\n"
        "blue\nred\nnothing\nnothing\n"
        "blue|red\n0\n4\ngreen\nred|amber|blue|red|green|violet\nblue\nred|amber|red|green|violet\nnothing\nyes\namber|red|green|violet\nno\namber|green|red|violet\nviolet|red|green|amber\n0\n"
        "1.5\n2\n2\n7.5\n6\n1\nyes\nno\n3\nnothing\n1\n0\n1.5\n2\n2.5\nnothing\nnothing\nnothing\n"
        "1.5\n2.5\n2\nnothing\nnothing\nnothing\n"
        "2\n1.5\n2.5\n4\n9.5\n6\n0.5\n7.5\n9.5\n5\nnothing\nyes\n4\n2.5\nno\n0.5\n2.5\n2.5\n0.5\n0\n"
        "yes\nyes\nyes\nyes\nno\nyes\n2\n1\n2\n1\nyes\nyes\n1\n2\n1\n2\nyes\nno\nnothing\n2\nno\nyes\n4\nno\n6\nno\nyes\nyes\n5\nnothing\nyes\n4\nyes\nyes\n0\nyes\nno\n0\n0\nnothing\nnothing\nnothing\nnothing\nnothing\nnothing\nno\nno\nyes\n0\nno\nno\nyes\nyes\n0\n"
        "2\n5\n6\n3\nalpha|beta\n3\n2\n2.75\n3\n2\nyes\nno\n3\n")


def test_bundled_std_map_package_runs(workdir):
    src = '''include "std/map"

to main:
    let scores be a map from text to number
    set item "ada" of scores to 36
    let scores_copy be (copy_number_map with scores)
    set item "ada" of scores to 99
    say item "ada" of scores_copy
    say item "ada" of scores
    set item "ada" of scores to 36
    say (number_has_key with scores, "ada")
    say (number_has_key with scores, "grace")
    say (number_at with scores, "ada")
    say (number_at with scores, "grace")
    say (number_or with scores, "grace", 0)
    add_count with scores, "ada"
    add_count with scores, "grace"
    say item "ada" of scores
    say item "grace" of scores
    say (take_number_at with scores, "ada")
    say length of scores
    say (number_at with scores, "ada")
    say (take_number_at with scores, "missing")
    say length of scores
    clear_number_map with scores
    say length of scores
    say (number_at with scores, "grace")
    let score_update_target be a map from text to number
    set item "a" of score_update_target to 1
    let score_update_more be a map from text to number
    set item "a" of score_update_more to 2
    set item "b" of score_update_more to 3
    update_number_map with score_update_target, score_update_more
    say item "a" of score_update_target
    say item "b" of score_update_target
    say length of score_update_target
    let score_ensure be a map from text to number
    say (ensure_number_at with score_ensure, "a", 4)
    say (ensure_number_at with score_ensure, "a", 5)
    say length of score_ensure
    let score_take_or be a map from text to number
    set item "a" of score_take_or to 7
    say (take_number_or with score_take_or, "a", 8)
    say (take_number_or with score_take_or, "a", 8)
    say length of score_take_or
    let score_values be a map from text to number
    set item "a" of score_values to 7
    say (number_has_value with score_values, 7)
    say (number_has_value with score_values, 8)

    let labels be a map from text to text
    set item "a" of labels to "alpha"
    let labels_copy be (copy_text_map with labels)
    set item "a" of labels to "after"
    say item "a" of labels_copy
    say item "a" of labels
    set item "a" of labels to "alpha"
    say (text_has_key with labels, "a")
    say (text_has_key with labels, "b")
    say (text_at with labels, "a")
    say (text_or with labels, "b", "missing")
    say (take_text_at with labels, "a")
    say length of labels
    say (take_text_at with labels, "b")
    set item "b" of labels to "bravo"
    clear_text_map with labels
    say length of labels
    say (text_at with labels, "b")
    let label_update_target be a map from text to text
    set item "a" of label_update_target to "old"
    let label_update_more be a map from text to text
    set item "a" of label_update_more to "after"
    set item "b" of label_update_more to "new"
    update_text_map with label_update_target, label_update_more
    say item "a" of label_update_target
    say item "b" of label_update_target
    say length of label_update_target
    let label_ensure be a map from text to text
    say (ensure_text_at with label_ensure, "a", "fallback")
    say (ensure_text_at with label_ensure, "a", "ignored")
    say length of label_ensure
    let label_take_or be a map from text to text
    set item "a" of label_take_or to "found"
    say (take_text_or with label_take_or, "a", "fallback")
    say (take_text_or with label_take_or, "a", "fallback")
    say length of label_take_or
    let label_values be a map from text to text
    set item "a" of label_values to "found"
    say (text_has_value with label_values, "found")
    say (text_has_value with label_values, "missing")

    let prices be a map from text to decimal
    set item "tea" of prices to 2.5
    let prices_copy be (copy_decimal_map with prices)
    set item "tea" of prices to 9.5
    say item "tea" of prices_copy
    say item "tea" of prices
    set item "tea" of prices to 2.5
    say (decimal_has_key with prices, "tea")
    say (decimal_has_key with prices, "cake")
    say (decimal_at with prices, "tea")
    say (decimal_at with prices, "cake")
    say (decimal_or with prices, "cake", 0.0)
    say (take_decimal_at with prices, "tea")
    say length of prices
    say (take_decimal_at with prices, "cake")
    set item "cake" of prices to 3.5
    clear_decimal_map with prices
    say length of prices
    say (decimal_at with prices, "cake")
    let price_update_target be a map from text to decimal
    set item "a" of price_update_target to 1.5
    let price_update_more be a map from text to decimal
    set item "a" of price_update_more to 2.5
    set item "b" of price_update_more to 3.5
    update_decimal_map with price_update_target, price_update_more
    say item "a" of price_update_target
    say item "b" of price_update_target
    say length of price_update_target
    let price_ensure be a map from text to decimal
    say (ensure_decimal_at with price_ensure, "a", 4.5)
    say (ensure_decimal_at with price_ensure, "a", 5.5)
    say length of price_ensure
    let price_take_or be a map from text to decimal
    set item "a" of price_take_or to 7.5
    say (take_decimal_or with price_take_or, "a", 8.5)
    say (take_decimal_or with price_take_or, "a", 8.5)
    say length of price_take_or
    let price_values be a map from text to decimal
    set item "a" of price_values to 7.5
    say (decimal_has_value with price_values, 7.5)
    say (decimal_has_value with price_values, 8.5)

    let flags be a map from text to yesno
    set item "ready" of flags to yes
    let flags_copy be (copy_yesno_map with flags)
    set item "ready" of flags to no
    say item "ready" of flags_copy
    say item "ready" of flags
    set item "ready" of flags to yes
    say (yesno_has_key with flags, "ready")
    say (yesno_has_key with flags, "missing")
    say (yesno_at with flags, "ready")
    say (yesno_at with flags, "missing")
    say (yesno_or with flags, "missing", no)
    say (take_yesno_at with flags, "ready")
    say length of flags
    say (take_yesno_at with flags, "missing")
    set item "missing" of flags to no
    clear_yesno_map with flags
    say length of flags
    say (yesno_at with flags, "missing")
    let flag_update_target be a map from text to yesno
    set item "a" of flag_update_target to yes
    let flag_update_more be a map from text to yesno
    set item "a" of flag_update_more to no
    set item "b" of flag_update_more to yes
    update_yesno_map with flag_update_target, flag_update_more
    say item "a" of flag_update_target
    say item "b" of flag_update_target
    say length of flag_update_target
    let flag_ensure be a map from text to yesno
    say (ensure_yesno_at with flag_ensure, "a", yes)
    say (ensure_yesno_at with flag_ensure, "a", no)
    say length of flag_ensure
    let flag_take_or be a map from text to yesno
    set item "a" of flag_take_or to no
    say (take_yesno_or with flag_take_or, "a", yes)
    say (take_yesno_or with flag_take_or, "a", yes)
    say length of flag_take_or
    let flag_values be a map from text to yesno
    set item "a" of flag_values to yes
    say (yesno_has_value with flag_values, yes)
    say (yesno_has_value with flag_values, no)

    let seats be a map from number to number
    set item 7 of seats to 42
    let seats_copy be (copy_number_key_number_map with seats)
    set item 7 of seats to 99
    say item 7 of seats_copy
    say item 7 of seats
    set item 7 of seats to 42
    say (number_key_number_has_key with seats, 7)
    say (number_key_number_has_key with seats, 8)
    say (number_key_number_at with seats, 7)
    say (number_key_number_at with seats, 8)
    say (number_key_number_or with seats, 8, 0)
    add_number_key_count with seats, 7
    add_number_key_count with seats, 8
    say item 7 of seats
    say item 8 of seats
    say (take_number_key_number_at with seats, 7)
    say length of seats
    say (number_key_number_at with seats, 7)
    say (take_number_key_number_at with seats, 99)
    clear_number_key_number_map with seats
    say length of seats
    say (number_key_number_at with seats, 8)
    let seat_update_target be a map from number to number
    set item 1 of seat_update_target to 10
    let seat_update_more be a map from number to number
    set item 1 of seat_update_more to 20
    set item 2 of seat_update_more to 30
    update_number_key_number_map with seat_update_target, seat_update_more
    say item 1 of seat_update_target
    say item 2 of seat_update_target
    say length of seat_update_target
    let seat_ensure be a map from number to number
    say (ensure_number_key_number_at with seat_ensure, 1, 40)
    say (ensure_number_key_number_at with seat_ensure, 1, 50)
    say length of seat_ensure
    let seat_take_or be a map from number to number
    set item 1 of seat_take_or to 70
    say (take_number_key_number_or with seat_take_or, 1, 80)
    say (take_number_key_number_or with seat_take_or, 1, 80)
    say length of seat_take_or
    let seat_values be a map from number to number
    set item 1 of seat_values to 70
    say (number_key_number_has_value with seat_values, 70)
    say (number_key_number_has_value with seat_values, 80)

    let names be a map from number to text
    set item 1 of names to "one"
    let names_copy be (copy_number_key_text_map with names)
    set item 1 of names to "after"
    say item 1 of names_copy
    say item 1 of names
    set item 1 of names to "one"
    say (number_key_text_has_key with names, 1)
    say (number_key_text_has_key with names, 2)
    say (number_key_text_at with names, 1)
    say (number_key_text_or with names, 2, "missing")
    say (take_number_key_text_at with names, 1)
    say length of names
    say (take_number_key_text_at with names, 2)
    set item 2 of names to "two"
    clear_number_key_text_map with names
    say length of names
    say (number_key_text_at with names, 2)
    let name_update_target be a map from number to text
    set item 1 of name_update_target to "old"
    let name_update_more be a map from number to text
    set item 1 of name_update_more to "after"
    set item 2 of name_update_more to "new"
    update_number_key_text_map with name_update_target, name_update_more
    say item 1 of name_update_target
    say item 2 of name_update_target
    say length of name_update_target
    let name_ensure be a map from number to text
    say (ensure_number_key_text_at with name_ensure, 1, "fallback")
    say (ensure_number_key_text_at with name_ensure, 1, "ignored")
    say length of name_ensure
    let name_take_or be a map from number to text
    set item 1 of name_take_or to "found"
    say (take_number_key_text_or with name_take_or, 1, "fallback")
    say (take_number_key_text_or with name_take_or, 1, "fallback")
    say length of name_take_or
    let name_values be a map from number to text
    set item 1 of name_values to "found"
    say (number_key_text_has_value with name_values, "found")
    say (number_key_text_has_value with name_values, "missing")

    let ratios be a map from number to decimal
    set item 2 of ratios to 0.5
    let ratios_copy be (copy_number_key_decimal_map with ratios)
    set item 2 of ratios to 9.5
    say item 2 of ratios_copy
    say item 2 of ratios
    set item 2 of ratios to 0.5
    say (number_key_decimal_has_key with ratios, 2)
    say (number_key_decimal_has_key with ratios, 3)
    say (number_key_decimal_at with ratios, 2)
    say (number_key_decimal_at with ratios, 3)
    say (number_key_decimal_or with ratios, 3, 1.0)
    say (take_number_key_decimal_at with ratios, 2)
    say length of ratios
    say (take_number_key_decimal_at with ratios, 3)
    set item 3 of ratios to 1.5
    clear_number_key_decimal_map with ratios
    say length of ratios
    say (number_key_decimal_at with ratios, 3)
    let ratio_update_target be a map from number to decimal
    set item 1 of ratio_update_target to 1.5
    let ratio_update_more be a map from number to decimal
    set item 1 of ratio_update_more to 2.5
    set item 2 of ratio_update_more to 3.5
    update_number_key_decimal_map with ratio_update_target, ratio_update_more
    say item 1 of ratio_update_target
    say item 2 of ratio_update_target
    say length of ratio_update_target
    let ratio_ensure be a map from number to decimal
    say (ensure_number_key_decimal_at with ratio_ensure, 1, 4.5)
    say (ensure_number_key_decimal_at with ratio_ensure, 1, 5.5)
    say length of ratio_ensure
    let ratio_take_or be a map from number to decimal
    set item 1 of ratio_take_or to 7.5
    say (take_number_key_decimal_or with ratio_take_or, 1, 8.5)
    say (take_number_key_decimal_or with ratio_take_or, 1, 8.5)
    say length of ratio_take_or
    let ratio_values be a map from number to decimal
    set item 1 of ratio_values to 7.5
    say (number_key_decimal_has_value with ratio_values, 7.5)
    say (number_key_decimal_has_value with ratio_values, 8.5)

    let switches be a map from number to yesno
    set item 1 of switches to yes
    let switches_copy be (copy_number_key_yesno_map with switches)
    set item 1 of switches to no
    say item 1 of switches_copy
    say item 1 of switches
    set item 1 of switches to yes
    say (number_key_yesno_has_key with switches, 1)
    say (number_key_yesno_has_key with switches, 2)
    say (number_key_yesno_at with switches, 1)
    say (number_key_yesno_at with switches, 2)
    say (number_key_yesno_or with switches, 2, no)
    say (take_number_key_yesno_at with switches, 1)
    say length of switches
    say (take_number_key_yesno_at with switches, 2)
    set item 2 of switches to no
    clear_number_key_yesno_map with switches
    say length of switches
    say (number_key_yesno_at with switches, 2)
    let switch_update_target be a map from number to yesno
    set item 1 of switch_update_target to yes
    let switch_update_more be a map from number to yesno
    set item 1 of switch_update_more to no
    set item 2 of switch_update_more to yes
    update_number_key_yesno_map with switch_update_target, switch_update_more
    say item 1 of switch_update_target
    say item 2 of switch_update_target
    say length of switch_update_target
    let switch_ensure be a map from number to yesno
    say (ensure_number_key_yesno_at with switch_ensure, 1, yes)
    say (ensure_number_key_yesno_at with switch_ensure, 1, no)
    say length of switch_ensure
    let switch_take_or be a map from number to yesno
    set item 1 of switch_take_or to no
    say (take_number_key_yesno_or with switch_take_or, 1, yes)
    say (take_number_key_yesno_or with switch_take_or, 1, yes)
    say length of switch_take_or
    let switch_values be a map from number to yesno
    set item 1 of switch_values to yes
    say (number_key_yesno_has_value with switch_values, yes)
    say (number_key_yesno_has_value with switch_values, no)
'''
    proc = run_program(workdir, "bundled_std_map", src)
    assert proc.stdout == (
        "36\n99\nyes\nno\n36\nnothing\n0\n37\n1\n37\n1\nnothing\nnothing\n1\n0\nnothing\n2\n3\n2\n4\n4\n1\n7\n8\n0\nyes\nno\n"
        "alpha\nafter\nyes\nno\nalpha\nmissing\nalpha\n0\nnothing\n0\nnothing\nafter\nnew\n2\nfallback\nfallback\n1\nfound\nfallback\n0\nyes\nno\n"
        "2.5\n9.5\nyes\nno\n2.5\nnothing\n0\n2.5\n0\nnothing\n0\nnothing\n2.5\n3.5\n2\n4.5\n4.5\n1\n7.5\n8.5\n0\nyes\nno\n"
        "yes\nno\nyes\nno\nyes\nnothing\nno\nyes\n0\nnothing\n0\nnothing\nno\nyes\n2\nyes\nyes\n1\nno\nyes\n0\nyes\nno\n"
        "42\n99\nyes\nno\n42\nnothing\n0\n43\n1\n43\n1\nnothing\nnothing\n0\nnothing\n20\n30\n2\n40\n40\n1\n70\n80\n0\nyes\nno\n"
        "one\nafter\nyes\nno\none\nmissing\none\n0\nnothing\n0\nnothing\nafter\nnew\n2\nfallback\nfallback\n1\nfound\nfallback\n0\nyes\nno\n"
        "0.5\n9.5\nyes\nno\n0.5\nnothing\n1\n0.5\n0\nnothing\n0\nnothing\n2.5\n3.5\n2\n4.5\n4.5\n1\n7.5\n8.5\n0\nyes\nno\n"
        "yes\nno\nyes\nno\nyes\nnothing\nno\nyes\n0\nnothing\n0\nnothing\nno\nyes\n2\nyes\nyes\n1\nno\nyes\n0\nyes\nno\n")


def test_bundled_std_list_filter_helpers_run(workdir):
    src = '''include "std/list"

to is_even with n as number giving yesno:
    give back remainder of n divided by 2 is 0

to starts_with_a with t as text giving yesno:
    give back t starts with "a"

to over_one with d as decimal giving yesno:
    give back d is more than 1.0

to same with flag as yesno giving yesno:
    give back flag

to main:
    let numbers be a list of 1, 2, 3, 4
    let even_numbers be (filter_number with numbers, the function is_even)
    say length of even_numbers
    say item 1 of even_numbers
    say item 2 of even_numbers

    let names be a list of "ada", "grace", "alan"
    let a_names be (filter_text with names, the function starts_with_a)
    say a_names joined with "|"

    let decimals be a list of 0.5, 1.5, 2.5
    let bigger be (filter_decimal with decimals, the function over_one)
    say length of bigger
    say item 1 of bigger
    say item 2 of bigger

    let flags be a list of yes, no, yes
    let yes_flags be (filter_yesno with flags, the function same)
    say length of yes_flags
    say item 1 of yes_flags
    say item 2 of yes_flags
'''
    proc = run_program(workdir, "bundled_std_list_filter", src)
    assert proc.stdout == "2\n2\n4\nada|alan\n2\n1.5\n2.5\n2\nyes\nyes\n"


def test_bundled_std_list_map_helpers_run(workdir):
    src = '''include "std/list"

to double with n as number giving number:
    give back n times 2

to shout with t as text giving text:
    give back uppercase of t

to add_half with d as decimal giving decimal:
    give back d plus 0.5

to flipped with flag as yesno giving yesno:
    if flag:
        give back no
    give back yes

to main:
    let numbers be a list of 1, 2, 3
    let doubled be (map_number with numbers, the function double)
    say length of doubled
    say item 1 of doubled
    say item 2 of doubled
    say item 3 of doubled

    let names be a list of "ada", "grace"
    let loud be (map_text with names, the function shout)
    say loud joined with "|"

    let decimals be a list of 1.5, 2.5
    let shifted be (map_decimal with decimals, the function add_half)
    say length of shifted
    say item 1 of shifted
    say item 2 of shifted

    let flags be a list of yes, no
    let inverted be (map_yesno with flags, the function flipped)
    say length of inverted
    say item 1 of inverted
    say item 2 of inverted
'''
    proc = run_program(workdir, "bundled_std_list_map", src)
    assert proc.stdout == "3\n2\n4\n6\nADA|GRACE\n2\n2\n3\n2\nno\nyes\n"


def test_bundled_std_list_predicate_helpers_run(workdir):
    src = '''include "std/list"

to is_even with n as number giving yesno:
    give back remainder of n divided by 2 is 0

to starts_with_a with t as text giving yesno:
    give back t starts with "a"

to over_two with d as decimal giving yesno:
    give back d is more than 2.0

to same with flag as yesno giving yesno:
    give back flag

to main:
    let numbers be a list of 2, 4, 5
    say (any_number with numbers, the function is_even)
    say (all_number with numbers, the function is_even)
    let empty_numbers be an empty list of number
    say (any_number with empty_numbers, the function is_even)
    say (all_number with empty_numbers, the function is_even)

    let names be a list of "ada", "alan"
    say (all_text with names, the function starts_with_a)
    let other_names be a list of "grace", "linus"
    say (any_text with other_names, the function starts_with_a)

    let decimals be a list of 1.5, 2.5
    say (any_decimal with decimals, the function over_two)
    say (all_decimal with decimals, the function over_two)

    let flags be a list of yes, no
    say (any_yesno with flags, the function same)
    say (all_yesno with flags, the function same)
'''
    proc = run_program(workdir, "bundled_std_list_predicate", src)
    assert proc.stdout == "yes\nno\nno\nyes\nyes\nno\nyes\nno\nyes\nno\n"


def test_bundled_std_text_any_edge_helpers_run(workdir):
    src = '''include "std/text"

to main:
    let prefixes be a list of "http://", "https://"
    say (has_any_prefix with "https://example.com", prefixes)
    say (has_any_prefix with "ftp://example.com", prefixes)
    let empty_prefixes be an empty list of text
    say (has_any_prefix with "anything", empty_prefixes)
    let blank_prefix be a list of ""
    say (has_any_prefix with "anything", blank_prefix)

    let suffixes be a list of ".par", ".md"
    say (has_any_suffix with "notes.par", suffixes)
    say (has_any_suffix with "archive.zip", suffixes)
    let empty_suffixes be an empty list of text
    say (has_any_suffix with "anything", empty_suffixes)
    let blank_suffix be a list of ""
    say (has_any_suffix with "anything", blank_suffix)
'''
    proc = run_program(workdir, "bundled_std_text_any_edge", src)
    assert proc.stdout == "yes\nno\nno\nyes\nyes\nno\nno\nyes\n"


def test_bundled_std_text_position_fallback_helpers_run(workdir):
    src = '''include "std/text"

to main:
    say (position_or_zero with "=", "key=value=tail")
    say (position_or_zero with ":", "no match")
    say (position_or_zero with "", "abc")
    say (position_or_zero with "c", "éclair")
    say (last_position_or_zero with "=", "key=value=tail")
    say (last_position_or_zero with ":", "no match")
    say (last_position_or_zero with "", "abc")
    say (last_position_or_zero with "c", "éclair")
'''
    proc = run_program(workdir, "bundled_std_text_position_fallback", src)
    assert proc.stdout == "4\n0\n1\n2\n10\n0\n4\n2\n"


def test_bundled_std_text_character_trim_helpers_run(workdir):
    src = '''include "std/text"

to main:
    say (left_trimmed_of with "***value!!", "*!")
    say (right_trimmed_of with "***value!!", "*!")
    say (trimmed_of with "***value!!", "*!")
    say (trimmed_of with "abc", "")
    say (trimmed_of with "aaaa", "a")
    say (trimmed_of with "é-éclair-é", "é-")
'''
    proc = run_program(workdir, "bundled_std_text_character_trim", src)
    assert proc.stdout == "value!!\n***value\nvalue\nabc\n\nclair\n"


def test_bundled_std_text_split_lines_kept_helper_runs(workdir):
    src = '''include "std/text"

to markers with t as text giving text:
    let no_cr be (replaced_text with t, "\\r", "<r>", 10)
    give back (replaced_text with no_cr, "\\n", "<n>", 10)

to main:
    let kept be (split_lines_kept with "one\\r\\ntwo\\rthree\\nfour")
    say length of kept
    say (markers with item 1 of kept)
    say (markers with item 2 of kept)
    say (markers with item 3 of kept)
    say (markers with item 4 of kept)
    let terminal be (split_lines_kept with "x\\n")
    say length of terminal
    say (markers with item 1 of terminal)
    let empty be (split_lines_kept with "")
    say length of empty
'''
    proc = run_program(workdir, "bundled_std_text_split_lines_kept", src)
    assert proc.stdout == "4\none<r><n>\ntwo<r>\nthree<n>\nfour\n1\nx<n>\n0\n"


def test_bundled_std_list_maybe_find_helpers_run(workdir):
    src = '''include "std/list"

to is_odd with n as number giving yesno:
    give back remainder of n divided by 2 is 1

to more_than_ten with n as number giving yesno:
    give back n is more than 10

to starts_with_g with t as text giving yesno:
    give back t starts with "g"

to over_two with d as decimal giving yesno:
    give back d is more than 2.0

to same with flag as yesno giving yesno:
    give back flag

to main:
    let numbers be a list of 2, 4, 5, 7
    say (maybe_find_number with numbers, the function is_odd)
    say (maybe_find_number with numbers, the function more_than_ten)

    let names be a list of "ada", "grace", "guido"
    say (maybe_find_text with names, the function starts_with_g)

    let decimals be a list of 1.5, 2.5, 4.5
    say (maybe_find_decimal with decimals, the function over_two)

    let flags be a list of no, yes
    say (maybe_find_yesno with flags, the function same)
    let empty_flags be an empty list of yesno
    say (maybe_find_yesno with empty_flags, the function same)
'''
    proc = run_program(workdir, "bundled_std_list_maybe_find", src)
    assert proc.stdout == "5\nnothing\ngrace\n2.5\nyes\nnothing\n"


def test_bundled_std_list_count_where_helpers_run(workdir):
    src = '''include "std/list"

to is_even with n as number giving yesno:
    give back remainder of n divided by 2 is 0

to starts_with_a with t as text giving yesno:
    give back t starts with "a"

to over_two with d as decimal giving yesno:
    give back d is more than 2.0

to same with flag as yesno giving yesno:
    give back flag

to main:
    let numbers be a list of 1, 2, 3, 4, 6
    say (count_where_number with numbers, the function is_even)
    let empty_numbers be an empty list of number
    say (count_where_number with empty_numbers, the function is_even)

    let names be a list of "ada", "grace", "alan"
    say (count_where_text with names, the function starts_with_a)
    let other_names be a list of "grace", "linus"
    say (count_where_text with other_names, the function starts_with_a)

    let decimals be a list of 1.5, 2.5, 3.5
    say (count_where_decimal with decimals, the function over_two)

    let flags be a list of yes, no, yes
    say (count_where_yesno with flags, the function same)
'''
    proc = run_program(workdir, "bundled_std_list_count_where", src)
    assert proc.stdout == "3\n0\n2\n0\n2\n2\n"


def test_bundled_std_list_fold_helpers_run(workdir):
    src = '''include "std/list"

to add_numbers with left as number, right as number giving number:
    give back left plus right

to join_text with left as text, right as text giving text:
    if left is "":
        give back right
    give back "{left}|{right}"

to add_decimals with left as decimal, right as decimal giving decimal:
    give back left plus right

to both_yes with left as yesno, right as yesno giving yesno:
    give back left and right

to main:
    let numbers be a list of 2, 3, 4
    say (fold_number with numbers, 10, the function add_numbers)
    let empty_numbers be an empty list of number
    say (fold_number with empty_numbers, 10, the function add_numbers)

    let names be a list of "ada", "grace", "linus"
    say (fold_text with names, "", the function join_text)
    let empty_names be an empty list of text
    say (fold_text with empty_names, "none", the function join_text)

    let decimals be a list of 1.5, 2.5
    say (fold_decimal with decimals, 0.5, the function add_decimals)

    let flags be a list of yes, no, yes
    say (fold_yesno with flags, yes, the function both_yes)
    let empty_flags be an empty list of yesno
    say (fold_yesno with empty_flags, yes, the function both_yes)
'''
    proc = run_program(workdir, "bundled_std_list_fold", src)
    assert proc.stdout == "19\n10\nada|grace|linus\nnone\n4.5\nno\nyes\n"


def test_bundled_std_list_take_drop_while_helpers_run(workdir):
    src = '''include "std/list"

to below_five with n as number giving yesno:
    give back n is less than 5

to starts_with_a with t as text giving yesno:
    give back t starts with "a"

to below_three with d as decimal giving yesno:
    give back d is less than 3.0

to same with flag as yesno giving yesno:
    give back flag

to main:
    let numbers be a list of 1, 2, 6, 3
    let low_prefix be (take_while_number with numbers, the function below_five)
    say length of low_prefix
    say item 1 of low_prefix
    say item 2 of low_prefix
    let after_low_prefix be (drop_while_number with numbers, the function below_five)
    say length of after_low_prefix
    say item 1 of after_low_prefix
    let empty_numbers be an empty list of number
    say length of (take_while_number with empty_numbers, the function below_five)
    say length of (drop_while_number with empty_numbers, the function below_five)

    let names be a list of "ada", "alan", "grace", "amy"
    say (take_while_text with names, the function starts_with_a) joined with "|"
    say (drop_while_text with names, the function starts_with_a) joined with "|"

    let decimals be a list of 1.5, 2.5, 4.5
    let small_decimals be (take_while_decimal with decimals, the function below_three)
    say length of small_decimals
    let big_tail be (drop_while_decimal with decimals, the function below_three)
    say item 1 of big_tail

    let flags be a list of yes, yes, no, yes
    say length of (take_while_yesno with flags, the function same)
    let flag_tail be (drop_while_yesno with flags, the function same)
    say length of flag_tail
    say item 1 of flag_tail
'''
    proc = run_program(workdir, "bundled_std_list_take_drop_while", src)
    assert proc.stdout == "2\n1\n2\n2\n6\n0\n0\nada|alan\ngrace|amy\n2\n4.5\n2\n2\nno\n"


def test_bundled_std_list_reject_helpers_run(workdir):
    src = '''include "std/list"

to below_five with n as number giving yesno:
    give back n is less than 5

to starts_with_a with t as text giving yesno:
    give back t starts with "a"

to below_three with d as decimal giving yesno:
    give back d is less than 3.0

to same with flag as yesno giving yesno:
    give back flag

to main:
    let numbers be a list of 1, 6, 2
    let high_numbers be (reject_number with numbers, the function below_five)
    say length of high_numbers
    say item 1 of high_numbers

    let names be a list of "ada", "grace", "alan"
    say (reject_text with names, the function starts_with_a) joined with "|"

    let decimals be a list of 1.5, 4.5, 2.5
    let large_decimals be (reject_decimal with decimals, the function below_three)
    say length of large_decimals
    say item 1 of large_decimals

    let flags be a list of yes, no, yes, no
    let false_flags be (reject_yesno with flags, the function same)
    say length of false_flags
    say item 1 of false_flags
    say item 2 of false_flags

    let empty_numbers be an empty list of number
    say length of (reject_number with empty_numbers, the function below_five)
'''
    proc = run_program(workdir, "bundled_std_list_reject", src)
    assert proc.stdout == "1\n6\ngrace\n1\n4.5\n2\nno\nno\n0\n"


def test_bundled_std_list_maybe_find_index_helpers_run(workdir):
    src = '''include "std/list"

to is_odd with n as number giving yesno:
    give back remainder of n divided by 2 is 1

to more_than_ten with n as number giving yesno:
    give back n is more than 10

to starts_with_g with t as text giving yesno:
    give back t starts with "g"

to over_two with d as decimal giving yesno:
    give back d is more than 2.0

to same with flag as yesno giving yesno:
    give back flag

to main:
    let numbers be a list of 2, 4, 5, 7
    say (maybe_find_index_number with numbers, the function is_odd)
    say (maybe_find_index_number with numbers, the function more_than_ten)

    let names be a list of "ada", "grace", "guido"
    say (maybe_find_index_text with names, the function starts_with_g)

    let decimals be a list of 1.5, 2.5, 4.5
    say (maybe_find_index_decimal with decimals, the function over_two)

    let flags be a list of no, yes
    say (maybe_find_index_yesno with flags, the function same)
    let empty_flags be an empty list of yesno
    say (maybe_find_index_yesno with empty_flags, the function same)
'''
    proc = run_program(workdir, "bundled_std_list_maybe_find_index", src)
    assert proc.stdout == "3\nnothing\n2\n2\n2\nnothing\n"


def test_bundled_std_list_indexes_where_helpers_run(workdir):
    src = '''include "std/list"

to is_odd with n as number giving yesno:
    give back remainder of n divided by 2 is 1

to more_than_ten with n as number giving yesno:
    give back n is more than 10

to starts_with_g with t as text giving yesno:
    give back t starts with "g"

to over_two with d as decimal giving yesno:
    give back d is more than 2.0

to same with flag as yesno giving yesno:
    give back flag

to main:
    let numbers be a list of 2, 5, 6, 7
    let odd_indexes be (indexes_where_number with numbers, the function is_odd)
    say length of odd_indexes
    say item 1 of odd_indexes
    say item 2 of odd_indexes
    say length of (indexes_where_number with numbers, the function more_than_ten)

    let names be a list of "ada", "grace", "guido"
    let g_indexes be (indexes_where_text with names, the function starts_with_g)
    say length of g_indexes
    say item 1 of g_indexes
    say item 2 of g_indexes

    let decimals be a list of 1.5, 2.5, 4.5
    let decimal_indexes be (indexes_where_decimal with decimals, the function over_two)
    say length of decimal_indexes
    say item 1 of decimal_indexes
    say item 2 of decimal_indexes

    let flags be a list of no, yes, no, yes
    let yes_indexes be (indexes_where_yesno with flags, the function same)
    say length of yes_indexes
    say item 1 of yes_indexes
    say item 2 of yes_indexes
    let empty_flags be an empty list of yesno
    say length of (indexes_where_yesno with empty_flags, the function same)
'''
    proc = run_program(workdir, "bundled_std_list_indexes_where", src)
    assert proc.stdout == "2\n2\n4\n0\n2\n2\n3\n2\n2\n3\n2\n2\n4\n0\n"


def test_build_produces_native_binary(workdir):
    src = 'to main:\n    say "compiled!"\n'
    f = workdir / "binme.par"
    f.write_text(src)
    proc = run_cli(["build", f.name, "-o", "binme"], cwd=workdir)
    assert proc.returncode == 0, proc.stderr
    import subprocess
    out = subprocess.run([str(workdir / "binme")], capture_output=True, text=True)
    assert out.stdout == "compiled!\n"


def test_check_json_clean(workdir):
    f = workdir / "clean.par"
    f.write_text('to main:\n    say "ok"\n')
    proc = run_cli(["check", f.name, "--json"], cwd=workdir)
    assert json.loads(proc.stdout) == {"ok": True, "diagnostics": []}


def test_rust_command_prints_source(workdir):
    f = workdir / "dump.par"
    f.write_text("to main:\n    say 1\n")
    proc = run_cli(["rust", f.name], cwd=workdir)
    assert proc.returncode == 0
    assert "fn main_p()" in proc.stdout


def test_new_command(workdir):
    proc = run_cli(["new", "fresh_proj"], cwd=workdir)
    assert proc.returncode == 0
    proc = run_cli(["run", "fresh_proj/main.par"], cwd=workdir)
    assert proc.returncode == 0, proc.stderr
    assert "Hello from fresh_proj!" in proc.stdout
    assert "the sum is 14" in proc.stdout


# ------------------------------------------------------------------ v0.2: when patterns + function values

def test_higher_order(workdir):
    proc = run_cli(["run", str(EXAMPLES / "higher_order.par")], cwd=workdir)
    assert proc.returncode == 0
    assert proc.stdout == (
        "double twice: 20\n"
        "triple twice: 45\n"
        "double says 10\n"
        "triple says 15\n")


def test_when_ranges_and_multi_values(workdir):
    proc = run_program(workdir, "ranges", (
        "to grade with score as number giving text:\n"
        "    when score:\n"
        "        is 90 to 100:\n"
        "            give back \"A\"\n"
        "        is 80 to 89:\n"
        "            give back \"B\"\n"
        "        is 1, 2 or 3:\n"
        "            give back \"tiny\"\n"
        "        otherwise:\n"
        "            give back \"other\"\n"
        "to main:\n"
        "    say (grade with 95)\n"
        "    say (grade with 80)\n"
        "    say (grade with 2)\n"
        "    say (grade with 50)\n"))
    assert proc.stdout == "A\nB\ntiny\nother\n"


def test_decimal_when_with_int_arm(workdir):
    proc = run_program(workdir, "decwhen", (
        "to main:\n"
        "    let x be 3.0\n"
        "    when x:\n"
        "        is 3:\n"
        "            say \"three\"\n"
        "        is 0.5 to 1.5:\n"
        "            say \"around one\"\n"
        "        otherwise:\n"
        "            say \"other\"\n"))
    assert proc.stdout == "three\n"


def test_closure_captures_values(workdir):
    proc = run_cli(["run", str(EXAMPLES / "closures.par")], cwd=workdir)
    assert proc.returncode == 0
    assert proc.stdout == "12\nvalue: 12\n"
