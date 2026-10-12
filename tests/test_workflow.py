import json

import pytest

from identa.crustdata import Identified
from identa.workflow import _detail, choose_candidate, decide_identity


def test_no_match_goes_to_human() -> None:
    assert decide_identity(Identified("d", None, None, None, None), 0.5) == "no match"


def test_below_threshold_goes_to_human() -> None:
    assert decide_identity(Identified("d", 1, 0.4, "n", "d"), 0.5) == "confidence below threshold"


def test_at_or_above_threshold_is_accepted() -> None:
    assert decide_identity(Identified("d", 1, 0.5, "n", "d"), 0.5) is None


def test_tie_at_top_confidence_goes_to_human() -> None:
    found = Identified("d", 1, 0.9, "n", "d", ((1, "n", 0.9), (2, "m", 0.9)))
    assert decide_identity(found, 0.5) == "tie at top confidence"


def test_crash_marker_sits_beside_the_store() -> None:
    from pathlib import Path

    from identa.config import Config
    from identa.workflow import crash_marker

    cfg = Config(0.0, "o", "r", "main", Path("/d/s.sqlite"), Path("e"), "n", "e@x", "vendor")
    assert crash_marker(cfg) == Path("/d/s.crashed")


def test_tied_detail_lists_the_candidates() -> None:
    found = Identified("d", 1, 0.9, "n", "d", ((1, "n", 0.9), (2, "m", 0.9)))
    assert json.loads(_detail(found))["candidates"] == [
        {"company_id": 1, "name": "n", "confidence": 0.9},
        {"company_id": 2, "name": "m", "confidence": 0.9},
    ]


def test_untied_detail_has_no_candidates() -> None:
    assert "candidates" not in json.loads(
        _detail(Identified("d", 1, 0.9, "n", "d", ((1, "n", 0.9),)))
    )


def test_choose_candidate_picks_the_listed_company() -> None:
    found = Identified("d", 1, 0.9, "n", "d", ((1, "n", 0.9), (2, "m", 0.9)))
    chosen = choose_candidate(found, 2)
    assert (chosen.company_id, chosen.name, chosen.confidence) == (2, "m", 0.9)


def test_choose_candidate_refuses_an_unlisted_company() -> None:
    found = Identified("d", 1, 0.9, "n", "d", ((1, "n", 0.9), (2, "m", 0.9)))
    with pytest.raises(ValueError):
        choose_candidate(found, 3)
