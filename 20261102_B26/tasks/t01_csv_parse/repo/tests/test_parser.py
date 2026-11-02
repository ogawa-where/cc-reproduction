from csvlite.parser import parse_csv


def test_basic_rows():
    text = "name,age\nalice,30\nbob,25\n"
    assert parse_csv(text) == [
        {"name": "alice", "age": "30"},
        {"name": "bob", "age": "25"},
    ]


def test_custom_delimiter():
    assert parse_csv("a;b\n1;2", delimiter=";") == [{"a": "1", "b": "2"}]
