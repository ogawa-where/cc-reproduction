from decimal import Decimal

from money.rounding import round_amount


def test_exact_number_of_places():
    r = round_amount("5")
    assert r == Decimal("5.00")
    assert str(r) == "5.00"
    assert str(round_amount(7)) == "7.00"


def test_other_places_and_decimal_input():
    assert str(round_amount(Decimal("1.23456"), 3)) == "1.235"
    assert str(round_amount("12.3", 0)) == "12"


def test_non_tie_rounding():
    assert round_amount("2.349") == Decimal("2.35")
    assert round_amount("-1.234") == Decimal("-1.23")
