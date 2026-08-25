"""OCR.Space API wrapper used when students upload past exam papers."""

import json
import mimetypes
import os
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings

OCR_SPACE_URL = "https://api.ocr.space/parse/image"
FREE_TIER_FILE_SIZE_LIMIT = 1 * 1024 * 1024  # OCR.Space free tier: 1 MB


class OCRUnavailableError(Exception):
    """Raised when OCR.Space cannot extract text from an uploaded file."""


def _make_multipart_body(file_path: str, boundary: str) -> bytes:
    """Create the multipart request body expected by OCR.Space."""
    filename = Path(file_path).name
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    with open(file_path, "rb") as uploaded_file:
        file_bytes = uploaded_file.read()

    fields = {
        "language": "eng",
        "isOverlayRequired": "false",
        "detectOrientation": "true",
        "scale": "true",
        "OCREngine": "2",
    }
    body_parts = []
    for name, value in fields.items():
        body_parts.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                f"{value}\r\n".encode(),
            ]
        )
    body_parts.extend(
        [
            f"--{boundary}\r\n".encode(),
            (
                "Content-Disposition: form-data; "
                f'name="file"; filename="{filename}"\r\n'
            ).encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(body_parts)


def _error_message(response: dict) -> str:
    error = response.get("ErrorMessage") or response.get("ErrorDetails")
    if isinstance(error, list):
        return "; ".join(str(item) for item in error)
    return str(error or "OCR.Space could not read this file.")


def extract_text_from_file(file_path: str) -> str:
    """Send an image or PDF to OCR.Space and return its extracted text."""
    if not settings.OCR_SPACE_API_KEY:
        raise OCRUnavailableError(
            "OCR.Space is not configured. Add OCR_SPACE_API_KEY to the backend .env file."
        )
    if not os.path.exists(file_path):
        raise OCRUnavailableError("The uploaded file could not be found.")
    if os.path.getsize(file_path) > FREE_TIER_FILE_SIZE_LIMIT:
        raise OCRUnavailableError(
            "This file is larger than the OCR.Space free-tier 1 MB limit."
        )

    boundary = f"----ChhayaOCR{uuid.uuid4().hex}"
    request = Request(
        OCR_SPACE_URL,
        data=_make_multipart_body(file_path, boundary),
        headers={
            "apikey": settings.OCR_SPACE_API_KEY,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:  # noqa: S310 - fixed API URL
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise OCRUnavailableError(f"OCR.Space returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise OCRUnavailableError("Could not connect to OCR.Space.") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise OCRUnavailableError(f"OCR.Space request failed: {exc}") from exc

    if result.get("IsErroredOnProcessing"):
        raise OCRUnavailableError(_error_message(result))

    text = "\n\n--- Page Break ---\n\n".join(
        page.get("ParsedText", "").strip()
        for page in result.get("ParsedResults", [])
        if page.get("ParsedText", "").strip()
    ).strip()
    if not text:
        raise OCRUnavailableError("OCR.Space did not find readable text in this file.")
    return text


# Keep the existing service import unchanged.
extract_text_from_image = extract_text_from_file
