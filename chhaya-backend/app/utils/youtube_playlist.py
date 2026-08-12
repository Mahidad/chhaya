"""
Playlist enumeration via yt-dlp -- separate from youtube.py because it's
a genuinely different job: youtube.py answers "what did this ONE video
say" (transcript text), this file answers "what videos are IN this
playlist, and who uploaded each one" (metadata only, no transcript).

WHY yt-dlp AND NOT THE YOUTUBE DATA API: the official API needs a Google
Cloud API key and has a daily quota that's easy to exhaust while testing.
yt-dlp reads the playlist page directly, no key needed. Trade-off: it's
scraping, so it can break when YouTube changes its page structure --
something to watch for if this starts failing across the board rather
than for specific playlists.

WHY channel_name MATTERS HERE: it's the signal
reference_source_service.py uses to detect "this playlist has more than
one instructor in it" and split into multiple teacher profiles instead of
force-blending two different teaching styles into one. It's an imperfect
heuristic -- a guest lecture on an otherwise single-instructor channel
would incorrectly get its own profile -- but it's a defensible, explainable
starting point: same channel is a reasonable proxy for "same teacher"
far more often than not.
"""

import yt_dlp


class PlaylistUnavailableError(Exception):
    pass


def enumerate_playlist(url: str) -> list[dict]:
    """
    Returns a list of
        {"video_id": ..., "title": ..., "channel_name": ..., "duration_seconds": ...}
    without downloading any video or audio -- `extract_flat` tells yt-dlp
    to just read the playlist's own listing page, not visit every video.
    """
    ydl_opts = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:  # noqa: BLE001 - yt-dlp raises its own broad exception types
        raise PlaylistUnavailableError(f"Could not read this playlist: {exc}") from exc

    entries = (info or {}).get("entries") or []
    videos = []
    for entry in entries:
        if not entry:
            continue
        videos.append(
            {
                "video_id": entry.get("id"),
                "title": entry.get("title") or "Untitled",
                "channel_name": entry.get("uploader") or entry.get("channel") or "Unknown channel",
                "duration_seconds": entry.get("duration"),
            }
        )

    if not videos:
        raise PlaylistUnavailableError("This playlist is empty or not publicly accessible.")

    return videos
