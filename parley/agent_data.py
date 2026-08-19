"""Deterministic structured-data packing for AI-agent context.

JSON remains the semantic interchange format.  The TOON encoder intentionally
implements the conservative v4.1 forms where TOON is strongest: primitives,
nested objects, primitive arrays, and uniform arrays of flat objects.  Shapes
outside that safe subset fall back to compact JSON in ``auto`` mode instead of
guessing at a novel encoding.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Callable


TOON_SPEC_VERSION = "4.1"
ROUGH_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
NUMBER_RE = re.compile(r"^-?[0-9]+(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?$", re.I)
SAFE_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
SAFE_STRING_RE = re.compile(r"^[A-Za-z0-9_./@+ -]+$")
HEADER_RE = re.compile(
    r'^(?:(?P<key>"(?:\\.|[^"\\])*"|[A-Za-z_][A-Za-z0-9_.-]*))?'
    r'\[(?P<count>[0-9]+)\](?:\{(?P<fields>.*)\})?:'
    r'(?: (?P<inline>.*))?$'
)


class AgentDataError(ValueError):
    """Base error for deterministic agent-data operations."""


class ToonUnsupported(AgentDataError):
    """The value is outside Parley's deliberately conservative TOON subset."""


class ToonDecodeError(AgentDataError):
    """The TOON input is invalid or outside the supported subset."""


@dataclass(frozen=True)
class _Line:
    depth: int
    content: str
    number: int


def load_json_text(text: str) -> Any:
    """Load strict JSON while rejecting JavaScript-only NaN/Infinity values."""
    # Deep-but-legal documents recurse in Python's json module; share the
    # compiler's stack headroom, and turn anything beyond it into the same
    # clean data error every other malformed input gets.
    from .parser import _ensure_stack_headroom

    _ensure_stack_headroom()

    def reject_constant(value: str):
        raise AgentDataError(f"JSON contains non-finite number {value}")

    try:
        return json.loads(text, parse_constant=reject_constant)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise AgentDataError(f"invalid JSON: {exc}") from exc
    except RecursionError as exc:
        raise AgentDataError("the JSON value nests too deeply to process") from exc


