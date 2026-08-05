#!/usr/bin/env python3
"""Build iteration 032's independent deeper-project confirmation corpus."""

from __future__ import annotations

import json
from pathlib import Path


BENCHMARKS = Path(__file__).resolve().parent
OUTPUT = BENCHMARKS / "agent_tasks_deep_confirmation_032.json"
FIXES = BENCHMARKS / "deep_reference_fixes_032.json"
LANGUAGES = ("parley", "python", "rust")


def symmetric_context(issue: str, flow: str, regression: str) -> dict:
    files = {
        "ISSUE.md": issue,
        "architecture/flow.md": flow,
        "tests/regression.txt": regression,
    }
    return {language: dict(files) for language in LANGUAGES}


def quoted_env_task() -> tuple[dict, dict]:
    parley_bug = '''include "std/text"

to normalize_env with token as text giving text:
    if token starts with "sq:":
        give back (without_prefix with token, "sq:")
    if token starts with "dq:":
        give back token
    if token is "empty":
        give back ""
    give back (without_prefix with token, "raw:")
'''
    parley_fix = parley_bug.replace(
        'if token starts with "dq:":\n        give back token',
        'if token starts with "dq:":\n        give back (without_prefix with token, "dq:")',
    )
    python_bug = '''def normalize_env(token: str) -> str:
    if token.startswith("sq:"):
        return token.removeprefix("sq:")
    if token.startswith("dq:"):
        return token
    if token == "empty":
        return ""
    return token.removeprefix("raw:")
'''
    python_fix = python_bug.replace(
        'if token.startswith("dq:"):\n        return token',
        'if token.startswith("dq:"):\n        return token.removeprefix("dq:")',
    )
    rust_bug = '''pub fn normalize_env(token: &str) -> String {
    if let Some(value) = token.strip_prefix("sq:") { return value.to_string(); }
    if token.starts_with("dq:") { return token.to_string(); }
    if token == "empty" { return String::new(); }
    token.strip_prefix("raw:").unwrap_or(token).to_string()
}
'''
    rust_fix = rust_bug.replace(
        'if token.starts_with("dq:") { return token.to_string(); }',
        'if let Some(value) = token.strip_prefix("dq:") { return value.to_string(); }',
    )
    seed_files = {
        "parley": {
            "normalization.par": parley_bug,
            "classification.par": '''to env_kind with token as text giving text:
    if token starts with "dq:" or token starts with "sq:":
        give back "quoted"
    if token is "empty":
        give back "empty"
    give back "raw"
''',
            "validation.par": '''to env_supported with token as text giving yesno:
    give back token is "empty" or token starts with "dq:" or token starts with "sq:" or token starts with "raw:"
''',
            "formatting.par": '''to format_env with key as text, value as text, kind as text giving text:
    give back "key=" + key + "|value=" + value + "|kind=" + kind
''',
            "main.par": '''include "normalization.par"
include "classification.par"
include "validation.par"
include "formatting.par"

to main:
    let count_input be ask for a number ""
    let count be value of count_input
    repeat count times:
        let parts be (ask "") split by "|"
        let key be item 1 of parts
        let token be item 2 of parts
        if (env_supported with token) is no:
            fail "unsupported environment token"
        say (format_env with key, (normalize_env with token), (env_kind with token))
''',
        },
        "python": {
            "normalization.py": python_bug,
            "classification.py": '''def env_kind(token: str) -> str:
    if token.startswith(("dq:", "sq:")):
        return "quoted"
    if token == "empty":
        return "empty"
    return "raw"
''',
            "validation.py": '''def env_supported(token: str) -> bool:
    return token == "empty" or token.startswith(("dq:", "sq:", "raw:"))
''',
            "formatting.py": '''def format_env(key: str, value: str, kind: str) -> str:
    return f"key={key}|value={value}|kind={kind}"
''',
            "main.py": '''from classification import env_kind
from formatting import format_env
from normalization import normalize_env
from validation import env_supported

count = int(input())
for _ in range(count):
    key, token = input().split("|", 1)
    if not env_supported(token):
        raise ValueError("unsupported environment token")
    print(format_env(key, normalize_env(token), env_kind(token)))
''',
        },
        "rust": {
            "normalization.rs": rust_bug,
            "classification.rs": '''pub fn env_kind(token: &str) -> &'static str {
    if token.starts_with("dq:") || token.starts_with("sq:") { return "quoted"; }
    if token == "empty" { return "empty"; }
    "raw"
}
''',
            "validation.rs": '''pub fn env_supported(token: &str) -> bool {
    token == "empty" || token.starts_with("dq:") || token.starts_with("sq:") || token.starts_with("raw:")
}
''',
            "formatting.rs": '''pub fn format_env(key: &str, value: &str, kind: &str) -> String {
    format!("key={key}|value={value}|kind={kind}")
}
''',
            "main.rs": '''mod classification;
mod formatting;
mod normalization;
mod validation;

use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();
    let count: usize = lines.next().unwrap().parse().unwrap();
    for line in lines.take(count) {
        let (key, token) = line.split_once('|').unwrap();
        assert!(validation::env_supported(token));
        println!("{}", formatting::format_env(key, &normalization::normalize_env(token), classification::env_kind(token)));
    }
}
''',
        },
    }
    task = {
        "id": "quoted_environment_project",
        "title": "Preserve values while removing environment quote markers",
        "category": "configuration normalization across parser layers",
        "statement": "Fix the quoted-environment normalization regression using the read-only issue, architecture, and regression evidence. Preserve the existing input/output contract and do not modify read-only files.",
        "show_public_examples": False,
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "public_cases": [{
            "stdin": "3\nURL|dq:db://local\nUSER|sq:admin\nMODE|raw:prod\n",
            "stdout": "key=URL|value=db://local|kind=quoted\nkey=USER|value=admin|kind=quoted\nkey=MODE|value=prod|kind=raw\n",
        }],
        "hidden_cases": [
            {"stdin": "1\nEMPTY|empty\n", "stdout": "key=EMPTY|value=|kind=empty\n"},
            {"stdin": "1\nTOKEN|dq:a=b=c\n", "stdout": "key=TOKEN|value=a=b=c|kind=quoted\n"},
            {"stdin": "2\nA|dq:x\nB|sq:y\n", "stdout": "key=A|value=x|kind=quoted\nkey=B|value=y|kind=quoted\n"},
            {"stdin": "1\nRAW|raw:dq:value\n", "stdout": "key=RAW|value=dq:value|kind=raw\n"},
        ],
        "seed_files": seed_files,
        "context_files": symmetric_context(
            "# Quoted environment values keep their quote marker\n\nThe environment loader represents matching double and single quotes as `dq:` and `sq:` markers. Both markers are syntax and must be removed exactly once. Raw values remove only `raw:`; an explicit empty value stays present and empty. Content after a marker is arbitrary and may contain `=` or marker-like text.\n",
            "# Environment loading flow\n\n`validation` accepts encoded tokens. `classification` records quoted, raw, or empty state. `normalization` owns removal of one outer marker. `formatting` owns stable output. `main` orchestrates. Repair normalization instead of hiding markers in the formatter.\n",
            "double-quoted marker is removed once\nsingle-quoted marker is removed once\nraw marker is removed without reinterpreting content\nempty remains present with an empty value\n",
        ),
    }
    return task, {"parley": {"normalization.par": parley_fix}, "python": {"normalization.py": python_fix}, "rust": {"normalization.rs": rust_fix}}


