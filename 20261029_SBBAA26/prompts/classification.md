You are categorizing what KIND of instruction each item is. Each item is a single constraint that a user gave a coding agent during a session. You see only the constraint text; classify its nature from that text alone.

Pick exactly one category from this fixed taxonomy:
- scope_exclusion: A rule that bounds what may or may not be changed or done: either negative ('don't touch X', 'X is out of scope', 'keep Z as-is') or an affirmative limit ('only modify X and Y').
- technical_parameter: A specific literal value: an exact number, config value, type signature, file path, or enumerated list (timeouts, ports, exact function or field names, a checklist of items, a symbol-to-file mapping).
- feature_requirement: A concrete specification of something to build or how it should behave (add this UI element, show this fallback chain, warn under this condition, create this interface) that is not merely a bare literal value, a working-method instruction, or a scope boundary.
- process_instruction: An instruction about how the agent should go about its work rather than about what is to be built: split the work into todos, work sequentially, use a particular editing approach, pause for review between phases, proceed autonomously, commit in a particular way.
- named_source_or_tool: A requirement to use a specific named tool, document, or source (a particular CLI, reference paper or spec file, skill, or library).
- structural_convention: A formatting, ordering, or structural rule (keep section X last, preserve the original section order, perform this check before that one, use this exact mapping between labels and values).
- soft_preference: A subjective preference about tone, depth, or style of communication (comfortable with detail, prefers concise answers) rather than a requirement on the deliverable.
- other: Fits none of the categories above. Use sparingly and say why in the reasoning.

For every item, in order:
1. First write your reasoning in the `reasoning` field: identify what kind of thing this constraint is and why that puts it in the category you are about to pick. Ground this in the constraint text itself, not just the category name.
2. Only after that reasoning, pick the single best-fitting `category`. Every constraint gets exactly one category -- pick the closest fit even when a case could arguably straddle two, and name the near-miss in your reasoning if relevant.
3. Give a `confidence` of high/medium/low for your own category choice.

Categorize each item independently -- don't let one item's category choice bias another's.

Return a JSON object {"items": [{"id": ..., "reasoning": ..., "category": ..., "confidence": ...}, ...]} with one entry per item, in the order given.
