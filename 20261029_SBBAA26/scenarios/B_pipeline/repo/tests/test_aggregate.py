from pipeline import aggregate

ROWS = [
    {"date": "2026-07-01", "region": "north", "product": "widget", "units": 2, "unit_price": 4.0},
    {"date": "2026-07-01", "region": "north", "product": "gadget", "units": 1, "unit_price": 10.0},
    {"date": "2026-07-02", "region": "south", "product": "widget", "units": 3, "unit_price": 4.0},
]


def test_revenue_by_region():
    assert aggregate.revenue_by_region(ROWS) == {"north": 18.0, "south": 12.0}


def test_units_by_product():
    assert aggregate.units_by_product(ROWS) == {"widget": 5, "gadget": 1}
