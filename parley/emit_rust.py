"""Parley → Rust emitter.

Every Parley construct maps to exactly one Rust construct. The checker has
already annotated the AST with types, so emission is mechanical:

  * heap values (text, lists, maps, records) are cloned when stored; read-only
    non-changing function parameters are borrowed in generated Rust
  * `changing` parameters become `&mut T`
  * runtime failures panic with English messages; `fn main` catches them and
    `attempt:` blocks scope them
  * a line map records which Parley line produced each Rust line, so any
    residual rustc diagnostic can be pointed back at the .par source
"""

from __future__ import annotations

from . import ast_nodes as A

RUST_KEYWORDS = {
    "as", "async", "await", "break", "const", "continue", "crate", "dyn",
    "else", "enum", "extern", "false", "fn", "for", "if", "impl", "in",
    "let", "loop", "match", "mod", "move", "mut", "pub", "ref", "return",
    "self", "static", "struct", "super", "trait", "true", "type", "union",
    "unsafe", "use", "where", "while", "yield",
    # reserved for future use
    "abstract", "become", "box", "do", "final", "gen", "macro", "override",
    "priv", "try", "typeof", "unsized", "virtual",
}

RESERVED_TYPE_NAMES = {
    "String", "Vec", "Option", "Box", "HashMap", "Result", "Self", "Clone",
    "Copy", "Debug", "Display", "PartialEq", "Ord", "Eq", "Send", "Sync",
}


def safe(name: str) -> str:
    if name in RUST_KEYWORDS or name == "main" or name.startswith("parley_"):
        return name + "_p"
    return name


def camel(name: str) -> str:
    out = "".join(part.capitalize() for part in name.split("_") if part)
    if out in RESERVED_TYPE_NAMES:
        out = "P" + out
    return out


def rust_type(ty: A.Type) -> str:
    if isinstance(ty, A.TNum):
        return "i64"
    if isinstance(ty, A.TDec):
        return "f64"
    if isinstance(ty, A.TText):
        return "String"
    if isinstance(ty, A.TBool):
        return "bool"
    if isinstance(ty, A.TUnit):
        return "()"
    if isinstance(ty, A.TList):
        return f"Vec<{rust_type(ty.elem)}>"
    if isinstance(ty, A.TMap):
        return f"HashMap<{rust_type(ty.key)}, {rust_type(ty.val)}>"
    if isinstance(ty, A.TMaybe):
        return f"Option<{rust_type(ty.elem)}>"
    if isinstance(ty, (A.TRecord, A.TEnum)):
        return camel(ty.name)
    if isinstance(ty, A.TFunc):
        params = ", ".join(rust_type(p) for p in ty.params)
        ret = f" -> {rust_type(ty.ret)}" if ty.ret is not None else ""
        return f"Rc<dyn Fn({params}){ret}>"
    raise AssertionError(f"no rust type for {ty}")


def rust_str_lit(s: str, for_format: bool = False) -> str:
    out = []
    for c in s:
        if c == "\\":
            out.append("\\\\")
        elif c == '"':
            out.append('\\"')
        elif c == "\n":
            out.append("\\n")
        elif c == "\t":
            out.append("\\t")
        elif c == "\r":
            out.append("\\r")
        elif c in "{}" and for_format:
            out.append(c + c)
        else:
            out.append(c)
    return "".join(out)


