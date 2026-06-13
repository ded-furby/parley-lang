"""Parley type checker — the agent-error firewall.

Runs after parsing and before Rust emission. Its job is to make sure that an
author (human or agent) never has to read a rustc error: every name, arity,
field, variant, and type mistake is caught here and explained in plain English
with a did-you-mean hint where possible.

The checker also annotates the AST for the emitter:
  * every Expr gets `.ty`
  * Var nodes that resolve to enum variants get `.variant_of`
  * Var nodes that resolve to zero-argument functions get `.is_call`/`.target_fn`
  * Var/LValue nodes referring to `changing` parameters get `.is_changing`
  * Call nodes get `.target_fn`
"""

from __future__ import annotations

import difflib

from . import ast_nodes as A
from .diagnostics import Diagnostic, ParleyError


class TErr(A.Type):
    """Sentinel for already-reported failures; silences cascade errors."""

    def __str__(self):
        return "?"


class TNothing(A.Type):
    """The type of a bare `nothing` literal before context is known."""

    def __str__(self):
        return "nothing"


# Words that are (or begin) Parley phrases in expression position. Using them
# as names would parse in some places and explode in others, so they are
# uniformly refused with a clear message instead.
RESERVED = {
    "a", "an", "is", "of", "to", "item", "ask", "sorted", "reversed",
    "trimmed", "rounded", "contains", "times", "changing", "plus", "minus",
    "yes", "no", "nothing", "not", "and", "or", "say", "let", "be", "set",
    "stop", "skip", "add", "remove", "write", "append", "if", "otherwise",
    "when", "while", "repeat", "attempt", "with", "giving", "has", "from",
    "in", "maybe", "include", "number", "decimal", "text", "yesno",
    "list", "map", "function", "taking", "the",
}

_NUMERIC = (A.TNum, A.TDec)
_ORDERED = (A.TNum, A.TDec, A.TText)


def _suggest(name: str, candidates) -> str | None:
    close = difflib.get_close_matches(name, list(candidates), n=1, cutoff=0.7)
    return close[0] if close else None


