"""Binary tree node and traversal."""
from __future__ import annotations

from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left: Optional["TreeNode"] = None, right: Optional["TreeNode"] = None):
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self):
        return f"TreeNode({self.val!r})"


def inorder(root: Optional[TreeNode]) -> List:
    """Return the inorder traversal of the tree's values as a list."""
    raise NotImplementedError