PRELUDE = r"""
use std::collections::HashMap;
use std::cell::RefCell;
use std::rc::Rc;

thread_local! {
    static LAST_ERROR: RefCell<String> = RefCell::new(String::new());
}

fn parley_last_error() -> String {
    LAST_ERROR.with(|e| e.borrow().clone())
}

fn parley_yesno(b: bool) -> &'static str { if b { "yes" } else { "no" } }

fn parley_fmt_maybe_disp<T: std::fmt::Display>(o: &Option<T>) -> String {
    match o { Some(v) => format!("{}", v), None => "nothing".to_string() }
}

fn parley_fmt_maybe_yesno(o: &Option<bool>) -> String {
    match o { Some(v) => parley_yesno(*v).to_string(), None => "nothing".to_string() }
}

fn parley_fmt_maybe_dbg<T: std::fmt::Debug>(o: &Option<T>) -> String {
    match o { Some(v) => format!("{:?}", v), None => "nothing".to_string() }
}

fn parley_value<T: Clone>(o: &Option<T>) -> T {
    match o {
        Some(v) => v.clone(),
        None => panic!("Tried to get the value of nothing."),
    }
}

fn parley_item<T: Clone>(xs: &[T], i: i64) -> T {
    if i < 1 || (i as usize) > xs.len() {
        panic!("There is no item {} — the list has {} item(s).", i, xs.len());
    }
    xs[(i - 1) as usize].clone()
}

fn parley_set_item<T>(xs: &mut Vec<T>, i: i64, v: T) {
    if i < 1 || (i as usize) > xs.len() {
        panic!("Cannot set item {} — the list has {} item(s).", i, xs.len());
    }
    xs[(i - 1) as usize] = v;
}

fn parley_remove<T>(xs: &mut Vec<T>, i: i64) {
    if i < 1 || (i as usize) > xs.len() {
        panic!("Cannot remove item {} — the list has {} item(s).", i, xs.len());
    }
    xs.remove((i - 1) as usize);
}

fn parley_get<K: std::hash::Hash + Eq + std::fmt::Debug, V: Clone>(m: &HashMap<K, V>, k: &K) -> V {
    match m.get(k) {
        Some(v) => v.clone(),
        None => panic!("There is no item {:?} in the map.", k),
    }
}

fn parley_keys<K: Ord + Clone, V>(m: &HashMap<K, V>) -> Vec<K> {
    let mut ks: Vec<K> = m.keys().cloned().collect();
    ks.sort();
    ks
}

fn parley_sum_i(xs: &[i64]) -> i64 { xs.iter().sum() }
fn parley_sum_f(xs: &[f64]) -> f64 { xs.iter().sum() }

fn parley_min<T: PartialOrd + Clone>(xs: &[T]) -> T {
    if xs.is_empty() { panic!("Cannot take the smallest of an empty list."); }
    let mut best = &xs[0];
    for x in xs { if x < best { best = x; } }
    best.clone()
}

fn parley_max<T: PartialOrd + Clone>(xs: &[T]) -> T {
    if xs.is_empty() { panic!("Cannot take the largest of an empty list."); }
    let mut best = &xs[0];
    for x in xs { if x > best { best = x; } }
    best.clone()
}

fn parley_sorted<T: PartialOrd + Clone>(xs: &[T]) -> Vec<T> {
    let mut v = xs.to_vec();
    v.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    v
}

fn parley_reversed<T: Clone>(xs: &[T]) -> Vec<T> {
    let mut v = xs.to_vec();
    v.reverse();
    v
}

fn parley_concat<T: Clone>(a: &[T], b: &[T]) -> Vec<T> {
    let mut v = a.to_vec();
    v.extend_from_slice(b);
    v
}

fn parley_split(s: &str, sep: &str) -> Vec<String> {
    if sep.is_empty() { panic!("Cannot split by empty text."); }
    s.split(sep).map(|p| p.to_string()).collect()
}

fn parley_position(needle: &str, text: &str) -> Option<i64> {
    text.find(needle).map(|byte_index| {
        let chars_before = text[..byte_index].chars().count() as i64;
        chars_before + 1
    })
}

fn parley_count(needle: &str, text: &str) -> i64 {
    if needle.is_empty() {
        return text.chars().count() as i64 + 1;
    }
    let mut count = 0i64;
    let mut rest = text;
    while let Some(byte_index) = rest.find(needle) {
        count += 1;
        rest = &rest[(byte_index + needle.len())..];
    }
    count
}

fn parley_div(a: f64, b: f64) -> f64 {
    if b == 0.0 { panic!("Cannot divide by zero."); }
    a / b
}

fn parley_rem(a: i64, b: i64) -> i64 {
    if b == 0 { panic!("Cannot take a remainder after dividing by zero."); }
    a % b
}

fn parley_pow(a: i64, b: i64) -> i64 {
    if b < 0 { panic!("Cannot raise a whole number to a negative power — use decimals."); }
    match a.checked_pow(b as u32) {
        Some(v) => v,
        None => panic!("That power is too big to compute."),
    }
}

fn parley_sqrt(x: f64) -> f64 {
    if x < 0.0 { panic!("Cannot take the square root of a negative number."); }
    x.sqrt()
}

fn parley_parse_int(s: &str) -> Option<i64> { s.trim().parse::<i64>().ok() }
fn parley_parse_dec(s: &str) -> Option<f64> { s.trim().parse::<f64>().ok() }

fn parley_ask(prompt: &str) -> String {
    use std::io::Write;
    print!("{}", prompt);
    std::io::stdout().flush().ok();
    let mut line = String::new();
    match std::io::stdin().read_line(&mut line) {
        Ok(0) => panic!("No more input to read."),
        Ok(_) => {}
        Err(_) => panic!("Could not read input."),
    }
    line.trim_end_matches(['\r', '\n']).to_string()
}

fn parley_ask_num(prompt: &str) -> Option<i64> { parley_parse_int(&parley_ask(prompt)) }

fn parley_read_file(p: &str) -> Option<String> { std::fs::read_to_string(p).ok() }

fn parley_write_file(p: &str, content: &str, append: bool) {
    use std::io::Write;
    let r = if append {
        std::fs::OpenOptions::new().create(true).append(true).open(p)
            .and_then(|mut f| f.write_all(content.as_bytes()))
    } else {
        std::fs::write(p, content)
    };
    if let Err(e) = r { panic!("Could not write to file \"{}\": {}.", p, e); }
}

fn parley_random(lo: i64, hi: i64) -> i64 {
    use std::sync::atomic::{AtomicU64, Ordering};
    static SEED: AtomicU64 = AtomicU64::new(0);
    if SEED.load(Ordering::Relaxed) == 0 {
        let t = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_nanos() as u64)
            .unwrap_or(0x9E3779B97F4A7C15);
        SEED.store(t | 1, Ordering::Relaxed);
    }
    let mut x = SEED.load(Ordering::Relaxed);
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    SEED.store(x, Ordering::Relaxed);
    let (a, b) = if lo <= hi { (lo, hi) } else { (hi, lo) };
    let span = (b - a + 1) as u64;
    a + (x % span) as i64
}

fn main() {
    std::panic::set_hook(Box::new(|info| {
        let msg = if let Some(s) = info.payload().downcast_ref::<&str>() {
            s.to_string()
        } else if let Some(s) = info.payload().downcast_ref::<String>() {
            s.clone()
        } else {
            "something went wrong".to_string()
        };
        LAST_ERROR.with(|e| *e.borrow_mut() = msg);
    }));
    if std::panic::catch_unwind(main_p).is_err() {
        eprintln!("The program stopped: {}", parley_last_error());
        std::process::exit(1);
    }
}
""".strip()


