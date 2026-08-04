#!/usr/bin/env python3
"""Build iteration 031's historically grounded deeper-project corpus."""

from __future__ import annotations

import json
from pathlib import Path


BENCHMARKS = Path(__file__).resolve().parent
OUTPUT = BENCHMARKS / "agent_tasks_deep_031.json"
FIXES = BENCHMARKS / "deep_reference_fixes_031.json"
LANGUAGES = ("parley", "python", "rust")


def symmetric_context(issue: str, flow: str, regression: str) -> dict:
    files = {
        "ISSUE.md": issue,
        "architecture/flow.md": flow,
        "tests/regression.txt": regression,
    }
    return {language: dict(files) for language in LANGUAGES}


def redirect_task() -> tuple[dict, dict]:
    parley_root_bug = '''to authorization_decision with current_scheme as text, current_host as text, current_port as text, next_scheme as text, next_host as text, next_port as text, authorization as text giving text:
    if authorization is "none":
        give back "absent"
    if current_port is next_port:
        if current_scheme is "https" and next_scheme is "http":
            give back "strip"
        give back "keep"
    give back "strip"
'''
    parley_root_fix = parley_root_bug.replace("current_port is next_port", "current_host is next_host")
    python_root_bug = '''def authorization_decision(current_scheme: str, current_host: str, current_port: str, next_scheme: str, next_host: str, next_port: str, authorization: str) -> str:
    if authorization == "none":
        return "absent"
    if current_port == next_port:
        if current_scheme == "https" and next_scheme == "http":
            return "strip"
        return "keep"
    return "strip"
'''
    python_root_fix = python_root_bug.replace("current_port == next_port", "current_host == next_host")
    rust_root_bug = '''pub fn authorization_decision(current_scheme: &str, _current_host: &str, current_port: &str, next_scheme: &str, _next_host: &str, next_port: &str, authorization: &str) -> &'static str {
    if authorization == "none" {
        return "absent";
    }
    if current_port == next_port {
        if current_scheme == "https" && next_scheme == "http" {
            return "strip";
        }
        return "keep";
    }
    "strip"
}
'''
    rust_root_fix = '''pub fn authorization_decision(current_scheme: &str, current_host: &str, _current_port: &str, next_scheme: &str, next_host: &str, _next_port: &str, authorization: &str) -> &'static str {
    if authorization == "none" {
        return "absent";
    }
    if current_host == next_host {
        if current_scheme == "https" && next_scheme == "http" {
            return "strip";
        }
        return "keep";
    }
    "strip"
}
'''
    seed_files = {
        "parley": {
            "credentials.par": parley_root_bug,
            "formatting.par": '''to format_redirect with target as text, authorization as text, proxy as text giving text:
    give back "target=" + target + "|authorization=" + authorization + "|proxy=" + proxy
''',
            "main.par": '''include "origin.par"
include "credentials.par"
include "proxy.par"
include "formatting.par"

to main:
    let count_input be ask for a number ""
    let count be value of count_input
    repeat count times:
        let parts be (ask "") split by "|"
        let current_scheme be item 1 of parts
        let current_host be item 2 of parts
        let current_port be item 3 of parts
        let next_scheme be item 4 of parts
        let next_host be item 5 of parts
        let next_port be item 6 of parts
        let authorization be item 7 of parts
        let proxy be item 8 of parts
        let target be (redirect_target with next_scheme, next_host, next_port)
        let auth_result be (authorization_decision with current_scheme, current_host, current_port, next_scheme, next_host, next_port, authorization)
        let proxy_result be (proxy_decision with proxy)
        say (format_redirect with target, auth_result, proxy_result)
''',
            "origin.par": '''to redirect_target with scheme as text, host as text, port as text giving text:
    give back scheme + "://" + host + ":" + port
''',
            "proxy.par": '''to proxy_decision with proxy_authorization as text giving text:
    if proxy_authorization is "none":
        give back "absent"
    give back "strip"
''',
        },
        "python": {
            "credentials.py": python_root_bug,
            "formatting.py": '''def format_redirect(target: str, authorization: str, proxy: str) -> str:
    return f"target={target}|authorization={authorization}|proxy={proxy}"
''',
            "main.py": '''from credentials import authorization_decision
from formatting import format_redirect
from origin import redirect_target
from proxy import proxy_decision

count = int(input())
for _ in range(count):
    current_scheme, current_host, current_port, next_scheme, next_host, next_port, authorization, proxy = input().split("|")
    target = redirect_target(next_scheme, next_host, next_port)
    auth_result = authorization_decision(current_scheme, current_host, current_port, next_scheme, next_host, next_port, authorization)
    print(format_redirect(target, auth_result, proxy_decision(proxy)))
''',
            "origin.py": '''def redirect_target(scheme: str, host: str, port: str) -> str:
    return f"{scheme}://{host}:{port}"
''',
            "proxy.py": '''def proxy_decision(proxy_authorization: str) -> str:
    return "absent" if proxy_authorization == "none" else "strip"
''',
        },
        "rust": {
            "credentials.rs": rust_root_bug,
            "formatting.rs": '''pub fn format_redirect(target: &str, authorization: &str, proxy: &str) -> String {
    format!("target={target}|authorization={authorization}|proxy={proxy}")
}
''',
            "main.rs": '''mod credentials;
mod formatting;
mod origin;
mod proxy;

use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();
    let count: usize = lines.next().unwrap().parse().unwrap();
    for line in lines.take(count) {
        let parts: Vec<&str> = line.split('|').collect();
        let target = origin::redirect_target(parts[3], parts[4], parts[5]);
        let authorization = credentials::authorization_decision(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]);
        let proxy = proxy::proxy_decision(parts[7]);
        println!("{}", formatting::format_redirect(&target, authorization, proxy));
    }
}
''',
            "origin.rs": '''pub fn redirect_target(scheme: &str, host: &str, port: &str) -> String {
    format!("{scheme}://{host}:{port}")
}
''',
            "proxy.rs": '''pub fn proxy_decision(proxy_authorization: &str) -> &'static str {
    if proxy_authorization == "none" { "absent" } else { "strip" }
}
''',
        },
    }
    task = {
        "id": "redirect_credential_scope_project",
        "title": "Repair redirect credential-scope regression",
        "category": "security policy across redirect layers",
        "statement": "Fix the redirect credential regression using the read-only issue, architecture, and regression evidence. Preserve the existing input/output contract and do not modify read-only files.",
        "show_public_examples": False,
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "public_cases": [{
            "stdin": "3\nhttp|api.local|80|https|api.local|443|bearer|proxy\nhttps|api.local|443|http|api.local|80|bearer|none\nhttps|api.local|443|https|cdn.local|443|bearer|proxy\n",
            "stdout": "target=https://api.local:443|authorization=keep|proxy=strip\ntarget=http://api.local:80|authorization=strip|proxy=absent\ntarget=https://cdn.local:443|authorization=strip|proxy=strip\n",
        }],
        "hidden_cases": [
            {"stdin": "1\nhttps|svc.local|443|https|svc.local|443|bearer|none\n", "stdout": "target=https://svc.local:443|authorization=keep|proxy=absent\n"},
            {"stdin": "1\nhttp|svc.local|8080|http|svc.local|9090|bearer|proxy\n", "stdout": "target=http://svc.local:9090|authorization=keep|proxy=strip\n"},
            {"stdin": "1\nhttp|one.local|80|https|two.local|443|bearer|none\n", "stdout": "target=https://two.local:443|authorization=strip|proxy=absent\n"},
            {"stdin": "1\nhttp|one.local|80|https|two.local|80|none|proxy\n", "stdout": "target=https://two.local:80|authorization=absent|proxy=strip\n"},
        ],
        "seed_files": seed_files,
        "context_files": symmetric_context(
            "# Redirect credentials escape or disappear at the wrong boundary\n\nAuthorization may survive a redirect only when the hostname is unchanged and the transition is not an HTTPS-to-HTTP downgrade. A port change on the same host is allowed. Authorization must be stripped for a different host. Proxy-Authorization is hop-specific and must be stripped on every redirect. Missing credentials remain absent.\n",
            "# Redirect flow\n\n`main` parses the redirect record. `origin` renders the next target. `credentials` owns end-to-end Authorization scope. `proxy` owns hop-specific Proxy-Authorization. `formatting` owns the stable audit line. Repair the owning policy rather than compensating in the caller or formatter.\n",
            "same host http:80 -> https:443 keeps Authorization\nsame host https:443 -> http:80 strips Authorization\ndifferent host on same port strips Authorization\nall redirects strip Proxy-Authorization\n",
        ),
    }
    fixes = {"parley": {"credentials.par": parley_root_fix}, "python": {"credentials.py": python_root_fix}, "rust": {"credentials.rs": rust_root_fix}}
    return task, fixes


