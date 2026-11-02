from decimal import Decimal

from money.rounding import round_amount, split_amount


def test_round_simple():
    assert round_amount("2.341") == Decimal("2.34")


def test_split_even():
    assert split_amount("9.00", 3) == [Decimal("3.00")] * 3
