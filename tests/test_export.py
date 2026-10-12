from pathlib import Path

from identa.export import select_files


def touch(folder: Path, names: list[str]) -> None:
    folder.mkdir(exist_ok=True)
    for n in names:
        (folder / n).write_text("{}")


def test_only_files_from_since_and_not_in_skip_dir(tmp_path: Path) -> None:
    ev, baked = tmp_path / "ev", tmp_path / "baked"
    touch(ev, ["20261011T230000-a.json", "20261012T050200-b.json", "20261012T060000-c.json"])
    touch(baked, ["20261012T060000-c.json"])
    assert [p.name for p in select_files(ev, baked, "20261012T0502")] == ["20261012T050200-b.json"]
    assert len(select_files(ev, None, "20261012T0502")) == 2