def retry_after_task() -> tuple[dict, dict]:
    parley_bug = '''to retry_delay with status as text, header_delay as text, configured_delay as text giving text:
    if status is not "429":
        give back "0"
    if configured_delay is not "none":
        give back configured_delay
    if header_delay is not "none":
        give back header_delay
    give back "60"
'''
    parley_fix = parley_bug.replace(
        'if configured_delay is not "none":\n        give back configured_delay\n    if header_delay is not "none":\n        give back header_delay',
        'if header_delay is not "none":\n        give back header_delay\n    if configured_delay is not "none":\n        give back configured_delay',
    )
    python_bug = '''def retry_delay(status: str, header_delay: str, configured_delay: str) -> str:
    if status != "429":
        return "0"
    if configured_delay != "none":
        return configured_delay
    if header_delay != "none":
        return header_delay
    return "60"
'''
    python_fix = python_bug.replace(
        'if configured_delay != "none":\n        return configured_delay\n    if header_delay != "none":\n        return header_delay',
        'if header_delay != "none":\n        return header_delay\n    if configured_delay != "none":\n        return configured_delay',
    )
    rust_bug = '''pub fn retry_delay(status: &str, header_delay: &str, configured_delay: &str) -> String {
    if status != "429" { return "0".to_string(); }
    if configured_delay != "none" { return configured_delay.to_string(); }
    if header_delay != "none" { return header_delay.to_string(); }
    "60".to_string()
}
'''
    rust_fix = rust_bug.replace(
        'if configured_delay != "none" { return configured_delay.to_string(); }\n    if header_delay != "none" { return header_delay.to_string(); }',
        'if header_delay != "none" { return header_delay.to_string(); }\n    if configured_delay != "none" { return configured_delay.to_string(); }',
    )
    seed_files = {
        "parley": {
            "retry_policy.par": parley_bug,
            "status.par": '''to is_throttled with status as text giving yesno:
    give back status is "429"
''',
            "source.par": '''to retry_source with status as text, header_delay as text, configured_delay as text giving text:
    if status is not "429":
        give back "none"
    if header_delay is not "none":
        give back "header"
    if configured_delay is not "none":
        give back "configured"
    give back "default"
''',
            "formatting.par": '''to format_retry with status as text, delay as text, source as text giving text:
    give back "status=" + status + "|delay=" + delay + "|source=" + source
''',
            "main.par": '''include "retry_policy.par"
include "status.par"
include "source.par"
include "formatting.par"

to main:
    let count_input be ask for a number ""
    let count be value of count_input
    repeat count times:
        let parts be (ask "") split by "|"
        let status be item 1 of parts
        let header_delay be item 2 of parts
        let configured_delay be item 3 of parts
        say (format_retry with status, (retry_delay with status, header_delay, configured_delay), (retry_source with status, header_delay, configured_delay))
''',
        },
        "python": {
            "retry_policy.py": python_bug,
            "status.py": '''def is_throttled(status: str) -> bool:
    return status == "429"
''',
            "source.py": '''def retry_source(status: str, header_delay: str, configured_delay: str) -> str:
    if status != "429": return "none"
    if header_delay != "none": return "header"
    if configured_delay != "none": return "configured"
    return "default"
''',
            "formatting.py": '''def format_retry(status: str, delay: str, source: str) -> str:
    return f"status={status}|delay={delay}|source={source}"
''',
            "main.py": '''from formatting import format_retry
from retry_policy import retry_delay
from source import retry_source

count = int(input())
for _ in range(count):
    status, header_delay, configured_delay = input().split("|")
    print(format_retry(status, retry_delay(status, header_delay, configured_delay), retry_source(status, header_delay, configured_delay)))
''',
        },
        "rust": {
            "retry_policy.rs": rust_bug,
            "status.rs": '''pub fn is_throttled(status: &str) -> bool { status == "429" }
''',
            "source.rs": '''pub fn retry_source(status: &str, header_delay: &str, configured_delay: &str) -> &'static str {
    if status != "429" { return "none"; }
    if header_delay != "none" { return "header"; }
    if configured_delay != "none" { return "configured"; }
    "default"
}
''',
            "formatting.rs": '''pub fn format_retry(status: &str, delay: &str, source: &str) -> String {
    format!("status={status}|delay={delay}|source={source}")
}
''',
            "main.rs": '''mod formatting;
mod retry_policy;
mod source;
mod status;

use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();
    let count: usize = lines.next().unwrap().parse().unwrap();
    for line in lines.take(count) {
        let parts: Vec<&str> = line.split('|').collect();
        println!("{}", formatting::format_retry(parts[0], &retry_policy::retry_delay(parts[0], parts[1], parts[2]), source::retry_source(parts[0], parts[1], parts[2])));
    }
}
''',
        },
    }
    task = {
        "id": "retry_after_precedence_project",
        "title": "Honor server Retry-After before configured backoff",
        "category": "throttling policy across response layers",
        "statement": "Fix the throttling-delay regression using the read-only issue, architecture, and regression evidence. Preserve the existing input/output contract and do not modify read-only files.",
        "show_public_examples": False,
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "public_cases": [{
            "stdin": "3\n429|30|5\n429|none|5\n200|20|5\n",
            "stdout": "status=429|delay=30|source=header\nstatus=429|delay=5|source=configured\nstatus=200|delay=0|source=none\n",
        }],
        "hidden_cases": [
            {"stdin": "1\n429|120|none\n", "stdout": "status=429|delay=120|source=header\n"},
            {"stdin": "1\n429|none|none\n", "stdout": "status=429|delay=60|source=default\n"},
            {"stdin": "1\n503|9|7\n", "stdout": "status=503|delay=0|source=none\n"},
            {"stdin": "2\n429|1|99\n429|none|8\n", "stdout": "status=429|delay=1|source=header\nstatus=429|delay=8|source=configured\n"},
        ],
        "seed_files": seed_files,
        "context_files": symmetric_context(
            "# Client ignores Retry-After while throttled\n\nFor HTTP 429, a server-provided Retry-After delay is authoritative and must override configured backoff. Configured backoff is used only when the header is absent; otherwise use the 60-second default. Non-429 responses are not scheduled for retry by this policy.\n",
            "# Retry decision flow\n\n`status` identifies throttling. `retry_policy` owns the selected delay. `source` independently labels the evidence source. `formatting` owns stable output. `main` orchestrates. Repair precedence in the policy instead of changing source labels or presentation.\n",
            "429 + header + configured -> header delay\n429 + no header -> configured delay\n429 + neither -> 60-second default\nnon-429 -> zero delay and no source\n",
        ),
    }
    return task, {"parley": {"retry_policy.par": parley_fix}, "python": {"retry_policy.py": python_fix}, "rust": {"retry_policy.rs": rust_fix}}


