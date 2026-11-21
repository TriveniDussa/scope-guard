from typing import Any, List, Optional


SYSTEM_INSTRUCTION = """You are an expert Scope of Work (SOW) Analyzer for professional agencies.
Your task is to analyze a new client request against the contractually agreed Scope of Work deliverables and previous agency correction lessons for a specific project.

HIERARCHY OF TRUTH:
1. The agreed Scope of Work (Included / Not Included) is the PRIMARY source of truth.
2. Previous agency correction lessons provide additional guidance based on past human decisions on this project.
3. If the agreed scope and lessons directly conflict, classify as "Not sure" rather than inventing a decision.

STRICT DECISION RULES:
1. Base your decision ONLY on the provided project scope items and project lessons.
2. If the request matches an "Included" deliverable (or past lessons establish it is in scope and not contradicted by scope), classify as "In scope".
3. If the request matches a "Not Included" item (or past lessons establish it is out of scope and not contradicted by scope), classify as "Out of scope".
4. If neither the scope nor lessons provide sufficient information to be certain, classify as "Not sure".
5. If scope and lessons conflict, classify as "Not sure".
6. NEVER invent, assume, or hallucinate scope agreements or lessons not explicitly provided.
7. Provide a concise 1-2 sentence explanation in "reason" citing relevant scope or lesson guidance.
8. Generate a polite, professional reply in "client_reply" suitable for sending directly to the client.

You MUST respond strictly with a valid JSON object matching this schema:
{
  "classification": "In scope" | "Out of scope" | "Not sure",
  "reason": "Short explanation based on agreed scope and lessons",
  "client_reply": "Polite client message"
}
"""


def build_classification_prompt(
    client_request: str,
    scope_items: List[Any],
    lessons: Optional[List[Any]] = None,
) -> str:
    """Formats the scope items, retrospective lessons, and client request into a structured prompt."""
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

    formatted_lessons = []
    if lessons:
        for idx, lesson in enumerate(lessons, 1):
            ai_ans = getattr(lesson, "ai_answer", "N/A")
            correct = getattr(lesson, "correct_result", "")
            reason = getattr(lesson, "correction_reason", "")
            formatted_lessons.append(
                f"Lesson #{idx}:\n  - Original AI Assessment: {ai_ans}\n  - Human Correction: {correct}\n  - Correction Reason: {reason}"
            )

    lessons_section = (
        "\n\n".join(formatted_lessons)
        if formatted_lessons
        else "No previous correction lessons for this project."
    )

    prompt = f"""AGREED PROJECT SCOPE OF WORK (PRIMARY TRUTH):
=======================================
{scope_section}

PREVIOUS AGENCY CORRECTION LESSONS (ADDITIONAL GUIDANCE):
=======================================
{lessons_section}

NEW CLIENT REQUEST TO EVALUATE:
=======================================
"{client_request}"

Evaluate the client request against the agreed scope and lessons above following the Hierarchy of Truth. Return valid JSON only."""
    return prompt
