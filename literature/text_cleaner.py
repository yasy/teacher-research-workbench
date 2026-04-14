import re


def clean_pdf_text(text: str) -> str:
    cleaned = (text or "").replace("\x00", " ")
    cleaned = re.sub(r"\r\n?", "\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ ]+\n", "\n", cleaned)
    return cleaned.strip()


def _is_noise_line(line: str) -> bool:
    if not line:
        return True
    if re.fullmatch(r"[\d\s./-]+", line):
        return True
    if len(line) <= 2 and not re.search(r"[\u4e00-\u9fffA-Za-z]", line):
        return True
    return False


def _is_heading_line(line: str) -> bool:
    patterns = [
        r"^(摘要|关键词|关键字|引言|前言|结论|讨论|参考文献)$",
        r"^(abstract|keywords?|introduction|conclusion|discussion|references)$",
        r"^[一二三四五六七八九十]+[、.]",
        r"^\d+[.、)]",
    ]
    lowered = line.lower()
    return any(re.search(pattern, line) or re.search(pattern, lowered) for pattern in patterns)


def split_into_paragraphs(text: str) -> list[str]:
    lines = [line.strip() for line in clean_pdf_text(text).splitlines()]
    paragraphs: list[str] = []
    current: list[str] = []

    for line in lines:
        if _is_noise_line(line):
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue

        if _is_heading_line(line):
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            paragraphs.append(line)
            continue

        current.append(line)
        if line.endswith(("。", "！", "？", ".", "!", "?")) and len(" ".join(current)) >= 60:
            paragraphs.append(" ".join(current).strip())
            current = []

    if current:
        paragraphs.append(" ".join(current).strip())

    return [paragraph for paragraph in paragraphs if paragraph]


def filter_noise_paragraphs(paragraphs: list[str]) -> list[str]:
    filtered: list[str] = []
    for paragraph in paragraphs:
        normalized = paragraph.strip()
        if len(normalized) < 8:
            continue
        if re.fullmatch(r"[\d\s./-]+", normalized):
            continue
        if normalized.lower() in {"doi", "copyright"}:
            continue
        filtered.append(normalized)
    return filtered
