from mdtoc.headings import extract_headings


def test_all_six_levels():
    doc = "\n".join("#" * n + f" H{n}" for n in range(1, 7))
    assert extract_headings(doc) == [(n, f"H{n}") for n in range(1, 7)]


def test_text_stripped_and_order_kept():
    doc = "##   Spaced out   \ntext\n# Back to one\n### Deep"
    assert extract_headings(doc) == [(2, "Spaced out"), (1, "Back to one"), (3, "Deep")]


def test_hash_inside_text_kept():
    assert extract_headings("## C# notes") == [(2, "C# notes")]
