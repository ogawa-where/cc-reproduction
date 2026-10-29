"""Reading the raw CSV. The schema is owned by the data team; do not change it here."""
from __future__ import annotations

import csv
from pathlib import Path

COLUMNS = ["date", "region", "product", "units", "unit_price"]


def read_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for row in reader:
            row["units"] = int(row["units"])
            row["unit_price"] = float(row["unit_price"])
            rows.append(row)
        return rows
