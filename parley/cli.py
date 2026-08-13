"""The `parley` command-line tool.

  parley run program.par          compile (debug) and run
  parley build program.par -o x   compile (release) to a native binary
  parley check program.par        parse + type-check only (fast agent loop)
  parley check program.par --json machine-readable diagnostics
  parley rust program.par         print the generated Rust
  parley explain P204             explain an error code
  parley new myproject            start a new program
  parley doctor                   verify local setup
  parley data compare input.json measure safe agent-context encodings
  parley data pack input.json     select JSON or TOON with a round-trip gate
  parley data unpack input.toon   restore strict TOON to canonical JSON
  parley data check input.toon    validate strict TOON without changing it
  parley package install name src vendor a local package
  parley package publish name src print a registry entry with owner metadata
  parley package review name src  dry-run package submission review
  parley package verify           verify vendored packages against the lockfile
  parley package check-registry x validate a package registry manifest
  parley workflow list            list bundled workflow starters
  parley workflow new name        create a workflow from a starter
  parley workflow run name        safely run a file-to-file workflow
  parley workflow test name       run deterministic workflow fixtures
  parley workflow install name    install a checksummed workflow product
  parley workflow verify          verify installed workflow checksums
  parley web check app            verify typed HTTP/JSON and browser contracts
  parley web build app            build a native server and browser/WASM bundle
  parley web serve app            build and run the full-stack project locally
  parley benchmark measure        measure the seed research corpus
  parley benchmark prompt         render language-neutral benchmark prompts
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import hmac
import importlib.util
from importlib import resources
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen
from pathlib import Path

from . import __version__
from .agent_data import (
    AgentDataError,
    compare_value,
    compact_json,
    load_json_file,
    load_json_text,
    packed_text,
    pretty_json,
    toon_decode,
)
from .checker import check_program
from .diagnostics import Diagnostic, ParleyError, explain, render_human, render_json
from .emit_rust import emit_program, program_uses_json
from .parser import SourceMap, parse_program
from .workflows import WORKFLOW_TEMPLATES
from .workflows.catalog import WORKFLOW_CATALOG
from .web import (
    WASM_CARGO_TOML,
    WEB_CARGO_TOML,
    WEB_CARGO_TOML_DERIVE,
    WebProject,
    WebProjectError,
    check_browser,
    check_web,
    load_project,
    render_browser,
    render_server,
)

CARGO_TOML = """\
[package]
name = "parley_program"
version = "0.1.0"
edition = "2021"

[profile.release]
strip = true
# Rust wraps on overflow in release by default. Parley promises the same
# behaviour from `run` and `build` — overflow stops the program — so the
# release profile keeps the checks debug builds already have.
overflow-checks = true
"""

CARGO_TOML_JSON = CARGO_TOML + """
[dependencies]
serde = { version = "=1.0.229", features = ["derive"] }
serde_json = "=1.0.151"
"""

NEW_TEMPLATE = """\
note: {name} — written in Parley

to main:
    say "Hello from {name}!"
    let numbers be a list of 3, 1, 4, 1, 5
    say "the sum is {{sum of numbers}}"
"""

PACKAGE_TEMPLATE = """\
note: {name} package

to package_ready giving yesno:
    give back yes
"""

LOCK_FILE = "parley.lock.json"
PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
PACKAGE_VERSION_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z][0-9A-Za-z.-]*)?(?:\+[0-9A-Za-z][0-9A-Za-z.-]*)?$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
SIGNATURE_RE = re.compile(r"^hmac-sha256:[0-9a-fA-F]{64}$")
DEFAULT_REGISTRY = "parley.registry.json"
WORKFLOW_LOCK_FILE = "parley.workflows.lock.json"

WEB_NEW_SOURCE = """\
a health has ok as yesno, service as text

to health_check giving health:
    give back a health with ok yes, service "{name}"
"""

WEB_NEW_INDEX = """\
<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}</title>
<main>
  <h1>{name}</h1>
  <p id="status">Checking the typed Parley API…</p>
</main>
<script type="module">
const response = await fetch("/api/health");
const value = await response.json();
document.querySelector("#status").textContent = value.ok
  ? `${{value.service}} is ready.` : "The service is not ready.";
