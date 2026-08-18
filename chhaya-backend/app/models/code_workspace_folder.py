"""
CodeWorkspaceFolder -- one flat list of folders per user, shared by
code_conversions and code_visualizations (Code Studio's storage system).
No nesting: see sql/schema.sql's comment on this table for why.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CodeWorkspaceFolder:
    id: str
    user_id: str
    name: str
    created_at: datetime
