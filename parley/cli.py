"""The `parley` command-line tool.

  parley run program.par          compile (debug) and run
  parley build program.par -o x   compile (release) to a native binary
  parley check program.par        parse + type-check only (fast agent loop)
  parley check program.par --json machine-readable diagnostics
  parley rust program.par         print the generated Rust
  parley explain P204             explain an error code
  parley new myproject            start a new program
  parley package install name src vendor a local package
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .checker import check_program
from .diagnostics import Diagnostic, ParleyError, explain, render_human, render_json
from .emit_rust import emit_program
from .parser import SourceMap, parse_program

CARGO_TOML = """\
[package]
name = "parley_program"
version = "0.1.0"
edition = "2021"

[profile.release]
strip = true
"""

NEW_TEMPLATE = """\
note: {name} — written in Parley

to main:
    say "Hello from {name}!"
    let numbers be a list of 3, 1, 4, 1, 5
    say "the sum is {{sum of numbers}}"
"""

LOCK_FILE = "parley.lock.json"
PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


# ------------------------------------------------------------------ pipeline

def compile_source(path: str):
    """parse → check → emit. Returns (rust, linemap, srcmap); raises ParleyError
    with file-resolved diagnostics on any failure."""
    program, srcmap = parse_program(path)
    diags = check_program(program)
    if diags:
        raise ParleyError(srcmap.resolve(diags))
    rust, linemap = emit_program(program)
    return rust, linemap, srcmap


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
                release: bool) -> Path:
    """Build the generated Rust; returns the binary path. Raises ParleyError."""
    if shutil.which("cargo") is None:
        raise ParleyError([Diagnostic(
            "P902", "Parley needs Rust to build native binaries, and `cargo` was not found.",
            file=srcmap.main_file, line=1,
            hint="Install it from https://rustup.rs (one command), then re-run.")])
    d = _build_dir(path)
    (d / "Cargo.toml").write_text(CARGO_TOML)
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
        rust, linemap, srcmap = compile_source(args.file)
        binary = cargo_build(path, rust, linemap, srcmap, release=False)
    except ParleyError as e:
        return _fail(e, None)
    proc = subprocess.run([str(binary)])
    return proc.returncode if proc.returncode >= 0 else 1

def cmd_build(args) -> int:
    path = Path(args.file)
    try:
        rust, linemap, srcmap = compile_source(args.file)
        binary = cargo_build(path, rust, linemap, srcmap, release=True)
    except ParleyError as e:
        return _fail(e, None)
    out = Path(args.output or path.stem)
    shutil.copy2(binary, out)
    print(f"Built ./{out} ({out.stat().st_size // 1024} KiB)")
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
        rust, _, _ = compile_source(args.file)
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
        source = Path(args.source).resolve()
        target = Path("parley_modules") / args.name
        _copy_package_source(source, target)
        lock = _read_lock()
        lock["packages"][args.name] = {
            "version": args.version,
            "source": str(source),
            "path": target.as_posix(),
        }
        _write_lock(lock)
    except OSError as exc:
        print(f"package error: {exc}", file=sys.stderr)
        return 1
    print(f"Installed {args.name} {args.version} -> {target.as_posix()}")
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="parley",
        description="Parley — speak plainly, ship native binaries.")
    ap.add_argument("--version", action="version", version=f"parley {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="compile and run a program")
    p.add_argument("file")
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

    p = sub.add_parser("package", help="manage local Parley packages")
    package_sub = p.add_subparsers(dest="package_cmd", required=True)
    install = package_sub.add_parser("install", help="vendor a local package")
    install.add_argument("name")
    install.add_argument("source")
    install.add_argument("--version", default="0.0.0")
    install.set_defaults(fn=cmd_package_install)
    package_list = package_sub.add_parser("list", help="list vendored packages")
    package_list.set_defaults(fn=cmd_package_list)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
