from identa.measure import summarize


def test_counts_duplicates_per_company() -> None:
    s = summarize(
        ["vendor/1-aaaa", "vendor/2-bbbb", "vendor/2-cccc", "other/9-x"],
        ["vendor/1-aaaa", "vendor/2-bbbb", "vendor/2-cccc", "vendor/2-dddd"],
        "vendor",
    )
    assert (s.companies, s.branches, s.pull_requests) == (2, 3, 4)
    assert (s.duplicate_branches, s.duplicate_pull_requests) == (1, 2)
    assert s.per_company["2"] == {"branches": 2, "pull_requests": 3}
