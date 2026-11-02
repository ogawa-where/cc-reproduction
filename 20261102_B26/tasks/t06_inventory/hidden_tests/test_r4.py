from stock.inventory import Inventory


def test_sorted_by_quantity_desc():
    inv = Inventory()
    inv.add("A", 1)
    inv.add("B", 5)
    inv.add("C", 3)
    assert inv.report() == [("B", 5), ("C", 3), ("A", 1)]


def test_ties_by_sku():
    inv = Inventory()
    inv.add("ZED", 2)
    inv.add("ALPHA", 2)
    inv.add("MID", 7)
    assert inv.report() == [("MID", 7), ("ALPHA", 2), ("ZED", 2)]


def test_zero_quantity_omitted():
    inv = Inventory()
    inv.add("A", 2)
    inv.add("B", 1)
    inv.remove("A", 2)
    assert inv.report() == [("B", 1)]
