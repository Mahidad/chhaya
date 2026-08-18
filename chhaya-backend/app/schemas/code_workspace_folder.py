from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CodeWorkspaceFolderCreate(BaseModel):
    name: str = Field(..., min_length=1)


class CodeWorkspaceFolderUpdate(BaseModel):
    name: str = Field(..., min_length=1)


class CodeWorkspaceFolderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime
