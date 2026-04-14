import json
from typing import Any

from core.schemas import LiteratureItem, LiteratureReviewPack, TopicCard


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


def _build_item_blocks(items: list[LiteratureItem]) -> str:
    summaries = []
    for item in items:
        summaries.append(
            f"文件: {item.file_name}\n"
            f"标题: {item.title}\n"
            f"摘要速读: {item.abstract}\n"
            f"方法: {item.method}\n"
            f"主要结论: {item.findings}"
        )
    return "\n\n".join(summaries)


def build_theme_cluster_prompt(items: list[LiteratureItem]) -> str:
    joined = _build_item_blocks(items)
    return f"""
请根据以下多篇文献速读卡，对它们进行主题归类。
要求：
- 只输出严格 JSON
- 不要输出 Markdown
- 主题数控制在 2-5 个
- 每个主题下放文件名列表

JSON 结构：
{{
  "themes": {{
    "主题名称1": ["file1.pdf", "file2.pdf"],
    "主题名称2": ["file3.pdf"]
  }}
}}

文献速读卡：
{joined}
""".strip()


def build_review_pack_prompt(items: list[LiteratureItem], topic_card: TopicCard | None = None) -> str:
    topic_context = ""
    if topic_card and topic_card.title:
        topic_context = (
            f"当前研究题目: {topic_card.title}\n"
            f"研究问题: {topic_card.research_problem}\n"
            f"研究场景: {topic_card.context}\n"
        )

    joined = _build_item_blocks(items)
    return f"""
请基于以下多篇文献速读卡，生成一个“文献综述素材包”，用于后续论文写作。
{topic_context}
要求：
- 只输出严格 JSON
- 不要输出 Markdown
- 每个字段输出 2-5 条，尽量简洁、可直接写进综述
- 只允许基于已有文献速读卡归纳，不要虚构未出现的信息

JSON 结构：
{{
  "high_frequency_themes": ["高频主题1", "高频主题2"],
  "common_methods": ["常用方法1", "常用方法2"],
  "common_findings": ["共同结论1", "共同结论2"],
  "major_disagreements": ["主要分歧1", "主要分歧2"],
  "research_limitations": ["研究不足1", "研究不足2"],
  "suggested_angles": ["可写切入点1", "可写切入点2"]
}}

文献速读卡：
{joined}
""".strip()


def cluster_themes(items: list[LiteratureItem], llm_client) -> dict[str, list[str]]:
    if not items:
        return {}

    prompt = build_theme_cluster_prompt(items)
    response_text = llm_client.chat(
        user_prompt=prompt,
        system_prompt="You are an academic literature clustering assistant. Return strict JSON only.",
        temperature=0.2,
        max_tokens=900,
    )
    data = _extract_json_object(response_text)
    themes = data.get("themes", {})

    normalized: dict[str, list[str]] = {}
    if isinstance(themes, dict):
        for key, value in themes.items():
            if not str(key).strip():
                continue
            if isinstance(value, list):
                normalized[str(key).strip()] = [str(item).strip() for item in value if str(item).strip()]
    return normalized


def build_literature_review_pack(
    items: list[LiteratureItem],
    llm_client,
    topic_card: TopicCard | None = None,
) -> LiteratureReviewPack:
    if not items:
        return LiteratureReviewPack()

    prompt = build_review_pack_prompt(items, topic_card=topic_card)
    response_text = llm_client.chat(
        user_prompt=prompt,
        system_prompt="You are an academic literature review synthesis assistant. Return strict JSON only.",
        temperature=0.3,
        max_tokens=1200,
    )
    data = _extract_json_object(response_text)

    def _as_list(name: str) -> list[str]:
        value = data.get(name, [])
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    return LiteratureReviewPack(
        high_frequency_themes=_as_list("high_frequency_themes"),
        common_methods=_as_list("common_methods"),
        common_findings=_as_list("common_findings"),
        major_disagreements=_as_list("major_disagreements"),
        research_limitations=_as_list("research_limitations"),
        suggested_angles=_as_list("suggested_angles"),
    )
