from treekit.tree import TreeNode, inorder


def test_inorder_small_tree():
    #     2
    #    / \
    #   1   3
    root = TreeNode(2, TreeNode(1), TreeNode(3))
    assert inorder(root) == [1, 2, 3]


def test_inorder_empty_and_skewed():
    assert inorder(None) == []
    root = TreeNode(1, right=TreeNode(2, left=TreeNode(3)))
    assert inorder(root) == [1, 3, 2]
