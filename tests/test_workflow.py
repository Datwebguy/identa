from identa.crustdata import Identified
from identa.workflow import decide_identity


def test_no_match_goes_to_human() -> None:
    assert decide_identity(Identified("d", None, None, None, None), 0.5) == "no match"


def test_below_threshold_goes_to_human() -> None:
    assert decide_identity(Identified("d", 1, 0.4, "n", "d"), 0.5) == "confidence below threshold"


def test_at_or_above_threshold_is_accepted() -> None:
    assert decide_identity(Identified("d", 1, 0.5, "n", "d"), 0.5) is None


def test_tie_at_top_confidence_goes_to_human() -> None:
    found = Identified("d", 1, 0.9, "n", "d", tied=True)
    assert decide_identity(found, 0.5) == "tie at top confidence"


def test_crash_marker_sits_beside_the_store() -> None:
    from pathlib import Path

    from identa.config import Config
    from identa.workflow import crash_marker

    cfg = Config(0.0, "o", "r", "main", Path("/d/s.sqlite"), Path("e"), "n", "e@x", "vendor")
    assert crash_marker(cfg) == Path("/d/s.crashed")
