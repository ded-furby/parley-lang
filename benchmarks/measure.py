#!/usr/bin/env python3
"""Measure the Parley seed benchmark corpus.

This is a Phase 1 harness for repository readiness. It records source-size
metrics and, by default, verifies each Parley task with `parley check --json`.
Use `--llm-tokenizer cl100k_base` after installing the `research` extra for
model-token counts. The `rough_tokens` value remains a stable regex fallback
for comparisons inside this repo.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
TASKS_FILE = Path(__file__).with_name("tasks.json")
DEFAULT_OUTPUT = Path(__file__).with_name("results") / "parley_seed_metrics.json"
LANGUAGE_EXTENSIONS = {
    "parley": ".par",
    "python": ".py",
    "rust": ".rs",
}

ROUGH_TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_']*|\d+\.\d+|\d+|==|!=|<=|>=|[^\s]",
    re.ASCII,
)
WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_']*|\d+(?:\.\d+)?", re.ASCII)


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def load_tasks(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("tasks.json must use schema_version 1")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks.json must contain a non-empty tasks list")

    seen: set[str] = set()
    for task in tasks:
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("each task needs a non-empty string id")
        if task_id in seen:
            raise ValueError(f"duplicate task id: {task_id}")
        seen.add(task_id)

        source = task.get("source")
        if not isinstance(source, str) or not source:
            raise ValueError(f"{task_id}: source must be a non-empty string")
        if not (REPO / source).is_file():
            raise ValueError(f"{task_id}: source does not exist: {source}")

    return data


def parse_languages(value: str) -> list[str]:
    languages = [part.strip() for part in value.split(",") if part.strip()]
    if not languages:
        raise ValueError("--languages must include at least one language")
    unknown = [lang for lang in languages if lang not in LANGUAGE_EXTENSIONS]
    if unknown:
        known = ", ".join(sorted(LANGUAGE_EXTENSIONS))
        raise ValueError(f"unknown language(s): {', '.join(unknown)}; known: {known}")
    return languages


def source_for(task: dict[str, Any], language: str) -> Path:
    if language == "parley":
        return REPO / task["source"]
    return REPO / "benchmarks" / language / f"{task['id']}{LANGUAGE_EXTENSIONS[language]}"


def load_llm_tokenizer(name: str | None) -> tuple[str | None, Callable[[str], int] | None]:
    if not name:
        return None, None
    try:
        import tiktoken  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ValueError(
            "LLM tokenizer counts need tiktoken. Install it with "
            "`python3 -m pip install -e \".[research]\"`."
        ) from exc
    encoding = tiktoken.get_encoding(name)
    return f"tiktoken:{name}", lambda text: len(encoding.encode(text))


def source_metrics(
    path: Path,
    llm_token_counter: Callable[[str], int] | None = None,
) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    metrics = {
        "bytes": len(text.encode("utf-8")),
        "chars": len(text),
        "lines": len(lines),
        "nonblank_lines": sum(1 for line in lines if line.strip()),
        "words": len(WORD_RE.findall(text)),
        "rough_tokens": len(ROUGH_TOKEN_RE.findall(text)),
    }
    if llm_token_counter is not None:
        metrics["llm_tokens"] = llm_token_counter(text)
    return metrics


def run_check(path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "parley.cli", "check", str(path), "--json"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=60,
    )
    elapsed = round(time.perf_counter() - started, 4)

    payload: dict[str, Any]
    try:
        loaded = json.loads(proc.stdout)
        payload = loaded if isinstance(loaded, dict) else {}
    except json.JSONDecodeError:
        payload = {}

    diagnostics = payload.get("diagnostics", [])
    if not isinstance(diagnostics, list):
        diagnostics = []

    return {
        "ok": proc.returncode == 0 and payload.get("ok") is True,
        "returncode": proc.returncode,
        "elapsed_seconds": elapsed,
        "diagnostics_count": len(diagnostics),
        "codes": sorted(
            {
                str(d.get("code"))
                for d in diagnostics
                if isinstance(d, dict) and d.get("code")
            }
        ),
        "stdout_bytes": len(proc.stdout.encode("utf-8")),
        "stderr_bytes": len(proc.stderr.encode("utf-8")),
    }


def build_report(
    tasks_data: dict[str, Any],
    include_check: bool,
    languages: list[str],
    llm_tokenizer: str | None = None,
    llm_token_counter: Callable[[str], int] | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for task in tasks_data["tasks"]:
        sources = {lang: source_for(task, lang) for lang in languages}
        missing = [rel(path) for path in sources.values() if not path.is_file()]
        if missing:
            raise ValueError(f"{task['id']}: missing source(s): {', '.join(missing)}")

        row = {
            "id": task["id"],
            "title": task["title"],
            "sources": {lang: rel(path) for lang, path in sources.items()},
            "interactive": bool(task.get("interactive", False)),
            "deterministic_run": bool(task.get("deterministic_run", False)),
            "features": list(task.get("features", [])),
            "metrics": {
                lang: source_metrics(path, llm_token_counter)
                for lang, path in sources.items()
            },
            "checks": {},
        }
        if "parley" in sources:
            if include_check:
                row["checks"]["parley"] = run_check(sources["parley"])
            else:
                row["checks"]["parley"] = {"skipped": True}
        rows.append(row)

    by_language = {}
    for lang in languages:
        totals_for_language = {
            "tasks": len(rows),
            "bytes": sum(row["metrics"][lang]["bytes"] for row in rows),
            "lines": sum(row["metrics"][lang]["lines"] for row in rows),
            "nonblank_lines": sum(row["metrics"][lang]["nonblank_lines"] for row in rows),
            "rough_tokens": sum(row["metrics"][lang]["rough_tokens"] for row in rows),
        }
        if llm_token_counter is not None:
            totals_for_language["llm_tokens"] = sum(
                row["metrics"][lang]["llm_tokens"] for row in rows
            )
        by_language[lang] = totals_for_language

    totals = {
        "tasks": len(rows),
        "languages": languages,
        "by_language": by_language,
        "checked_ok": (
            sum(
                1
                for row in rows
                if row.get("checks", {}).get("parley", {}).get("ok") is True
            )
            if include_check and "parley" in languages
            else 0
        ),
    }

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "language_version": tasks_data.get("language_version"),
        "method": {
            "source_metrics": "UTF-8 bytes, characters, lines, nonblank lines, words, and regex rough_tokens.",
            "rough_tokens": "Regex token count for stable repo-local tracking, not an LLM tokenizer.",
            "check": "Runs `python -m parley.cli check <source> --json` for Parley sources unless --no-check is used.",
        },
        "tasks": rows,
        "totals": totals,
    }
    if llm_tokenizer is not None:
        report["method"]["llm_tokenizer"] = llm_tokenizer
    return report


def print_table(report: dict[str, Any]) -> None:
    print("id               lang    lines  rough_tokens  check  source")
    print("---------------  ------  -----  ------------  -----  -----------------------------")
    for row in report["tasks"]:
        for index, lang in enumerate(report["totals"]["languages"]):
            check_data = row.get("checks", {}).get(lang)
            if check_data is None:
                check = "-"
            elif check_data.get("skipped"):
                check = "skip"
            else:
                check = "ok" if check_data.get("ok") else "fail"
            print(
                f"{row['id'] if index == 0 else '':<15}  "
                f"{lang:<6}  "
                f"{row['metrics'][lang]['lines']:>5}  "
                f"{row['metrics'][lang]['rough_tokens']:>12}  "
                f"{check:<5}  "
                f"{row['sources'][lang]}"
            )
    print("---------------  ------  -----  ------------  -----  -----------------------------")
    for lang, totals in report["totals"]["by_language"].items():
        check = (
            f"{report['totals']['checked_ok']}/{report['totals']['tasks']}"
            if lang == "parley"
            else "-"
        )
        print(
            f"{'total':<15}  "
            f"{lang:<6}  "
            f"{totals['lines']:>5}  "
            f"{totals['rough_tokens']:>12}  "
            f"{check:<5}  "
            "benchmark corpus"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure the Parley seed benchmark corpus.")
    parser.add_argument("--tasks", type=Path, default=TASKS_FILE, help="benchmark task manifest")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON report path")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="stdout format")
    parser.add_argument(
        "--languages",
        default="parley,python,rust",
        help="comma-separated languages to measure: parley, python, rust",
    )
    parser.add_argument(
        "--llm-tokenizer",
        help="optional tiktoken encoding name, e.g. cl100k_base, for LLM-token counts",
    )
    parser.add_argument("--no-check", action="store_true", help="skip parley check --json verification")
    args = parser.parse_args(argv)

    try:
        languages = parse_languages(args.languages)
        llm_tokenizer, llm_token_counter = load_llm_tokenizer(args.llm_tokenizer)
        tasks_data = load_tasks(args.tasks)
        report = build_report(
            tasks_data,
            include_check=not args.no_check,
            languages=languages,
            llm_tokenizer=llm_tokenizer,
            llm_token_counter=llm_token_counter,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print_table(report)
        print(f"\nWrote {rel(args.output) if args.output.resolve().is_relative_to(REPO) else args.output}")

    if (
        "parley" in report["totals"]["languages"]
        and not args.no_check
        and report["totals"]["checked_ok"] != report["totals"]["tasks"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
