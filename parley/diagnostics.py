"""Structured diagnostics — Parley's contract with agents.

Every error the toolchain can produce has a stable P-code, a plain-English
message, and (where possible) a hint that tells the author the exact fix.
`parley check --json` emits these as machine-readable JSON so an agent can
repair a program without parsing prose.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Diagnostic:
    code: str
    message: str
    file: str = ""
    line: int = 0
    col: int = 0
    hint: Optional[str] = None
    replacement: Optional[str] = None
    severity: str = "error"

    def to_dict(self) -> dict:
        return asdict(self)


class ParleyError(Exception):
    """Raised by any compiler stage; carries one or more diagnostics."""

    def __init__(self, diagnostics: list[Diagnostic]):
        self.diagnostics = diagnostics
        super().__init__(diagnostics[0].message if diagnostics else "error")


# ------------------------------------------------------------------ catalog

ERROR_CATALOG: dict[str, dict] = {
    # --- parse errors (P1xx)
    "P101": {
        "title": "Unexpected word or symbol",
        "explain": "The parser reached a word or symbol that does not fit the sentence it was reading.",
        "fix": "Check the hint for what was expected at this spot. Common causes: a missing ':' at the end of an if/while/to line, a reserved phrase used as a name, or a list/record value used inside arguments without parentheses.",
    },
    "P102": {
        "title": "Character Parley does not know",
        "explain": "The file contains a character that is not part of any Parley word, number, or string.",
        "fix": "Remove or replace the character. Strings use double quotes only.",
    },
    "P103": {
        "title": "Indentation problem",
        "explain": "A line is indented in a way that does not match any open block.",
        "fix": "Indent consistently (4 spaces per level is the convention). Every ':' opens a block that must be indented one level deeper.",
    },
    "P104": {
        "title": "Bad interpolation inside a string",
        "explain": "A {…} inside a string could not be read as an expression.",
        "fix": "Put a valid expression inside the braces, e.g. \"hello {name}\". Use {{ and }} for literal braces.",
    },
    "P105": {
        "title": "Include problem",
        "explain": "An `include \"file.par\"` line points to a file that cannot be loaded.",
        "fix": "Check the relative path, parley_modules/ package, or PARLEY_PATH root, and make sure the file exists and is not included in a cycle.",
    },
    # --- name errors (P2xx)
    "P201": {
        "title": "Unknown name",
        "explain": "A name was used that is not a variable in scope, a function, or an enum variant.",
        "fix": "Declare it first with `let name be …`, or fix the spelling (see the hint).",
    },
    "P202": {
        "title": "Unknown function",
        "explain": "A call was made to a function that is not defined anywhere in the program.",
        "fix": "Define it with `to name …:` or fix the spelling (see the hint).",
    },
    "P203": {
        "title": "Wrong number of arguments",
        "explain": "A function was called with more or fewer arguments than its definition takes.",
        "fix": "Match the call to the definition; the hint shows the expected parameters.",
    },
    "P204": {
        "title": "Unknown field",
        "explain": "A record was accessed or built with a field it does not have.",
        "fix": "Use one of the record's declared fields (listed in the hint).",
    },
    "P205": {
        "title": "Unknown type",
        "explain": "A type annotation names a record or enum that is not defined.",
        "fix": "Define the record/enum at the top of the file, or fix the spelling.",
    },
    "P206": {
        "title": "Construction does not match the record",
        "explain": "A record was built with missing, repeated, or extra fields.",
        "fix": "Give every declared field exactly once, in any order.",
    },
    "P207": {
        "title": "Duplicate definition",
        "explain": "Two records, enums, functions, or enum variants share the same name.",
        "fix": "Rename one of them. Enum variants share one global namespace so each variant name must be unique.",
    },
    "P208": {
        "title": "`when` does not cover every case",
        "explain": "A `when` over an enum must either name every variant or end with `otherwise:`.",
        "fix": "Add the missing variants (listed in the hint) or add an `otherwise:` arm.",
    },
    "P209": {
        "title": "Name already in use",
        "explain": "A `let` reuses a name that already exists in this scope (or shadows a function).",
        "fix": "Use `set name to …` to change an existing variable, or pick a new name.",
    },
    "P210": {
        "title": "Missing or malformed `to main:`",
        "explain": "Every program starts at `to main:`, which takes no parameters and gives nothing back.",
        "fix": "Add `to main:` with the program body indented underneath.",
    },
    "P211": {
        "title": "Variable used before it exists",
        "explain": "`set` changes an existing variable, but this one was never created.",
        "fix": "Create it first with `let name be …`.",
    },
    # --- type errors (P3xx)
    "P301": {
        "title": "Type mismatch",
        "explain": "A value of one type was put where a different type is required.",
        "fix": "The message names both types. Convert explicitly (text from …, number from …, decimal from …) or fix the value.",
    },
    "P302": {
        "title": "Operator used on the wrong types",
        "explain": "An operator like plus/times/contains was applied to types it does not work on.",
        "fix": "See the hint. To put values into text, use interpolation: \"total: {x}\".",
    },
    "P303": {
        "title": "Condition is not yes/no",
        "explain": "if/while/and/or/not need a yesno value.",
        "fix": "Use a comparison (is, is more than, …) or a yesno variable.",
    },
    "P304": {
        "title": "give back problem",
        "explain": "A function's `give back` does not match its `giving` type, or a path is missing one.",
        "fix": "Every path through a `giving` function must `give back` a value of the declared type.",
    },
    "P305": {
        "title": "changing argument must be a variable",
        "explain": "A parameter marked `changing` mutates the caller's variable, so the argument must be a plain variable of the same type.",
        "fix": "Pass a variable (not a literal or computed value).",
    },
    "P306": {
        "title": "item/contains used on the wrong type",
        "explain": "`item … of …`, `add … to …`, `keys of` and friends only work on lists, maps, or text as documented.",
        "fix": "See the hint for which operations this type supports.",
    },
    "P307": {
        "title": "value of needs a maybe",
        "explain": "`value of x` unwraps a `maybe` value; this x is not a maybe.",
        "fix": "Only use `value of` on results of things like `ask for a number`, `read file`, `number from`.",
    },
    "P308": {
        "title": "Cannot infer the type",
        "explain": "The right-hand side (like bare `nothing`) does not say what type the variable should be.",
        "fix": "Start from a real value, or get the maybe from an operation like `number from text`.",
    },
    "P309": {
        "title": "Map keys must be number or text",
        "explain": "Parley maps are deterministic; keys are limited to number or text.",
        "fix": "Use a number or text key.",
    },
    "P310": {
        "title": "Not allowed inside attempt",
        "explain": "`give back`, `stop`, and `skip` cannot jump out of an `attempt:` block.",
        "fix": "Set a variable inside the attempt and act on it afterwards.",
    },
    "P311": {
        "title": "stop/skip outside a loop",
        "explain": "`stop` ends the nearest loop and `skip` jumps to its next turn, so they need a loop around them.",
        "fix": "Use them inside while/repeat/for each, or use `give back` to leave a function.",
    },
    "P312": {
        "title": "Bad range in a `when` arm",
        "explain": "A range arm (`is 1 to 10:`) needs a numeric `when` subject, numeric literal ends, and the smaller value first.",
        "fix": "Make sure the `when` is over number or decimal, the ends are plain literals of the matching type, and the low end comes first.",
    },
    "P313": {
        "title": "Cannot be used as a function value",
        "explain": "`the function name` turns a defined function into a value, but `main`, functions with `changing` parameters, and variables cannot be used that way.",
        "fix": "Use `the function` only on plain defined functions. A variable that already holds a function value is used directly, without `the function`.",
    },
    "P314": {
        "title": "Closure cannot change captured value",
        "explain": "An anonymous function captures outside variables by value when it is created.",
        "fix": "Read the captured value, store a new local value inside the function, or give back the changed value and assign it outside.",
    },
    # --- residual Rust errors (P9xx)
    "P901": {
        "title": "The Rust backend rejected the program",
        "explain": "The generated Rust did not compile. This usually means a Parley checker gap — the position points at the Parley line involved.",
        "fix": "Simplify the line if possible, and please report this at https://github.com/ded-furby/parley-lang/issues with the program.",
    },
    "P902": {
        "title": "Build tooling problem",
        "explain": "cargo/rustc could not be run.",
        "fix": "Install Rust from https://rustup.rs and make sure `cargo` is on PATH.",
    },
}


def explain(code: str) -> str:
    entry = ERROR_CATALOG.get(code.upper())
    if not entry:
        known = ", ".join(sorted(ERROR_CATALOG))
        return f"Unknown code {code}. Known codes: {known}"
    return (
        f"{code.upper()} — {entry['title']}\n\n"
        f"What it means: {entry['explain']}\n"
        f"How to fix it: {entry['fix']}"
    )


# ------------------------------------------------------------------ rendering

def render_json(diags: list[Diagnostic]) -> str:
    return json.dumps(
        {"ok": not any(d.severity == "error" for d in diags),
         "diagnostics": [d.to_dict() for d in diags]},
        indent=2,
    )


def render_human(diags: list[Diagnostic], sources: dict[str, str]) -> str:
    """Pretty terminal output: location, source line, caret, message, hint."""
    out = []
    for d in diags:
        head = f"error[{d.code}]" if d.severity == "error" else f"warning[{d.code}]"
        loc = f"{d.file}:{d.line}" if d.file else ""
        out.append(f"{head}: {d.message}")
        if loc:
            out.append(f"  --> {loc}")
            src = sources.get(d.file)
            if src:
                lines = src.splitlines()
                if 1 <= d.line <= len(lines):
                    text = lines[d.line - 1]
                    out.append(f"   | {text}")
                    if d.col > 0:
                        out.append("   | " + " " * (d.col - 1) + "^")
        if d.hint:
            out.append(f"  hint: {d.hint}")
        if d.replacement:
            out.append(f"  try:  {d.replacement}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"
