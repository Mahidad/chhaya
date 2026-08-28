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


# --- proxy plumbing -------------------------------------------------------
# Every YouTube request below goes through these two helpers so that the
# datacenter-IP block has exactly one place to be fixed. See the comment on
# YOUTUBE_PROXY_URL in app/core/config.py for why a proxy is the only fix.

def _proxy_url() -> str | None:
    """One proxy URL for every YouTube call, however it was configured.

    The Webshare credentials and YOUTUBE_PROXY_URL have to converge here
    because yt-dlp takes a plain URL and knows nothing about
    WebshareProxyConfig. Without this, setting only the Webshare pair would
    proxy the transcript API but let the yt-dlp fallback egress from the
    server's own blocked IP -- so the first attempt would work and the
    fallback would still fail with the bot message.
    """
    from app.core.config import settings

    if settings.WEBSHARE_PROXY_USERNAME and settings.WEBSHARE_PROXY_PASSWORD:
        from youtube_transcript_api.proxies import WebshareProxyConfig

        return WebshareProxyConfig(
            proxy_username=settings.WEBSHARE_PROXY_USERNAME,
            proxy_password=settings.WEBSHARE_PROXY_PASSWORD,
        ).url
    return settings.YOUTUBE_PROXY_URL


def _transcript_api():
    """YouTubeTranscriptApi, routed through a proxy when one is configured."""
    from app.core.config import settings

    if settings.WEBSHARE_PROXY_USERNAME and settings.WEBSHARE_PROXY_PASSWORD:
        from youtube_transcript_api.proxies import WebshareProxyConfig

        return YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=settings.WEBSHARE_PROXY_USERNAME,
                proxy_password=settings.WEBSHARE_PROXY_PASSWORD,
            )
        )
    if settings.YOUTUBE_PROXY_URL:
        from youtube_transcript_api.proxies import GenericProxyConfig

        return YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(
                http_url=settings.YOUTUBE_PROXY_URL,
                https_url=settings.YOUTUBE_PROXY_URL,
            )
        )
    return YouTubeTranscriptApi()


def _is_bot_block(exc: Exception) -> bool:
    """Whether this failure is YouTube refusing the server's IP.

    Worth distinguishing because it is not a property of the video -- the same
    URL works from a laptop -- so telling the user "no transcript available"
    would send them looking for a problem that is not there.
    """
    text = str(exc).lower()
    return "sign in to confirm" in text or "not a bot" in text or "blocked" in text


def fetch_transcript_text_ytdlp(video_id: str) -> str:
    """Fallback method using yt-dlp to extract auto-generated or manual subtitles when youtube-transcript-api is blocked."""
    import yt_dlp
    import urllib.request
    import json

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en", ".*"],
        "quiet": True,
        "no_warnings": True,
    }
    proxy = _proxy_url()
    if proxy:
        ydl_opts["proxy"] = proxy
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get("subtitles") or info.get("automatic_captions") or {}
            
            # Find an english or best available subtitle track
            sub_track = None
            for lang in ["en", "en-US", "en-GB"]:
                if lang in subtitles:
                    sub_track = subtitles[lang]
                    break
            if not sub_track and subtitles:
                sub_track = next(iter(subtitles.values()))

            if not sub_track:
                raise TranscriptUnavailableError(f"No subtitle tracks found for video {video_id} via yt-dlp.")

            # Find json3 or vtt format url
            json_fmt = next((item for item in sub_track if item.get("ext") == "json3"), None)
            if json_fmt and "url" in json_fmt:
                req = urllib.request.Request(json_fmt["url"], headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    events = data.get("events", [])
                    text_parts = []
                    for ev in events:
                        for seg in ev.get("segs", []):
                            t = seg.get("utf8", "").strip()
                            if t and t != "\n":
                                text_parts.append(t)
                    raw_text = " ".join(text_parts)
                    if raw_text.strip():
                        return clean_transcript_text(raw_text)

            # Fallback to plain vtt/srv format if json3 not available
            fmt = next((item for item in sub_track if "url" in item), None)
            if fmt and "url" in fmt:
                req = urllib.request.Request(fmt["url"], headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req) as resp:
                    content = resp.read().decode("utf-8", errors="ignore")
                    # Basic strip of WebVTT metadata / timestamps
                    content = re.sub(r"WEBVTT.*?\n", "", content)
                    content = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}.*", "", content)
                    content = re.sub(r"<.*?>", "", content)
                    if content.strip():
                        return clean_transcript_text(content)

            raise TranscriptUnavailableError(f"Could not parse subtitles for video {video_id} from yt-dlp tracks.")
    except Exception as exc:
        raise TranscriptUnavailableError(f"yt-dlp subtitle fallback failed for video {video_id}: {exc}") from exc


def fetch_transcript_text(
    video_id: str,
    languages: list[str] | None = None,
    skip_short: bool = False,
) -> str:
    """Returns the transcript as one clean string of plain text."""
    # First, try fetching directly using youtube_transcript_api
    try:
        langs = languages or ["en"]
        fetched = _transcript_api().fetch(video_id, languages=langs)

        total_duration = sum(getattr(snippet, "duration", 0) for snippet in fetched)
        if skip_short and total_duration > 0 and total_duration < 180:
            raise TranscriptUnavailableError(
                f"Video {video_id} is shorter than 3 minutes ({int(total_duration)}s) and was skipped."
            )

        raw = " ".join(snippet.text for snippet in fetched)
        return clean_transcript_text(raw)

    except TranscriptUnavailableError:
        raise
    except (TranscriptsDisabled, NoTranscriptFound) as exc:
        if languages:
            raise TranscriptUnavailableError(
                f"No transcript available for video {video_id} in languages {languages}"
            ) from exc
        # Check fallback language list via youtube_transcript_api
        try:
            transcript_list = _transcript_api().list(video_id)
            first_transcript = next(iter(transcript_list))
            fetched = first_transcript.fetch()
            raw = " ".join(snippet.text for snippet in fetched)
            return clean_transcript_text(raw)
        except Exception:
            pass
    except Exception:
        # On IP block or other youtube-transcript-api network failures, fall back to yt-dlp
        pass

    # Try yt-dlp subtitle extraction fallback
    try:
        return fetch_transcript_text_ytdlp(video_id)
    except TranscriptUnavailableError as exc:
        if _is_bot_block(exc):
            raise TranscriptUnavailableError(
                "YouTube is blocking transcript requests from this server's IP "
                "address (\"Sign in to confirm you're not a bot\"). This is a "
                "hosting limitation, not a problem with the video -- the same "
                "link works from a home connection. Set YOUTUBE_PROXY_URL (or "
                "the Webshare credentials) to route these requests through a "
                "residential IP."
            ) from exc
        raise
    except Exception as exc:
        if _is_bot_block(exc):
            raise TranscriptUnavailableError(
                "YouTube is blocking transcript requests from this server's IP "
                "address. Set YOUTUBE_PROXY_URL to route them through a "
                "residential IP."
            ) from exc
        raise TranscriptUnavailableError(
            f"Could not retrieve transcript for video {video_id}: {exc}"
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

