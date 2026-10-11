"""Reconciliation verdicts, decided only from what GitHub reported for one exact branch name."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Verdict(StrEnum):
    APPLIED = "Applied"
    NOT_APPLIED = "NotApplied"
    UNKNOWN = "Unknown"
    RESUME = "Resume"


class Step(StrEnum):
    CREATE_BRANCH = "create_branch"
    COMMIT_FILE = "commit_file"
    OPEN_PR = "open_pr"


class FileState(StrEnum):
    MISSING = "missing"
    MATCHES = "matches"
    MISMATCH = "mismatch"
    ERROR = "error"


class PrState(StrEnum):
    NONE = "none"
    OPEN_MATCHES = "open_matches"
    MISMATCH = "mismatch"
    ERROR = "error"


@dataclass(frozen=True)
class Decision:
    verdict: Verdict
    resume_from: Step | None = None
    reason: str = ""


def decide(ref_status: int | None, file: FileState, pr: PrState) -> Decision:
    """Map GitHub's answers to a verdict.

    ref_status is the HTTP status of GET git/ref/heads/<branch>, or None if the call
    failed or timed out. file and pr are only consulted when the ref exists.
    """
    if ref_status == 404:
        return Decision(Verdict.NOT_APPLIED, reason="branch does not exist")
    if ref_status != 200:
        return Decision(Verdict.UNKNOWN, reason=f"branch check returned {ref_status}")
    if file is FileState.ERROR or pr is PrState.ERROR:
        return Decision(Verdict.UNKNOWN, reason="file or pull request check failed")
    if file is FileState.MISMATCH or pr is PrState.MISMATCH:
        return Decision(Verdict.UNKNOWN, reason="content does not match the intent")
    if file is FileState.MATCHES and pr is PrState.OPEN_MATCHES:
        return Decision(Verdict.APPLIED, reason="branch, file and pull request match")
    if file is FileState.MISSING and pr is PrState.NONE:
        return Decision(Verdict.RESUME, Step.COMMIT_FILE, "branch exists, file missing")
    if file is FileState.MATCHES and pr is PrState.NONE:
        return Decision(Verdict.RESUME, Step.OPEN_PR, "file committed, no pull request")
    return Decision(Verdict.UNKNOWN, reason="pull request exists without the expected file")
