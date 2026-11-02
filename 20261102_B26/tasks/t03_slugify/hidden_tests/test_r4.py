from slugkit.slug import slugify


def test_only_punctuation():
    assert slugify("!!! ???") == "n-a"


def test_empty_string():
    assert slugify("") == "n-a"