class Checker:
    def __init__(self, program: A.Program):
        self.program = program
        self.diags: list[Diagnostic] = []
        self.records: dict[str, A.RecordDef] = {}
        self.enums: dict[str, A.EnumDef] = {}
        self.variants: dict[str, str] = {}      # variant -> enum name
        self.funcs: dict[str, A.FuncDef] = {}
        # per-function state
        self.scopes: list[dict[str, A.Type]] = []
        self.changing: set[str] = set()
        self.fn: A.FuncDef | None = None
        self.loop_depth = 0
        self.attempt_loop_marks: list[int] = []

    # ------------------------------------------------------------- plumbing

    def err(self, code: str, msg: str, node, hint: str | None = None,
            replacement: str | None = None):
        self.diags.append(Diagnostic(
            code, msg, line=getattr(node, "line", 0), col=getattr(node, "col", 0),
            hint=hint, replacement=replacement))

    def check_name_ok(self, name: str, node, what: str) -> bool:
        if name in RESERVED:
            self.err("P209",
                     f'"{name}" is part of Parley\'s own vocabulary, so it cannot name a {what}.',
                     node,
                     hint=f'Pick a more specific name, e.g. "{name}_value" or "my_{name}".')
            return False
        return True

    def lookup(self, name: str) -> A.Type | None:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def declare(self, name: str, ty: A.Type, node) -> None:
        if self.lookup(name) is not None:
            self.err("P209", f'"{name}" already exists here.',
                     node, hint=f'Use `set {name} to …` to change it, or pick a new name.')
            return
        if name in self.funcs:
            self.err("P209", f'"{name}" is already the name of a function.', node)
            return
        if name in self.variants:
            self.err("P209", f'"{name}" is already a variant of {self.variants[name]}.', node)
            return
        self.scopes[-1][name] = ty

    # ------------------------------------------------------------- types

    def resolve_type(self, ty: A.Type, node) -> A.Type:
        if isinstance(ty, A.TNamed):
            if ty.name in self.records:
                return A.TRecord(ty.name)
            if ty.name in self.enums:
                return A.TEnum(ty.name)
            hint = None
            s = _suggest(ty.name, list(self.records) + list(self.enums)
                         + ["number", "decimal", "text", "yesno"])
            if s:
                hint = f'Did you mean "{s}"?'
            self.err("P205", f'There is no type called "{ty.name}".', node, hint=hint)
            return TErr()
        if isinstance(ty, A.TList):
            return A.TList(self.resolve_type(ty.elem, node))
        if isinstance(ty, A.TMaybe):
            return A.TMaybe(self.resolve_type(ty.elem, node))
        if isinstance(ty, A.TMap):
            key = self.resolve_type(ty.key, node)
            if not isinstance(key, (A.TNum, A.TText, TErr)):
                self.err("P309", f"Map keys must be number or text, not {key}.", node)
                key = TErr()
            return A.TMap(key, self.resolve_type(ty.val, node))
        if isinstance(ty, A.TFunc):
            return A.TFunc(
                [self.resolve_type(p, node) for p in ty.params],
                None if ty.ret is None else self.resolve_type(ty.ret, node))
        return ty

    def assignable(self, expected: A.Type, actual: A.Type) -> bool:
        """Can a value of `actual` be stored where `expected` is required?
        number -> decimal promotion is allowed (the emitter inserts the cast)."""
        if isinstance(expected, TErr) or isinstance(actual, TErr):
            return True
        if isinstance(actual, TNothing) and isinstance(expected, A.TMaybe):
            return True
        if isinstance(expected, A.TDec) and isinstance(actual, A.TNum):
            return True
        return expected == actual

    def type_mismatch(self, expected: A.Type, actual: A.Type, node, context: str):
        hint = None
        if isinstance(expected, A.TText):
            hint = 'To turn a value into text, use interpolation "{x}" or `text from x`.'
        elif isinstance(expected, A.TNum) and isinstance(actual, A.TDec):
            hint = "Use `rounded x`, `floor of x`, or `ceiling of x` to get a whole number."
        elif isinstance(expected, A.TNum) and isinstance(actual, A.TMaybe):
            hint = "This is a maybe — check `… is nothing` first, then use `value of x`."
        elif isinstance(expected, A.TMaybe) and self.assignable(expected.elem, actual):
            hint = "A plain value fits a maybe automatically only as `nothing`; wrap logic so both sides are the same."
        self.err("P301", f"{context} needs {expected}, but this is {actual}.", node, hint=hint)

    # ------------------------------------------------------------- programs

    def check(self) -> list[Diagnostic]:
        p = self.program
        for r in p.records:
            self.check_name_ok(r.name, r, "record")
            if r.name in self.records or r.name in self.enums or r.name in self.funcs:
                self.err("P207", f'There are two definitions called "{r.name}".', r)
                continue
            seen = set()
            fields = []
            for fname, fty in r.fields:
                self.check_name_ok(fname, r, "field")
                if fname in seen:
                    self.err("P207", f'Record {r.name} declares the field "{fname}" twice.', r)
                    continue
                seen.add(fname)
                fields.append((fname, fty))
            r.fields = fields
            self.records[r.name] = r
        for e in p.enums:
            self.check_name_ok(e.name, e, "kind")
            if e.name in self.records or e.name in self.enums or e.name in self.funcs:
                self.err("P207", f'There are two definitions called "{e.name}".', e)
                continue
            self.enums[e.name] = e
            for v in e.variants:
                self.check_name_ok(v, e, "variant")
                if v in self.variants:
                    self.err("P207",
                             f'The variant "{v}" appears in both {self.variants[v]} and {e.name}. '
                             "Variant names are global, so each must be unique.", e)
                    continue
                self.variants[v] = e.name
        # resolve record field types after all type names are known
        for r in self.records.values():
            r.fields = [(fn, self.resolve_type(ft, r)) for fn, ft in r.fields]
        for f in p.funcs:
            if f.name != "main":
                self.check_name_ok(f.name, f, "function")
            if f.name in self.funcs or f.name in self.records or f.name in self.enums:
                self.err("P207", f'There are two definitions called "{f.name}".', f)
                continue
            self.funcs[f.name] = f
            for prm in f.params:
                prm.type = self.resolve_type(prm.type, prm)
            if f.ret is not None:
                f.ret = self.resolve_type(f.ret, f)

        main = self.funcs.get("main")
        if main is None:
            self.err("P210", "Every program needs a `to main:` to start from.", p,
                     hint="Add `to main:` with the program body indented underneath.")
        else:
            if main.params:
                self.err("P210", "`to main:` takes no parameters.", main)
            if main.ret is not None:
                self.err("P210", "`to main:` cannot have a giving type.", main)

        for f in p.funcs:
            if f.name in self.funcs and self.funcs[f.name] is f:
                self.check_function(f)
        return self.diags

    def check_function(self, fn: A.FuncDef):
        self.fn = fn
        self.scopes = [{}]
        self.changing = set()
        self.loop_depth = 0
        self.attempt_loop_marks = []
        seen = set()
        for prm in fn.params:
            self.check_name_ok(prm.name, prm, "parameter")
            if prm.name in seen:
                self.err("P207", f'Parameter "{prm.name}" appears twice.', prm)
                continue
            seen.add(prm.name)
            self.scopes[0][prm.name] = prm.type
            if prm.changing:
                self.changing.add(prm.name)
        self.check_block(fn.body, new_scope=False)
        if fn.ret is not None and not self._always_gives(fn.body):
            self.err("P304",
                     f'"{fn.name}" promises to give back {fn.ret}, but not every path does.',
                     fn, hint="Make sure every branch ends with `give back …`.")
        self.fn = None

    def _always_gives(self, body: list[A.Stmt]) -> bool:
        for st in body:
            if isinstance(st, A.Give):
                return True
            if isinstance(st, A.If) and st.otherwise is not None:
                if all(self._always_gives(b) for _, b in st.arms) and self._always_gives(st.otherwise):
                    return True
            if isinstance(st, A.When):
                arms_ok = all(self._always_gives(b) for _, b in st.arms)
                if arms_ok and st.otherwise is not None and self._always_gives(st.otherwise):
                    return True
                if arms_ok and st.otherwise is None and getattr(st, "exhaustive", False):
                    return True
        return False

    # ------------------------------------------------------------- statements

    def check_block(self, body: list[A.Stmt], new_scope: bool = True,
                    preset: dict[str, A.Type] | None = None):
        if new_scope:
            self.scopes.append(dict(preset or {}))
        for st in body:
            self.check_stmt(st)
        if new_scope:
            self.scopes.pop()

    def check_stmt(self, st: A.Stmt):
        m = getattr(self, "st_" + type(st).__name__.lower(), None)
        if m is None:
            raise AssertionError(f"no checker for {type(st).__name__}")
        m(st)

    def st_let(self, st: A.Let):
        ty = self.infer(st.value)
        if isinstance(ty, TNothing):
            self.err("P308",
                     f'I can\'t tell what type "{st.name}" should be from bare `nothing`.',
                     st, hint="Start from a real value, or from an operation that gives a maybe "
                              "(ask for a number, read file, number from …).")
            ty = TErr()
        if isinstance(ty, A.TUnit):
            self.err("P301", "This gives nothing back, so there is no value to store.", st)
            ty = TErr()
        if self.check_name_ok(st.name, st, "variable"):
            self.declare(st.name, ty, st)

    def _resolve_lvalue(self, lv: A.LValue) -> A.Type:
        base_ty = self.lookup(lv.base)
        if base_ty is None:
            hint = None
            s = _suggest(lv.base, self._known_names())
            if s:
                hint = f'Did you mean "{s}"?'
            elif lv.base in self.funcs:
                hint = "Functions cannot be assigned to."
            self.err("P211" if not lv.fields else "P201",
                     f'There is no variable called "{lv.base}" here.', lv, hint=hint)
            lv.ty = TErr()
            return lv.ty
        lv.is_changing = lv.base in self.changing
        ty = base_ty
        for fname in lv.fields:
            ty = self._field_type(ty, fname, lv)
            if isinstance(ty, TErr):
                break
        lv.ty = ty
        return ty

    def _field_type(self, ty: A.Type, fname: str, node) -> A.Type:
        if isinstance(ty, TErr):
            return ty
        if isinstance(ty, A.TRecord):
            rec = self.records[ty.name]
            for fn_, ft in rec.fields:
                if fn_ == fname:
                    return ft
            names = ", ".join(n for n, _ in rec.fields)
            s = _suggest(fname, [n for n, _ in rec.fields])
            hint = f'Did you mean "{s}"?' if s else f"{ty.name} has: {names}."
            self.err("P204", f'"{fname}" is not a field of {ty.name}.', node, hint=hint)
            return TErr()
        self.err("P204", f"A {ty} has no fields, so 's cannot be used on it.", node)
        return TErr()

    def st_setvar(self, st: A.SetVar):
        target_ty = self._resolve_lvalue(st.target)
        val_ty = self.infer(st.value)
        if not self.assignable(target_ty, val_ty):
            self.type_mismatch(target_ty, val_ty, st, f'`set {st.target.show()}`')

    def st_setitem(self, st: A.SetItem):
        target_ty = self._resolve_lvalue(st.target)
        idx_ty = self.infer(st.index)
        val_ty = self.infer(st.value)
        if isinstance(target_ty, A.TList):
            if not self.assignable(A.TNum(), idx_ty):
                self.type_mismatch(A.TNum(), idx_ty, st, "A list position")
            if not self.assignable(target_ty.elem, val_ty):
                self.type_mismatch(target_ty.elem, val_ty, st, "This list's items")
        elif isinstance(target_ty, A.TMap):
            if not self.assignable(target_ty.key, idx_ty):
                self.type_mismatch(target_ty.key, idx_ty, st, "This map's keys")
            if not self.assignable(target_ty.val, val_ty):
                self.type_mismatch(target_ty.val, val_ty, st, "This map's values")
        elif not isinstance(target_ty, TErr):
            self.err("P306", f"`set item … of …` works on lists and maps, not {target_ty}.", st)

    def st_say(self, st: A.Say):
        ty = self.infer(st.value)
        if isinstance(ty, A.TUnit):
            self.err("P301", "This gives nothing back, so there is nothing to say.", st)
        elif isinstance(ty, A.TFunc):
            self.err("P301", "A function value cannot be turned into text, so it cannot be said.", st)

    def _check_cond(self, cond: A.Expr, what: str):
        ty = self.infer(cond)
        if not isinstance(ty, (A.TBool, TErr)):
            hint = None
            if isinstance(ty, (A.TNum, A.TDec)):
                hint = f"Compare it: `{what} x is more than 0:`."
            if isinstance(ty, A.TMaybe):
                hint = "Check `… is nothing` or `… is not nothing`."
            self.err("P303", f"After `{what}` Parley needs yes or no, but this is {ty}.",
                     cond, hint=hint)

    def st_if(self, st: A.If):
        for cond, body in st.arms:
            self._check_cond(cond, "if")
            self.check_block(body)
        if st.otherwise is not None:
            self.check_block(st.otherwise)

    def st_when(self, st: A.When):
        subj_ty = self.infer(st.subject)
        covered: set[str] = set()
        for pats, body in st.arms:
            for pat in pats:
                self._check_pattern(pat, subj_ty, covered)
            self.check_block(body)
        if st.otherwise is not None:
            self.check_block(st.otherwise)
        st.exhaustive = False
        if isinstance(subj_ty, A.TEnum):
            all_v = set(self.enums[subj_ty.name].variants)
            missing = sorted(all_v - covered)
            st.exhaustive = not missing
            if missing and st.otherwise is None:
                self.err("P208",
                         f"This `when` does not cover: {', '.join(missing)}.",
                         st, hint="Add arms for them, or end with `otherwise:`.")
        elif isinstance(subj_ty, A.TBool):
            st.exhaustive = {"yes", "no"} <= covered
            if not st.exhaustive and st.otherwise is None:
                self.err("P208", "Cover both yes and no, or add `otherwise:`.", st)
        elif not isinstance(subj_ty, TErr):
            if st.otherwise is None:
                self.err("P208",
                         f"A `when` over {subj_ty} can't list every possible value, "
                         "so it must end with `otherwise:`.", st)

    def _check_pattern(self, pat: A.Pattern, subj_ty: A.Type, covered: set[str]):
        if isinstance(subj_ty, TErr):
            return
        if pat.kind == "range":
            lo, hi = pat.value
            if not isinstance(subj_ty, _NUMERIC):
                self.err("P312", f"A range arm (`is a to b:`) needs a numeric `when`, "
                         f"but this one is over {subj_ty}.", pat)
                return
            for end in (lo, hi):
                if end.kind not in ("int", "dec"):
                    self.err("P312", "Range ends must be number or decimal literals.", end)
                    return
                if end.kind == "dec" and isinstance(subj_ty, A.TNum):
                    self.err("P312", "This `when` is over number, so range ends must be "
                             "whole numbers.", end)
                    return
            if lo.value > hi.value:
                self.err("P312", f"This range is empty — {lo.value} is more than {hi.value}.",
                         pat, hint="Write the smaller value first: "
                                   f"`is {hi.value} to {lo.value}:`.")
            return
        if pat.kind == "name":
            if isinstance(subj_ty, A.TEnum):
                enum = self.enums[subj_ty.name]
                if pat.value not in enum.variants:
                    s = _suggest(pat.value, enum.variants)
                    hint = f'Did you mean "{s}"?' if s else f"{subj_ty.name} has: {', '.join(enum.variants)}."
                    self.err("P201", f'"{pat.value}" is not a variant of {subj_ty.name}.',
                             pat, hint=hint)
                    return
                if pat.value in covered:
                    self.err("P207", f'The arm "is {pat.value}:" appears twice.', pat)
                covered.add(pat.value)
            else:
                self.err("P301", f"This `when` is over {subj_ty}, but the arm names a variant.", pat)
            return
        want = {"int": A.TNum(), "dec": A.TDec(), "text": A.TText(),
                "yes": A.TBool(), "no": A.TBool()}[pat.kind]
        if pat.kind in ("yes", "no"):
            covered.add(pat.kind)
        if not self.assignable(want, subj_ty) and not self.assignable(subj_ty, want):
            self.err("P301", f"This `when` is over {subj_ty}, but an arm checks {want}.", pat)

    def st_while(self, st: A.While):
        self._check_cond(st.cond, "while")
        self.loop_depth += 1
        self.check_block(st.body)
        self.loop_depth -= 1

    def st_repeat(self, st: A.Repeat):
        ty = self.infer(st.count)
        if not self.assignable(A.TNum(), ty):
            self.type_mismatch(A.TNum(), ty, st, "`repeat … times`")
        self.loop_depth += 1
        self.check_block(st.body)
        self.loop_depth -= 1

    def st_forrange(self, st: A.ForRange):
        for e, what in ((st.lo, "from"), (st.hi, "to")):
            ty = self.infer(e)
            if not self.assignable(A.TNum(), ty):
                self.type_mismatch(A.TNum(), ty, e, f"The `{what}` bound")
        self.check_name_ok(st.var, st, "loop variable")
        self.loop_depth += 1
        self.check_block(st.body, preset={st.var: A.TNum()})
        self.loop_depth -= 1

    def st_foreach(self, st: A.ForEach):
        ty = self.infer(st.iter)
        elem: A.Type = TErr()
        if isinstance(ty, A.TList):
            elem = ty.elem
        elif isinstance(ty, A.TMap):
            self.err("P306", "Loop over a map with `for each k in keys of m:`.", st)
        elif isinstance(ty, A.TText):
            self.err("P306", "Loop over text by splitting it first: `for each part in t split by \",\":`.", st)
        elif not isinstance(ty, TErr):
            self.err("P306", f"`for each` needs a list, but this is {ty}.", st)
        self.check_name_ok(st.var, st, "loop variable")
        self.loop_depth += 1
        self.check_block(st.body, preset={st.var: elem})
        self.loop_depth -= 1

    def st_give(self, st: A.Give):
        if self.attempt_loop_marks:
            self.err("P310", "`give back` cannot jump out of an `attempt:` block.", st,
                     hint="Set a variable inside the attempt and give back after it.")
        ret = self.fn.ret
        if st.value is None:
            if ret is not None:
                self.err("P304", f'"{self.fn.name}" must give back {ret}, but this gives back nothing.', st)
            return
        ty = self.infer(st.value)
        if ret is None:
            self.err("P304",
                     f'"{self.fn.name}" has no `giving` type, so it cannot give back a value.',
                     st, hint=f"Add `giving {ty}` to the `to {self.fn.name} …:` line.")
        elif not self.assignable(ret, ty):
            self.type_mismatch(ret, ty, st, "`give back`")

    def st_stop(self, st: A.Stop):
        self._loop_jump(st, "stop")

    def st_skip(self, st: A.Skip):
        self._loop_jump(st, "skip")

    def _loop_jump(self, st, word: str):
        if self.loop_depth == 0:
            self.err("P311", f"`{word}` only makes sense inside a loop.", st)
        elif self.attempt_loop_marks and self.loop_depth <= self.attempt_loop_marks[-1]:
            self.err("P310", f"`{word}` cannot jump out of an `attempt:` block.", st)

    def st_attempt(self, st: A.Attempt):
        self.attempt_loop_marks.append(self.loop_depth)
        self.check_block(st.body)
        self.attempt_loop_marks.pop()
        self.check_block(st.handler)

    def st_add(self, st: A.Add):
        target_ty = self._resolve_lvalue(st.target)
        val_ty = self.infer(st.value)
        if isinstance(target_ty, A.TList):
            if not self.assignable(target_ty.elem, val_ty):
                self.type_mismatch(target_ty.elem, val_ty, st, f"This list holds {target_ty.elem}, so `add`")
        elif isinstance(target_ty, A.TMap):
            self.err("P306", "Use `set item key of map to value` to put things in a map.", st)
        elif not isinstance(target_ty, TErr):
            self.err("P306", f"`add … to …` needs a list, but {st.target.show()} is {target_ty}.", st)

    def st_removeitem(self, st: A.RemoveItem):
        target_ty = self._resolve_lvalue(st.target)
        idx_ty = self.infer(st.index)
        if isinstance(target_ty, A.TList):
            if not self.assignable(A.TNum(), idx_ty):
                self.type_mismatch(A.TNum(), idx_ty, st, "A list position")
        elif isinstance(target_ty, A.TMap):
            if not self.assignable(target_ty.key, idx_ty):
                self.type_mismatch(target_ty.key, idx_ty, st, "This map's keys")
        elif not isinstance(target_ty, TErr):
            self.err("P306", f"`remove item` works on lists and maps, not {target_ty}.", st)

    def st_writefile(self, st: A.WriteFile):
        for e, what in ((st.value, "The content"), (st.path, "The file path")):
            ty = self.infer(e)
            if not isinstance(ty, (A.TText, TErr)):
                self.type_mismatch(A.TText(), ty, e, what)

    def st_callstmt(self, st: A.CallStmt):
        self._check_call(st, st.name, st.args, statement=True)

    # ------------------------------------------------------------- calls

    def _check_call(self, node, name: str, args: list[A.Expr], statement: bool) -> A.Type:
        fn = self.funcs.get(name)
        if fn is None:
            vty = self.lookup(name)
            if isinstance(vty, A.TFunc):
                return self._check_value_call(node, name, vty, args)
            hint = None
            s = _suggest(name, self.funcs)
            if s:
                hint = f'Did you mean "{s}"?'
            elif vty is not None:
                hint = f'"{name}" is a variable; only functions can be called.'
            self.err("P202", f'There is no function called "{name}".', node, hint=hint)
            for a in args:
                self.infer(a)
            return TErr()
        node.target_fn = fn
        if len(args) != len(fn.params):
            sig = ", ".join(f"{p.name} as {p.type}" for p in fn.params) or "no parameters"
            self.err("P203",
                     f'"{name}" takes {len(fn.params)} argument(s), but {len(args)} were given.',
                     node, hint=f"Its definition is: to {name} with {sig}.")
            for a in args:
                self.infer(a)
            return fn.ret or A.TUnit()
        for prm, arg in zip(fn.params, args):
            a_ty = self.infer(arg)
            if prm.changing:
                if not (isinstance(arg, A.Var) and not getattr(arg, "is_call", False)):
                    self.err("P305",
                             f'"{prm.name}" is a changing parameter, so the argument must be a variable.',
                             arg)
                    continue
                if not (isinstance(a_ty, TErr) or prm.type == a_ty):
                    self.type_mismatch(prm.type, a_ty, arg, f'The changing argument "{prm.name}"')
            elif not self.assignable(prm.type, a_ty):
                self.type_mismatch(prm.type, a_ty, arg, f'The argument "{prm.name}" of {name}')
        return fn.ret or A.TUnit()

    def _check_value_call(self, node, name: str, fty: A.TFunc, args: list[A.Expr]) -> A.Type:
        """A call through a variable that holds a function value."""
        node.fn_value = True
        node.fn_type = fty
        node.callee_changing = name in self.changing
        if len(args) != len(fty.params):
            sig = ", ".join(str(p) for p in fty.params) or "no arguments"
            self.err("P203",
                     f'"{name}" holds {fty}, which takes {len(fty.params)} argument(s), '
                     f"but {len(args)} were given.",
                     node, hint=f"It takes: {sig}.")
            for a in args:
                self.infer(a)
            return fty.ret or A.TUnit()
        for i, (pt, arg) in enumerate(zip(fty.params, args), 1):
            a_ty = self.infer(arg)
            if not self.assignable(pt, a_ty):
                self.type_mismatch(pt, a_ty, arg, f"Argument {i} of {name}")
        return fty.ret or A.TUnit()

    # ------------------------------------------------------------- expressions

    def _known_names(self):
        names = set()
        for s in self.scopes:
            names |= set(s)
        return names | set(self.funcs) | set(self.variants)

    def infer(self, e: A.Expr) -> A.Type:
        ty = self._infer(e)
        e.ty = ty
        return ty

    def _infer(self, e: A.Expr) -> A.Type:
        if isinstance(e, A.Num):
            return A.TNum()
        if isinstance(e, A.Dec):
            return A.TDec()
        if isinstance(e, A.YesLit) or isinstance(e, A.NoLit):
            return A.TBool()
        if isinstance(e, A.NothingLit):
            return TNothing()
        if isinstance(e, A.TheError):
            return A.TText()
        if isinstance(e, A.Str):
            for p in e.parts:
                if isinstance(p, A.Expr):
                    pty = self.infer(p)
                    if isinstance(pty, A.TUnit):
                        self.err("P301", "This gives nothing back, so it cannot go inside a string.", p)
                    elif isinstance(pty, A.TFunc):
                        self.err("P301", "A function value cannot be turned into text.", p)
            return A.TText()
        if isinstance(e, A.Var):
            return self._infer_var(e)
        if isinstance(e, A.FieldGet):
            obj_ty = self.infer(e.obj)
            return self._field_type(obj_ty, e.field_name, e)
        if isinstance(e, A.BinOp):
            return self._infer_binop(e)
        if isinstance(e, A.Compare):
            return self._infer_compare(e)
        if isinstance(e, A.Not):
            ty = self.infer(e.value)
            if not isinstance(ty, (A.TBool, TErr)):
                self.err("P303", f"`not` needs yes or no, but this is {ty}.", e)
            return A.TBool()
        if isinstance(e, A.Neg):
            ty = self.infer(e.value)
            if isinstance(ty, (A.TNum, A.TDec, TErr)):
                return ty if not isinstance(ty, TErr) else TErr()
            self.err("P302", f"Only numbers can be negated, but this is {ty}.", e)
            return TErr()
        if isinstance(e, A.SplitBy):
            for part, what in ((e.value, "The thing being split"), (e.sep, "The separator")):
                ty = self.infer(part)
                if not isinstance(ty, (A.TText, TErr)):
                    self.type_mismatch(A.TText(), ty, part, what)
            return A.TList(A.TText())
        if isinstance(e, A.JoinedWith):
            vty = self.infer(e.value)
            sty = self.infer(e.sep)
            if not (isinstance(vty, TErr) or vty == A.TList(A.TText())):
                self.err("P302", f"`joined with` needs a list of text, but this is {vty}.",
                         e, hint="Convert items first: build a list of text using `text from x`.")
            if not isinstance(sty, (A.TText, TErr)):
                self.type_mismatch(A.TText(), sty, e.sep, "The separator")
            return A.TText()
        if isinstance(e, A.PrefixOp):
            return self._infer_prefix(e)
        if isinstance(e, A.Remainder):
            for side in (e.left, e.right):
                ty = self.infer(side)
                if not isinstance(ty, (A.TNum, TErr)):
                    self.type_mismatch(A.TNum(), ty, side, "`remainder of`")
            return A.TNum()
        if isinstance(e, A.ItemOf):
            return self._infer_item(e)
        if isinstance(e, A.ReadFile):
            ty = self.infer(e.path)
            if not isinstance(ty, (A.TText, TErr)):
                self.type_mismatch(A.TText(), ty, e.path, "The file path")
            return A.TMaybe(A.TText())
        if isinstance(e, A.Ask):
            ty = self.infer(e.prompt)
            if not isinstance(ty, (A.TText, TErr)):
                self.type_mismatch(A.TText(), ty, e.prompt, "The prompt")
            return A.TMaybe(A.TNum()) if e.numeric else A.TText()
        if isinstance(e, A.RandomFrom):
            for side in (e.lo, e.hi):
                ty = self.infer(side)
                if not isinstance(ty, (A.TNum, TErr)):
                    self.type_mismatch(A.TNum(), ty, side, "A random range bound")
            return A.TNum()
        if isinstance(e, A.ListLit):
            return self._infer_list(e)
        if isinstance(e, A.EmptyList):
            e.elem_type = self.resolve_type(e.elem_type, e)
            return A.TList(e.elem_type)
        if isinstance(e, A.EmptyMap):
            e.key_type = self.resolve_type(e.key_type, e)
            e.val_type = self.resolve_type(e.val_type, e)
            if not isinstance(e.key_type, (A.TNum, A.TText, TErr)):
                self.err("P309", f"Map keys must be number or text, not {e.key_type}.", e)
                e.key_type = TErr()
            return A.TMap(e.key_type, e.val_type)
        if isinstance(e, A.Construct):
            return self._infer_construct(e)
        if isinstance(e, A.CallExpr):
            ret = self._check_call(e, e.name, e.args, statement=False)
            if isinstance(ret, A.TUnit):
                self.err("P301",
                         f'"{e.name}" gives nothing back, so it cannot be used as a value.', e)
                return TErr()
            return ret
        if isinstance(e, A.FuncRef):
            return self._infer_funcref(e)
        raise AssertionError(f"no inference for {type(e).__name__}")

    def _infer_funcref(self, e: A.FuncRef) -> A.Type:
        fn = self.funcs.get(e.name)
        if fn is None:
            vty = self.lookup(e.name)
            if isinstance(vty, A.TFunc):
                self.err("P313", f'"{e.name}" is already a function value — use it directly, '
                         f'without `the function`.', e, replacement=e.name)
                return vty
            hint = None
            s = _suggest(e.name, self.funcs)
            if s:
                hint = f'Did you mean "{s}"?'
            elif vty is not None:
                hint = f'"{e.name}" is a variable, not a function.'
            self.err("P202", f'There is no function called "{e.name}".', e, hint=hint)
            return TErr()
        if e.name == "main":
            self.err("P313", "`main` cannot be used as a function value.", e)
            return TErr()
        if any(p.changing for p in fn.params):
            self.err("P313",
                     f'"{e.name}" has a changing parameter, so it cannot be used as a value.',
                     e, hint="Function values pass everything by value; "
                             "rewrite the function to give back the changed value instead.")
            return TErr()
        e.target_fn = fn
        return A.TFunc([p.type for p in fn.params], fn.ret)

    def _infer_var(self, e: A.Var) -> A.Type:
        ty = self.lookup(e.name)
        if ty is not None:
            e.is_changing = e.name in self.changing
            return ty
        if e.name in self.variants:
            e.variant_of = self.variants[e.name]
            return A.TEnum(e.variant_of)
        fn = self.funcs.get(e.name)
        if fn is not None:
            if fn.params:
                sig = ", ".join(p.name for p in fn.params)
                self.err("P203", f'"{e.name}" needs arguments ({sig}).', e,
                         replacement=f"({e.name} with …)")
                return fn.ret or TErr()
            e.is_call = True
            e.target_fn = fn
            if fn.ret is None:
                return A.TUnit()
            return fn.ret
        s = _suggest(e.name, self._known_names())
        hint = f'Did you mean "{s}"?' if s else "Create it first with `let …`."
        self.err("P201", f'There is no "{e.name}" here.', e, hint=hint)
        return TErr()

    def _infer_binop(self, e: A.BinOp) -> A.Type:
        if e.op in ("and", "or"):
            for side in (e.left, e.right):
                ty = self.infer(side)
                if not isinstance(ty, (A.TBool, TErr)):
                    self.err("P303", f"`{e.op}` needs yes or no on both sides, but this is {ty}.", side)
            return A.TBool()
        lt = self.infer(e.left)
        rt = self.infer(e.right)
        if isinstance(lt, TErr) or isinstance(rt, TErr):
            return TErr()
        if e.op == "+" and isinstance(lt, A.TText) and isinstance(rt, A.TText):
            return A.TText()
        if e.op == "+" and (isinstance(lt, A.TText) or isinstance(rt, A.TText)):
            self.err("P302", f"`plus` cannot join {lt} and {rt}.", e,
                     hint='Use interpolation instead: "score: {x}".')
            return TErr()
        if e.op == "+" and isinstance(lt, A.TList) and lt == rt:
            return lt
        if not (isinstance(lt, _NUMERIC) and isinstance(rt, _NUMERIC)):
            word = {"+": "plus", "-": "minus", "*": "times", "/": "divided by",
                    "%": "%", "pow": "to the power of"}[e.op]
            self.err("P302", f"`{word}` works on numbers, but this is {lt} and {rt}.", e)
            return TErr()
        if e.op == "/":
            return A.TDec()
        if e.op == "%":
            if isinstance(lt, A.TDec) or isinstance(rt, A.TDec):
                self.err("P302", "`%` works on whole numbers; use decimals with `divided by`.", e)
                return TErr()
            return A.TNum()
        if isinstance(lt, A.TDec) or isinstance(rt, A.TDec):
            return A.TDec()
        return A.TNum()

    def _infer_compare(self, e: A.Compare) -> A.Type:
        lt = self.infer(e.left)
        rt = self.infer(e.right)
        if isinstance(lt, TErr) or isinstance(rt, TErr):
            return A.TBool()
        if e.op in ("==", "!="):
            nothing_check = isinstance(lt, TNothing) or isinstance(rt, TNothing)
            maybe_side = lt if isinstance(lt, A.TMaybe) else rt if isinstance(rt, A.TMaybe) else None
            if nothing_check:
                if maybe_side is None and not (isinstance(lt, TNothing) and isinstance(rt, TNothing)):
                    other = rt if isinstance(lt, TNothing) else lt
                    self.err("P301",
                             f"Only maybe values can be compared with nothing; this is {other}.", e)
            elif isinstance(lt, A.TMaybe) != isinstance(rt, A.TMaybe):
                inner = lt.elem if isinstance(lt, A.TMaybe) else rt.elem
                self.err("P301", f"One side is a maybe and the other is not.",
                         e, hint=f"Unwrap the maybe first with `value of …` (after checking `is not nothing`).")
            elif not (self.assignable(lt, rt) or self.assignable(rt, lt)):
                self.err("P301", f"{lt} and {rt} can never be the same, so `is` cannot compare them.", e)
            return A.TBool()
        if e.op in (">", "<", ">=", "<="):
            ok = (isinstance(lt, _NUMERIC) and isinstance(rt, _NUMERIC)) or \
                 (isinstance(lt, A.TText) and isinstance(rt, A.TText))
            if not ok:
                self.err("P302", f"Sizes of {lt} and {rt} cannot be compared.", e)
            return A.TBool()
        # contains / startswith / endswith
        if e.op == "contains":
            if isinstance(lt, A.TList):
                if not self.assignable(lt.elem, rt):
                    self.err("P302", f"This list holds {lt.elem}, so it cannot contain {rt}.", e)
            elif isinstance(lt, A.TText):
                if not isinstance(rt, (A.TText, TErr)):
                    self.err("P302", f"Text can only contain text, not {rt}.", e)
            elif isinstance(lt, A.TMap):
                if not self.assignable(lt.key, rt):
                    self.err("P302", f"This map's keys are {lt.key}, so it cannot contain {rt}.", e)
            else:
                self.err("P302", f"`contains` works on lists, maps and text, not {lt}.", e)
            return A.TBool()
        for side, ty in ((e.left, lt), (e.right, rt)):
            if not isinstance(ty, (A.TText, TErr)):
                self.type_mismatch(A.TText(), ty, side,
                                   "`starts with`/`ends with`")
        return A.TBool()

    def _infer_prefix(self, e: A.PrefixOp) -> A.Type:
        ty = self.infer(e.value)
        op = e.op
        if isinstance(ty, TErr):
            return TErr()
        if op == "length":
            if isinstance(ty, (A.TText, A.TList, A.TMap)):
                return A.TNum()
            self.err("P306", f"`length of` works on text, lists and maps, not {ty}.", e)
            return TErr()
        if op == "sum":
            if isinstance(ty, A.TList) and isinstance(ty.elem, _NUMERIC):
                return ty.elem
            self.err("P306", f"`sum of` needs a list of numbers, but this is {ty}.", e)
            return TErr()
        if op in ("smallest", "largest"):
            if isinstance(ty, A.TList) and isinstance(ty.elem, _ORDERED):
                return ty.elem
            self.err("P306", f"`{op} of` needs a list of numbers or text, but this is {ty}.", e)
            return TErr()
        if op in ("upper", "lower", "trimmed"):
            if isinstance(ty, A.TText):
                return A.TText()
            word = {"upper": "uppercase of", "lower": "lowercase of", "trimmed": "trimmed"}[op]
            self.err("P306", f"`{word}` works on text, not {ty}.", e)
            return TErr()
        if op == "abs":
            if isinstance(ty, _NUMERIC):
                return ty
            self.err("P306", f"`absolute of` works on numbers, not {ty}.", e)
            return TErr()
        if op in ("floor", "ceil", "rounded"):
            if isinstance(ty, _NUMERIC):
                return A.TNum()
            self.err("P306", f"That operation works on numbers, not {ty}.", e)
            return TErr()
        if op == "sqrt":
            if isinstance(ty, _NUMERIC):
                return A.TDec()
            self.err("P306", f"`square root of` works on numbers, not {ty}.", e)
            return TErr()
        if op == "value":
            if isinstance(ty, A.TMaybe):
                return ty.elem
            self.err("P307", f"`value of` unwraps a maybe, but this is already {ty}.", e,
                     hint="Just use the value directly.")
            return ty
        if op == "keys":
            if isinstance(ty, A.TMap):
                return A.TList(ty.key)
            self.err("P306", f"`keys of` works on maps, not {ty}.", e)
            return TErr()
        if op == "text_from":
            if isinstance(ty, A.TUnit):
                self.err("P301", "This gives nothing back, so there is nothing to turn into text.", e)
                return TErr()
            if isinstance(ty, A.TFunc):
                self.err("P301", "A function value cannot be turned into text.", e)
                return TErr()
            return A.TText()
        if op == "number_from":
            if isinstance(ty, A.TText):
                return A.TMaybe(A.TNum())
            if isinstance(ty, _NUMERIC):
                return A.TNum()
            self.err("P306", f"`number from` works on text and decimals, not {ty}.", e)
            return TErr()
        if op == "decimal_from":
            if isinstance(ty, A.TText):
                return A.TMaybe(A.TDec())
            if isinstance(ty, _NUMERIC):
                return A.TDec()
            self.err("P306", f"`decimal from` works on text and numbers, not {ty}.", e)
            return TErr()
        if op in ("sorted", "reversed"):
            if isinstance(ty, A.TList) and isinstance(ty.elem, _ORDERED):
                return ty
            if op == "reversed" and isinstance(ty, A.TText):
                return A.TText()
            self.err("P306", f"`{op}` needs a list of numbers or text"
                     + (" (or text)" if op == "reversed" else "") + f", but this is {ty}.", e)
            return TErr()
        raise AssertionError(f"unknown prefix op {op}")

    def _infer_item(self, e: A.ItemOf) -> A.Type:
        cty = self.infer(e.container)
        ity = self.infer(e.index)
        if isinstance(cty, A.TList):
            if not self.assignable(A.TNum(), ity):
                self.type_mismatch(A.TNum(), ity, e.index, "A list position")
            return cty.elem
        if isinstance(cty, A.TMap):
            if not self.assignable(cty.key, ity):
                self.type_mismatch(cty.key, ity, e.index, "This map's keys")
            return cty.val
        if isinstance(cty, A.TText):
            self.err("P306", "Text has no items; split it first: `t split by \"\"` "
                     "is not supported — use `split by` with a separator.", e)
            return TErr()
        if not isinstance(cty, TErr):
            self.err("P306", f"`item … of …` works on lists and maps, not {cty}.", e)
        return TErr()

    def _infer_list(self, e: A.ListLit) -> A.Type:
        tys = [self.infer(it) for it in e.items]
        elem: A.Type | None = None
        for it, ty in zip(e.items, tys):
            if isinstance(ty, TErr):
                return TErr()
            if isinstance(ty, TNothing):
                self.err("P308", "A list cannot start from bare `nothing`.", it)
                return TErr()
            if elem is None:
                elem = ty
            elif elem == ty:
                pass
            elif isinstance(elem, A.TNum) and isinstance(ty, A.TDec):
                elem = A.TDec()
            elif isinstance(elem, A.TDec) and isinstance(ty, A.TNum):
                pass
            else:
                self.err("P301", f"This list mixes {elem} and {ty}; lists hold one type.", it)
                return TErr()
        return A.TList(elem if elem is not None else TErr())

    def _infer_construct(self, e: A.Construct) -> A.Type:
        rec = self.records.get(e.record)
        if rec is None:
            hint = None
            s = _suggest(e.record, self.records)
            if s:
                hint = f'Did you mean "{s}"?'
            elif e.record in self.enums:
                hint = f"{e.record} is a kind — use one of its variants directly: " \
                       f"{', '.join(self.enums[e.record].variants)}."
            self.err("P205", f'There is no record called "{e.record}".', e, hint=hint)
            for _, v in e.inits:
                self.infer(v)
            return TErr()
        field_types = dict(rec.fields)
        given = set()
        for fname, fval in e.inits:
            vty = self.infer(fval)
            if fname not in field_types:
                s = _suggest(fname, field_types)
                hint = f'Did you mean "{s}"?' if s else \
                    f"{rec.name} has: {', '.join(n for n, _ in rec.fields)}."
                self.err("P204", f'"{fname}" is not a field of {rec.name}.', fval, hint=hint)
                continue
            if fname in given:
                self.err("P206", f'The field "{fname}" is given twice.', fval)
                continue
            given.add(fname)
            if not self.assignable(field_types[fname], vty):
                self.type_mismatch(field_types[fname], vty, fval, f'The field "{fname}"')
        missing = [n for n, _ in rec.fields if n not in given]
        if missing:
            self.err("P206",
                     f"This {rec.name} is missing: {', '.join(missing)}.",
                     e, hint="Every field must be given when building a record.")
        return A.TRecord(rec.name)


def check_program(program: A.Program) -> list[Diagnostic]:
    """Convenience entry point. Returns diagnostics (empty list = all good)."""
    return Checker(program).check()
