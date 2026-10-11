from pathlib import Path

from identa.store import COMPLETED, PENDING, Store


def make(tmp_path: Path) -> Store:
    return Store(tmp_path / "s.sqlite")


def test_intent_written_once(tmp_path: Path) -> None:
    s = make(tmp_path)
    assert s.write_intent("k", "1", "a", "{}", "{}", "vendor/1-k") is True
    assert s.write_intent("k", "1", "a", "{}", "{}", "vendor/1-k") is False
    intent = s.get_intent("k")
    assert intent is not None and intent.state == PENDING


def test_unfinished_excludes_completed(tmp_path: Path) -> None:
    s = make(tmp_path)
    s.write_intent("k1", "1", "a", "{}", "{}", "b1")
    s.write_intent("k2", "2", "a", "{}", "{}", "b2")
    s.commit_outcome("k1", "url", "{}")
    assert [i.key for i in s.unfinished()] == ["k2"]
    got = s.get_intent("k1")
    assert got is not None and got.state == COMPLETED
    assert s.outcome_pr_url("k1") == "url"


def test_state_survives_reopen(tmp_path: Path) -> None:
    s = make(tmp_path)
    s.write_intent("k", "1", "a", "{}", "{}", "b")
    s.log_step("k", "create_branch", "started")
    s.close()
    s2 = make(tmp_path)
    assert [i.key for i in s2.unfinished()] == ["k"]
    assert s2.steps("k") == [("create_branch", "started")]


def test_human_queue(tmp_path: Path) -> None:
    s = make(tmp_path)
    s.enqueue_human(None, "d", "no match", "{}")
    assert [r["reason"] for r in s.human_queue()] == ["no match"]


def test_find_by_company_and_set_state(tmp_path: Path) -> None:
    s = make(tmp_path)
    assert s.find_by_company("1", "a") is None
    s.write_intent("k", "1", "a", "{}", "{}", "b")
    found = s.find_by_company("1", "a")
    assert found is not None and found.key == "k"
    s.set_state("k", "needs_human")
    assert s.unfinished() == []
