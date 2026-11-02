from slugkit.slug import slugify


def test_simple_title():
    assert slugify("Hello World") == "hello-world"


def test_punctuation_becomes_hyphen():
    assert slugify("Hello, World!") == "hello-world"
