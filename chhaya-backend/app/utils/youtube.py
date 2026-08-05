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


def clean_transcript_text(raw_text: str) -> str:
    """Strips timestamps, caption noise like [Music], and filler words."""
    # Strip bracketed caption noise like [Music], [Applause], (Laughter)
    text = re.sub(r"\[.*?\]|\(.*?\)", " ", raw_text)
    # Strip timestamps like 0:00, 12:34, 1:23:45
    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", text)
    # Strip common filler words and verbal ticks
    fillers = [
        r"\bumm+\b", r"\buhh+\b", r"\berr+\b", r"\bso basically\b",
        r"\byou know\b", r"\bbasically\b", r"\bi mean\b", r"\bkind of\b"
    ]
    for pattern in fillers:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    # Collapse multiple whitespace characters
    return re.sub(r"\s+", " ", text).strip()


def fetch_transcript_text(
    video_id: str,
    languages: list[str] | None = None,
    skip_short: bool = False,
) -> str:
    """Returns the transcript as one clean string of plain text."""
    try:
        langs = languages or ["en"]
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=langs)
    except (TranscriptsDisabled, NoTranscriptFound) as exc:
        if languages:
            raise TranscriptUnavailableError(
                f"No transcript available for video {video_id} in languages {languages}"
            ) from exc
        # Try to fallback to any available transcript (e.g. auto-generated or other language)
        try:
            transcript_list = YouTubeTranscriptApi().list(video_id)
            first_transcript = next(iter(transcript_list))
            fetched = first_transcript.fetch()
        except Exception as fallback_exc:
            raise TranscriptUnavailableError(
                f"No transcript available for video {video_id}"
            ) from fallback_exc
    except Exception as exc:  # noqa: BLE001 - network/IP-block/etc. from the library
        raise TranscriptUnavailableError(
            f"Could not fetch transcript for video {video_id}: {exc}"
        ) from exc

    # Check total video duration if skip_short is set
    total_duration = sum(getattr(snippet, "duration", 0) for snippet in fetched)
    if skip_short and total_duration > 0 and total_duration < 180:
        raise TranscriptUnavailableError(
            f"Video {video_id} is shorter than 3 minutes ({int(total_duration)}s) and was skipped."
        )

    # FetchedTranscript is iterable of FetchedTranscriptSnippet(text, start, duration)
    raw = " ".join(snippet.text for snippet in fetched)
    return clean_transcript_text(raw)

