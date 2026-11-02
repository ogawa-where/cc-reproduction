"""In-memory inventory of SKUs and their quantities."""


class InsufficientStock(ValueError):
    """Raised when removing more units than are in stock."""


class Inventory:
    def __init__(self) -> None:
        raise NotImplementedError

    def add(self, sku: str, qty: int) -> None:
        raise NotImplementedError

    def remove(self, sku: str, qty: int) -> None:
        raise NotImplementedError

    def quantity(self, sku: str) -> int:
        raise NotImplementedError

    def report(self) -> list[tuple[str, int]]:
        raise NotImplementedError
