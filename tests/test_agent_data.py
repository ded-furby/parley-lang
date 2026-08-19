import hashlib
import json

import pytest

from conftest import run_cli
from parley.agent_data import (
    AgentDataError,
    ToonDecodeError,
    ToonUnsupported,
    compare_value,
    json_model_equal,
    load_json_text,
    packed_text,
    toon_decode,
    toon_encode,
)


@pytest.mark.parametrize(
    "value",
    [
        {},
        [],
        None,
        True,
        0,
        1e20,
        1e-7,
        {"name": "Parley", "active": True, "empty": {}},
        {"nested": {"comma": "a,b", "quote": 'say "hi"'}, "items": [1, "2", None]},
    ],
)
def test_safe_subset_round_trips_the_json_data_model(value):
    encoded = toon_encode(value)
    assert json_model_equal(value, toon_decode(encoded))


def test_uniform_objects_use_a_counted_table_and_round_trip():
    value = {
        "checks": [
            {"name": "unit", "passed": True, "count": 362},
            {"name": "types", "passed": True, "count": 24},
        ]
    }

    encoded = toon_encode(value)

    assert encoded == (
        "checks[2]{name,passed,count}:\n"
        "  unit,true,362\n"
        "  types,true,24"
    )
    assert toon_decode(encoded) == value


def test_ambiguous_strings_and_keys_are_quoted():
    value = {
        "spaced key": "true",
        "numeric": "001",
        "comment": "# not a comment",
        "control": "line one\nline two",
    }

    encoded = toon_encode(value)

    assert '"spaced key": "true"' in encoded
    assert 'numeric: 001' in encoded
    assert 'comment: "# not a comment"' in encoded
    assert 'control: "line one\\nline two"' in encoded
    assert toon_decode(encoded) == value


def test_nonuniform_or_nested_arrays_are_outside_the_safe_subset():
    with pytest.raises(ToonUnsupported, match="non-uniform"):
        toon_encode([{"name": "a"}, {"name": "b", "extra": 1}])
    with pytest.raises(ToonUnsupported, match="nested"):
        toon_encode([[1, 2], [3, 4]])


def test_strict_decoder_rejects_counts_width_duplicates_and_noncanonical_space():
    with pytest.raises(ToonDecodeError, match="declared 3 items"):
        toon_decode("values[3]: 1,2")
    with pytest.raises(ToonDecodeError, match="expected 2 cells"):
        toon_decode("rows[1]{a,b}:\n  1")
    with pytest.raises(ToonDecodeError, match="duplicate key"):
        toon_decode("name: first\nname: second")
    with pytest.raises(ToonDecodeError, match="whitespace"):
        toon_decode("name: value ")


def test_strict_decoder_rejects_json_escapes_outside_the_profile():
    with pytest.raises(ToonDecodeError, match="unsupported quoted-string escape"):
        toon_decode(r'name: "a\b"')
    with pytest.raises(ToonDecodeError, match="surrogates"):
        toon_decode(r'name: "\ud800"')


def test_auto_selects_toon_only_when_supported_and_strictly_smaller():
    table = [{"id": index, "status": "ready", "passed": True} for index in range(20)]
    report = compare_value(table)

    assert report["selected_format"] == "toon"
    assert report["selection_reason"] == "strictly_fewer_tokens"
    assert report["savings"]["tokens"] > 0
    assert report["candidates"]["toon"]["round_trip"] is True
    assert packed_text(table, report) == toon_encode(table)

    nonuniform = [{"name": "a"}, {"name": "b", "extra": 1}]
    fallback = compare_value(nonuniform)
    assert fallback["selected_format"] == "json"
    assert fallback["selection_reason"] == "toon_unsupported"
    assert fallback["candidates"]["toon"]["supported"] is False
    assert json.loads(packed_text(nonuniform, fallback)) == nonuniform


def test_strict_json_rejects_non_finite_numbers():
    with pytest.raises(AgentDataError, match="non-finite"):
        load_json_text('{"value": NaN}')


