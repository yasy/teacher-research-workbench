from core.exceptions import PDFParseError
from literature.extraction_backends import PDFExtractionResult, extract_with_backend


def extract_pdf_content(file_path: str, backend: str = "auto") -> PDFExtractionResult:
    return extract_with_backend(file_path, preferred_backend=backend)


def extract_pages_from_pdf(file_path: str, backend: str = "auto") -> list[str]:
    return extract_pdf_content(file_path, backend=backend).pages


def extract_text_from_pdf(file_path: str, backend: str = "auto") -> str:
    try:
        return extract_pdf_content(file_path, backend=backend).text
    except PDFParseError:
        return ""
