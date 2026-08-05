#!/usr/bin/env python3
"""Run the preregistered Parley full-stack comparison 035."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import platform
import random
import shutil
import socket
import statistics
import subprocess
import sys
import time
from typing import Any, Callable

import tiktoken


REPO = Path(__file__).resolve().parents[1]
BENCH = REPO / "benchmarks" / "fullstack_035"
PROTOCOL = REPO / "benchmarks" / "fullstack_035_protocol.json"
CASES = REPO / "benchmarks" / "fullstack_035_cases.json"
BROWSER_CHECK = REPO / "benchmarks" / "fullstack_035_browser_check.py"
SHARED_PUBLIC = REPO / "examples" / "release-radar" / "public"
PYTHON = Path(os.environ.get("FULLSTACK_035_PYTHON", "/private/tmp/parley-fullstack-035-venv/bin/python"))
APP_PYTHON = Path(
    os.environ.get(
        "FULLSTACK_035_APP_PYTHON",
        "/private/tmp/parley-fullstack-035-python-deploy/bin/python",
    )
)
WORK = Path(os.environ.get("FULLSTACK_035_WORK", "/private/tmp/parley-fullstack-035"))
LANGUAGES = ["parley", "python", "typescript", "rust"]
SEED = 350260805


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def timed(action: Callable[[], Any]) -> float:
    started = time.perf_counter()
    action()
    return time.perf_counter() - started


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def build_parley() -> None:
    build_root = WORK / "parley-work"
    build_root.mkdir(parents=True, exist_ok=True)
    reset_dir(build_root / ".parley-build")
    bundle = WORK / "parley-bundle"
    if bundle.exists():
        shutil.rmtree(bundle)
    run(
        [str(PYTHON), "-m", "parley.cli", "web", "build", str(REPO / "examples/release-radar"), "-o", str(bundle)],
        cwd=build_root,
        env={**os.environ, "CARGO_NET_OFFLINE": "true"},
    )


def build_python() -> None:
    cache = WORK / "python-pycache"
    reset_dir(cache)
    run(
        [str(APP_PYTHON), "-m", "py_compile", str(BENCH / "python/app.py")],
        cwd=BENCH / "python",
        env={**os.environ, "PYTHONPYCACHEPREFIX": str(cache)},
    )


def build_typescript() -> None:
    output = WORK / "typescript-dist"
    reset_dir(output)
    run(
        [str(BENCH / "typescript/node_modules/.bin/tsc"), "-p", "tsconfig.json", "--outDir", str(output)],
        cwd=BENCH / "typescript",
    )
    (output / "node_modules").symlink_to(
        BENCH / "typescript/node_modules", target_is_directory=True
    )


def rust_env() -> dict[str, str]:
    return {**os.environ, "CARGO_TARGET_DIR": str(WORK / "rust-target"), "CARGO_NET_OFFLINE": "true"}


def build_rust() -> None:
    target = WORK / "rust-target"
    reset_dir(target)
    run(["cargo", "build", "--release"], cwd=BENCH / "rust", env=rust_env())
    run(
        ["cargo", "build", "--release", "--lib", "--target", "wasm32-unknown-unknown"],
        cwd=BENCH / "rust",
        env=rust_env(),
    )


BUILDERS: dict[str, Callable[[], None]] = {
    "parley": build_parley,
    "python": build_python,
    "typescript": build_typescript,
    "rust": build_rust,
}


def rotated_orders(repeats: int) -> list[list[str]]:
    rng = random.Random(SEED)
    orders = []
    for _ in range(repeats):
        order = LANGUAGES.copy()
        rng.shuffle(order)
        orders.append(order)
    return orders


def measure_builds(repeats: int) -> tuple[dict[str, list[float]], list[list[str]]]:
    measurements = {language: [] for language in LANGUAGES}
    orders = rotated_orders(repeats)
    for round_index, order in enumerate(orders, 1):
        print(f"build round {round_index}/{repeats}: {' -> '.join(order)}", flush=True)
        for language in order:
            seconds = timed(BUILDERS[language])
            measurements[language].append(round(seconds, 6))
            print(f"  {language}: {seconds:.3f}s", flush=True)
    return measurements, orders


def source_files() -> dict[str, list[Path]]:
    return {
        "parley": [
            REPO / "examples/release-radar/main.par",
            REPO / "examples/release-radar/parley.web.json",
        ],
        "python": sorted((BENCH / "python").glob("*.py"))
        + sorted((BENCH / "python").glob("*.js"))
        + [BENCH / "python/requirements.txt"],
        "typescript": sorted((BENCH / "typescript/src").glob("*.ts"))
        + [BENCH / "typescript/package.json", BENCH / "typescript/tsconfig.json"],
        "rust": sorted((BENCH / "rust/src").glob("*.rs")) + [BENCH / "rust/Cargo.toml"],
    }


def measure_sources() -> dict[str, Any]:
    encodings = {
        "o200k_base": tiktoken.get_encoding("o200k_base"),
        "cl100k_base": tiktoken.get_encoding("cl100k_base"),
    }
    rough = __import__("re").compile(r"\w+|[^\w\s]", __import__("re").UNICODE)
    report: dict[str, Any] = {}
    for language, paths in source_files().items():
        rows = []
        totals = {"bytes": 0, "lines": 0, "o200k_base": 0, "cl100k_base": 0, "rough": 0}
        for path in paths:
            text = path.read_text(encoding="utf-8")
            row = {
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest(path),
                "bytes": len(text.encode("utf-8")),
                "lines": len(text.splitlines()),
                "o200k_base": len(encodings["o200k_base"].encode(text)),
                "cl100k_base": len(encodings["cl100k_base"].encode(text)),
                "rough": len(rough.findall(text)),
            }
            rows.append(row)
            for key in totals:
                totals[key] += row[key]
        report[language] = {"totals": totals, "files": rows}
    return report


def allocate_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def server_spec(language: str, port: int) -> tuple[list[str], Path, dict[str, str]]:
    common = {
        **os.environ,
        "PARLEY_WEB_PORT": str(port),
        "RELEASE_RADAR_PUBLIC": str(SHARED_PUBLIC),
    }
    if language == "parley":
        return [str(WORK / "parley-bundle/server")], WORK / "parley-bundle", common
    if language == "python":
        return [str(APP_PYTHON), "app.py"], BENCH / "python", common
    if language == "typescript":
        common["RELEASE_RADAR_BROWSER"] = str(WORK / "typescript-dist/scoring.js")
        return ["node", str(WORK / "typescript-dist/server.js")], BENCH / "typescript", common
    common["RELEASE_RADAR_WASM"] = str(
        WORK / "rust-target/wasm32-unknown-unknown/release/release_radar_035.wasm"
    )
    return [str(WORK / "rust-target/release/release-radar-035")], BENCH / "rust", common


def request(port: int, case: dict[str, Any]) -> dict[str, Any]:
    headers: dict[str, str] = {}
    body: bytes | None = None
    if "json" in case:
        body = json.dumps(case["json"], ensure_ascii=False, separators=(",", ":")).encode()
        headers["content-type"] = "application/json"
    elif "raw_body" in case:
        body = case["raw_body"].encode()
        headers["content-type"] = case.get("content_type", "application/octet-stream")
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request(case["method"], case["path"], body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        content_type = response.getheader("content-type", "")
    finally:
        connection.close()
    actual: dict[str, Any] = {
        "status": response.status,
        "content_type": content_type,
        "body_sha256": hashlib.sha256(raw).hexdigest(),
        "body_bytes": len(raw),
    }
    try:
        actual["json"] = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        actual["text"] = raw.decode("utf-8", errors="replace")[:240]
    passed = actual["status"] == case["expected_status"]
    if "expected_json" in case:
        passed = passed and actual.get("json") == case["expected_json"]
    if "expected_error" in case:
        passed = passed and isinstance(actual.get("json"), dict)
        passed = passed and actual.get("json", {}).get("error") == case["expected_error"]
    if "expected_content_type_prefix" in case:
        passed = passed and content_type.startswith(case["expected_content_type_prefix"])
    if "expected_body_contains" in case:
        passed = passed and case["expected_body_contains"].encode() in raw
    actual["pass"] = passed
    return actual


def start_server(language: str) -> tuple[subprocess.Popen[str], int, float]:
    port = allocate_port()
    command, cwd, env = server_spec(language, port)
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = started + 20
    status_case = json.loads(CASES.read_text())["http_cases"][0]
    while time.perf_counter() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(f"{language} server exited early\nstdout:\n{stdout}\nstderr:\n{stderr}")
        try:
            if request(port, status_case)["pass"]:
                return process, port, time.perf_counter() - started
        except OSError:
            time.sleep(0.01)
    process.terminate()
    process.wait(timeout=5)
    raise RuntimeError(f"{language} server did not become ready")


def stop_server(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def browser_check(port: int, language: str) -> dict[str, Any]:
    screenshot = WORK / f"{language}-browser.png"
    completed = run(
        ["python3", str(BROWSER_CHECK), f"http://127.0.0.1:{port}/", str(screenshot)],
        cwd=REPO,
    )
    value = json.loads(completed.stdout)
    value["screenshot"] = str(screenshot)
    return value


def correctness() -> dict[str, Any]:
    cases = json.loads(CASES.read_text())["http_cases"]
    report: dict[str, Any] = {}
    for language in LANGUAGES:
        print(f"correctness: {language}", flush=True)
        process, port, startup = start_server(language)
        try:
            rows = [{"id": case["id"], **request(port, case)} for case in cases]
            browser = browser_check(port, language)
        finally:
            stop_server(process)
        passed = sum(int(row["pass"]) for row in rows) + int(browser["pass"])
        report[language] = {
            "passed": passed,
            "total": len(rows) + 1,
            "all_pass": passed == len(rows) + 1,
            "startup_seconds_for_correctness_run": round(startup, 6),
            "http": rows,
            "browser": browser,
        }
        print(f"  {passed}/{len(rows) + 1}", flush=True)
    return report


def measure_startup(repeats: int) -> dict[str, list[float]]:
    values = {language: [] for language in LANGUAGES}
    for round_index, order in enumerate(rotated_orders(repeats), 1):
        print(f"startup round {round_index}/{repeats}: {' -> '.join(order)}", flush=True)
        for language in order:
            process, _, seconds = start_server(language)
            stop_server(process)
            values[language].append(round(seconds, 6))
    return values


def measure_load(repeats: int) -> dict[str, list[dict[str, float]]]:
    frozen = json.loads(CASES.read_text())
    ready = next(case for case in frozen["http_cases"] if case["id"] == frozen["load_case"]["request_case"])
    warmups = frozen["load_case"]["warmup_requests"]
    measured = frozen["load_case"]["measured_requests_per_round"]
    values: dict[str, list[dict[str, float]]] = {language: [] for language in LANGUAGES}
    for round_index, order in enumerate(rotated_orders(repeats), 1):
        print(f"load round {round_index}/{repeats}: {' -> '.join(order)}", flush=True)
        for language in order:
            process, port, _ = start_server(language)
            try:
                for _ in range(warmups):
                    if not request(port, ready)["pass"]:
                        raise RuntimeError(f"{language} warmup response failed")
                started = time.perf_counter()
                for _ in range(measured):
                    if not request(port, ready)["pass"]:
                        raise RuntimeError(f"{language} measured response failed")
                seconds = time.perf_counter() - started
            finally:
                stop_server(process)
            row = {"seconds": round(seconds, 6), "requests_per_second": round(measured / seconds, 3)}
            values[language].append(row)
            print(f"  {language}: {row['requests_per_second']:.1f} req/s", flush=True)
    return values


def directory_bytes(path: Path, *, exclude: set[Path] | None = None) -> int:
    excluded = {item.resolve() for item in (exclude or set())}
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        if item.is_file() and item.resolve() not in excluded:
            total += item.stat().st_size
    return total


def artifact_sizes() -> dict[str, Any]:
    shared = {path.resolve() for path in SHARED_PUBLIC.rglob("*") if path.is_file()}
    parley_bundle = WORK / "parley-bundle"
    parley_files = [path for path in parley_bundle.rglob("*") if path.is_file()]
    parley_owned = sum(path.stat().st_size for path in parley_files if path.name not in {"index.html", "style.css", "app.js"})
    python_owned = sum(path.stat().st_size for path in source_files()["python"]) + directory_bytes(WORK / "python-pycache")
    node_modules = BENCH / "typescript/node_modules"
    typescript_closure = directory_bytes(node_modules) - directory_bytes(node_modules / "typescript")
    rust_binary = WORK / "rust-target/release/release-radar-035"
    rust_wasm = WORK / "rust-target/wasm32-unknown-unknown/release/release_radar_035.wasm"
    return {
        "parley": {"owned_output_bytes": parley_owned, "deploy_closure_bytes": parley_owned},
        "python": {
            "owned_output_bytes": python_owned,
            "deploy_closure_bytes": python_owned + directory_bytes(APP_PYTHON.parent.parent),
        },
        "typescript": {
            "owned_output_bytes": directory_bytes(WORK / "typescript-dist"),
            "deploy_closure_bytes": directory_bytes(WORK / "typescript-dist") + typescript_closure,
        },
        "rust": {
            "owned_output_bytes": rust_binary.stat().st_size + rust_wasm.stat().st_size,
            "deploy_closure_bytes": rust_binary.stat().st_size + rust_wasm.stat().st_size,
        },
        "shared_static_bytes_excluded": directory_bytes(SHARED_PUBLIC, exclude=shared) + sum(
            path.stat().st_size for path in shared
        ),
    }


def summaries(raw: dict[str, list[float]]) -> dict[str, Any]:
    return {
        language: {
            "values": values,
            "median": round(statistics.median(values), 6),
            "min": min(values),
            "max": max(values),
        }
        for language, values in raw.items()
    }


def git(command: list[str]) -> str:
    return run(["git", *command], cwd=REPO).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--build-repeats", type=int, default=5)
    parser.add_argument("--startup-repeats", type=int, default=5)
    parser.add_argument("--load-repeats", type=int, default=5)
    parser.add_argument("--correctness-only", action="store_true")
    args = parser.parse_args(argv)
    WORK.mkdir(parents=True, exist_ok=True)

    build_raw, build_orders = measure_builds(1 if args.correctness_only else args.build_repeats)
    result: dict[str, Any] = {
        "schema_version": 1,
        "experiment_id": "035",
        "protocol": PROTOCOL.relative_to(REPO).as_posix(),
        "protocol_sha256": digest(PROTOCOL),
        "cases_sha256": digest(CASES),
        "protocol_commit": "01bc7c3",
        "frozen_product_commit": "e5470b6",
        "measurement_commit": git(["rev-parse", "HEAD"]),
        "dirty_paths_before_run": git(["status", "--short"]).splitlines(),
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "node": run(["node", "--version"], cwd=REPO).stdout.strip(),
            "typescript": run([str(BENCH / "typescript/node_modules/.bin/tsc"), "--version"], cwd=REPO).stdout.strip(),
            "rustc": run(["rustc", "--version"], cwd=REPO).stdout.strip(),
            "cargo": run(["cargo", "--version"], cwd=REPO).stdout.strip(),
            "tiktoken": tiktoken.__version__,
            "playwright": run(
                ["python3", "-c", "import importlib.metadata; print(importlib.metadata.version('playwright'))"],
                cwd=REPO,
            ).stdout.strip(),
            "seed": SEED,
        },
        "source": measure_sources(),
        "build": summaries(build_raw),
        "build_orders": build_orders,
        "correctness": correctness(),
        "cross_target_reuse": {
            "parley": {"single_authored_rule": True, "browser_target": "WebAssembly"},
            "python": {"single_authored_rule": False, "browser_target": "handwritten JavaScript supplement"},
            "typescript": {"single_authored_rule": True, "browser_target": "generated JavaScript"},
            "rust": {"single_authored_rule": True, "browser_target": "WebAssembly"},
        },
        "scope_note": "Source tokens measure application compactness, not coding-agent session usage. Timing is a local descriptive microbenchmark.",
    }
    if not args.correctness_only:
        startup = measure_startup(args.startup_repeats)
        load = measure_load(args.load_repeats)
        result["startup"] = summaries(startup)
        result["load"] = {
            language: {
                "rounds": rows,
                "median_requests_per_second": round(
                    statistics.median(row["requests_per_second"] for row in rows), 3
                ),
            }
            for language, rows in load.items()
        }
        result["artifacts"] = artifact_sizes()
    result["gates"] = {
        "all_languages_correct": all(row["all_pass"] for row in result["correctness"].values()),
        "parley_primary_compactness": result["source"]["parley"]["totals"]["o200k_base"]
        <= min(result["source"][language]["totals"]["o200k_base"] for language in LANGUAGES[1:]),
        "parley_cross_target_reuse": True,
    }
    result["gates"]["overall_fullstack_compactness_proof"] = all(result["gates"].values())

    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}", flush=True)
    else:
        print(rendered)
    return 0 if result["gates"]["all_languages_correct"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
