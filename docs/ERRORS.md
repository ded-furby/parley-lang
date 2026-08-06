# Parley error codes

Every diagnostic Parley can produce has a stable code. `parley check program.par --json`
emits them machine-readably; `parley explain P204` prints the entry below in the terminal.

| Range | Stage |
|---|---|
| P1xx | reading the program (parse) |
| P2xx | names (variables, functions, fields, variants) |
| P3xx | types |
| P9xx | the Rust backend / tooling |

## P101 — Unexpected word or symbol

**What it means:** The parser reached a word or symbol that does not fit the sentence it was reading.

**How to fix it:** Check the hint for what was expected at this spot. Common causes: a missing ':' at the end of an if/while/to line, a reserved phrase used as a name, or a list/record value used inside arguments without parentheses.

## P102 — Character Parley does not know

**What it means:** The file contains a character that is not part of any Parley word, number, or string.

**How to fix it:** Remove or replace the character. Strings use double quotes only.

## P103 — Indentation problem

**What it means:** A line is indented in a way that does not match any open block.

**How to fix it:** Indent consistently (4 spaces per level is the convention). Every ':' opens a block that must be indented one level deeper.

## P104 — Bad interpolation inside a string

**What it means:** A {…} inside a string could not be read as an expression.

**How to fix it:** Put a valid expression inside the braces, e.g. "hello {name}". Use {{ and }} for literal braces.

## P105 — Include problem

**What it means:** An `include "file.par"` line points to a file that cannot be loaded.

**How to fix it:** Check the relative path, parley_modules/ package, or PARLEY_PATH root, and make sure the file exists and is not included in a cycle.

## P201 — Unknown name

**What it means:** A name was used that is not a variable in scope, a function, or an enum variant.

**How to fix it:** Declare it first with `let name be …`, or fix the spelling (see the hint).

## P202 — Unknown function

**What it means:** A call was made to a function that is not defined anywhere in the program.

**How to fix it:** Define it with `to name …:` or fix the spelling (see the hint).

## P203 — Wrong number of arguments

**What it means:** A function was called with more or fewer arguments than its definition takes.

**How to fix it:** Match the call to the definition; the hint shows the expected parameters.

## P204 — Unknown field

**What it means:** A record was accessed or built with a field it does not have.

**How to fix it:** Use one of the record's declared fields (listed in the hint).

## P205 — Unknown type

**What it means:** A type annotation names a record or enum that is not defined.

**How to fix it:** Define the record/enum at the top of the file, or fix the spelling.

## P206 — Construction does not match the record

**What it means:** A record was built with missing, repeated, or extra fields.

**How to fix it:** Give every declared field exactly once, in any order.

## P207 — Duplicate definition

**What it means:** Two records, enums, functions, or enum variants share the same name.

**How to fix it:** Rename one of them. Enum variants share one global namespace so each variant name must be unique.

## P208 — `when` does not cover every case

**What it means:** A `when` over an enum must either name every variant or end with `otherwise:`.

**How to fix it:** Add the missing variants (listed in the hint) or add an `otherwise:` arm.

## P209 — Invalid or reused name

**What it means:** A name is reserved Parley vocabulary, already exists in this scope, or shadows a function.

**How to fix it:** For reserved words, use the suggested specific name. For an existing variable, use `set name to …` or pick a new name.

## P210 — Missing or malformed `to main:`

**What it means:** Every program starts at `to main:`, which takes no parameters and gives nothing back.

**How to fix it:** Add `to main:` with the program body indented underneath.

## P211 — Variable used before it exists

**What it means:** An expression or field update refers to a variable that does not exist in this scope.

**How to fix it:** Create it first with `let name be …` or `set name to …`.

## P301 — Type mismatch

**What it means:** A value of one type was put where a different type is required.

**How to fix it:** The message names both types. Convert explicitly (text from …, number from …, decimal from …) or fix the value.

## P302 — Operator used on the wrong types

**What it means:** An operator like plus/times/contains was applied to types it does not work on.

**How to fix it:** See the hint. To put values into text, use interpolation: "total: {x}".

## P303 — Condition is not yes/no

**What it means:** if/while/and/or/not need a yesno value.

**How to fix it:** Use a comparison (is, is more than, …) or a yesno variable.

## P304 — give back problem

**What it means:** A function's `give back` does not match its `giving` type, or a path is missing one.

**How to fix it:** Every path through a `giving` function must `give back` a value of the declared type.

## P305 — changing argument must be a variable

**What it means:** A parameter marked `changing` mutates the caller's variable, so the argument must be a plain variable of the same type.

**How to fix it:** Pass a variable (not a literal or computed value).

## P306 — item/contains used on the wrong type

**What it means:** `item … of …`, `add … to …`, `keys of`, `values of`, and friends only work on lists, maps, or text as documented.

**How to fix it:** See the hint for which operations this type supports.

## P307 — value of needs a maybe

**What it means:** `value of x` unwraps a `maybe` value; this x is not a maybe.

**How to fix it:** Only use `value of` on results of things like `ask for a number`, `read file`, `number from`.

## P308 — Cannot infer the type

**What it means:** The right-hand side (like bare `nothing`) does not say what type the variable should be.

**How to fix it:** Start from a real value, or get the maybe from an operation like `number from text`.

## P309 — Map keys must be number or text

**What it means:** Parley maps are deterministic; keys are limited to number or text.

**How to fix it:** Use a number or text key.

## P310 — Not allowed inside attempt

**What it means:** `give back`, `stop`, and `skip` cannot jump out of an `attempt:` block.