def test_data_cli_compare_pack_check_and_unpack(tmp_path):
    value = {
        "checks": [
            {"name": f"check-{index}", "status": "passed", "count": index}
            for index in range(12)
        ]
    }
    source = tmp_path / "release.json"
    packed = tmp_path / "release.toon"
    measurement = tmp_path / "release.measurement.json"
    restored = tmp_path / "restored.json"
    source.write_text(json.dumps(value), encoding="utf-8")

    compared = run_cli(["data", "compare", str(source)], cwd=tmp_path)
    assert compared.returncode == 0, compared.stderr
    comparison = json.loads(compared.stdout)
    assert comparison["selected_format"] == "toon"

    proc = run_cli(
        [
            "data", "pack", str(source), "--output", str(packed),
            "--report", str(measurement),
        ],
        cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Packed" in proc.stdout
    assert toon_decode(packed.read_text(encoding="utf-8")) == value
    report = json.loads(measurement.read_text(encoding="utf-8"))
    assert report["requested_format"] == "auto"
    assert report["delivered_format"] == "toon"
    assert report["output_sha256"] == hashlib.sha256(packed.read_bytes()).hexdigest()

    checked = run_cli(["data", "check", str(packed), "--json"], cwd=tmp_path)
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["ok"] is True

    unpacked = run_cli(
        ["data", "unpack", str(packed), "--output", str(restored), "--pretty"],
        cwd=tmp_path,
    )
    assert unpacked.returncode == 0, unpacked.stderr
    assert json.loads(restored.read_text(encoding="utf-8")) == value


def test_data_cli_refuses_overwrite_and_input_output_identity(tmp_path):
    source = tmp_path / "input.json"
    output = tmp_path / "packed.txt"
    source.write_text('{"items":[1,2,3]}', encoding="utf-8")
    output.write_text("keep me", encoding="utf-8")

    existing = run_cli(
        ["data", "pack", str(source), "--output", str(output)], cwd=tmp_path)
    assert existing.returncode == 1
    assert "pass --force" in existing.stderr
    assert output.read_text(encoding="utf-8") == "keep me"

    identity = run_cli(
        ["data", "pack", str(source), "--output", str(source), "--force"], cwd=tmp_path)
    assert identity.returncode == 1
    assert "different files" in identity.stderr
    assert json.loads(source.read_text(encoding="utf-8")) == {"items": [1, 2, 3]}


def test_forced_toon_fails_cleanly_for_unsupported_shape(tmp_path):
    source = tmp_path / "nonuniform.json"
    source.write_text('[{"a":1},{"a":2,"b":3}]', encoding="utf-8")

    proc = run_cli(
        ["data", "pack", str(source), "--format", "toon"], cwd=tmp_path)

    assert proc.returncode == 1
    assert "cannot safely encode" in proc.stderr


def test_unpack_and_check_accept_the_json_fallback_pack_produces(tmp_path):
    # A nested shape is outside the TOON profile, so `pack` delivers compact
    # JSON. The documented pack -> unpack round trip has to survive that.
    source = tmp_path / "nested.json"
    document = {"rows": [{"n": "a", "v": {"deep": [1, 2, {"x": True}]}}]}
    source.write_text(json.dumps(document))
    packed = tmp_path / "nested.agent"

    pack = run_cli(["data", "pack", str(source), "--output", str(packed)], cwd=tmp_path)
    assert pack.returncode == 0, pack.stdout + pack.stderr
    assert packed.read_text().lstrip().startswith("{")

    restored = tmp_path / "restored.json"
    unpack = run_cli(
        ["data", "unpack", str(packed), "--output", str(restored)], cwd=tmp_path)
    assert unpack.returncode == 0, unpack.stdout + unpack.stderr
    assert json.loads(restored.read_text()) == document

    checked = run_cli(["data", "check", str(packed), "--json"], cwd=tmp_path)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert json.loads(checked.stdout)["format"] == "json"


def test_check_still_reports_toon_for_a_toon_artifact(tmp_path):
    source = tmp_path / "rows.json"
    document = {"rows": [{"n": "a", "v": 1}, {"n": "b", "v": 2}]}
    source.write_text(json.dumps(document))
    packed = tmp_path / "rows.agent"
    run_cli(["data", "pack", str(source), "--output", str(packed)], cwd=tmp_path)

    checked = run_cli(["data", "check", str(packed), "--json"], cwd=tmp_path)
    assert json.loads(checked.stdout)["format"] == "toon"


def test_deep_json_is_processed_or_refused_cleanly(tmp_path):
    import json as _json
    import subprocess
    import sys

    # 3,000 levels is legal and must work; 60,000 must come back as a clean
    # data error, never a traceback (the same contract parley check keeps).
    deep = {"a": None}
    node = deep
    for _ in range(3000):
        node["a"] = {"a": None}
        node = node["a"]
    node["a"] = 1
    legal = tmp_path / "deep.json"
    legal.write_text(_json.dumps(deep))
    ok = subprocess.run([sys.executable, "-m", "parley.cli", "data", "compare", str(legal)],
                        capture_output=True, text=True, timeout=120)
    assert ok.returncode == 0, ok.stderr

    absurd = tmp_path / "deep60k.json"
    absurd.write_text('{"a":' * 60000 + "1" + "}" * 60000)
    for command in (["data", "compare", str(absurd)],
                    ["data", "pack", str(absurd), "--output", str(tmp_path / "d.agent")]):
        proc = subprocess.run([sys.executable, "-m", "parley.cli", *command],
                              capture_output=True, text=True, timeout=120)
        combined = proc.stdout + proc.stderr
        assert "Traceback" not in combined
        if proc.returncode != 0:
            assert "nests too deeply" in combined
