import base64

from identa.github import Reply
from identa.reconciler import classify_file, classify_prs
from identa.verdict import FileState, PrState


def pr(ref: str, state: str, base: str) -> dict[str, object]:
    return {"head": {"ref": ref}, "base": {"ref": base}, "state": state, "html_url": "u"}


def test_file_states() -> None:
    enc = base64.encodebytes(b"abc").decode()
    assert classify_file(Reply(404, {}), "abc") is FileState.MISSING
    assert classify_file(Reply(500, {}), "abc") is FileState.ERROR
    assert classify_file(Reply(200, {"content": enc}), "abc") is FileState.MATCHES
    assert classify_file(Reply(200, {"content": enc}), "abd") is FileState.MISMATCH


def test_pr_states() -> None:
    assert classify_prs(Reply(500, []), "b", "main") == (PrState.ERROR, None)
    assert classify_prs(Reply(200, []), "b", "main") == (PrState.NONE, None)
    assert classify_prs(Reply(200, [pr("x", "open", "main")]), "b", "main") == (PrState.NONE, None)
    assert classify_prs(Reply(200, [pr("b", "open", "main")]), "b", "main") == (
        PrState.OPEN_MATCHES,
        "u",
    )
    assert classify_prs(Reply(200, [pr("b", "closed", "main")]), "b", "main")[0] is PrState.MISMATCH
    two = [pr("b", "open", "main"), pr("b", "open", "main")]
    assert classify_prs(Reply(200, two), "b", "main")[0] is PrState.MISMATCH
    assert classify_prs(Reply(200, [pr("b", "open", "dev")]), "b", "main")[0] is PrState.MISMATCH
