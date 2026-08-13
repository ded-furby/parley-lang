#!/usr/bin/env python3
"""Prepare the pinned offline dependency stores for study 046."""

from __future__ import annotations

import argparse
import hashlib
import io
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile


REPO = Path(__file__).resolve().parents[1]
BENCH = REPO / "benchmarks/fullstack_035"
RUST_BENCH = REPO / "benchmarks/fullstack_046/rust"
SOURCE_COMMIT = "6bae1149d101d5a483f31f55905083e0a939c1da"
SOURCE_TREE = "525b23b0191cb5f16a9cc4b5281d9b9af912898c"
PARLEY_VERSION = "parley 0.5.6"
LARK_VERSION = "1.3.1"


def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha256(root: Path) -> str:
    checksum = hashlib.sha256()
    for path in sorted(
        candidate
        for candidate in root.rglob("*")
        if candidate.is_file()
        and "__pycache__" not in candidate.parts
        and candidate.suffix != ".pyc"
    ):
        checksum.update(path.relative_to(root).as_posix().encode())
        checksum.update(b"\0")
        checksum.update(path.read_bytes())
        checksum.update(b"\0")
    return checksum.hexdigest()


def command_version(command: list[str], *, cwd: Path = REPO) -> str:
    completed = run(command, cwd=cwd)
    return (completed.stdout or completed.stderr).strip().splitlines()[-1]


def isolated_root(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink: {path}")
    resolved = path.resolve()
    home = Path.home().resolve()
    if (
        resolved in {Path("/"), home, REPO}
        or REPO.is_relative_to(resolved)
        or resolved.is_relative_to(REPO)
        or not resolved.name.startswith("parley-fullstack-046-")
    ):
        raise ValueError(
            f"{label} must be a dedicated parley-fullstack-046-* root outside the repository: "
            f"{resolved}"
        )
    if resolved.exists() and not resolved.is_dir():
        raise ValueError(f"{label} is not a directory: {resolved}")
    return resolved


def browser_provenance() -> dict[str, str]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path).resolve()
        browser = playwright.chromium.launch(headless=True)
        version = browser.version
        browser.close()
    return {
        "browser": "playwright chromium",
        "browser_version": version,
        "browser_executable": str(executable),
        "browser_executable_sha256": sha256(executable),
    }