def empty_collection_task() -> tuple[dict, dict]:
    parley_bug = '''to config_kind with token as text giving text:
    if token is "missing":
        give back "missing"
    if token is "null":
        give back "null"
    if token is "empty":
        give back "missing"
    if token is "one" or token is "two" or token is "three":
        give back "list"
    give back "invalid"
'''
    parley_fix = parley_bug.replace('if token is "empty":\n        give back "missing"', 'if token is "empty":\n        give back "empty"')
    python_bug = '''def config_kind(token: str) -> str:
    if token == "missing":
        return "missing"
    if token == "null":
        return "null"
    if token == "empty":
        return "missing"
    if token in ("one", "two", "three"):
        return "list"
    return "invalid"
'''
    python_fix = python_bug.replace('if token == "empty":\n        return "missing"', 'if token == "empty":\n        return "empty"')
    rust_bug = '''pub fn config_kind(token: &str) -> &'static str {
    match token {
        "missing" => "missing",
        "null" => "null",
        "empty" => "missing",
        "one" | "two" | "three" => "list",
        _ => "invalid",
    }
}
'''
    rust_fix = rust_bug.replace('"empty" => "missing"', '"empty" => "empty"')
    seed_files = {
        "parley": {
            "classification.par": parley_bug,
            "counts.par": '''to item_count with token as text, kind as text giving number:
    if kind is not "list":
        give back 0
    if token is "one":
        give back 1
    if token is "two":
        give back 2
    give back 3
''',
            "formatting.par": '''to format_config with source as text, kind as text, count as number giving text:
    give back "source=" + source + "|kind=" + kind + "|count=" + count
''',
            "main.par": '''include "classification.par"
include "selection.par"
include "counts.par"
include "formatting.par"

to main:
    let count_input be ask for a number ""
    let count be value of count_input
    repeat count times:
        let parts be (ask "") split by "|"
        let chosen be (select_config with item 1 of parts, item 2 of parts)
        let selected be chosen split by "|"
        let source be item 1 of selected
        let token be item 2 of selected
        let kind be (config_kind with token)
        say (format_config with source, kind, (item_count with token, kind))
''',
            "selection.par": '''to select_config with primary as text, fallback as text giving text:
    if (config_kind with primary) is not "missing":
        give back "primary|" + primary
    if (config_kind with fallback) is not "missing":
        give back "fallback|" + fallback
    give back "default|empty"
''',
        },
        "python": {
            "classification.py": python_bug,
            "counts.py": '''def item_count(token: str, kind: str) -> int:
    if kind != "list":
        return 0
    return {"one": 1, "two": 2, "three": 3}[token]
''',
            "formatting.py": '''def format_config(source: str, kind: str, count: int) -> str:
    return f"source={source}|kind={kind}|count={count}"
''',
            "main.py": '''from classification import config_kind
from counts import item_count
from formatting import format_config
from selection import select_config

count = int(input())
for _ in range(count):
    primary, fallback = input().split("|")
    source, token = select_config(primary, fallback).split("|")
    kind = config_kind(token)
    print(format_config(source, kind, item_count(token, kind)))
''',
            "selection.py": '''from classification import config_kind

def select_config(primary: str, fallback: str) -> str:
    if config_kind(primary) != "missing":
        return f"primary|{primary}"
    if config_kind(fallback) != "missing":
        return f"fallback|{fallback}"
    return "default|empty"
''',
        },
        "rust": {
            "classification.rs": rust_bug,
            "counts.rs": '''pub fn item_count(token: &str, kind: &str) -> i64 {
    if kind != "list" { return 0; }
    match token { "one" => 1, "two" => 2, _ => 3 }
}
''',
            "formatting.rs": '''pub fn format_config(source: &str, kind: &str, count: i64) -> String {
    format!("source={source}|kind={kind}|count={count}")
}
''',
            "main.rs": '''mod classification;
mod counts;
mod formatting;
mod selection;

use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();
    let count: usize = lines.next().unwrap().parse().unwrap();
    for line in lines.take(count) {
        let pair: Vec<&str> = line.split('|').collect();
        let chosen = selection::select_config(pair[0], pair[1]);
        let selected: Vec<&str> = chosen.split('|').collect();
        let kind = classification::config_kind(selected[1]);
        println!("{}", formatting::format_config(selected[0], kind, counts::item_count(selected[1], kind)));
    }
}
''',
            "selection.rs": '''use crate::classification::config_kind;

pub fn select_config(primary: &str, fallback: &str) -> String {
    if config_kind(primary) != "missing" { return format!("primary|{primary}"); }
    if config_kind(fallback) != "missing" { return format!("fallback|{fallback}"); }
    "default|empty".to_string()
}
''',
        },
    }
    task = {
        "id": "empty_collection_config_project",
        "title": "Preserve explicit empty collections through configuration fallback",
        "category": "configuration value-state preservation",
        "statement": "Fix the configuration regression using the read-only issue, architecture, and regression evidence. Preserve the existing input/output contract and do not modify read-only files.",
        "show_public_examples": False,
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "public_cases": [{
            "stdin": "4\nempty|two\nmissing|two\nnull|three\nmissing|missing\n",
            "stdout": "source=primary|kind=empty|count=0\nsource=fallback|kind=list|count=2\nsource=primary|kind=null|count=0\nsource=default|kind=empty|count=0\n",
        }],
        "hidden_cases": [
            {"stdin": "1\nempty|three\n", "stdout": "source=primary|kind=empty|count=0\n"},
            {"stdin": "1\nmissing|empty\n", "stdout": "source=fallback|kind=empty|count=0\n"},
            {"stdin": "1\none|empty\n", "stdout": "source=primary|kind=list|count=1\n"},
            {"stdin": "1\nnull|empty\n", "stdout": "source=primary|kind=null|count=0\n"},
        ],
        "seed_files": seed_files,
        "context_files": symmetric_context(
            "# Explicit empty collections become missing during configuration binding\n\nThe configuration pipeline must preserve four distinct states: missing, explicit null, explicit empty collection, and populated list. Only missing may fall through to the lower-precedence source. An explicit empty collection blocks fallback and binds as an empty list; null also blocks fallback but remains null.\n",
            "# Configuration flow\n\n`classification` assigns the value state. `selection` applies source precedence using that state. `counts` measures populated lists. `formatting` owns the stable output. `main` only orchestrates. Repair the earliest layer that loses the distinction; caller-side special cases are not maintainable.\n",
            "primary empty + fallback two -> primary empty count 0\nprimary missing + fallback empty -> fallback empty count 0\nprimary null never falls through\nmissing at both levels -> default empty\n",
        ),
    }
    fixes = {"parley": {"classification.par": parley_fix}, "python": {"classification.py": python_fix}, "rust": {"classification.rs": rust_fix}}
    return task, fixes