def load_json_file(path: Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise AgentDataError(f"could not read UTF-8 JSON from {path}: {exc}") from exc
    return load_json_text(text), raw


def compact_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise AgentDataError(f"value is not JSON-compatible: {exc}") from exc


def pretty_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    except (TypeError, ValueError) as exc:
        raise AgentDataError(f"value is not JSON-compatible: {exc}") from exc


def _quote(value: str) -> str:
    out = ['"']
    for char in value:
        code = ord(char)
        if char == "\\":
            out.append("\\\\")
        elif char == '"':
            out.append('\\"')
        elif char == "\n":
            out.append("\\n")
        elif char == "\r":
            out.append("\\r")
        elif char == "\t":
            out.append("\\t")
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        elif 0xD800 <= code <= 0xDFFF:
            raise ToonUnsupported("TOON cannot encode unpaired Unicode surrogates")
        else:
            out.append(char)
    out.append('"')
    return "".join(out)


def _encode_key(value: str) -> str:
    return value if SAFE_KEY_RE.fullmatch(value) else _quote(value)


def _looks_numeric(value: str) -> bool:
    if not NUMBER_RE.fullmatch(value):
        return False
    unsigned = value[1:] if value.startswith("-") else value
    integer = re.split(r"[.eE]", unsigned, maxsplit=1)[0]
    return integer == "0" or not integer.startswith("0")


def _encode_string(value: str) -> str:
    must_quote = (
        not value
        or value != value.strip()
        or value in {"true", "false", "null", "[]"}
        or _looks_numeric(value)
        or not SAFE_STRING_RE.fullmatch(value)
        or value.startswith("- ")
        or value.startswith("#")
    )
    return _quote(value) if must_quote else value


def _encode_number(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    if not math.isfinite(value):
        raise ToonUnsupported("TOON only supports finite JSON numbers")
    if value == 0:
        return "0"
    magnitude = abs(value)
    raw = repr(value).lower()
    if 1e-6 <= magnitude < 1e21:
        rendered = format(Decimal(raw), "f")
        if "." in rendered:
            rendered = rendered.rstrip("0").rstrip(".")
        return rendered or "0"
    coefficient, exponent = raw.split("e")
    coefficient = coefficient.rstrip("0").rstrip(".")
    sign = "+" if not exponent.startswith(("+", "-")) else exponent[0]
    digits = exponent.lstrip("+-0") or "0"
    return f"{coefficient}e{sign}{digits}"


def _is_primitive(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _encode_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _encode_string(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _encode_number(value)
    raise ToonUnsupported(f"{type(value).__name__} is not a JSON primitive")


def _uniform_flat_table(value: list[Any]) -> tuple[list[str], list[dict[str, Any]]] | None:
    if not value or not all(isinstance(item, dict) and item for item in value):
        return None
    fields = list(value[0])
    if any(list(item) != fields for item in value[1:]):
        return None
    if any(not _is_primitive(item[field]) for item in value for field in fields):
        return None
    return fields, value


def _encode_array(lines: list[str], key: str | None, value: list[Any], depth: int) -> None:
    indent = "  " * depth
    prefix = "" if key is None else _encode_key(key)
    if not value:
        if key is None:
            lines.append("[]")
        else:
            lines.append(f"{indent}{prefix}: []")
        return
    if all(_is_primitive(item) for item in value):
        body = ",".join(_encode_scalar(item) for item in value)
        lines.append(f"{indent}{prefix}[{len(value)}]: {body}")
        return
    table = _uniform_flat_table(value)
    if table is None:
        raise ToonUnsupported(
            "TOON auto mode supports primitive arrays and uniform arrays of flat objects; "
            "this array is nested, mixed, empty-object, or non-uniform"
        )
    fields, rows = table
    encoded_fields = ",".join(_encode_key(field) for field in fields)
    lines.append(f"{indent}{prefix}[{len(rows)}]{{{encoded_fields}}}:")
    row_indent = "  " * (depth + 1)
    for row in rows:
        cells = ",".join(_encode_scalar(row[field]) for field in fields)
        lines.append(f"{row_indent}{cells}")


def _encode_object(lines: list[str], value: dict[str, Any], depth: int) -> None:
    indent = "  " * depth
    for key, item in value.items():
        if not isinstance(key, str):
            raise ToonUnsupported("TOON object keys must be text")
        encoded_key = _encode_key(key)
        if _is_primitive(item):
            lines.append(f"{indent}{encoded_key}: {_encode_scalar(item)}")
        elif isinstance(item, dict):
            lines.append(f"{indent}{encoded_key}:")
            if item:
                _encode_object(lines, item, depth + 1)
        elif isinstance(item, list):
            _encode_array(lines, key, item, depth)
        else:
            raise ToonUnsupported(f"{type(item).__name__} is not JSON-compatible")


def toon_encode(value: Any) -> str:
    """Encode the deterministic, lossless TOON v4.1 safe subset.

    Unsupported shapes raise :class:`ToonUnsupported`; callers using adaptive
    mode must retain compact JSON rather than emitting a partial conversion.
    """

    lines: list[str] = []
    if isinstance(value, dict):
        _encode_object(lines, value, 0)
    elif isinstance(value, list):
        _encode_array(lines, None, value, 0)
    elif _is_primitive(value):
        lines.append(_encode_scalar(value))
    else:
        raise ToonUnsupported(f"{type(value).__name__} is not JSON-compatible")
    return "\n".join(lines)


def _decode_quoted(token: str, line: int) -> str:
    cursor = 1
    while cursor < len(token) - 1:
        if token[cursor] != "\\":
            if ord(token[cursor]) < 0x20:
                raise ToonDecodeError(
                    f"line {line}: quoted strings cannot contain raw control characters"
                )
            cursor += 1
            continue
        cursor += 1
        if cursor >= len(token) - 1:
            raise ToonDecodeError(f"line {line}: incomplete quoted-string escape")
        escape = token[cursor]
        if escape in {'"', "\\", "n", "r", "t"}:
            cursor += 1
            continue
        if escape == "u" and re.fullmatch(r"[0-9A-Fa-f]{4}", token[cursor + 1 : cursor + 5]):
            cursor += 5
            continue
        raise ToonDecodeError(f"line {line}: unsupported quoted-string escape \\{escape}")
    try:
        value = json.loads(token)
    except json.JSONDecodeError as exc:
        raise ToonDecodeError(f"line {line}: invalid quoted string: {exc.msg}") from exc
    if not isinstance(value, str):
        raise ToonDecodeError(f"line {line}: quoted key or value must decode to text")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ToonDecodeError(f"line {line}: unpaired or escaped Unicode surrogates are unsupported")
    return value


def _decode_key(token: str, line: int) -> str:
    token = token.strip()
    if token.startswith('"'):
        return _decode_quoted(token, line)
    if not SAFE_KEY_RE.fullmatch(token):
        raise ToonDecodeError(f"line {line}: unsupported or invalid key {token!r}")
    return token


def _decode_scalar(token: str, line: int) -> Any:
    token = token.strip()
    if token.startswith('"'):
        return _decode_quoted(token, line)
    if token == "true":
        return True
    if token == "false":
        return False
    if token == "null":
        return None
    if _looks_numeric(token):
        try:
            return float(token) if any(char in token.lower() for char in (".", "e")) else int(token)
        except ValueError as exc:
            raise ToonDecodeError(f"line {line}: invalid number {token!r}") from exc
    return token


def _split_tokens(text: str, line: int) -> list[str]:
    if text == "":
        return [""]
    parts: list[str] = []
    start = 0
    quoted = False
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
        elif char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == "," and not quoted:
            parts.append(text[start:index])
            start = index + 1
    if quoted or escaped:
        raise ToonDecodeError(f"line {line}: unterminated quoted token")
    parts.append(text[start:])
    return parts


def _prepare_lines(text: str) -> list[_Line]:
    prepared: list[_Line] = []
    for number, raw in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        if not raw.strip() or raw.lstrip(" ").startswith("#"):
            continue
        if raw.endswith((" ", "\t")) or "\t" in raw or "\r" in raw:
            raise ToonDecodeError(f"line {number}: indentation/trailing whitespace is not canonical")
        spaces = len(raw) - len(raw.lstrip(" "))
        if spaces % 2:
            raise ToonDecodeError(f"line {number}: indentation must use two-space units")
        prepared.append(_Line(spaces // 2, raw[spaces:], number))
    return prepared


def _parse_header(content: str, line: int):
    match = HEADER_RE.fullmatch(content)
    if not match:
        return None
    fields_text = match.group("fields")
    fields = None
    if fields_text is not None:
        fields = [_decode_key(token, line) for token in _split_tokens(fields_text, line)]
        if not fields or len(fields) != len(set(fields)):
            raise ToonDecodeError(f"line {line}: table fields must be non-empty and unique")
    return {
        "key": None if match.group("key") is None else _decode_key(match.group("key"), line),
        "count": int(match.group("count")),
        "fields": fields,
        "inline": match.group("inline"),
    }


def _parse_array(lines: list[_Line], index: int, depth: int, header: dict) -> tuple[list[Any], int]:
    count = header["count"]
    fields = header["fields"]
    inline = header["inline"]
    if fields is None:
        if inline is None:
            raise ToonDecodeError(
                f"line {lines[index].number}: expanded/mixed array form is outside the supported safe subset"
            )
        tokens = _split_tokens(inline, lines[index].number)
        if count != len(tokens):
            raise ToonDecodeError(
                f"line {lines[index].number}: declared {count} items but found {len(tokens)}"
            )
        return [_decode_scalar(token, lines[index].number) for token in tokens], index + 1
    if inline is not None:
        raise ToonDecodeError(f"line {lines[index].number}: table header cannot carry inline values")
    rows: list[dict[str, Any]] = []
    cursor = index + 1
    for _ in range(count):
        if cursor >= len(lines) or lines[cursor].depth != depth + 1:
            raise ToonDecodeError(f"line {lines[index].number}: declared {count} table rows")
        cells = _split_tokens(lines[cursor].content, lines[cursor].number)
        if len(cells) != len(fields):
            raise ToonDecodeError(
                f"line {lines[cursor].number}: expected {len(fields)} cells but found {len(cells)}"
            )
        rows.append({field: _decode_scalar(cell, lines[cursor].number) for field, cell in zip(fields, cells)})
        cursor += 1
    return rows, cursor


def _split_field(content: str, line: int) -> tuple[str, str]:
    quoted = False
    escaped = False
    for index, char in enumerate(content):
        if escaped:
            escaped = False
        elif char == "\\" and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == ":" and not quoted:
            return _decode_key(content[:index], line), content[index + 1 :].lstrip(" ")
    raise ToonDecodeError(f"line {line}: expected key: value")


def _parse_object(lines: list[_Line], index: int, depth: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    cursor = index
    while cursor < len(lines) and lines[cursor].depth == depth:
        current = lines[cursor]
        header = _parse_header(current.content, current.number)
        if header is not None and header["key"] is not None:
            key = header["key"]
            value, cursor = _parse_array(lines, cursor, depth, header)
        else:
            key, tail = _split_field(current.content, current.number)
            cursor += 1
            if tail == "[]":
                value = []
            elif tail:
                value = _decode_scalar(tail, current.number)
            elif cursor < len(lines) and lines[cursor].depth == depth + 1:
                value, cursor = _parse_object(lines, cursor, depth + 1)
            else:
                value = {}
        if key in result:
            raise ToonDecodeError(f"line {current.number}: duplicate key {key!r}")
        result[key] = value
    if cursor < len(lines) and lines[cursor].depth > depth:
        raise ToonDecodeError(f"line {lines[cursor].number}: unexpected indentation")
    return result, cursor


def toon_decode(text: str) -> Any:
    """Decode Parley's strict TOON v4.1 safe subset."""

    lines = _prepare_lines(text)
    if not lines:
        return {}
    if lines[0].depth != 0:
        raise ToonDecodeError(f"line {lines[0].number}: root content cannot be indented")
    if len(lines) == 1 and lines[0].content == "[]":
        return []
    header = _parse_header(lines[0].content, lines[0].number)
    if header is not None and header["key"] is None:
        value, cursor = _parse_array(lines, 0, 0, header)
    elif len(lines) == 1 and ":" not in lines[0].content:
        value, cursor = _decode_scalar(lines[0].content, lines[0].number), 1
    else:
        value, cursor = _parse_object(lines, 0, 0)
    if cursor != len(lines):
        raise ToonDecodeError(f"line {lines[cursor].number}: trailing content outside the root value")
    return value


def json_model_equal(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return Decimal(str(left)) == Decimal(str(right))
    if isinstance(left, str) or isinstance(right, str):
        return isinstance(left, str) and isinstance(right, str) and left == right
    if isinstance(left, list) or isinstance(right, list):
        return (
            isinstance(left, list)
            and isinstance(right, list)
            and len(left) == len(right)
            and all(json_model_equal(a, b) for a, b in zip(left, right))
        )
    if isinstance(left, dict) or isinstance(right, dict):
        return (
            isinstance(left, dict)
            and isinstance(right, dict)
            and list(left) == list(right)
            and all(json_model_equal(left[key], right[key]) for key in left)
        )
    return False


def token_counter(name: str) -> tuple[str, Callable[[str], int]]:
    if name == "rough":
        return "rough-regex-v1", lambda text: len(ROUGH_TOKEN_RE.findall(text))
    try:
        import tiktoken  # type: ignore[import-not-found]
    except ImportError as exc:
        raise AgentDataError(
            f"tokenizer {name!r} needs tiktoken; install Parley with the research extra"
        ) from exc
    try:
        encoding = tiktoken.get_encoding(name)
    except Exception as exc:
        raise AgentDataError(f"unknown tiktoken encoding {name!r}: {exc}") from exc
    return f"tiktoken:{name}", lambda text: len(encoding.encode(text))


def compare_value(value: Any, *, tokenizer: str = "rough", source_bytes: bytes | None = None) -> dict[str, Any]:
    tokenizer_name, count = token_counter(tokenizer)
    json_text = compact_json(value)
    json_tokens = count(json_text)
    candidates: dict[str, Any] = {
        "json": {
            "supported": True,
            "bytes": len(json_text.encode("utf-8")),
            "characters": len(json_text),
            "tokens": json_tokens,
            "round_trip": True,
        }
    }
    toon_text: str | None = None
    toon_error: str | None = None
    try:
        toon_text = toon_encode(value)
        decoded = toon_decode(toon_text)
        if not json_model_equal(value, decoded):
            raise ToonUnsupported("TOON round-trip changed the JSON data model")
    except (ToonUnsupported, ToonDecodeError) as exc:
        toon_error = str(exc)
    if toon_text is None:
        candidates["toon"] = {"supported": False, "reason": toon_error}
        selected = "json"
        selection_reason = "toon_unsupported"
        savings_tokens = 0
        savings_percent = 0.0
    else:
        toon_tokens = count(toon_text)
        candidates["toon"] = {
            "supported": True,
            "spec_version": TOON_SPEC_VERSION,
            "profile": "parley-safe-subset-v1",
            "bytes": len(toon_text.encode("utf-8")),
            "characters": len(toon_text),
            "tokens": toon_tokens,
            "round_trip": True,
        }
        if toon_tokens < json_tokens:
            selected = "toon"
            selection_reason = "strictly_fewer_tokens"
            savings_tokens = json_tokens - toon_tokens
            savings_percent = 100.0 * savings_tokens / json_tokens if json_tokens else 0.0
        else:
            selected = "json"
            selection_reason = "json_not_larger"
            savings_tokens = 0
            savings_percent = 0.0
    return {
        "schema_version": 1,
        "semantic_format": "json-data-model",
        "tokenizer": tokenizer_name,
        "input_sha256": None if source_bytes is None else hashlib.sha256(source_bytes).hexdigest(),
        "selected_format": selected,
        "selection_reason": selection_reason,
        "savings": {
            "tokens": savings_tokens,
            "percent_vs_compact_json": round(savings_percent, 4),
        },
        "candidates": candidates,
    }


def packed_text(value: Any, report: dict[str, Any], requested_format: str = "auto") -> str:
    if requested_format not in {"auto", "json", "toon"}:
        raise AgentDataError(f"unknown output format {requested_format!r}")
    if requested_format == "json":
        return compact_json(value)
    if requested_format == "toon":
        try:
            encoded = toon_encode(value)
            if not json_model_equal(value, toon_decode(encoded)):
                raise ToonUnsupported("TOON round-trip changed the JSON data model")
            return encoded
        except (ToonUnsupported, ToonDecodeError) as exc:
            raise AgentDataError(f"cannot safely encode this value as TOON: {exc}") from exc
    return toon_encode(value) if report["selected_format"] == "toon" else compact_json(value)
