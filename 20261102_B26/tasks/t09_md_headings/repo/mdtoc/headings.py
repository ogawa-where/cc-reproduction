"""Find the headings in a Markdown document."""


def extract_headings(markdown: str) -> list[tuple[int, str]]:
    """Return ``(level, text)`` for each ATX heading in ``markdown``."""
    raise NotImplementedError
