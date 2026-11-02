from decimal import Decimal

from money.rounding import split_amount


def test_leftover_to_earliest():
    assert split_amount("10.00", 3) == [Decimal("3.34"), Decimal("3.33"), Decimal("3.33")]
    assert split_amount("0.05", 3) == [Decimal("0.02"), Decimal("0.02"), Decimal("0.01")]


def test_sum_is_exact_and_two_places():
    parts = split_amount("100", 7)
    assert sum(parts) == Decimal("100.00")
    assert all(p.as_tuple().exponent == -2 for p in parts)
    assert max(parts) - min(parts) <= Decimal("0.01")


def test_total_rounded_first():
    parts = split_amount("1.004", 2)
    assert parts == [Decimal("0.50"), Decimal("0.50")]
