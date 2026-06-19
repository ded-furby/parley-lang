"""The `parley` command-line tool.

  parley run program.par          compile (debug) and run
  parley build program.par -o x   compile (release) to a native binary
  parley check program.par        parse + type-check only (fast agent loop)
  parley check program.par --json machine-readable diagnostics
  parley rust program.par         print the generated Rust
  parley explain P204             explain an error code
  parley new myproject            start a new program
  parley doctor                   verify local setup
  parley package install name src vendor a local package
  parley package publish name src print a registry-ready entry
  parley package verify           verify vendored packages against the lockfile
  parley package check-registry x validate a package registry manifest
  parley benchmark measure        measure the seed research corpus
"""

from __future__ import annotations

import argparse
import hashlib
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

PACKAGE_TEMPLATE = """\
note: {name} package

to package_ready giving yesno:
    give back yes
"""

LOCK_FILE = "parley.lock.json"
PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
DEFAULT_REGISTRY = "parley.registry.json"


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
    required_stdlib = ["std/math", "std/text", "std/list", "std/map"]
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
        source = Path(args.package_source).resolve()
        sha256 = _package_sha256(source)
        source_ref = args.source or (f"packages/{args.name}" if source.is_dir() else source.name)
        entry = {
            "version": args.version,
            "source": source_ref,
            "description": args.description or "",
            "sha256": sha256,
        }
    except OSError as exc:
        print(f"package error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"name": args.name, "entry": entry}, indent=2, sort_keys=True))
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
                if not str(entry.get("version") or "").strip():
                    raise OSError(f"{name} registry entry is missing version")
                if not str(entry.get("description") or "").strip():
                    raise OSError(f"{name} registry entry is missing description")
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
    package_publish.add_argument("--source", help="source path or URL to place in the registry entry")
    package_publish.set_defaults(fn=cmd_package_publish)
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
