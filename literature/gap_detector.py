from pathlib import Path

from core.schemas import LiteratureItem, TopicCard


PROMPT_PATH = Path(__file__).resolve().parent.parent / "assets" / "prompts" / "gap_analysis_prompt.md"


def build_gap_prompt(items: list[LiteratureItem], topic_card: TopicCard | None = None) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    literature_summaries = []
    for item in items:
        literature_summaries.append(
            f"文件: {item.file_name}\n"
            f"标题: {item.title}\n"
            f"摘要速读: {item.abstract}\n"
            f"方法: {item.method}\n"
            f"主要结论: {item.findings}"
        )

    topic_context = ""
    if topic_card:
        topic_context = (
            f"选题标题: {topic_card.title}\n"
            f"研究问题: {topic_card.research_problem}\n"
            f"研究场景: {topic_card.context}\n"
            f"关键词: {', '.join(topic_card.keywords)}"
        )

    return template.format(
        literature_summaries="\n\n".join(literature_summaries),
        topic_context=topic_context or "暂无选题上下文，请仅基于文献速读卡归纳研究空白。",
    )


def detect_research_gaps(
    items: list[LiteratureItem],
    llm_client,
    topic_card: TopicCard | None = None,
) -> list[str]:
    if not items:
        return []

    prompt = build_gap_prompt(items, topic_card=topic_card)
    response_text = llm_client.chat(
        user_prompt=prompt,
        system_prompt="You are an academic gap analysis assistant. Return a plain numbered list only.",
        temperature=0.3,
        max_tokens=900,
    )

    lines = []
    for line in response_text.splitlines():
        cleaned = line.strip().lstrip("-").strip()
        if cleaned and cleaned[0:2].rstrip(".") != "":
            if cleaned[0].isdigit() and "." in cleaned[:4]:
                cleaned = cleaned.split(".", 1)[1].strip()
        if cleaned:
            lines.append(cleaned)

    return lines[:5]
