from identa.crustdata import Identified
from identa.workflow import decide_identity


def test_no_match_goes_to_human() -> None:
    assert decide_identity(Identified("d", None, None, None, None), 0.5) == "no match"


def test_below_threshold_goes_to_human() -> None:
    assert decide_identity(Identified("d", 1, 0.4, "n", "d"), 0.5) == "confidence below threshold"


def test_at_or_above_threshold_is_accepted() -> None:
    assert decide_identity(Identified("d", 1, 0.5, "n", "d"), 0.5) is None
