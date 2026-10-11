from pathlib import Path

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


def test_saved_enrich_is_reused(tmp_path: "Path") -> None:
    import json

    from identa.crustdata import find_saved_enrich

    assert find_saved_enrich(tmp_path, 7) is None
    rec = {
        "status": 200,
        "body": [{"matched_on": 7, "matches": [{"company_data": {"crustdata_company_id": 7}}]}],
    }
    (tmp_path / "20260101T000000000000Z-crustdata-enrich.json").write_text(json.dumps(rec))
    assert find_saved_enrich(tmp_path, 7) == {"crustdata_company_id": 7}
    assert find_saved_enrich(tmp_path, 8) is None