def forwarded_origin_task() -> tuple[dict, dict]:
    parley_bug = '''to redirect_origin with trusted as text, request_scheme as text, request_host as text, request_port as text, forwarded_scheme as text, forwarded_host as text, forwarded_port as text giving text:
    let scheme be (selected_header with trusted, forwarded_scheme, request_scheme)
    let host be request_host
    let port be (selected_header with trusted, forwarded_port, request_port)
    give back scheme + "://" + host + ":" + port
'''
    parley_fix = parley_bug.replace("let host be request_host", "let host be (selected_header with trusted, forwarded_host, request_host)")
    python_bug = '''from headers import selected_header

def redirect_origin(trusted: str, request_scheme: str, request_host: str, request_port: str, forwarded_scheme: str, forwarded_host: str, forwarded_port: str) -> str:
    scheme = selected_header(trusted, forwarded_scheme, request_scheme)
    host = request_host
    port = selected_header(trusted, forwarded_port, request_port)
    return f"{scheme}://{host}:{port}"
'''
    python_fix = python_bug.replace("host = request_host", "host = selected_header(trusted, forwarded_host, request_host)")
    rust_bug = '''use crate::headers::selected_header;

pub fn redirect_origin<'a>(trusted: &str, request_scheme: &'a str, request_host: &'a str, request_port: &'a str, forwarded_scheme: &'a str, _forwarded_host: &'a str, forwarded_port: &'a str) -> String {
    let scheme = selected_header(trusted, forwarded_scheme, request_scheme);
    let host = request_host;
    let port = selected_header(trusted, forwarded_port, request_port);
    format!("{scheme}://{host}:{port}")
}
'''
    rust_fix = rust_bug.replace("_forwarded_host: &'a str", "forwarded_host: &'a str").replace("let host = request_host;", "let host = selected_header(trusted, forwarded_host, request_host);")
    seed_files = {
        "parley": {
            "formatting.par": '''to format_login with source as text, location as text giving text:
    give back "source=" + source + "|location=" + location
''',
            "headers.par": '''to selected_header with trusted as text, forwarded as text, original as text giving text:
    if trusted is "yes" and forwarded is not "-":
        give back forwarded
    give back original

to origin_source with trusted as text giving text:
    if trusted is "yes":
        give back "trusted-proxy"
    give back "request"
''',
            "main.par": '''include "headers.par"
include "origin.par"
include "paths.par"
include "formatting.par"

to main:
    let count_input be ask for a number ""
    let count be value of count_input
    repeat count times:
        let parts be (ask "") split by "|"
        let origin be (redirect_origin with item 1 of parts, item 2 of parts, item 3 of parts, item 4 of parts, item 5 of parts, item 6 of parts, item 7 of parts)
        let location be (join_location with origin, item 8 of parts)
        say (format_login with (origin_source with item 1 of parts), location)
''',
            "origin.par": parley_bug,
            "paths.par": '''to join_location with origin as text, path as text giving text:
    if path is "-":
        give back origin + "/"
    give back origin + path
''',
        },
        "python": {
            "formatting.py": '''def format_login(source: str, location: str) -> str:
    return f"source={source}|location={location}"
''',
            "headers.py": '''def selected_header(trusted: str, forwarded: str, original: str) -> str:
    if trusted == "yes" and forwarded != "-":
        return forwarded
    return original

def origin_source(trusted: str) -> str:
    return "trusted-proxy" if trusted == "yes" else "request"
''',
            "main.py": '''from formatting import format_login
from headers import origin_source
from origin import redirect_origin
from paths import join_location

count = int(input())
for _ in range(count):
    parts = input().split("|")
    origin = redirect_origin(*parts[:7])
    print(format_login(origin_source(parts[0]), join_location(origin, parts[7])))
''',
            "origin.py": python_bug,
            "paths.py": '''def join_location(origin: str, path: str) -> str:
    return origin + ("/" if path == "-" else path)
''',
        },
        "rust": {
            "formatting.rs": '''pub fn format_login(source: &str, location: &str) -> String {
    format!("source={source}|location={location}")
}
''',
            "headers.rs": '''pub fn selected_header<'a>(trusted: &str, forwarded: &'a str, original: &'a str) -> &'a str {
    if trusted == "yes" && forwarded != "-" { forwarded } else { original }
}

pub fn origin_source(trusted: &str) -> &'static str {
    if trusted == "yes" { "trusted-proxy" } else { "request" }
}
''',
            "main.rs": '''mod formatting;
mod headers;
mod origin;
mod paths;

use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();
    let count: usize = lines.next().unwrap().parse().unwrap();
    for line in lines.take(count) {
        let parts: Vec<&str> = line.split('|').collect();
        let origin = origin::redirect_origin(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]);
        let location = paths::join_location(&origin, parts[7]);
        println!("{}", formatting::format_login(headers::origin_source(parts[0]), &location));
    }
}
''',
            "origin.rs": rust_bug,
            "paths.rs": '''pub fn join_location(origin: &str, path: &str) -> String {
    if path == "-" { format!("{origin}/") } else { format!("{origin}{path}") }
}
''',
        },
    }
    task = {
        "id": "forwarded_origin_project",
        "title": "Reconstruct external redirect origin behind a trusted proxy",
        "category": "trusted boundary and origin reconstruction",
        "statement": "Fix the external-origin regression using the read-only issue, architecture, and regression evidence. Preserve the existing input/output contract and do not modify read-only files.",
        "show_public_examples": False,
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "public_cases": [{
            "stdin": "3\nyes|http|oauth.internal|4180|https|login.example.com|443|/callback\nno|http|direct.local|8080|https|spoof.example|443|/login\nyes|http|oauth.internal|4180|https|-|8443|-\n",
            "stdout": "source=trusted-proxy|location=https://login.example.com:443/callback\nsource=request|location=http://direct.local:8080/login\nsource=trusted-proxy|location=https://oauth.internal:8443/\n",
        }],
        "hidden_cases": [
            {"stdin": "1\nyes|http|backend|80|https|public.example|444|/oauth/start\n", "stdout": "source=trusted-proxy|location=https://public.example:444/oauth/start\n"},
            {"stdin": "1\nno|https|direct.example|443|http|attacker|80|/safe\n", "stdout": "source=request|location=https://direct.example:443/safe\n"},
            {"stdin": "1\nyes|http|backend|8080|-|public.example|-|/x\n", "stdout": "source=trusted-proxy|location=http://public.example:8080/x\n"},
            {"stdin": "1\nyes|http|backend|8080|https|public.example|443|-\n", "stdout": "source=trusted-proxy|location=https://public.example:443/\n"},
        ],
        "seed_files": seed_files,
        "context_files": symmetric_context(
            "# OAuth redirects point at an internal host behind the gateway\n\nWhen and only when the immediate proxy is trusted, reconstruct the public origin field-by-field from non-missing forwarded scheme, host, and port. A missing forwarded field falls back to the request value. For an untrusted request, ignore every forwarded field. Preserve the callback path.\n",
            "# Origin reconstruction flow\n\n`headers` owns trust-aware field selection. `origin` assembles the external origin. `paths` appends the callback path. `formatting` owns the stable audit line. `main` orchestrates the request record. Repair the origin layer; do not hard-code public hosts in the caller.\n",
            "trusted proxy uses forwarded host, scheme, and port\nmissing forwarded fields fall back independently\nuntrusted requests ignore all forwarded values\ncallback path and source label remain stable\n",
        ),
    }
    fixes = {"parley": {"origin.par": parley_fix}, "python": {"origin.py": python_fix}, "rust": {"origin.rs": rust_fix}}
    return task, fixes


