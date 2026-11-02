from mdtoc.headings import extract_headings


def test_closing_run_removed():
    assert extract_headings("## Setup ##") == [(2, "Setup")]


def test_closing_run_of_different_length():
    assert extract_headings("# Title #####\n### Install #") == [(1, "Title"), (3, "Install")]
