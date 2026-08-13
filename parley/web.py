"""Typed HTTP/JSON and browser/WASM project support for Parley.

The web layer deliberately uses ordinary Parley records and functions.  A
small JSON manifest binds exact HTTP routes to checked functions and selects
deterministic scalar functions for the browser ABI; it does not add a second
language or web-specific syntax to the compiler.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import json
from pathlib import Path
import re
from typing import Iterable

from . import ast_nodes as A
from .checker import check_program
from .diagnostics import Diagnostic, ParleyError
from .emit_rust import camel, emit_program, program_uses_json, rust_str_lit, rust_type, safe
from .parser import SourceMap, parse_program


WEB_MANIFEST = "parley.web.json"
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
FUNCTION_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
HTTP_METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"}

WEB_CARGO_TOML = """\
[package]
name = "parley_web"
version = "0.1.0"
edition = "2021"

[profile.release]
strip = true
# Same promise as the command target: overflow stops, never wraps.
overflow-checks = true
"""

WEB_CARGO_TOML_DERIVE = WEB_CARGO_TOML.replace(
    "[profile.release]",
    """[dependencies]
serde = { version = "=1.0.229", features = ["derive"] }
serde_json = "=1.0.151"

[profile.release]""",
)

WASM_CARGO_TOML = """\
[package]
name = "parley_browser"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[profile.release]
opt-level = "s"
lto = true
panic = "abort"
strip = true
overflow-checks = true
"""


class WebProjectError(Exception):
    """A safe, user-facing project or manifest error."""


@dataclass(frozen=True)
class Route:
    method: str
    path: str
    handler: str
    success_status: int


@dataclass(frozen=True)
class BrowserExport:
    name: str


@dataclass(frozen=True)
class WebProject:
    root: Path
    manifest_path: Path
    name: str
    entrypoint: Path
    static_dir: Path | None
    routes: tuple[Route, ...]
    host: str
    port: int
    max_body_bytes: int
    browser_entrypoint: Path | None
    browser_exports: tuple[BrowserExport, ...]


@dataclass(frozen=True)
class CheckedRoute:
    route: Route
    function: A.FuncDef
    has_request: bool
    body_param: A.Param | None


@dataclass(frozen=True)
class CheckedWeb:
    project: WebProject
    program: A.Program
    srcmap: SourceMap
    routes: tuple[CheckedRoute, ...]


@dataclass(frozen=True)
class CheckedBrowser:
    project: WebProject
    program: A.Program
    srcmap: SourceMap
    exports: tuple[A.FuncDef, ...]


def _contained(root: Path, raw: str, label: str, *, must_be_file: bool) -> Path:
    if not isinstance(raw, str) or not raw or Path(raw).is_absolute():
        raise WebProjectError(f"{label} must be a non-empty path inside the project")
    path = (root / raw).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise WebProjectError(f"{label} must stay inside the project") from exc
    if must_be_file and not path.is_file():
        raise WebProjectError(f"{label} does not exist: {raw}")
    if not must_be_file and not path.is_dir():
        raise WebProjectError(f"{label} does not exist: {raw}")
    return path


def _object(value, label: str) -> dict:
    if not isinstance(value, dict):
        raise WebProjectError(f"{label} must be a JSON object")
    return value


def _integer(value, label: str, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise WebProjectError(f"{label} must be a whole number from {lo} to {hi}")
    return value


def load_project(path: str | Path) -> WebProject:
    given = Path(path).resolve()
    manifest_path = given if given.is_file() else given / WEB_MANIFEST
    if not manifest_path.is_file():
        raise WebProjectError(f"cannot find {WEB_MANIFEST} at {given}")
    root = manifest_path.parent.resolve()
    try:
        data = json.loads(manifest_path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WebProjectError(f"cannot read {manifest_path.name}: {exc}") from exc
    data = _object(data, WEB_MANIFEST)
    if data.get("schema_version") != 1:
        raise WebProjectError("parley.web.json schema_version must be 1")
    name = data.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise WebProjectError("name must start with a letter and use letters, numbers, _ or -")
    entrypoint = _contained(root, data.get("entrypoint", "main.par"), "entrypoint",
                            must_be_file=True)

    raw_static = data.get("static_dir")
    static_dir = None
    if raw_static is not None:
        static_dir = _contained(root, raw_static, "static_dir", must_be_file=False)

    server = _object(data.get("server", {}), "server")
    host = server.get("host", "127.0.0.1")
    if not isinstance(host, str) or not host or any(c.isspace() for c in host):
        raise WebProjectError("server.host must be a host name or IP address without spaces")
    port = _integer(server.get("port", 8787), "server.port", 1, 65535)
    max_body = _integer(
        server.get("max_body_bytes", 1_048_576),
        "server.max_body_bytes", 1, 16_777_216,
    )

    raw_routes = data.get("routes", [])
    if not isinstance(raw_routes, list):
        raise WebProjectError("routes must be a JSON list")
    routes: list[Route] = []
    seen_routes: set[tuple[str, str]] = set()
    for index, raw in enumerate(raw_routes, 1):
        route = _object(raw, f"routes item {index}")
        method = route.get("method")
        if not isinstance(method, str) or method.upper() not in HTTP_METHODS:
            raise WebProjectError(
                f"routes item {index} method must be one of {', '.join(sorted(HTTP_METHODS))}")
        method = method.upper()
        route_path = route.get("path")
        if (not isinstance(route_path, str) or not route_path.startswith("/")
                or any(c in route_path for c in "?#\r\n")):
            raise WebProjectError(
                f"routes item {index} path must be an exact path beginning with /")
        handler = route.get("handler")
        if not isinstance(handler, str) or not FUNCTION_RE.fullmatch(handler):
            raise WebProjectError(f"routes item {index} handler is not a Parley function name")
        success = _integer(route.get("success_status", 200),
                           f"routes item {index} success_status", 200, 299)
        key = (method, route_path)
        if key in seen_routes:
            raise WebProjectError(f"route {method} {route_path} is declared twice")
        seen_routes.add(key)
        routes.append(Route(method, route_path, handler, success))
    if not routes and static_dir is None:
        raise WebProjectError("declare at least one route or a static_dir")

    browser_raw = data.get("browser")
    browser_entrypoint = None
    browser_exports: list[BrowserExport] = []
    if browser_raw is not None:
        browser = _object(browser_raw, "browser")
        browser_entrypoint = _contained(
            root, browser.get("entrypoint", data.get("entrypoint", "main.par")),
            "browser.entrypoint", must_be_file=True,
        )
        raw_exports = browser.get("exports")
        if not isinstance(raw_exports, list) or not raw_exports:
            raise WebProjectError("browser.exports must be a non-empty JSON list")
        seen_exports: set[str] = set()
        for index, raw in enumerate(raw_exports, 1):
            export = _object(raw, f"browser.exports item {index}")
            export_name = export.get("name")
            if not isinstance(export_name, str) or not FUNCTION_RE.fullmatch(export_name):
                raise WebProjectError(
                    f"browser.exports item {index} name is not a Parley function name")
            if export_name in seen_exports:
                raise WebProjectError(f"browser export {export_name} is declared twice")
            seen_exports.add(export_name)
            browser_exports.append(BrowserExport(export_name))

    return WebProject(
        root=root,
        manifest_path=manifest_path,
        name=name,
        entrypoint=entrypoint,
        static_dir=static_dir,
        routes=tuple(routes),
        host=host,
        port=port,
        max_body_bytes=max_body,
        browser_entrypoint=browser_entrypoint,
        browser_exports=tuple(browser_exports),
    )


def _diag(code: str, message: str, node: A.Node | None, srcmap: SourceMap,
          hint: str | None = None) -> Diagnostic:
    line = node.line if node is not None else 1
    diagnostic = Diagnostic(code, message, line=line, hint=hint)
    return srcmap.resolve([diagnostic])[0]


def _type_name(ty: A.Type) -> str:
    return str(ty)


def _json_type_error(ty: A.Type, records: dict[str, A.RecordDef], enums: set[str],
                     trail: set[str] | None = None) -> str | None:
    """Return why a checked type cannot cross JSON, or None when it can."""
    trail = set() if trail is None else set(trail)
    if isinstance(ty, (A.TNum, A.TDec, A.TText, A.TBool)):
        return None
    if isinstance(ty, A.TMaybe):
        return _json_type_error(ty.elem, records, enums, trail)
    if isinstance(ty, A.TList):
        return _json_type_error(ty.elem, records, enums, trail)
    if isinstance(ty, A.TMap):
        if not isinstance(ty.key, A.TText):
            return "JSON object maps must use text keys"
        return _json_type_error(ty.val, records, enums, trail)
    if isinstance(ty, A.TEnum):
        return None if ty.name in enums else f"unknown kind {ty.name}"
    if isinstance(ty, A.TRecord):
        if ty.name in trail:
            return f"recursive record {ty.name} cannot cross JSON yet"
        record = records.get(ty.name)
        if record is None:
            return f"unknown record {ty.name}"
        trail.add(ty.name)
        for field_name, field_type in record.fields:
            problem = _json_type_error(field_type, records, enums, trail)
            if problem:
                return f"field {field_name}: {problem}"
        return None
    return f"{_type_name(ty)} values cannot cross JSON"


def _web_request_ok(record: A.RecordDef | None) -> bool:
    if record is None:
        return False
    expected = [
        ("method", A.TText()),
        ("path", A.TText()),
        ("query", A.TText()),
        ("headers", A.TMap(A.TText(), A.TText())),
        ("body", A.TText()),
    ]
    return record.fields == expected


def check_web(project: WebProject) -> CheckedWeb:
    program, srcmap = parse_program(project.entrypoint)
    diagnostics = check_program(program, require_main=False)
    if diagnostics:
        raise ParleyError(srcmap.resolve(diagnostics))
    functions = {function.name: function for function in program.funcs}
    records = {record.name: record for record in program.records}
    enums = {enum.name for enum in program.enums}
    checked: list[CheckedRoute] = []
    contract_diags: list[Diagnostic] = []
    for route in project.routes:
        function = functions.get(route.handler)
        if function is None:
            contract_diags.append(_diag(
                "P710", f'Web route {route.method} {route.path} names missing function "{route.handler}".',
                None, srcmap, hint=f"Add `to {route.handler} ... giving ...:` to the entrypoint."))
            continue
        if function.ret is None:
            contract_diags.append(_diag(
                "P711", f'Web handler "{function.name}" must give back a JSON response value.',
                function, srcmap, hint="Add a `giving` type and give back that value on every path."))
            continue
        response_problem = _json_type_error(function.ret, records, enums)
        if response_problem:
            contract_diags.append(_diag(
                "P712", f'Web handler "{function.name}" response is not JSON-safe: {response_problem}.',
                function, srcmap))
            continue
        if len(function.params) > 2:
            contract_diags.append(_diag(
                "P713", f'Web handler "{function.name}" takes too many parameters.',
                function, srcmap,
                hint="Use no parameters, one typed JSON body, or web_request followed by a typed JSON body."))
            continue
        if any(param.changing for param in function.params):
            contract_diags.append(_diag(
                "P713", f'Web handler "{function.name}" cannot take changing parameters.',
                function, srcmap))
            continue
        has_request = False
        body_param = None
        params = list(function.params)
        if params and isinstance(params[0].type, A.TRecord) and params[0].type.name == "web_request":
            has_request = True
            if not _web_request_ok(records.get("web_request")):
                contract_diags.append(_diag(
                    "P714", "web_request does not have the required HTTP fields.",
                    records.get("web_request") or function, srcmap,
                    hint="Define method, path, query, headers, and body using the documented types and order."))
                continue
            params.pop(0)
        if len(params) == 1:
            body_param = params[0]
            problem = _json_type_error(body_param.type, records, enums)
            if problem:
                contract_diags.append(_diag(
                    "P715", f'Web handler "{function.name}" request body is not JSON-safe: {problem}.',
                    body_param, srcmap))
                continue
        elif params:
            contract_diags.append(_diag(
                "P713", f'Web handler "{function.name}" has an unsupported parameter shape.',
                function, srcmap,
                hint="Use no parameters, one typed JSON body, or web_request followed by a typed JSON body."))
            continue
        checked.append(CheckedRoute(route, function, has_request, body_param))
    if contract_diags:
        raise ParleyError(contract_diags)
    return CheckedWeb(project, program, srcmap, tuple(checked))


def _walk_declared(value) -> Iterable[A.Node]:
    if isinstance(value, A.Node):
        yield value
        for field in fields(value):
            child = getattr(value, field.name)
            yield from _walk_declared(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_declared(child)


def _wasm_effect_problem(function: A.FuncDef, functions: dict[str, A.FuncDef],
                         seen: set[str] | None = None) -> str | None:
    seen = set() if seen is None else seen
    if function.name in seen:
        return None
    seen.add(function.name)
    forbidden = {
        A.Say: "prints output", A.WriteFile: "writes files", A.ReadFile: "reads files",
        A.Ask: "reads terminal input", A.RandomFrom: "uses system randomness",
        A.Attempt: "catches native runtime failures", A.TheError: "reads a native runtime failure",
    }
    for node in _walk_declared(function.body):
        for cls, explanation in forbidden.items():
            if isinstance(node, cls):
                return f'{function.name} {explanation}'
        if isinstance(node, A.FuncRef) or isinstance(node, A.Closure):
            return f'{function.name} uses a dynamic function value'
        if isinstance(node, (A.CallExpr, A.CallStmt)):
            target = getattr(node, "target_fn", None)
            if target is None:
                return f'{function.name} makes a dynamic function call'
            problem = _wasm_effect_problem(target, functions, seen)
            if problem:
                return problem
        if isinstance(node, A.Var) and getattr(node, "is_call", False):
            target = functions.get(node.name)
            if target is not None:
                problem = _wasm_effect_problem(target, functions, seen)
                if problem:
                    return problem
    return None


def _wasm_scalar(ty: A.Type | None) -> bool:
    return isinstance(ty, (A.TNum, A.TDec, A.TBool))


def check_browser(project: WebProject) -> CheckedBrowser | None:
    if project.browser_entrypoint is None:
        return None
    program, srcmap = parse_program(project.browser_entrypoint)
    diagnostics = check_program(program, require_main=False)
    if diagnostics:
        raise ParleyError(srcmap.resolve(diagnostics))
    functions = {function.name: function for function in program.funcs}
    exports: list[A.FuncDef] = []
    contract_diags: list[Diagnostic] = []
    for export in project.browser_exports:
        function = functions.get(export.name)
        if function is None:
            contract_diags.append(_diag(
                "P720", f'Browser export names missing function "{export.name}".',
                None, srcmap))
            continue
        if function.ret is None or not _wasm_scalar(function.ret):
            contract_diags.append(_diag(
                "P721", f'Browser export "{function.name}" must give number, decimal, or yesno.',
                function, srcmap))
            continue
        bad_param = next((param for param in function.params
                          if param.changing or not _wasm_scalar(param.type)), None)
        if bad_param is not None:
            contract_diags.append(_diag(
                "P722", f'Browser export "{function.name}" has unsupported parameter "{bad_param.name}".',
                bad_param, srcmap,
                hint="The stable browser ABI currently accepts non-changing number, decimal, and yesno values."))
            continue
        problem = _wasm_effect_problem(function, functions)
        if problem:
            contract_diags.append(_diag(
                "P723", f'Browser export "{function.name}" is not deterministic: {problem}.',
                function, srcmap,
                hint="Move terminal, file, random, and dynamic-function work outside the browser export call graph."))
            continue
        exports.append(function)
    if contract_diags:
        raise ParleyError(contract_diags)
    return CheckedBrowser(project, program, srcmap, tuple(exports))


def _rust_arg(param: A.Param, name: str) -> str:
    return f"&{name}" if A.is_heap(param.type) else name


def _route_arm(checked: CheckedRoute, *, uses_program_json: bool) -> str:
    route = checked.route
    function = checked.function
    setup: list[str] = []
    args: list[str] = []
    if checked.has_request:
        setup.append("""
            let parley_request = WebRequest {
                method: request.method.clone(),
                path: request.path.clone(),
                query: request.query.clone(),
                headers: request.headers.clone(),
                body: request.body.clone(),
            };""".rstrip())
        args.append(_rust_arg(function.params[0], "parley_request"))
    if checked.body_param is not None:
        # rust_type lives on the emitter module; importing here avoids exposing
        # backend details in the manifest model.
        from .emit_rust import rust_type
        decode = (
            "serde_json::from_str(&request.body)"
            if uses_program_json
            else "parley_web_json_runtime::decode(&request.body)"
        )
        setup.append(f"""
            let content_type = request.headers.get("content-type")
                .and_then(|value| value.split(';').next()).unwrap_or("").trim();
            if content_type != "application/json" && !content_type.ends_with("+json") {{
                return parley_json_error(415, "json_content_type_required", "typed request bodies require application/json");
            }}
            let parley_body: {rust_type(checked.body_param.type)} = match {decode} {{
                Ok(value) => value,
                Err(error) => return parley_json_error(400, "invalid_json", &error.to_string()),
            }};""".rstrip())
        args.append(_rust_arg(checked.body_param, "parley_body"))
    setup_text = "\n".join(setup)
    call = f"{safe(function.name)}({', '.join(args)})"
    encode = (
        "serde_json::to_vec(&result)"
        if uses_program_json
        else "parley_web_json_runtime::encode(&result).map(String::into_bytes)"
    )
    return f'''        ("{rust_str_lit(route.method)}", "{rust_str_lit(route.path)}") => {{
{setup_text}
            let result = {call};
            match {encode} {{
                Ok(body) => ParleyHttpResponse::new({route.success_status}, "application/json; charset=utf-8", body),
                Err(error) => parley_json_error(500, "response_json_failed", &error.to_string()),
            }}
        }}'''


def _manual_serde_impls(program: A.Program) -> str:
    """Emit strict serde traits without compiling serde's proc-macro stack.

    Web projects need JSON at their typed route boundary even when the Parley
    program itself never uses `from json` or `as json`. Those projects can use
    ordinary trait implementations and avoid compiling syn/quote/proc-macro2
    for every fresh Cargo target. Programs that explicitly use JSON keep the
    derive backend so their internal expressions retain identical semantics.
    """
    chunks: list[str] = []
    for record in program.records:
        type_name = camel(record.name)
        visitor_name = f"ParleySerdeVisitor{type_name}"
        fields = [name for name, _field_type in record.fields]
        field_literals = ", ".join(
            f'"{rust_str_lit(field)}"' for field in fields
        )
        serialize_fields = "\n".join(
            f'        state.serialize_field("{rust_str_lit(field)}", '
            f'&self.{safe(field)})?;'
            for field in fields
        )
        declarations = "\n".join(
            f"                let mut parley_field_{safe(field)}: "
            f"Option<{rust_type(field_type)}> = None;"
            for field, field_type in record.fields
        )
        match_arms = "\n".join(
            f'''                    "{rust_str_lit(field)}" => {{
                        if parley_field_{safe(field)}.is_some() {{
                            return Err(serde::de::Error::duplicate_field("{rust_str_lit(field)}"));
                        }}
                        parley_field_{safe(field)} = Some(map.next_value()?);
                    }}'''
            for field, _field_type in record.fields
        )
        required_fields = []
        for field, field_type in record.fields:
            variable = f"parley_field_{safe(field)}"
            if isinstance(field_type, A.TMaybe):
                required_fields.append(
                    f"                let {variable} = {variable}.unwrap_or(None);"
                )
            else:
                required_fields.append(
                    f'''                let {variable} = {variable}.ok_or_else(||
                    serde::de::Error::missing_field("{rust_str_lit(field)}"))?;'''
                )
        initializers = ", ".join(
            f"{safe(field)}: parley_field_{safe(field)}" for field in fields
        )
        chunks.append(f'''
impl serde::Serialize for {type_name} {{
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where S: serde::Serializer {{
        use serde::ser::SerializeStruct;
        let mut state = serializer.serialize_struct("{type_name}", {len(fields)})?;
{serialize_fields}
        state.end()
    }}
}}

impl<'de> serde::Deserialize<'de> for {type_name} {{
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where D: serde::Deserializer<'de> {{
        const FIELDS: &[&str] = &[{field_literals}];
        struct {visitor_name};
        impl<'de> serde::de::Visitor<'de> for {visitor_name} {{
            type Value = {type_name};
            fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {{
                formatter.write_str("a strict {type_name} JSON object")
            }}
            fn visit_map<M>(self, mut map: M) -> Result<Self::Value, M::Error>
            where M: serde::de::MapAccess<'de> {{
{declarations}
                while let Some(parley_key) = map.next_key::<String>()? {{
                    match parley_key.as_str() {{
{match_arms}
                        _ => return Err(serde::de::Error::unknown_field(&parley_key, FIELDS)),
                    }}
                }}
{chr(10).join(required_fields)}
                Ok({type_name} {{ {initializers} }})
            }}
        }}
        deserializer.deserialize_struct("{type_name}", FIELDS, {visitor_name})
    }}
}}
'''.strip())

    for enum in program.enums:
        type_name = camel(enum.name)
        variants = ", ".join(
            f'"{rust_str_lit(variant)}"' for variant in enum.variants
        )
        serialize_arms = "\n".join(
            f'            {type_name}::{camel(variant)} => "{rust_str_lit(variant)}",'
            for variant in enum.variants
        )
        deserialize_arms = "\n".join(
            f'            "{rust_str_lit(variant)}" => Ok({type_name}::{camel(variant)}),'
            for variant in enum.variants
        )
        chunks.append(f'''
impl serde::Serialize for {type_name} {{
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where S: serde::Serializer {{
        serializer.serialize_str(match self {{
{serialize_arms}
        }})
    }}
}}

impl<'de> serde::Deserialize<'de> for {type_name} {{
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where D: serde::Deserializer<'de> {{
        const VARIANTS: &[&str] = &[{variants}];
        let value = <String as serde::Deserialize>::deserialize(deserializer)?;
        match value.as_str() {{
{deserialize_arms}
            _ => Err(serde::de::Error::unknown_variant(&value, VARIANTS)),
        }}
    }}
}}
'''.strip())
    return "\n\n".join(chunks)


def _direct_json_impls(program: A.Program) -> str:
    """Emit strict codecs for typed routes without third-party Rust crates."""
    chunks: list[str] = []
    runtime = "parley_web_json_runtime"
    for record in program.records:
        type_name = camel(record.name)
        declarations = "\n".join(
            f"        let mut parley_field_{safe(field)}: "
            f"Option<{rust_type(field_type)}> = None;"
            for field, field_type in record.fields
        )
        match_arms = "\n".join(
            f'''                "{rust_str_lit(field)}" => {{
                    if parley_field_{safe(field)}.is_some() {{
                        return Err("duplicate field {rust_str_lit(field)}".to_string());
                    }}
                    parley_field_{safe(field)} = Some(<{rust_type(field_type)} as {runtime}::Codec>::decode(parley_value)?);
                }}'''
            for field, field_type in record.fields
        )
        required_fields: list[str] = []
        for field, field_type in record.fields:
            variable = f"parley_field_{safe(field)}"
            if isinstance(field_type, A.TMaybe):
                required_fields.append(
                    f"        let {variable} = {variable}.unwrap_or(None);"
                )
            else:
                required_fields.append(
                    f'''        let {variable} = {variable}.ok_or_else(||
            "missing field {rust_str_lit(field)}".to_string())?;'''
                )
        initializers = ", ".join(
            f"{safe(field)}: parley_field_{safe(field)}"
            for field, _field_type in record.fields
        )
        encode_fields = "\n".join(
            f'        {runtime}::write_member("{rust_str_lit(field)}", '
            f'&self.{safe(field)}, output, &mut first)?;'
            for field, _field_type in record.fields
        )
        chunks.append(f'''
impl {runtime}::Codec for {type_name} {{
    fn decode(value: &{runtime}::Value) -> Result<Self, String> {{
        let parley_fields = {runtime}::object(value)?;
{declarations}
        for (parley_key, parley_value) in parley_fields {{
            match parley_key.as_str() {{
{match_arms}
                _ => return Err(format!("unknown field {{}}", parley_key)),
            }}
        }}
{chr(10).join(required_fields)}
        Ok({type_name} {{ {initializers} }})
    }}

    fn encode(&self, output: &mut String) -> Result<(), String> {{
        output.push('{{');
        let mut first = true;
{encode_fields}
        output.push('}}');
        Ok(())
    }}
}}
'''.strip())

    for enum in program.enums:
        type_name = camel(enum.name)
        decode_arms = "\n".join(
            f'            "{rust_str_lit(variant)}" => Ok({type_name}::{camel(variant)}),'
            for variant in enum.variants
        )
        encode_arms = "\n".join(
            f'            {type_name}::{camel(variant)} => "{rust_str_lit(variant)}",'
            for variant in enum.variants
        )
        expected = ", ".join(enum.variants)
        chunks.append(f'''
impl {runtime}::Codec for {type_name} {{
    fn decode(value: &{runtime}::Value) -> Result<Self, String> {{
        match {runtime}::string(value)? {{
{decode_arms}
            other => Err(format!("unknown variant {{}}; expected one of {rust_str_lit(expected)}", other)),
        }}
    }}

    fn encode(&self, output: &mut String) -> Result<(), String> {{
        {runtime}::write_string(match self {{
{encode_arms}
        }}, output);
        Ok(())
    }}
}}
'''.strip())
    return "\n\n".join(chunks)


WEB_JSON_RUNTIME = r'''
mod parley_web_json_runtime {
    use std::collections::BTreeMap;

    pub(crate) enum Value {
        Null,
        Bool(bool),
        Number(String),
        String(String),
        Array(Vec<Value>),
        Object(Vec<(String, Value)>),
    }

    pub(crate) trait Codec: Sized {
        fn decode(value: &Value) -> Result<Self, String>;
        fn encode(&self, output: &mut String) -> Result<(), String>;
    }

    pub(crate) fn decode<T: Codec>(text: &str) -> Result<T, String> {
        let value = Parser::new(text).parse()?;
        T::decode(&value)
    }

    pub(crate) fn encode<T: Codec>(value: &T) -> Result<String, String> {
        let mut output = String::new();
        value.encode(&mut output)?;
        Ok(output)
    }

    pub(crate) fn object(value: &Value) -> Result<&[(String, Value)], String> {
        match value {
            Value::Object(fields) => Ok(fields),
            _ => Err("expected JSON object".to_string()),
        }
    }

    pub(crate) fn string(value: &Value) -> Result<&str, String> {
        match value {
            Value::String(text) => Ok(text),
            _ => Err("expected JSON string".to_string()),
        }
    }

    pub(crate) fn write_member<T: Codec>(
        name: &str,
        value: &T,
        output: &mut String,
        first: &mut bool,
    ) -> Result<(), String> {
        if !*first { output.push(','); }
        *first = false;
        write_string(name, output);
        output.push(':');
        value.encode(output)
    }

    pub(crate) fn write_string(value: &str, output: &mut String) {
        use std::fmt::Write as _;
        output.push('"');
        for character in value.chars() {
            match character {
                '"' => output.push_str("\\\""),
                '\\' => output.push_str("\\\\"),
                '\u{08}' => output.push_str("\\b"),
                '\u{0c}' => output.push_str("\\f"),
                '\n' => output.push_str("\\n"),
                '\r' => output.push_str("\\r"),
                '\t' => output.push_str("\\t"),
                character if character <= '\u{1f}' => {
                    let _ = write!(output, "\\u{:04x}", character as u32);
                }
                character => output.push(character),
            }
        }
        output.push('"');
    }

    impl Codec for i64 {
        fn decode(value: &Value) -> Result<Self, String> {
            match value {
                Value::Number(number) => number.parse::<i64>()
                    .map_err(|_| "expected whole JSON number in i64 range".to_string()),
                _ => Err("expected JSON number".to_string()),
            }
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            output.push_str(&self.to_string());
            Ok(())
        }
    }

    impl Codec for f64 {
        fn decode(value: &Value) -> Result<Self, String> {
            let parsed = match value {
                Value::Number(number) => number.parse::<f64>()
                    .map_err(|_| "expected finite JSON number".to_string())?,
                _ => return Err("expected JSON number".to_string()),
            };
            if parsed.is_finite() { Ok(parsed) }
            else { Err("expected finite JSON number".to_string()) }
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            if !self.is_finite() { return Err("cannot encode non-finite decimal".to_string()); }
            let rendered = self.to_string();
            output.push_str(&rendered);
            if !rendered.contains('.') && !rendered.contains('e') && !rendered.contains('E') {
                output.push_str(".0");
            }
            Ok(())
        }
    }

    impl Codec for bool {
        fn decode(value: &Value) -> Result<Self, String> {
            match value {
                Value::Bool(value) => Ok(*value),
                _ => Err("expected JSON boolean".to_string()),
            }
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            output.push_str(if *self { "true" } else { "false" });
            Ok(())
        }
    }

    impl Codec for String {
        fn decode(value: &Value) -> Result<Self, String> {
            string(value).map(str::to_string)
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            write_string(self, output);
            Ok(())
        }
    }

    impl<T: Codec> Codec for Option<T> {
        fn decode(value: &Value) -> Result<Self, String> {
            match value {
                Value::Null => Ok(None),
                value => T::decode(value).map(Some),
            }
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            match self {
                Some(value) => value.encode(output),
                None => { output.push_str("null"); Ok(()) }
            }
        }
    }

    impl<T: Codec> Codec for Vec<T> {
        fn decode(value: &Value) -> Result<Self, String> {
            let values = match value {
                Value::Array(values) => values,
                _ => return Err("expected JSON array".to_string()),
            };
            values.iter().map(T::decode).collect()
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            output.push('[');
            for (index, value) in self.iter().enumerate() {
                if index > 0 { output.push(','); }
                value.encode(output)?;
            }
            output.push(']');
            Ok(())
        }
    }

    impl<T: Codec> Codec for BTreeMap<String, T> {
        fn decode(value: &Value) -> Result<Self, String> {
            let mut output = BTreeMap::new();
            for (key, value) in object(value)? {
                output.insert(key.clone(), T::decode(value)?);
            }
            Ok(output)
        }

        fn encode(&self, output: &mut String) -> Result<(), String> {
            output.push('{');
            for (index, (key, value)) in self.iter().enumerate() {
                if index > 0 { output.push(','); }
                write_string(key, output);
                output.push(':');
                value.encode(output)?;
            }
            output.push('}');
            Ok(())
        }
    }

    struct Parser<'a> {
        text: &'a str,
        index: usize,
    }

    impl<'a> Parser<'a> {
        fn new(text: &'a str) -> Self { Self { text, index: 0 } }

        fn parse(mut self) -> Result<Value, String> {
            self.whitespace();
            let value = self.value(0)?;
            self.whitespace();
            if self.index != self.text.len() {
                return Err(format!("unexpected trailing JSON at byte {}", self.index));
            }
            Ok(value)
        }

        fn value(&mut self, depth: usize) -> Result<Value, String> {
            if depth > 128 { return Err("JSON nesting exceeds 128 levels".to_string()); }
            self.whitespace();
            match self.peek() {
                Some(b'n') => { self.literal("null")?; Ok(Value::Null) }
                Some(b't') => { self.literal("true")?; Ok(Value::Bool(true)) }
                Some(b'f') => { self.literal("false")?; Ok(Value::Bool(false)) }
                Some(b'"') => self.quoted().map(Value::String),
                Some(b'[') => self.array(depth + 1),
                Some(b'{') => self.object(depth + 1),
                Some(b'-' | b'0'..=b'9') => self.number().map(Value::Number),
                Some(_) => Err(format!("unexpected JSON value at byte {}", self.index)),
                None => Err("unexpected end of JSON".to_string()),
            }
        }

        fn array(&mut self, depth: usize) -> Result<Value, String> {
            self.index += 1;
            self.whitespace();
            let mut values = Vec::new();
            if self.take(b']') { return Ok(Value::Array(values)); }
            loop {
                values.push(self.value(depth)?);
                self.whitespace();
                if self.take(b']') { return Ok(Value::Array(values)); }
                if !self.take(b',') { return Err("expected comma or ] in JSON array".to_string()); }
                self.whitespace();
            }
        }

        fn object(&mut self, depth: usize) -> Result<Value, String> {
            self.index += 1;
            self.whitespace();
            let mut fields = Vec::new();
            if self.take(b'}') { return Ok(Value::Object(fields)); }
            loop {
                if self.peek() != Some(b'"') { return Err("expected string key in JSON object".to_string()); }
                let key = self.quoted()?;
                self.whitespace();
                if !self.take(b':') { return Err("expected colon after JSON object key".to_string()); }
                fields.push((key, self.value(depth)?));
                self.whitespace();
                if self.take(b'}') { return Ok(Value::Object(fields)); }
                if !self.take(b',') { return Err("expected comma or } in JSON object".to_string()); }
                self.whitespace();
            }
        }

        fn number(&mut self) -> Result<String, String> {
            let start = self.index;
            self.take(b'-');
            match self.peek() {
                Some(b'0') => {
                    self.index += 1;
                    if matches!(self.peek(), Some(b'0'..=b'9')) {
                        return Err("JSON number has a leading zero".to_string());
                    }
                }
                Some(b'1'..=b'9') => {
                    self.index += 1;
                    while matches!(self.peek(), Some(b'0'..=b'9')) { self.index += 1; }
                }
                _ => return Err("invalid JSON number".to_string()),
            }
            if self.take(b'.') {
                let fraction = self.index;
                while matches!(self.peek(), Some(b'0'..=b'9')) { self.index += 1; }
                if self.index == fraction { return Err("JSON fraction needs digits".to_string()); }
            }
            if matches!(self.peek(), Some(b'e' | b'E')) {
                self.index += 1;
                if matches!(self.peek(), Some(b'+' | b'-')) { self.index += 1; }
                let exponent = self.index;
                while matches!(self.peek(), Some(b'0'..=b'9')) { self.index += 1; }
                if self.index == exponent { return Err("JSON exponent needs digits".to_string()); }
            }
            Ok(self.text[start..self.index].to_string())
        }

        fn quoted(&mut self) -> Result<String, String> {
            self.index += 1;
            let mut output = String::new();
            loop {
                let byte = self.peek().ok_or_else(|| "unterminated JSON string".to_string())?;
                match byte {
                    b'"' => { self.index += 1; return Ok(output); }
                    b'\\' => {
                        self.index += 1;
                        let escape = self.peek().ok_or_else(|| "unterminated JSON escape".to_string())?;
                        self.index += 1;
                        match escape {
                            b'"' => output.push('"'), b'\\' => output.push('\\'), b'/' => output.push('/'),
                            b'b' => output.push('\u{08}'), b'f' => output.push('\u{0c}'),
                            b'n' => output.push('\n'), b'r' => output.push('\r'), b't' => output.push('\t'),
                            b'u' => output.push(self.unicode_escape()?),
                            _ => return Err("invalid JSON string escape".to_string()),
                        }
                    }
                    0..=31 => return Err("unescaped control byte in JSON string".to_string()),
                    _ => {
                        let character = self.text[self.index..].chars().next()
                            .ok_or_else(|| "invalid UTF-8 in JSON string".to_string())?;
                        output.push(character);
                        self.index += character.len_utf8();
                    }
                }
            }
        }

        fn unicode_escape(&mut self) -> Result<char, String> {
            let first = self.hex_quad()?;
            let scalar = if (0xd800..=0xdbff).contains(&first) {
                if !self.take(b'\\') || !self.take(b'u') {
                    return Err("high surrogate must be followed by a low surrogate".to_string());
                }
                let second = self.hex_quad()?;
                if !(0xdc00..=0xdfff).contains(&second) {
                    return Err("invalid low surrogate in JSON string".to_string());
                }
                0x10000 + ((first - 0xd800) << 10) + (second - 0xdc00)
            } else {
                if (0xdc00..=0xdfff).contains(&first) {
                    return Err("unexpected low surrogate in JSON string".to_string());
                }
                first
            };
            char::from_u32(scalar).ok_or_else(|| "invalid Unicode scalar in JSON string".to_string())
        }

        fn hex_quad(&mut self) -> Result<u32, String> {
            let mut value = 0u32;
            for _ in 0..4 {
                let byte = self.peek().ok_or_else(|| "short Unicode escape".to_string())?;
                self.index += 1;
                value = value * 16 + match byte {
                    b'0'..=b'9' => (byte - b'0') as u32,
                    b'a'..=b'f' => (byte - b'a' + 10) as u32,
                    b'A'..=b'F' => (byte - b'A' + 10) as u32,
                    _ => return Err("invalid hex digit in Unicode escape".to_string()),
                };
            }
            Ok(value)
        }

        fn literal(&mut self, expected: &str) -> Result<(), String> {
            if self.text[self.index..].starts_with(expected) {
                self.index += expected.len();
                Ok(())
            } else {
                Err(format!("invalid JSON literal at byte {}", self.index))
            }
        }

        fn whitespace(&mut self) {
            while matches!(self.peek(), Some(b' ' | b'\n' | b'\r' | b'\t')) { self.index += 1; }
        }

        fn peek(&self) -> Option<u8> { self.text.as_bytes().get(self.index).copied() }

        fn take(&mut self, wanted: u8) -> bool {
            if self.peek() == Some(wanted) { self.index += 1; true } else { false }
        }
    }
}
'''


WEB_RUNTIME = r'''
const PARLEY_MAX_HEADER_BYTES: usize = 65_536;
const PARLEY_MAX_BODY_BYTES: usize = __MAX_BODY__;
const PARLEY_STATIC_ROOT: &str = "__STATIC_ROOT__";

#[derive(Clone)]
struct ParleyHttpRequest {
    method: String,
    path: String,
    query: String,
    headers: BTreeMap<String, String>,
    body: String,
}

struct ParleyHttpResponse {
    status: u16,
    content_type: String,
    body: Vec<u8>,
}

impl ParleyHttpResponse {
    fn new(status: u16, content_type: &str, body: Vec<u8>) -> Self {
        Self { status, content_type: content_type.to_string(), body }
    }
}

fn parley_json_write_string(value: &str, output: &mut String) {
    use std::fmt::Write as _;
    output.push('"');
    for character in value.chars() {
        match character {
            '"' => output.push_str("\\\""),
            '\\' => output.push_str("\\\\"),
            '\u{08}' => output.push_str("\\b"),
            '\u{0c}' => output.push_str("\\f"),
            '\n' => output.push_str("\\n"),
            '\r' => output.push_str("\\r"),
            '\t' => output.push_str("\\t"),
            character if character <= '\u{1f}' => {
                let _ = write!(output, "\\u{:04x}", character as u32);
            }
            character => output.push(character),
        }
    }
    output.push('"');
}

fn parley_json_error(status: u16, code: &str, detail: &str) -> ParleyHttpResponse {
    let mut body = String::from("{\"error\":");
    parley_json_write_string(code, &mut body);
    body.push_str(",\"detail\":");
    parley_json_write_string(detail, &mut body);
    body.push('}');
    ParleyHttpResponse::new(status, "application/json; charset=utf-8", body.into_bytes())
}

fn parley_reason(status: u16) -> &'static str {
    match status {
        200 => "OK", 201 => "Created", 202 => "Accepted", 204 => "No Content",
        400 => "Bad Request", 404 => "Not Found", 405 => "Method Not Allowed",
        408 => "Request Timeout", 413 => "Content Too Large",
        415 => "Unsupported Media Type", 431 => "Request Header Fields Too Large",
        500 => "Internal Server Error", 501 => "Not Implemented",
        _ => "Response",
    }
}

fn parley_mime(path: &std::path::Path) -> &'static str {
    match path.extension().and_then(|value| value.to_str()).unwrap_or("") {
        "html" => "text/html; charset=utf-8", "css" => "text/css; charset=utf-8",
        "js" | "mjs" => "text/javascript; charset=utf-8",
        "json" => "application/json; charset=utf-8", "wasm" => "application/wasm",
        "svg" => "image/svg+xml", "png" => "image/png", "jpg" | "jpeg" => "image/jpeg",
        "webp" => "image/webp", "ico" => "image/x-icon", "txt" => "text/plain; charset=utf-8",
        _ => "application/octet-stream",
    }
}

fn parley_static(path: &str) -> Option<ParleyHttpResponse> {
    if PARLEY_STATIC_ROOT.is_empty() || path.contains('\\') || path.as_bytes().contains(&0) {
        return None;
    }
    let relative = if path == "/" { "index.html" } else { path.trim_start_matches('/') };
    let candidate_path = std::path::Path::new(relative);
    if candidate_path.components().any(|part| !matches!(part, std::path::Component::Normal(_))) {
        return None;
    }
    let root = std::fs::canonicalize(PARLEY_STATIC_ROOT).ok()?;
    let candidate = std::fs::canonicalize(root.join(candidate_path)).ok()?;
    if !candidate.starts_with(&root) || !candidate.is_file() {
        return None;
    }
    let body = std::fs::read(&candidate).ok()?;
    Some(ParleyHttpResponse::new(200, parley_mime(&candidate), body))
}

fn parley_read_request(stream: &mut std::net::TcpStream) -> Result<ParleyHttpRequest, ParleyHttpResponse> {
    use std::io::Read;
    let _ = stream.set_read_timeout(Some(std::time::Duration::from_secs(10)));
    let mut bytes = Vec::new();
    let mut chunk = [0u8; 4096];
    let header_end;
    loop {
        let count = stream.read(&mut chunk).map_err(|error|
            parley_json_error(400, "request_read_failed", &error.to_string()))?;
        if count == 0 {
            return Err(parley_json_error(400, "incomplete_request", "connection closed before headers"));
        }
        bytes.extend_from_slice(&chunk[..count]);
        if let Some(index) = bytes.windows(4).position(|window| window == b"\r\n\r\n") {
            header_end = index + 4;
            break;
        }
        if bytes.len() > PARLEY_MAX_HEADER_BYTES {
            return Err(parley_json_error(431, "headers_too_large", "request headers exceeded the configured limit"));
        }
    }
    if header_end > PARLEY_MAX_HEADER_BYTES {
        return Err(parley_json_error(431, "headers_too_large", "request headers exceeded the configured limit"));
    }
    let header_text = std::str::from_utf8(&bytes[..header_end])
        .map_err(|_| parley_json_error(400, "invalid_headers", "headers must be UTF-8"))?;
    let mut lines = header_text[..header_text.len() - 4].split("\r\n");
    let request_line = lines.next().unwrap_or("");
    let parts: Vec<String> = request_line.split_whitespace().map(str::to_string).collect();
    if parts.len() != 3 || !matches!(parts[2].as_str(), "HTTP/1.0" | "HTTP/1.1") {
        return Err(parley_json_error(400, "invalid_request_line", "expected METHOD /path HTTP/1.1"));
    }
    if !parts[1].starts_with('/') {
        return Err(parley_json_error(400, "invalid_target", "only origin-form request targets are accepted"));
    }
    let method = parts[0].to_ascii_uppercase();
    let target = parts[1].clone();
    let mut headers = BTreeMap::new();
    for line in lines {
        let (raw_name, raw_value) = line.split_once(':')
            .ok_or_else(|| parley_json_error(400, "invalid_header", "header line has no colon"))?;
        let name = raw_name.trim().to_ascii_lowercase();
        let value = raw_value.trim().to_string();
        if name.is_empty() || !name.bytes().all(|byte|
                byte.is_ascii_alphanumeric() || matches!(byte, b'!' | b'#' | b'$' | b'%' | b'&' | b'\'' | b'*' | b'+' | b'-' | b'.' | b'^' | b'_' | b'`' | b'|' | b'~')) {
            return Err(parley_json_error(400, "invalid_header_name", "header name contains unsupported bytes"));
        }
        if let Some(previous) = headers.insert(name.clone(), value.clone()) {
            if name == "content-length" && previous != value {
                return Err(parley_json_error(400, "ambiguous_content_length", "conflicting Content-Length headers"));
            }
        }
    }
    if headers.contains_key("transfer-encoding") {
        return Err(parley_json_error(501, "transfer_encoding_unsupported", "chunked requests are not accepted"));
    }
    let content_length = match headers.get("content-length") {
        Some(value) => value.parse::<usize>()
            .map_err(|_| parley_json_error(400, "invalid_content_length", "Content-Length is not a number"))?,
        None => 0,
    };
    if content_length > PARLEY_MAX_BODY_BYTES {
        return Err(parley_json_error(413, "body_too_large", "request body exceeded the configured limit"));
    }
    let wanted = header_end + content_length;
    while bytes.len() < wanted {
        let count = stream.read(&mut chunk).map_err(|error|
            parley_json_error(400, "body_read_failed", &error.to_string()))?;
        if count == 0 {
            return Err(parley_json_error(400, "incomplete_body", "connection closed before Content-Length bytes arrived"));
        }
        let remaining = wanted - bytes.len();
        bytes.extend_from_slice(&chunk[..count.min(remaining)]);
    }
    let body = String::from_utf8(bytes[header_end..wanted].to_vec())
        .map_err(|_| parley_json_error(400, "invalid_body", "typed JSON bodies must be UTF-8"))?;
    let (path, query) = target.split_once('?').unwrap_or((target.as_str(), ""));
    Ok(ParleyHttpRequest {
        method, path: path.to_string(), query: query.to_string(),
        headers, body,
    })
}

fn parley_dispatch(request: &ParleyHttpRequest) -> ParleyHttpResponse {
    // RFC 9110: a server that answers GET for a resource must answer HEAD for
    // it too, with the same headers. parley_write_response drops the body.
    let method = if request.method == "HEAD" { "GET" } else { request.method.as_str() };
    match (method, request.path.as_str()) {
__ROUTES__
        _ => {
            if matches!(request.method.as_str(), "GET" | "HEAD") {
                if let Some(response) = parley_static(&request.path) { return response; }
            }
            parley_json_error(404, "not_found", "no typed route or static file matched")
        }
    }
}

fn parley_write_response(stream: &mut std::net::TcpStream, method: &str, response: ParleyHttpResponse) {
    use std::io::Write;
    let status = if (100..=599).contains(&response.status) { response.status } else { 500 };
    let content_type = if response.content_type.contains('\r') || response.content_type.contains('\n') {
        "application/octet-stream"
    } else {
        response.content_type.as_str()
    };
    let head = format!(
        "HTTP/1.1 {} {}\r\nContent-Type: {}\r\nContent-Length: {}\r\nConnection: close\r\nX-Content-Type-Options: nosniff\r\n\r\n",
        status, parley_reason(status), content_type, response.body.len()
    );
    let _ = stream.set_write_timeout(Some(std::time::Duration::from_secs(10)));
    if stream.write_all(head.as_bytes()).is_ok() && method != "HEAD" {
        let _ = stream.write_all(&response.body);
    }
    let _ = stream.flush();
}

fn parley_connection(mut stream: std::net::TcpStream) {
    let request = match parley_read_request(&mut stream) {
        Ok(request) => request,
        Err(response) => {
            parley_write_response(&mut stream, "GET", response);
            return;
        }
    };
    let method = request.method.clone();
    let response = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| parley_dispatch(&request)))
        .unwrap_or_else(|_| parley_json_error(500, "handler_failed", &parley_last_error()));
    parley_write_response(&mut stream, &method, response);
}

fn main() {
    let host = std::env::var("PARLEY_WEB_HOST").unwrap_or_else(|_| "__HOST__".to_string());
    let port = std::env::var("PARLEY_WEB_PORT").ok()
        .and_then(|value| value.parse::<u16>().ok()).unwrap_or(__PORT__);
    let address = format!("{}:{}", host, port);
    let listener = match std::net::TcpListener::bind(&address) {
        Ok(listener) => listener,
        Err(error) => {
            eprintln!("Could not start Parley web server on {}: {}", address, error);
            std::process::exit(1);
        }
    };
    std::panic::set_hook(Box::new(|info| {
        let message = if let Some(value) = info.payload().downcast_ref::<&str>() {
            value.to_string()
        } else if let Some(value) = info.payload().downcast_ref::<String>() {
            value.clone()
        } else {
            "something went wrong".to_string()
        };
        LAST_ERROR.with(|error| *error.borrow_mut() = message);
    }));
    println!("Parley web listening on http://{}", address);
    for stream in listener.incoming() {
        match stream {
            Ok(stream) => { std::thread::spawn(move || parley_connection(stream)); }
            Err(error) => eprintln!("Parley web connection failed: {}", error),
        }
    }
}
'''


def render_server(checked: CheckedWeb) -> tuple[str, dict[int, int]]:
    uses_program_json = program_uses_json(checked.program)
    rust, linemap = emit_program(
        checked.program,
        program_main=None,
        serde=uses_program_json,
    )
    if not uses_program_json:
        rust += "\n" + WEB_JSON_RUNTIME.strip() + "\n"
        rust += "\n" + _direct_json_impls(checked.program) + "\n"
    routes = ",\n".join(
        _route_arm(route, uses_program_json=uses_program_json)
        for route in checked.routes
    )
    runtime = (WEB_RUNTIME
               .replace("__MAX_BODY__", str(checked.project.max_body_bytes))
               .replace("__STATIC_ROOT__", "public" if checked.project.static_dir else "")
               .replace("__HOST__", rust_str_lit(checked.project.host))
               .replace("__PORT__", str(checked.project.port))
               .replace("__ROUTES__", routes))
    return rust + "\n" + runtime.strip() + "\n", linemap


def _abi_rust_type(ty: A.Type) -> str:
    if isinstance(ty, A.TNum):
        return "i64"
    if isinstance(ty, A.TDec):
        return "f64"
    if isinstance(ty, A.TBool):
        return "i32"
    raise AssertionError(ty)


def _abi_in(name: str, ty: A.Type) -> str:
    return f"{name} != 0" if isinstance(ty, A.TBool) else name


def _abi_out(expression: str, ty: A.Type) -> str:
    return f"if {expression} {{ 1 }} else {{ 0 }}" if isinstance(ty, A.TBool) else expression


def render_browser(checked: CheckedBrowser) -> tuple[str, dict[int, int], str, str]:
    rust, linemap = emit_program(checked.program, program_main=None, serde=False)
    wrappers: list[str] = []
    js_functions: list[str] = []
    declarations: list[str] = []
    for function in checked.exports:
        rust_params = [f"arg{index}: {_abi_rust_type(param.type)}"
                       for index, param in enumerate(function.params)]
        call_args = [_abi_in(f"arg{index}", param.type)
                     for index, param in enumerate(function.params)]
        result = f"{safe(function.name)}({', '.join(call_args)})"
        wrappers.append(
            f'#[no_mangle]\npub extern "C" fn parley_{safe(function.name)}'
            f'({", ".join(rust_params)}) -> {_abi_rust_type(function.ret)} {{\n'
            f'    {_abi_out(result, function.ret)}\n}}')

        js_params = ", ".join(param.name for param in function.params)
        converted: list[str] = []
        ts_params: list[str] = []
        for param in function.params:
            if isinstance(param.type, A.TNum):
                converted.append(f'asI64({param.name}, "{param.name}")')
                ts_params.append(f"{param.name}: number | bigint")
            elif isinstance(param.type, A.TBool):
                converted.append(f'({param.name} ? 1 : 0)')
                ts_params.append(f"{param.name}: boolean")
            else:
                converted.append(param.name)
                ts_params.append(f"{param.name}: number")
        raw_call = f'wasm.parley_{function.name}({", ".join(converted)})'
        if isinstance(function.ret, A.TBool):
            returned = f"{raw_call} !== 0"
            ts_return = "boolean"
        elif isinstance(function.ret, A.TNum):
            returned = raw_call
            ts_return = "bigint"
        else:
            returned = raw_call
            ts_return = "number"
        js_functions.append(
            f"    {function.name}({js_params}) {{ return {returned}; }}")
        declarations.append(
            f"  {function.name}({', '.join(ts_params)}): {ts_return};")

    js = """\
