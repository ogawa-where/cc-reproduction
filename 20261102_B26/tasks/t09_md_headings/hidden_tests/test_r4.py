from mdtoc.headings import extract_headings


def test_seven_hashes_not_heading():
    assert extract_headings("####### too deep") == []


def test_no_space_not_heading():
    assert extract_headings("#hashtag\n##also") == []


def test_mixed_document():
    doc = "#tag\n# Real\n######## nope\n###### Six"
    assert extract_headings(doc) == [(1, "Real"), (6, "Six")]
