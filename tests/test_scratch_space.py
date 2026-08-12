import json
from pathlib import Path

import pytest

from benchmarks.scratch_space import (
    DiskUsage,
    ScratchBoundaryError,
    ScratchBudget,
    ScratchCapacityError,
    cleanup_finished_workspace,
    preflight_scratch_space,
    validate_evidence_boundary,
)


def usage_with_free(free: int):
    return lambda _path: DiskUsage(total=100_000, used=100_000 - free, free=free)


def test_scratch_preflight_records_full_worker_budget(tmp_path):
    work = tmp_path / "work"
    journals = tmp_path / "journals"
    attempts = tmp_path / "attempts"
    journals.mkdir()
    attempts.mkdir()
    budget = ScratchBudget(max_workers=4, reserve_bytes=1_000, per_worker_bytes=250)

    record = preflight_scratch_space(
        work,
        budget,
        evidence_roots=[journals, attempts],
        usage_reader=usage_with_free(2_500),
    )

    assert record["status"] == "pass"
    assert record["required_free_bytes"] == 2_000
    assert record["headroom_bytes"] == 500
    assert record["evidence_roots"] == [
        str(journals.resolve()),
        str(attempts.resolve()),
    ]


def test_scratch_preflight_fails_before_measurement_when_under_budget(tmp_path):
    budget = ScratchBudget(max_workers=3, reserve_bytes=1_000, per_worker_bytes=500)

    with pytest.raises(ScratchCapacityError, match="before journaling"):
        preflight_scratch_space(
            tmp_path / "work",
            budget,
            usage_reader=usage_with_free(2_499),
        )


@pytest.mark.parametrize("relationship", ["equal", "evidence_inside", "work_inside"])
def test_scratch_boundary_rejects_overlapping_evidence(tmp_path, relationship):
    if relationship == "equal":
        work = evidence = tmp_path / "shared"
        work.mkdir()
    elif relationship == "evidence_inside":
        work = tmp_path / "work"
        evidence = work / "journal"
        evidence.mkdir(parents=True)
    else:
        evidence = tmp_path / "evidence"
        work = evidence / "work"
        work.mkdir(parents=True)

    with pytest.raises(ScratchBoundaryError):
        validate_evidence_boundary(work, [evidence])


def finished_record(path: Path, workspace: Path, *, status: str = "finished") -> None:
    path.write_text(
        json.dumps({"status": status, "result": {"workdir": str(workspace)}})
    )


def test_cleanup_removes_only_workspace_certified_by_finished_journal(tmp_path):
    work = tmp_path / "work"
    workspace = work / "cell-001"
    workspace.mkdir(parents=True)
    (workspace / "large-build.bin").write_bytes(b"x" * 32)
    journal = tmp_path / "cell-001.finished.json"
    finished_record(journal, workspace)

    record = cleanup_finished_workspace(work, workspace, journal)

    assert record["status"] == "removed"
    assert not workspace.exists()
    assert work.is_dir()
    assert journal.is_file()


def test_cleanup_refuses_mismatched_or_unfinished_evidence(tmp_path):
    work = tmp_path / "work"
    workspace = work / "cell-001"
    other = work / "cell-002"
    workspace.mkdir(parents=True)
    other.mkdir()
    mismatch = tmp_path / "mismatch.finished.json"
    unfinished = tmp_path / "unfinished.json"
    finished_record(mismatch, other)
    finished_record(unfinished, workspace, status="started")

    with pytest.raises(ScratchBoundaryError, match="does not match"):
        cleanup_finished_workspace(work, workspace, mismatch)
    with pytest.raises(ScratchBoundaryError, match="does not certify"):
        cleanup_finished_workspace(work, workspace, unfinished)

    assert workspace.is_dir()
    assert other.is_dir()


def test_cleanup_refuses_nested_target_and_workspace_symlink(tmp_path):
    work = tmp_path / "work"
    nested = work / "cell-001" / "nested"
    nested.mkdir(parents=True)
    nested_journal = tmp_path / "nested.finished.json"
    finished_record(nested_journal, nested)
    outside = tmp_path / "outside"
    outside.mkdir()
    symlink = work / "cell-link"
    symlink.symlink_to(outside, target_is_directory=True)
    symlink_journal = tmp_path / "link.finished.json"
    finished_record(symlink_journal, symlink)

    with pytest.raises(ScratchBoundaryError, match="immediate child"):
        cleanup_finished_workspace(work, nested, nested_journal)
    with pytest.raises(ScratchBoundaryError, match="must not be a symlink"):
        cleanup_finished_workspace(work, symlink, symlink_journal)

    assert nested.is_dir()
    assert outside.is_dir()
