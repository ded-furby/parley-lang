#!/usr/bin/env python3
"""Prepare the pinned offline dependency stores for study 036."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
BENCH = REPO / "benchmarks/fullstack_035"


def run(command: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, text=True)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--python-root",
        type=Path,
        default=Path(os.environ.get("FULLSTACK_036_PYTHON_ROOT", "/private/tmp/parley-fullstack-036-python")),
    )
    parser.add_argument(
        "--typescript-root",
        type=Path,
        default=Path(os.environ.get("FULLSTACK_036_TYPESCRIPT", "/private/tmp/parley-fullstack-036-typescript")),
    )
    args = parser.parse_args(argv)

    if not (args.python_root / "bin/python").is_file():
        run([sys.executable, "-m", "venv", str(args.python_root)], cwd=REPO)
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
    run(
        [
            "cargo",
            "fetch",
            "--locked",
            "--manifest-path",
            str(BENCH / "rust/Cargo.toml"),
        ],
        cwd=REPO,
    )
    run([sys.executable, "-m", "playwright", "install", "chromium"], cwd=REPO)

    result = {
        "python": str(args.python_root / "bin/python"),
        "typescript": str(args.typescript_root / "node_modules"),
        "rust_target": "wasm32-unknown-unknown",
        "browser": "playwright chromium",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
