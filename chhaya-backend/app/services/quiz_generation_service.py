"""Gemini interaction for Module 3 Feature 7 – generating quiz questions.

Flow:
  - Build a prompt
  - Call Gemini (raises ExternalServiceError if API key is missing or not configured)
  - Parse the JSON response, clamping marks to [min_marks, max_marks]
  - Retry once if parsing fails
  - Raise ExternalServiceError on second failure
"""

import json

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError


# ── prompt ────────────────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """You are a quiz generator for a student learning platform.
Read the study notes below and generate exactly {num_questions} quiz questions.

Rules:
- Difficulty level for ALL questions must be: {difficulty}
- Each question must have an individual marks value between {min_marks} and {max_marks}
- Assign higher marks to questions that are more complex or require deeper explanation
- Question types should be short-answer or explain-in-your-own-words (no MCQ)
- Base questions ONLY on the content in the notes below

Return ONLY valid JSON in exactly this shape (no extra text, no markdown fences):
{{
  "questions": [
    {{
      "question_text": "a simpler question",
      "marks": {min_marks},
      "difficulty": "{difficulty}"
    }},
    {{
      "question_text": "a more complex question requiring deeper explanation",
      "marks": {max_marks},
      "difficulty": "{difficulty}"
    }}
  ]
}}

Student notes:
{notes_text}
"""



# ── JSON parsing ──────────────────────────────────────────────────────────────

def _parse_questions(text: str, min_marks: int, max_marks: int) -> list[dict]:
    """Strip markdown fences if present, parse JSON, validate shape, clamp marks to range."""
    cleaned = text.strip()

    # Gemini sometimes wraps the JSON in ```json ... ```
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # drop the first line (```json or ```) and the last (```)
        cleaned = "\n".join(lines[1:-1])

    data = json.loads(cleaned.strip())

    if not isinstance(data.get("questions"), list):
        raise ValueError("Response is missing a 'questions' list.")

    for q in data["questions"]:
        if not q.get("question_text") or q.get("marks") is None:
            raise ValueError("A question is missing required fields.")
        # Clamp marks to [min_marks, max_marks] instead of rejecting the whole batch
        q["marks"] = max(min_marks, min(max_marks, int(q["marks"])))

    return data["questions"]


# ── main entry point ──────────────────────────────────────────────────────────

def generate_questions(
    *,
    notes_text: str,
    num_questions: int,
    min_marks: int,
    max_marks: int,
    difficulty: str,
) -> list[dict]:
    """
    Call Gemini to generate quiz questions from notes text.
    Marks vary per question within [min_marks, max_marks].
    Retries the parse once if the first attempt fails.
    Raises ExternalServiceError if Gemini is unavailable or both attempts fail.
    """
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    prompt = PROMPT_TEMPLATE.format(
        num_questions=num_questions,
        difficulty=difficulty,
        min_marks=min_marks,
        max_marks=max_marks,
        notes_text=notes_text,
    )

    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    # First attempt
    try:
        response = model.generate_content(prompt)
        return _parse_questions(response.text, min_marks, max_marks)
    except (ValueError, json.JSONDecodeError):
        pass  # parsing failed, try once more

    # Second attempt (one retry)
    try:
        response = model.generate_content(prompt)
        return _parse_questions(response.text, min_marks, max_marks)
    except Exception as exc:
        raise ExternalServiceError(
            f"Gemini quiz generation failed after retry: {exc}"
        ) from exc
