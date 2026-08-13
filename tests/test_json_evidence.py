import json

import pytest

from benchmarks.json_evidence import (
    atomic_write_json_native,
    header_pairs,
    json_native,
)


@pytest.mark.parametrize(
    ("pairs", "expected"),
    [
        ([], []),
        (
            [("Location", "/api/items/7"), ("X-State", "accepted")],
            [["location", "/api/items/7"], ["x-state", "accepted"]],
        ),
        (
            [("Set-Cookie", "a=1"), ("set-cookie", "b=2")],
            [["set-cookie", "a=1"], ["set-cookie", "b=2"]],
        ),
    ],
)
def test_header_pairs_are_json_native_and_preserve_duplicates(pairs, expected):
    result = header_pairs(pairs)
    assert result == expected
    assert json.loads(json.dumps(result)) == result


def test_atomic_evidence_normalizes_before_comparison(tmp_path):
    path = tmp_path / "attempt.json"
    source = {
        "headers": header_pairs([("WWW-Authenticate", "Bearer")]),
        "nested_tuple": ("becomes", "array"),
    }
    normalized = atomic_write_json_native(path, source)
    assert normalized == {
        "headers": [["www-authenticate", "Bearer"]],
        "nested_tuple": ["becomes", "array"],
    }
    assert json.loads(path.read_text()) == normalized


def test_json_native_rejects_nonfinite_numbers():
    with pytest.raises(ValueError):
        json_native({"invalid": float("nan")})
