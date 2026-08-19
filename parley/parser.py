"""Parley parser: source text → AST.

Pipeline pieces that live here:
  * load_program  — reads a .par file, splices `include "…"` lines, and builds
                    a SourceMap so every diagnostic points at the original file.
  * parse         — Lark (LALR + indenter) parse + transform into ast_nodes.
  * friendly parse errors — lark's expected-token sets are translated into
                    plain English with hints (reserved phrases, missing ':').
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError, UnexpectedCharacters, UnexpectedToken, VisitError
from lark.indenter import Indenter

from . import ast_nodes as A
from .diagnostics import Diagnostic, ParleyError


# ------------------------------------------------------------------ sources

@dataclass
class SourceMap:
    """Maps lines of the combined (include-expanded) text to original files."""

    entries: list[tuple[str, int]]          # combined line (1-based) -> (file, line)
    sources: dict[str, str]                 # file -> original text
    main_file: str

    def loc(self, combined_line: int) -> tuple[str, int]:
        if 1 <= combined_line <= len(self.entries):
            return self.entries[combined_line - 1]
        return self.main_file, max(combined_line, 1)

    def resolve(self, diags: list[Diagnostic]) -> list[Diagnostic]:
        for d in diags:
            if not d.file:
                d.file, d.line = self.loc(d.line)
        return diags


INCLUDE_RE = re.compile(r'^\s*include\s+"([^"]+)"\s*((note:|#).*)?$')


def _display(p: Path) -> str:
    try:
        return str(p.relative_to(Path.cwd()))
    except ValueError:
        return str(p)


def _candidate_package_files(root: Path, name: str) -> list[Path]:
    target = root / name
    out = [target]
    if Path(name).suffix == "":
        out.append(target.with_suffix(".par"))
    out.append(target / "main.par")
    return out


def _include_roots(including_file: Path) -> list[Path]:
    roots = [including_file.parent / "parley_modules", Path(__file__).parent / "stdlib"]
    roots.extend(Path(p) for p in os.environ.get("PARLEY_PATH", "").split(os.pathsep) if p)
    return roots


def _resolve_include(name: str, including_file: Path) -> Path:
    raw = Path(name)
    if raw.is_absolute():
        return raw.resolve()
    relative = (including_file.parent / raw).resolve()
    candidates = [relative]
    if raw.suffix == "":
        candidates.append(relative.with_suffix(".par"))
    for root in _include_roots(including_file):
        candidates.extend(_candidate_package_files(root, name))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return relative


def load_program(path) -> tuple[str, SourceMap]:
    """Read a program and expand includes. Returns (combined_text, sourcemap)."""
    main = Path(path).resolve()
    out_lines: list[str] = []
    entries: list[tuple[str, int]] = []
    sources: dict[str, str] = {}
    # Splicing a file twice would redefine everything in it, so two modules
    # that each need the same helper file must not collide. A file already in
    # the current stack is still a cycle; one merely already spliced is a
    # diamond, and is simply skipped.
    spliced: set[Path] = set()

    def load(p: Path, stack: list[Path]):
        if p in stack:
            raise ParleyError([Diagnostic(
                "P105", f'"{p.name}" is included in a cycle (a file ends up including itself).',
                file=_display(p), line=1)])
        if p in spliced:
            return
        spliced.add(p)
        try:
            text = p.read_text()
        except OSError as e:
            where = _display(stack[-1]) if stack else _display(p)
            raise ParleyError([Diagnostic(
                "P105", f'Cannot read "{_display(p)}": {e.strerror or e}.',
                file=where, line=1,
                hint="Includes are relative to the including file, or to "
                     "parley_modules/ and PARLEY_PATH package roots.")])
        sources[_display(p)] = text
        for i, ln in enumerate(text.splitlines(), 1):
            m = INCLUDE_RE.match(ln)
            if m:
                load(_resolve_include(m.group(1), p), stack + [p])
            else:
                out_lines.append(ln)
                entries.append((_display(p), i))

    load(main, [])
    return "\n".join(out_lines) + "\n", SourceMap(entries, sources, _display(main))


# ------------------------------------------------------------------ lark setup

class ParleyIndenter(Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types = ["_LPAR"]
    CLOSE_PAREN_types = ["_RPAR"]
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 8


_GRAMMAR = (Path(__file__).parent / "grammar.lark").read_text()
_LARK = None


def _grammar_cache_path() -> Path:
    """Where the serialized LALR tables live for this exact grammar.

    Building the tables costs ~0.1 s — half of a `parley check` — and the
    grammar only changes with a Parley release, so the tables are cached per
    grammar hash (a grammar edit gets a fresh file automatically) and per
    lark version (the serialization format is lark's own).
    """
    import hashlib
    import lark as _lark_pkg

    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    key = hashlib.sha256(
        (_GRAMMAR + "\n" + _lark_pkg.__version__).encode()
    ).hexdigest()[:16]
    return Path(base) / "parley" / f"grammar-{key}.cache"


def _build_lark(cache: str | None) -> Lark:
    return Lark(
        _GRAMMAR,
        parser="lalr",
        postlex=ParleyIndenter(),
        propagate_positions=True,
        maybe_placeholders=True,
        start=["start", "rhs"],
        **({"cache": cache} if cache else {}),
    )


def _lark() -> Lark:
    global _LARK
    if _LARK is None:
        cache = _grammar_cache_path()
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            _LARK = _build_lark(str(cache))
        except Exception:
            # A corrupt or unwritable cache must never break parsing: drop it
            # and pay the one-off table build instead.
            try:
                cache.unlink(missing_ok=True)
            except OSError:
                pass
            _LARK = _build_lark(None)
    return _LARK


# ------------------------------------------------------------------ strings

def _split_string(raw: str, line: int, col: int) -> list:
    """Unescape a STRING token and split out {…} interpolations.

    Returns a list mixing plain `str` chunks and parsed Expr nodes.
    """
    inner = raw[1:-1]
    parts: list = []
    buf = []
    i = 0
    n = len(inner)
    while i < n:
        c = inner[i]
        if c == "\\" and i + 1 < n:
            nxt = inner[i + 1]
            buf.append({"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}.get(nxt, nxt))
            i += 2
        elif c == "{":
            if i + 1 < n and inner[i + 1] == "{":
                buf.append("{")
                i += 2
            else:
                # Scan to the matching '}' — escaped quotes (\") delimit inner
                # string literals, and a '}' inside one does not end the
                # interpolation. \" and \\ are unescaped for the sub-parser.
                j = i + 1
                expr_chars: list[str] = []
                in_string = False
                end = -1
                while j < n:
                    cj = inner[j]
                    if cj == "\\" and j + 1 < n:
                        nxt = inner[j + 1]
                        if nxt == '"':
                            in_string = not in_string
                            expr_chars.append('"')
                        elif nxt == "\\":
                            expr_chars.append("\\")
                        else:
                            expr_chars.append(cj)
                            expr_chars.append(nxt)
                        j += 2
                        continue
                    if cj == "}" and not in_string:
                        end = j
                        break
                    expr_chars.append(cj)
                    j += 1
                if end == -1:
                    raise ParleyError([Diagnostic(
                        "P104", "A '{' inside this string is never closed with '}'.",
                        line=line, col=col,
                        hint="Write {{ for a literal brace, or close the interpolation: \"{name}\".")])
                src = "".join(expr_chars).strip()
                if not src:
                    raise ParleyError([Diagnostic(
                        "P104", "There is an empty {} inside this string.",
                        line=line, col=col, hint="Put an expression inside: \"{count}\".")])
                if buf:
                    parts.append("".join(buf))
                    buf = []
                parts.append(_parse_snippet(src, line, col))
                i = end + 1
        elif c == "}":
            if i + 1 < n and inner[i + 1] == "}":
                buf.append("}")
                i += 2
            else:
                raise ParleyError([Diagnostic(
                    "P104", "There is a stray '}' inside this string.",
                    line=line, col=col, hint="Write }} for a literal brace.")])
        else:
            buf.append(c)
            i += 1
    if buf:
        parts.append("".join(buf))
    if not parts:
        parts.append("")
    return parts


def _retag(node, line: int, col: int):
    """Point an interpolated sub-expression's positions at the host string."""
    if isinstance(node, A.Node):
        node.line, node.col = line, col
        for v in vars(node).values():
            if isinstance(v, list):
                for x in v:
                    _retag(x, line, col)
            else:
                _retag(v, line, col)


def _transform(tree) -> "A.Node":
    """Run the AST transformer, unwrapping ParleyErrors from lark's VisitError."""
    try:
        return ToAst().transform(tree)
    except VisitError as ve:
        if isinstance(ve.orig_exc, ParleyError):
            raise ve.orig_exc
        raise


def _parse_snippet(src: str, line: int, col: int) -> A.Expr:
    try:
        tree = _lark().parse(src, start="rhs")
        node = _transform(tree)
    except ParleyError:
        raise
    except LarkError:
        raise ParleyError([Diagnostic(
            "P104", f"Could not read the expression inside {{{src}}}.",
            line=line, col=col,
            hint="Interpolations hold a normal Parley expression, e.g. \"{score plus 1}\".")])
    _retag(node, line, col)
    return node


# ------------------------------------------------------------------ transformer

def _pos(meta) -> dict:
    if getattr(meta, "empty", False):
        return {"line": 0, "col": 0}
    return {"line": meta.line, "col": meta.column}


@v_args(meta=True)
class ToAst(Transformer):
    # ---- program structure

    def start(self, meta, ch):
        prog = A.Program(records=[], enums=[], funcs=[], line=1, col=1)
        loose: list[A.Stmt] = []
        for it in ch:
            if isinstance(it, A.RecordDef):
                prog.records.append(it)
            elif isinstance(it, A.EnumDef):
                prog.enums.append(it)
            elif isinstance(it, A.FuncDef):
                prog.funcs.append(it)
            elif isinstance(it, A.Stmt):
                loose.append(it)
        if loose:
            first = loose[0]
            prog.funcs.append(A.FuncDef(
                name="main", params=[], ret=None, body=loose,
                line=getattr(first, "line", 1), col=getattr(first, "col", 1),
                implicit_main=True))
        return prog

    def item(self, meta, ch):
        return ch[0]

    def record_def(self, meta, ch):
        return A.RecordDef(name=str(ch[0]), fields=ch[1:], **_pos(meta))

    def field(self, meta, ch):
        return (str(ch[0]), ch[1])

    def enum_def(self, meta, ch):
        return A.EnumDef(name=str(ch[0]), variants=[str(v) for v in ch[1:]], **_pos(meta))

    def func_def(self, meta, ch):
        name, params, giving, body = ch
        return A.FuncDef(name=str(name), params=params, ret=giving, body=body, **_pos(meta))

    def params(self, meta, ch):
        params = [p for p in ch if isinstance(p, A.Param)]
        if any(str(item) == "and" for item in ch if item is not None):
            for param in params:
                param.natural_separator = True
        return params

    def param(self, meta, ch):
        changing, name, ty = ch
        return A.Param(name=str(name), type=ty, changing=changing is not None, **_pos(meta))

    def giving(self, meta, ch):
        return ch[0] if ch else None

    # ---- types

    def t_number(self, meta, ch):
        return A.TNum()

    def t_decimal(self, meta, ch):
        return A.TDec()

    def t_text(self, meta, ch):
        return A.TText()

    def t_yesno(self, meta, ch):
        return A.TBool()

    def t_list(self, meta, ch):
        return A.TList(ch[0])

    def t_map(self, meta, ch):
        return A.TMap(ch[0], ch[1])

    def t_maybe(self, meta, ch):
        return A.TMaybe(ch[0])

    def t_var(self, meta, ch):
        return A.TVar(str(ch[0]))

    def t_named(self, meta, ch):
        return A.TNamed(str(ch[0]))

    def t_func(self, meta, ch):
        # children: param types…, then the (possibly None) giving result;
        # an absent `taking` clause leaves a None placeholder to drop
        return A.TFunc(params=[t for t in ch[:-1] if t is not None], ret=ch[-1])

    # ---- statements

    def block(self, meta, ch):
        return list(ch)

    def let_stmt(self, meta, ch):
        return A.Let(name=str(ch[0]), value=ch[1], **_pos(meta))

    def set_stmt(self, meta, ch):
        return A.SetVar(target=ch[0], value=ch[1], **_pos(meta))

    def set_item_stmt(self, meta, ch):
        return A.SetItem(index=ch[0], target=ch[1], value=ch[2], **_pos(meta))

    def say_stmt(self, meta, ch):
        return A.Say(value=ch[0], **_pos(meta))

    def sort_stmt(self, meta, ch):
        name = str(ch[0])
        field = ch[1]
        pos = _pos(meta)
        target = A.Var(name=name, **pos)
        sorted_value = (
            A.SortedBy(value=target, field_name=str(field), **pos) if field is not None
            else A.PrefixOp(op="sorted", value=target, **pos))
        return A.SetVar(
            target=A.LValue(base=name, fields=[], **pos),
            value=sorted_value,
            **pos,
        )

    def sorted_by(self, meta, ch):
        return A.SortedBy(value=ch[0], field_name=str(ch[1]), **_pos(meta))

    def give_stmt(self, meta, ch):
        return A.Give(value=ch[0], **_pos(meta))

    def stop_stmt(self, meta, ch):
        return A.Stop(**_pos(meta))

    def skip_stmt(self, meta, ch):
        return A.Skip(**_pos(meta))

    def assert_stmt(self, meta, ch):
        message = ch[1] if len(ch) > 1 else None
        return A.Assert(cond=ch[0], message=message, **_pos(meta))

    def fail_stmt(self, meta, ch):
        return A.Fail(message=ch[0], **_pos(meta))

    def add_stmt(self, meta, ch):
        return A.Add(value=ch[0], target=ch[1], **_pos(meta))

    def remove_stmt(self, meta, ch):
        return A.RemoveItem(index=ch[0], target=ch[1], **_pos(meta))

    def write_stmt(self, meta, ch):
        return A.WriteFile(value=ch[0], path=ch[1], append=False, **_pos(meta))

    def append_stmt(self, meta, ch):
        return A.WriteFile(value=ch[0], path=ch[1], append=True, **_pos(meta))

    def call_stmt(self, meta, ch):
        return A.CallStmt(name=str(ch[0]), args=ch[1], **_pos(meta))

    def args(self, meta, ch):
        return [a for a in ch if a is not None]

    def if_stmt(self, meta, ch):
        arms = [(ch[0], ch[1])]
        otherwise = None
        for x in ch[2:]:
            if x is None:
                continue
            if isinstance(x, tuple):
                arms.append(x)
            else:
                otherwise = x
        return A.If(arms=arms, otherwise=otherwise, **_pos(meta))

    def elif_(self, meta, ch):
        return (ch[0], ch[1])

    def else_(self, meta, ch):
        return ch[0]

    def when_stmt(self, meta, ch):
        subject = ch[0]
        arms = []
        otherwise = None
        for x in ch[1:]:
            if x is None:
                continue
            if isinstance(x, tuple):
                arms.append(x)
            else:
                otherwise = x
        return A.When(subject=subject, arms=arms, otherwise=otherwise, **_pos(meta))

    def when_arm(self, meta, ch):
        pats = [p for p in ch[:-1] if p is not None]
        return (pats, ch[-1])

    def pat_range(self, meta, ch):
        return A.Pattern(kind="range", value=(ch[0], ch[1]), **_pos(meta))

    def pat_int(self, meta, ch):
        return A.Pattern(kind="int", value=int(ch[0]), **_pos(meta))

    def pat_neg_int(self, meta, ch):
        return A.Pattern(kind="int", value=-int(ch[0]), **_pos(meta))

    def pat_float(self, meta, ch):
        return A.Pattern(kind="dec", value=float(ch[0]), **_pos(meta))

    def pat_neg_float(self, meta, ch):
        return A.Pattern(kind="dec", value=-float(ch[0]), **_pos(meta))

    def pat_string(self, meta, ch):
        tok = ch[0]
        parts = _split_string(str(tok), tok.line, tok.column)
        if any(not isinstance(p, str) for p in parts):
            raise ParleyError([Diagnostic(
                "P104", "Strings in `when` patterns cannot contain {…} interpolations.",
                line=tok.line, col=tok.column)])
        return A.Pattern(kind="text", value="".join(parts), **_pos(meta))

    def pat_yes(self, meta, ch):
        return A.Pattern(kind="yes", value=None, **_pos(meta))

    def pat_no(self, meta, ch):
        return A.Pattern(kind="no", value=None, **_pos(meta))

    def pat_name(self, meta, ch):
        return A.Pattern(kind="name", value=str(ch[0]), **_pos(meta))

    def while_stmt(self, meta, ch):
        return A.While(cond=ch[0], body=ch[1], **_pos(meta))

    def repeat_stmt(self, meta, ch):
        return A.Repeat(count=ch[0], body=ch[1], **_pos(meta))

    def forrange_stmt(self, meta, ch):
        return A.ForRange(var=str(ch[0]), lo=ch[1], hi=ch[2], body=ch[3], **_pos(meta))

    def foreach_stmt(self, meta, ch):
        return A.ForEach(var=str(ch[0]), iter=ch[1], body=ch[2], **_pos(meta))

    def attempt_stmt(self, meta, ch):
        return A.Attempt(body=ch[0], handler=ch[1], **_pos(meta))

    def lvalue(self, meta, ch):
        return A.LValue(base=str(ch[0]), fields=[str(x) for x in ch[1:]], **_pos(meta))

    # ---- rhs-only constructs

    def list_lit(self, meta, ch):
        return A.ListLit(items=list(ch), **_pos(meta))

    def empty_list(self, meta, ch):
        return A.EmptyList(elem_type=ch[0], **_pos(meta))

    def empty_map(self, meta, ch):
        return A.EmptyMap(key_type=ch[0], val_type=ch[1], **_pos(meta))

    def construct(self, meta, ch):
        return A.Construct(record=str(ch[0]), inits=ch[1:], **_pos(meta))

    def field_init(self, meta, ch):
        return (str(ch[0]), ch[1])

    def closure_lit(self, meta, ch):
        return A.Closure(params=ch[0], ret=ch[1], body=ch[2], **_pos(meta))

    def closure_params(self, meta, ch):
        return [p for p in ch if p is not None]

    def closure_param(self, meta, ch):
        return A.Param(name=str(ch[0]), type=ch[1], changing=False, **_pos(meta))

    # ---- expressions

    def or_op(self, meta, ch):
        return A.BinOp(op="or", left=ch[0], right=ch[1], **_pos(meta))

    def and_op(self, meta, ch):
        return A.BinOp(op="and", left=ch[0], right=ch[1], **_pos(meta))

    def not_op(self, meta, ch):
        return A.Not(value=ch[0], **_pos(meta))

    def _cmp(self, meta, ch, op):
        return A.Compare(op=op, left=ch[0], right=ch[1], **_pos(meta))

    def eq(self, meta, ch):
        return self._cmp(meta, ch, "==")

    def ne(self, meta, ch):
        return self._cmp(meta, ch, "!=")

    def gt(self, meta, ch):
        return self._cmp(meta, ch, ">")

    def lt(self, meta, ch):
        return self._cmp(meta, ch, "<")

    def ge(self, meta, ch):
        return self._cmp(meta, ch, ">=")

    def le(self, meta, ch):
        return self._cmp(meta, ch, "<=")

    def has_no_value(self, meta, ch):
        return A.Compare(
            op="==", left=ch[0], right=A.NothingLit(**_pos(meta)), **_pos(meta)
        )

    def has_value(self, meta, ch):
        return A.Compare(
            op="!=", left=ch[0], right=A.NothingLit(**_pos(meta)), **_pos(meta)
        )

    def contains(self, meta, ch):
        return self._cmp(meta, ch, "contains")

    def startswith(self, meta, ch):
        return self._cmp(meta, ch, "startswith")

    def endswith(self, meta, ch):
        return self._cmp(meta, ch, "endswith")

    def split_by(self, meta, ch):
        return A.SplitBy(value=ch[0], sep=ch[1], **_pos(meta))

    def as_number(self, meta, ch):
        pos = _pos(meta)
        parsed = A.PrefixOp(op="number_from", value=ch[0], **pos)
        return A.PrefixOp(op="value", value=parsed, **pos)

    def as_text(self, meta, ch):
        return A.PrefixOp(op="text_from", value=ch[0], **_pos(meta))

    def joined_with(self, meta, ch):
        return A.JoinedWith(value=ch[0], sep=ch[1], **_pos(meta))

    def replacing_with(self, meta, ch):
        return A.ReplacingWith(value=ch[0], old=ch[1], new=ch[2], **_pos(meta))

    def otherwise_op(self, meta, ch):
        return A.Otherwise(value=ch[0], fallback=ch[1], **_pos(meta))

    def position_of(self, meta, ch):
        return A.PositionOf(needle=ch[0], value=ch[1], **_pos(meta))

    def count_of(self, meta, ch):
        return A.CountOf(needle=ch[0], value=ch[1], **_pos(meta))

    def _bin(self, meta, ch, op):
        return A.BinOp(op=op, left=ch[0], right=ch[1], **_pos(meta))

    def add_op(self, meta, ch):
        return self._bin(meta, ch, "+")

    def sub_op(self, meta, ch):
        return self._bin(meta, ch, "-")

    def mul_op(self, meta, ch):
        return self._bin(meta, ch, "*")

    def div_op(self, meta, ch):
        return self._bin(meta, ch, "/")

    def mod_op(self, meta, ch):
        return self._bin(meta, ch, "%")

    def pow_op(self, meta, ch):
        return self._bin(meta, ch, "pow")

    def neg(self, meta, ch):
        return A.Neg(value=ch[0], **_pos(meta))

    def _prefix(self, meta, ch, op):
        return A.PrefixOp(op=op, value=ch[0], **_pos(meta))

    def length_of(self, meta, ch):
        return self._prefix(meta, ch, "length")

    def sum_of(self, meta, ch):
        return self._prefix(meta, ch, "sum")

    def smallest_of(self, meta, ch):
        return self._prefix(meta, ch, "smallest")

    def largest_of(self, meta, ch):
        return self._prefix(meta, ch, "largest")

    def uppercase_of(self, meta, ch):
        return self._prefix(meta, ch, "upper")

    def lowercase_of(self, meta, ch):
        return self._prefix(meta, ch, "lower")

    def absolute_of(self, meta, ch):
        return self._prefix(meta, ch, "abs")

    def floor_of(self, meta, ch):
        return self._prefix(meta, ch, "floor")

    def ceiling_of(self, meta, ch):
        return self._prefix(meta, ch, "ceil")

    def sqrt_of(self, meta, ch):
        return self._prefix(meta, ch, "sqrt")

    def value_of(self, meta, ch):
        return self._prefix(meta, ch, "value")

    def some_of(self, meta, ch):
        return self._prefix(meta, ch, "some")

    def keys_of(self, meta, ch):
        return self._prefix(meta, ch, "keys")

    def values_of(self, meta, ch):
        return self._prefix(meta, ch, "values")

    def text_from(self, meta, ch):
        return self._prefix(meta, ch, "text_from")

    def number_from(self, meta, ch):
        return self._prefix(meta, ch, "number_from")

    def decimal_from(self, meta, ch):
        return self._prefix(meta, ch, "decimal_from")

    def sorted_of(self, meta, ch):
        return self._prefix(meta, ch, "sorted")

    def reversed_of(self, meta, ch):
        return self._prefix(meta, ch, "reversed")

    def trimmed_of(self, meta, ch):
        return self._prefix(meta, ch, "trimmed")

    def rounded_of(self, meta, ch):
        return self._prefix(meta, ch, "rounded")

    def remainder(self, meta, ch):
        return A.Remainder(left=ch[0], right=ch[1], **_pos(meta))

    def item_of(self, meta, ch):
        return A.ItemOf(index=ch[0], container=ch[1], **_pos(meta))

    def maybe_item_of(self, meta, ch):
        return A.ItemOf(index=ch[0], container=ch[1], safe=True, **_pos(meta))

    def read_file(self, meta, ch):
        return A.ReadFile(path=ch[0], **_pos(meta))

    def files_in(self, meta, ch):
        return A.FilesIn(path=ch[0], **_pos(meta))

    def setting_of(self, meta, ch):
        return A.Setting(name=ch[0], **_pos(meta))

    def the_time(self, meta, ch):
        return A.TheTime(**_pos(meta))

    def from_json(self, meta, ch):
        return A.FromJson(type_name=str(ch[0]), value=ch[1], **_pos(meta))

    def as_json(self, meta, ch):
        return self._prefix(meta, ch, "json_text")

    def ask_number(self, meta, ch):
        return A.Ask(prompt=ch[0], numeric=True, **_pos(meta))

    def ask_text(self, meta, ch):
        return A.Ask(prompt=ch[0], numeric=False, **_pos(meta))

    def random_from(self, meta, ch):
        return A.RandomFrom(lo=ch[0], hi=ch[1], **_pos(meta))

    def field_get(self, meta, ch):
        return A.FieldGet(obj=ch[0], field_name=str(ch[1]), **_pos(meta))

    def num(self, meta, ch):
        return A.Num(value=int(ch[0]), **_pos(meta))

    def dec(self, meta, ch):
        return A.Dec(value=float(ch[0]), **_pos(meta))

    def text_lit(self, meta, ch):
        tok = ch[0]
        parts = _split_string(str(tok), tok.line, tok.column)
        return A.Str(parts=parts, **_pos(meta))

    def yes_lit(self, meta, ch):
        return A.YesLit(**_pos(meta))

    def no_lit(self, meta, ch):
        return A.NoLit(**_pos(meta))

    def nothing_lit(self, meta, ch):
        return A.NothingLit(**_pos(meta))

    def the_error(self, meta, ch):
        return A.TheError(**_pos(meta))

    def the_arguments(self, meta, ch):
        return A.TheArguments(**_pos(meta))

    def the_input(self, meta, ch):
        return A.TheInput(**_pos(meta))

    def var(self, meta, ch):
        return A.Var(name=str(ch[0]), **_pos(meta))

    def paren(self, meta, ch):
        return ch[0]

    def call_expr(self, meta, ch):
        return A.CallExpr(name=str(ch[0]), args=list(ch[1:]), **_pos(meta))

    def func_ref(self, meta, ch):
        return A.FuncRef(name=str(ch[0]), **_pos(meta))


# ------------------------------------------------------------------ errors

_TERM_DESC = {
    "NAME": "a name",
    "INT": "a whole number",
    "FLOAT": "a decimal number",
    "STRING": "a string in double quotes",
    "_NL": "the end of the line",
    "_INDENT": "an indented block",
    "_DEDENT": "the end of the block (less indentation)",
    "$END": "the end of the file",
    "COLON": "':'",
    "COMMA": "','",
    "_LPAR": "'('",
    "_RPAR": "')'",
    "_APOS_S": "'s",
    "CHANGING": "'changing'",
    # Terminals whose internal name is not what an author would type.
    "PARAM_AND": "'and'",
    "_DIV": "'divided by'",
    "_POW": "'to the power of'",
    "_MOD": "'modulo'",
    "_A": "'a'",
}

# Punctuation and layout answer "what does this line still need"; operators
# only answer "what else could this expression contain", which is rarely the
# author's mistake. Lower number sorts first.
_TERM_RANK = {
    "COLON": 0, "_NL": 0, "$END": 0, "_INDENT": 0, "_DEDENT": 0,
    "COMMA": 1, "_RPAR": 1,
}


def _describe_terminal(t: str) -> str:
    if t in _TERM_DESC:
        return _TERM_DESC[t]
    word = t.lstrip("_").lower().replace("_", " ")
    if word.startswith("anon"):
        return "a symbol"
    return f"'{word}'"


def _describe_expected(expected: list[str]) -> str | None:
    """Turn lark's accepted-terminal set into one short, useful sentence."""
    terms = list(expected)
    collapsed = []
    if {"NAME", "INT", "STRING"} <= set(terms):
        # A value position. Every other accepted terminal here is one more way
        # to begin a value (`length of`, `some`, `-`, `(`, …), so listing them
        # is noise; only structural expectations still carry information.
        terms = [t for t in terms if t in _TERM_RANK]
        collapsed = ["a value"]
    ranked = sorted(terms, key=lambda t: (_TERM_RANK.get(t, 2), t))
    shown = collapsed + [_describe_terminal(t) for t in ranked[:3]]
    if not shown:
        return None
    more = "…" if len(ranked) > 3 else "."
    return "Expected " + " or ".join(shown) + more


def _nested_quote_hint(line: str) -> str | None:
    """`"{name otherwise "unknown"}"` closes the string at the inner quote.

    Escaped quotes inside an interpolation are supported, so the fix is one
    character per quote — but the resulting error lands on whatever followed
    and says nothing about that. Name it whenever the shape is present.
    """
    pos = 0
    while True:
        open_brace = line.find("{", pos)
        if open_brace == -1:
            return None
        rest = line[open_brace + 1:]
        close = rest.find("}")
        inside = rest if close == -1 else rest[:close]
        if '"' in inside:
            return ('Escape quotes inside {…}: write \\" for each one, as in '
                    '"{name otherwise \\"unknown\\"}".')
        if close == -1:
            return None
        pos = open_brace + 1 + close + 1


def _token_error(e: UnexpectedToken, text: str) -> Diagnostic:
    tok = e.token
    if tok.type == "$END":
        got = "the end of the file"
    elif not str(tok.value).strip():
        got = "the end of the line"
    else:
        got = f"'{tok.value}'"
    expected = sorted(e.accepts or e.expected or [])
    hint = _describe_expected(expected)
    word = str(tok.value) if tok.type != "$END" else ""
    if "NAME" in expected and tok.type != "NAME" and re.fullmatch(r"[a-z][a-z ]*", word):
        hint = (hint or "") + f" Note: '{word}' is a reserved Parley phrase, so it cannot be used as a name here."
    if "COLON" in expected:
        hint = (hint or "") + " Lines that open a block (to/if/while/when/…) end with ':'."
    lines = text.splitlines()
    line = lines[e.line - 1] if 1 <= e.line <= len(lines) else ""
    definition = re.match(r"^\s*to\s+([A-Za-z_]\w*)\s+([A-Za-z_]\w*)", line)
    if definition and definition.group(2) not in {"with", "giving"}:
        hint = (hint or "") + (
            " Function names are one identifier: join multiple words with "
            "underscores, for example 'record_range'."
        )
    if re.match(r"^\s*(?:if|otherwise\s+if|while)\s+[A-Za-z_]\w*\s+with\b", line):
        hint = (hint or "") + (
            " A function call used as a condition needs parentheses, for "
            "example `if (is_valid with line):`."
        )
    if not line.lstrip().startswith("to ") and re.search(r"\bwith\b.*\bchanging\s+[A-Za-z_]", line):
        hint = (hint or "") + (
            " Write 'changing' only in the parameter declaration; pass the "
            "plain variable at the call site."
        )
    if re.search(r"\bis\s+(?:not\s+)?equal\s+to\b", line):
        hint = (hint or "") + (
            " Equality is written `is`; inequality is `is not`. Do not write "
            "`equal to`."
        )
    if re.search(r"\bnumber\s+from\s+text\s+[A-Za-z_]", line):
        hint = (hint or "") + (
            " Put only the value after `number from`, for example "
            "`number from quantity_text`."
        )
    if re.match(r"^\s*to\b.*\breturns\b", line):
        hint = (hint or "") + " Write `giving TYPE`, not `returns TYPE`."
    if re.match(r"^\s*(?:return\b|give\s+(?!back\b))", line):
        hint = (hint or "") + " Return a value with `give back value`."
    if re.match(r"^\s*add\b.*\bto\s+item\b", line):
        hint = (hint or "") + (
            " A container inside a map or list is changed by copying it out: "
            "`let inner be item k of m`, change `inner`, then "
            "`set item k of m to inner`."
        )
    nested = _nested_quote_hint(line)
    if nested:
        hint = (hint or "") + " " + nested
    return Diagnostic(
        "P101", f"I didn't expect {got} here.",
        line=getattr(tok, "line", 0) or 0, col=getattr(tok, "column", 0) or 0,
        hint=hint)


def _ensure_stack_headroom() -> None:
    """Deep-but-legal programs recurse in the transformer, checker, and
    emitter; the depth cap itself lives in the checker (P106), but every
    phase before it needs enough Python stack to reach that judgement."""
    import sys

    if sys.getrecursionlimit() < 20000:
        sys.setrecursionlimit(20000)


def parse(text: str) -> A.Program:
    """Parse combined program text into an AST. Raises ParleyError.

    Positions in the AST/diagnostics refer to the combined text; resolve them
    through the SourceMap before showing them to anyone.
    """
    _ensure_stack_headroom()
    if not text.endswith("\n"):
        text += "\n"
    try:
        tree = _lark().parse(text, start="start")
    except UnexpectedToken as e:
        raise ParleyError([_token_error(e, text)])
    except UnexpectedCharacters as e:
        bad_line = text.splitlines()[e.line - 1]
        hint = "Strings use double quotes; names use letters, digits and underscores."
        nested = _nested_quote_hint(bad_line)
        if nested:
            hint = nested
        raise ParleyError([Diagnostic(
            "P102", f"Parley does not recognise the character {bad_line[e.column - 1]!r}.",
            line=e.line, col=e.column, hint=hint)])
    except ParleyError:
        raise
    except LarkError as e:
        msg = str(e)
        if "dedent" in msg.lower() or "indent" in msg.lower():
            return_diag = Diagnostic(
                "P103", "The indentation of a line does not match any open block.",
                hint="Use a consistent indent (4 spaces per level). Every ':' opens a deeper block.")
        else:
            return_diag = Diagnostic("P101", f"Could not read the program: {msg}")
        raise ParleyError([return_diag])
    return _transform(tree)


def parse_program(path) -> tuple[A.Program, SourceMap]:
    """Load (with includes) and parse a program from disk."""
    text, srcmap = load_program(path)
    try:
        program = parse(text)
    except ParleyError as e:
        srcmap.resolve(e.diagnostics)
        raise
    _reject_included_top_level(program, srcmap)
    return program, srcmap


def _reject_included_top_level(program: A.Program, srcmap: SourceMap) -> None:
    """Top-level statements belong to the file being run, not to its includes.

    Includes are spliced textually, so without this an included file's loose
    statements would silently join the entrypoint's `main`.
    """
    implicit = next((f for f in program.funcs
                     if f.name == "main" and getattr(f, "implicit_main", False)), None)
    if implicit is None:
        return
    for st in implicit.body:
        file, line = srcmap.loc(getattr(st, "line", 1))
        if file != srcmap.main_file:
            raise ParleyError([Diagnostic(
                "P213",
                f'"{file}" is included, so it can only define functions, '
                f"records, and enums — not loose statements.",
                file=file, line=line,
                hint="Move the statement into a `to name:` function and call "
                     "that from the file you run.")])
