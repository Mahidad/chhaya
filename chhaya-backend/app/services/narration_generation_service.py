"""
Turns (source text + a teacher's style profile) into a version of that
text rewritten to *read well aloud* -- Module 3's Voice Narration
(Lamia). Same mock-fallback shape as guide_generation_service.py,
deliberately, for the same reason: this is the second time this exact
pattern (call Gemini, fall back to labeled placeholder text if no key)
shows up in the codebase, so there was no reason to invent a new one.

WHAT THIS DOES NOT DO: insert SSML markup (<break>, <prosody>, etc.).
edge-tts doesn't accept per-sentence instructions (see app/utils/tts.py's
docstring for why), so this prompt only asks for better PUNCTUATION --
shorter sentences, natural pause commas, matching emphasis punctuation to
tone -- which neural TTS voices already read naturally on their own. The
teacher's actual speaking speed is handled separately and for free, by
mapping `pacing` straight to edge-tts's `rate` parameter in
app/utils/tts.py -- no AI call needed for that part.
WHAT THIS DOES DO: incorporates the teacher's actual word choices and
recurring phrases (Mahidad's Feature 1 already extracts these as
`signature_phrases` and `concept_sequencing_notes` -- e.g. a StatQuest-style
profile might capture "BAM" as a signature phrase) into the rewrite, so the
narration at least *uses the teacher's own vocabulary* even though it can't
reproduce their actual vocal delivery of it (see the limitation above).
This is "at least a partial match" on word/phrase choice, explicitly not a
claim of matching tone or comedic timing.
"""

from app.core.config import settings
from app.utils import gemini
from app.utils.exceptions import ExternalServiceError

NARRATION_REWRITE_PROMPT = """Rewrite the following study material so it
reads naturally when spoken aloud by a text-to-speech voice, in the style
of a teacher with this profile:

- Pacing: {pacing}
- Vocabulary level: {vocabulary_level}
- Analogy frequency: {analogy_frequency}
- How this teacher sequences ideas: {concept_sequencing_notes}
- Phrases this teacher tends to use (weave a couple in naturally, ONLY
  where they'd genuinely fit -- do not force one into every paragraph):
  {signature_phrases}

Rules:
- Do NOT add stage directions, SSML tags, or any markup -- plain sentences only.
- Break long sentences into shorter ones a listener can follow without re-reading.
- Use natural pause punctuation (commas, periods, occasional ellipses "...")
  where a real teacher would pause or take a breath.
- Use exclamation points or rhetorical questions sparingly, only where the
  original tone actually calls for emphasis -- don't overdo it.
- Strip out Markdown syntax (##, **, bullet dashes, LaTeX $...$) since this
  text will be spoken, not displayed -- describe formulas and structure in
  plain words instead of symbols.
- Keep the same meaning and factual content as the original. Do not
  shorten, summarize, or add new information.

Source material:
\"\"\"
{text}
\"\"\"

Respond with ONLY the rewritten, speakable text. No preamble, no notes.
"""


def _mock_rewrite(text: str) -> str:
    # Deliberately still produces *something* speakable so the rest of
    # the pipeline (saving, edge-tts synthesis, the frontend's ready
    # screen) can be exercised end-to-end without a Gemini key -- unlike
    # the mock guide/formula text elsewhere, this one is real source text
    # with light punctuation cleanup, not a placeholder sentence, since
    # it's about to actually be spoken aloud and a "MOCK NARRATION" label
    # read out by the voice would be a strange listening experience.
    import re
    cleaned = re.sub(r"[#*_`$]", "", text)
    cleaned = re.sub(r"\n{2,}", ". ", cleaned)
    return cleaned.strip()


def rewrite_for_narration(*, text: str, style: dict) -> str:
    if not settings.GEMINI_API_KEY:
        return _mock_rewrite(text)
    try:
        prompt = NARRATION_REWRITE_PROMPT.format(
            pacing=style.get("pacing", "moderate"),
            vocabulary_level=style.get("vocabulary_level", "intermediate"),
            analogy_frequency=style.get("analogy_frequency", "medium"),
            concept_sequencing_notes=style.get("concept_sequencing_notes") or "no particular pattern noted",
            signature_phrases=", ".join(style.get("signature_phrases") or []) or "none noted",
            text=text[:12000],  # token-budget guard, same idea as teaching_style_service.py
        )
        response_text = gemini.generate_text(prompt)
        return response_text.strip()
    except Exception as exc:  # noqa: BLE001
        raise ExternalServiceError(f"Gemini narration rewrite failed: {exc}") from exc
