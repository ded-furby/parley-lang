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
from .json_codec import JSON_RUNTIME as WEB_JSON_RUNTIME, direct_json_impls as _direct_json_impls
from .emit_rust import camel, emit_program, program_uses_json, rust_str_lit, rust_type, safe
from .parser import SourceMap, parse_program


WEB_MANIFEST = "parley.web.json"
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
FUNCTION_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
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
class ResponseControl:
    status_field: str
    headers_field: str
    body_field: str


@dataclass(frozen=True)
class Route:
    method: str
    path: str
    path_parameters: tuple[str, ...]
    handler: str
    success_status: int
    response: ResponseControl | None


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
    has_path_parameters: bool
    has_query_parameters: bool
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


def _path_parameters(path: str, label: str) -> tuple[str, ...]:
    if "{" not in path and "}" not in path:
        return ()
    segments = path.split("/")[1:]
    if not segments or any(not segment for segment in segments):
        raise WebProjectError(
            f"{label} template must not contain empty segments or end with /"
        )
    parameters: list[str] = []
    for segment in segments:
        if segment.startswith("{") and segment.endswith("}"):
            name = segment[1:-1]
            if not FIELD_RE.fullmatch(name):
                raise WebProjectError(
                    f"{label} capture must be a whole segment with a Parley field name"
                )
            if name in parameters:
                raise WebProjectError(f"{label} repeats path capture {name}")
            parameters.append(name)
        elif "{" in segment or "}" in segment:
            raise WebProjectError(
                f"{label} capture must occupy one complete path segment"
            )
    if not parameters:
        raise WebProjectError(f"{label} contains braces but no path capture")
    return tuple(parameters)


def _template_segments(route: Route) -> tuple[str | None, ...]:
    parameters = set(route.path_parameters)
    return tuple(
        None
        if segment.startswith("{")
        and segment.endswith("}")
        and segment[1:-1] in parameters
        else segment
        for segment in route.path.split("/")[1:]
    )


def _templates_overlap(left: Route, right: Route) -> bool:
    left_segments = _template_segments(left)
    right_segments = _template_segments(right)
    return len(left_segments) == len(right_segments) and all(
        left_segment is None
        or right_segment is None
        or left_segment == right_segment
        for left_segment, right_segment in zip(left_segments, right_segments)
    )


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
                f"routes item {index} path must begin with / and exclude ?, #, CR, and LF")
        path_parameters = _path_parameters(route_path, f"routes item {index} path")
        handler = route.get("handler")
        if not isinstance(handler, str) or not FUNCTION_RE.fullmatch(handler):
            raise WebProjectError(f"routes item {index} handler is not a Parley function name")
        response = None
        if "response" in route:
            raw_response = _object(route["response"], f"routes item {index} response")
            expected = {"status_field", "headers_field", "body_field"}
            if set(raw_response) != expected:
                raise WebProjectError(
                    f"routes item {index} response must contain exactly "
                    "status_field, headers_field, and body_field")
            values: dict[str, str] = {}
            for field in sorted(expected):
                value = raw_response[field]
                if not isinstance(value, str) or not FIELD_RE.fullmatch(value):
                    raise WebProjectError(
                        f"routes item {index} response {field} is not a Parley field name")
                values[field] = value
            if len(set(values.values())) != 3:
                raise WebProjectError(
                    f"routes item {index} response field names must be distinct")
            if "success_status" in route:
                raise WebProjectError(
                    f"routes item {index} cannot combine response with success_status")
            response = ResponseControl(**values)
        success = _integer(route.get("success_status", 200),
                           f"routes item {index} success_status", 200, 299)
        key = (method, route_path)
        if key in seen_routes:
            raise WebProjectError(f"route {method} {route_path} is declared twice")
        candidate = Route(
            method, route_path, path_parameters, handler, success, response
        )
        overlap = next(
            (
                previous
                for previous in routes
                if previous.method == method
                and previous.path_parameters
                and path_parameters
                and _templates_overlap(previous, candidate)
            ),
            None,
        )
        if overlap is not None:
            raise WebProjectError(
                f"route templates {method} {overlap.path} and {route_path} overlap"
            )
        seen_routes.add(key)
        routes.append(candidate)
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


