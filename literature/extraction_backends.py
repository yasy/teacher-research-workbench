import re
from dataclasses import dataclass, field
from pathlib import Path

from PyPDF2 import PdfReader

from core.exceptions import PDFParseError


@dataclass
class PDFExtractionResult:
    backend_name: str
    pages: list[str]
    text: str
    quality_score: float
    quality_flags: list[str] = field(default_factory=list)


def _join_pages(pages: list[str]) -> str:
    return "\n\n".join(page for page in pages if page.strip()).strip()


def _is_expected_char(char: str) -> bool:
    if char.isspace():
        return True
    if "\u4e00" <= char <= "\u9fff":
        return True
    if char.isascii() and char.isalnum():
        return True
    return char in "，。！？；：“”‘’（）()《》【】[]、,.!?:;\"'_-—%+=<>~·"


def _looks_like_mojibake(text: str) -> bool:
    stripped = re.sub(r"\s+", "", text)
    if not stripped:
        return False

    latin1_chars = re.findall(r"[\u00C0-\u00FF]", stripped)
    replacement_chars = stripped.count("�")
    box_chars = sum(stripped.count(char) for char in ("■", "□", "▪", "▢", "▣"))

    return (
        replacement_chars > 0
        or len(latin1_chars) / len(stripped) > 0.03
        or box_chars / len(stripped) > 0.02
    )


def _assess_quality(text: str, source_path: str = "") -> tuple[float, list[str]]:
    stripped = re.sub(r"\s+", "", text)
    flags: list[str] = []
    source_name = Path(source_path).name if source_path else ""

    if len(stripped) < 500:
        flags.append("text_too_short")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        short_lines = [line for line in lines if len(line) <= 20]
        if len(short_lines) / len(lines) > 0.55:
            flags.append("fragmented_lines")

    readable_chars = len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", stripped))
    if stripped and readable_chars / len(stripped) < 0.6:
        flags.append("low_readable_ratio")

    unexpected_chars = [char for char in stripped if not _is_expected_char(char)]
    if stripped and len(unexpected_chars) / len(stripped) > 0.12:
        flags.append("suspected_garbled_text")

    if _looks_like_mojibake(text):
        flags.append("suspected_mojibake_text")

    if re.search(r"[\u4e00-\u9fff]", source_name):
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", stripped))
        if len(stripped) >= 200 and chinese_chars / len(stripped) < 0.03:
            flags.append("missing_cjk_text")

    score = 1.0
    if "text_too_short" in flags:
        score -= 0.2
    if "fragmented_lines" in flags:
        score -= 0.15
    if "low_readable_ratio" in flags:
        score -= 0.25
    if "suspected_garbled_text" in flags:
        score -= 0.35
    if "suspected_mojibake_text" in flags:
        score -= 0.45
    if "missing_cjk_text" in flags:
        score -= 0.4
    score = max(0.1, score)
    return score, flags


def _is_cjk_source(file_path: str) -> bool:
    source_name = Path(file_path or "").name
    return bool(re.search(r"[\u4e00-\u9fff]", source_name))


class BasicPythonExtractionBackend:
    name = "basic_python"

    @classmethod
    def extract(cls, file_path: str) -> PDFExtractionResult:
        try:
            reader = PdfReader(file_path)
            pages = [(page.extract_text() or "").strip() for page in reader.pages]
            text = _join_pages(pages)
            if not text:
                raise PDFParseError(f"Failed to parse PDF: {Path(file_path).name}")
            quality_score, quality_flags = _assess_quality(text, file_path)
            return PDFExtractionResult(
                backend_name=cls.name,
                pages=pages,
                text=text,
                quality_score=quality_score,
                quality_flags=quality_flags,
            )
        except Exception as exc:
            if isinstance(exc, PDFParseError):
                raise
            raise PDFParseError(f"Failed to parse PDF: {Path(file_path).name}") from exc


