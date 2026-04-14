import re


def chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    if not text.strip():
        return []

    paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= max_chars:
            current = f"{current}\n{paragraph}".strip()
        else:
            if current:
                chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def _keyword_tokens(selected_topic: str | None) -> list[str]:
    if not selected_topic:
        return []
    return [token for token in re.split(r"[\s，,、；;：:（）()]+", selected_topic) if len(token) >= 2]


def select_body_snippets(
    paragraphs: list[str],
    selected_topic: str | None = None,
    max_snippets: int = 3,
    min_len: int = 40,
    max_chars: int = 260,
) -> list[str]:
    topic_tokens = _keyword_tokens(selected_topic)
    scored: list[tuple[int, str]] = []

    for paragraph in paragraphs:
        if len(paragraph) < min_len:
            continue

        score = 0
        if any(keyword in paragraph for keyword in ("方法", "实验", "结果", "调查", "访谈", "效果", "策略", "设计")):
            score += 2
        for token in topic_tokens:
            if token in paragraph:
                score += 3
        score += min(len(paragraph) // 80, 3)
        scored.append((score, paragraph[:max_chars].strip()))

    scored.sort(key=lambda item: item[0], reverse=True)
    snippets: list[str] = []
    seen: set[str] = set()
    for _, snippet in scored:
        if snippet in seen:
            continue
        seen.add(snippet)
        snippets.append(snippet)
        if len(snippets) >= max_snippets:
            break
    return snippets