def _web_request_kind(record: A.RecordDef | None) -> str | None:
    if record is None:
        return None
    expected = [
        ("method", A.TText()),
        ("path", A.TText()),
        ("query", A.TText()),
        ("headers", A.TMap(A.TText(), A.TText())),
        ("body", A.TText()),
    ]
    if record.fields == expected:
        return "legacy"
    if record.fields == [
        *expected,
        ("path_parameters", A.TMap(A.TText(), A.TText())),
    ]:
        return "path"
    if record.fields == [
        *expected,
        ("path_parameters", A.TMap(A.TText(), A.TText())),
        ("query_parameters", A.TMap(A.TText(), A.TList(A.TText()))),
    ]:
        return "query"
    return None


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
        if route.response is None:
            response_problem = _json_type_error(function.ret, records, enums)
            if response_problem:
                contract_diags.append(_diag(
                    "P712", f'Web handler "{function.name}" response is not JSON-safe: {response_problem}.',
                    function, srcmap))
                continue
        else:
            control = route.response
            if not isinstance(function.ret, A.TRecord):
                contract_diags.append(_diag(
                    "P716", f'Web handler "{function.name}" must give a response-control record.',
                    function, srcmap,
                    hint="Return a record containing the configured status, headers, and body fields."))
                continue
            response_record = records.get(function.ret.name)
            if response_record is None:
                contract_diags.append(_diag(
                    "P716", f'Web handler "{function.name}" response-control record is missing.',
                    function, srcmap))
                continue
            field_types = dict(response_record.fields)
            wanted_fields = {control.status_field, control.headers_field, control.body_field}
            if set(field_types) != wanted_fields:
                contract_diags.append(_diag(
                    "P717", f'Web handler "{function.name}" response-control fields do not match its manifest.',
                    response_record, srcmap,
                    hint="The response record must contain exactly the configured status, headers, and body fields."))
                continue
            if not isinstance(field_types[control.status_field], A.TNum):
                contract_diags.append(_diag(
                    "P718", f'Web handler "{function.name}" response status must be number.',
                    response_record, srcmap))
                continue
            header_type = field_types[control.headers_field]
            if not (isinstance(header_type, A.TMap)
                    and isinstance(header_type.key, A.TText)
                    and isinstance(header_type.val, A.TText)):
                contract_diags.append(_diag(
                    "P719", f'Web handler "{function.name}" response headers must be map from text to text.',
                    response_record, srcmap))
                continue
            body_problem = _json_type_error(field_types[control.body_field], records, enums)
            if body_problem:
                contract_diags.append(_diag(
                    "P719", f'Web handler "{function.name}" response body is not JSON-safe: {body_problem}.',
                    response_record, srcmap))
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
        has_path_parameters = False
        has_query_parameters = False
        body_param = None
        params = list(function.params)
        if params and isinstance(params[0].type, A.TRecord) and params[0].type.name == "web_request":
            has_request = True
            request_kind = _web_request_kind(records.get("web_request"))
            if request_kind is None:
                contract_diags.append(_diag(
                    "P714", "web_request does not have the required HTTP fields.",
                    records.get("web_request") or function, srcmap,
                    hint=(
                        "Define method, path, query, headers, and body in order; "
                        "optionally add path_parameters as the sixth text-to-text map, "
                        "then query_parameters as the seventh text-to-list-of-text map."
                    )))
                continue
            has_path_parameters = request_kind in {"path", "query"}
            has_query_parameters = request_kind == "query"
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
        if route.path_parameters and not (has_request and has_path_parameters):
            contract_diags.append(_diag(
                "P725",
                f'Parameterized route "{route.path}" requires extended web_request metadata.',
                function,
                srcmap,
                hint=(
                    "Take web_request first and add path_parameters as the final "
                    "map from text to text field."
                ),
            ))
            continue
        checked.append(CheckedRoute(
            route, function, has_request, has_path_parameters,
            has_query_parameters, body_param
        ))
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


