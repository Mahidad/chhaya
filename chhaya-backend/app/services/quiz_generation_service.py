"""Gemini interaction for Module 3 Feature 7 – generating quiz questions.

Pattern is identical to likely_question_generation_service.py:
  - Build a prompt
  - Call Gemini (or return a mock if no key is set)
  - Parse the JSON response
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
- Each question is worth {marks} marks
- Question types should be short-answer or explain-in-your-own-words (no MCQ)
- Base questions ONLY on the content in the notes below

Return ONLY valid JSON in exactly this shape (no extra text, no markdown fences):
{{
  "questions": [
    {{
      "question_text": "the question",
      "marks": {marks},
      "difficulty": "{difficulty}"
    }}
  ]
}}

Student notes:
{notes_text}
"""


# ── mock fallback (used when GEMINI_API_KEY is not set) ───────────────────────

def _mock_questions(num_questions: int, marks: int, difficulty: str) -> list[dict]:
    """Return placeholder questions so the rest of the feature still works locally."""
    return [
        {
            "question_text": f"[Mock question {i + 1}] Explain a key concept from your notes in your own words.",
            "marks": marks,
            "difficulty": difficulty,
        }
        for i in range(num_questions)
    ]


# ── JSON parsing ──────────────────────────────────────────────────────────────

def _parse_questions(text: str) -> list[dict]:
    """Strip markdown fences if present, then parse JSON and validate shape."""
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

    return data["questions"]


# ── main entry point ──────────────────────────────────────────────────────────

def generate_questions(
    *,
    notes_text: str,
    num_questions: int,
    marks_per_question: int,
    difficulty: str,
) -> list[dict]:
    """
    Call Gemini to generate quiz questions from notes text.
    Retries the parse once if the first attempt fails.
    Falls back to mock questions if no API key is configured.
    """
    if not settings.GEMINI_API_KEY:
        return _mock_questions(num_questions, marks_per_question, difficulty)

    prompt = PROMPT_TEMPLATE.format(
        num_questions=num_questions,
        difficulty=difficulty,
        marks=marks_per_question,
        notes_text=notes_text,
    )

    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    # First attempt
    try:
        response = model.generate_content(prompt)
        return _parse_questions(response.text)
    except (ValueError, json.JSONDecodeError):
        pass  # parsing failed, try once more

    # Second attempt (one retry)
    try:
        response = model.generate_content(prompt)
        return _parse_questions(response.text)
    except Exception as exc:
        raise ExternalServiceError(
            f"Gemini quiz generation failed after retry: {exc}"
        ) from exc