const asI64 = (value, name) => {
  if (typeof value === "bigint") return value;
  if (!Number.isSafeInteger(value)) {
    throw new TypeError(`${name} must be a safe whole number or bigint`);
  }
  return BigInt(value);
};

export async function loadParley(moduleUrl = new URL("./parley.wasm", import.meta.url)) {
  const response = await fetch(moduleUrl);
  if (!response.ok) throw new Error(`Could not load Parley WASM: ${response.status}`);
  let instance;
  if (WebAssembly.instantiateStreaming &&
      response.headers.get("content-type")?.includes("application/wasm")) {
    ({ instance } = await WebAssembly.instantiateStreaming(response, {}));
  } else {
    ({ instance } = await WebAssembly.instantiate(await response.arrayBuffer(), {}));
  }
  const wasm = instance.exports;
  return Object.freeze({
__FUNCTIONS__
  });
}
""".replace("__FUNCTIONS__", ",\n".join(js_functions))
    dts = """\
export interface ParleyBrowserModule {
__DECLARATIONS__
}
export function loadParley(moduleUrl?: string | URL): Promise<ParleyBrowserModule>;
""".replace("__DECLARATIONS__", "\n".join(declarations))
    return rust + "\n\n" + "\n\n".join(wrappers) + "\n", linemap, js, dts
