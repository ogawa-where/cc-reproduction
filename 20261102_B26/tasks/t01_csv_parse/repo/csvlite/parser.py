"""Parse CSV text into a list of row dicts."""


def parse_csv(text: str, delimiter: str = ",") -> list[dict[str, str]]:
    """Parse ``text`` and return one dict per data row, keyed by the header names."""
    raise NotImplementedError
