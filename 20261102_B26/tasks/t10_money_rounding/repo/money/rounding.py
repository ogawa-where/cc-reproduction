"""Rounding and splitting of currency amounts."""
from decimal import Decimal


def round_amount(amount: Decimal | str | int, places: int = 2) -> Decimal:
    """Return ``amount`` as a Decimal rounded to ``places`` decimal places."""
    raise NotImplementedError


def split_amount(total: Decimal | str | int, parts: int) -> list[Decimal]:
    """Split ``total`` into ``parts`` amounts that add up to it exactly."""
    raise NotImplementedError
