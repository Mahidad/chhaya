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
from app.utils.tts import AVAILABLE_VOICES, DEFAULT_VOICE

_VOICE_CHOICES = ", ".join(f'"{v["id"]}" ({v["label"]})' for v in AVAILABLE_VOICES)

STYLE_PROMPT_TEMPLATE = """You are analyzing a teaching transcript to build a
structured "teaching style profile". Read the transcript and respond with
ONLY a JSON object (no markdown, no commentary) matching exactly this shape:

{{
  "pacing": "slow" | "moderate" | "fast",
  "vocabulary_level": "beginner" | "intermediate" | "advanced",
  "analogy_frequency": "low" | "medium" | "high",
  "example_density": "low" | "medium" | "high",
  "concept_sequencing_notes": "<one or two sentences describing how the teacher orders ideas>",
  "signature_phrases": ["<short phrase>", "..."],
  "narration_voice_guess": "<your best-effort guess at which ONE of these
    voice ids sounds closest to this teacher, based on the channel name
    below and any self-introduction/phrasing in the transcript. This is
    necessarily a guess, not a fact -- you cannot hear the actual audio,
    only read text. Pick exactly one id from this list: {voice_choices}>"
}}

Channel name (may hint at gender/region, e.g. a personal name): "{channel_name}"

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
        "narration_voice_guess": DEFAULT_VOICE,
        "_mock": True,
    }


def analyze_style(transcript_text: str, channel_name: str | None = None) -> dict:
    if not settings.GEMINI_API_KEY:
        return _mock_style_profile(transcript_text)

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        prompt = STYLE_PROMPT_TEMPLATE.format(
            transcript=transcript_text[:15000],
            channel_name=channel_name or "unknown",
            voice_choices=_VOICE_CHOICES,
        )
        response = model.generate_content(prompt)
        text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        style = json.loads(text)
        # Gemini can hallucinate an id outside the list we gave it --
        # never trust free-form model output as a value that's about to
        # be used to pick a real voice; fall back to the default instead
        # of silently storing a voice id that doesn't exist.
        valid_ids = {v["id"] for v in AVAILABLE_VOICES}
        if style.get("narration_voice_guess") not in valid_ids:
            style["narration_voice_guess"] = DEFAULT_VOICE
        return style
    except Exception as exc:  # noqa: BLE001 - any failure here should degrade, not crash ingestion
        raise ExternalServiceError(f"Gemini style analysis failed: {exc}") from exc
