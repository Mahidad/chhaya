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

from functools import lru_cache

from app.core.config import settings


@lru_cache(maxsize=1)
def _client():
    from google import genai

    return genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_text(contents) -> str:
    """Send `contents` to the configured model and return the reply text.

    `contents` is either a prompt string, or a list mixing strings and parts
    from file_part() for multimodal requests.

    Returns the raw text -- callers own their own parsing, because they
    disagree about it: some expect JSON in a fenced block, some expect prose.
    """
    response = _client().models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=contents,
    )
    return response.text


def file_part(*, data: bytes, mime_type: str):
    """A PDF or image to send alongside a prompt.

    Takes RAW bytes. The old SDK accepted a dict holding base64-encoded text;
    this one does the encoding itself, so base64-encoding first would send
    the model a picture of base64.
    """
    from google.genai import types

    return types.Part.from_bytes(data=data, mime_type=mime_type)
