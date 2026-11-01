"""Classify a Python solution as recursive / iterative / other.

Rule: extract the Python code (fenced block if present); parse it; 'recursive' when any function
(or nested function/method) contains a call to its own name; otherwise 'iterative' when a loop
(for/while) exists; else 'other'. Unparseable code falls back to a regex on self-calls."""
from __future__ import annotations

import ast
import re

FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)


def extract_code(text: str) -> str:
    m = FENCE.findall(text or "")
    return max(m, key=len) if m else (text or "")


class _Finder(ast.NodeVisitor):
    def __init__(self):
        self.recursive = False
        self.loops = False
        self._stack = []

    def visit_FunctionDef(self, node):
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node):
        f = node.func
        name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
        if name and name in self._stack:
            self.recursive = True
        self.generic_visit(node)

    def visit_For(self, node):
        self.loops = True
        self.generic_visit(node)

    visit_While = visit_For


def classify(text: str) -> str:
    code = extract_code(text)
    try:
        tree = ast.parse(code)
    except SyntaxError:
        names = set(re.findall(r"def\s+(\w+)\s*\(", code))
        if any(re.search(r"\b" + re.escape(n) + r"\s*\(", code[code.find("def " + n) + 4:]) for n in names):
            return "recursive"
        return "iterative" if re.search(r"\b(for|while)\b", code) else "other"
    f = _Finder()
    f.visit(tree)
    if not any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree)):
        return "other"
    if f.recursive:
        return "recursive"
    return "iterative" if f.loops else "other"


if __name__ == "__main__":
    import sys
    print(classify(sys.stdin.read()))
