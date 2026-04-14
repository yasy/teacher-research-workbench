import re
import unicodedata
from pathlib import Path


def _looks_garbled(text: str) -> bool:
    stripped = re.sub(r"\s+", "", text or "")
    if not stripped:
        return False
    latin1_chars = re.findall(r"[\u00C0-\u00FF]", stripped)
    box_chars = sum(stripped.count(char) for char in ("■", "□", "▪", "▢", "▣", "�"))
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", stripped))
    return (
        len(latin1_chars) / len(stripped) > 0.05
        or box_chars / len(stripped) > 0.03
        or ("-" not in stripped and chinese_chars == 0 and len(stripped) > 18 and not stripped.isascii())
    )


def _normalize_line(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "").strip()


def _clean_title_candidate(text: str) -> str:
    candidate = _normalize_line(text)
    candidate = re.sub(r"(投稿|收稿|录用|基金项目|作者简介).*", "", candidate).strip(" -*·")
    candidate = re.sub(r"\s+", " ", candidate).strip()
    return candidate


def _clean_author_candidate(text: str) -> str:
    candidate = _normalize_line(text)
    candidate = re.sub(r"[0-9＊*†‡§\[\]\(\)（）]+", " ", candidate)
    candidate = re.sub(r"(投稿|收稿|录用|作者简介|基金项目).*", "", candidate)
    candidate = re.sub(r"\s+", " ", candidate).strip()
    return candidate


def _file_stem_title(file_name: str) -> str:
    title = re.sub(r"_[0-9a-f]{8,}$", "", _clean_title_candidate(Path(file_name).stem)).strip()
    title = re.sub(r"_+", "_", title).strip("_")
    return title


def _is_valid_author_name(text: str) -> bool:
    if _looks_garbled(text):
        return False
    invalid_patterns = (
        "专业",
        "课程",
        "教育",
        "研究",
        "实践",
        "学院",
        "大学",
        "学校",
        "摘要",
        "关键词",
    )
    return not any(pattern in text for pattern in invalid_patterns)


def extract_basic_metadata(text: str, file_name: str) -> dict[str, str | list[str]]:
    lines = [_normalize_line(line) for line in text.splitlines() if line.strip()]

    file_stem_title = _file_stem_title(file_name)
    title = file_stem_title
    for line in lines[:12]:
        title_candidate = _clean_title_candidate(line)
        if len(title_candidate) < 6 or len(title_candidate) > 120:
            continue
        if re.search(r"(摘要|abstract|关键词|keywords?|投稿|收稿|录用)", title_candidate, re.IGNORECASE):
            continue
        if _looks_garbled(title_candidate):
            continue
        if re.search(r"(课程|教学|研究|实践|改革|路径|模式|体系|能力|培养|赋能|驱动)", title_candidate):
            title = title_candidate
            break

    if title == file_stem_title:
        first_paragraph = next((line for line in lines[:4] if len(line) >= 12 and not _looks_garbled(line)), "")
        first_paragraph = _clean_title_candidate(first_paragraph)
        if 12 <= len(first_paragraph) <= 120:
            title = first_paragraph

    if len(title) < 10 or title in {"项目式教学实践", "教学实践", "研究", "实践路径研究"}:
        title = file_stem_title

    year_match = re.search(r"(20\d{2}|19\d{2})", unicodedata.normalize("NFKC", text[:3000]))
    year = year_match.group(1) if year_match else ""

    authors: list[str] = []
    for line in lines[1:10]:
        line_candidate = _clean_author_candidate(line)
        if len(line_candidate) > 80 or not line_candidate:
            continue
        if re.search(r"(摘要|abstract|关键词|keywords?|大学|学院|学校|课程|教学|研究|实践|基金)", line_candidate, re.IGNORECASE):
            continue
        if _looks_garbled(line_candidate):
            continue
        split_result = re.split(r"[,，、；\s]{1,3}", line_candidate)
        candidate_authors = [
            item.strip()
            for item in split_result
            if 1 < len(item.strip()) < 12
            and _is_valid_author_name(item.strip())
            and not re.search(r"(邮箱|email)", item, re.IGNORECASE)
        ]
        if 1 <= len(candidate_authors) <= 8:
            authors = candidate_authors
            break

    if not authors:
        normalized_text = unicodedata.normalize("NFKC", text[:1200])
        author_candidates = re.findall(r"[\u4e00-\u9fff]{2,4}(?=[0-9＊*†‡§\s])", normalized_text)
        filtered_authors = [
            candidate
            for candidate in author_candidates
            if candidate not in {"非化学专业", "化学教育", "项目式教学", "复合材料", "原理课程", "新能源与新材料学院", "首都师范大学"}
        ]
        deduped_authors: list[str] = []
        for candidate in filtered_authors:
            if candidate not in deduped_authors:
                deduped_authors.append(candidate)
        if 1 <= len(deduped_authors) <= 8:
            authors = deduped_authors

    return {"title": title, "authors": authors, "year": year}


def _find_heading_index(paragraphs: list[str], keywords: tuple[str, ...], search_limit: int | None = None) -> int:
    scope = paragraphs if search_limit is None else paragraphs[:search_limit]
    for idx, paragraph in enumerate(scope):
        if any(keyword.lower() in paragraph.lower() for keyword in keywords):
            return idx
    return -1


def extract_abstract_text(paragraphs: list[str]) -> str:
    idx = _find_heading_index(paragraphs, ("摘要", "abstract"), search_limit=10)
    if idx == -1:
        return ""
    paragraph = paragraphs[idx]
    if len(paragraph) > 25 and paragraph.lower() not in {"摘要", "abstract"}:
        return paragraph
    if idx + 1 < len(paragraphs):
        return paragraphs[idx + 1]
    return ""


def extract_intro_snippets(paragraphs: list[str], limit: int = 2) -> list[str]:
    snippets: list[str] = []
    start_index = _find_heading_index(paragraphs, ("引言", "前言", "问题提出", "研究背景", "introduction"), search_limit=16)
    if start_index == -1:
        start_index = 0

    for paragraph in paragraphs[start_index : start_index + 8]:
        if len(paragraph) >= 40:
            snippets.append(paragraph[:280].strip())
        if len(snippets) >= limit:
            break
    return snippets


def extract_conclusion_snippets(paragraphs: list[str], limit: int = 2) -> list[str]:
    snippets: list[str] = []
    reverse_index = -1
    for idx in range(len(paragraphs) - 1, max(-1, len(paragraphs) - 12), -1):
        paragraph = paragraphs[idx]
        if any(keyword in paragraph.lower() for keyword in ("结论", "结语", "讨论", "启示", "建议", "conclusion", "discussion")):
            reverse_index = idx
            break

    start_index = reverse_index if reverse_index != -1 else max(0, len(paragraphs) - 6)
    for paragraph in paragraphs[start_index : start_index + 6]:
        if len(paragraph) >= 40:
            snippets.append(paragraph[:280].strip())
        if len(snippets) >= limit:
            break
    return snippets
