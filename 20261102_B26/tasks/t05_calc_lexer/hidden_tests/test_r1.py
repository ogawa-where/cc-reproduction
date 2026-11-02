from calclex.lexer import tokenize


def test_all_operators_without_spaces():
    assert tokenize("12+34*5/6") == [
        ("NUM", "12"), ("OP", "+"), ("NUM", "34"), ("OP", "*"),
        ("NUM", "5"), ("OP", "/"), ("NUM", "6"),
    ]


def test_whitespace_variants():
    assert tokenize("  7 \t*\n( 8 )  ") == [
        ("NUM", "7"), ("OP", "*"), ("LPAREN", "("), ("NUM", "8"), ("RPAREN", ")"),
    ]


def test_binary_minus_between_numbers():
    assert tokenize("9 - 4") == [("NUM", "9"), ("OP", "-"), ("NUM", "4")]


def test_empty_expression():
    assert tokenize("") == []
