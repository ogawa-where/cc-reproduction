"""Questions, output schema and system prompts, following Bagal, Ganta & Chellingi (2026), Section 4."""
from __future__ import annotations

import json

QUESTIONS = {
    "reasons": "Summarize the top five reasons customers provide feedback.",
    "pain_points": "Identify the top three customer pain points and affected workflows.",
    "feature_requests": "Identify and prioritize the top feature requests, their underlying needs, and frequency.",
}

# The shared strict structured-output contract (name, volume, summary, up to five evidence IDs; no quotes).
ANSWER_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["themes"],
    "properties": {"themes": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["name", "volume", "summary", "evidence_ids"],
        "properties": {
            "name": {"type": "string", "description": "short theme name"},
            "volume": {"type": "integer", "minimum": 0, "description": "number of records supporting the theme"},
            "summary": {"type": "string", "description": "concise summary; no customer quotes"},
            "evidence_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 5,
                             "description": "at most five supporting record IDs"}}}}}}

TASK_TEXT = ("Each theme needs a name, the volume (how many records support it), a concise summary, and up to five "
             "supporting record IDs. Customer quotes are unnecessary; do not include them. Return only the structured answer.")

SYSTEM_PROMPTS = {
    # task and schema only
    "minimal": "You analyze customer feedback records and answer the question with the requested structured output. " + TASK_TEXT,
    # record-first extraction followed by semantic consolidation
    "bottom_up": ("You analyze customer feedback records. Work bottom-up: first extract the issue raised by each record, "
                  "then consolidate semantically equivalent issues into themes, then answer the question with the requested "
                  "structured output. " + TASK_TEXT),
    # canonical labels, stable boundaries, non-overlap, deterministic tie-breaking
    "consistency_first": ("You analyze customer feedback records. Consistency is the top priority: use canonical, generic theme "
                          "labels (short noun phrases, no adjectives of degree), keep theme boundaries stable and mutually "
                          "exclusive, do not create overlapping themes, break ties deterministically (larger volume first, then "
                          "alphabetical name), and report volumes as exact record counts. If the same records were given again, "
                          "your answer should be identical. Answer the question with the requested structured output. " + TASK_TEXT),
}

TAXONOMY_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["themes"],
    "properties": {"themes": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["id", "name", "definition", "subthemes"],
        "properties": {"id": {"type": "string"}, "name": {"type": "string"}, "definition": {"type": "string"},
                       "subthemes": {"type": "array", "items": {"type": "string"}}}}}}}

CLASSIFY_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["predictions"],
    "properties": {"predictions": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["record_id", "theme_ids"],
        "properties": {"record_id": {"type": "string"}, "theme_ids": {"type": "array", "items": {"type": "string"}}}}}}}

TAXONOMY_PROMPT = ("You build a persistent customer-feedback taxonomy. Read all records and return a taxonomy of 8-14 themes, "
                   "each with a stable id (t01, t02, ...), a canonical name, a one-sentence definition and 2-4 subthemes. "
                   "Themes must be mutually exclusive and cover the corpus.")
CLASSIFY_PROMPT = ("You label customer feedback records with a fixed taxonomy. For every record, return the ids of all themes "
                   "that apply (usually one, sometimes two, never zero). Use only the given theme ids.")
TGA_ANSWER_PROMPT = ("You are an analyst agent that answers questions about customer feedback by querying a persistent taxonomy "
                     "store. You do not see raw records. The store gives you, for the frozen time window, every theme with its "
                     "definition, its subthemes, the number of records predicted to belong to it, and representative record IDs. "
                     "Compose the answer from the store only: theme names are the store's canonical names, volumes are the "
                     "store's counts, evidence IDs come from the store's representative IDs. " + TASK_TEXT)

MATCH_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["pairs"],
    "properties": {"pairs": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["a", "b", "similarity"],
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"},
                       "similarity": {"type": "number", "minimum": 0, "maximum": 1}}}}}}
MATCH_PROMPT = ("You compare two lists of customer-feedback theme names (list A and list B) and judge which names denote the "
                "same operating category. For every pair (a from A, b from B) that is at least loosely related, return a "
                "similarity in [0, 1]: 1.0 = same category (paraphrase); 0.85 = same category with a difference of scope or "
                "wording; 0.7 = overlapping but not the same category; below 0.6 = different. Omit unrelated pairs. "
                "Judge the names only.")


def schema_json(s):
    return json.dumps(s)
