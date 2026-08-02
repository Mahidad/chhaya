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
