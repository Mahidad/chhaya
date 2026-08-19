"""
Local wrapper around `edge-tts` -- Module 3's Voice Narration (Lamia).
Same "one function everything else calls" shape as utils/ocr.py and
utils/youtube.py, so if the underlying library's interface ever changes,
only this file needs to know.

WHAT EDGE-TTS ACTUALLY IS: a third-party package that talks to the same
backend Microsoft Edge's browser uses for its built-in "Read aloud"
feature. It IS an external network call (audio is synthesized on
Microsoft's servers, not locally) -- but unlike Gemini, it needs no API
key and has no billing, because it's riding on infrastructure Edge itself
already uses for free. It's unofficial/reverse-engineered, though, so
(same caution as youtube-transcript-api and yt-dlp elsewhere in this
project) Microsoft could change or throttle it without notice.

WHY NO SSML / PER-SENTENCE PAUSES HERE: edge-tts's public interface takes
one block of text plus a handful of GLOBAL dials (voice, rate, pitch) --
it does not accept different pause/emphasis instructions per sentence.
Getting that would mean generating SSML with Gemini and splicing multiple
separately-synthesized audio clips together (a new dependency on an audio
library like pydub/ffmpeg). Instead, the personalization happens two
cheaper ways: (1) narration_generation_service.py has Gemini rewrite the
source text into phrasing that *reads* well aloud -- shorter sentences,
natural comma/period pacing, matching punctuation to tone -- which neural
voices already interpret reasonably well on their own, and (2) `rate` is
derived directly from the teacher profile's `pacing` field below, no
extra AI call needed for that part at all.
"""

import asyncio
import os
import wave

# A small curated subset of Edge's neural voices -- enough variety
# (accent x gender) to matter, short enough to show as a real dropdown
# instead of an overwhelming list of 100+ options.
AVAILABLE_VOICES = [
    {"id": "en-US-AriaNeural", "label": "Aria (US, female)"},
    {"id": "en-US-GuyNeural", "label": "Guy (US, male)"},
    {"id": "en-GB-SoniaNeural", "label": "Sonia (UK, female)"},
    {"id": "en-GB-RyanNeural", "label": "Ryan (UK, male)"},
    {"id": "en-AU-NatashaNeural", "label": "Natasha (AU, female)"},
    {"id": "en-IN-PrabhatNeural", "label": "Prabhat (IN, male)"},
]
DEFAULT_VOICE = AVAILABLE_VOICES[0]["id"]

# The teacher profile's `pacing` field (from the teaching-style analysis)
# maps straight to edge-tts's `rate` parameter -- this is real data, not
# a guess, unlike the voice/accent guess above.
_PACING_TO_RATE = {
    "slow": "-15%",
    "moderate": "+0%",
    "fast": "+15%",
}


def list_available_voices() -> list[dict]:
    return AVAILABLE_VOICES


def rate_for_pacing(style: dict) -> str:
    """style is a teacher profile's raw_style_profile dict (or {} for a
    note being narrated with no style attached, though in practice a
    note always has a resolved teacher_profile by the time this is
    called -- see narration_service.create_and_generate)."""
    return _PACING_TO_RATE.get((style or {}).get("pacing"), "+0%")


def _mock_synthesize(output_path: str) -> None:
    """
    Writes a short silent WAV file using only the standard library (no
    edge-tts dependency needed for this path) so the rest of the pipeline
    -- saving, status transitions, the frontend's audio player -- is
    fully buildable and testable before edge-tts is installed/working.
    Saved with a .wav extension regardless of the real output_path's
    extension, since we can't fabricate a real MP3 without the library.
    """
    silent_path = os.path.splitext(output_path)[0] + ".wav"
    with wave.open(silent_path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b"\x00\x00" * 16000)  # 1 second of silence
    return silent_path


async def _synthesize_async(text: str, voice: str, rate: str, output_path: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


def synthesize(text: str, voice: str, rate: str, output_path: str) -> tuple[str, bool]:
    """
    Synthesizes `text` as speech and writes it to output_path (an .mp3
    path). Returns (actual_path_written, is_mock) -- actual_path may
    differ from output_path in mock mode (see _mock_synthesize).

    edge-tts's own interface is async (it streams audio over a
    websocket); every other network call in this codebase (Gemini,
    youtube-transcript-api) is synchronous, so this wraps the async call
    in asyncio.run() to keep narration_service.py's orchestration code
    looking like everything else in app/services/ -- plain, top-to-bottom
    synchronous functions.
    """
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        return _mock_synthesize(output_path), True

    try:
        asyncio.run(_synthesize_async(text, voice, rate, output_path))
        return output_path, False
    except Exception:  # noqa: BLE001 -- network hiccup, rate limit, voice id typo, etc.
        return _mock_synthesize(output_path), True
