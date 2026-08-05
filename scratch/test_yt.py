import sys
from youtube_transcript_api import YouTubeTranscriptApi

video_id = "_t2GVaQasRY"
try:
    transcript_list = YouTubeTranscriptApi().list(video_id)
    print("Available transcripts:")
    for t in transcript_list:
        print(f"Language: {t.language}, Code: {t.language_code}, Is generated: {t.is_generated}")
except Exception as e:
    print("Error:", e)