def _route_body(
    checked: CheckedRoute,
    *,
    request_name: str,
) -> str:
    route = checked.route
    function = checked.function
    setup: list[str] = []
    args: list[str] = []
    if checked.has_request:
        path_parameters = (
            f"\n                path_parameters: {request_name}.path_parameters.clone(),"
            if checked.has_path_parameters
            else ""
        )
        query_parameters = ""
        if checked.has_query_parameters:
            setup.append(f"""
            let parley_query_parameters = match parley_parse_query_parameters(&{request_name}.query) {{
                Ok(value) => value,
                Err(response) => return response,
            }};""".rstrip())
            query_parameters = (
                "\n                query_parameters: parley_query_parameters,"
            )
        setup.append(f"""
            let parley_request = WebRequest {{
                method: method.to_string(),
                path: {request_name}.path.clone(),
                query: {request_name}.query.clone(),
                headers: {request_name}.headers.clone(),
                body: {request_name}.body.clone(),{path_parameters}{query_parameters}
            }};""".rstrip())
        args.append(_rust_arg(function.params[0], "parley_request"))
    if checked.body_param is not None:
        # rust_type lives on the emitter module; importing here avoids exposing
        # backend details in the manifest model.
        from .emit_rust import rust_type
        decode = f"parley_web_json_runtime::decode(&{request_name}.body)"
        setup.append(f"""
            let content_type = {request_name}.headers.get("content-type")
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
    response = route.response
    encoded_value = "result" if response is None else f"result.{safe(response.body_field)}"
    encode = f"parley_web_json_runtime::encode(&{encoded_value}).map(String::into_bytes)"
    if response is None:
        success = (
            f'ParleyHttpResponse::new({route.success_status}, '
            '"application/json; charset=utf-8", body)'
        )
    else:
        success = (
            f"parley_dynamic_json_response(result.{safe(response.status_field)}, "
            f"result.{safe(response.headers_field)}, body)"
        )
    return f'''{{
{setup_text}
            let result = {call};
            match {encode} {{
                Ok(body) => {success},
                Err(error) => parley_json_error(500, "response_json_failed", &error.to_string()),
            }}
        }}'''


def _route_dispatch(checked: CheckedRoute) -> str:
    route = checked.route
    if not route.path_parameters:
        body = _route_body(
            checked, request_name="request"
        )
        return f'''    if method == "{rust_str_lit(route.method)}" && request.path == "{rust_str_lit(route.path)}" {{
        return {body};
    }}'''
    body = _route_body(
        checked, request_name="routed_request"
    )
    return f'''    if method == "{rust_str_lit(route.method)}" {{
        match parley_match_path("{rust_str_lit(route.path)}", &request.path) {{
            Ok(Some(path_parameters)) => {{
                let mut routed_request = request.clone();
                routed_request.path_parameters = path_parameters;
                return {body};
            }}
            Ok(None) => {{}},
            Err(response) => return response,
        }}
    }}'''




WEB_RUNTIME = r'''
const PARLEY_MAX_HEADER_BYTES: usize = 65_536;
const PARLEY_MAX_BODY_BYTES: usize = __MAX_BODY__;
const PARLEY_MAX_RESPONSE_HEADERS: usize = 100;
const PARLEY_MAX_RESPONSE_HEADER_BYTES: usize = 32_768;
const PARLEY_STATIC_ROOT: &str = "__STATIC_ROOT__";

#[derive(Clone)]
struct ParleyHttpRequest {
    method: String,
    path: String,
    query: String,
    headers: BTreeMap<String, String>,
    body: String,
    path_parameters: BTreeMap<String, String>,
}

struct ParleyHttpResponse {
    status: u16,
    content_type: String,
    headers: BTreeMap<String, String>,
    body: Vec<u8>,
}

impl ParleyHttpResponse {
    fn new(status: u16, content_type: &str, body: Vec<u8>) -> Self {
        Self { status, content_type: content_type.to_string(), headers: BTreeMap::new(), body }
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

fn parley_path_hex(byte: u8) -> Option<u8> {
    match byte {
        b'0'..=b'9' => Some(byte - b'0'),
        b'a'..=b'f' => Some(byte - b'a' + 10),
        b'A'..=b'F' => Some(byte - b'A' + 10),
        _ => None,
    }
}

fn parley_decode_path_parameter(value: &str) -> Result<String, ParleyHttpResponse> {
    let input = value.as_bytes();
    let mut output = Vec::with_capacity(input.len());
    let mut index = 0usize;
    while index < input.len() {
        if input[index] == b'%' {
            if index + 2 >= input.len() {
                return Err(parley_json_error(
                    400, "invalid_path_parameter", "path parameter has a truncated percent escape"));
            }
            let high = parley_path_hex(input[index + 1]);
            let low = parley_path_hex(input[index + 2]);
            match (high, low) {
                (Some(high), Some(low)) => output.push(high * 16 + low),
                _ => return Err(parley_json_error(
                    400, "invalid_path_parameter", "path parameter has an invalid percent escape")),
            }
            index += 3;
        } else {
            output.push(input[index]);
            index += 1;
        }
    }
    if output.iter().any(|byte| matches!(*byte, 0..=0x1f | 0x7f | b'/' | b'\\')) {
        return Err(parley_json_error(
            400, "invalid_path_parameter", "path parameter contains a forbidden separator or control byte"));
    }
    String::from_utf8(output).map_err(|_| parley_json_error(
        400, "invalid_path_parameter", "path parameter is not valid UTF-8"))
}

fn parley_decode_query_component(value: &str) -> Result<String, ParleyHttpResponse> {
    let input = value.as_bytes();
    let mut output = Vec::with_capacity(input.len());
    let mut index = 0usize;
    while index < input.len() {
        match input[index] {
            b'%' => {
                if index + 2 >= input.len() {
                    return Err(parley_json_error(
                        400, "invalid_query_parameter", "query parameter has a truncated percent escape"));
                }
                match (parley_path_hex(input[index + 1]), parley_path_hex(input[index + 2])) {
                    (Some(high), Some(low)) => output.push(high * 16 + low),
                    _ => return Err(parley_json_error(
                        400, "invalid_query_parameter", "query parameter has an invalid percent escape")),
                }
                index += 3;
            }
            b'+' => {
                output.push(b' ');
                index += 1;
            }
            byte => {
                output.push(byte);
                index += 1;
            }
        }
    }
    if output.iter().any(|byte| matches!(*byte, 0..=0x1f | 0x7f)) {
        return Err(parley_json_error(
            400, "invalid_query_parameter", "query parameter contains a forbidden control byte"));
    }
    String::from_utf8(output).map_err(|_| parley_json_error(
        400, "invalid_query_parameter", "query parameter is not valid UTF-8"))
}

fn parley_parse_query_parameters(
    query: &str,
) -> Result<BTreeMap<String, Vec<String>>, ParleyHttpResponse> {
    let mut parameters: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut pairs = 0usize;
    for pair in query.split('&').filter(|pair| !pair.is_empty()) {
        pairs += 1;
        if pairs > 128 {
            return Err(parley_json_error(
                400, "invalid_query_parameter", "query parameters exceeded 128 pairs"));
        }
        let (raw_name, raw_value) = pair.split_once('=').unwrap_or((pair, ""));
        let name = parley_decode_query_component(raw_name)?;
        if name.is_empty() {
            return Err(parley_json_error(
                400, "invalid_query_parameter", "query parameter name is empty"));
        }
        let value = parley_decode_query_component(raw_value)?;
        parameters.entry(name).or_default().push(value);
    }
    Ok(parameters)
}

fn parley_match_path(
    template: &str,
    path: &str,
) -> Result<Option<BTreeMap<String, String>>, ParleyHttpResponse> {
    let template_segments: Vec<&str> = template.trim_start_matches('/').split('/').collect();
    let path_segments: Vec<&str> = path.trim_start_matches('/').split('/').collect();
    if template_segments.len() != path_segments.len() {
        return Ok(None);
    }
    for (template_segment, path_segment) in template_segments.iter().zip(&path_segments) {
        let capture = template_segment.starts_with('{') && template_segment.ends_with('}');
        if !capture && template_segment != path_segment {
            return Ok(None);
        }
        if capture && path_segment.is_empty() {
            return Ok(None);
        }
    }
    let mut parameters = BTreeMap::new();
    for (template_segment, path_segment) in template_segments.iter().zip(&path_segments) {
        if template_segment.starts_with('{') {
            let name = &template_segment[1..template_segment.len() - 1];
            parameters.insert(name.to_string(), parley_decode_path_parameter(path_segment)?);
        }
    }
    Ok(Some(parameters))
}

fn parley_header_name_ok(name: &str) -> bool {
    !name.is_empty() && name.bytes().all(|byte|
        byte.is_ascii_alphanumeric() || matches!(byte,
            b'!' | b'#' | b'$' | b'%' | b'&' | b'\'' | b'*' | b'+' | b'-' |
            b'.' | b'^' | b'_' | b'`' | b'|' | b'~'))
}

fn parley_reserved_response_header(name: &str) -> bool {
    matches!(name,
        "connection" | "content-length" | "content-type" | "date" |
        "keep-alive" | "proxy-authenticate" | "proxy-authorization" |
        "server" | "te" | "trailer" | "transfer-encoding" | "upgrade" |
        "x-content-type-options")
}

fn parley_response_header_error(detail: &str) -> ParleyHttpResponse {
    parley_json_error(500, "invalid_response_headers", detail)
}

fn parley_dynamic_json_response(
    status: i64,
    headers: BTreeMap<String, String>,
    body: Vec<u8>,
) -> ParleyHttpResponse {
    if !(200..=599).contains(&status) {
        return parley_json_error(
            500, "invalid_response_status", "response status must be from 200 to 599");
    }
    if headers.len() > PARLEY_MAX_RESPONSE_HEADERS {
        return parley_response_header_error("response headers exceeded 100 fields");
    }
    let mut normalized = BTreeMap::new();
    let mut encoded_bytes = 0usize;
    for (name, value) in headers {
        if !parley_header_name_ok(&name) {
            return parley_response_header_error(
                "response header name contains unsupported bytes");
        }
        let name = name.to_ascii_lowercase();
        if parley_reserved_response_header(&name) {
            return parley_response_header_error("response header is owned by the server");
        }
        if value.bytes().any(|byte| byte < 0x20 || byte == 0x7f) {
            return parley_response_header_error(
                "response header value contains unsupported control bytes");
        }
        if normalized.contains_key(&name) {
            return parley_response_header_error(
                "response header names must be unique ignoring case");
        }
        encoded_bytes = match encoded_bytes.checked_add(name.len() + value.len() + 4) {
            Some(total) if total <= PARLEY_MAX_RESPONSE_HEADER_BYTES => total,
            _ => return parley_response_header_error(
                "response headers exceeded 32768 bytes"),
        };
        normalized.insert(name, value);
    }
    ParleyHttpResponse {
        status: status as u16,
        content_type: "application/json; charset=utf-8".to_string(),
        headers: normalized,
        body,
    }
}

fn parley_reason(status: u16) -> &'static str {
    match status {
        200 => "OK", 201 => "Created", 202 => "Accepted", 204 => "No Content",
        205 => "Reset Content", 301 => "Moved Permanently", 302 => "Found",
        304 => "Not Modified", 307 => "Temporary Redirect", 308 => "Permanent Redirect",
        400 => "Bad Request", 401 => "Unauthorized", 403 => "Forbidden",
        404 => "Not Found", 405 => "Method Not Allowed", 409 => "Conflict",
        408 => "Request Timeout", 413 => "Content Too Large",
        415 => "Unsupported Media Type", 422 => "Unprocessable Content",
        429 => "Too Many Requests", 431 => "Request Header Fields Too Large",
        500 => "Internal Server Error", 501 => "Not Implemented",
        502 => "Bad Gateway", 503 => "Service Unavailable", 504 => "Gateway Timeout",
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
        if !parley_header_name_ok(&name) {
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
        headers, body, path_parameters: BTreeMap::new(),
    })
}

fn parley_dispatch(request: &ParleyHttpRequest) -> ParleyHttpResponse {
    // RFC 9110: a server that answers GET for a resource must answer HEAD for
    // it too, with the same headers. parley_write_response drops the body.
    let method = if request.method == "HEAD" { "GET" } else { request.method.as_str() };
__ROUTES__
    if matches!(request.method.as_str(), "GET" | "HEAD") {
        if let Some(response) = parley_static(&request.path) { return response; }
    }
    parley_json_error(404, "not_found", "no typed route or static file matched")
}

fn parley_write_response(stream: &mut std::net::TcpStream, method: &str, response: ParleyHttpResponse) {
    use std::io::Write;
    let status = if (100..=599).contains(&response.status) { response.status } else { 500 };
    let content_type = if response.content_type.contains('\r') || response.content_type.contains('\n') {
        "application/octet-stream"
    } else {
        response.content_type.as_str()
    };
    let bodyless = matches!(status, 204 | 205 | 304);
    let mut head = format!(
        "HTTP/1.1 {} {}\r\nContent-Type: {}\r\n",
        status, parley_reason(status), content_type);
    if !matches!(status, 204 | 304) {
        let content_length = if status == 205 { 0 } else { response.body.len() };
        head.push_str(&format!("Content-Length: {}\r\n", content_length));
    }
    for (name, value) in &response.headers {
        head.push_str(name);
        head.push_str(": ");
        head.push_str(value);
        head.push_str("\r\n");
    }
    head.push_str("Connection: close\r\nX-Content-Type-Options: nosniff\r\n\r\n");
    let _ = stream.set_write_timeout(Some(std::time::Duration::from_secs(10)));
    if stream.write_all(head.as_bytes()).is_ok() && method != "HEAD" && !bodyless {
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
    # emit_program embeds the shared codec itself when the program mentions
    # JSON; route-only programs get the same module appended here, so every
    # server carries exactly one copy either way.
    uses_program_json = program_uses_json(checked.program)
    rust, linemap = emit_program(
        checked.program,
        program_main=None,
        serde=uses_program_json,
    )
    if not uses_program_json:
        rust += "\n" + WEB_JSON_RUNTIME.strip() + "\n"
        rust += "\n" + _direct_json_impls(checked.program) + "\n"
    ordered_routes = sorted(
        checked.routes,
        key=lambda route: bool(route.route.path_parameters),
    )
    routes = "\n".join(
        _route_dispatch(route)
        for route in ordered_routes
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
