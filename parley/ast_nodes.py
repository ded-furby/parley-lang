"""AST node and type definitions for Parley.

Every node carries the (line, col) of its first token, measured against the
combined (include-expanded) source. Diagnostics translate those positions back
to the original file via the SourceMap. The checker annotates every expression
node with `.ty` before the emitter runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union


# ---------------------------------------------------------------- types

class Type:
    def __eq__(self, other):
        return type(self) is type(other) and self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(str(self))


class TNum(Type):
    def __str__(self):
        return "number"


class TDec(Type):
    def __str__(self):
        return "decimal"


class TText(Type):
    def __str__(self):
        return "text"


class TBool(Type):
    def __str__(self):
        return "yesno"


class TUnit(Type):
    def __str__(self):
        return "nothing at all"


class TList(Type):
    def __init__(self, elem: Type):
        self.elem = elem

    def __str__(self):
        return f"list of {self.elem}"


class TMap(Type):
    def __init__(self, key: Type, val: Type):
        self.key = key
        self.val = val

    def __str__(self):
        return f"map from {self.key} to {self.val}"


class TMaybe(Type):
    def __init__(self, elem: Type):
        self.elem = elem

    def __str__(self):
        return f"maybe {self.elem}"


class TNamed(Type):
    """A user-written type name, resolved by the checker to record or enum."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


class TRecord(Type):
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


class TEnum(Type):
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


class TFunc(Type):
    """A function value: Rust fn pointer, so Copy and zero-cost."""

    def __init__(self, params: list[Type], ret: Optional[Type]):
        self.params = params
        self.ret = ret

    def __str__(self):
        out = "(function"
        if self.params:
            out += " taking " + ", ".join(str(p) for p in self.params)
        if self.ret is not None:
            out += f" giving {self.ret}"
        return out + ")"


def is_heap(ty: Type) -> bool:
    """Types that are not Copy in Rust — assignment must clone."""
    if isinstance(ty, (TText, TList, TMap, TRecord)):
        return True
    if isinstance(ty, TMaybe):
        return is_heap(ty.elem)
    return False


# ---------------------------------------------------------------- base

@dataclass
class Node:
    line: int = field(default=0, kw_only=True)
    col: int = field(default=0, kw_only=True)


@dataclass
class Expr(Node):
    ty: Optional[Type] = field(default=None, kw_only=True)


# ---------------------------------------------------------------- program

@dataclass
class Param(Node):
    name: str
    type: Type
    changing: bool = False


@dataclass
class RecordDef(Node):
    name: str
    fields: list[tuple[str, Type]]


@dataclass
class EnumDef(Node):
    name: str
    variants: list[str]


@dataclass
class FuncDef(Node):
    name: str
    params: list[Param]
    ret: Optional[Type]
    body: list["Stmt"]


@dataclass
class Program(Node):
    records: list[RecordDef]
    enums: list[EnumDef]
    funcs: list[FuncDef]


# ---------------------------------------------------------------- lvalues

@dataclass
class LValue(Node):
    """A variable, optionally followed by a chain of 's field accesses."""
    base: str
    fields: list[str]
    ty: Optional[Type] = field(default=None, kw_only=True)

    def show(self) -> str:
        out = self.base
        for f in self.fields:
            out += f"'s {f}"
        return out


# ---------------------------------------------------------------- statements

@dataclass
class Stmt(Node):
    pass


@dataclass
class Let(Stmt):
    name: str
    value: Expr


@dataclass
class SetVar(Stmt):
    target: LValue
    value: Expr


@dataclass
class SetItem(Stmt):
    index: Expr
    target: LValue
    value: Expr


@dataclass
class Say(Stmt):
    value: Expr


@dataclass
class If(Stmt):
    arms: list[tuple[Expr, list[Stmt]]]
    otherwise: Optional[list[Stmt]]


