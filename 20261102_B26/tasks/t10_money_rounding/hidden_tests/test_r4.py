from decimal import Decimal

import pytest

from money.rounding import round_amount, split_amount


def test_round_rejects_float():
    with pytest.raises(TypeError):
        round_amount(2.5)


def test_split_rejects_float():
    with pytest.raises(TypeError):
        split_amount(10.0, 3)


def test_non_floats_accepted():
    assert round_amount(Decimal("1.10")) == Decimal("1.10")
