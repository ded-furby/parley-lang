#!/usr/bin/env python3
"""Build the iteration-029 historically grounded diagnostic expansion."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


BENCHMARKS = Path(__file__).resolve().parent
BASE = BENCHMARKS / "agent_tasks_diagnostic_028.json"
ADDITIONS = BENCHMARKS / "agent_tasks_historical_additions_029.json"
OUTPUT = BENCHMARKS / "agent_tasks_historical_029.json"


def text(value: str) -> str:
    return dedent(value).lstrip("\n")


def symmetric_context(issue: str, regression: str) -> dict[str, dict[str, str]]:
    files = {"ISSUE.md": text(issue), "tests/regression.txt": text(regression)}
    return {language: dict(files) for language in ("parley", "python", "rust")}


def additions() -> list[dict]:
    return [
        {
            "id": "config_recovery_project",
            "title": "Preserve valid configuration beside unknown keys",
            "category": "configuration recovery and security policy",
            "statement": "Repair the configuration-recovery regression using the read-only issue and regression evidence. Preserve parsing, defaults, warning counts, and output fields. Do not modify files marked read-only.",
            "show_public_examples": False,
            "historical_inspiration": {
                "url": "https://github.com/openclaw/openclaw/issues/28140",
                "mechanism": "an unknown configuration key causes valid settings to be discarded in favor of defaults",
                "adaptation": "deterministic cross-language fixture; no upstream source copied",
            },
            "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
            "public_cases": [{
                "stdin": "3\nvisibility|all\nunknown_tool|enabled\naudit|on\n",
                "stdout": "visibility=all|audit=on|unknown=1\n",
            }],
            "hidden_cases": [
                {"stdin": "0\n", "stdout": "visibility=tree|audit=off|unknown=0\n"},
                {"stdin": "2\nvisibility|all\naudit|on\n", "stdout": "visibility=all|audit=on|unknown=0\n"},
                {"stdin": "2\nbad|x\nvisibility|team\n", "stdout": "visibility=team|audit=off|unknown=1\n"},
                {"stdin": "4\naudit|on\njunk|1\nvisibility|all\nother|2\n", "stdout": "visibility=all|audit=on|unknown=2\n"},
            ],
            "seed_files": {
                "parley": {
                    "formatting.par": text('''
                        to format_config with visibility as text, audit as text, unknown as number giving text:
                            give back "visibility=" + visibility + "|audit=" + audit + "|unknown=" + unknown
                    '''),
                    "main.par": text('''
                        include "policy.par"
                        include "formatting.par"

                        to main:
                            let count_input be ask for a number ""
                            let count be value of count_input
                            let visibility be "tree"
                            let audit be "off"
                            let unknown be 0
                            repeat count times:
                                let parts be (ask "") split by "|"
                                let key be item 1 of parts
                                let setting be item 2 of parts
                                if key is "visibility":
                                    set visibility to setting
                                otherwise if key is "audit":
                                    set audit to setting
                                otherwise:
                                    set unknown to unknown + 1
                            let final_visibility be (recover_visibility with visibility, unknown)
                            let final_audit be (recover_audit with audit, unknown)
                            say (format_config with final_visibility, final_audit, unknown)
                    '''),
                    "policy.par": text('''
                        to recover_visibility with visibility as text, unknown as number giving text:
                            if unknown is more than 0:
                                give back "tree"
                            give back visibility

                        to recover_audit with audit as text, unknown as number giving text:
                            if unknown is more than 0:
                                give back "off"
                            give back audit
                    '''),
                },
                "python": {
                    "formatting.py": text('''
                        def format_config(visibility: str, audit: str, unknown: int) -> str:
                            return f"visibility={visibility}|audit={audit}|unknown={unknown}"
                    '''),
                    "main.py": text('''
                        from formatting import format_config
                        from policy import recover_audit, recover_visibility

                        count = int(input())
                        visibility = "tree"
                        audit = "off"
                        unknown = 0
                        for _ in range(count):
                            key, setting = input().split("|", 1)
                            if key == "visibility":
                                visibility = setting
                            elif key == "audit":
                                audit = setting
                            else:
                                unknown += 1
                        print(format_config(
                            recover_visibility(visibility, unknown),
                            recover_audit(audit, unknown),
                            unknown,
                        ))
                    '''),
                    "policy.py": text('''
                        def recover_visibility(visibility: str, unknown: int) -> str:
                            return "tree" if unknown > 0 else visibility

                        def recover_audit(audit: str, unknown: int) -> str:
                            return "off" if unknown > 0 else audit
                    '''),
                },
                "rust": {
                    "formatting.rs": text('''
                        pub fn format_config(visibility: &str, audit: &str, unknown: i64) -> String {
                            format!("visibility={visibility}|audit={audit}|unknown={unknown}")
                        }
                    '''),
                    "main.rs": text('''
                        mod formatting;
                        mod policy;

                        use formatting::format_config;
                        use policy::{recover_audit, recover_visibility};
                        use std::io::{self, Read};

                        fn main() {
                            let mut input = String::new();
                            io::stdin().read_to_string(&mut input).unwrap();
                            let mut lines = input.lines();
                            let count: usize = lines.next().unwrap().parse().unwrap();
                            let mut visibility = "tree";
                            let mut audit = "off";
                            let mut unknown = 0;
                            for _ in 0..count {
                                let mut parts = lines.next().unwrap().splitn(2, '|');
                                let key = parts.next().unwrap();
                                let setting = parts.next().unwrap();
                                match key {
                                    "visibility" => visibility = setting,
                                    "audit" => audit = setting,
                                    _ => unknown += 1,
                                }
                            }
                            println!("{}", format_config(
                                recover_visibility(visibility, unknown),
                                recover_audit(audit, unknown),
                                unknown,
                            ));
                        }
                    '''),
                    "policy.rs": text('''
                        pub fn recover_visibility(visibility: &str, unknown: i64) -> &str {
                            if unknown > 0 { "tree" } else { visibility }
                        }

                        pub fn recover_audit(audit: &str, unknown: i64) -> &str {
                            if unknown > 0 { "off" } else { audit }
                        }
                    '''),
                },
            },
            "context_files": symmetric_context(
                '''
                # Unknown key erases valid configuration

                A forward-compatibility warning should count unknown keys without discarding recognized, valid settings from the same document. Defaults apply only when a recognized setting is absent. The current service reports the warning but silently restores every default.
                ''',
                '''
                visibility=all + unknown key + audit=on -> keep all and on; unknown=1
                unknown key + visibility=team -> keep team and default audit; unknown=1
                empty document -> visibility tree, audit off, unknown=0
                ''',
            ),
        },
        {
            "id": "aliased_identity_cache_project",
            "title": "Normalize aliased identity fields into cache keys",
            "category": "cache identity and response aliasing",
            "statement": "Repair the cache-identity regression using the read-only issue and regression evidence. Preserve record order, duplicate accounting, and output fields. Do not modify files marked read-only.",
            "show_public_examples": False,
            "historical_inspiration": {
                "url": "https://github.com/apollographql/apollo-client/issues/10599",
                "mechanism": "an aliased id response field is not normalized into the entity cache identity",
                "adaptation": "deterministic cross-language fixture; no upstream source copied",
            },
            "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
            "public_cases": [{
                "stdin": "3\nPerson|id|personId|1\nPerson|id|id|2\nPerson|id|personId|1\n",
                "stdout": "stored=Person:1\nstored=Person:2\nduplicate=Person:1\nentries=2|duplicates=1|uncached=0\n",
            }],
            "hidden_cases": [
                {"stdin": "0\n", "stdout": "entries=0|duplicates=0|uncached=0\n"},
                {"stdin": "2\nUser|id|id|7\nUser|id|id|8\n", "stdout": "stored=User:7\nstored=User:8\nentries=2|duplicates=0|uncached=0\n"},
                {"stdin": "2\nUser|name|name|Ada\nUser|id|userId|7\n", "stdout": "uncached\nstored=User:7\nentries=1|duplicates=0|uncached=1\n"},
                {"stdin": "3\nNode|id|nodeId|4\nNode|id|identifier|4\nNode|id|id|4\n", "stdout": "stored=Node:4\nduplicate=Node:4\nduplicate=Node:4\nentries=1|duplicates=2|uncached=0\n"},
            ],
            "seed_files": {
                "parley": {
                    "formatting.par": text('''
                        to format_cache_counts with entries as number, duplicates as number, uncached as number giving text:
                            give back "entries=" + entries + "|duplicates=" + duplicates + "|uncached=" + uncached
                    '''),
                    "identity.par": text('''
                        to entity_key with kind as text, source_field as text, response_field as text, value as text giving text:
                            if response_field is not "id":
                                give back ""
                            give back kind + ":" + value
                    '''),
                    "main.par": text('''
                        include "identity.par"
                        include "formatting.par"

                        to main:
                            let count_input be ask for a number ""
                            let count be value of count_input
                            let seen be an empty list of text
                            let duplicates be 0
                            let uncached be 0
                            repeat count times:
                                let parts be (ask "") split by "|"
                                let key be (entity_key with item 1 of parts, item 2 of parts, item 3 of parts, item 4 of parts)
                                if key is "":
                                    set uncached to uncached + 1
                                    say "uncached"
                                otherwise if seen contains key:
                                    set duplicates to duplicates + 1
                                    say "duplicate=" + key
                                otherwise:
                                    add key to seen
                                    say "stored=" + key
                            say (format_cache_counts with length of seen, duplicates, uncached)
                    '''),
                },
                "python": {
                    "formatting.py": text('''
                        def format_cache_counts(entries: int, duplicates: int, uncached: int) -> str:
                            return f"entries={entries}|duplicates={duplicates}|uncached={uncached}"
                    '''),
                    "identity.py": text('''
                        def entity_key(kind: str, source_field: str, response_field: str, value: str) -> str:
                            if response_field != "id":
                                return ""
                            return f"{kind}:{value}"
                    '''),
                    "main.py": text('''
                        from formatting import format_cache_counts
                        from identity import entity_key

                        count = int(input())
                        seen = set()
                        duplicates = 0
                        uncached = 0
                        for _ in range(count):
                            kind, source_field, response_field, value = input().split("|", 3)
                            key = entity_key(kind, source_field, response_field, value)
                            if not key:
                                uncached += 1
                                print("uncached")
                            elif key in seen:
                                duplicates += 1
                                print(f"duplicate={key}")
                            else:
                                seen.add(key)
                                print(f"stored={key}")
                        print(format_cache_counts(len(seen), duplicates, uncached))
                    '''),
                },
                "rust": {
                    "formatting.rs": text('''
                        pub fn format_cache_counts(entries: usize, duplicates: usize, uncached: usize) -> String {
                            format!("entries={entries}|duplicates={duplicates}|uncached={uncached}")
                        }
                    '''),
                    "identity.rs": text('''
                        pub fn entity_key(kind: &str, _source_field: &str, response_field: &str, value: &str) -> String {
                            if response_field != "id" { return String::new(); }
                            format!("{kind}:{value}")
                        }
                    '''),
                    "main.rs": text('''
                        mod formatting;
                        mod identity;

                        use formatting::format_cache_counts;
                        use identity::entity_key;
                        use std::collections::HashSet;
                        use std::io::{self, Read};

                        fn main() {
                            let mut input = String::new();
                            io::stdin().read_to_string(&mut input).unwrap();
                            let mut lines = input.lines();
                            let count: usize = lines.next().unwrap().parse().unwrap();
                            let mut seen = HashSet::new();
                            let (mut duplicates, mut uncached) = (0, 0);
                            for _ in 0..count {
                                let mut parts = lines.next().unwrap().splitn(4, '|');
                                let key = entity_key(
                                    parts.next().unwrap(), parts.next().unwrap(),
                                    parts.next().unwrap(), parts.next().unwrap(),
                                );
                                if key.is_empty() {
                                    uncached += 1;
                                    println!("uncached");
                                } else if seen.contains(&key) {
                                    duplicates += 1;
                                    println!("duplicate={key}");
                                } else {
                                    println!("stored={key}");
                                    seen.insert(key);
                                }
                            }
                            println!("{}", format_cache_counts(seen.len(), duplicates, uncached));
                        }
                    '''),
                },
            },
            "context_files": symmetric_context(
                '''
                # Aliased id is missing from the normalized cache

                Entity identity comes from the source field named id, regardless of the response alias chosen by a query. Records whose id is returned as personId or another alias should share the same Kind:value key with an unaliased response. Non-id source fields remain uncacheable.
                ''',
                '''
                Person id returned as personId with value 1 -> stored Person:1
                same Person id returned under a different alias -> duplicate Person:1
                source field name with value Ada -> uncached
                ''',
            ),
        },
        {
            "id": "fsm_rollback_project",
            "title": "Restore termination state when rolling back an FSM",
            "category": "state-machine rollback",
            "statement": "Repair the matcher rollback regression using the read-only issue and regression evidence. Preserve command parsing, event order, and summary fields. Do not modify files marked read-only.",
            "show_public_examples": False,
            "historical_inspiration": {
                "url": "https://github.com/vllm-project/vllm/issues/27210",
                "mechanism": "rollback rewinds position but leaves a termination flag set",
                "adaptation": "deterministic cross-language fixture; no upstream source copied",
            },
            "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
            "public_cases": [{
                "stdin": "4\naccept|word\naccept|stop\nrollback|stop\naccept|word\n",
                "stdout": "accept\naccept\nrollback\naccept\nprocessed=2|terminated=no|rejected=0\n",
            }],
            "hidden_cases": [
                {"stdin": "0\n", "stdout": "processed=0|terminated=no|rejected=0\n"},
                {"stdin": "2\naccept|word\naccept|word\n", "stdout": "accept\naccept\nprocessed=2|terminated=no|rejected=0\n"},
                {"stdin": "3\naccept|stop\naccept|word\nrollback|stop\n", "stdout": "accept\nreject\nrollback\nprocessed=0|terminated=no|rejected=1\n"},
                {"stdin": "5\naccept|word\naccept|stop\nrollback|stop\naccept|stop\naccept|word\n", "stdout": "accept\naccept\nrollback\naccept\nreject\nprocessed=2|terminated=yes|rejected=1\n"},
            ],
            "seed_files": {
                "parley": {
                    "formatting.par": text('''
                        to format_matcher with processed as number, terminated as yesno, rejected as number giving text:
                            give back "processed=" + processed + "|terminated=" + terminated + "|rejected=" + rejected
                    '''),
                    "main.par": text('''
                        include "matcher.par"
                        include "formatting.par"

                        to main:
                            let count_input be ask for a number ""
                            let count be value of count_input
                            let processed be 0
                            let terminated be no
                            let rejected be 0
                            repeat count times:
                                let parts be (ask "") split by "|"
                                let action be item 1 of parts
                                let token be item 2 of parts
                                if action is "accept":
                                    if (can_accept with terminated):
                                        set processed to processed + 1
                                        if token is "stop":
                                            set terminated to yes
                                        say "accept"
                                    otherwise:
                                        set rejected to rejected + 1
                                        say "reject"
                                otherwise:
                                    if processed is more than 0:
                                        set processed to processed - 1
                                    set terminated to (termination_after_rollback with terminated, token)
                                    say "rollback"
                            say (format_matcher with processed, terminated, rejected)
                    '''),
                    "matcher.par": text('''
                        to can_accept with terminated as yesno giving yesno:
                            if terminated:
                                give back no
                            give back yes

                        to termination_after_rollback with terminated as yesno, removed_token as text giving yesno:
                            give back terminated
                    '''),
                },
                "python": {
                    "formatting.py": text('''
                        def format_matcher(processed: int, terminated: bool, rejected: int) -> str:
                            state = "yes" if terminated else "no"
                            return f"processed={processed}|terminated={state}|rejected={rejected}"
                    '''),
                    "main.py": text('''
                        from formatting import format_matcher
                        from matcher import can_accept, termination_after_rollback

                        count = int(input())
                        processed = 0
                        terminated = False
                        rejected = 0
                        for _ in range(count):
                            action, token = input().split("|", 1)
                            if action == "accept":
                                if can_accept(terminated):
                                    processed += 1
                                    terminated = terminated or token == "stop"
                                    print("accept")
                                else:
                                    rejected += 1
                                    print("reject")
                            else:
                                processed = max(processed - 1, 0)
                                terminated = termination_after_rollback(terminated, token)
                                print("rollback")
                        print(format_matcher(processed, terminated, rejected))
                    '''),
                    "matcher.py": text('''
                        def can_accept(terminated: bool) -> bool:
                            return not terminated

                        def termination_after_rollback(terminated: bool, removed_token: str) -> bool:
                            return terminated
                    '''),
                },
                "rust": {
                    "formatting.rs": text('''
                        pub fn format_matcher(processed: i64, terminated: bool, rejected: i64) -> String {
                            let state = if terminated { "yes" } else { "no" };
                            format!("processed={processed}|terminated={state}|rejected={rejected}")
                        }
                    '''),
                    "main.rs": text('''
                        mod formatting;
                        mod matcher;

                        use formatting::format_matcher;
                        use matcher::{can_accept, termination_after_rollback};
                        use std::io::{self, Read};

                        fn main() {
                            let mut input = String::new();
                            io::stdin().read_to_string(&mut input).unwrap();
                            let mut lines = input.lines();
                            let count: usize = lines.next().unwrap().parse().unwrap();
                            let (mut processed, mut rejected) = (0, 0);
                            let mut terminated = false;
                            for _ in 0..count {
                                let mut parts = lines.next().unwrap().splitn(2, '|');
                                let action = parts.next().unwrap();
                                let token = parts.next().unwrap();
                                if action == "accept" {
                                    if can_accept(terminated) {
                                        processed += 1;
                                        terminated = terminated || token == "stop";
                                        println!("accept");
                                    } else {
                                        rejected += 1;
                                        println!("reject");
                                    }
                                } else {
                                    processed = std::cmp::max(processed - 1, 0);
                                    terminated = termination_after_rollback(terminated, token);
                                    println!("rollback");
                                }
                            }
                            println!("{}", format_matcher(processed, terminated, rejected));
                        }
                    '''),
                    "matcher.rs": text('''
                        pub fn can_accept(terminated: bool) -> bool {
                            !terminated
                        }

                        pub fn termination_after_rollback(terminated: bool, _removed_token: &str) -> bool {
                            terminated
                        }
                    '''),
                },
            },
            "context_files": symmetric_context(
                '''
                # Rollback rewinds position but not termination

                After a terminating token is removed by rollback, the matcher must become active again. The current position rewinds, yet later valid tokens are rejected because the terminated state survives. Rolling back a non-terminating token does not independently clear a real termination state.
                ''',
                '''
                accept word, accept stop, rollback stop, accept word -> final token accepted; terminated no
                accept stop, accept word -> second token rejected
                removing stop is the state transition that clears termination
                ''',
            ),
        },
        {
            "id": "cancellation_lock_project",
            "title": "Retain lock authority during cancellation rollback",
            "category": "cancellation and rollback authority",
            "statement": "Repair the cancellation rollback regression using the read-only issue and regression evidence. Preserve change order, lock semantics, and summary fields. Do not modify files marked read-only.",
            "show_public_examples": False,
            "historical_inspiration": {
                "url": "https://github.com/vitessio/vitess/issues/17620",
                "mechanism": "cancellation creates fresh context and loses lock authority required to restore state",
                "adaptation": "deterministic cross-language fixture; no upstream source copied",
            },
            "entrypoints": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
            "public_cases": [{
                "stdin": "yes\n3\ncatalog|old|new\nsearch|ready|paused\nbilling|open|closed\n",
                "stdout": "catalog:old\nsearch:ready\nbilling:open\nrestored=3|failed=0\n",
            }],
            "hidden_cases": [
                {"stdin": "yes\n0\n", "stdout": "restored=0|failed=0\n"},
                {"stdin": "yes\n2\na|one|two\nb|left|right\n", "stdout": "a:one\nb:left\nrestored=2|failed=0\n"},
                {"stdin": "no\n1\na|old|new\n", "stdout": "a:new\nrestored=0|failed=1\n"},
                {"stdin": "no\n2\nx|up|down\ny|hot|cold\n", "stdout": "x:down\ny:cold\nrestored=0|failed=2\n"},
            ],
            "seed_files": {
                "parley": {
                    "cancellation.par": text('''
                        to rollback_has_lock with original_lock as yesno giving yesno:
                            give back no
                    '''),
                    "formatting.par": text('''
                        to format_rollback with restored as number, failed as number giving text:
                            give back "restored=" + restored + "|failed=" + failed
                    '''),
                    "main.par": text('''
                        include "cancellation.par"
                        include "formatting.par"

                        to main:
                            let original_lock be (ask "") is "yes"
                            let count_input be ask for a number ""
                            let count be value of count_input
                            let restored be 0
                            let failed be 0
                            repeat count times:
                                let parts be (ask "") split by "|"
                                let resource be item 1 of parts
                                let old_value be item 2 of parts
                                let new_value be item 3 of parts
                                if (rollback_has_lock with original_lock):
                                    say resource + ":" + old_value
                                    set restored to restored + 1
                                otherwise:
                                    say resource + ":" + new_value
                                    set failed to failed + 1
                            say (format_rollback with restored, failed)
                    '''),
                },
                "python": {
                    "cancellation.py": text('''
                        def rollback_has_lock(original_lock: bool) -> bool:
                            return False
                    '''),
                    "formatting.py": text('''
                        def format_rollback(restored: int, failed: int) -> str:
                            return f"restored={restored}|failed={failed}"
                    '''),
                    "main.py": text('''
                        from cancellation import rollback_has_lock
                        from formatting import format_rollback

                        original_lock = input() == "yes"
                        count = int(input())
                        restored = 0
                        failed = 0
                        for _ in range(count):
                            resource, old_value, new_value = input().split("|", 2)
                            if rollback_has_lock(original_lock):
                                print(f"{resource}:{old_value}")
                                restored += 1
                            else:
                                print(f"{resource}:{new_value}")
                                failed += 1
                        print(format_rollback(restored, failed))
                    '''),
                },
                "rust": {
                    "cancellation.rs": text('''
                        pub fn rollback_has_lock(_original_lock: bool) -> bool {
                            false
                        }
                    '''),
                    "formatting.rs": text('''
                        pub fn format_rollback(restored: i64, failed: i64) -> String {
                            format!("restored={restored}|failed={failed}")
                        }
                    '''),
                    "main.rs": text('''
                        mod cancellation;
                        mod formatting;

                        use cancellation::rollback_has_lock;
                        use formatting::format_rollback;
                        use std::io::{self, Read};

                        fn main() {
                            let mut input = String::new();
                            io::stdin().read_to_string(&mut input).unwrap();
                            let mut lines = input.lines();
                            let original_lock = lines.next().unwrap() == "yes";
                            let count: usize = lines.next().unwrap().parse().unwrap();
                            let (mut restored, mut failed) = (0, 0);
                            for _ in 0..count {
                                let mut parts = lines.next().unwrap().splitn(3, '|');
                                let resource = parts.next().unwrap();
                                let old_value = parts.next().unwrap();
                                let new_value = parts.next().unwrap();
                                if rollback_has_lock(original_lock) {
                                    println!("{resource}:{old_value}");
                                    restored += 1;
                                } else {
                                    println!("{resource}:{new_value}");
                                    failed += 1;
                                }
                            }
                            println!("{}", format_rollback(restored, failed));
                        }
                    '''),
                },
            },
            "context_files": symmetric_context(
                '''
                # Cancellation cannot restore state after losing its lock

                Best-effort rollback must retain the original operation's lock authority. The current cancellation path creates isolated rollback state, so every restore is rejected even though the original operation still owns the lock. If the original operation truly has no lock, restoration must continue to fail.
                ''',
                '''
                original lock yes -> every changed resource returns to its old value
                original lock no -> each resource remains at the new value and counts as failed
                zero resources -> restored=0,failed=0
                ''',
            ),
        },
    ]


def main() -> None:
    base = json.loads(BASE.read_text(encoding="utf-8"))
    new_tasks = additions()
    additions_payload = {
        "schema_version": 1,
        "description": "Four historically grounded, synthetic project regressions for iteration 029.",
        "tasks": new_tasks,
    }
    tasks = [*base["tasks"], *new_tasks]
    ids = [task["id"] for task in tasks]
    if len(tasks) != 8 or len(ids) != len(set(ids)):
        raise ValueError("iteration 029 requires eight unique diagnostic repositories")
    combined = {
        "schema_version": 1,
        "description": "Eight project-style regression repairs with equal read-only evidence and explicit root-cause auditing.",
        "predeclared_analysis": {
            "experiment_id": "029",
            "matrix": "8 diagnostic repositories x 3 languages x 6 complete-bundle replicates = 18 fresh sessions and 144 hidden-judged assignments",
            "seed": 20260821,
            "scope": "The four iteration-028 repositories are preserved exactly. Four historically grounded synthetic additions require dependency navigation across configuration, cache identity, state rollback, and cancellation authority.",
            "primary_question": "Does Parley match or beat both baselines when project-style diagnosis expands to eight unrelated regressions under equal read-only evidence?",
            "root_cause_gate": "Every Parley assignment must change its predeclared seeded defect file; caller-side compensation remains hidden-correct but fails this maintainability condition.",
            "root_cause_files": {
                "invoice_boundary_project": {"parley": "pricing.par", "python": "pricing.py", "rust": "pricing.rs"},
                "after_hours_routing_project": {"parley": "routing.par", "python": "routing.py", "rust": "routing.rs"},
                "normalized_tag_project": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
                "capacity_state_project": {"parley": "main.par", "python": "main.py", "rust": "main.rs"},
                "config_recovery_project": {"parley": "policy.par", "python": "policy.py", "rust": "policy.rs"},
                "aliased_identity_cache_project": {"parley": "identity.par", "python": "identity.py", "rust": "identity.rs"},
                "fsm_rollback_project": {"parley": "matcher.par", "python": "matcher.py", "rust": "matcher.rs"},
                "cancellation_lock_project": {"parley": "cancellation.par", "python": "cancellation.py", "rust": "cancellation.rs"}
            },
            "change_rule": "Preserve all output. No language change follows one repository, transcript, session, or token gap. Proposals require recurrence across unrelated projects and independent sessions, then general usefulness, semantic consistency, and maintainability.",
            "instruction_rule": "Use the unchanged 1,519-character Parley skill. The one allowed instruction-compression experiment remains closed.",
        },
        "tasks": tasks,
    }
    ADDITIONS.write_text(json.dumps(additions_payload, indent=2) + "\n", encoding="utf-8")
    OUTPUT.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
