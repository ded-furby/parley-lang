#!/usr/bin/env python3
"""Capacity and cleanup controls for future measured benchmark scratch roots."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
from typing import Any, Callable, NamedTuple


GIB = 1024**3
DEFAULT_RESERVE_BYTES = 8 * GIB
DEFAULT_PER_WORKER_BYTES = 2 * GIB


class ScratchCapacityError(RuntimeError):
    """Raised before measurement when the scratch filesystem is under budget."""


class ScratchBoundaryError(RuntimeError):
    """Raised when cleanup could escape the declared disposable root."""


class DiskUsage(NamedTuple):
    total: int
    used: int
    free: int


DiskUsageReader = Callable[[Path], DiskUsage]


@dataclass(frozen=True)
class ScratchBudget:
    """A conservative concurrency budget with a host safety reserve."""

    max_workers: int
    reserve_bytes: int = DEFAULT_RESERVE_BYTES
    per_worker_bytes: int = DEFAULT_PER_WORKER_BYTES

    def __post_init__(self) -> None:
        for field in ("max_workers", "reserve_bytes", "per_worker_bytes"):
            value = getattr(self, field)
            if not isinstance(value, int) or value < 1:
                raise ValueError(f"{field} must be a positive integer")

    @property
    def required_free_bytes(self) -> int:
        return self.reserve_bytes + self.max_workers * self.per_worker_bytes


def _usage(path: Path) -> DiskUsage:
    usage = shutil.disk_usage(path)
    return DiskUsage(usage.total, usage.used, usage.free)


def _resolved_directory(path: Path, *, create: bool) -> Path:
    if create:
        path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir() or path.is_symlink():
        raise ScratchBoundaryError(f"scratch root must be a real directory: {path}")
    return path.resolve()


def validate_evidence_boundary(
    work_root: Path,
    evidence_roots: list[Path] | tuple[Path, ...],
    *,
    create_work_root: bool = True,
) -> dict[str, Any]:
    """Prove that disposable scratch and durable evidence roots do not overlap."""

    resolved_work = _resolved_directory(work_root, create=create_work_root)
    resolved_evidence: list[Path] = []
    for root in evidence_roots:
        resolved = _resolved_directory(root, create=False)
        if resolved == resolved_work:
            raise ScratchBoundaryError(
                f"evidence root equals disposable work root: {resolved}"
            )
        if resolved_work in resolved.parents:
            raise ScratchBoundaryError(
                f"evidence root is inside disposable work root: {resolved}"
            )
        if resolved in resolved_work.parents:
            raise ScratchBoundaryError(
                f"disposable work root is inside evidence root: {resolved}"
            )
        resolved_evidence.append(resolved)
    if len(resolved_evidence) != len(set(resolved_evidence)):
        raise ScratchBoundaryError("evidence roots must be distinct")
    return {
        "work_root": str(resolved_work),
        "evidence_roots": [str(root) for root in resolved_evidence],
        "overlap": False,
    }


def preflight_scratch_space(
    work_root: Path,
    budget: ScratchBudget,
    *,
    evidence_roots: list[Path] | tuple[Path, ...] = (),
    usage_reader: DiskUsageReader = _usage,
) -> dict[str, Any]:
    """Refuse to start any measured cell unless the full worker budget is free."""

    boundary = validate_evidence_boundary(work_root, evidence_roots)
    resolved_work = Path(boundary["work_root"])
    usage = usage_reader(resolved_work)
    required = budget.required_free_bytes
    record = {
        "schema_version": 1,
        "status": "pass" if usage.free >= required else "fail",
        "work_root": str(resolved_work),
        "evidence_roots": boundary["evidence_roots"],
        "max_workers": budget.max_workers,
        "reserve_bytes": budget.reserve_bytes,
        "per_worker_bytes": budget.per_worker_bytes,
        "required_free_bytes": required,
        "filesystem_total_bytes": usage.total,
        "filesystem_used_bytes": usage.used,
        "filesystem_free_bytes": usage.free,
        "headroom_bytes": usage.free - required,
    }
    if usage.free < required:
        raise ScratchCapacityError(
            "scratch preflight failed before journaling: "
            f"free={usage.free} required={required} root={resolved_work}"
        )
    return record


def _finished_workspace(finished_record: Path) -> Path:
    if not finished_record.is_file() or finished_record.is_symlink():
        raise ScratchBoundaryError(
            f"finished journal must be a real file: {finished_record}"
        )
    try:
        payload = json.loads(finished_record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScratchBoundaryError(
            f"could not read finished journal: {finished_record}"
        ) from exc
    if payload.get("status") != "finished":
        raise ScratchBoundaryError(
            f"journal does not certify finished evidence: {finished_record}"
        )
    workdir = payload.get("result", {}).get("workdir")
    if not isinstance(workdir, str) or not workdir:
        raise ScratchBoundaryError(
            f"finished journal does not identify its workspace: {finished_record}"
        )
    return Path(workdir)


def cleanup_finished_workspace(
    work_root: Path,
    workspace: Path,
    finished_record: Path,
) -> dict[str, Any]:
    """Remove one immediate child only after durable finished evidence exists."""

    resolved_root = _resolved_directory(work_root, create=False)
    recorded_workspace = _finished_workspace(finished_record)
    if workspace.is_symlink():
        raise ScratchBoundaryError(f"managed workspace must not be a symlink: {workspace}")
    resolved_workspace = workspace.resolve(strict=True)
    if resolved_workspace.parent != resolved_root:
        raise ScratchBoundaryError(
            f"workspace is not an immediate child of scratch root: {resolved_workspace}"
        )
    if recorded_workspace.resolve(strict=True) != resolved_workspace:
        raise ScratchBoundaryError(
            "finished journal workspace does not match cleanup target: "
            f"{recorded_workspace} != {resolved_workspace}"
        )
    shutil.rmtree(resolved_workspace)
    return {
        "schema_version": 1,
        "status": "removed",
        "work_root": str(resolved_root),
        "workspace": str(resolved_workspace),
        "finished_record": str(finished_record.resolve()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--evidence-root", action="append", type=Path, default=[])
    parser.add_argument("--max-workers", type=int, required=True)
    parser.add_argument("--reserve-gib", type=int, default=8)
    parser.add_argument("--per-worker-gib", type=int, default=2)
    args = parser.parse_args(argv)
    record = preflight_scratch_space(
        args.work_root,
        ScratchBudget(
            max_workers=args.max_workers,
            reserve_bytes=args.reserve_gib * GIB,
            per_worker_bytes=args.per_worker_gib * GIB,
        ),
        evidence_roots=args.evidence_root,
    )
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
