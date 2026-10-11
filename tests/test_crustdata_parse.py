from identa.crustdata import Crustdata


def test_empty_matches_gives_no_company() -> None:
    r = Crustdata._parse("d.example", {"matches": []})
    assert r.company_id is None and r.confidence is None


def test_top_match_is_used() -> None:
    entry = {
        "matches": [
            {
                "confidence_score": 0.5,
                "company_data": {"crustdata_company_id": 9, "basic_info": {"name": "n"}},
            }
        ]
    }
    r = Crustdata._parse("d", entry)
    assert (r.company_id, r.confidence, r.name) == (9, 0.5, "n")
