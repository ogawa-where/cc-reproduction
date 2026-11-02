import pytest

from calclex.lexer import LexError, tokenize


def test_unknown_character_position():
    with pytest.raises(LexError) as info:
        tokenize("2 $ 3")
    assert info.value.pos == 2


def test_letter_position_later_in_input():
    with pytest.raises(LexError) as info:
        tokenize("12 + x")
    assert info.value.pos == 5


def test_lexerror_is_valueerror():
    with pytest.raises(ValueError):
        tokenize("1 % 2")
