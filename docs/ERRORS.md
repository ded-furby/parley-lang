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

**How to fix it:** Check the path (it is relative to the including file) and make sure the file exists and is not included in a cycle.

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

## P209 — Name already in use

**What it means:** A `let` reuses a name that already exists in this scope (or shadows a function).

**How to fix it:** Use `set name to …` to change an existing variable, or pick a new name.

## P210 — Missing or malformed `to main:`

**What it means:** Every program starts at `to main:`, which takes no parameters and gives nothing back.

**How to fix it:** Add `to main:` with the program body indented underneath.

## P211 — Variable used before it exists

**What it means:** `set` changes an existing variable, but this one was never created.

**How to fix it:** Create it first with `let name be …`.

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

**What it means:** `item … of …`, `add … to …`, `keys of` and friends only work on lists, maps, or text as documented.

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

**What it means:** `stop` ends the nearest loop and `skip` jumps to its next turn, so they need a loop around them.

**How to fix it:** Use them inside while/repeat/for each, or use `give back` to leave a function.

## P312 — Bad range in a `when` arm

**What it means:** A range arm (`is 1 to 10:`) needs a numeric `when` subject, numeric literal ends, and the smaller value first.

**How to fix it:** Make sure the `when` is over number or decimal, the ends are plain literals of the matching type, and the low end comes first.

## P313 — Cannot be used as a function value

**What it means:** `the function name` turns a defined function into a value, but `main`, functions with `changing` parameters, and variables cannot be used that way.

**How to fix it:** Use `the function` only on plain defined functions. A variable that already holds a function value is used directly, without `the function`.

## P314 — Closure cannot change captured value

**What it means:** An anonymous function captures outside variables by value when it is created.

**How to fix it:** Read the captured value, store a new local value inside the function, or give back the changed value and assign it outside.

## P901 — The Rust backend rejected the program

**What it means:** The generated Rust did not compile. This usually means a Parley checker gap — the position points at the Parley line involved.

**How to fix it:** Simplify the line if possible, and please report this at https://github.com/ded-furby/parley-lang/issues with the program.

## P902 — Build tooling problem

**What it means:** cargo/rustc could not be run.

**How to fix it:** Install Rust from https://rustup.rs and make sure `cargo` is on PATH.
