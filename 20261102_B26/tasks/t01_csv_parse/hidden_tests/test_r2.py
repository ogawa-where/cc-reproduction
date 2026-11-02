from csvlite.parser import parse_csv


def test_quoted_field_with_delimiter():
    rows = parse_csv('name,address\nAnn,"12 Main St, Springfield"')
    assert rows == [{"name": "Ann", "address": "12 Main St, Springfield"}]


def test_doubled_quote_is_literal_quote():
    rows = parse_csv('title,note\nA,"She said ""hi"""')
    assert rows == [{"title": "A", "note": 'She said "hi"'}]


def test_quoted_empty_field_and_semicolon():
    rows = parse_csv('a;b;c\n"";"x;y";z', delimiter=";")
    assert rows == [{"a": "", "b": "x;y", "c": "z"}]