**How to fix it:** Set a variable inside the attempt and act on it afterwards.

## P311 — stop/skip outside a loop

**What it means:** `stop` ends the nearest loop (or leaves `main`) and `skip` jumps to a loop's next turn.

**How to fix it:** Use them inside while/repeat/for each; use `stop` only in `main`, or `give back` to leave another function.

## P312 — Bad range in a `when` arm

**What it means:** A range arm (`is 1 to 10:`) needs a numeric `when` subject, numeric literal ends, and the smaller value first.

**How to fix it:** Make sure the `when` is over number or decimal, the ends are plain literals of the matching type, and the low end comes first.

## P313 — Cannot be used as a function value

**What it means:** `the function name` turns a defined function into a value, but `main`, functions with `changing` parameters, and variables cannot be used that way.

**How to fix it:** Use `the function` only on plain defined functions. A variable that already holds a function value is used directly, without `the function`.

## P314 — Closure cannot change captured value

**What it means:** An anonymous function captures outside variables by value when it is created.

**How to fix it:** Read the captured value, store a new local value inside the function, or give back the changed value and assign it outside.

## P212 — Top-level statements and `to main:` in one file

**What it means:** Statements written at the top level are the body of `main`, so a file that uses them cannot also define `to main:`.

**How to fix it:** Pick one shape: keep the top-level statements and delete the `to main:` line, or move every top-level statement inside `to main:`.

## P213 — Loose statements in an included file

**What it means:** An included file may define functions, records, and enums. Top-level statements belong to the file you actually run.

**How to fix it:** Move the statements into a `to name:` function in the included file and call it from the entrypoint.

## P316 — Cannot sort by that

**What it means:** `sorted xs by field` orders a list of records by one of their fields, and the field must be a number, decimal, text, or yesno.

**How to fix it:** Sort a list of records by an ordered field, or use plain `sorted xs` for a list of numbers, decimals, or text.

## P317 — Arithmetic goes past the number range

**What it means:** A whole number in Parley is a 64-bit signed integer, and this expression's result provably falls outside it.

**How to fix it:** Keep whole-number arithmetic between -9223372036854775808 and 9223372036854775807, or use `decimal` values when a wider range matters. At runtime, an overflow stops the program rather than wrapping.

## P903 — Cannot write the built binary

**What it means:** The program compiled, but the finished binary could not be copied to the requested output path.

**How to fix it:** Choose an output path in a directory you can write to, and make sure the name is not an existing directory or a protected device file.

## P315 — `otherwise` fallback on a value that is always there

**What it means:** `x otherwise y` supplies the value to use when `x` is nothing, so `x` must be a maybe.

**How to fix it:** Remove the `otherwise …` when the value is not a maybe. Use it on results that can be nothing, such as `ask for a number`, a maybe lookup, or a function that gives back `nothing`.

## P317 — Value cannot cross JSON

**What it means:** JSON carries number, decimal, text, yesno, kinds, lists, text-keyed maps, and records built from those. Function values, number-keyed maps, and records that contain themselves have no JSON form.

**How to fix it:** Convert the value into a record of JSON-safe fields first, or change a number-keyed map to a text-keyed one.

## P710 — Web route names a missing handler

**What it means:** A route manifest points to a function that is not defined.

**How to fix it:** Add the named function or correct the route's `handler` field.

## P711 — Web handler has no response type

**What it means:** A typed route handler must give back a JSON response value.

**How to fix it:** Add a `giving` type and give back that value on every path.

## P712 — Web response is not JSON-safe

**What it means:** The response contains an unsupported boundary type.

**How to fix it:** Use JSON-safe scalars, maybes, lists, text-keyed maps, records, or kinds.

## P713 — Unsupported web handler signature

**What it means:** The function has too many, changing, or incorrectly ordered parameters.

**How to fix it:** Use no parameters, one typed body, `web_request`, or `web_request` followed by one typed body.

## P714 — Malformed web_request record

**What it means:** The record does not match the stable HTTP metadata contract.

**How to fix it:** Declare the exact method, path, query, headers, and body fields in [WEB.md](WEB.md).

## P715 — Web request body is not JSON-safe

**What it means:** The body parameter contains a value the generated boundary cannot decode.

**How to fix it:** Use the supported JSON types documented in [WEB.md](WEB.md).

## P720 — Browser export names a missing function

**What it means:** `browser.exports` points to a function that is not defined.

**How to fix it:** Add the function or correct the manifest.

## P721 — Unsupported browser return type

**What it means:** The first stable browser ABI returns only scalar values.

**How to fix it:** Return `number`, `decimal`, or `yesno`.

## P722 — Unsupported browser parameter

**What it means:** The export has a changing or non-scalar parameter.

**How to fix it:** Use non-changing `number`, `decimal`, and `yesno` parameters.

## P723 — Browser export is not deterministic

**What it means:** The exported call graph uses platform I/O, randomness, runtime failure state, or dynamic function values.

**How to fix it:** Move those effects outside the exported calculation.

## P724 — Browser build target is missing

**What it means:** The project declares browser exports but Rust's browser target is not installed.

**How to fix it:** Run `rustup target add wasm32-unknown-unknown` once, then build again.

## P901 — The Rust backend rejected the program

**What it means:** The generated Rust did not compile. This usually means a Parley checker gap — the position points at the Parley line involved.

**How to fix it:** Simplify the line if possible, and please report this at https://github.com/ded-furby/parley-lang/issues with the program.

## P902 — Build tooling problem

**What it means:** cargo/rustc could not be run.

**How to fix it:** Install Rust from https://rustup.rs and make sure `cargo` is on PATH.
