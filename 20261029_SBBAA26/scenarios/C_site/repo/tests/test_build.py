from pathlib import Path

from ssg import build


def test_build_writes_html(tmp_path):
    (tmp_path / "c").mkdir()
    (tmp_path / "c" / "p.md").write_text("# Hi\n\ntext\n")
    written = build.build(tmp_path / "c", tmp_path / "o")
    assert [p.name for p in written] == ["p.html"]
    assert "<title>Hi</title>" in (tmp_path / "o" / "p.html").read_text()
