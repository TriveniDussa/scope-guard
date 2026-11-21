import json
from typing import Any, List


SYSTEM_INSTRUCTION = """You are an expert Scope of Work (SOW) Analyzer for professional agencies.
Your task is to analyze a new client request against the contractually agreed Scope of Work deliverables for a specific project.

STRICT DECISION RULES:
1. Base your decision ONLY on the provided "Included" and "Not Included" scope items.
2. If the request clearly matches an "Included" deliverable, classify as "In scope".
3. If the request clearly matches an item listed under "Not Included" (or contradicts/exceeds agreed boundaries), classify as "Out of scope".
4. If the provided scope does not contain enough information to be certain, or if there are no scope items defined, classify as "Not sure".
5. NEVER invent, assume, or hallucinate scope agreements not explicitly provided.
6. Provide a concise 1-2 sentence explanation in "reason".
7. Generate a polite, professional reply in "client_reply" suitable for sending directly to the client.

You MUST respond strictly with a valid JSON object matching this schema:
{
  "classification": "In scope" | "Out of scope" | "Not sure",
  "reason": "Short explanation based on agreed scope",
  "client_reply": "Polite client message"
}
"""


def build_classification_prompt(client_request: str, scope_items: List[Any]) -> str:
    """Formats the scope items and client request into a structured prompt."""
    formatted_items = []
    for idx, item in enumerate(scope_items, 1):
        inc = getattr(item, "included_description", "")
        not_inc = getattr(item, "not_included_description", "")
        formatted_items.append(
            f"Deliverable #{idx}:\n  - Included: {inc}\n  - Not Included: {not_inc}"
        )

    scope_section = (
        "\n\n".join(formatted_items)
        if formatted_items
        else "No Scope of Work items have been defined for this project yet."
    )

    prompt = f"""AGREED PROJECT SCOPE OF WORK:
=======================================
{scope_section}

NEW CLIENT REQUEST TO EVALUATE:
=======================================
"{client_request}"

Evaluate the client request against the agreed scope above. Return valid JSON only."""
    return prompt
