# Full-stack agent study 043 — final execution freeze

This checkpoint freezes the complete measured execution path after the v0.5.4
product commit, semantics-only corpus commit, protocol preregistration, harness
implementation, and clean-room validation. It precedes every measured model
session.

## Zero-session evidence

- Measured sessions before this freeze: 0
- Harness commit: `9ca28d531197c69b5171c52b64c165b193faa767`
- Protocol revision before this amendment: 1
- Corpus task/case semantics changed after freeze: no
- Product/compiler/context changed after freeze: no
- Gate, models, reasoning, replicates, thresholds, or metrics changed: no

The clean-room reference run passed 16/16 task/language cells and all 144 named
cases. All 16 broken seeds built and failed public semantics. All eight
maintenance root boundaries passed. Every exact native/WASM build preserved
protected hashes. The orchestration smoke passed through parent-owned FIFO
feedback, HTTP, real Chromium, hidden judgment, cross-target agreement, and
final integrity. The rendered Parley prompt contains only the frozen 222-token
card; its fixed prompt difference from Python is 207 `o200k_base` tokens per
task.

## Scratch capacity and cleanup

The frozen four-worker budget requires 17,179,869,184 bytes free before any
journal is initialized: 8 GiB host reserve plus 2 GiB per worker. Clean-room
calibration recorded a maximum retained workspace of 161,170,519 bytes, so the
per-worker budget is 13.324× that observation and is not reduced.

Disposable workspaces and durable journal/attempt roots must be disjoint real
directories. Each cell's complete finished journal and external attempts are
persisted before `cleanup_finished_workspace` may remove the exact
immediate-child workspace. Cleanup evidence is independently journaled and
verified on resume. Observed free bytes are retained as evidence but excluded
from the static resume identity. The executor keeps at most four active cells
with no queued backlog, rechecks the full budget before every refill, and
records each workspace's retained bytes before cleanup. A capacity, boundary,
or cleanup error stops new scheduling, permanently seals all unstarted cells as
failures, fails execution integrity after measurement begins, and never permits
a rerun.

## Once-run boundary

The first measured invocation must use a clean repository at the committed
revision-2 protocol. Every cell receives exactly one start journal. A started
cell without a finished record becomes a permanent interruption failure; only
never-started cells may execute during resume. All outcomes are retained and
published. No same-corpus change or selective rerun is allowed.
