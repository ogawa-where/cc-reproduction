from slugkit.slug import slugify


def test_runs_collapse():
    assert slugify("a  --  b") == "a-b"
    assert slugify("C++ & Python: 2024 edition") == "c-python-2024-edition"


def test_no_edge_hyphens():
    assert slugify("  ...Leading and trailing!!!  ") == "leading-and-trailing"


def test_lowercase_and_digits_kept():
    assert slugify("ABC123def") == "abc123def"
