"""Human-readable timestamps and durations."""


def format_timestamp(ts: float) -> str:
    """Format a Unix timestamp as ``YYYY-MM-DD HH:MM:SS UTC``."""
    raise NotImplementedError


def format_duration(seconds: int) -> str:
    """Format a number of seconds such as ``1h 2m 5s``."""
    raise NotImplementedError