def webhook_body_task() -> tuple[dict, dict]:
    parley_bug = '''to webhook_verified with raw_body as text, normalized_body as text, signature as text giving yesno:
    give back signature is "sig:" + normalized_body
'''
    parley_fix = parley_bug.replace('"sig:" + normalized_body', '"sig:" + raw_body')
    python_bug = '''def webhook_verified(raw_body: str, normalized_body: str, signature: str) -> bool:
    return signature == "sig:" + normalized_body
'''
    python_fix = python_bug.replace('"sig:" + normalized_body', '"sig:" + raw_body')
    rust_bug = '''pub fn webhook_verified(_raw_body: &str, normalized_body: &str, signature: &str) -> bool {
    signature == format!("sig:{normalized_body}")
}
'''
    rust_fix = '''pub fn webhook_verified(raw_body: &str, _normalized_body: &str, signature: &str) -> bool {
    signature == format!("sig:{raw_body}")
}
'''
    seed_files = {
        "parley": {
            "verification.par": parley_bug,
            "capture.par": '''to captured_body with raw_body as text giving text:
    give back raw_body
''',
            "normalization.par": '''to normalized_for_application with normalized_body as text giving text:
    give back normalized_body
''',
            "formatting.par": '''to format_webhook with delivery as text, verified as yesno, body as text giving text:
    give back "delivery={delivery}|verified={verified}|body={body}"
''',
            "main.par": '''include "verification.par"
include "capture.par"
include "normalization.par"
include "formatting.par"

to main:
    let count_input be ask for a number ""
    let count be value of count_input
    repeat count times:
        let parts be (ask "") split by "|"
        let delivery be item 1 of parts
        let raw_body be item 2 of parts
        let normalized_body be (normalized_for_application with item 3 of parts)
        let signature be item 4 of parts
        say (format_webhook with delivery, (webhook_verified with raw_body, normalized_body, signature), (captured_body with raw_body))
''',
        },
        "python": {
            "verification.py": python_bug,
            "capture.py": '''def captured_body(raw_body: str) -> str:
    return raw_body
''',
            "normalization.py": '''def normalized_for_application(normalized_body: str) -> str:
    return normalized_body
''',
            "formatting.py": '''def format_webhook(delivery: str, verified: bool, body: str) -> str:
    return f"delivery={delivery}|verified={'yes' if verified else 'no'}|body={body}"
''',
            "main.py": '''from capture import captured_body
from formatting import format_webhook
from normalization import normalized_for_application
from verification import webhook_verified

count = int(input())
for _ in range(count):
    delivery, raw_body, normalized_body, signature = input().split("|")
    normalized_body = normalized_for_application(normalized_body)
    print(format_webhook(delivery, webhook_verified(raw_body, normalized_body, signature), captured_body(raw_body)))
''',
        },
        "rust": {
            "verification.rs": rust_bug,
            "capture.rs": '''pub fn captured_body(raw_body: &str) -> &str { raw_body }
''',
            "normalization.rs": '''pub fn normalized_for_application(normalized_body: &str) -> &str { normalized_body }
''',
            "formatting.rs": '''pub fn format_webhook(delivery: &str, verified: bool, body: &str) -> String {
    format!("delivery={delivery}|verified={}|body={body}", if verified { "yes" } else { "no" })
}
''',
            "main.rs": '''mod capture;
mod formatting;
mod normalization;
mod verification;

use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();
    let count: usize = lines.next().unwrap().parse().unwrap();
    for line in lines.take(count) {
        let parts: Vec<&str> = line.split('|').collect();
        let normalized = normalization::normalized_for_application(parts[2]);
        println!("{}", formatting::format_webhook(parts[0], verification::webhook_verified(parts[1], normalized, parts[3]), capture::captured_body(parts[1])));
    }
}
''',
        },
    }
    task = {
        "id": "webhook_raw_body_project",
        "title": "Verify webhook signatures against the captured raw body",
        "category": "security verification across request middleware",
        "statement": "Fix the webhook-verification regression using the read-only issue, architecture, and regression evidence. Preserve the existing input/output contract and do not modify read-only files.",
        "show_public_examples": False,
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "public_cases": [{
            "stdin": "3\nd1|a:1,b:2|a:1;b:2|sig:a:1,b:2\nd2|same|same|sig:same\nd3|raw-x|norm-x|sig:norm-x\n",
            "stdout": "delivery=d1|verified=yes|body=a:1,b:2\ndelivery=d2|verified=yes|body=same\ndelivery=d3|verified=no|body=raw-x\n",
        }],
        "hidden_cases": [
            {"stdin": "1\nx|space+kept|space-trimmed|sig:space+kept\n", "stdout": "delivery=x|verified=yes|body=space+kept\n"},
            {"stdin": "1\ny|unicode-raw|unicode-normal|sig:unicode-normal\n", "stdout": "delivery=y|verified=no|body=unicode-raw\n"},
            {"stdin": "1\nz|same|same|sig:wrong\n", "stdout": "delivery=z|verified=no|body=same\n"},
            {"stdin": "2\na|r1|n1|sig:r1\nb|r2|n2|sig:n2\n", "stdout": "delivery=a|verified=yes|body=r1\ndelivery=b|verified=no|body=r2\n"},
        ],
        "seed_files": seed_files,
        "context_files": symmetric_context(
            "# Webhook signatures fail or validate after body parsing\n\nA signature authenticates the exact captured request bytes. Application normalization may reorder or rewrite the body and is useful only after verification. Compare the provided signature with the raw-body signature; never verify normalized content. The output still exposes the captured body for audit.\n",
            "# Webhook request flow\n\n`capture` owns the immutable raw body. `normalization` prepares application content. `verification` owns signature comparison. `formatting` owns stable audit output. `main` orchestrates. Repair verification instead of bypassing normalization or rewriting audit output.\n",
            "raw differs from normalized + raw signature -> verified\nraw differs + normalized signature -> rejected\nidentical bodies still verify correctly\naudit body is always the captured raw value\n",
        ),
    }
    return task, {"parley": {"verification.par": parley_fix}, "python": {"verification.py": python_fix}, "rust": {"verification.rs": rust_fix}}


