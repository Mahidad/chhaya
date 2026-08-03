from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ExamPaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    course: str | None
    status: str
    error_message: str | None
    extracted_text: str | None
    created_at: datetime
