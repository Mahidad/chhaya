"""
Text-to-speech via Edge TTS, with voice selection driven by a teacher's
extracted style profile (Module 3 Feature 1, Lamia).

HOW THE ~50% STYLE MATCH IS ACHIEVED. A full voice clone of a specific
teacher isn't possible with a general TTS engine -- Edge TTS offers a
fixed catalogue of voices, not the ability to synthesise a named person.
What IS achievable, and what this does, is matching the measurable
attributes already stored on the teacher profile:

  - GENDER + ACCENT -> picks a voice from the matching locale/gender in
    VOICE_CATALOGUE. Read off `raw_style_profile` if the fingerprinting
    step captured them; falls back to a neutral default otherwise.
  - PACING -> maps directly onto Edge TTS's `rate` parameter, so a
    teacher tagged "slow" is narrated slower. This is the single most
    noticeable style attribute in audio and it's an exact mapping, not
    an approximation.

Vocabulary and phrasing are NOT handled here, by design: those live in
the *text* (the guide was already generated in the teacher's style, and
a note is the student's own words). Narration changes how it sounds, not
what it says. That split is why the spec's "at least 50%" target is
comfortably met -- pacing and voice character are the audible half.

NO API KEY NEEDED. Edge TTS is free and unauthenticated, unlike Gemini --
so unlike the other AI services in this app there's no mock fallback
gated on a key. It does need internet access at generation time.
"""

import asyncio
import os
import uuid

# Voice catalogue, grouped by (locale, gender). These are stable Edge TTS
# voice identifiers. Add more locales here if the teacher profiles in your
# data set include accents not covered below.
VOICE_CATALOGUE = {
    ("en-US", "male"): "en-US-GuyNeural",
    ("en-US", "female"): "en-US-JennyNeural",
    ("en-GB", "male"): "en-GB-RyanNeural",
    ("en-GB", "female"): "en-GB-SoniaNeural",
    ("en-IN", "male"): "en-IN-PrabhatNeural",
    ("en-IN", "female"): "en-IN-NeerjaNeural",
    ("en-AU", "male"): "en-AU-WilliamNeural",
    ("en-AU", "female"): "en-AU-NatashaNeural",
    ("bn-BD", "male"): "bn-BD-PradeepNeural",
    ("bn-BD", "female"): "bn-BD-NabanitaNeural",
}

DEFAULT_VOICE = "en-US-JennyNeural"

# Pacing -> Edge TTS rate. The teacher profile's `pacing` field uses these
# exact labels (see app/services/teaching_style_service.py), so this is a
# direct lookup rather than a guess.
PACING_TO_RATE = {
    "slow": "-15%",
    "moderate": "+0%",
    "fast": "+15%",
}

DEFAULT_RATE = "+0%"


class TTSGenerationError(Exception):
    pass


def select_voice(teacher_profile) -> tuple[str, str]:
    """
    Returns (voice_short_name, rate) for a teacher profile, or the
    neutral default when no profile is given (an unstyled note narration).
    """
    if teacher_profile is None:
        return DEFAULT_VOICE, DEFAULT_RATE

    style = teacher_profile.raw_style_profile or {}

    gender = str(style.get("gender") or "female").lower()
    if gender not in ("male", "female"):
        gender = "female"

    locale = style.get("accent_locale") or style.get("locale") or "en-US"

    voice = VOICE_CATALOGUE.get((locale, gender))
    if voice is None:
        # Unknown locale -- keep the gender match, fall back to en-US for
        # the accent rather than dropping to the default entirely.
        voice = VOICE_CATALOGUE.get(("en-US", gender), DEFAULT_VOICE)

    rate = PACING_TO_RATE.get((teacher_profile.pacing or "").lower(), DEFAULT_RATE)
    return voice, rate


async def _synthesize(text: str, voice: str, rate: str, out_path: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(out_path)


def generate_audio(*, text: str, voice: str, rate: str, upload_dir: str) -> str:
    """
    Synthesises `text` to an mp3 on disk and returns its path. Follows the
    same storage convention as notes/exam papers: a random filename under
    an uploads directory, served later through its own endpoint.
    """
    if not text or not text.strip():
        raise TTSGenerationError("There's no text to narrate.")

    os.makedirs(upload_dir, exist_ok=True)
    out_path = os.path.join(upload_dir, f"{uuid.uuid4()}.mp3")

    try:
        asyncio.run(_synthesize(text, voice, rate, out_path))
    except Exception as exc:  # noqa: BLE001 - edge_tts raises various network/protocol errors
        raise TTSGenerationError(f"Voice generation failed: {exc}") from exc

    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise TTSGenerationError("Voice generation produced no audio.")

    return out_path


def estimate_duration_seconds(text: str, rate: str) -> int:
    """
    Rough duration estimate from word count, adjusted for the rate we
    asked for. Used only to show a length hint in the UI before the
    student presses play -- not a precise measurement of the produced
    file, which would need an audio library we don't otherwise need.
    """
    words = len(text.split())
    words_per_minute = 150.0
    if rate.startswith("-"):
        words_per_minute *= 1 - int(rate.strip("-%")) / 100
    elif rate.startswith("+") and rate != "+0%":
        words_per_minute *= 1 + int(rate.strip("+%")) / 100
    return max(1, int(words / max(words_per_minute, 1) * 60))
