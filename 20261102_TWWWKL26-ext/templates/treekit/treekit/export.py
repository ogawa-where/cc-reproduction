"""Export helpers."""
from __future__ import annotations

from .tree import inorder


def to_csv(root) -> str:
    """Return the tree's values in inorder as one comma-separated line."""
    return ",".join(str(v) for v in inorder(root))
