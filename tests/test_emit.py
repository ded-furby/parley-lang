"""Emitter tests: the generated Rust uses the mappings the docs promise."""

from conftest import emit_text


def test_clone_on_assign_for_heap_types():
    rust = emit_text(
        "to main:\n"
        "    let first_list be a list of 1, 2\n"
        "    let second_list be first_list\n"
        "    say second_list\n")
    assert "first_list.clone()" in rust


def test_numbers_are_copied_not_cloned():
    rust = emit_text(
        "to main:\n"
        "    let x be 1\n"
        "    let y be x\n"
        "    say y\n")
    assert "x.clone()" not in rust


def test_changing_param_is_mut_ref():
    rust = emit_text(
        "to bump with changing n as number:\n"
        "    set n to n plus 1\n"
        "to main:\n"
        "    let c be 0\n"
        "    bump with c\n"
        "    say c\n")
    assert "n: &mut i64" in rust
    assert "bump(&mut c)" in rust
    assert "(*n) = " in rust


def test_read_only_heap_param_is_borrowed():
    rust = emit_text(
        "to count with xs as list of number giving number:\n"
        "    give back length of xs\n"
        "to main:\n"
        "    let values be a list of 1, 2, 3\n"
        "    say (count with values)\n")
    assert "fn count(xs: &Vec<i64>) -> i64" in rust
    assert "count(&(values))" in rust
    assert "count(values.clone())" not in rust
    assert "let mut xs" not in rust


def test_mutated_heap_param_clones_inside_function():
    rust = emit_text(
        "to changed_size with xs as list of number giving number:\n"
        "    add 4 to xs\n"
        "    give back length of xs\n"
        "to main:\n"
        "    let values be a list of 1, 2, 3\n"
        "    say (changed_size with values)\n")
    assert "fn changed_size(xs: &Vec<i64>) -> i64" in rust
    assert "let mut xs: Vec<i64> = (*xs).clone();" in rust
    assert "changed_size(&(values))" in rust
    assert "changed_size(values.clone())" not in rust


def test_enum_becomes_match():
    rust = emit_text(
        "a mood is one of happy, grumpy\n"
        "to main:\n"
        "    let m be happy\n"
        "    when m:\n"
        "        is happy:\n"
        "            say 1\n"
        "        is grumpy:\n"
        "            say 2\n")
    assert "enum Mood" in rust
    assert "Mood::Happy => {" in rust
    assert "match " in rust


def test_record_becomes_struct():
    rust = emit_text(
        "a point has x as number, y as number\n"
        "to main:\n"
        "    let p be a point with x 1, y 2\n"
        "    say p's x\n")
    assert "struct Point {" in rust
    assert "Point { x: 1i64, y: 2i64 }" in rust


def test_interpolation_becomes_format():
    rust = emit_text('to main:\n    let n be 3\n    say "n is {n}"\n')
    assert 'format!("n is {}"' in rust


def test_text_replacement_emits_rust_replace():
    rust = emit_text('to main:\n    say "a-b-a" replacing "-" with ":"\n')
    assert ".replace((" in rust
    assert ').as_str(), (' in rust


def test_text_position_emits_utf8_safe_helper():
    rust = emit_text('to main:\n    say position of "c" in "écart"\n')
    assert "fn parley_position" in rust
    assert "parley_position(&(" in rust


def test_division_is_guarded_and_decimal():
    rust = emit_text("to main:\n    say 10 divided by 4\n")
    assert "parley_div" in rust


def test_one_based_indexing_uses_helper():
    rust = emit_text(
        "to main:\n"
        "    let xs be a list of 1, 2\n"
        "    say item 1 of xs\n")
    assert "parley_item" in rust


def test_rust_keyword_names_are_mangled():
    rust = emit_text(
        "to main:\n"
        "    let loop be 1\n"
        "    let match be 2\n"
        "    say loop plus match\n")
    assert "let mut loop_p: i64" in rust
    assert "let mut match_p: i64" in rust


