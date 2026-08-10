
import shutil #built-in Python module. provides utilities for working with files and the operating system.


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
        import pytesseract   # Python wrapper. communicates with the tesseract installed on computer
        from PIL import Image

        if file_path.lower().endswith(".pdf"):
            from pdf2image import convert_from_path  # OCR cannot directly read PDFs.

            images = convert_from_path(file_path)
            extracted_pages = [pytesseract.image_to_string(img).strip() for img in images]
            return "\n\n--- Page Break ---\n\n".join(filter(None, extracted_pages)).strip()  # filter(None, ) --> removes empty string

        return pytesseract.image_to_string(Image.open(file_path)).strip()   # jodi pdf na hoy tahole direct convert korbe
    except Exception as exc:  # noqa: BLE001
        raise OCRUnavailableError(f"OCR failed for {file_path}: {exc}") from exc


# Keep backward compatibility wrapper if needed
extract_text_from_image = extract_text_from_file