class PyMuPDF4LLMExtractionBackend:
    name = "pymupdf4llm"

    @staticmethod
    def is_available() -> bool:
        try:
            import pymupdf4llm  # noqa: F401

            return True
        except Exception:
            return False

    @classmethod
    def extract(cls, file_path: str) -> PDFExtractionResult:
        if not cls.is_available():
            raise RuntimeError("pymupdf4llm is not available.")

        try:
            import pymupdf4llm

            markdown_text = pymupdf4llm.to_markdown(file_path)
            text = str(markdown_text or "").strip()
            if not text:
                raise PDFParseError(f"Failed to parse PDF with pymupdf4llm: {Path(file_path).name}")
            quality_score, quality_flags = _assess_quality(text, file_path)
            return PDFExtractionResult(
                backend_name=cls.name,
                pages=[text],
                text=text,
                quality_score=quality_score,
                quality_flags=quality_flags,
            )
        except Exception as exc:
            if isinstance(exc, PDFParseError):
                raise
            raise PDFParseError(f"Failed to parse PDF with pymupdf4llm: {Path(file_path).name}") from exc


class PyMuPDFExtractionBackend:
    name = "pymupdf"

    @staticmethod
    def is_available() -> bool:
        try:
            import fitz  # noqa: F401

            return True
        except Exception:
            return False

    @classmethod
    def extract(cls, file_path: str) -> PDFExtractionResult:
        if not cls.is_available():
            raise RuntimeError("pymupdf is not available.")

        try:
            import fitz

            doc = fitz.open(file_path)
            pages = [(doc.load_page(index).get_text("text") or "").strip() for index in range(doc.page_count)]
            text = _join_pages(pages)
            if not text:
                raise PDFParseError(f"Failed to parse PDF with pymupdf: {Path(file_path).name}")
            quality_score, quality_flags = _assess_quality(text, file_path)
            return PDFExtractionResult(
                backend_name=cls.name,
                pages=pages,
                text=text,
                quality_score=quality_score,
                quality_flags=quality_flags,
            )
        except Exception as exc:
            if isinstance(exc, PDFParseError):
                raise
            raise PDFParseError(f"Failed to parse PDF with pymupdf: {Path(file_path).name}") from exc


def extract_with_backend(file_path: str, preferred_backend: str = "auto") -> PDFExtractionResult:
    preferred = (preferred_backend or "auto").strip().lower()

    if preferred == "basic_python":
        return BasicPythonExtractionBackend.extract(file_path)

    if preferred == "pymupdf4llm":
        return PyMuPDF4LLMExtractionBackend.extract(file_path)

    if preferred == "pymupdf":
        return PyMuPDFExtractionBackend.extract(file_path)

    candidate_results: list[PDFExtractionResult] = []
    severe_flags = {"suspected_garbled_text", "suspected_mojibake_text", "missing_cjk_text"}
    prefer_pymupdf = _is_cjk_source(file_path) and PyMuPDFExtractionBackend.is_available()

    if prefer_pymupdf:
        try:
            pymupdf_result = PyMuPDFExtractionBackend.extract(file_path)
            if pymupdf_result.quality_score >= 0.7 and not (severe_flags & set(pymupdf_result.quality_flags)):
                return pymupdf_result
            if pymupdf_result.quality_score >= 0.55 and "missing_cjk_text" not in pymupdf_result.quality_flags:
                return pymupdf_result
            candidate_results.append(pymupdf_result)
        except Exception:
            pass

    basic_result = BasicPythonExtractionBackend.extract(file_path)
    if basic_result.quality_score >= 0.85 and not (severe_flags & set(basic_result.quality_flags)):
        return basic_result

    candidate_results.append(basic_result)

    if not prefer_pymupdf and PyMuPDFExtractionBackend.is_available():
        try:
            candidate_results.append(PyMuPDFExtractionBackend.extract(file_path))
        except Exception:
            pass

    if PyMuPDF4LLMExtractionBackend.is_available():
        try:
            candidate_results.append(PyMuPDF4LLMExtractionBackend.extract(file_path))
        except Exception:
            pass

    def _candidate_key(result: PDFExtractionResult) -> tuple[float, int, int]:
        text_len = len(re.sub(r"\s+", "", result.text))
        garbled_penalty = 1 if severe_flags & set(result.quality_flags) else 0
        return (result.quality_score, -garbled_penalty, text_len)

    best_result = max(candidate_results, key=_candidate_key)

    if severe_flags & set(basic_result.quality_flags) and not (severe_flags & set(best_result.quality_flags)):
        return best_result

    if best_result.quality_score > basic_result.quality_score:
        return best_result

    best_text_len = len(re.sub(r"\s+", "", best_result.text))
    basic_text_len = len(re.sub(r"\s+", "", basic_result.text))
    if best_text_len > basic_text_len * 1.15:
        return best_result

    return basic_result
