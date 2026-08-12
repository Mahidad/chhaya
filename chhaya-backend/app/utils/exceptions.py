"""
Custom exceptions services can raise, that api/deps.py-level exception
handlers (or individual routes) translate into proper HTTP responses.
Keeping these separate from FastAPI's HTTPException means the service
layer stays framework-agnostic -- it doesn't need to know it's being
called over HTTP at all, which matters if a background worker calls the
same service later.
"""


class NotFoundError(Exception):
    pass


class PermissionDeniedError(Exception):
    pass


class ExternalServiceError(Exception):
    """Raised when a third-party call (Gemini, YouTube) fails."""
    pass

class DuplicateSourceError(Exception):
    """
    Raised when a submitted link matches something this user already
    extracted, and they haven't confirmed they want to extract it again
    (see ReferenceSourceCreate.force). Carries enough info for the
    endpoint to tell the frontend what already exists.
    """
    def __init__(self, *, existing_source_id: str, existing_title: str):
        self.existing_source_id = existing_source_id
        self.existing_title = existing_title
        super().__init__(f"Already extracted as '{existing_title}'.")