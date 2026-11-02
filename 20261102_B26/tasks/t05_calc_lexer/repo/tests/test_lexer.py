from calclex.lexer import tokenize


def test_simple_sum():
    assert tokenize("1 + 2") == [("NUM", "1"), ("OP", "+"), ("NUM", "2")]


def test_parentheses():
    assert tokenize("(3*4)/5") == [
        ("LPAREN", "("), ("NUM", "3"), ("OP", "*"), ("NUM", "4"),
        ("RPAREN", ")"), ("OP", "/"), ("NUM", "5"),
    ]
