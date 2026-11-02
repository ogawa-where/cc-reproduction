from stock.inventory import Inventory


def test_case_and_whitespace_insensitive():
    inv = Inventory()
    inv.add(" ab-1 ", 2)
    inv.add("AB-1", 3)
    assert inv.quantity("Ab-1") == 5


def test_remove_with_other_spelling():
    inv = Inventory()
    inv.add("widget", 5)
    inv.remove("  WIDGET", 2)
    assert inv.quantity("Widget ") == 3


def test_report_uses_uppercase():
    inv = Inventory()
    inv.add("gizmo", 1)
    inv.add(" Gizmo", 1)
    assert inv.report() == [("GIZMO", 2)]
