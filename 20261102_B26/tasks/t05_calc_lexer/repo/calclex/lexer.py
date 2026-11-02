"""Split an arithmetic expression into tokens."""


class LexError(ValueError):
    """Raised for a character that cannot start a token."""

    def __init__(self, message: str, pos: int):
        super().__init__(message)
        self.pos = pos


def tokenize(expr: str) -> list[tuple[str, str]]:
    """Return the tokens of ``expr`` as ``(kind, text)`` pairs."""
    raise NotImplementedError
