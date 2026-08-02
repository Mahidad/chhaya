"""
Turns a raw transcript into a structured "teaching style fingerprint"
using Gemini.

WHY A MOCK FALLBACK:
Your team is learning this stack while building it, under a 2-month
deadline, with 4 people working in parallel. If Group 2/3/4's features
all need a real TeacherProfile row to build against, they shouldn't be
blocked waiting for someone to get a Gemini key working. When
GEMINI_API_KEY isn't set, `analyze_style` returns a realistic-shaped mock
instead of a real call -- same JSON shape, so nothing downstream needs to
change when the real key gets added later. Swap it out by setting
GEMINI_API_KEY in .env; no other file needs to change.
"""

import json

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError

STYLE_PROMPT_TEMPLATE = """You are analyzing a teaching transcript to build a
structured "teaching style profile". Read the transcript and respond with
ONLY a JSON object (no markdown, no commentary) matching exactly this shape:

{{
  "pacing": "slow" | "moderate" | "fast",
  "vocabulary_level": "beginner" | "intermediate" | "advanced",
  "analogy_frequency": "low" | "medium" | "high",
  "example_density": "low" | "medium" | "high",
  "concept_sequencing_notes": "<one or two sentences describing how the teacher orders ideas>",
  "signature_phrases": ["<short phrase>", "..."]
}}

Transcript:
\"\"\"
{transcript}
\"\"\"
"""


def _mock_style_profile(transcript_text: str) -> dict:
    word_count = len(transcript_text.split())
    return {
        "pacing": "moderate" if word_count > 500 else "fast",
        "vocabulary_level": "intermediate",
        "analogy_frequency": "medium",
        "example_density": "medium",
        "concept_sequencing_notes": (
            "MOCK PROFILE (no GEMINI_API_KEY set): builds on prior concepts "
            "step by step before introducing a new idea."
        ),
        "signature_phrases": ["let's break this down", "in other words"],
        "_mock": True,
    }


def analyze_style(transcript_text: str) -> dict:
    if not settings.GEMINI_API_KEY:
        return _mock_style_profile(transcript_text)

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        prompt = STYLE_PROMPT_TEMPLATE.format(transcript=transcript_text[:15000])
        response = model.generate_content(prompt)
        text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(text)
    except Exception as exc:  # noqa: BLE001 - any failure here should degrade, not crash ingestion
        raise ExternalServiceError(f"Gemini style analysis failed: {exc}") from exc