</script>
"""


# ------------------------------------------------------------------ pipeline

def compile_source(path: str):
    """parse → check → emit. Returns (rust, linemap, srcmap); raises ParleyError
    with file-resolved diagnostics on any failure."""
    program, srcmap = parse_program(path)
    diags = check_program(program)
    if diags:
        raise ParleyError(srcmap.resolve(diags))
    uses_json = program_uses_json(program)
    rust, linemap = emit_program(program, serde=uses_json)
    return rust, linemap, srcmap, uses_json


def _build_dir(path: Path) -> Path:
    d = Path(".parley-build") / path.stem
    (d / "src").mkdir(parents=True, exist_ok=True)
    return d


def _target_dir() -> Path:
    return (Path(".parley-build") / "target").resolve()


def _cargo_env() -> dict:
    env = dict(os.environ)
    env["CARGO_TARGET_DIR"] = str(_target_dir())
    return env


def _map_rustc_errors(stdout: str, linemap: dict[int, int], srcmap: SourceMap) -> list[Diagnostic]:
    diags = []
    for line in stdout.splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("reason") != "compiler-message":
            continue
        m = msg.get("message", {})
        if m.get("level") != "error":
            continue
        text = m.get("message", "rust build error")
        par_line = 0
        for span in m.get("spans", []):
            if span.get("is_primary"):
                rust_line = span.get("line_start", 0)
                for ln in range(rust_line, max(rust_line - 80, 0), -1):
                    if ln in linemap:
                        par_line = linemap[ln]
                        break
                break
        if "will overflow" in text:
            # Not a checker gap: the author wrote arithmetic on literals whose
            # result cannot be a whole number, and rustc proved it up front.
            d = Diagnostic(
                "P317",
                "This arithmetic goes past the largest value a number can hold.",
                line=par_line,
                hint="Whole numbers run from -9223372036854775808 to "
                     "9223372036854775807. Use `decimal` values if you need a "
                     "wider range.")
        else:
            d = Diagnostic("P901", f"The Rust backend rejected this line: {text}",
                           line=par_line,
                           hint="This usually means a Parley checker gap. Simplify the line, "
                                "and please report it: https://github.com/ded-furby/parley-lang/issues")
        diags.append(d)
    if not diags:
        diags.append(Diagnostic("P901", "The Rust backend rejected the program.",
                                line=1))
    return srcmap.resolve(diags)


def cargo_build(path: Path, rust: str, linemap: dict[int, int], srcmap: SourceMap,
                release: bool, uses_json: bool = False) -> Path:
    """Build the generated Rust; returns the binary path. Raises ParleyError."""
    if shutil.which("cargo") is None:
        raise ParleyError([Diagnostic(
            "P902", "Parley needs Rust to build native binaries, and `cargo` was not found.",
            file=srcmap.main_file, line=1,
            hint="Install it from https://rustup.rs (one command), then re-run.")])
    d = _build_dir(path)
    (d / "Cargo.toml").write_text(CARGO_TOML_JSON if uses_json else CARGO_TOML)
    (d / "src" / "main.rs").write_text(rust)
    cmd = ["cargo", "build", "--message-format=json", "-q"]
    if release:
        cmd.append("--release")
    proc = subprocess.run(cmd, cwd=d, env=_cargo_env(), capture_output=True, text=True)
    if proc.returncode != 0:
        raise ParleyError(_map_rustc_errors(proc.stdout, linemap, srcmap))
    profile = "release" if release else "debug"
    return _target_dir() / profile / "parley_program"


def _fail(e: ParleyError, srcmap: SourceMap | None, as_json: bool = False) -> int:
    if as_json:
        print(render_json(e.diagnostics))
    else:
        sources = srcmap.sources if srcmap else {}
        sys.stderr.write(render_human(e.diagnostics, sources))
    return 1


# ------------------------------------------------------------------ commands

def cmd_run(args) -> int:
    path = Path(args.file)
    try:
        rust, linemap, srcmap, uses_json = compile_source(args.file)
        binary = cargo_build(path, rust, linemap, srcmap, release=False, uses_json=uses_json)
    except ParleyError as e:
        return _fail(e, None)
    forwarded = [a for a in getattr(args, "program_args", []) if a != "--"]
    proc = subprocess.run([str(binary), *forwarded])
    return proc.returncode if proc.returncode >= 0 else 1

def cmd_build(args) -> int:
    path = Path(args.file)
    try:
        rust, linemap, srcmap, uses_json = compile_source(args.file)
        binary = cargo_build(path, rust, linemap, srcmap, release=True, uses_json=uses_json)
    except ParleyError as e:
        return _fail(e, None)
    out = Path(args.output or path.stem)
    try:
        # copy2 into a directory silently writes a differently-named file and
        # then reports the directory's size, so refuse that up front.
        if out.is_dir():
            raise IsADirectoryError(21, "Is a directory")
        shutil.copy2(binary, out)
    except OSError as e:
        return _fail(ParleyError([Diagnostic(
            "P903", f'Cannot write the binary to "{out}": {e.strerror or e}.',
            file=str(path), line=1,
            hint="Pick an output path in a writable directory, "
                 "e.g. `-o ./program`.")]), None)
    shown = out if out.is_absolute() else f"./{out}"
    print(f"Built {shown} ({out.stat().st_size // 1024} KiB)")
    return 0


def cmd_check(args) -> int:
    srcmap = None
    try:
        program, srcmap = parse_program(args.file)
        diags = check_program(program)
        if diags:
            raise ParleyError(srcmap.resolve(diags))
    except ParleyError as e:
        return _fail(e, srcmap, as_json=args.json)
    if args.json:
        print(render_json([]))
    else:
        print(f"✓ {args.file}: no problems found.")
    return 0


def cmd_rust(args) -> int:
    try:
        rust, _, _, _ = compile_source(args.file)
    except ParleyError as e:
        return _fail(e, None)
    print(rust, end="")
    return 0


def cmd_explain(args) -> int:
    print(explain(args.code))
    return 0


def cmd_new(args) -> int:
    d = Path(args.name)
    if d.exists():
        print(f"'{args.name}' already exists.", file=sys.stderr)
        return 1
    d.mkdir(parents=True)
    (d / "main.par").write_text(NEW_TEMPLATE.format(name=args.name))
    print(f"Created {args.name}/main.par — run it with:\n  parley run {args.name}/main.par")
    return 0


def cmd_workflow_list(args) -> int:
    print("Parley workflow starters")
    for name, metadata in WORKFLOW_TEMPLATES.items():
        print(f"{name:18} {metadata['description']}")
    print("\nFirst-party workflow catalog")
    for name, description in WORKFLOW_CATALOG.items():
        print(f"{name:18} {description}")
    try:
        lock = _read_workflow_lock()
    except OSError as exc:
        print(f"workflow error: {exc}", file=sys.stderr)
        return 1
    if lock["workflows"]:
        print("\nInstalled workflows")
        for name, metadata in sorted(lock["workflows"].items()):
            print(f"{name:18} {metadata['version']}  {metadata['path']}")
    return 0


def cmd_workflow_new(args) -> int:
    root = Path(args.name)
    if root.exists():
        print(f"workflow error: '{args.name}' already exists.", file=sys.stderr)
        return 1
    if not PACKAGE_NAME_RE.fullmatch(root.name):
        print(
            "workflow error: names may only contain letters, numbers, dashes, "
            "underscores, and dots",
            file=sys.stderr,
        )
        return 1

    template = WORKFLOW_TEMPLATES[args.template]
    source = (
        resources.files("parley.workflows.templates")
        .joinpath(f"{args.template}.par")
        .read_text()
        .replace("__WORKFLOW_NAME__", root.name)
    )
    root.mkdir(parents=True)
    (root / "main.par").write_text(source)
    (root / "input.txt").write_text(template["sample"])
    fixture_root = root / "tests" / "sample"
    fixture_root.mkdir(parents=True)
    (fixture_root / "input.txt").write_text(template["sample"])
    (fixture_root / "expected.txt").write_text(template["expected"])
    (root / "workflow.json").write_text(json.dumps({
        "schema_version": 2,
        "name": root.name,
        "template": args.template,
        "entrypoint": "main.par",
        "inputs": [
            {
                "name": "source",
                "description": "Text file to process",
            },
        ],
        "tests": [
            {
                "name": "sample",
                "inputs": {"source": "tests/sample/input.txt"},
                "expected_output": "tests/sample/expected.txt",
            },
        ],
    }, indent=2) + "\n")
    print(
        f"Created {root.as_posix()}/ from the {args.template} starter.\n"
        f"Check it: parley check {root.as_posix()}/main.par\n"
        f"Test it:  parley workflow test {root.as_posix()}\n"
        f"Run it:   parley workflow run {root.as_posix()} "
        f"--input source={root.as_posix()}/input.txt --output output.txt"
    )
    return 0


def _read_workflow(target: str) -> tuple[Path, Path, dict]:
    path = Path(target)
    if not path.exists() and PACKAGE_NAME_RE.fullmatch(target):
        installed = Path("parley_workflows") / target
        if installed.exists():
            path = installed
    manifest = {"schema_version": 1, "entrypoint": path.name}
    root = path.parent
    if path.is_dir():
        root = path
        manifest_path = path / "workflow.json"
        entrypoint = "main.par"
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text())
            except json.JSONDecodeError as exc:
                raise OSError(f"invalid workflow.json: {exc.msg}") from exc
            if manifest.get("schema_version") not in {1, 2}:
                raise OSError("workflow.json must use schema_version 1 or 2")
            entrypoint = manifest.get("entrypoint", "main.par")
            if not isinstance(entrypoint, str) or not entrypoint.strip():
                raise OSError("workflow.json entrypoint must be a file name")
            entry_path = Path(entrypoint)
            if entry_path.is_absolute() or ".." in entry_path.parts:
                raise OSError("workflow.json entrypoint must stay inside the workflow")
        path = path / entrypoint
    if not path.is_file():
        raise OSError(f"workflow entrypoint does not exist: {path.as_posix()}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise OSError("workflow.json entrypoint must stay inside the workflow")
    return path, root, manifest


def _workflow_input_names(manifest: dict) -> list[str]:
    if manifest.get("schema_version") == 1:
        return ["input"]
    inputs = manifest.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise OSError("schema-2 workflow.json needs a non-empty inputs list")
    names: list[str] = []
    for item in inputs:
        if not isinstance(item, dict):
            raise OSError("workflow.json inputs must be objects")
        name = item.get("name")
        if not isinstance(name, str) or not PACKAGE_NAME_RE.fullmatch(name):
            raise OSError(
                "workflow input names may only contain letters, numbers, dashes, "
                "underscores, and dots")
        if name in names:
            raise OSError(f"workflow input name is duplicated: {name}")
        description = item.get("description")
        if description is not None and not isinstance(description, str):
            raise OSError(f"workflow input description must be text: {name}")
        names.append(name)
    return names


def _workflow_inputs(raw_inputs: list[str], names: list[str], schema_version: int) -> list[Path]:
    if schema_version == 1:
        if len(raw_inputs) != 1:
            raise OSError("schema-1 workflows need exactly one --input PATH")
        raw = raw_inputs[0]
        if raw.startswith("input="):
            raw = raw.split("=", 1)[1]
        values = {"input": raw}
    else:
        values: dict[str, str] = {}
        for raw in raw_inputs:
            if "=" not in raw:
                raise OSError("schema-2 workflow inputs use --input NAME=PATH")
            name, value = raw.split("=", 1)
            if name not in names:
                raise OSError(f"unknown workflow input: {name}")
            if name in values:
                raise OSError(f"workflow input was provided twice: {name}")
            if not value:
                raise OSError(f"workflow input path is empty: {name}")
            values[name] = value
        missing = [name for name in names if name not in values]
        if missing:
            raise OSError("missing workflow inputs: " + ", ".join(missing))

    paths: list[Path] = []
    for name in names:
        value = values[name]
        path = Path(value).resolve()
        if "\n" in str(path):
            raise OSError("workflow paths cannot contain newlines")
        if not path.is_file():
            raise OSError(f"input file does not exist: {value}")
        paths.append(path)
    return paths


def _validate_workflow_output(input_paths: list[Path], raw_output: str, force: bool) -> Path:
    output_path = Path(raw_output).resolve()
    if "\n" in str(output_path):
        raise OSError("workflow paths cannot contain newlines")
    for input_path in input_paths:
        same_existing_file = output_path.exists() and os.path.samefile(input_path, output_path)
        if input_path == output_path or same_existing_file:
            raise OSError("workflow inputs and output must be different files")
    if not output_path.parent.is_dir():
        raise OSError(f"output directory does not exist: {output_path.parent}")
    if output_path.exists() and not output_path.is_file():
        raise OSError(f"output path is not a file: {raw_output}")
    if output_path.exists() and not force:
        raise OSError(f"output already exists: {raw_output}; pass --force to replace it")
    return output_path


def _run_workflow_binary(binary: Path, input_paths: list[Path], output_path: Path,
                         capture_output: bool = False) -> subprocess.CompletedProcess:
    stdin = "".join(f"{path}\n" for path in [*input_paths, output_path])
    return subprocess.run(
        [str(binary)],
        input=stdin,
        text=True,
        capture_output=capture_output,
    )


def cmd_workflow_run(args) -> int:
    try:
        entrypoint, _, manifest = _read_workflow(args.workflow)
        names = _workflow_input_names(manifest)
        input_paths = _workflow_inputs(args.input, names, manifest["schema_version"])
        output_path = _validate_workflow_output(input_paths, args.output, args.force)
        rust, linemap, srcmap, uses_json = compile_source(str(entrypoint))
        binary = cargo_build(entrypoint, rust, linemap, srcmap, release=False, uses_json=uses_json)
    except OSError as exc:
        print(f"workflow error: {exc}", file=sys.stderr)
        return 1
    except ParleyError as exc:
        return _fail(exc, None)

    proc = _run_workflow_binary(binary, input_paths, output_path)
    return proc.returncode if proc.returncode >= 0 else 1


def _workflow_fixture(root: Path, raw_path: object, label: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise OSError(f"{label} must be a relative file path")
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts:
        raise OSError(f"{label} must stay inside the workflow")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise OSError(f"{label} must stay inside the workflow")
    if not resolved.is_file():
        raise OSError(f"{label} does not exist: {raw_path}")
    return resolved


def cmd_workflow_test(args) -> int:
    try:
        entrypoint, root, manifest = _read_workflow(args.workflow)
        names = _workflow_input_names(manifest)
        if manifest.get("schema_version") != 2:
            raise OSError("workflow tests require a schema-2 workflow.json")
        tests = manifest.get("tests")
        if not isinstance(tests, list) or not tests:
            raise OSError("workflow.json needs at least one test fixture")
        rust, linemap, srcmap, uses_json = compile_source(str(entrypoint))
        binary = cargo_build(entrypoint, rust, linemap, srcmap, release=False, uses_json=uses_json)
    except OSError as exc:
        print(f"workflow error: {exc}", file=sys.stderr)
        return 1
    except ParleyError as exc:
        return _fail(exc, None)

    failures = 0
    print(f"Testing workflow {manifest.get('name', root.name)}")
    with tempfile.TemporaryDirectory(prefix="parley-workflow-test-") as tmp:
        for index, case in enumerate(tests, start=1):
            try:
                if not isinstance(case, dict):
                    raise OSError("workflow test fixtures must be objects")
                case_name = case.get("name")
                if not isinstance(case_name, str) or not case_name.strip():
                    raise OSError(f"test fixture {index} needs a name")
                raw_inputs = case.get("inputs")
                if not isinstance(raw_inputs, dict):
                    raise OSError(f"test fixture '{case_name}' needs an inputs object")
                unknown = sorted(set(raw_inputs) - set(names))
                missing = [name for name in names if name not in raw_inputs]
                if unknown:
                    raise OSError(
                        f"test fixture '{case_name}' has unknown inputs: {', '.join(unknown)}")
                if missing:
                    raise OSError(
                        f"test fixture '{case_name}' is missing inputs: {', '.join(missing)}")
                input_paths = [
                    _workflow_fixture(
                        root,
                        raw_inputs[name],
                        f"test fixture '{case_name}' input '{name}'",
                    )
                    for name in names
                ]
                expected = _workflow_fixture(
                    root,
                    case.get("expected_output"),
                    f"test fixture '{case_name}' expected_output",
                )
                output = Path(tmp) / f"case-{index}.out"
                proc = _run_workflow_binary(binary, input_paths, output, capture_output=True)
                if proc.returncode != 0:
                    failures += 1
                    print(f"FAIL {case_name}: workflow exited with {proc.returncode}")
                    if proc.stderr:
                        print(proc.stderr.rstrip())
                    continue
                actual_bytes = output.read_bytes() if output.is_file() else b""
                expected_bytes = expected.read_bytes()
                if actual_bytes != expected_bytes:
                    failures += 1
                    print(f"FAIL {case_name}: output differs")
                    expected_text = expected_bytes.decode(
                        "utf-8", errors="replace").splitlines(keepends=True)
                    actual_text = actual_bytes.decode(
                        "utf-8", errors="replace").splitlines(keepends=True)
                    diff = difflib.unified_diff(
                        expected_text,
                        actual_text,
                        fromfile=case.get("expected_output", "expected"),
                        tofile="actual",
                    )
                    sys.stdout.writelines(diff)
                    continue
                print(f"PASS {case_name}")
            except OSError as exc:
                failures += 1
                print(f"FAIL fixture {index}: {exc}")

    total = len(tests)
    if failures:
        print(f"{failures} of {total} workflow fixtures failed", file=sys.stderr)
        return 1
    print(f"All {total} workflow fixtures passed.")
    return 0


def _workflow_lock_path() -> Path:
    return Path(WORKFLOW_LOCK_FILE)


def _read_workflow_lock() -> dict:
    path = _workflow_lock_path()
    if not path.exists():
        return {"schema_version": 1, "workflows": {}}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise OSError(f"invalid {WORKFLOW_LOCK_FILE}: {exc.msg}") from exc
    if data.get("schema_version") != 1 or not isinstance(data.get("workflows"), dict):
        raise OSError(
            f"{WORKFLOW_LOCK_FILE} must use schema_version 1 with a workflows object")
    return data


def _write_workflow_lock(data: dict) -> None:
    _workflow_lock_path().write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _catalog_workflow_path(name: str) -> Path:
    if name not in WORKFLOW_CATALOG:
        raise OSError(
            f"'{name}' is not in the first-party catalog; provide a local source path")
    return Path(str(resources.files("parley.workflows.catalog").joinpath(name)))


def _validate_workflow_product(source: Path, expected_name: str) -> tuple[dict, str]:
    if not source.is_dir():
        raise OSError(f"workflow source must be a directory: {source}")
    entrypoint, root, manifest = _read_workflow(str(source))
    if manifest.get("schema_version") != 2:
        raise OSError("installable workflows must use schema_version 2")
    name = manifest.get("name")
    if name != expected_name:
        raise OSError(
            f"workflow manifest name is '{name}', expected '{expected_name}'")
    version = manifest.get("version")
    if not isinstance(version, str):
        raise OSError("installable workflows need a semantic version")
    _validate_package_version(version, context="workflow ")
    description = manifest.get("description")
    if not isinstance(description, str) or not description.strip():
        raise OSError("installable workflows need a description")
    names = _workflow_input_names(manifest)
    tests = manifest.get("tests")
    if not isinstance(tests, list) or not tests:
        raise OSError("installable workflows need at least one test fixture")
    for index, case in enumerate(tests, start=1):
        if not isinstance(case, dict):
            raise OSError(f"workflow test fixture {index} must be an object")
        case_name = case.get("name")
        if not isinstance(case_name, str) or not case_name.strip():
            raise OSError(f"workflow test fixture {index} needs a name")
        raw_inputs = case.get("inputs")
        if not isinstance(raw_inputs, dict):
            raise OSError(f"test fixture '{case_name}' needs an inputs object")
        if set(raw_inputs) != set(names):
            raise OSError(
                f"test fixture '{case_name}' inputs must exactly match the manifest")
        for input_name in names:
            _workflow_fixture(
                root,
                raw_inputs[input_name],
                f"test fixture '{case_name}' input '{input_name}'",
            )
        _workflow_fixture(
            root,
            case.get("expected_output"),
            f"test fixture '{case_name}' expected_output",
        )
    try:
        rust, _, _, _ = compile_source(str(entrypoint))
    except ParleyError as exc:
        diag = exc.diagnostics[0]
        raise OSError(
            f"workflow source does not check: {diag.code} {diag.message}") from exc
    if not rust:
        raise OSError("workflow source did not compile")
    return manifest, _package_sha256(source)


def _install_workflow_tree(source: Path, target: Path, force: bool) -> None:
    if source.resolve() == target.resolve():
        raise OSError("workflow source and install target must be different directories")
    if target.exists() and not force:
        raise OSError(f"workflow is already installed: {target}; pass --force to replace it")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
            prefix=".parley-workflow-install-", dir=target.parent) as tmp:
        staging = Path(tmp) / "staging"
        shutil.copytree(source, staging)
        backup = Path(tmp) / "previous"
        if target.exists():
            target.rename(backup)
        try:
            staging.rename(target)
        except OSError:
            if backup.exists() and not target.exists():
                backup.rename(target)
            raise


def cmd_workflow_install(args) -> int:
    try:
        _validate_package_name(args.name)
        source = Path(args.source).resolve() if args.source else _catalog_workflow_path(args.name)
        manifest, sha256 = _validate_workflow_product(source, args.name)
        target = Path("parley_workflows") / args.name
        _install_workflow_tree(source, target, args.force)
        installed_sha256 = _package_sha256(target)
        if installed_sha256 != sha256:
            raise OSError(f"installed workflow checksum mismatch for {args.name}")
        lock = _read_workflow_lock()
        lock["workflows"][args.name] = {
            "version": manifest["version"],
            "source": args.source or f"catalog:{args.name}",
            "path": target.as_posix(),
            "sha256": sha256,
        }
        _write_workflow_lock(lock)
    except OSError as exc:
        print(f"workflow error: {exc}", file=sys.stderr)
        return 1
    print(
        f"Installed workflow {args.name} {manifest['version']} to {target.as_posix()}\n"
        f"Test it: parley workflow test {args.name}")
    return 0


def cmd_workflow_verify(args) -> int:
    try:
        lock = _read_workflow_lock()
        failures: list[str] = []
        for name, metadata in sorted(lock["workflows"].items()):
            if not isinstance(metadata, dict):
                failures.append(f"{name}: invalid lock metadata")
                continue
            target = Path("parley_workflows") / name
            if metadata.get("path") != target.as_posix():
                failures.append(f"{name}: lock path must be {target.as_posix()}")
                continue
            expected = metadata.get("sha256")
            if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
                failures.append(f"{name}: invalid sha256 in {WORKFLOW_LOCK_FILE}")
                continue
            if not target.is_dir():
                failures.append(f"{name}: installed directory is missing")
                continue
            actual = _package_sha256(target)
            if actual != expected:
                failures.append(
                    f"{name}: checksum mismatch; expected {expected}, got {actual}")
                continue
            print(f"OK {name} {metadata.get('version', '')} {actual}")
        if failures:
            for failure in failures:
                print(f"workflow error: {failure}", file=sys.stderr)
            return 1
    except OSError as exc:
        print(f"workflow error: {exc}", file=sys.stderr)
        return 1
    print(f"Verified {len(lock['workflows'])} installed workflows.")
    return 0


def _doctor_checks() -> list[dict]:
    checks = [
        {
            "name": "parley",
            "ok": True,
            "detail": f"parley {__version__}",
            "hint": "",
        },
        {
            "name": "python",
            "ok": True,
            "detail": ".".join(map(str, sys.version_info[:3])),
            "hint": "",
        },
    ]

    cargo = shutil.which("cargo")
    if cargo is None:
        checks.append({
            "name": "cargo",
            "ok": False,
            "detail": "not found",
            "hint": "Install Rust from https://rustup.rs, then run parley doctor again.",
        })
    else:
        try:
            proc = subprocess.run(
                ["cargo", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            cargo_ok = proc.returncode == 0
            detail = proc.stdout.strip() or cargo
        except (OSError, subprocess.SubprocessError) as exc:
            cargo_ok = False
            detail = str(exc)
        checks.append({
            "name": "cargo",
            "ok": cargo_ok,
            "detail": detail,
            "hint": "" if cargo_ok else "Check that cargo runs from this shell.",
        })

    stdlib_root = resources.files("parley.stdlib.std")
    stdlib = sorted(
        f"std/{path.name[:-4]}"
        for path in stdlib_root.iterdir()
        if path.name.endswith(".par")
    )
    required_stdlib = ["std/math", "std/text", "std/list", "std/map",
                       "std/time", "std/workflow"]
    missing = [name for name in required_stdlib if name not in stdlib]
    checks.append({
        "name": "stdlib",
        "ok": not missing,
        "detail": ", ".join(stdlib),
        "hint": "" if not missing else f"Missing bundled packages: {', '.join(missing)}.",
    })

    lock = _lock_path()
    module_root = Path("parley_modules")
    if lock.exists():
        detail = f"{lock.as_posix()} present"
    elif module_root.exists():
        detail = f"{module_root.as_posix()} present; no lockfile yet"
    else:
        detail = "no local packages installed yet"
    checks.append({
        "name": "packages",
        "ok": True,
        "detail": detail,
        "hint": "",
    })
    return checks


def cmd_doctor(args) -> int:
    checks = _doctor_checks()
    ok = all(check["ok"] for check in checks)
    if args.json:
        print(json.dumps({"ok": ok, "version": __version__, "checks": checks}, indent=2))
        return 0 if ok else 1

    print("Parley doctor")
    for check in checks:
        status = "OK" if check["ok"] else "MISSING"
        print(f"{status} {check['name']}: {check['detail']}")
        if check["hint"]:
            print(f"  hint: {check['hint']}")
    print("Parley is ready." if ok else "Parley is not ready yet.")
    return 0 if ok else 1


def _data_error(message: str, *, as_json: bool = False) -> int:
    if as_json:
        print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    else:
        print(f"data error: {message}", file=sys.stderr)
    return 1


def _data_output_path(raw_path: str, input_path: Path, *, force: bool) -> Path | None:
    if raw_path == "-":
        return None
    path = Path(raw_path).resolve()
    if path == input_path.resolve() or (
        path.exists() and input_path.exists() and os.path.samefile(path, input_path)
    ):
        raise AgentDataError("input and output must be different files")
    if not path.parent.is_dir():
        raise AgentDataError(f"output directory does not exist: {path.parent}")
    if path.exists() and not path.is_file():
        raise AgentDataError(f"output path is not a file: {raw_path}")
    if path.exists() and not force:
        raise AgentDataError(f"output already exists: {raw_path}; pass --force to replace it")
    return path


def _write_data_text(path: Path | None, content: str) -> bytes:
    encoded = (content + "\n").encode("utf-8")
    if path is None:
        sys.stdout.buffer.write(encoded)
    else:
        path.write_bytes(encoded)
    return encoded


def cmd_data_compare(args) -> int:
    input_path = Path(args.input)
    try:
        value, raw = load_json_file(input_path)
        report = compare_value(value, tokenizer=args.tokenizer, source_bytes=raw)
    except AgentDataError as exc:
        return _data_error(str(exc), as_json=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_data_pack(args) -> int:
    input_path = Path(args.input)
    try:
        value, raw = load_json_file(input_path)
        report = compare_value(value, tokenizer=args.tokenizer, source_bytes=raw)
        content = packed_text(value, report, args.format)
        output_path = _data_output_path(args.output, input_path, force=args.force)
        if args.report:
            report_path = _data_output_path(args.report, input_path, force=args.force)
            if report_path is None:
                raise AgentDataError("the measurement report must be written to a file")
            if output_path is not None and output_path == report_path:
                raise AgentDataError("packed output and measurement report must be different files")
        else:
            report_path = None
        delivered_format = report["selected_format"] if args.format == "auto" else args.format
        output_bytes = (content + "\n").encode("utf-8")
        report.update({
            "requested_format": args.format,
            "delivered_format": delivered_format,
            "output_sha256": hashlib.sha256(output_bytes).hexdigest(),
        })
        _write_data_text(output_path, content)
        if report_path is not None:
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    except (AgentDataError, OSError) as exc:
        return _data_error(str(exc))
    if output_path is not None:
        print(
            f"Packed {args.input} as {delivered_format} -> {output_path.as_posix()} "
            f"({report['savings']['tokens']} measured tokens saved)."
        )
    return 0


def _decode_packed(source: str, *, with_format: bool = False):
    """Read whichever representation `pack` delivered.

    Automatic packing falls back to compact JSON for nested, mixed, or
    unhelpful shapes, so unpack and check must accept their own output. No
    TOON document the encoder emits parses as JSON, so JSON is tried first.
    """
    try:
        value = load_json_text(source)
        delivered = "json"
    except AgentDataError:
        value = toon_decode(source)
        delivered = "toon"
    return (value, delivered) if with_format else value


def cmd_data_unpack(args) -> int:
    input_path = Path(args.input)
    try:
        try:
            source = input_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise AgentDataError(f"could not read UTF-8 TOON from {input_path}: {exc}") from exc
        value = _decode_packed(source)
        content = pretty_json(value).rstrip("\n") if args.pretty else compact_json(value)
        output_path = _data_output_path(args.output, input_path, force=args.force)
        _write_data_text(output_path, content)
    except (AgentDataError, OSError) as exc:
        return _data_error(str(exc))
    if output_path is not None:
        print(f"Unpacked {args.input} as JSON -> {output_path.as_posix()}.")
    return 0


def cmd_data_check(args) -> int:
    input_path = Path(args.input)
    try:
        try:
            source = input_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise AgentDataError(f"could not read UTF-8 TOON from {input_path}: {exc}") from exc
        value, delivered = _decode_packed(source, with_format=True)
        canonical = packed_text(value, {"selected_format": delivered}, delivered)
        details = {
            "ok": True,
            "format": delivered,
            "profile": "parley-safe-subset-v1",
            "canonical": source.rstrip("\n") == canonical,
            "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        }
    except (AgentDataError, OSError) as exc:
        return _data_error(str(exc), as_json=args.json)
    if args.json:
        print(json.dumps(details, ensure_ascii=False, indent=2))
    else:
        status = "canonical" if details["canonical"] else "valid but non-canonical"
        shape = "TOON" if details["format"] == "toon" else "JSON"
        print(f"✓ {args.input}: valid {details['profile']} {shape} ({status}).")
    return 0


def _lock_path() -> Path:
    return Path(LOCK_FILE)


def _read_lock() -> dict:
    path = _lock_path()
    if not path.exists():
        return {"schema_version": 1, "packages": {}}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        data = {}
    if data.get("schema_version") != 1 or not isinstance(data.get("packages"), dict):
        return {"schema_version": 1, "packages": {}}
    return data


def _write_lock(data: dict) -> None:
    _lock_path().write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _validate_package_name(name: str) -> None:
    if not PACKAGE_NAME_RE.fullmatch(name):
        raise OSError(
            "package names may only contain letters, numbers, dashes, underscores, and dots")


def _validate_package_version(version: str, context: str = "") -> None:
    if not PACKAGE_VERSION_RE.fullmatch(version):
        raise OSError(
            f"{context}package versions must use semantic version form X.Y.Z")


def _is_url(value: str) -> bool:
    return urlparse(value).scheme in {"http", "https", "file"}


def _read_registry(path_or_url: str | None) -> tuple[dict, str]:
    source = path_or_url or os.environ.get("PARLEY_REGISTRY") or DEFAULT_REGISTRY
    try:
        if _is_url(source):
            with urlopen(source, timeout=30) as response:
                raw = response.read().decode("utf-8")
            base = source
        else:
            path = Path(source)
            raw = path.read_text(encoding="utf-8")
            base = str(path.resolve().parent)
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise OSError(f"cannot read package registry {source}: {exc}") from exc
    if data.get("schema_version") != 1 or not isinstance(data.get("packages"), dict):
        raise OSError("package registry must use schema_version 1 with a packages object")
    return data, base


def _registry_entry(registry: dict, name: str) -> dict:
    entry = registry["packages"].get(name)
    if not isinstance(entry, dict):
        raise OSError(f"package '{name}' is not in the registry")
    if not entry.get("source"):
        raise OSError(f"package '{name}' registry entry is missing source")
    return entry


def _entry_sha256(entry: dict) -> str | None:
    value = entry.get("sha256")
    if value is None:
        return None
    digest = str(value).strip()
    if not SHA256_RE.fullmatch(digest):
        raise OSError("package registry sha256 must be 64 hex characters")
    return digest.lower()


def _resolve_registry_source(source: str, base: str) -> str:
    if _is_url(source):
        return source
    if _is_url(base):
        return urljoin(base, source)
    path = Path(source)
    return str(path if path.is_absolute() else Path(base) / path)


def _update_package_hash(sha, name: str, data: bytes) -> None:
    sha.update(name.encode("utf-8"))
    sha.update(b"\0")
    sha.update(data)


def _package_sha256(source: Path) -> str:
    if source.is_file():
        sha = hashlib.sha256()
        _update_package_hash(sha, "main.par", source.read_bytes())
        return sha.hexdigest()
    if source.is_dir():
        if not (source / "main.par").is_file():
            raise OSError("package directories need a main.par file")
        sha = hashlib.sha256()
        files = sorted(p for p in source.rglob("*") if p.is_file())
        for path in files:
            _update_package_hash(
                sha,
                path.relative_to(source).as_posix(),
                path.read_bytes(),
            )
        return sha.hexdigest()
    raise OSError(f"package source does not exist: {source}")


def _package_parley_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if source.is_dir():
        return sorted(p for p in source.rglob("*.par") if p.is_file())
    raise OSError(f"package source does not exist: {source}")


def _review_package_parley_files(source: Path) -> list[str]:
    files = _package_parley_files(source)
    if not files:
        raise OSError("package sources need at least one .par file")
    reviewed: list[str] = []
    root = source if source.is_dir() else source.parent
    for path in files:
        label = path.relative_to(root).as_posix()
        try:
            parse_program(path)
        except ParleyError as exc:
            diag = exc.diagnostics[0]
            location = label
            if diag.line:
                location = f"{location}:{diag.line}"
                if diag.col:
                    location = f"{location}:{diag.col}"
            raise OSError(f"{location}: {diag.code} {diag.message}") from exc
        reviewed.append(label)
    return reviewed


def _validate_submission_metadata(description: str, license_name: str, maintainer: str) -> None:
    missing = [
        field for field, value in (
            ("description", description),
            ("license", license_name),
            ("maintainer", maintainer),
        )
        if not str(value or "").strip()
    ]
    if missing:
        raise OSError("package submissions need " + ", ".join(missing))


def _signature_payload(name: str, entry: dict) -> bytes:
    payload = {"name": name}
    for field in ("version", "source", "description", "license", "maintainer", "sha256", "signing_key"):
        payload[field] = str(entry.get(field) or "")
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign_registry_entry(name: str, entry: dict, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), _signature_payload(name, entry), hashlib.sha256)
    return f"hmac-sha256:{digest.hexdigest()}"


def _maybe_sign_registry_entry(args, name: str, entry: dict) -> None:
    signing_key = getattr(args, "signing_key", None)
    signing_secret = getattr(args, "signing_secret", None)
    if bool(signing_key) != bool(signing_secret):
        raise OSError("package signing needs both --signing-key and --signing-secret")
    if not signing_key:
        return
    entry["signing_key"] = signing_key
    entry["signature"] = _sign_registry_entry(name, entry, signing_secret)


def _verify_registry_signature(name: str, entry: dict, signing_secret: str | None, required: bool) -> None:
    signature = str(entry.get("signature") or "").strip()
    signing_key = str(entry.get("signing_key") or "").strip()
    if not signature and not signing_key:
        if required:
            raise OSError(f"{name} has no signature")
        return
    if not signature or not signing_key:
        raise OSError(f"{name} signature needs both signature and signing_key")
    if not SIGNATURE_RE.fullmatch(signature):
        raise OSError(f"{name} signature must be hmac-sha256:<64 hex characters>")
    if not signing_secret:
        raise OSError("signature verification needs --signing-secret")
    expected = _sign_registry_entry(name, entry, signing_secret)
    if not hmac.compare_digest(signature.lower(), expected):
        raise OSError(f"signature mismatch for {name}")


def _materialize_package_source(source: str, temp_root: Path | None = None) -> Path:
    parsed = urlparse(source)
    if parsed.scheme == "file":
        return Path(parsed.path).resolve()
    if parsed.scheme in {"http", "https"}:
        if not parsed.path.endswith(".par"):
            raise OSError("remote package sources must point to a .par file")
        if temp_root is None:
            raise OSError("internal error: missing temporary directory for remote package")
        target = temp_root / "main.par"
        with urlopen(source, timeout=60) as response:
            target.write_bytes(response.read())
        return target
    return Path(source).resolve()


def _copy_package_source(source: Path, target: Path) -> None:
    if source.is_dir():
        if not (source / "main.par").is_file():
            raise OSError("package directories need a main.par file")
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
        return
    if source.is_file():
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir(parents=True)
        shutil.copy2(source, target / "main.par")
        return
    raise OSError(f"package source does not exist: {source}")


def cmd_package_install(args) -> int:
    try:
        _validate_package_name(args.name)
        registry_path = None
        expected_sha256 = None
        version = args.version
        source_text = args.source
        if args.registry:
            registry, registry_base = _read_registry(args.registry)
            entry = _registry_entry(registry, args.name)
            registry_path = args.registry
            expected_sha256 = _entry_sha256(entry)
            source_text = source_text or _resolve_registry_source(str(entry["source"]), registry_base)
            version = version or str(entry.get("version") or "0.0.0")
        if not source_text:
            raise OSError("package source is required unless --registry is used")
        version = version or "0.0.0"
        _validate_package_version(str(version))
        target = Path("parley_modules") / args.name
        with tempfile.TemporaryDirectory(prefix="parley-package-") as tmp:
            source = _materialize_package_source(source_text, Path(tmp))
            actual_sha256 = _package_sha256(source)
            if expected_sha256 is not None and actual_sha256 != expected_sha256:
                raise OSError(
                    f"sha256 mismatch for {args.name}: expected {expected_sha256}, got {actual_sha256}")
            _copy_package_source(source, target)
        lock = _read_lock()
        lock["packages"][args.name] = {
            "version": version,
            "source": source_text,
            "path": target.as_posix(),
            "sha256": actual_sha256,
        }
        if registry_path is not None:
            lock["packages"][args.name]["registry"] = registry_path
        _write_lock(lock)
    except OSError as exc:
        print(f"package error: {exc}", file=sys.stderr)
        return 1
    print(f"Installed {args.name} {version} -> {target.as_posix()}")
    return 0


def cmd_package_publish(args) -> int:
    try:
        _validate_package_name(args.name)
        _validate_package_version(args.version)
        source = Path(args.package_source).resolve()
        sha256 = _package_sha256(source)
        source_ref = args.source or (f"packages/{args.name}" if source.is_dir() else source.name)
        entry = {
            "version": args.version,
            "source": source_ref,
            "description": args.description or "",
            "license": args.license,
            "maintainer": args.maintainer,
            "sha256": sha256,
        }
        _maybe_sign_registry_entry(args, args.name, entry)
    except OSError as exc:
        print(f"package error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"name": args.name, "entry": entry}, indent=2, sort_keys=True))
    return 0


def cmd_package_review(args) -> int:
    try:
        _validate_package_name(args.name)
        _validate_package_version(args.version)
        _validate_submission_metadata(args.description, args.license, args.maintainer)
        source = Path(args.package_source).resolve()
        sha256 = _package_sha256(source)
        reviewed_files = _review_package_parley_files(source)
        source_ref = args.source or (f"packages/{args.name}" if source.is_dir() else source.name)
        entry = {
            "version": args.version,
            "source": source_ref,
            "description": args.description,
            "license": args.license,
            "maintainer": args.maintainer,
            "sha256": sha256,
        }
        _maybe_sign_registry_entry(args, args.name, entry)
    except OSError as exc:
        print(f"package error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "ok": True,
        "name": args.name,
        "entry": entry,
        "review": {
            "parley_files": reviewed_files,
            "sha256": sha256,
        },
    }, indent=2, sort_keys=True))
    return 0


def cmd_package_verify(args) -> int:
    packages = _read_lock().get("packages", {})
    if not packages:
        print("No packages installed.")
        return 0

    ok = True
    for name in sorted(packages):
        pkg = packages[name]
        path_text = str(pkg.get("path") or "")
        version = str(pkg.get("version") or "0.0.0")
        digest = str(pkg.get("sha256") or "").strip().lower()
        if not path_text:
            print(f"package error: {name} has no path in {LOCK_FILE}", file=sys.stderr)
            ok = False
            continue
        if not SHA256_RE.fullmatch(digest):
            print(f"package error: {name} has no sha256 in {LOCK_FILE}", file=sys.stderr)
            ok = False
            continue
        try:
            actual = _package_sha256(Path(path_text))
        except OSError as exc:
            print(f"package error: {name}: {exc}", file=sys.stderr)
            ok = False
            continue
        if actual != digest:
            print(
                f"package error: sha256 mismatch for {name}: expected {digest}, got {actual}",
                file=sys.stderr,
            )
            ok = False
            continue
        print(f"OK {name} {version} {path_text}")
    return 0 if ok else 1


def cmd_package_check_registry(args) -> int:
    try:
        registry, registry_base = _read_registry(args.registry)
    except OSError as exc:
        print(f"package error: {exc}", file=sys.stderr)
        return 1

    ok = True
    packages = registry.get("packages", {})
    if not packages:
        print("No packages found.")
        return 0

    with tempfile.TemporaryDirectory(prefix="parley-registry-check-") as tmp:
        temp_root = Path(tmp)
        for name in sorted(packages):
            entry = packages[name]
            try:
                _validate_package_name(name)
                if not isinstance(entry, dict):
                    raise OSError(f"{name} registry entry must be an object")
                missing = [
                    field for field in ("version", "description", "license", "maintainer")
                    if not str(entry.get(field) or "").strip()
                ]
                if missing:
                    raise OSError("; ".join(
                        f"{name} registry entry is missing {field}" for field in missing))
                version = str(entry.get("version") or "").strip()
                _validate_package_version(
                    version,
                    f"{name} version {version} is invalid: ",
                )
                if not entry.get("sha256"):
                    raise OSError(f"{name} has no sha256")
                expected_sha256 = _entry_sha256(entry)
                entry = _registry_entry(registry, name)
                source_text = _resolve_registry_source(str(entry["source"]), registry_base)
                source = _materialize_package_source(source_text, temp_root)
                actual_sha256 = _package_sha256(source)
                if actual_sha256 != expected_sha256:
                    raise OSError(
                        f"sha256 mismatch for {name}: expected {expected_sha256}, got {actual_sha256}")
                _verify_registry_signature(
                    name,
                    entry,
                    args.signing_secret,
                    args.require_signatures,
                )
            except OSError as exc:
                print(f"package error: {exc}", file=sys.stderr)
                ok = False
                continue
            print(f"OK {name} {entry.get('version', '0.0.0')} {entry.get('source')}")
    return 0 if ok else 1


def cmd_package_new(args) -> int:
    try:
        _validate_package_name(args.name)
    except OSError as exc:
        print(f"package error: {exc}", file=sys.stderr)
        return 1
    target = Path(args.name)
    if target.exists():
        print(f"package error: '{args.name}' already exists.", file=sys.stderr)
        return 1
    target.mkdir(parents=True)
    (target / "main.par").write_text(PACKAGE_TEMPLATE.format(name=args.name))
    print(f"Created {target.as_posix()}/main.par")
    return 0


def cmd_package_list(args) -> int:
    packages = _read_lock().get("packages", {})
    if not packages:
        print("No packages installed.")
        return 0
    for name in sorted(packages):
        pkg = packages[name]
        print(f"{name} {pkg.get('version', '0.0.0')} {pkg.get('path', '')}")
    return 0


def cmd_package_search(args) -> int:
    try:
        registry, _ = _read_registry(args.registry)
    except OSError as exc:
        print(f"package error: {exc}", file=sys.stderr)
        return 1
    packages = registry.get("packages", {})
    if not packages:
        print("No packages found.")
        return 0
    query = (args.query or "").lower()
    for name in sorted(packages):
        entry = packages[name]
        if not isinstance(entry, dict):
            continue
        description = str(entry.get("description") or "")
        if query and query not in name.lower() and query not in description.lower():
            continue
        print(f"{name} {entry.get('version', '0.0.0')} {description}".rstrip())
    return 0


def _web_project_error(exc: Exception) -> int:
    print(f"web error: {exc}", file=sys.stderr)
    return 1


def cmd_web_new(args) -> int:
    root = Path(args.name)
    if root.exists():
        return _web_project_error(WebProjectError(f"'{args.name}' already exists"))
    if not PACKAGE_NAME_RE.fullmatch(root.name):
        return _web_project_error(WebProjectError(
            "project names may only contain letters, numbers, dashes, underscores, and dots"))
    root.mkdir(parents=True)
    public = root / "public"
    public.mkdir()
    (root / "main.par").write_text(WEB_NEW_SOURCE.format(name=root.name))
    (public / "index.html").write_text(WEB_NEW_INDEX.format(name=root.name))
    (root / "parley.web.json").write_text(json.dumps({
        "schema_version": 1,
        "name": root.name,
        "entrypoint": "main.par",
        "static_dir": "public",
        "routes": [
            {"method": "GET", "path": "/api/health", "handler": "health_check"},
        ],
        "server": {"host": "127.0.0.1", "port": 8787, "max_body_bytes": 1048576},
    }, indent=2) + "\n")
    print(f"Created typed web project {root}/")
    print(f"Run it with: parley web serve {root}")
    return 0


def _load_checked_web(path: str):
    project = load_project(path)
    web = check_web(project)
    browser = check_browser(project)
    return project, web, browser


def _web_response_contract(route) -> dict:
    control = route.route.response
    if control is None:
        return {"mode": "static", "status": route.route.success_status}
    return {
        "mode": "dynamic",
        "status_field": control.status_field,
        "headers_field": control.headers_field,
        "body_field": control.body_field,
    }


def cmd_web_check(args) -> int:
    try:
        project, web, browser = _load_checked_web(args.project)
    except WebProjectError as exc:
        return _web_project_error(exc)
    except ParleyError as exc:
        return _fail(exc, None, as_json=args.json)
    result = {
        "ok": True,
        "project": project.name,
        "entrypoint": str(project.entrypoint.relative_to(project.root)),
        "routes": [
            {
                "method": route.route.method,
                "path": route.route.path,
                "path_parameters": list(route.route.path_parameters),
                "handler": route.route.handler,
                "request_metadata": route.has_request,
                "query_parameters": route.has_query_parameters,
                "json_body": None if route.body_param is None else str(route.body_param.type),
                "json_response": str(route.function.ret),
                "response": _web_response_contract(route),
            }
            for route in web.routes
        ],
        "browser_exports": [] if browser is None else [
            {
                "name": function.name,
                "parameters": [str(param.type) for param in function.params],
                "returns": str(function.ret),
            }
            for function in browser.exports
        ],
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"✓ {project.name}: typed web contract is valid.")
        for route in result["routes"]:
            request = route["json_body"] or "no JSON body"
            print(
                f"  {route['method']:6} {route['path']:<24} "
                f"{route['handler']} ({request} → {route['json_response']})")
        for export in result["browser_exports"]:
            params = ", ".join(export["parameters"]) or "no parameters"
            print(f"  WASM   {export['name']} ({params} → {export['returns']})")
    return 0


def _wasm_target_ready() -> bool:
    if shutil.which("rustc") is None:
        return False
    proc = subprocess.run(
        ["rustc", "--print", "target-libdir", "--target", "wasm32-unknown-unknown"],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0 and Path(proc.stdout.strip()).is_dir()


def _cargo_web_artifact(
        build_dir: Path,
        cargo_toml: str,
        rust: str,
        linemap: dict[int, int],
        srcmap: SourceMap,
        *,
        release: bool,
        wasm: bool,
) -> Path:
    if shutil.which("cargo") is None:
        raise ParleyError([Diagnostic(
            "P902", "Parley needs Rust to build web projects, and `cargo` was not found.",
            file=srcmap.main_file, line=1,
            hint="Install it from https://rustup.rs, then re-run.")])
    source_dir = build_dir / "src"
    source_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "Cargo.toml").write_text(cargo_toml)
    source_name = "lib.rs" if wasm else "main.rs"
    (source_dir / source_name).write_text(rust)
    command = ["cargo", "build", "--message-format=json", "-q"]
    if release:
        command.append("--release")
    if wasm:
        command.extend(["--target", "wasm32-unknown-unknown"])
    proc = subprocess.run(
        command,
        cwd=build_dir,
        env=_cargo_env(),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        diagnostics = _map_rustc_errors(proc.stdout, linemap, srcmap)
        if diagnostics and all(d.code == "P901" for d in diagnostics):
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            if detail:
                diagnostics[0].hint = detail[-1][:500]
        raise ParleyError(diagnostics)
    profile = "release" if release else "debug"
    if wasm:
        return _target_dir() / "wasm32-unknown-unknown" / profile / "parley_browser.wasm"
    return _target_dir() / profile / "parley_web"


def _web_build_key(project: WebProject) -> str:
    digest = hashlib.sha256(str(project.root).encode()).hexdigest()[:12]
    return f"{project.name}-{digest}"


def _build_web_artifacts(project: WebProject, web, browser, *, release: bool):
    if browser is not None and not _wasm_target_ready():
        raise ParleyError([Diagnostic(
            "P724",
            "This project has browser exports, but Rust's wasm32-unknown-unknown target is not installed.",
            file=browser.srcmap.main_file,
            line=1,
            hint="Install it once with `rustup target add wasm32-unknown-unknown`.",
        )])
    key = _web_build_key(project)
    server_rust, server_linemap = render_server(web)
    server_binary = _cargo_web_artifact(
        Path(".parley-build") / "web" / key / "server",
        (
            WEB_CARGO_TOML_DERIVE
            if program_uses_json(web.program)
            else WEB_CARGO_TOML
        ),
        server_rust,
        server_linemap,
        web.srcmap,
        release=release,
        wasm=False,
    )
    browser_artifacts = None
    if browser is not None:
        wasm_rust, wasm_linemap, javascript, declarations = render_browser(browser)
        wasm_binary = _cargo_web_artifact(
            Path(".parley-build") / "web" / key / "browser",
            WASM_CARGO_TOML,
            wasm_rust,
            wasm_linemap,
            browser.srcmap,
            release=True,
            wasm=True,
        )
        browser_artifacts = wasm_binary, javascript, declarations
    return server_binary, browser_artifacts


def _safe_bundle_target(project: WebProject, raw_output: str | None) -> Path:
    output = (Path(raw_output).resolve() if raw_output
              else (project.root / "dist").resolve())
    forbidden = {Path("/").resolve(), project.root, Path.home().resolve()}
    if output in forbidden or output in project.root.parents:
        raise WebProjectError("the bundle output must be a dedicated directory, not a broad root")
    return output


def _write_web_bundle(project: WebProject, web, browser, server_binary: Path,
                      browser_artifacts, output: Path, *, force: bool) -> None:
    if output.exists():
        if not force:
            raise WebProjectError(f"{output} already exists; use --force to replace that bundle")
        if output.is_dir():
            shutil.rmtree(output)
        else:
            output.unlink()
    output.mkdir(parents=True)
    copied_server = output / "server"
    shutil.copy2(server_binary, copied_server)
    public = output / "public"
    if project.static_dir is not None:
        shutil.copytree(project.static_dir, public)
    else:
        public.mkdir()
    if browser_artifacts is not None:
        wasm_binary, javascript, declarations = browser_artifacts
        shutil.copy2(wasm_binary, public / "parley.wasm")
        (public / "parley.js").write_text(javascript)
        (public / "parley.d.ts").write_text(declarations)
    metadata = {
        "schema_version": 1,
        "parley_version": __version__,
        "project": project.name,
        "server": "server",
        "public": "public",
        "routes": [
            {"method": route.route.method, "path": route.route.path,
             "path_parameters": list(route.route.path_parameters),
             "query_parameters": route.has_query_parameters,
             "handler": route.route.handler,
             "response": _web_response_contract(route)}
            for route in web.routes
        ],
        "browser_exports": [] if browser is None else [
            function.name for function in browser.exports
        ],
    }
    (output / "parley.build.json").write_text(json.dumps(metadata, indent=2) + "\n")


def cmd_web_build(args) -> int:
    try:
        project, web, browser = _load_checked_web(args.project)
        output = _safe_bundle_target(project, args.output)
        server, browser_artifacts = _build_web_artifacts(
            project, web, browser, release=True)
        _write_web_bundle(
            project, web, browser, server, browser_artifacts, output, force=args.force)
    except WebProjectError as exc:
        return _web_project_error(exc)
    except ParleyError as exc:
        return _fail(exc, None)
    print(f"Built {project.name} full-stack bundle at {output}")
    print(f"  native server: {output / 'server'}")
    if browser is not None:
        print(f"  browser module: {output / 'public' / 'parley.wasm'}")
    return 0


def cmd_web_serve(args) -> int:
    try:
        project, web, browser = _load_checked_web(args.project)
        server, browser_artifacts = _build_web_artifacts(
            project, web, browser, release=False)
    except WebProjectError as exc:
        return _web_project_error(exc)
    except ParleyError as exc:
        return _fail(exc, None)
    with tempfile.TemporaryDirectory(prefix=f"parley-web-{project.name}-") as temp:
        bundle = Path(temp) / "bundle"
        _write_web_bundle(
            project, web, browser, server, browser_artifacts, bundle, force=False)
        env = dict(os.environ)
        env["PARLEY_WEB_HOST"] = args.host or project.host
        env["PARLEY_WEB_PORT"] = str(args.port or project.port)
        try:
            proc = subprocess.run([str(bundle / "server")], cwd=bundle, env=env)
        except KeyboardInterrupt:
            return 130
    return proc.returncode if proc.returncode >= 0 else 1


def _load_benchmark_script(name: str):
    path = Path("benchmarks") / f"{name}.py"
    if not path.is_file():
        raise OSError(
            "benchmark harness not found; run this command from a Parley source checkout")
    spec = importlib.util.spec_from_file_location(f"_parley_benchmark_{name}", path)
    if spec is None or spec.loader is None:
        raise OSError(f"could not load benchmark script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cmd_benchmark_measure(args) -> int:
    try:
        module = _load_benchmark_script("measure")
    except OSError as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 1
    return module.main(args.benchmark_args)


def cmd_benchmark_prompt(args) -> int:
    try:
        module = _load_benchmark_script("prompts")
    except OSError as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 1
    return module.main(args.benchmark_args)


def cmd_benchmark_runlog(args) -> int:
    try:
        module = _load_benchmark_script("runlog")
    except OSError as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 1
    return module.main([args.runlog_cmd, *args.benchmark_args])


def main(argv: list[str] | None = None) -> int:
    raw_argv = sys.argv[1:] if argv is None else list(argv)
    if len(raw_argv) >= 2 and raw_argv[0] == "benchmark":
        bench_cmd, bench_args = raw_argv[1], raw_argv[2:]
        if bench_cmd == "measure":
            return cmd_benchmark_measure(argparse.Namespace(benchmark_args=bench_args))
        if bench_cmd == "prompt":
            return cmd_benchmark_prompt(argparse.Namespace(benchmark_args=bench_args))
        if bench_cmd in {"append", "summarize"}:
            return cmd_benchmark_runlog(argparse.Namespace(
                runlog_cmd=bench_cmd,
                benchmark_args=bench_args,
            ))

    ap = argparse.ArgumentParser(
        prog="parley",
        description="Parley — speak plainly, ship native binaries.")
    ap.add_argument("--version", action="version", version=f"parley {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="compile and run a program")
    p.add_argument("file")
    p.add_argument("program_args", nargs=argparse.REMAINDER,
                   metavar="ARG",
                   help="arguments passed through to the program as `the arguments`")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("build", help="build a native binary (release)")
    p.add_argument("file")
    p.add_argument("-o", "--output", help="output binary name")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("check", help="parse and type-check without building")
    p.add_argument("file")
    p.add_argument("--json", action="store_true", help="machine-readable diagnostics")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("rust", help="print the generated Rust source")
    p.add_argument("file")
    p.set_defaults(fn=cmd_rust)

    p = sub.add_parser("explain", help="explain an error code (e.g. P204)")
    p.add_argument("code")
    p.set_defaults(fn=cmd_explain)

    p = sub.add_parser("new", help="create a new Parley program")
    p.add_argument("name")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("doctor", help="verify local Parley setup")
    p.add_argument("--json", action="store_true", help="machine-readable setup report")
    p.set_defaults(fn=cmd_doctor)

    p = sub.add_parser("data", help="pack structured data for AI-agent context")
    data_sub = p.add_subparsers(dest="data_cmd", required=True)
    data_compare = data_sub.add_parser(
        "compare", help="measure compact JSON and safe TOON without writing output")
    data_compare.add_argument("input", help="strict JSON input file")
    data_compare.add_argument(
        "--tokenizer", default="rough", help="rough or a tiktoken encoding name")
    data_compare.set_defaults(fn=cmd_data_compare)
    data_pack = data_sub.add_parser(
        "pack", help="pack JSON as the smallest verified safe encoding")
    data_pack.add_argument("input", help="strict JSON input file")
    data_pack.add_argument(
        "--format", choices=("auto", "json", "toon"), default="auto")
    data_pack.add_argument(
        "--tokenizer", default="rough", help="rough or a tiktoken encoding name")
    data_pack.add_argument("-o", "--output", default="-", help="output file or - for stdout")
    data_pack.add_argument("--report", help="write the measurement and integrity report as JSON")
    data_pack.add_argument(
        "--force", action="store_true", help="replace existing output/report files")
    data_pack.set_defaults(fn=cmd_data_pack)
    data_unpack = data_sub.add_parser(
        "unpack", help="decode strict safe-subset TOON to canonical JSON")
    data_unpack.add_argument("input", help="TOON input file")
    data_unpack.add_argument("-o", "--output", default="-", help="output file or - for stdout")
    data_unpack.add_argument("--pretty", action="store_true", help="indent the JSON output")
    data_unpack.add_argument(
        "--force", action="store_true", help="replace an existing output file")
    data_unpack.set_defaults(fn=cmd_data_unpack)
    data_check = data_sub.add_parser(
        "check", help="validate strict safe-subset TOON and report canonical status")
    data_check.add_argument("input", help="TOON input file")
    data_check.add_argument("--json", action="store_true", help="machine-readable result")
    data_check.set_defaults(fn=cmd_data_check)

    p = sub.add_parser("workflow", help="create and run safe file workflows")
    workflow_sub = p.add_subparsers(dest="workflow_cmd", required=True)
    workflow_list = workflow_sub.add_parser(
        "list", help="list bundled workflow starters")
    workflow_list.set_defaults(fn=cmd_workflow_list)
    workflow_new = workflow_sub.add_parser(
        "new", help="create a workflow from a bundled starter")
    workflow_new.add_argument("name")
    workflow_new.add_argument(
        "--template",
        choices=tuple(WORKFLOW_TEMPLATES),
        default="clean-text",
        help="starter to use (default: clean-text)",
    )
    workflow_new.set_defaults(fn=cmd_workflow_new)
    workflow_run = workflow_sub.add_parser(
        "run", help="compile and safely run a file-to-file workflow")
    workflow_run.add_argument("workflow", help="workflow directory or .par entrypoint")
    workflow_run.add_argument(
        "--input",
        action="append",
        required=True,
        help="existing input file; schema 2 uses NAME=PATH and may repeat",
    )
    workflow_run.add_argument("--output", required=True, help="output file to create")
    workflow_run.add_argument(
        "--force", action="store_true", help="replace an existing output file")
    workflow_run.set_defaults(fn=cmd_workflow_run)
    workflow_test = workflow_sub.add_parser(
        "test", help="run exact-output fixtures declared by a workflow")
    workflow_test.add_argument("workflow", help="schema-2 workflow directory")
    workflow_test.set_defaults(fn=cmd_workflow_test)
    workflow_install = workflow_sub.add_parser(
        "install", help="install a checksummed workflow product")
    workflow_install.add_argument("name", help="workflow product name")
    workflow_install.add_argument(
        "source",
        nargs="?",
        help="local workflow directory (omit for the first-party catalog)",
    )
    workflow_install.add_argument(
        "--force", action="store_true", help="replace an installed workflow")
    workflow_install.set_defaults(fn=cmd_workflow_install)
    workflow_verify = workflow_sub.add_parser(
        "verify", help=f"verify installed workflows against {WORKFLOW_LOCK_FILE}")
    workflow_verify.set_defaults(fn=cmd_workflow_verify)

    p = sub.add_parser("web", help="build typed HTTP/JSON and browser/WASM projects")
    web_sub = p.add_subparsers(dest="web_cmd", required=True)
    web_new = web_sub.add_parser("new", help="create a typed full-stack project")
    web_new.add_argument("name")
    web_new.set_defaults(fn=cmd_web_new)
    web_check = web_sub.add_parser(
        "check", help="verify route, JSON, and browser export contracts")
    web_check.add_argument("project", help="project directory or parley.web.json")
    web_check.add_argument("--json", action="store_true", help="machine-readable contract")
    web_check.set_defaults(fn=cmd_web_check)
    web_build = web_sub.add_parser(
        "build", help="build a native server plus optional browser/WASM bundle")
    web_build.add_argument("project", help="project directory or parley.web.json")
    web_build.add_argument("-o", "--output", help="bundle directory (default: PROJECT/dist)")
    web_build.add_argument(
        "--force", action="store_true", help="replace an existing dedicated bundle directory")
    web_build.set_defaults(fn=cmd_web_build)
    web_serve = web_sub.add_parser("serve", help="build and run a project locally")
    web_serve.add_argument("project", help="project directory or parley.web.json")
    web_serve.add_argument("--host", help="listen host override")
    web_serve.add_argument("--port", type=int, choices=range(1, 65536), help="listen port override")
    web_serve.set_defaults(fn=cmd_web_serve)

    p = sub.add_parser("package", help="manage local Parley packages")
    package_sub = p.add_subparsers(dest="package_cmd", required=True)
    install = package_sub.add_parser("install", help="vendor a local package")
    install.add_argument("name")
    install.add_argument("source", nargs="?")
    install.add_argument("--version")
    install.add_argument("--registry", help="registry manifest JSON path or URL")
    install.set_defaults(fn=cmd_package_install)
    package_publish = package_sub.add_parser(
        "publish", help="print a registry-ready package entry")
    package_publish.add_argument("name")
    package_publish.add_argument("package_source")
    package_publish.add_argument("--version", required=True)
    package_publish.add_argument("--description", default="")
    package_publish.add_argument("--license", required=True)
    package_publish.add_argument("--maintainer", required=True)
    package_publish.add_argument("--source", help="source path or URL to place in the registry entry")
    package_publish.add_argument("--signing-key", help="release signing key id to include in the registry entry")
    package_publish.add_argument("--signing-secret", help="secret used to sign the registry entry")
    package_publish.set_defaults(fn=cmd_package_publish)
    package_review = package_sub.add_parser(
        "review", help="dry-run a package submission before registry publishing")
    package_review.add_argument("name")
    package_review.add_argument("package_source")
    package_review.add_argument("--version", required=True)
    package_review.add_argument("--description", required=True)
    package_review.add_argument("--license", required=True)
    package_review.add_argument("--maintainer", required=True)
    package_review.add_argument("--source", help="source path or URL to place in the registry entry")
    package_review.add_argument("--signing-key", help="release signing key id to include in the registry entry")
    package_review.add_argument("--signing-secret", help="secret used to sign the registry entry")
    package_review.set_defaults(fn=cmd_package_review)
    package_new = package_sub.add_parser("new", help="create a local package skeleton")
    package_new.add_argument("name")
    package_new.set_defaults(fn=cmd_package_new)
    package_list = package_sub.add_parser("list", help="list vendored packages")
    package_list.set_defaults(fn=cmd_package_list)
    package_verify = package_sub.add_parser(
        "verify", help="verify vendored packages against parley.lock.json")
    package_verify.set_defaults(fn=cmd_package_verify)
    package_check_registry = package_sub.add_parser(
        "check-registry", help="validate a registry manifest before publishing")
    package_check_registry.add_argument("registry", nargs="?", help="registry manifest JSON path or URL")
    package_check_registry.add_argument("--require-signatures", action="store_true",
                                        help="require every package entry to carry a valid release signature")
    package_check_registry.add_argument("--signing-secret",
                                        help="secret used to verify package entry signatures")
    package_check_registry.set_defaults(fn=cmd_package_check_registry)
    package_search = package_sub.add_parser("search", help="list packages in a registry")
    package_search.add_argument("query", nargs="?")
    package_search.add_argument("--registry", help="registry manifest JSON path or URL")
    package_search.set_defaults(fn=cmd_package_search)

    p = sub.add_parser("benchmark", help="measure and summarize benchmark research data")
    benchmark_sub = p.add_subparsers(dest="benchmark_cmd", required=True)
    measure = benchmark_sub.add_parser("measure", help="measure the seed benchmark corpus")
    measure.add_argument("benchmark_args", nargs=argparse.REMAINDER)
    measure.set_defaults(fn=cmd_benchmark_measure)
    prompt = benchmark_sub.add_parser("prompt", help="render language-neutral benchmark prompts")
    prompt.add_argument("benchmark_args", nargs=argparse.REMAINDER)
    prompt.set_defaults(fn=cmd_benchmark_prompt)
    append = benchmark_sub.add_parser("append", help="append one benchmark attempt log row")
    append.add_argument("benchmark_args", nargs=argparse.REMAINDER)
    append.set_defaults(fn=cmd_benchmark_runlog, runlog_cmd="append")
    summarize = benchmark_sub.add_parser("summarize", help="summarize a benchmark run log")
    summarize.add_argument("benchmark_args", nargs=argparse.REMAINDER)
    summarize.set_defaults(fn=cmd_benchmark_runlog, runlog_cmd="summarize")

    args = ap.parse_args(raw_argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
