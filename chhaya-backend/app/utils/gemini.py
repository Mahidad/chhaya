"""
The single place this codebase talks to the Gemini SDK.

WHY IT EXISTS: the same three lines (import, configure, construct a model)
were repeated in eleven places across ten services. When Google ended support
for `google.generativeai` and replaced it with `google.genai`, that meant
eleven identical edits -- and the next SDK change would mean eleven more.
Everything now goes through generate_text() below, so a future migration is
one file.

WHY THE IMPORT IS INSIDE THE FUNCTION: importing the SDK is not free, and the
app must start and serve non-AI routes on a machine where GEMINI_API_KEY was
never set. Callers already check `if not settings.GEMINI_API_KEY` and fall
back to their mock responses before reaching this module.

THE CLIENT IS CACHED because it holds connection state; rebuilding it per
request would add a handshake to every AI call.
"""

import random
import time
from functools import lru_cache

from app.core.config import settings


@lru_cache(maxsize=1)
def _client():
    from google import genai

    return genai.Client(api_key=settings.GEMINI_API_KEY)


# Gemini's flash models return 503 UNAVAILABLE ("experiencing high demand")
# intermittently -- often enough that a single-shot call fails several times an
# hour under no unusual load. One retry usually succeeds immediately.
_TRANSIENT_ATTEMPTS = 4
_TRANSIENT_BACKOFF = 1.0  # seconds; doubles each attempt, plus jitter


def generate_text(contents) -> str:
    """Send `contents` to the configured model and return the reply text.

    `contents` is either a prompt string, or a list mixing strings and parts
    from file_part() for multimodal requests.

    Returns the raw text -- callers own their own parsing, because they
    disagree about it: some expect JSON in a fenced block, some expect prose.

    RETRIES ONLY 5xx. A 503 means the model is momentarily busy and the same
    request will very likely succeed a second later. A 4xx will not: 429 is a
    quota that retrying only burns faster, and 404 means GEMINI_MODEL names a
    model that does not exist, which no amount of waiting fixes.
    """
    from google.genai import errors

    last_exc = None
    for attempt in range(_TRANSIENT_ATTEMPTS):
        try:
            response = _client().models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
            )
            return response.text
        except errors.ServerError as exc:
            last_exc = exc
            if attempt == _TRANSIENT_ATTEMPTS - 1:
                break
            delay = _TRANSIENT_BACKOFF * (2**attempt) + random.uniform(0, 0.4)
            print(
                f"[gemini] {settings.GEMINI_MODEL} returned a transient error "
                f"({str(exc)[:80]}); retrying in {delay:.1f}s "
                f"({attempt + 1}/{_TRANSIENT_ATTEMPTS - 1})"
            )
            time.sleep(delay)
        except errors.ClientError as exc:
            # Make the single most common misconfiguration self-explanatory
            # instead of surfacing a raw 404 to the user.
            if "NOT_FOUND" in str(exc):
                raise RuntimeError(
                    f"GEMINI_MODEL is set to {settings.GEMINI_MODEL!r}, which this "
                    "API key cannot use -- the model may have been retired. "
                    "Check the current list at ai.google.dev/gemini-api/docs/models."
                ) from exc
            raise

    raise RuntimeError(
        f"{settings.GEMINI_MODEL} was unavailable after {_TRANSIENT_ATTEMPTS} "
        f"attempts: {last_exc}"
    ) from last_exc


def file_part(*, data: bytes, mime_type: str):
    """A PDF or image to send alongside a prompt.

    Takes RAW bytes. The old SDK accepted a dict holding base64-encoded text;
    this one does the encoding itself, so base64-encoding first would send
    the model a picture of base64.
    """
    from google.genai import types

    return types.Part.from_bytes(data=data, mime_type=mime_type)