def terminal_liveness_task() -> tuple[dict, dict]:
    parley_bug = '''to reconciled_state with persisted as text, live as text giving text:
    if persisted is "running":
        give back "running"
    if live is "yes":
        give back "running"
    give back "stopped"
'''
    parley_fix = '''to reconciled_state with persisted as text, live as text giving text:
    if live is "yes":
        give back "running"
    give back "stopped"
'''
    python_bug = '''def reconciled_state(persisted: str, live: str) -> str:
    if persisted == "running":
        return "running"
    if live == "yes":
        return "running"
    return "stopped"
'''
    python_fix = '''def reconciled_state(persisted: str, live: str) -> str:
    if live == "yes":
        return "running"
    return "stopped"
'''
    rust_bug = '''pub fn reconciled_state(persisted: &str, live: &str) -> &'static str {
    if persisted == "running" {
        return "running";
    }
    if live == "yes" {
        return "running";
    }
    "stopped"
}
'''
    rust_fix = '''pub fn reconciled_state(_persisted: &str, live: &str) -> &'static str {
    if live == "yes" {
        return "running";
    }
    "stopped"
}
'''
    seed_files = {
        "parley": {
            "formatting.par": '''to format_terminal with id as text, state as text, reason as text giving text:
    give back "id=" + id + "|state=" + state + "|reason=" + reason

to format_summary with running as number, stopped as number giving text:
    give back "running=" + running + "|stopped=" + stopped
''',
            "liveness.par": parley_bug,
            "main.par": '''include "liveness.par"
include "reasons.par"
include "summary.par"
include "formatting.par"

to main:
    let count_input be ask for a number ""
    let count be value of count_input
    let running be 0
    repeat count times:
        let parts be (ask "") split by "|"
        let state be (reconciled_state with item 2 of parts, item 3 of parts)
        if state is "running":
            set running to running + 1
        say (format_terminal with item 1 of parts, state, (reconcile_reason with item 3 of parts))
    say (format_summary with running, (stopped_count with count, running))
''',
            "reasons.par": '''to reconcile_reason with live as text giving text:
    if live is "yes":
        give back "authoritative-live"
    give back "authoritative-dead"
''',
            "summary.par": '''to stopped_count with total as number, running as number giving number:
    give back total - running
''',
        },
        "python": {
            "formatting.py": '''def format_terminal(identifier: str, state: str, reason: str) -> str:
    return f"id={identifier}|state={state}|reason={reason}"

def format_summary(running: int, stopped: int) -> str:
    return f"running={running}|stopped={stopped}"
''',
            "liveness.py": python_bug,
            "main.py": '''from formatting import format_summary, format_terminal
from liveness import reconciled_state
from reasons import reconcile_reason
from summary import stopped_count

count = int(input())
running = 0
for _ in range(count):
    identifier, persisted, live = input().split("|")
    state = reconciled_state(persisted, live)
    if state == "running":
        running += 1
    print(format_terminal(identifier, state, reconcile_reason(live)))
print(format_summary(running, stopped_count(count, running)))
''',
            "reasons.py": '''def reconcile_reason(live: str) -> str:
    return "authoritative-live" if live == "yes" else "authoritative-dead"
''',
            "summary.py": '''def stopped_count(total: int, running: int) -> int:
    return total - running
''',
        },
        "rust": {
            "formatting.rs": '''pub fn format_terminal(identifier: &str, state: &str, reason: &str) -> String {
    format!("id={identifier}|state={state}|reason={reason}")
}

pub fn format_summary(running: i64, stopped: i64) -> String {
    format!("running={running}|stopped={stopped}")
}
''',
            "liveness.rs": rust_bug,
            "main.rs": '''mod formatting;
mod liveness;
mod reasons;
mod summary;

use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();
    let count: i64 = lines.next().unwrap().parse().unwrap();
    let mut running = 0;
    for line in lines.take(count as usize) {
        let parts: Vec<&str> = line.split('|').collect();
        let state = liveness::reconciled_state(parts[1], parts[2]);
        if state == "running" { running += 1; }
        println!("{}", formatting::format_terminal(parts[0], state, reasons::reconcile_reason(parts[2])));
    }
    println!("{}", formatting::format_summary(running, summary::stopped_count(count, running)));
}
''',
            "reasons.rs": '''pub fn reconcile_reason(live: &str) -> &'static str {
    if live == "yes" { "authoritative-live" } else { "authoritative-dead" }
}
''',
            "summary.rs": '''pub fn stopped_count(total: i64, running: i64) -> i64 {
    total - running
}
''',
        },
    }
    task = {
        "id": "terminal_liveness_project",
        "title": "Reconcile persisted terminal state with authoritative liveness",
        "category": "state reconciliation across process lifecycle",
        "statement": "Fix the terminal-liveness regression using the read-only issue, architecture, and regression evidence. Preserve the existing input/output contract and do not modify read-only files.",
        "show_public_examples": False,
        "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
        "public_cases": [{
            "stdin": "4\nt1|running|no\nt2|running|yes\nt3|finished|yes\nt4|finished|no\n",
            "stdout": "id=t1|state=stopped|reason=authoritative-dead\nid=t2|state=running|reason=authoritative-live\nid=t3|state=running|reason=authoritative-live\nid=t4|state=stopped|reason=authoritative-dead\nrunning=2|stopped=2\n",
        }],
        "hidden_cases": [
            {"stdin": "1\nold|running|no\n", "stdout": "id=old|state=stopped|reason=authoritative-dead\nrunning=0|stopped=1\n"},
            {"stdin": "1\nrevived|finished|yes\n", "stdout": "id=revived|state=running|reason=authoritative-live\nrunning=1|stopped=0\n"},
            {"stdin": "2\na|running|yes\nb|running|no\n", "stdout": "id=a|state=running|reason=authoritative-live\nid=b|state=stopped|reason=authoritative-dead\nrunning=1|stopped=1\n"},
            {"stdin": "0\n", "stdout": "running=0|stopped=0\n"},
        ],
        "seed_files": seed_files,
        "context_files": symmetric_context(
            "# Terminal tracker shows stale running processes after external death\n\nPersisted UI state is a cache, not the authority. During reconciliation, current process liveness determines the displayed state: a live process is running even if the snapshot says finished, and a dead process is stopped even if the snapshot says running. Summary counts must use reconciled state.\n",
            "# Reconciliation flow\n\n`liveness` reconciles snapshot state with the authoritative process probe. `reasons` records the evidence source. `summary` derives counts. `formatting` owns stable records. `main` orchestrates. Repair reconciliation, not presentation or summary compensation.\n",
            "persisted running + dead probe -> stopped\npersisted finished + live probe -> running\nsummary counts reconciled states\nzero records still emits a zero summary\n",
        ),
    }
    fixes = {"parley": {"liveness.par": parley_fix}, "python": {"liveness.py": python_fix}, "rust": {"liveness.rs": rust_fix}}
    return task, fixes


