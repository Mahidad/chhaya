"""Gemini calls for analysing papers and producing practice predictions."""

import json

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError


PROMPT_TEMPLATE = """You are an academic exam-pattern analyst. Analyse the
OCR text from past exam papers below, then generate likely practice questions.
These are study predictions only, not leaked or guaranteed exam questions.

Return ONLY valid JSON in exactly this shape:
{{
  "analysis": {{
    "question_types": ["short description"],
    "point_distribution": "summary of marks/points patterns",
    "section_breakdown": ["section summary"],
    "phrasing_style": "summary of typical wording",
    "coverage_notes": "brief statement of recurring topics and limits"
  }},
  "predicted_questions": [
    {{
      "question": "practice question",
      "estimated_marks": 5,
      "question_type": "short answer | problem solving | essay | other",
      "rationale": "briefly tie this to a recurring pattern"
    }}
  ]
}}

Generate exactly {question_count} questions. Do not claim certainty, access to
future exams, or access to material beyond these papers.

Past-paper OCR text:
{papers}
"""


def _mock_result(*, question_count: int, papers: list[dict]) -> dict:
    titles = ", ".join(p["title"] for p in papers[:3]) or "the selected papers"
    return {
        "analysis": {
            "question_types": ["Short-answer definitions", "Explain-and-apply questions"],
            "point_distribution": "Mock analysis: inspect the selected papers for exact marks.",
            "section_breakdown": ["Mock analysis based on selected papers"],
            "phrasing_style": "Often asks students to define, explain, compare, or apply concepts.",
            "coverage_notes": f"Mock result generated from {titles}. Add GEMINI_API_KEY for a real analysis.",
            "_mock": True,
        },
        "predicted_questions": [
            {
                "question": f"Practice question {number}: Explain a core concept that appears in the selected past papers and apply it to a new example.",
                "estimated_marks": 5,
                "question_type": "Explain and apply",
                "rationale": "Mock prediction based on the selected paper set; it is not a guarantee.",
            }
            for number in range(1, question_count + 1)
        ],
    }


def _parse_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    result = json.loads(cleaned.strip())
    if not isinstance(result.get("analysis"), dict) or not isinstance(result.get("predicted_questions"), list):
        raise ValueError("Gemini returned an unexpected question-set structure.")
    return result


def analyze_and_predict(*, papers: list[dict], question_count: int) -> dict:
    if not settings.GEMINI_API_KEY:
        return _mock_result(question_count=question_count, papers=papers)

    try:
        paper_text = "\n\n".join(
            f"--- {paper['title']} ---\n{paper['extracted_text']}"
            for paper in papers
        )
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        response = genai.GenerativeModel(settings.GEMINI_MODEL).generate_content(
            PROMPT_TEMPLATE.format(papers=paper_text[:45000], question_count=question_count)
        )
        return _parse_json(response.text)
    except Exception as exc:  # noqa: BLE001
        raise ExternalServiceError(f"Gemini likely-question generation failed: {exc}") from exc
