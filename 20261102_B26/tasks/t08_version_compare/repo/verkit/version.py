"""Compare and sort dotted version strings."""


def compare_versions(a: str, b: str) -> int:
    """Return -1 if ``a`` < ``b``, 0 if they are equal, 1 if ``a`` > ``b``."""
    raise NotImplementedError


def sort_versions(versions: list[str]) -> list[str]:
    """Return a new list of ``versions`` sorted from lowest to highest."""
    raise NotImplementedError