def stable_pagination_task() -> tuple[dict, dict]:
    parley_bug = '''to first_item with left_time as number, left_id as number, right_time as number, right_id as number giving number:
    if left_time is less than right_time:
        give back left_id
    if left_time is right_time:
        give back right_id
    give back right_id
'''
    parley_fix = parley_bug.replace(
        'if left_time is right_time:\n        give back right_id',
        'if left_time is right_time:\n        if left_id is less than right_id:\n            give back left_id\n        give back right_id',
    )
    python_bug = '''def first_item(left_time: int, left_id: int, right_time: int, right_id: int) -> int:
    if left_time < right_time:
        return left_id
    if left_time == right_time:
        return right_id
    return right_id
'''
    python_fix = python_bug.replace(
        'if left_time == right_time:\n        return right_id',
        'if left_time == right_time:\n        return min(left_id, right_id)',
    )
    rust_bug = '''pub fn first_item(left_time: i64, left_id: i64, right_time: i64, right_id: i64) -> i64 {
    if left_time < right_time { return left_id; }
    if left_time == right_time { return right_id; }
    right_id
}
'''
    rust_fix = rust_bug.replace(
        'if left_time == right_time { return right_id; }',
        'if left_time == right_time { return left_id.min(right_id); }',
    )
    seed_files = {
        "parley": {
            "ordering.par": parley_bug,
            "page.par": '''to second_item with first as number, left_id as number, right_id as number giving number:
    if first is left_id:
        give back right_id
    give back left_id
''',
            "cursor.par": '''to page_cursor with second as number giving number:
    give back second
''',
            "formatting.par": '''to format_page with first as number, second as number, cursor as number giving text:
    give back "first={first}|second={second}|cursor={cursor}"
''',
            "main.par": '''include "ordering.par"
include "page.par"
include "cursor.par"
include "formatting.par"

to main:
    let count_input be ask for a number ""
    let count be value of count_input
    repeat count times:
        let parts be (ask "") split by "|"
        let left_time_input be number from item 1 of parts
        let left_id_input be number from item 2 of parts
        let right_time_input be number from item 3 of parts
        let right_id_input be number from item 4 of parts
        let left_time be value of left_time_input
        let left_id be value of left_id_input
        let right_time be value of right_time_input
        let right_id be value of right_id_input
        let first be (first_item with left_time, left_id, right_time, right_id)
        let second be (second_item with first, left_id, right_id)
        say (format_page with first, second, (page_cursor with second))
''',
        },
        "python": {
            "ordering.py": python_bug,
            "page.py": '''def second_item(first: int, left_id: int, right_id: int) -> int:
    return right_id if first == left_id else left_id
''',
            "cursor.py": '''def page_cursor(second: int) -> int:
    return second
''',
            "formatting.py": '''def format_page(first: int, second: int, cursor: int) -> str:
    return f"first={first}|second={second}|cursor={cursor}"
''',
            "main.py": '''from cursor import page_cursor
from formatting import format_page
from ordering import first_item
from page import second_item

count = int(input())
for _ in range(count):
    left_time, left_id, right_time, right_id = map(int, input().split("|"))
    first = first_item(left_time, left_id, right_time, right_id)
    second = second_item(first, left_id, right_id)
    print(format_page(first, second, page_cursor(second)))
''',
        },
        "rust": {
            "ordering.rs": rust_bug,
            "page.rs": '''pub fn second_item(first: i64, left_id: i64, right_id: i64) -> i64 {
    if first == left_id { right_id } else { left_id }
}
''',
            "cursor.rs": '''pub fn page_cursor(second: i64) -> i64 { second }
''',
            "formatting.rs": '''pub fn format_page(first: i64, second: i64, cursor: i64) -> String {
    format!("first={first}|second={second}|cursor={cursor}")
}
''',
            "main.rs": '''mod cursor;
mod formatting;
mod ordering;
mod page;

use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();
    let count: usize = lines.next().unwrap().parse().unwrap();
    for line in lines.take(count) {
        let values: Vec<i64> = line.split('|').map(|part| part.parse().unwrap()).collect();
        let first = ordering::first_item(values[0], values[1], values[2], values[3]);
        let second = page::second_item(first, values[1], values[3]);
        println!("{}", formatting::format_page(first, second, cursor::page_cursor(second)));
    }
}
''',
        },
    }
    task = {
        "id": "stable_pagination_project",
        "title": "Stabilize pagination ordering with a unique tie-breaker",
        "category": "deterministic ordering across pagination layers",
        "statement": "Fix the pagination-order regression using the read-only issue, architecture, and regression evidence. Preserve the existing input/output contract and do not modify read-only files.",
        "show_public_examples": False,
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "public_cases": [{
            "stdin": "3\n10|4|10|9\n2|8|7|3\n9|7|3|2\n",
            "stdout": "first=4|second=9|cursor=9\nfirst=8|second=3|cursor=3\nfirst=2|second=7|cursor=7\n",
        }],
        "hidden_cases": [
            {"stdin": "1\n5|99|5|1\n", "stdout": "first=1|second=99|cursor=99\n"},
            {"stdin": "1\n1|9|2|1\n", "stdout": "first=9|second=1|cursor=1\n"},
            {"stdin": "1\n3|2|1|8\n", "stdout": "first=8|second=2|cursor=2\n"},
            {"stdin": "2\n7|3|7|4\n8|6|8|2\n", "stdout": "first=3|second=4|cursor=4\nfirst=2|second=6|cursor=6\n"},
        ],
        "seed_files": seed_files,
        "context_files": symmetric_context(
            "# Adjacent pages duplicate items when timestamps tie\n\nPagination orders records by creation time, but timestamps are not unique. A stable total order must use ascending creation time and then ascending unique ID. The page cursor is the second item's ID after ordering. Without the ID tie-breaker, equal-time records can swap and appear twice across page boundaries.\n",
            "# Pagination flow\n\n`ordering` owns the stable first item. `page` derives the second item. `cursor` advances from that second item. `formatting` owns stable output. `main` parses and orchestrates. Repair ordering rather than compensating in cursor or presentation code.\n",
            "earlier timestamp sorts first\nlater timestamp sorts second\nequal timestamps use ascending unique ID\ncursor is always the ordered second ID\n",
        ),
    }
    return task, {"parley": {"ordering.par": parley_fix}, "python": {"ordering.py": python_fix}, "rust": {"ordering.rs": rust_fix}}


