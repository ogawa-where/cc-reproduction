from slugkit.slug import slugify


def test_truncates_to_max_length():
    assert slugify("abcdefghij", max_length=4) == "abcd"


def test_no_trailing_hyphen_after_cut():
    assert slugify("hello world foo", max_length=6) == "hello"


def test_short_slug_untouched():
    assert slugify("hello world", max_length=50) == "hello-world"
    assert slugify("hello world", max_length=None) == "hello-world"
