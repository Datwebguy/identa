from identa.vendor import pr_title, render_vendor_file


def test_render_is_deterministic() -> None:
    assert render_vendor_file("5", "N", "d.x") == render_vendor_file(5, "N", "d.x")
    assert render_vendor_file(5, "N", "d.x") == ("crustdata_company_id: 5\ndomain: d.x\nname: N\n")


def test_title() -> None:
    assert pr_title("N", "d.x") == "Add vendor N (d.x)"
