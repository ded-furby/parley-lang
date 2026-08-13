"""JSON-native normalization and atomic persistence for benchmark evidence."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable


def json_native(value: Any) -> Any:
    """Return the exact value shape that JSON persistence will retain."""
    return json.loads(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    )


def header_pairs(pairs: Iterable[tuple[str, str]]) -> list[list[str]]:
    """Represent ordered response-header pairs without tuple/array drift."""
    return [[name.lower(), value] for name, value in pairs]


def atomic_write_json_native(path: Path, value: Any) -> Any:
    """Normalize, atomically persist, reread, and verify one JSON value."""
    normalized = json_native(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(normalized, ensure_ascii=False, allow_nan=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)
    persisted = json.loads(path.read_text(encoding="utf-8"))
    if persisted != normalized:
        raise RuntimeError(f"JSON evidence round trip changed shape: {path}")
    return normalized
