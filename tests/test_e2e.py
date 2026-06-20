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
    let lines be (nonempty_lines with " one \\n\\n  two\\n  ")
    say length of lines
    say lines joined with "|"
    let raw_lines be (lines_of with "one\\n\\n  two\\n")
    say length of raw_lines
    say raw_lines joined with "|"
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
    say (last_position with "=", "key=value=tail")
    say (last_position with "aa", "aaaa")
    say (last_position with ":", "no match")
    say (last_position with "", "abc")
    say (last_position with "c", "éclair")
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
    say (padded_center with "go", 5, ".")
    say (padded_center with "go", 6, ".")
    say (padded_center with "wide", 2, ".")
    say (padded_center with "x", 4, "")
    say (padded_center with "x", 4, "ab")
'''
    proc = run_program(workdir, "bundled_std", src)
    assert proc.stdout == (
        "10\n10.5\n1.5\nyes\nno\n25\nyes\nhahaha\n0\n3\n2\n3\n"
        "3\none|two|three\n0\n2\none|two\n4\none||  two|\n0\n0\né\nc\nnothing\nnothing\n"
        "rèm\ncr\nme\n\n\nyelraP\nrialcé\n\n3\nkey|=|value=tail\nno match||\né|c|lair\nkey=value|=|tail\n||no match\né|c|lair\n10\n3\nnothing\n4\n2\nlang\nparley-lang\nparley-lang\nnotes\nnotes.par\nnotes.par\nyes\nno\nyes\nyes\nno\nyes\n"
        "yes\nyes\nno\nyes\nno\nno\nyes\nno\nno\nyes\nno\nno\nyes\nyes\nno\nyes\nyes\nyes\nyes\nno\nyes\nyes\nyes\nno\nno\nyes\nno\nno\nyes\nno\nno\npARLEY 3\n\nParley Language\nMixed   Case\n\nyes\nno\nno\nno\nParley\nMixed case\nX\n\nleft  \n  right\nboth\nboth\n\n\n"
        "007\ngo...\nwide\nstay\nx\nxababab\n.go..\n..go..\nwide\nx\nabxab\n")


def test_bundled_std_list_package_runs(workdir):
    src = '''include "std/list"

to main:
    let nums be a list of 4, 2, 4, 8
    say (first_number with nums)
    say (last_number with nums)
    say (average_number with nums)
    say (count_number with nums, 4)
    say (index_number with nums, 8)
    say (index_number with nums, 9)
    let empty_nums be an empty list of number
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
    say (count_decimal with decimals, 2.5)
    say (index_decimal with decimals, 2.0)
    say (index_decimal with decimals, 9.0)
    let empty_decimals be an empty list of decimal
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
    say (index_yes with flags)
    say (index_no with flags)
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
    say (index_yes with empty_flags)
    say (index_no with empty_flags)
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
        "4\n8\n4.5\n2\n4\nnothing\n4\n8\n2\nnothing\nnothing\n"
        "nothing\nnothing\n"
        "2\n8\n4.5\nnothing\nnothing\nnothing\n"
        "2\n2\n4\n2\n2\n0\n6\n10\n99\n77\n55\n77\n8\n4\nnothing\n8\nyes\n7\n2\nno\n7\n2\n99\n99\n2\n0\n"
        "red\nred\n2\nnothing\nred\nred\nblue\nnothing\nnothing\nnothing\n"
        "blue\nred\nnothing\nnothing\n"
        "blue|red\n0\n4\ngreen\nred|amber|blue|red|green|violet\nblue\nred|amber|red|green|violet\nnothing\nyes\namber|red|green|violet\nno\namber|green|red|violet\nviolet|red|green|amber\n0\n"
        "1.5\n2\n2\n1\n3\nnothing\n1.5\n2\n2.5\nnothing\nnothing\nnothing\n"
        "1.5\n2.5\n2\nnothing\nnothing\nnothing\n"
        "2\n1.5\n2.5\n4\n9.5\n6\n0.5\n7.5\n9.5\n5\nnothing\nyes\n4\n2.5\nno\n0.5\n2.5\n2.5\n0.5\n0\n"
        "yes\nyes\nyes\nyes\nno\nyes\n2\n1\n1\n2\nyes\nno\nnothing\n2\nno\nyes\n4\nno\n6\nno\nyes\nyes\n5\nnothing\nyes\n4\nyes\nyes\n0\nyes\nno\nnothing\nnothing\nnothing\nnothing\nno\nno\nyes\n0\nno\nno\nyes\nyes\n0\n"
        "2\n5\n6\n3\nalpha|beta\n3\n2\n2.75\n3\n2\nyes\nno\n3\n")


def test_bundled_std_map_package_runs(workdir):
    src = '''include "std/map"

to main:
    let scores be a map from text to number
    set item "ada" of scores to 36
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

    let labels be a map from text to text
    set item "a" of labels to "alpha"
    say (text_at with labels, "a")
    say (text_or with labels, "b", "missing")
    say (take_text_at with labels, "a")
    say length of labels
    say (take_text_at with labels, "b")
    set item "b" of labels to "bravo"
    clear_text_map with labels
    say length of labels
    say (text_at with labels, "b")

    let prices be a map from text to decimal
    set item "tea" of prices to 2.5
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

    let flags be a map from text to yesno
    set item "ready" of flags to yes
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

    let seats be a map from number to number
    set item 7 of seats to 42
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

    let names be a map from number to text
    set item 1 of names to "one"
    say (number_key_text_at with names, 1)
    say (number_key_text_or with names, 2, "missing")
    say (take_number_key_text_at with names, 1)
    say length of names
    say (take_number_key_text_at with names, 2)
    set item 2 of names to "two"
    clear_number_key_text_map with names
    say length of names
    say (number_key_text_at with names, 2)

    let ratios be a map from number to decimal
    set item 2 of ratios to 0.5
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

    let switches be a map from number to yesno
    set item 1 of switches to yes
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
'''
    proc = run_program(workdir, "bundled_std_map", src)
    assert proc.stdout == (
        "36\nnothing\n0\n37\n1\n37\n1\nnothing\nnothing\n1\n0\nnothing\n"
        "alpha\nmissing\nalpha\n0\nnothing\n0\nnothing\n"
        "2.5\nnothing\n0\n2.5\n0\nnothing\n0\nnothing\n"
        "yes\nnothing\nno\nyes\n0\nnothing\n0\nnothing\n"
        "42\nnothing\n0\n43\n1\n43\n1\nnothing\nnothing\n0\nnothing\n"
        "one\nmissing\none\n0\nnothing\n0\nnothing\n"
        "0.5\nnothing\n1\n0.5\n0\nnothing\n0\nnothing\n"
        "yes\nnothing\nno\nyes\n0\nnothing\n0\nnothing\n")


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