def test_rust_reserved_type_names_are_prefixed():
    rust = emit_text(
        "a string has x as number\n"
        "to main:\n"
        "    let s be a string with x 1\n"
        "    say s's x\n")
    assert "struct PString" in rust


def test_number_promotes_to_decimal():
    rust = emit_text(
        "to main:\n"
        "    let d be 1.5\n"
        "    set d to 2\n"
        "    say d\n")
    assert "as f64" in rust


def test_attempt_is_catch_unwind():
    rust = emit_text(
        "to main:\n"
        "    attempt:\n"
        "        say 1 divided by 0\n"
        "    if it failed:\n"
        "        say the error\n")
    assert "catch_unwind" in rust
    assert "parley_last_error()" in rust


def test_fail_statement_emits_runtime_failure():
    rust = emit_text('to main:\n    fail "custom failure"\n')
    assert 'panic!("{}", "custom failure".to_string());' in rust


def test_assert_statement_emits_guarded_runtime_failure():
    rust = emit_text('to main:\n    assert no, "custom failure"\n')
    assert 'if !(false)' in rust
    assert 'panic!("{}", "custom failure".to_string());' in rust


def test_assert_statement_without_message_uses_default_failure():
    rust = emit_text("to main:\n    assert no\n")
    assert 'panic!("{}", "Assertion failed.".to_string());' in rust


def test_main_catches_panics_in_english():
    rust = emit_text("to main:\n    say 1\n")
    assert "The program stopped" in rust
    assert "fn main_p()" in rust


def test_linemap_points_at_parley_lines():
    from parley.checker import check_program
    from parley.emit_rust import emit_program
    from parley.parser import parse

    program = parse("to main:\n    say 1\n    say 2\n")
    assert not check_program(program)
    rust, linemap = emit_program(program)
    lines = rust.splitlines()
    say_lines = sorted(i + 1 for i, l in enumerate(lines)
                       if l.strip().startswith("println!"))
    assert linemap[say_lines[0]] == 2
    assert linemap[say_lines[1]] == 3


# ------------------------------------------------------------------ v0.2: when patterns + function values

def test_multi_value_enum_arm_emits_or_patterns():
    rust = emit_text(
        "a mood is one of happy, grumpy, sleepy\n"
        "to main:\n"
        "    let m be happy\n"
        "    when m:\n"
        "        is happy, sleepy:\n"
        "            say 1\n"
        "        is grumpy:\n"
        "            say 2\n")
    assert "Mood::Happy | Mood::Sleepy =>" in rust


def test_range_arm_emits_bounds_check():
    rust = emit_text(
        "to main:\n"
        "    when 15:\n"
        "        is 10 to 20:\n"
        "            say 1\n"
        "        otherwise:\n"
        "            say 2\n")
    assert ">= 10i64" in rust and "<= 20i64" in rust


def test_decimal_when_uses_float_literals():
    rust = emit_text(
        "to main:\n"
        "    let x be 2.5\n"
        "    when x:\n"
        "        is 3:\n"
        "            say 1\n"
        "        otherwise:\n"
        "            say 2\n")
    assert "== 3.0f64" in rust


def test_function_value_is_rc_dyn_fn():
    rust = emit_text(
        "to double with x as number giving number:\n"
        "    give back x times 2\n"
        "to apply with f as (function taking number giving number) giving number:\n"
        "    give back (f with 21)\n"
        "to main:\n"
        "    let d be the function double\n"
        "    say (apply with d)\n")
    assert "Rc<dyn Fn(i64) -> i64>" in rust
    assert "Rc::new(move |arg1: i64| -> i64 { double(arg1) })" in rust
    assert "f(21i64)" in rust


def test_closure_emits_rc_dyn_fn_with_move_capture():
    rust = emit_text(
        "to main:\n"
        "    let offset be 7\n"
        "    let add_offset be a function taking x as number giving number:\n"
        "        give back x plus offset\n"
        "    say (add_offset with 5)\n"
    )
    assert "Rc<dyn Fn(i64) -> i64>" in rust
    assert "Rc::new(move |x: i64|" in rust
    assert "x plus offset" not in rust
