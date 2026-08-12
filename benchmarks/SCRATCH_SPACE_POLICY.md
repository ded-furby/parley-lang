# Measured benchmark scratch-space policy

This policy applies to full-stack studies after iteration 040. It does not
alter or reinterpret any frozen historical runner or result.

## Failure being prevented

Iteration 040 accumulated disposable native and WebAssembly build workspaces
until the host filesystem returned ENOSPC. Five frozen cells were affected and
the once-run comparison was correctly published as invalidated. The generic
control must prevent a new measured cell from starting when the whole planned
worker pool lacks safe disk headroom, and it must reclaim completed cell
workspaces without touching durable evidence.

## Frozen inputs for a future protocol

A successor protocol must record these values before measurement:

- the resolved disposable `work_root`;
- every durable evidence root, including journals and parent attempt records;
- `max_workers`;
- host reserve bytes;
- estimated peak scratch bytes per active worker; and
- the SHA-256 of `benchmarks/scratch_space.py`.

The default policy requires 8 GiB of host reserve plus 2 GiB for every active
worker. With four workers, no journal may be initialized unless at least 16 GiB
is free on the scratch filesystem. A protocol may choose a larger preregistered
budget after clean-room calibration, but may not lower it after measured cells
start.

## Evidence boundary

Disposable workspaces and durable evidence must be disjoint real directories:
neither may equal, contain, or be contained by the other. Journal and attempt
records remain outside `work_root`. Source snapshots, agent output, build
diagnostics, exact-build checks, and public/hidden outcomes must be embedded in
the finished journal record before cleanup.

`cleanup_finished_workspace` removes only a real immediate child of the
declared work root, only when a real finished journal identifies that exact
workspace. It refuses symlinks, missing or non-finished journals, mismatched
paths, nested targets, and root-level targets. This keeps cleanup bounded and
recoverable from independently retained evidence.

## Execution order

1. Create or resolve the empty disposable work root and existing evidence
   roots.
2. Run `preflight_scratch_space` before initializing any measured journal.
3. If capacity is below the frozen full-worker budget, abort with no started
   cells. Free space may be reclaimed only from explicitly identified inactive
   scratch roots; never delete repository files, journals, attempts, or raw
   results.
4. Run each cell once under the frozen protocol.
5. Atomically persist its finished journal and external attempt evidence.
6. Remove that cell's disposable workspace through
   `cleanup_finished_workspace`.
7. Preserve the preflight record in the final raw result and audit it against
   the frozen budget.

Cleanup failure is an execution-integrity failure. It must stop scheduling new
cells before capacity becomes unsafe; it never authorizes rerunning a started
cell.
