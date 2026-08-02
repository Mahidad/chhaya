"""
Thin wrapper around `youtube-transcript-api`.

WHY WRAP IT INSTEAD OF CALLING IT DIRECTLY IN THE SERVICE:
`youtube-transcript-api`'s exact function names/exceptions can change
between versions (v1.x rewrote its whole interface from a classmethod
returning a list of dicts to an instance method returning a
FetchedTranscript object -- caught by the test run below), and one day
this call might get swapped for the official YouTube Data API. If every
place that needs a transcript calls this one function instead of the
library directly, that swap or version bump touches one file, not every
service that ever needed a transcript.
"""

import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound


class TranscriptUnavailableError(Exception):
    pass


def extract_video_id(url_or_id: str) -> str:
    """Accepts a full YouTube URL or a bare 11-char video id, returns the id."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",  # watch?v=... or youtu.be/...
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    if len(url_or_id) == 11:
        return url_or_id
    raise ValueError(f"Could not extract a YouTube video id from: {url_or_id}")


def fetch_transcript_text(video_id: str, languages: list[str] | None = None) -> str:
    """Returns the transcript as one clean string of plain text."""
    languages = languages or ["en"]
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=languages)
    except (TranscriptsDisabled, NoTranscriptFound) as exc:
        raise TranscriptUnavailableError(
            f"No transcript available for video {video_id}"
        ) from exc
    except Exception as exc:  # noqa: BLE001 - network/IP-block/etc. from the library
        raise TranscriptUnavailableError(
            f"Could not fetch transcript for video {video_id}: {exc}"
        ) from exc
    # FetchedTranscript is iterable of FetchedTranscriptSnippet(text, start, duration)
    return " ".join(snippet.text for snippet in fetched)

