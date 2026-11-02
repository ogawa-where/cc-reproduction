from csvlite.parser import parse_csv


def test_header_maps_values_in_order():
    rows = parse_csv("id,name,city\n1,Ann,Oslo\n2,Bo,Rome")
    assert rows == [
        {"id": "1", "name": "Ann", "city": "Oslo"},
        {"id": "2", "name": "Bo", "city": "Rome"},
    ]
    assert list(rows[0].keys()) == ["id", "name", "city"]


def test_header_only_gives_no_rows():
    assert parse_csv("a,b,c\n") == []


def test_values_kept_as_written_strings():
    rows = parse_csv("x,y\n007, 1.50 ")
    assert rows == [{"x": "007", "y": " 1.50 "}]


def test_tab_delimiter():
    assert parse_csv("k\tv\nfoo\tbar", delimiter="\t") == [{"k": "foo", "v": "bar"}]
