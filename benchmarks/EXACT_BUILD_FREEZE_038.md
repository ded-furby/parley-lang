# Exact-build freeze preflight for iteration 038

Status: execution-mechanism work only. No iteration-038 task, case, formula,
route, field, scaffold, model prompt, or comparison threshold exists at this
checkpoint.

Iteration 037 proved that `cargo metadata --locked --offline` is not a strong
enough read-only preflight. It accepted a semantically correct but
noncanonically ordered lockfile; the later measured `cargo build` rewrote that
file in all Rust cells.

`exact_build_freeze.py` closes that gap. It captures the content hash, size,
mode, device, and inode of every declared read-only input, rejects symlinks,
runs an exact argv command, and captures the same inputs immediately afterward.
Any content, size, mode, type, missing-file, command, or timeout failure stops
the sequence and fails the gate. A stable inode is recorded for audit but is not
required because some build tools may atomically replace an identical file.

The task-free 038 smoke uses the same pinned Rust dependency surface and the
same native-release plus WASM-release command shapes as the full-stack study.
It proves three things before corpus design:

1. A lock generated from the final smoke manifest survives both exact build
   paths byte-for-byte.
2. Moving the root package block to a noncanonical location still passes the
   old `cargo metadata --locked --offline` probe without a hash change.
3. The iteration-037 command `cargo build --release` succeeds but canonicalizes
   that lock, and the new validator rejects the mutation. The future smoke uses
   explicit `--locked --offline` flags as well as post-command hashes.

The saved evidence is `exact_build_freeze_038_smoke.json`. This preflight does
not repair, rejudge, or rerun any iteration-037 agent cell and is not language
performance evidence. Once committed, an independent 038 corpus can be frozen;
its later reference validator must call this mechanism with the exact build
commands and complete protected/read-only file set before measurement.
