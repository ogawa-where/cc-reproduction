from decimal import Decimal

from money.rounding import round_amount


def test_half_to_even_down():
    assert round_amount("2.345") == Decimal("2.34")
    assert round_amount("0.125") == Decimal("0.12")


def test_half_to_even_up():
    assert round_amount("2.355") == Decimal("2.36")


def test_half_to_even_whole_numbers():
    assert str(round_amount("2.5", 0)) == "2"
    assert str(round_amount("3.5", 0)) == "4"
