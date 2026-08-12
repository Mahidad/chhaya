"""
Note dataclass -- Module 2's Import/Upload Personal Notes (Lamia).

`file_path` follows the exact same convention as ExamPaper.file_path
(models/exam_paper.py): kept on the dataclass so the service/endpoint can
read and delete the file on disk, excluded from NoteOut so it never
reaches the frontend directly -- the file is served through its own
`/notes/{id}/file` endpoint instead, same as exam papers.
"""

from dataclasses import dataclass
from datetime import datetime


class NoteType:
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"


@dataclass
class Note:
    id: str
    user_id: str
    chapter_id: str
    title: str
    note_type: str
    created_at: datetime
    updated_at: datetime
    text_content: str | None = None
    file_path: str | None = None
