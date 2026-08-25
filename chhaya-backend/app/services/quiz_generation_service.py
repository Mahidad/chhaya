"""Gemini interaction for Module 3 Feature 7 – generating quiz questions.

Flow:
  - Build a prompt
  - Call Gemini with either plain text or a multimodal file (PDF/image)
  - Parse the JSON response, clamping marks to [min_marks, max_marks]
  - Retry once if parsing fails
  - Raise ExternalServiceError on second failure
"""

import json
import mimetypes
import os

from app.core.config import settings
from app.utils import gemini
from app.utils.exceptions import ExternalServiceError


# ── prompt instructions (shared by both text and multimodal paths) ────────────

def _build_prompt(*, num_questions: int, min_marks: int, max_marks: int, difficulty: str, notes_text: str | None = None) -> str:
    """
    Build the quiz-generation prompt.

    When notes_text is provided it is appended at the end (text path).
    For multimodal calls, notes_text is omitted — Gemini reads the file instead.
    """
    rules = f"""You are a quiz generator for a student learning platform.
Generate exactly {num_questions} quiz questions based on the study material provided.

Rules:
- Difficulty level for ALL questions must be: {difficulty}
- Each question must have an individual marks value between {min_marks} and {max_marks}
- Assign higher marks to questions that are more complex or require deeper explanation
- Question types should be short-answer or explain-in-your-own-words (no MCQ)
- Base questions ONLY on the content in the provided material

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
}}"""

    if notes_text:
        return rules + f"\n\nStudent notes:\n{notes_text}\n"
    return rules


# ── file encoding helper ──────────────────────────────────────────────────────

def _encode_file(file_path: str) -> tuple[str, bytes] | None:
    """
    Read a file from disk and return (mime_type, file_bytes).

    Returns None if the file is missing or unreadable — caller should skip it.
    The mime_type is guessed from the file extension:
      .pdf   → application/pdf
      .png   → image/png
      .jpg   → image/jpeg
      .jpeg  → image/jpeg
      (others attempted via mimetypes module, fall back to application/octet-stream)
    """
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    except OSError:
        return None

    # Guess the mime type from the extension
    guessed, _ = mimetypes.guess_type(file_path)
    mime_type = guessed or "application/octet-stream"

    return mime_type, file_bytes


# ── JSON parsing (shared) ─────────────────────────────────────────────────────

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



# ── text-based generation ─────────────────────────────────────────────────────

def generate_questions(
    *,
    notes_text: str,
    num_questions: int,
    min_marks: int,
    max_marks: int,
    difficulty: str,
) -> list[dict]:
    """
    Call Gemini with plain text notes to generate quiz questions.
    Marks vary per question within [min_marks, max_marks].
    Retries the parse once if the first attempt fails.
    Raises ExternalServiceError if Gemini is unavailable or both attempts fail.
    """
    prompt = _build_prompt(
        num_questions=num_questions,
        difficulty=difficulty,
        min_marks=min_marks,
        max_marks=max_marks,
        notes_text=notes_text,
    )

    # First attempt
    try:
        response_text = gemini.generate_text(prompt)
        return _parse_questions(response_text, min_marks, max_marks)
    except (ValueError, json.JSONDecodeError):
        pass  # parsing failed, try once more

    # Second attempt (one retry)
    try:
        response_text = gemini.generate_text(prompt)
        return _parse_questions(response_text, min_marks, max_marks)
    except Exception as exc:
        raise ExternalServiceError(
            f"Gemini quiz generation failed after retry: {exc}"
        ) from exc


# ── multimodal generation (PDF / image notes) ─────────────────────────────────

def generate_questions_from_file(
    *,
    file_path: str,
    num_questions: int,
    min_marks: int,
    max_marks: int,
    difficulty: str,
) -> list[dict]:
    """
    Call Gemini with a PDF or image file to generate quiz questions.

    The file is sent as an inline multimodal part alongside the text prompt
    instructions.  Same retry-once-then-raise behavior as
    the text path — no mock fallback.

    Raises ValueError if the file cannot be read before even calling Gemini.
    Raises ExternalServiceError if Gemini fails after retry.
    """
    encoded = _encode_file(file_path)
    if encoded is None:
        raise ValueError(
            f"Could not read the note file from disk. "
            "Please re-upload the note and try again."
        )

    mime_type, file_bytes = encoded
    prompt_text = _build_prompt(
        num_questions=num_questions,
        difficulty=difficulty,
        min_marks=min_marks,
        max_marks=max_marks,
    )

    # Gemini multimodal content: one inline file part + the prompt text.
    # file_part takes RAW bytes -- the SDK base64-encodes internally, so
    # encoding here first would send the model a picture of base64.
    content = [
        gemini.file_part(data=file_bytes, mime_type=mime_type),
        prompt_text,
    ]

    # First attempt
    try:
        response_text = gemini.generate_text(content)
        return _parse_questions(response_text, min_marks, max_marks)
    except (ValueError, json.JSONDecodeError):
        pass  # parsing failed, try once more

    # Second attempt (one retry)
    try:
        response_text = gemini.generate_text(content)
        return _parse_questions(response_text, min_marks, max_marks)
    except Exception as exc:
        raise ExternalServiceError(
            f"Gemini multimodal quiz generation failed after retry: {exc}"
        ) from exc
