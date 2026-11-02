from stock.inventory import Inventory


def test_add_accumulates():
    inv = Inventory()
    inv.add("X1", 3)
    inv.add("X1", 4)
    assert inv.quantity("X1") == 7


def test_unknown_sku_is_zero():
    inv = Inventory()
    assert inv.quantity("NOPE") == 0
    inv.add("A", 1)
    assert inv.quantity("B") == 0


def test_remove_to_zero():
    inv = Inventory()
    inv.add("A", 2)
    inv.remove("A", 2)
    assert inv.quantity("A") == 0
