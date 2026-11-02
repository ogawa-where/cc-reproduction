import pytest

from stock.inventory import InsufficientStock, Inventory


def test_over_removal_raises():
    inv = Inventory()
    inv.add("A", 3)
    with pytest.raises(InsufficientStock):
        inv.remove("A", 4)


def test_stock_unchanged_after_failure():
    inv = Inventory()
    inv.add("A", 3)
    with pytest.raises(InsufficientStock):
        inv.remove("A", 10)
    assert inv.quantity("A") == 3


def test_removing_unknown_sku_raises():
    inv = Inventory()
    with pytest.raises(InsufficientStock):
        inv.remove("GHOST", 1)
    assert inv.quantity("GHOST") == 0
