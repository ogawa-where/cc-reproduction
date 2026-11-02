from csvlite.parser import parse_csv


def test_empty_lines_are_skipped():
    rows = parse_csv("a,b\n\n1,2\n\n\n3,4\n")
    assert rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]


def test_whitespace_only_lines_are_blank():
    rows = parse_csv("a,b\n   \n1,2\n\t \n3,4\n  ")
    assert rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]


def test_blank_lines_before_header():
    rows = parse_csv("\n  \nx,y\n5,6")
    assert rows == [{"x": "5", "y": "6"}]