def prepare_frozen_parley(source_root: Path, parley_root: Path) -> dict[str, str]:
    archive = subprocess.run(
        ["git", "archive", "--format=tar", SOURCE_COMMIT],
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout
    if source_root.exists():
        shutil.rmtree(source_root)
    source_root.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
        bundle.extractall(source_root, filter="data")
    source_tree_sha256 = tree_sha256(source_root)

    actual_tree = command_version(["git", "show", "-s", "--format=%T", SOURCE_COMMIT])
    if actual_tree != SOURCE_TREE:
        raise RuntimeError(f"frozen source tree mismatch: {actual_tree} != {SOURCE_TREE}")
    run([sys.executable, "-m", "venv", "--clear", str(parley_root)], cwd=REPO)
    python = parley_root / "bin/python"
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            f"lark=={LARK_VERSION}",
            str(source_root),
        ],
        cwd=REPO,
    )
    for generated in (source_root / "build", source_root / "parley_lang.egg-info"):
        if generated.exists():
            shutil.rmtree(generated)
    executable = parley_root / "bin/parley"
    reported_version = command_version([str(executable), "--version"], cwd=parley_root)
    if reported_version != PARLEY_VERSION:
        raise RuntimeError(
            f"frozen Parley version mismatch: {reported_version!r} != {PARLEY_VERSION!r}"
        )
    freeze = run([str(python), "-m", "pip", "freeze", "--all"], cwd=REPO).stdout
    package_root = Path(
        run(
            [
                str(python),
                "-c",
                "from pathlib import Path; import parley; print(Path(parley.__file__).parent)",
            ],
            cwd=parley_root,
        ).stdout.strip()
    ).resolve()
    if not package_root.is_relative_to(parley_root):
        raise RuntimeError(f"Parley imported outside its frozen environment: {package_root}")
    site_packages_root = Path(
        run(
            [
                str(python),
                "-c",
                "import site; print(site.getsitepackages()[0])",
            ],
            cwd=REPO,
        ).stdout.strip()
    ).resolve()
    if tree_sha256(source_root) != source_tree_sha256:
        raise RuntimeError("frozen source checkout changed while building Parley")
    return {
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "source_archive_sha256": hashlib.sha256(archive).hexdigest(),
        "source_tree_sha256": source_tree_sha256,
        "source_root": str(source_root.resolve()),
        "parley_root": str(parley_root.resolve()),
        "executable": str(executable.resolve()),
        "executable_sha256": sha256(executable),
        "reported_version": reported_version,
        "package_root": str(package_root),
        "package_tree_sha256": tree_sha256(package_root),
        "site_packages_root": str(site_packages_root),
        "site_packages_tree_sha256": tree_sha256(site_packages_root),
        "python": command_version([str(python), "--version"]),
        "lark_version": LARK_VERSION,
        "pip_freeze": freeze,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--parley-root",
        type=Path,
        default=Path(os.environ.get("FULLSTACK_046_PARLEY_ROOT", "/private/tmp/parley-fullstack-046-parley")),
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(os.environ.get("FULLSTACK_046_SOURCE_ROOT", "/private/tmp/parley-fullstack-046-source")),
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        default=Path(os.environ.get("FULLSTACK_046_PROVENANCE", "/private/tmp/parley-fullstack-046-provenance.json")),
    )
    parser.add_argument(
        "--python-root",
        type=Path,
        default=Path(os.environ.get("FULLSTACK_046_PYTHON_ROOT", "/private/tmp/parley-fullstack-046-python")),
    )
    parser.add_argument(
        "--typescript-root",
        type=Path,
        default=Path(os.environ.get("FULLSTACK_046_TYPESCRIPT", "/private/tmp/parley-fullstack-046-typescript")),
    )
    args = parser.parse_args(argv)

    args.parley_root = isolated_root(args.parley_root, "Parley environment")
    args.source_root = isolated_root(args.source_root, "Parley source")
    args.python_root = isolated_root(args.python_root, "Python environment")
    args.typescript_root = isolated_root(args.typescript_root, "TypeScript environment")
    if len({args.parley_root, args.source_root, args.python_root, args.typescript_root}) != 4:
        raise ValueError("preparation roots must be distinct")

    parley = prepare_frozen_parley(args.source_root, args.parley_root)

    run([sys.executable, "-m", "venv", "--clear", str(args.python_root)], cwd=REPO)
    run(
        [
            str(args.python_root / "bin/python"),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-r",
            str(BENCH / "python/requirements.lock.txt"),
        ],
        cwd=REPO,
    )

    args.typescript_root.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        shutil.copy2(BENCH / "typescript" / name, args.typescript_root / name)
    run(["npm", "ci", "--ignore-scripts"], cwd=args.typescript_root)

    run(["rustup", "target", "add", "wasm32-unknown-unknown"], cwd=REPO)
    lock_text = (RUST_BENCH / "Cargo.lock").read_text(encoding="utf-8")
    if 'name = "fullstack-agent-046"' not in lock_text or 'name = "release-radar-035"' in lock_text:
        raise RuntimeError("046 Rust lockfile root package does not match its manifest")
    run(
        [
            "cargo",
            "fetch",
            "--locked",
            "--manifest-path",
            str(RUST_BENCH / "Cargo.toml"),
        ],
        cwd=REPO,
    )
    run([sys.executable, "-m", "playwright", "install", "chromium"], cwd=REPO)
    browser = browser_provenance()
    python_freeze = run(
        [str(args.python_root / "bin/python"), "-m", "pip", "freeze", "--all"],
        cwd=REPO,
    ).stdout
    python_site_packages = Path(
        run(
            [
                str(args.python_root / "bin/python"),
                "-c",
                "import site; print(site.getsitepackages()[0])",
            ],
            cwd=REPO,
        ).stdout.strip()
    ).resolve()
    npm_tree = run(["npm", "ls", "--all", "--json"], cwd=args.typescript_root).stdout

    result = {
        "schema_version": 1,
        "experiment_id": "046",
        "parley": parley,
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "host_python": platform.python_version(),
            "host_python_executable": str(Path(sys.executable).resolve()),
            "host_python_executable_sha256": sha256(Path(sys.executable).resolve()),
            "python_environment_root": str(args.python_root),
            "python_runtime": str(args.python_root / "bin/python"),
            "python_runtime_target": str((args.python_root / "bin/python").resolve()),
            "python_runtime_version": command_version([str(args.python_root / "bin/python"), "--version"]),
            "python_runtime_executable_sha256": sha256((args.python_root / "bin/python").resolve()),
            "python_pip_freeze": python_freeze,
            "python_site_packages": str(python_site_packages),
            "python_site_packages_tree_sha256": tree_sha256(python_site_packages),
            "python_requirements_lock_sha256": sha256(BENCH / "python/requirements.lock.txt"),
            "typescript_modules": str((args.typescript_root / "node_modules").resolve()),
            "typescript_version": command_version([str(args.typescript_root / "node_modules/.bin/tsc"), "--version"]),
            "typescript_compiler_sha256": sha256((args.typescript_root / "node_modules/.bin/tsc").resolve()),
            "typescript_npm_tree_sha256": hashlib.sha256(npm_tree.encode()).hexdigest(),
            "typescript_modules_tree_sha256": tree_sha256(
                args.typescript_root / "node_modules"
            ),
            "typescript_lock_sha256": sha256(BENCH / "typescript/package-lock.json"),
            "node_version": command_version(["node", "--version"]),
            "npm_version": command_version(["npm", "--version"]),
            "rustc_version": command_version(["rustc", "--version"]),
            "cargo_version": command_version(["cargo", "--version"]),
            "rust_manifest_sha256": sha256(RUST_BENCH / "Cargo.toml"),
            "rust_lock_sha256": sha256(RUST_BENCH / "Cargo.lock"),
            "rust_target": "wasm32-unknown-unknown",
            "playwright_version": importlib.metadata.version("playwright"),
            **browser,
        },
    }
    args.provenance.parent.mkdir(parents=True, exist_ok=True)
    args.provenance.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**result, "provenance": str(args.provenance.resolve())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
