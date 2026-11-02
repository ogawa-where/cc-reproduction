from mdtoc.headings import extract_headings


def test_comment_in_fence_ignored():
    doc = "# Real\n```\n# not a heading\n```\n## Also real\n"
    assert extract_headings(doc) == [(1, "Real"), (2, "Also real")]


def test_fence_with_language_tag():
    doc = "```python\n# comment\nx = 1\n```\n# After\n"
    assert extract_headings(doc) == [(1, "After")]


def test_two_fences():
    doc = "```\n# a\n```\n# Mid\n```bash\n## b\n```\n"
    assert extract_headings(doc) == [(1, "Mid")]
