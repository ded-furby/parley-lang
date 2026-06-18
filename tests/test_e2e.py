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
    if t starts with "The" and t ends with "Fox":
        say "framed"
    say "quick" contains "ick"
'''
    proc = run_program(workdir, "text_toolbox", src)
    assert proc.stdout == (
        "the quick fox\nTHE QUICK FOX\n13\ndesserts\nframed\nyes\n")


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


def test_map_operations(workdir):
    src = '''to main:
    let m be a map from number to text
    set item 1 of m to "one"
    set item 2 of m to "two"
    say length of m
    remove item 1 of m
    say length of m
    say m contains 2
    say m contains 1
'''
    proc = run_program(workdir, "map_ops", src)
    assert proc.stdout == "2\n1\nyes\nno\n"


def test_uncaught_error_is_english_and_exit_1(workdir):
    src = '''to main:
    let xs be a list of 1
    say item 5 of xs
'''
    proc = run_program(workdir, "boom", src, expect_ok=False)
    assert proc.returncode == 1
    assert "The program stopped: There is no item 5 — the list has 1 item(s)." in proc.stderr


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
    say (is_blank with "   ")
    say (repeated_text with "ha", 3)
'''
    proc = run_program(workdir, "bundled_std", src)
    assert proc.stdout == "10\nyes\nhahaha\n"


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
    let words be a list of "red", "blue", "red"
    say (first_text with words)
    say (last_text with words)
    say (count_text with words, "red")
    say (index_text with words, "green")
'''
    proc = run_program(workdir, "bundled_std_list", src)
    assert proc.stdout == (
        "4\n8\n4.5\n2\n4\nnothing\nred\nred\n2\nnothing\n")


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
