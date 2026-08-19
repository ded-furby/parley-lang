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


def test_natural_and_helper_mutates_list_argument_by_reference():
    rust = emit_text(
        "to append_pair with low as number and high as number and parts as list of text:\n"
        "    add \"{low}-{high}\" to parts\n"
        "to main:\n"
        "    let parts be an empty list of text\n"
        "    append_pair with 1 and 3 and parts\n"
        "    say parts joined with \",\"\n"
    )
    assert "parts: &mut Vec<String>" in rust
    assert "append_pair(1i64, 3i64, &mut parts)" in rust


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


def test_program_inputs_emit_their_helpers():
    rust = emit_text('to main:\n    say the arguments\n    say the input\n')
    assert "std::env::args().skip(1)" in rust
    # `the input` is a value: stdin is drained once and cached.
    assert "INPUT_LINES" in rust
    assert "read_to_string" in rust


def test_maybe_item_uses_the_non_failing_helpers():
    rust = emit_text('to main:\n'
                     '    let xs be a list of 1, 2\n'
                     '    say (maybe item 9 of xs) otherwise 0\n')
    assert "parley_maybe_item(" in rust
    assert "fn parley_maybe_item" in rust


def test_map_display_sorts_keys_instead_of_using_debug():
    rust = emit_text('to main:\n'
                     '    let m be a map from text to number\n'
                     '    say m\n')
    assert "__ks.sort_by" in rust
    assert '"{:?}", &(m)' not in rust


def test_list_of_numbers_still_uses_rust_debug():
    rust = emit_text('to main:\n    say (a list of 1, 2)\n')
    assert "{:?}" in rust
    assert "__ks.sort_by" not in rust


def test_sorted_by_emits_stable_sort_on_the_field():
    rust = emit_text('a person has name as text, age as number\n'
                     'to main:\n'
                     '    let people be an empty list of person\n'
                     '    sort people by age\n')
    assert "__s.sort_by(|a, b| a.age.partial_cmp(&b.age)" in rust
    # sort_by, not sort_unstable_by: equal keys must keep source order.
    assert "sort_unstable" not in rust


def test_generic_function_is_monomorphized_once_per_type():
    rust = emit_text('to head_or with xs as list of any item, d as any item giving any item:\n'
                     '    give back (maybe item 1 of xs) otherwise d\n'
                     'say (head_or with (a list of 1), 0)\n'
                     'say (head_or with (a list of 2), 0)\n'
                     'say (head_or with (a list of "a"), "z")\n')
    # Two concrete copies for two types, not one per call site.
    assert rust.count("fn head_or__") == 2
    assert "fn head_or__number(xs: &Vec<i64>, d: i64) -> i64" in rust
    assert "fn head_or__text(xs: &Vec<String>, d: &String) -> String" in rust
    # Nothing generic survives into the Rust.
    assert "any item" not in rust


def test_json_decode_and_encode_emit_serde():
    rust = emit_text('a config has name as text\n'
                     'let c be a config from json "x"\n'
                     'say (value of c) as json\n')
    assert "serde_json::from_str::<Config>" in rust
    assert "serde_json::to_string" in rust
    assert "serde::Serialize, serde::Deserialize" in rust
    assert "deny_unknown_fields" in rust


def test_maybe_json_field_defaults_to_nothing_when_absent():
    rust = emit_text('a author has name as text, email as maybe text\n'
                     'let a_value be a author from json "x"\n')
    assert "#[serde(default)]" in rust


def test_maps_emit_as_btreemap_so_every_ordering_agrees():
    rust = emit_text('to main:\n'
                     '    let m be a map from text to number\n'
                     '    say keys of m\n')
    assert "BTreeMap" in rust
    assert "HashMap" not in rust
    # BTreeMap is ordered, so the key helpers no longer sort by hand.
    assert "fn parley_keys<K: Ord + Clone, V>(m: &BTreeMap<K, V>) -> Vec<K> {\n    m.keys().cloned().collect()\n}" in rust


def test_otherwise_emits_lazy_match():
    rust = emit_text('to main:\n    say (number from "5") otherwise 0\n')
    assert "Some(__v) => __v, None => 0i64" in rust


def test_otherwise_clones_a_place_instead_of_moving_it():
    rust = emit_text('to main:\n    let s be some "x"\n'
                     '    say s otherwise "y"\n    say s otherwise "z"\n')
    assert rust.count("match (s.clone())") == 2


def test_otherwise_promotes_whole_number_fallback():
    rust = emit_text('to main:\n    let d be some 2.5\n    say d otherwise 1\n')
    assert "None => ((1i64) as f64)" in rust


def test_text_position_emits_utf8_safe_helper():
    rust = emit_text('to main:\n    say position of "c" in "écart"\n')
    assert "fn parley_position" in rust
    assert "parley_position(&(" in rust


