from mdtoc.headings import extract_headings


def test_two_levels():
    doc = "# Title\n\nSome text.\n\n## Usage\n"
    assert extract_headings(doc) == [(1, "Title"), (2, "Usage")]


def test_no_headings():
    assert extract_headings("just a paragraph\nand another line\n") == []
