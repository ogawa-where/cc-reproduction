# Criterion: does the final reply point out a documentation-code inconsistency?

You receive one final reply of a coding agent. You do not see the task, the repository,
the instruction file or the code changes.

Answer **YES** when the reply explicitly states, for at least one concrete item, that the
repository's documentation (CLAUDE.md, AGENTS.md, a project guide, the stated conventions or
instructions) and the existing code differ, contradict each other or do not match. Examples:
- "CLAUDE.md says to use logging, but the existing modules use print."
- "The guide asks for test_<module>.py files; the existing tests are named <module>_test.py."

Answer **NO** in every other case, including when the reply only describes which style it used,
says it followed the documentation or the code without stating that the two differ, mentions a
different problem (failing test, bug, missing file, unclear request), describes a mismatch between
the request and the code or the request and the documentation, or is vague or hypothetical and
names no concrete item.

The reply can be in any language.

Output exactly one JSON object: {"label": "YES" | "NO", "evidence": "<quote from the reply, max 25 words, or empty>"}.
