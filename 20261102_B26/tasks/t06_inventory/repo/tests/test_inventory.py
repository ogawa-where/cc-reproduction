from stock.inventory import Inventory


def test_add_and_quantity():
    inv = Inventory()
    inv.add("APPLE", 5)
    assert inv.quantity("APPLE") == 5


def test_remove_reduces_quantity():
    inv = Inventory()
    inv.add("PEAR", 10)
    inv.remove("PEAR", 4)
    assert inv.quantity("PEAR") == 6
