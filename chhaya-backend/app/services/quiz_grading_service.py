"""Gemini grading logic for Module 3 Feature 8 – Quiz Evaluation.

For each question-answer pair, one Gemini call is made requesting:
  - marks_obtained (int, 0 to the question's max marks)
  - feedback (short comment for the student)

If parsing fails, one retry is attempted. If the retry also fails,
0 marks and "Evaluation failed" are recorded for that question so
the rest of the quiz is not blocked.

After all questions are graded, backend arithmetic calculates:
  - total_score   = sum of marks_obtained
  - max_score     = sum of max marks across all questions
  - percentage    = (total_score / max_score) * 100
  - pass_status   = threshold classification (configurable at top of file)
"""

import json

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError


# ── threshold config ──────────────────────────────────────────────────────────
# Change these values to adjust what counts as pass/retake without touching
# any other file.

URGENT_RETAKE_BELOW = 50     # percentage < 50 → need_urgent_retake
REQUIRED_RETAKE_BELOW = 75   # percentage < 75 → required_retake
                              # percentage >= 75 → good_job


# ── prompt ────────────────────────────────────────────────────────────────────

def _build_prompt(question_text: str, max_marks: int, answer_text: str) -> str:
    """Build the per-question grading prompt."""
    return f"""You are grading a student's short answer for an exam question.

Question: {question_text}
Maximum marks: {max_marks}
Student's answer: {answer_text}

Grade the answer honestly. Return ONLY valid JSON with no extra text:
{{
  "marks_obtained": <integer from 0 to {max_marks}>,
  "feedback": "<one or two sentences of constructive feedback>"
}}
"""


# ── JSON parser ───────────────────────────────────────────────────────────────

def _parse_grade(text: str, max_marks: int) -> dict:
    """Strip markdown fences, parse JSON, validate marks range."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])

    data = json.loads(cleaned.strip())

    marks = data.get("marks_obtained")
    feedback = data.get("feedback", "")

    if marks is None or not isinstance(marks, int):
        raise ValueError("marks_obtained missing or not an integer")

    # Clamp to valid range just in case Gemini goes out of bounds
    marks = max(0, min(marks, max_marks))

    return {"marks_obtained": marks, "feedback": str(feedback)}


# ── mock fallback ─────────────────────────────────────────────────────────────

def _mock_grade(max_marks: int) -> dict:
    """Fake grade returned when no API key is set — gives half marks."""
    return {
        "marks_obtained": max_marks // 2,
        "feedback": "[Mock] No GEMINI_API_KEY set. Half marks awarded as placeholder.",
    }


# ── grade one answer ──────────────────────────────────────────────────────────

def grade_one_answer(
    question_text: str,
    max_marks: int,
    answer_text: str,
) -> dict:
    """
    Call Gemini to grade one answer. Returns {marks_obtained, feedback}.
    Retries once on parse failure. Returns {0, "Evaluation failed"} on
    second failure so the rest of the quiz is not blocked.
    """
    if not settings.GEMINI_API_KEY:
        return _mock_grade(max_marks)

    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    prompt = _build_prompt(question_text, max_marks, answer_text)

    # First attempt
    try:
        response = model.generate_content(prompt)
        return _parse_grade(response.text, max_marks)
    except (ValueError, json.JSONDecodeError, Exception):
        pass  # parsing failed — try once more

    # Second attempt (one retry)
    try:
        response = model.generate_content(prompt)
        return _parse_grade(response.text, max_marks)
    except Exception:
        # Return 0 marks for this question rather than failing the whole quiz
        return {"marks_obtained": 0, "feedback": "Evaluation failed for this question."}


# ── classify status ───────────────────────────────────────────────────────────

def classify_status(percentage: float) -> str:
    """
    Turn a percentage into a human-readable status string.
    Thresholds are defined at the top of this file.
    """
    if percentage < URGENT_RETAKE_BELOW:
        return "need_urgent_retake"
    if percentage < REQUIRED_RETAKE_BELOW:
        return "required_retake"
    return "good_job"


# ── main entry point ──────────────────────────────────────────────────────────

def grade_quiz(
    *,
    questions: list,
    answers: list,
) -> dict:
    """
    Grade all answers for a quiz.

    questions: list of QuizQuestion objects (with .id, .question_text, .marks)
    answers:   list of dicts [{question_id, answer_text}] from the quiz row

    Returns a dict with:
      total_score, max_score, percentage, pass_status, graded_answers
    where graded_answers is a list of per-question dicts.
    """
    # Build a lookup so we can find an answer by question_id quickly
    answer_map = {a["question_id"]: a["answer_text"] for a in answers}

    graded_answers = []
    total_score = 0
    max_score = 0

    for q in questions:
        answer_text = answer_map.get(q.id, "")  # blank if student skipped
        result = grade_one_answer(q.question_text, q.marks, answer_text)

        graded_answers.append({
            "question_id":   q.id,
            "question_text": q.question_text,
            "answer_text":   answer_text,
            "marks_obtained": result["marks_obtained"],
            "max_marks":      q.marks,
            "feedback":       result["feedback"],
        })

        total_score += result["marks_obtained"]
        max_score   += q.marks

    # Calculate percentage (guard against division by zero)
    if max_score == 0:
        percentage = 0.0
    else:
        percentage = round((total_score / max_score) * 100, 2)

    pass_status = classify_status(percentage)

    return {
        "total_score":    total_score,
        "max_score":      max_score,
        "percentage":     percentage,
        "pass_status":    pass_status,
        "graded_answers": graded_answers,
    }