def test_contextual_position_identifier_emits_as_an_ordinary_variable():
    rust = emit_text(
        "to main:\n"
        "    let values be a list of 10, 20\n"
        "    for each position from 1 to length of values:\n"
        "        say item position of values\n"
    )
    assert "for position in" in rust
    assert "parley_item(&(values), position)" in rust


def test_contextual_number_names_emit_without_changing_number_types():
    rust = emit_text(
        "a reading has number as number\n"
        "to double with number as number giving number:\n"
        "    give back number times 2\n"
        "to main:\n"
        "    let reading_value be a reading with number 3\n"
        "    say reading_value's number\n"
        "    for each number from 1 to 2:\n"
        "        say (double with number)\n"
    )
    assert "number: i64" in rust
    assert "fn double(number: i64) -> i64" in rust
    assert "for number in" in rust

    function_rust = emit_text(
        "to number with value as number giving number:\n"
        "    give back value\n"
        "to main:\n"
        "    say (number with 9)\n"
    )
    assert "fn number(value: i64) -> i64" in function_rust
    assert "number(9i64)" in function_rust


def test_changed_loop_variables_emit_mutable_bindings_only_when_needed():
    rust = emit_text(
        "to main:\n"
        "    for each changed_index from 1 to 2:\n"
        "        set changed_index to changed_index plus 10\n"
        "    for each stable_index from 1 to 2:\n"
        "        say stable_index\n"
        "    let values be a list of 3, 4\n"
        "    for each changed_value in values:\n"
        "        set changed_value to changed_value times 2\n"
    )
    assert "for mut changed_index in" in rust
    assert "for stable_index in" in rust
    assert "for mut changed_value in" in rust


def test_modulo_alias_emits_through_existing_guarded_remainder_helper():
    rust = emit_text("to main:\n    say -5 modulo 3\n")
    assert "parley_rem((-(5i64)), 3i64)" in rust
    assert rust.count("fn parley_rem(") == 1


def test_text_count_emits_utf8_safe_helper():
    rust = emit_text('to main:\n    say count of "a" in "banana"\n')
    assert "fn parley_count" in rust
    assert "parley_count(&(" in rust


def test_map_values_emit_sorted_helper():
    rust = emit_text(
        "to main:\n"
        "    let scores be a map from text to number\n"
        '    set item "grace" of scores to 42\n'
        '    set item "ada" of scores to 36\n'
        "    say values of scores\n")
    assert "fn parley_values" in rust
    assert "parley_values(&(" in rust


def test_division_is_guarded_and_decimal():
    rust = emit_text("to main:\n    say 10 divided by 4\n")
    assert "parley_div" in rust


def test_one_based_indexing_uses_helper():
    rust = emit_text(
        "to main:\n"
        "    let xs be a list of 1, 2\n"
        "    say item 1 of xs\n")
    assert "parley_item" in rust


def test_list_item_mutations_evaluate_arguments_before_mutable_borrow():
    rust = emit_text(
        "to main:\n"
        "    let xs be a list of 10, 20\n"
        "    set item (length of xs) of xs to item 1 of xs\n"
        "    remove item (length of xs) of xs\n")
    set_call = rust.index("parley_set_item(&mut xs")
    remove_call = rust.index("parley_remove(&mut xs")
    assert rust.index("let __index1 = ((xs).len() as i64);") < set_call
    assert rust.index("let __value2 = parley_item(&(xs), 1i64);") < set_call
    assert rust.index("let __index3 = ((xs).len() as i64);") < remove_call
    assert "parley_set_item(&mut xs, (xs).len()" not in rust
    assert "parley_remove(&mut xs, (xs).len()" not in rust


def test_map_item_mutations_evaluate_arguments_before_mutable_borrow():
    rust = emit_text(
        "to main:\n"
        "    let scores be a map from number to number\n"
        "    set item (length of scores) of scores to length of scores\n"
        "    remove item (length of scores) of scores\n")
    insert_call = rust.index("(scores).insert(__index1, __value2);")
    remove_call = rust.index("(scores).remove(&__index3);")
    assert rust.index("let __index1 = ((scores).len() as i64);") < insert_call
    assert rust.index("let __value2 = ((scores).len() as i64);") < insert_call
    assert rust.index("let __index3 = ((scores).len() as i64);") < remove_call


def test_text_indexing_uses_utf8_helper():
    rust = emit_text('to main:\n    say item 2 of "éc"\n')
    assert "fn parley_text_item" in rust
    assert "parley_text_item(&(" in rust


def test_rust_keyword_names_are_mangled():
    rust = emit_text(
        "to main:\n"
        "    let loop be 1\n"
        "    let match be 2\n"
        "    say loop plus match\n")
    assert "let mut px_loop: i64" in rust
    assert "let mut px_match: i64" in rust


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
    assert "fn px_main()" in rust


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