@dataclass
class Pattern(Node):
    kind: str          # "int" | "dec" | "text" | "yes" | "no" | "name" | "range"
    value: Union[int, float, str, tuple, None]   # "range": (lo Pattern, hi Pattern)


@dataclass
class When(Stmt):
    subject: Expr
    arms: list[tuple[list[Pattern], list[Stmt]]]
    otherwise: Optional[list[Stmt]]


@dataclass
class While(Stmt):
    cond: Expr
    body: list[Stmt]


@dataclass
class Repeat(Stmt):
    count: Expr
    body: list[Stmt]


@dataclass
class ForRange(Stmt):
    var: str
    lo: Expr
    hi: Expr
    body: list[Stmt]


@dataclass
class ForEach(Stmt):
    var: str
    iter: Expr
    body: list[Stmt]


@dataclass
class Give(Stmt):
    value: Optional[Expr]


@dataclass
class Stop(Stmt):
    pass


@dataclass
class Skip(Stmt):
    pass


@dataclass
class Attempt(Stmt):
    body: list[Stmt]
    handler: list[Stmt]


@dataclass
class Add(Stmt):
    value: Expr
    target: LValue


@dataclass
class RemoveItem(Stmt):
    index: Expr
    target: LValue


@dataclass
class WriteFile(Stmt):
    value: Expr
    path: Expr
    append: bool


@dataclass
class CallStmt(Stmt):
    name: str
    args: list[Expr]


# ---------------------------------------------------------------- expressions

@dataclass
class Num(Expr):
    value: int


@dataclass
class Dec(Expr):
    value: float


@dataclass
class Str(Expr):
    """String literal; parts mixes plain text (str) and interpolated Expr."""
    parts: list[Union[str, Expr]]

    @property
    def is_plain(self) -> bool:
        return all(isinstance(p, str) for p in self.parts)

    def plain_text(self) -> str:
        return "".join(p for p in self.parts if isinstance(p, str))


@dataclass
class YesLit(Expr):
    pass


@dataclass
class NoLit(Expr):
    pass


@dataclass
class NothingLit(Expr):
    pass


@dataclass
class TheError(Expr):
    pass


@dataclass
class Var(Expr):
    name: str


@dataclass
class EnumLit(Expr):
    """Produced by the checker when a Var resolves to an enum variant."""
    enum: str
    variant: str


@dataclass
class FieldGet(Expr):
    obj: Expr
    field_name: str


@dataclass
class BinOp(Expr):
    op: str            # + - * / % pow and or
    left: Expr
    right: Expr


@dataclass
class Compare(Expr):
    op: str            # == != > < >= <= contains startswith endswith
    left: Expr
    right: Expr


@dataclass
class Not(Expr):
    value: Expr


@dataclass
class Neg(Expr):
    value: Expr


@dataclass
class SplitBy(Expr):
    value: Expr
    sep: Expr


@dataclass
class JoinedWith(Expr):
    value: Expr
    sep: Expr


@dataclass
class PrefixOp(Expr):
    """English prefix builtins: length of, sum of, sorted, value of, ..."""
    op: str
    value: Expr


@dataclass
class Remainder(Expr):
    left: Expr
    right: Expr


@dataclass
class ItemOf(Expr):
    index: Expr
    container: Expr


@dataclass
class ReadFile(Expr):
    path: Expr


@dataclass
class Ask(Expr):
    prompt: Expr
    numeric: bool


@dataclass
class RandomFrom(Expr):
    lo: Expr
    hi: Expr


@dataclass
class ListLit(Expr):
    items: list[Expr]


@dataclass
class EmptyList(Expr):
    elem_type: Type


@dataclass
class EmptyMap(Expr):
    key_type: Type
    val_type: Type


@dataclass
class Construct(Expr):
    record: str
    inits: list[tuple[str, Expr]]


@dataclass
class CallExpr(Expr):
    name: str
    args: list[Expr]


@dataclass
class FuncRef(Expr):
    """`the function NAME` — a named function used as a value."""
    name: str
