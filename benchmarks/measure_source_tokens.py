"""How many tokens does the same program cost in Parley, Python, and Rust?

Reads every paired corpus in `benchmarks/agent_tasks_*.json` — the same seeded
programs the frozen agent benchmarks use — and tokenizes each language's
implementation of each task. This is a *source* measurement, not a session
measurement: report 030 put most of the Parley/Python session gap in fixed
context, so a change here is not a session claim.

    python3 benchmarks/measure_source_tokens.py             # totals per task
    python3 benchmarks/measure_source_tokens.py --attribute # excess by phrase

Needs `pip install tiktoken` (the `research` extra).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

# Parley phrase -> (pattern, the Python spelling it competes with). Used only
# to rank where the difference lives; the totals above are the real result.
PHRASES = [
    ("let X be", r"\blet\s+\w+\s+be\b", "x ="),
    ("set X to", r"\bset\s+\w+\s+to\b", "x ="),
    ("value of", r"\bvalue\s+of\b", ""),
    ("ask for a number", r"\bask\s+for\s+a\s+number\b", "int(input())"),
    ("give back", r"\bgive\s+back\b", "return"),
    ("to NAME with", r"^to\s+\w+\s+with\b", "def f("),
    ("giving TYPE", r"\bgiving\s+\w+", "-> str"),
    ("as TYPE", r"\bas\s+(number|text|yesno|decimal)\b", ": int"),
    ("for each X in", r"\bfor\s+each\s+\w+\s+in\b", "for x in"),
    ("length of", r"\blength\s+of\b", "len("),
    ("item I of", r"\bitem\s+\w+\s+of\b", "x["),
    ("is more than", r"\bis\s+more\s+than\b", ">"),
    ("is at least", r"\bis\s+at\s+least\b", ">="),
    ("an empty list of T", r"\ban\s+empty\s+list\s+of\s+\w+", "[]"),
    ("include", r'^include\s+"[^"]+"', "from x import y"),
]


def encoder(name: str):
    try:
        import tiktoken
    except ImportError:  # pragma: no cover - depends on the optional extra
        sys.exit("This needs tiktoken: pip install 'parley-lang[research]'")
    enc = tiktoken.get_encoding(name)
    return lambda text: len(enc.encode(text))


def paired_tasks() -> list[dict]:
    """Every corpus task that ships all three implementations."""
    tasks, seen = [], set()
    for path in sorted(REPO.glob("benchmarks/agent_tasks_*.json")):
        try:
            doc = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        for task in doc.get("tasks", []):
            files = task.get("seed_files")
            if not isinstance(files, dict) or not isinstance(files.get("parley"), dict):
                continue
            if task.get("id") in seen:
                continue
            seen.add(task.get("id"))
            tasks.append(task)
    return tasks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokenizer", default="o200k_base")
    ap.add_argument("--attribute", action="store_true",
                    help="rank Parley phrases by how much excess they carry")
    args = ap.parse_args()
    tok = encoder(args.tokenizer)

    tasks = paired_tasks()
    if not tasks:
        return print("no paired corpora found") or 1

    rows = []
    for task in tasks:
        row = {"id": task.get("id", "?")}
        for lang in ("parley", "python", "rust"):
            row[lang] = sum(tok(text) for text in (task["seed_files"].get(lang) or {}).values())
        rows.append(row)

    print(f"{len(rows)} paired tasks, tokenizer {args.tokenizer}\n")
    print(f"{'task':42} {'parley':>8} {'python':>8} {'rust':>8} {'vs python':>11}")
    for row in sorted(rows, key=lambda r: -(r["parley"] - r["python"])):
        delta = row["parley"] - row["python"]
        pct = 100.0 * delta / row["python"] if row["python"] else 0.0
        print(f"{row['id'][:41]:42} {row['parley']:8} {row['python']:8} "
              f"{row['rust']:8} {delta:+6} {pct:+6.1f}%")

    totals = {lang: sum(r[lang] for r in rows) for lang in ("parley", "python", "rust")}
    print(f"\n{'TOTAL':42} {totals['parley']:8} {totals['python']:8} {totals['rust']:8}")
    for lang in ("python", "rust"):
        gap = 100.0 * (totals["parley"] - totals[lang]) / totals[lang]
        print(f"  Parley is {gap:+.1f}% versus {lang}")

    if args.attribute:
        text = "\n".join(t for task in tasks
                         for t in task["seed_files"]["parley"].values())
        print(f"\n--- where the Parley excess lives ---")
        print(f"{'phrase':22} {'count':>6} {'tok':>5} {'py':>4} {'excess':>8}")
        found = []
        for label, pattern, python in PHRASES:
            matches = re.findall(pattern, text, re.M)
            if not matches:
                continue
            sample = re.search(pattern, text, re.M).group(0)
            cost, py_cost = tok(sample), (tok(python) if python else 0)
            found.append((label, len(matches), cost, py_cost,
                          len(matches) * (cost - py_cost)))
        for label, n, cost, py_cost, excess in sorted(found, key=lambda r: -r[4]):
            print(f"{label:22} {n:6} {cost:5} {py_cost:4} {excess:+8}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