def main() -> None:
    built = [redirect_task(), empty_collection_task(), forwarded_origin_task(), terminal_liveness_task()]
    tasks = [item[0] for item in built]
    fixes = {task["id"]: item[1] for task, item in zip(tasks, built)}
    roots = {
        "redirect_credential_scope_project": {"parley": "credentials.par", "python": "credentials.py", "rust": "credentials.rs"},
        "empty_collection_config_project": {"parley": "classification.par", "python": "classification.py", "rust": "classification.rs"},
        "forwarded_origin_project": {"parley": "origin.par", "python": "origin.py", "rust": "origin.rs"},
        "terminal_liveness_project": {"parley": "liveness.par", "python": "liveness.py", "rust": "liveness.rs"},
    }
    manifest = {
        "schema_version": 1,
        "description": "Four deeper five-module regressions with equal read-only evidence and explicit root-cause auditing.",
        "predeclared_analysis": {
            "experiment_id": "031",
            "scope": "Independent project episodes adapted from primary issue reports; each has five editable modules and three visibly read-only evidence files per language.",
            "primary_question": "When dependency navigation and state reconstruction dominate fixed prompt cost, does Parley match or beat both Python and Rust without language or instruction tuning?",
            "historical_sources": [
                {"task": "redirect_credential_scope_project", "url": "https://github.com/open-policy-agent/opa/issues/3093", "mechanism": "redirected Proxy-Authorization escaping its hop boundary"},
                {"task": "empty_collection_config_project", "url": "https://github.com/dotnet/extensions/issues/5858", "mechanism": "empty array collapsed into null/missing configuration state"},
                {"task": "forwarded_origin_project", "url": "https://github.com/oauth2-proxy/oauth2-proxy/issues/724", "mechanism": "external OAuth redirect origin lost behind a forwarded host"},
                {"task": "terminal_liveness_project", "url": "https://github.com/openai/codex/issues/12321", "mechanism": "persisted running terminals remain stale after process death"},
            ],
            "adaptation_rule": "Mechanisms and dependency shapes are adapted independently; no upstream source code, tests, names, or fixtures are copied.",
            "root_cause_files": roots,
            "root_cause_gate": "Every Parley assignment must change exactly its predeclared seeded defect file; caller or formatter compensation fails maintainability even if hidden output passes.",
            "change_rule": "No language change follows one project or efficiency delta. Eligibility requires a semantic failure recurring across independent projects, followed by general usefulness, semantic consistency, maintainability, and full regression coverage.",
            "instruction_rule": "Use the unchanged 1,519-character Parley skill. The one allowed instruction-compression experiment remains closed.",
        },
        "tasks": tasks,
    }
    reference = {
        "schema_version": 1,
        "description": "Unmeasured reference root fixes used only to validate the frozen iteration-031 corpus before preregistration.",
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