def main() -> None:
    built = [quoted_env_task(), retry_after_task(), webhook_body_task(), stable_pagination_task()]
    tasks = [item[0] for item in built]
    fixes = {task["id"]: item[1] for task, item in zip(tasks, built)}
    roots = {
        "quoted_environment_project": {"parley": "normalization.par", "python": "normalization.py", "rust": "normalization.rs"},
        "retry_after_precedence_project": {"parley": "retry_policy.par", "python": "retry_policy.py", "rust": "retry_policy.rs"},
        "webhook_raw_body_project": {"parley": "verification.par", "python": "verification.py", "rust": "verification.rs"},
        "stable_pagination_project": {"parley": "ordering.par", "python": "ordering.py", "rust": "ordering.rs"},
    }
    manifest = {
        "schema_version": 1,
        "description": "Four new five-module regressions for an independent deeper-project confirmation after product work.",
        "predeclared_analysis": {
            "experiment_id": "032",
            "scope": "New project mechanisms selected independently of report 031; each has five editable modules and three visibly read-only evidence files per language.",
            "primary_question": "After shipping workflow products without compiler or instruction tuning, does Parley repeat strict efficiency/reliability parity against Python and Rust on new deeper projects?",
            "historical_sources": [
                {"task": "quoted_environment_project", "url": "https://github.com/quarkusio/quarkus/issues/35861", "mechanism": "quoted dotenv values retaining their quote representation"},
                {"task": "retry_after_precedence_project", "url": "https://github.com/microsoftgraph/msgraph-sdk-javascript/issues/42", "mechanism": "Retry-After response evidence lost before retry policy"},
                {"task": "webhook_raw_body_project", "url": "https://github.com/stripe/stripe-node/issues/331", "mechanism": "signature verification requires the exact raw request body"},
                {"task": "stable_pagination_project", "url": "https://github.com/orgs/langfuse/discussions/7623", "mechanism": "non-unique sort keys duplicate records across paginated responses"},
            ],
            "adaptation_rule": "Mechanisms and dependency shapes are adapted independently; no upstream source code, tests, names, or fixtures are copied.",
            "independence_rule": "No task mechanism, defect location, fixture, or expected repair was selected from report 031 outcomes or failures.",
            "root_cause_files": roots,
            "root_cause_gate": "Every Parley assignment must change exactly its predeclared seeded defect file; caller, formatter, or downstream compensation fails maintainability even if hidden output passes.",
            "change_rule": "No language change follows one project or efficiency delta. Eligibility requires a semantic failure recurring across independent products or projects, followed by general usefulness, semantic consistency, maintainability, and full regression coverage.",
            "instruction_rule": "Use the unchanged 1,519-character Parley skill. The one allowed instruction-compression experiment remains closed.",
        },
        "tasks": tasks,
    }
    reference = {
        "schema_version": 1,
        "description": "Unmeasured reference root fixes used only to validate the frozen iteration-032 corpus before preregistration.",
        "fixes": fixes,
    }
    OUTPUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    FIXES.write_text(json.dumps(reference, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "manifest": str(OUTPUT),
        "reference_fixes": str(FIXES),
        "tasks": len(tasks),
        "editable_files_per_language_task": sorted({len(task["seed_files"][language]) for task in tasks for language in LANGUAGES}),
        "context_files_per_language_task": sorted({len(task["context_files"][language]) for task in tasks for language in LANGUAGES}),
    }, indent=2))


if __name__ == "__main__":
    main()