class Emitter:
    def __init__(self, program: A.Program):
        self.program = program
        self.lines: list[str] = []
        self.linemap: dict[int, int] = {}   # rust line (1-based) -> parley line
        self.indent = 0
        self.enums = {e.name: e for e in program.enums}
        self.tmp = 0
        self.borrowed_params: set[str] = set()

    # --------------------------------------------------------------- output

    def out(self, code: str, par_line: int = 0):
        self.lines.append("    " * self.indent + code)
        if par_line:
            self.linemap[len(self.lines)] = par_line

    def fresh(self, base: str) -> str:
        self.tmp += 1
        return f"__{base}{self.tmp}"

    # --------------------------------------------------------------- emit

    def emit(self) -> tuple[str, dict[int, int]]:
        self.out("#![allow(unused_mut, unused_variables, dead_code, unused_imports,")
        self.out("         unreachable_code, unused_parens, non_snake_case)]")
        self.out("")
        for line in PRELUDE.splitlines():
            self.out(line)
        self.out("")
        for r in self.program.records:
            self.emit_record(r)
        for e in self.program.enums:
            self.emit_enum(e)
        for f in self.program.funcs:
            self.emit_func(f)
        return "\n".join(self.lines) + "\n", self.linemap

    def emit_record(self, r: A.RecordDef):
        self.out("#[derive(Clone, Debug, PartialEq)]", r.line)
        self.out(f"struct {camel(r.name)} {{", r.line)
        self.indent += 1
        for fname, fty in r.fields:
            self.out(f"{safe(fname)}: {rust_type(fty)},", r.line)
        self.indent -= 1
        self.out("}")
        self.out("")

    def emit_enum(self, e: A.EnumDef):
        name = camel(e.name)
        self.out("#[derive(Clone, Copy, Debug, PartialEq)]", e.line)
        self.out(f"enum {name} {{", e.line)
        self.indent += 1
        for v in e.variants:
            self.out(f"{camel(v)},", e.line)
        self.indent -= 1
        self.out("}")
        self.out(f"impl std::fmt::Display for {name} {{")
        self.indent += 1
        self.out("fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {")
        self.indent += 1
        self.out("match self {")
        self.indent += 1
        for v in e.variants:
            self.out(f'{name}::{camel(v)} => write!(f, "{v}"),')
        self.indent -= 1
        self.out("}")
        self.indent -= 1
        self.out("}")
        self.indent -= 1
        self.out("}")
        self.out("")

    def fn_name(self, name: str) -> str:
        return "main_p" if name == "main" else safe(name)

    def param_takes_ref(self, p: A.Param) -> bool:
        return not p.changing and A.is_heap(p.type)

    def mutated_names_in_block(self, body: list[A.Stmt]) -> set[str]:
        out: set[str] = set()
        for st in body:
            out |= self.mutated_names_in_stmt(st)
        return out

    def mutated_names_in_stmt(self, st: A.Stmt) -> set[str]:
        out: set[str] = set()
        if isinstance(st, A.Let):
            return self.mutated_names_in_expr(st.value)
        if isinstance(st, A.SetVar):
            return {st.target.base} | self.mutated_names_in_expr(st.value)
        if isinstance(st, A.SetItem):
            return (
                {st.target.base}
                | self.mutated_names_in_expr(st.index)
                | self.mutated_names_in_expr(st.value)
            )
        if isinstance(st, A.Say):
            return self.mutated_names_in_expr(st.value)
        if isinstance(st, A.If):
            for cond, body in st.arms:
                out |= self.mutated_names_in_expr(cond)
                out |= self.mutated_names_in_block(body)
            if st.otherwise is not None:
                out |= self.mutated_names_in_block(st.otherwise)
            return out
        if isinstance(st, A.When):
            out |= self.mutated_names_in_expr(st.subject)
            for _, body in st.arms:
                out |= self.mutated_names_in_block(body)
            if st.otherwise is not None:
                out |= self.mutated_names_in_block(st.otherwise)
            return out
        if isinstance(st, A.While):
            return self.mutated_names_in_expr(st.cond) | self.mutated_names_in_block(st.body)
        if isinstance(st, A.Repeat):
            return self.mutated_names_in_expr(st.count) | self.mutated_names_in_block(st.body)
        if isinstance(st, A.ForRange):
            return (
                self.mutated_names_in_expr(st.lo)
                | self.mutated_names_in_expr(st.hi)
                | self.mutated_names_in_block(st.body)
            )
        if isinstance(st, A.ForEach):
            return self.mutated_names_in_expr(st.iter) | self.mutated_names_in_block(st.body)
        if isinstance(st, A.Give):
            return self.mutated_names_in_expr(st.value) if st.value is not None else set()
        if isinstance(st, A.Attempt):
            return self.mutated_names_in_block(st.body) | self.mutated_names_in_block(st.handler)
        if isinstance(st, A.Add):
            return {st.target.base} | self.mutated_names_in_expr(st.value)
        if isinstance(st, A.RemoveItem):
            return {st.target.base} | self.mutated_names_in_expr(st.index)
        if isinstance(st, A.WriteFile):
            return self.mutated_names_in_expr(st.value) | self.mutated_names_in_expr(st.path)
        if isinstance(st, A.CallStmt):
            return self.mutated_names_from_call(st) | self.mutated_names_in_exprs(st.args)
        return set()

    def mutated_names_in_exprs(self, exprs: list[A.Expr]) -> set[str]:
        out: set[str] = set()
        for expr in exprs:
            out |= self.mutated_names_in_expr(expr)
        return out

    def mutated_names_from_call(self, node) -> set[str]:
        fn = getattr(node, "target_fn", None)
        if fn is None:
            return set()
        out: set[str] = set()
        for prm, arg in zip(fn.params, node.args):
            if prm.changing and isinstance(arg, A.Var):
                out.add(arg.name)
        return out

    def mutated_names_in_expr(self, e: A.Expr | None) -> set[str]:
        if e is None:
            return set()
        if isinstance(e, A.Str):
            return self.mutated_names_in_exprs([p for p in e.parts if isinstance(p, A.Expr)])
        if isinstance(e, A.FieldGet):
            return self.mutated_names_in_expr(e.obj)
        if isinstance(e, A.BinOp) or isinstance(e, A.Compare):
            return self.mutated_names_in_expr(e.left) | self.mutated_names_in_expr(e.right)
        if isinstance(e, A.Not) or isinstance(e, A.Neg) or isinstance(e, A.PrefixOp):
            return self.mutated_names_in_expr(e.value)
        if isinstance(e, A.SplitBy) or isinstance(e, A.JoinedWith):
            return self.mutated_names_in_expr(e.value) | self.mutated_names_in_expr(e.sep)
        if isinstance(e, A.ReplacingWith):
            return (
                self.mutated_names_in_expr(e.value)
                | self.mutated_names_in_expr(e.old)
                | self.mutated_names_in_expr(e.new)
            )
        if isinstance(e, A.PositionOf):
            return self.mutated_names_in_expr(e.needle) | self.mutated_names_in_expr(e.value)
        if isinstance(e, A.CountOf):
            return self.mutated_names_in_expr(e.needle) | self.mutated_names_in_expr(e.value)
        if isinstance(e, A.Remainder):
            return self.mutated_names_in_expr(e.left) | self.mutated_names_in_expr(e.right)
        if isinstance(e, A.ItemOf):
            return self.mutated_names_in_expr(e.index) | self.mutated_names_in_expr(e.container)
        if isinstance(e, A.ReadFile) or isinstance(e, A.Ask):
            return self.mutated_names_in_expr(e.path if isinstance(e, A.ReadFile) else e.prompt)
        if isinstance(e, A.RandomFrom):
            return self.mutated_names_in_expr(e.lo) | self.mutated_names_in_expr(e.hi)
        if isinstance(e, A.ListLit):
            return self.mutated_names_in_exprs(e.items)
        if isinstance(e, A.Construct):
            return self.mutated_names_in_exprs([value for _, value in e.inits])
        if isinstance(e, A.CallExpr):
            return self.mutated_names_from_call(e) | self.mutated_names_in_exprs(e.args)
        return set()

    def emit_func(self, fn: A.FuncDef):
        mutated_params = self.mutated_names_in_block(fn.body)
        borrowed_params = {
            p.name for p in fn.params
            if self.param_takes_ref(p) and p.name not in mutated_params
        }
        params = []
        for p in fn.params:
            t = rust_type(p.type)
            if p.changing:
                rendered = f"&mut {t}"
            elif self.param_takes_ref(p):
                rendered = f"&{t}"
            else:
                rendered = t
            params.append(f"{safe(p.name)}: {rendered}")
        ret = f" -> {rust_type(fn.ret)}" if fn.ret is not None else ""
        self.out(f"fn {self.fn_name(fn.name)}({', '.join(params)}){ret} {{", fn.line)
        self.cur_ret = fn.ret
        self.indent += 1
        for p in fn.params:
            if p.changing:
                continue
            n = safe(p.name)
            if self.param_takes_ref(p):
                if p.name in mutated_params:
                    self.out(f"let mut {n}: {rust_type(p.type)} = (*{n}).clone();", fn.line)
            else:
                self.out(f"let mut {n} = {n};", fn.line)
        self.changing = {p.name for p in fn.params if p.changing}
        self.borrowed_params = borrowed_params
        self.emit_block(fn.body)
        self.borrowed_params = set()
        self.indent -= 1
        self.out("}")
        self.out("")

    def emit_block(self, body: list[A.Stmt]):
        for st in body:
            self.emit_stmt(st)

    # --------------------------------------------------------------- places

    def is_place(self, e: A.Expr) -> bool:
        if isinstance(e, A.Var):
            return not getattr(e, "is_call", False) and not hasattr(e, "variant_of")
        if isinstance(e, A.FieldGet):
            return self.is_place(e.obj)
        return False

    def place(self, e: A.Expr) -> str:
        if isinstance(e, A.Var):
            n = safe(e.name)
            if e.name in self.borrowed_params:
                return f"(*{n})"
            return f"(*{n})" if getattr(e, "is_changing", False) else n
        if isinstance(e, A.FieldGet):
            return f"{self.place(e.obj)}.{safe(e.field_name)}"
        raise AssertionError("not a place")

    def lplace(self, lv: A.LValue) -> str:
        n = safe(lv.base)
        out = f"(*{n})" if getattr(lv, "is_changing", False) else n
        for f in lv.fields:
            out += f".{safe(f)}"
        return out

    def borrow(self, e: A.Expr) -> str:
        """An expression usable behind a reference — places stay un-cloned."""
        if self.is_place(e):
            return self.place(e)
        return self.value(e)

    # --------------------------------------------------------------- values

    def value(self, e: A.Expr, expected: A.Type | None = None) -> str:
        s = self._value(e)
        if expected is not None and isinstance(expected, A.TDec) and isinstance(e.ty, A.TNum):
            s = f"(({s}) as f64)"
        return s

    def _num_pair(self, l: A.Expr, r: A.Expr, want_dec: bool) -> tuple[str, str]:
        ls, rs = self.value(l), self.value(r)
        if want_dec:
            if isinstance(l.ty, A.TNum):
                ls = f"(({ls}) as f64)"
            if isinstance(r.ty, A.TNum):
                rs = f"(({rs}) as f64)"
        return ls, rs

    def fmt_arg(self, e: A.Expr) -> tuple[str, str]:
        """(format-spec, argument) for one interpolated/said value."""
        ty = e.ty
        if isinstance(ty, A.TBool):
            return "{}", f"parley_yesno({self.value(e)})"
        if isinstance(ty, A.TMaybe):
            if isinstance(ty.elem, A.TBool):
                fn = "parley_fmt_maybe_yesno"
            elif isinstance(ty.elem, (A.TNum, A.TDec, A.TText)):
                fn = "parley_fmt_maybe_disp"
            else:
                fn = "parley_fmt_maybe_dbg"
            return "{}", f"{fn}(&({self.borrow(e)}))"
        if isinstance(ty, (A.TList, A.TMap, A.TRecord)):
            return "{:?}", f"&({self.borrow(e)})"
        # text, numbers, enums (Display)
        return "{}", f"&({self.borrow(e)})"

    def _value(self, e: A.Expr) -> str:
        ty = e.ty
        if isinstance(e, A.Num):
            return f"{e.value}i64"
        if isinstance(e, A.Dec):
            s = repr(e.value)
            if not any(c in s for c in ".e"):
                s += ".0"
            return s + "f64"
        if isinstance(e, A.YesLit):
            return "true"
        if isinstance(e, A.NoLit):
            return "false"
        if isinstance(e, A.NothingLit):
            return "None"
        if isinstance(e, A.TheError):
            return "parley_last_error()"
        if isinstance(e, A.Str):
            if e.is_plain:
                return f'"{rust_str_lit(e.plain_text())}".to_string()'
            fmt, args = [], []
            for p in e.parts:
                if isinstance(p, str):
                    fmt.append(rust_str_lit(p, for_format=True))
                else:
                    spec, arg = self.fmt_arg(p)
                    fmt.append(spec)
                    args.append(arg)
            return f'format!("{"".join(fmt)}", {", ".join(args)})'
        if isinstance(e, A.Var):
            if hasattr(e, "variant_of"):
                return f"{camel(e.variant_of)}::{camel(e.name)}"
            if getattr(e, "is_call", False):
                return f"{self.fn_name(e.name)}()"
            p = self.place(e)
            return f"{p}.clone()" if A.is_heap(ty) else p
        if isinstance(e, A.FieldGet):
            if self.is_place(e):
                p = self.place(e)
                return f"{p}.clone()" if A.is_heap(ty) else p
            obj = self.value(e.obj)
            return f"({obj}).{safe(e.field_name)}"
        if isinstance(e, A.BinOp):
            return self._value_binop(e)
        if isinstance(e, A.Compare):
            return self._value_compare(e)
        if isinstance(e, A.Not):
            return f"(!({self.value(e.value)}))"
        if isinstance(e, A.Neg):
            return f"(-({self.value(e.value)}))"
        if isinstance(e, A.SplitBy):
            return f"parley_split(&({self.borrow(e.value)}), &({self.borrow(e.sep)}))"
        if isinstance(e, A.JoinedWith):
            return f"({self.borrow(e.value)}).join(({self.borrow(e.sep)}).as_str())"
        if isinstance(e, A.ReplacingWith):
            return (
                f"({self.borrow(e.value)}).replace("
                f"({self.borrow(e.old)}).as_str(), "
                f"({self.borrow(e.new)}).as_str())"
            )
        if isinstance(e, A.PositionOf):
            return f"parley_position(&({self.borrow(e.needle)}), &({self.borrow(e.value)}))"
        if isinstance(e, A.CountOf):
            return f"parley_count(&({self.borrow(e.needle)}), &({self.borrow(e.value)}))"
        if isinstance(e, A.PrefixOp):
            return self._value_prefix(e)
        if isinstance(e, A.Remainder):
            return f"parley_rem({self.value(e.left)}, {self.value(e.right)})"
        if isinstance(e, A.ItemOf):
            cty = e.container.ty
            if isinstance(cty, A.TMap):
                return f"parley_get(&({self.borrow(e.container)}), &({self.value(e.index, cty.key)}))"
            return f"parley_item(&({self.borrow(e.container)}), {self.value(e.index)})"
        if isinstance(e, A.ReadFile):
            return f"parley_read_file(&({self.borrow(e.path)}))"
        if isinstance(e, A.Ask):
            fn = "parley_ask_num" if e.numeric else "parley_ask"
            return f"{fn}(&({self.borrow(e.prompt)}))"
        if isinstance(e, A.RandomFrom):
            return f"parley_random({self.value(e.lo)}, {self.value(e.hi)})"
        if isinstance(e, A.ListLit):
            elem = ty.elem if isinstance(ty, A.TList) else None
            items = ", ".join(self.value(it, elem) for it in e.items)
            return f"vec![{items}]"
        if isinstance(e, A.EmptyList):
            return f"Vec::<{rust_type(e.elem_type)}>::new()"
        if isinstance(e, A.EmptyMap):
            return f"HashMap::<{rust_type(e.key_type)}, {rust_type(e.val_type)}>::new()"
        if isinstance(e, A.Construct):
            rec = next(r for r in self.program.records if r.name == e.record)
            ftypes = dict(rec.fields)
            inits = ", ".join(
                f"{safe(n)}: {self.value(v, ftypes.get(n))}" for n, v in e.inits)
            return f"{camel(e.record)} {{ {inits} }}"
        if isinstance(e, A.CallExpr):
            if getattr(e, "fn_value", False):
                return self.value_call_str(e)
            return self.call_str(e.target_fn, e.args) if hasattr(e, "target_fn") else "/*?*/"
        if isinstance(e, A.FuncRef):
            return self.func_ref_value(e)
        if isinstance(e, A.Closure):
            return self.closure_value(e)
        raise AssertionError(f"no emission for {type(e).__name__}")

    def _render_inline_closure_body(self, body: list[A.Stmt], params: list[A.Param],
                                    ret: A.Type | None) -> str:
        saved_lines, saved_linemap = self.lines, self.linemap
        saved_indent, saved_ret = self.indent, self.cur_ret
        saved_changing = self.changing
        saved_borrowed_params = self.borrowed_params
        self.lines, self.linemap = [], {}
        self.indent = 0
        self.cur_ret = ret
        self.changing = set()
        self.borrowed_params = set()
        for p in params:
            n = safe(p.name)
            self.out(f"let mut {n} = {n};", p.line)
        self.emit_block(body)
        code = " ".join(line.strip() for line in self.lines)
        self.lines, self.linemap = saved_lines, saved_linemap
        self.indent, self.cur_ret = saved_indent, saved_ret
        self.changing = saved_changing
        self.borrowed_params = saved_borrowed_params
        return code

    def func_ref_value(self, e: A.FuncRef) -> str:
        fty = e.ty
        assert isinstance(fty, A.TFunc)
        fn = e.target_fn
        params = []
        args = []
        for i, (prm, pty) in enumerate(zip(fn.params, fty.params), 1):
            name = f"arg{i}"
            params.append(f"{name}: {rust_type(pty)}")
            args.append(f"&({name})" if self.param_takes_ref(prm) else name)
        ret = f" -> {rust_type(fty.ret)}" if fty.ret is not None else ""
        call = f"{self.fn_name(e.name)}({', '.join(args)})"
        return f"(Rc::new(move |{', '.join(params)}|{ret} {{ {call} }}) as {rust_type(fty)})"

    def closure_value(self, e: A.Closure) -> str:
        fty = e.ty
        assert isinstance(fty, A.TFunc)
        captures = []
        for name, ty in e.captures:
            src = (
                f"(*{safe(name)})"
                if name in self.changing or name in self.borrowed_params
                else safe(name)
            )
            val = f"{src}.clone()" if A.is_heap(ty) else src
            captures.append(f"let {safe(name)} = {val};")
        params = ", ".join(f"{safe(p.name)}: {rust_type(p.type)}" for p in e.params)
        ret = f" -> {rust_type(e.ret)}" if e.ret is not None else ""
        body = self._render_inline_closure_body(e.body, e.params, e.ret)
        setup = " ".join(captures)
        return f"{{ {setup} Rc::new(move |{params}|{ret} {{ {body} }}) as {rust_type(fty)} }}"

    def _value_binop(self, e: A.BinOp) -> str:
        op = e.op
        if op in ("and", "or"):
            sym = "&&" if op == "and" else "||"
            return f"(({self.value(e.left)}) {sym} ({self.value(e.right)}))"
        if op == "+" and isinstance(e.ty, A.TText):
            la, ra = self.borrow(e.left), self.borrow(e.right)
            return f'format!("{{}}{{}}", &({la}), &({ra}))'
        if op == "+" and isinstance(e.ty, A.TList):
            return f"parley_concat(&({self.borrow(e.left)}), &({self.borrow(e.right)}))"
        if op == "/":
            ls, rs = self._num_pair(e.left, e.right, want_dec=True)
            return f"parley_div({ls}, {rs})"
        if op == "%":
            return f"parley_rem({self.value(e.left)}, {self.value(e.right)})"
        if op == "pow":
            if isinstance(e.ty, A.TNum):
                return f"parley_pow({self.value(e.left)}, {self.value(e.right)})"
            ls, rs = self._num_pair(e.left, e.right, want_dec=True)
            return f"({ls}).powf({rs})"
        want_dec = isinstance(e.ty, A.TDec)
        ls, rs = self._num_pair(e.left, e.right, want_dec)
        sym = {"+": "+", "-": "-", "*": "*"}[op]
        return f"(({ls}) {sym} ({rs}))"

    def _value_compare(self, e: A.Compare) -> str:
        op = e.op
        if op in ("==", "!="):
            l_nothing = isinstance(e.left, A.NothingLit)
            r_nothing = isinstance(e.right, A.NothingLit)
            if l_nothing and r_nothing:
                return "true" if op == "==" else "false"
            if l_nothing or r_nothing:
                side = e.right if l_nothing else e.left
                method = "is_none" if op == "==" else "is_some"
                return f"({self.borrow(side)}).{method}()"
            if isinstance(e.left.ty, (A.TNum, A.TDec)) and isinstance(e.right.ty, (A.TNum, A.TDec)):
                want_dec = isinstance(e.left.ty, A.TDec) or isinstance(e.right.ty, A.TDec)
                ls, rs = self._num_pair(e.left, e.right, want_dec)
                return f"(({ls}) {op} ({rs}))"
            return f"(({self.borrow(e.left)}) {op} ({self.borrow(e.right)}))"
        if op in (">", "<", ">=", "<="):
            if isinstance(e.left.ty, A.TText):
                return f"(({self.borrow(e.left)}) {op} ({self.borrow(e.right)}))"
            want_dec = isinstance(e.left.ty, A.TDec) or isinstance(e.right.ty, A.TDec)
            ls, rs = self._num_pair(e.left, e.right, want_dec)
            return f"(({ls}) {op} ({rs}))"
        if op == "contains":
            lty = e.left.ty
            if isinstance(lty, A.TText):
                return f"({self.borrow(e.left)}).contains(({self.borrow(e.right)}).as_str())"
            if isinstance(lty, A.TMap):
                return f"({self.borrow(e.left)}).contains_key(&({self.borrow(e.right)}))"
            return f"({self.borrow(e.left)}).contains(&({self.value(e.right, lty.elem if isinstance(lty, A.TList) else None)}))"
        if op == "startswith":
            return f"({self.borrow(e.left)}).starts_with(({self.borrow(e.right)}).as_str())"
        if op == "endswith":
            return f"({self.borrow(e.left)}).ends_with(({self.borrow(e.right)}).as_str())"
        raise AssertionError(op)

    def _value_prefix(self, e: A.PrefixOp) -> str:
        op = e.op
        v = e.value
        vty = v.ty
        if op == "length":
            if isinstance(vty, A.TText):
                return f"(({self.borrow(v)}).chars().count() as i64)"
            return f"(({self.borrow(v)}).len() as i64)"
        if op == "sum":
            fn = "parley_sum_f" if isinstance(vty, A.TList) and isinstance(vty.elem, A.TDec) \
                else "parley_sum_i"
            return f"{fn}(&({self.borrow(v)}))"
        if op == "smallest":
            return f"parley_min(&({self.borrow(v)}))"
        if op == "largest":
            return f"parley_max(&({self.borrow(v)}))"
        if op == "upper":
            return f"({self.borrow(v)}).to_uppercase()"
        if op == "lower":
            return f"({self.borrow(v)}).to_lowercase()"
        if op == "trimmed":
            return f"({self.borrow(v)}).trim().to_string()"
        if op == "abs":
            return f"({self.value(v)}).abs()"
        if op in ("floor", "ceil", "rounded"):
            if isinstance(vty, A.TNum):
                return self.value(v)
            method = {"floor": "floor", "ceil": "ceil", "rounded": "round"}[op]
            return f"(({self.value(v)}).{method}() as i64)"
        if op == "sqrt":
            inner = self.value(v)
            if isinstance(vty, A.TNum):
                inner = f"(({inner}) as f64)"
            return f"parley_sqrt({inner})"
        if op == "value":
            return f"parley_value(&({self.borrow(v)}))"
        if op == "some":
            elem = e.ty.elem if isinstance(e.ty, A.TMaybe) else None
            return f"Some({self.value(v, elem)})"
        if op == "keys":
            return f"parley_keys(&({self.borrow(v)}))"
        if op == "text_from":
            spec, arg = self.fmt_arg(v)
            return f'format!("{spec}", {arg})'
        if op == "number_from":
            if isinstance(vty, A.TText):
                return f"parley_parse_int(&({self.borrow(v)}))"
            if isinstance(vty, A.TDec):
                return f"(({self.value(v)}) as i64)"
            return self.value(v)
        if op == "decimal_from":
            if isinstance(vty, A.TText):
                return f"parley_parse_dec(&({self.borrow(v)}))"
            if isinstance(vty, A.TNum):
                return f"(({self.value(v)}) as f64)"
            return self.value(v)
        if op == "sorted":
            return f"parley_sorted(&({self.borrow(v)}))"
        if op == "reversed":
            if isinstance(vty, A.TText):
                return f"({self.borrow(v)}).chars().rev().collect::<String>()"
            return f"parley_reversed(&({self.borrow(v)}))"
        raise AssertionError(op)

    def value_call_str(self, node) -> str:
        """Call through a variable holding a function value."""
        callee = safe(node.name)
        if getattr(node, "callee_changing", False):
            callee = f"(*{callee})"
        args = ", ".join(self.value(a, pt)
                         for a, pt in zip(node.args, node.fn_type.params))
        return f"{callee}({args})"

    def call_str(self, fn: A.FuncDef, args: list[A.Expr]) -> str:
        parts = []
        for prm, arg in zip(fn.params, args):
            if prm.changing:
                # checker guarantees arg is a plain Var
                n = safe(arg.name)
                parts.append(f"&mut *{n}" if getattr(arg, "is_changing", False) else f"&mut {n}")
            elif self.param_takes_ref(prm):
                parts.append(f"&({self.borrow(arg)})")
            else:
                parts.append(self.value(arg, prm.type))
        return f"{self.fn_name(fn.name)}({', '.join(parts)})"

    # --------------------------------------------------------------- statements

    def emit_stmt(self, st: A.Stmt):
        m = getattr(self, "em_" + type(st).__name__.lower(), None)
        if m is None:
            raise AssertionError(f"no emitter for {type(st).__name__}")
        m(st)

    def em_let(self, st: A.Let):
        ty = st.value.ty
        self.out(f"let mut {safe(st.name)}: {rust_type(ty)} = {self.value(st.value)};", st.line)

    def em_setvar(self, st: A.SetVar):
        self.out(f"{self.lplace(st.target)} = {self.value(st.value, st.target.ty)};", st.line)

    def em_setitem(self, st: A.SetItem):
        tty = st.target.ty
        place = self.lplace(st.target)
        if isinstance(tty, A.TMap):
            k = self.value(st.index, tty.key)
            v = self.value(st.value, tty.val)
            self.out(f"({place}).insert({k}, {v});", st.line)
        else:
            elem = tty.elem if isinstance(tty, A.TList) else None
            self.out(f"parley_set_item(&mut {place}, {self.value(st.index)}, "
                     f"{self.value(st.value, elem)});", st.line)

    def em_say(self, st: A.Say):
        spec, arg = self.fmt_arg(st.value)
        self.out(f'println!("{spec}", {arg});', st.line)

    def em_if(self, st: A.If):
        for i, (cond, body) in enumerate(st.arms):
            kw = "if" if i == 0 else "} else if"
            self.out(f"{kw} {self.value(cond)} {{", cond.line or st.line)
            self.indent += 1
            self.emit_block(body)
            self.indent -= 1
        if st.otherwise is not None:
            self.out("} else {")
            self.indent += 1
            self.emit_block(st.otherwise)
            self.indent -= 1
        self.out("}")

    def em_when(self, st: A.When):
        subj_ty = st.subject.ty
        if isinstance(subj_ty, A.TEnum):
            ename = camel(subj_ty.name)
            self.out(f"match {self.value(st.subject)} {{", st.line)
            self.indent += 1
            for pats, body in st.arms:
                rust_pats = " | ".join(f"{ename}::{camel(p.value)}" for p in pats)
                self.out(f"{rust_pats} => {{", pats[0].line or st.line)
                self.indent += 1
                self.emit_block(body)
                self.indent -= 1
                self.out("}")
            if st.otherwise is not None:
                self.out("_ => {")
                self.indent += 1
                self.emit_block(st.otherwise)
                self.indent -= 1
                self.out("}")
            elif not getattr(st, "exhaustive", False):
                self.out("_ => {}")
            self.indent -= 1
            self.out("}")
            return
        subj = self.fresh("when")
        self.out(f"let {subj} = {self.value(st.subject)};", st.line)
        first = True
        for pats, body in st.arms:
            cond = " || ".join(self._pattern_cond(subj, p, subj_ty) for p in pats)
            kw = "if" if first else "} else if"
            first = False
            self.out(f"{kw} {cond} {{", pats[0].line or st.line)
            self.indent += 1
            self.emit_block(body)
            self.indent -= 1
        if st.otherwise is not None:
            if first:
                self.emit_block(st.otherwise)
                return
            self.out("} else {")
            self.indent += 1
            self.emit_block(st.otherwise)
            self.indent -= 1
        if not first:
            self.out("}")

    def _pattern_num(self, value, subj_ty: A.Type) -> str:
        """A numeric pattern literal, typed to match the subject."""
        if isinstance(subj_ty, A.TDec):
            s = repr(float(value))
            if not any(c in s for c in ".e"):
                s += ".0"
            return s + "f64"
        return f"{value}i64"

    def _pattern_cond(self, subj: str, pat: A.Pattern, subj_ty: A.Type) -> str:
        if pat.kind in ("int", "dec"):
            return f"{subj} == {self._pattern_num(pat.value, subj_ty)}"
        if pat.kind == "range":
            lo, hi = pat.value
            return (f"({subj} >= {self._pattern_num(lo.value, subj_ty)} "
                    f"&& {subj} <= {self._pattern_num(hi.value, subj_ty)})")
        if pat.kind == "text":
            return f'{subj} == "{rust_str_lit(pat.value)}"'
        if pat.kind == "yes":
            return subj
        if pat.kind == "no":
            return f"!{subj}"
        raise AssertionError(pat.kind)

    def em_while(self, st: A.While):
        self.out(f"while {self.value(st.cond)} {{", st.line)
        self.indent += 1
        self.emit_block(st.body)
        self.indent -= 1
        self.out("}")

    def em_repeat(self, st: A.Repeat):
        self.out(f"for _ in 0..({self.value(st.count)}) {{", st.line)
        self.indent += 1
        self.emit_block(st.body)
        self.indent -= 1
        self.out("}")

    def em_forrange(self, st: A.ForRange):
        self.out(f"for {safe(st.var)} in ({self.value(st.lo)})..=({self.value(st.hi)}) {{",
                 st.line)
        self.indent += 1
        self.emit_block(st.body)
        self.indent -= 1
        self.out("}")

    def em_foreach(self, st: A.ForEach):
        self.out(f"for {safe(st.var)} in {self.value(st.iter)} {{", st.line)
        self.indent += 1
        self.emit_block(st.body)
        self.indent -= 1
        self.out("}")

    def em_give(self, st: A.Give):
        if st.value is None:
            self.out("return;", st.line)
        else:
            self.out(f"return {self.value(st.value, self.cur_ret)};", st.line)

    def em_stop(self, st: A.Stop):
        self.out("break;", st.line)

    def em_skip(self, st: A.Skip):
        self.out("continue;", st.line)

    def em_assert(self, st: A.Assert):
        message = self.value(st.message, A.TText()) if st.message is not None \
            else '"Assertion failed.".to_string()'
        self.out(f'if !({self.value(st.cond)}) {{ panic!("{{}}", {message}); }}', st.line)

    def em_fail(self, st: A.Fail):
        self.out(f'panic!("{{}}", {self.value(st.message, A.TText())});', st.line)

    def em_attempt(self, st: A.Attempt):
        flag = self.fresh("attempt")
        self.out(f"let {flag} = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {{",
                 st.line)
        self.indent += 1
        self.emit_block(st.body)
        self.indent -= 1
        self.out("}));")
        self.out(f"if {flag}.is_err() {{", st.line)
        self.indent += 1
        self.emit_block(st.handler)
        self.indent -= 1
        self.out("}")

    def em_add(self, st: A.Add):
        elem = st.target.ty.elem if isinstance(st.target.ty, A.TList) else None
        self.out(f"({self.lplace(st.target)}).push({self.value(st.value, elem)});", st.line)

    def em_removeitem(self, st: A.RemoveItem):
        tty = st.target.ty
        place = self.lplace(st.target)
        if isinstance(tty, A.TMap):
            self.out(f"({place}).remove(&({self.value(st.index, tty.key)}));", st.line)
        else:
            self.out(f"parley_remove(&mut {place}, {self.value(st.index)});", st.line)

    def em_writefile(self, st: A.WriteFile):
        self.out(f"parley_write_file(&({self.borrow(st.path)}), &({self.borrow(st.value)}), "
                 f"{'true' if st.append else 'false'});", st.line)

    def em_callstmt(self, st: A.CallStmt):
        if getattr(st, "fn_value", False):
            call = self.value_call_str(st)
            if st.fn_type.ret is not None:
                self.out(f"let _ = {call};", st.line)
            else:
                self.out(f"{call};", st.line)
            return
        if not hasattr(st, "target_fn"):
            return
        call = self.call_str(st.target_fn, st.args)
        if st.target_fn.ret is not None:
            self.out(f"let _ = {call};", st.line)
        else:
            self.out(f"{call};", st.line)


def emit_program(program: A.Program) -> tuple[str, dict[int, int]]:
    """Emit Rust for a checked program. Returns (source, rust_line -> par_line)."""
    return Emitter(program).emit()
