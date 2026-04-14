import json
from pathlib import Path
from typing import Any

from core.schemas import LiteratureItem, LiteraturePreprocessResult


PROMPT_PATH = Path(__file__).resolve().parent.parent / "assets" / "prompts" / "literature_digest_prompt.md"


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model response does not contain a valid JSON object.")
    return json.loads(text[start : end + 1])


def build_preprocessed_material(preprocess_result: LiteraturePreprocessResult) -> str:
    parts = [
        f"文件: {preprocess_result.file_name}",
        f"标题: {preprocess_result.title or '暂无'}",
        f"作者: {', '.join(preprocess_result.authors) if preprocess_result.authors else '暂无'}",
        f"年份: {preprocess_result.year or '暂无'}",
        f"摘要: {preprocess_result.abstract_text or '暂无'}",
        "前言关键段:",
    ]

    if preprocess_result.intro_snippets:
        parts.extend(f"- {text}" for text in preprocess_result.intro_snippets)
    else:
        parts.append("- 暂无")

    parts.append("结论关键段:")
    if preprocess_result.conclusion_snippets:
        parts.extend(f"- {text}" for text in preprocess_result.conclusion_snippets)
    else:
        parts.append("- 暂无")

    parts.append("正文关键片段:")
    if preprocess_result.body_snippets:
        parts.extend(f"- {text}" for text in preprocess_result.body_snippets)
    else:
        parts.append("- 暂无")

    return "\n".join(parts)


def build_literature_summary_prompt(preprocess_result: LiteraturePreprocessResult) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(paper_text=build_preprocessed_material(preprocess_result))


def summarize_preprocessed_result(preprocess_result: LiteraturePreprocessResult, llm_client) -> LiteratureItem:
    if not preprocess_result.is_ai_ready:
        raise ValueError(f"Preprocess result is not ready for AI analysis: {preprocess_result.file_name}")

    prompt = build_literature_summary_prompt(preprocess_result)
    response_text = llm_client.chat(
        user_prompt=prompt,
        system_prompt="You are an academic literature reading assistant. Return strict JSON only.",
        temperature=0.2,
        max_tokens=900,
    )
    data = _extract_json_object(response_text)

    return LiteratureItem(
        file_name=preprocess_result.file_name,
        title=str(data.get("title") or preprocess_result.title or "").strip(),
        authors=[
            str(item).strip()
            for item in data.get("authors", preprocess_result.authors)
            if str(item).strip()
        ],
        year=str(data.get("year") or preprocess_result.year or "").strip(),
        abstract=str(data.get("abstract") or preprocess_result.abstract_text or "").strip(),
        method=str(data.get("method", "")).strip(),
        findings=str(data.get("findings", "")).strip(),
        theme="",
    )
