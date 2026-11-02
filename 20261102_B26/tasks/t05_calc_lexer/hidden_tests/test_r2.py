from calclex.lexer import tokenize


def test_decimal_forms():
    assert tokenize("3.14") == [("NUM", "3.14")]
    assert tokenize("10.") == [("NUM", "10.")]
    assert tokenize(".5") == [("NUM", ".5")]


def test_decimals_in_expression():
    assert tokenize("1.5*.25+2.") == [
        ("NUM", "1.5"), ("OP", "*"), ("NUM", ".25"), ("OP", "+"), ("NUM", "2."),
    ]
