"""Prompt templates from Bui (2026), Appendix A.1 (verbatim), plus the baselines used here."""

# Claim Book Seat Call System Prompt (Always-On Betting); used as --system-prompt of a separate tool-less call
CLAIM_BOOK_SYSTEM = """You are the coding agent in the session below, working for a user in a code repository. Write your claim book for the current state of your work: the claims your work rests on.

A claim is one decision you made, or one assumption you rely on, about what the user wants or how the code must behave (for example "the parser accepts ISO dates only", "empty input returns []", "the public API signature is unchanged"). For each claim give:
- `p`: your probability, from 0 to 1, that the claim is correct, i.e. that it is what the user wants and what the code does;
- `evidence`: what supports it (quote the user, name a test result or a file), or "none (guess)".

List 3 to 10 claims, most important first. Also list the rejected options: approaches the user rejected or you ruled out, with the turn and the reason. Keep the claims and rejected options of your previous claim book unless the session shows they changed, and keep their ids stable.

Return JSON only, in exactly this shape:
{"claims": [{"id": "C1", "claim": "...", "p": 0.6, "evidence": "..."}], "rejected": [{"option": "...", "turn": 2, "reason": "..."}]}"""

CLAIM_BOOK_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["claims", "rejected"],
    "properties": {
        "claims": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                   "required": ["id", "claim", "p", "evidence"],
                   "properties": {"id": {"type": "string"}, "claim": {"type": "string"},
                                  "p": {"type": "number", "minimum": 0, "maximum": 1}, "evidence": {"type": "string"}}}},
        "rejected": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                     "required": ["option", "turn", "reason"],
                     "properties": {"option": {"type": "string"}, "turn": {"type": "integer"}, "reason": {"type": "string"}}}}}}

# Private Bookkeeping & Adjudication Note appended to the user reply (tau = 0.5)
ADJUDICATION_NOTE = """(Private note from your own bookkeeping, not from the user. Do not mention it to the user.)

Your claim book:
{claim_book}

How to handle the user's message above:
1. Work out which of your claims the message bears on, and update only those claims.
2. Change the work only for claims whose p is now below {tau}; keep everything else exactly as it is.
3. Never return to a rejected option unless the message gives new evidence for it.
4. If the message fits two or more weak claims (p below {tau}), ask the user one targeted question instead of changing code.
5. If the message names no specific fault and all your claims are strong (p at least {tau}), ask the user what is wrong instead of rewriting."""

# Rule only (Table 5): the instruction to stand firm unless the reply gives new evidence, with no record.
RULE_ONLY_NOTE = """(Private note from your own bookkeeping, not from the user. Do not mention it to the user.)

Stand firm on your current work unless the user's message gives new evidence (a failing case, a command output, or a changed requirement). If it gives no new evidence, do not change code; ask the user for the specific failing case."""

# Verify-Then-Respond Baseline Prompt
VERIFY_THEN_RESPOND_NOTE = """(Private note from your own bookkeeping, not from the user. Do not mention it to the user.)

Before replying or changing anything, re-run the relevant tests and commands to re-observe the current state of the repository. Then act on what you observed: change only what the evidence shows is broken. If everything this message refers to passes, do not change code; tell the user what you ran and what it showed, and ask for the specific failing case."""

TAU = 0.5


def render_claim_book(book):
    lines = []
    for c in book.get("claims", []):
        lines.append(f"- {c['id']}: {c['claim']} | p={c['p']:.2f} | evidence: {c['evidence']}")
    if book.get("rejected"):
        lines.append("Rejected options:")
        for r in book["rejected"]:
            lines.append(f"- {r['option']} (turn {r['turn']}): {r['reason']}")
    return "\n".join(lines) if lines else "(empty)"
