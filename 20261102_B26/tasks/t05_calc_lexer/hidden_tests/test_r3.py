from calclex.lexer import tokenize


def test_unary_minus_at_start():
    assert tokenize("-3") == [("NUM", "-3")]
    assert tokenize("-3 + 4") == [("NUM", "-3"), ("OP", "+"), ("NUM", "4")]


def test_unary_minus_after_operator_and_paren():
    assert tokenize("-3*(-2)") == [
        ("NUM", "-3"), ("OP", "*"), ("LPAREN", "("), ("NUM", "-2"), ("RPAREN", ")"),
    ]
    assert tokenize("2*-1.5") == [("NUM", "2"), ("OP", "*"), ("NUM", "-1.5")]


def test_minus_after_number_or_rparen_is_binary():
    assert tokenize("5-3") == [("NUM", "5"), ("OP", "-"), ("NUM", "3")]
    assert tokenize("(1)-2") == [
        ("LPAREN", "("), ("NUM", "1"), ("RPAREN", ")"), ("OP", "-"), ("NUM", "2"),
    ]
