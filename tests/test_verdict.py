import pytest

from identa.verdict import FileState, PrState, Step, Verdict, decide


def test_404_is_not_applied() -> None:
    assert decide(404, FileState.MISSING, PrState.NONE).verdict is Verdict.NOT_APPLIED


@pytest.mark.parametrize("status", [None, 401, 403, 500, 502])
def test_other_ref_status_is_unknown(status: int | None) -> None:
    assert decide(status, FileState.MATCHES, PrState.OPEN_MATCHES).verdict is Verdict.UNKNOWN


def test_all_match_is_applied() -> None:
    assert decide(200, FileState.MATCHES, PrState.OPEN_MATCHES).verdict is Verdict.APPLIED


def test_branch_without_file_resumes_at_file() -> None:
    d = decide(200, FileState.MISSING, PrState.NONE)
    assert (d.verdict, d.resume_from) == (Verdict.RESUME, Step.COMMIT_FILE)


def test_file_without_pr_resumes_at_pr() -> None:
    d = decide(200, FileState.MATCHES, PrState.NONE)
    assert (d.verdict, d.resume_from) == (Verdict.RESUME, Step.OPEN_PR)


@pytest.mark.parametrize(
    ("file", "pr"),
    [
        (FileState.ERROR, PrState.NONE),
        (FileState.MATCHES, PrState.ERROR),
        (FileState.MISMATCH, PrState.NONE),
        (FileState.MATCHES, PrState.MISMATCH),
        (FileState.MISSING, PrState.OPEN_MATCHES),
    ],
)
def test_ambiguous_is_unknown(file: FileState, pr: PrState) -> None:
    assert decide(200, file, pr).verdict is Verdict.UNKNOWN
