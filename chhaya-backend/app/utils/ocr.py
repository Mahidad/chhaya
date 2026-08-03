"""
Thin wrapper around `pytesseract`, following the exact wrapping pattern
used in utils/youtube.py -- one function other code calls, so the actual
OCR library can be swapped (e.g. to EasyOCR) by editing only this file.

WHY A MOCK FALLBACK: `pytesseract` needs the system `tesseract-ocr` binary
installed separately from anything `pip install` can provide (it's not a
Python package, it's a C++ program pytesseract calls out to). Not every
teammate will have that installed while building other parts of the app.
Same trick as Gemini and the mock style profile: if tesseract genuinely
isn't available, return clearly-labeled placeholder text instead of
crashing every exam-paper upload for anyone who hasn't installed it yet.
"""

import shutil


class OCRUnavailableError(Exception):
    pass


def _tesseract_installed() -> bool:
    return shutil.which("tesseract") is not None


def extract_text_from_file(file_path: str) -> str:
    if not _tesseract_installed():
        return (
            "MOCK OCR TEXT (tesseract-ocr is not installed on this machine) — "
            "install the system tesseract-ocr binary, then pytesseract will "
            "read the real file instead of this placeholder. "
            f"File received: {file_path}"
        )

    try:
        import pytesseract
        from PIL import Image

        if file_path.lower().endswith(".pdf"):
            from pdf2image import convert_from_path

            images = convert_from_path(file_path)
            extracted_pages = [pytesseract.image_to_string(img).strip() for img in images]
            return "\n\n--- Page Break ---\n\n".join(filter(None, extracted_pages)).strip()

        return pytesseract.image_to_string(Image.open(file_path)).strip()
    except Exception as exc:  # noqa: BLE001
        raise OCRUnavailableError(f"OCR failed for {file_path}: {exc}") from exc


# Keep backward compatibility wrapper if needed
extract_text_from_image = extract_text_from_file

