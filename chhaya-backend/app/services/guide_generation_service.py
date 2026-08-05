"""
Turns (topic + a teacher's style profile) into guide text using Gemini.

Same mock-fallback shape as teaching_style_service.py, deliberately --
Lamia shouldn't have to invent this pattern from scratch when it already
exists once in the codebase. If GEMINI_API_KEY isn't set, this returns
clearly-labeled placeholder text instead of failing, so the rest of the
pipeline (saving, status transitions, the frontend polling) can be built
and tested without an API key.

WHAT'S DELIBERATELY NOT HERE: PDF export and real Bangla translation.
Both are listed in the functional requirements doc as part of this
feature, but neither is "generate text with an AI" -- PDF export is a
rendering step (reuse the same skill/library pattern the docx/pdf
generation elsewhere in this course uses), and Bangla needs an actual
translation call (Gemini can do this too, but it's a second, separate
prompt, not a side effect of this one). `bangla_content` and a PDF
download endpoint are the two natural next additions here.
"""

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError

GUIDE_PROMPT_TEMPLATE = """You are writing a study guide chapter on "{topic}"
for a student, in the teaching style described below. Match the pacing,
vocabulary level, and use of analogies described. Depth: {depth}.

Teaching style:
- Pacing: {pacing}
- Vocabulary level: {vocabulary_level}
- Analogy frequency: {analogy_frequency}
- Example density: {example_density}
- Notes on how this teacher sequences ideas: {sequencing_notes}

Respond with ONLY the guide's body text (no JSON, no markdown headers) --
plain prose organized into clear sections a student can read top to bottom.
"""

FORMULA_SHEET_PROMPT_TEMPLATE = """Extract a condensed formula sheet for the
STEM topic "{topic}" -- key formulas only, one per line, no explanation."""


def _mock_guide(topic: str, depth: str) -> str:
    return (
        f"MOCK GUIDE (no GEMINI_API_KEY set) — {depth} depth chapter on {topic}.\n\n"
        f"This is placeholder text so the rest of the pipeline (saving, status "
        f"transitions, the frontend's generating→ready screen) can be built and "
        f"tested before a real Gemini key is added. Set GEMINI_API_KEY in .env "
        f"to get real generated content here."
    )


def _mock_formula_sheet(topic: str) -> str:
    return f"MOCK FORMULA SHEET (no GEMINI_API_KEY set) for {topic}."


def generate_guide_text(*, topic: str, depth: str, style: dict) -> str:
    if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.startswith("AIzaSy"):
        return _mock_guide(topic, depth)
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        prompt = GUIDE_PROMPT_TEMPLATE.format(
            topic=topic,
            depth=depth,
            pacing=style.get("pacing", "moderate"),
            vocabulary_level=style.get("vocabulary_level", "intermediate"),
            analogy_frequency=style.get("analogy_frequency", "medium"),
            example_density=style.get("example_density", "medium"),
            sequencing_notes=style.get("concept_sequencing_notes", "not specified"),
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:  # noqa: BLE001
        raise ExternalServiceError(f"Gemini guide generation failed: {exc}") from exc


def generate_formula_sheet(*, topic: str) -> str:
    if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.startswith("AIzaSy"):
        return _mock_formula_sheet(topic)
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(FORMULA_SHEET_PROMPT_TEMPLATE.format(topic=topic))
        return response.text.strip()
    except Exception as exc:  # noqa: BLE001
        raise ExternalServiceError(f"Gemini formula sheet generation failed: {exc}") from exc
