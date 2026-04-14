import json
from typing import Any

from config.settings import Settings
from core.schemas import TopicCard
from llm.factory import build_llm_client
from services.mentor_service import build_mentor_system_prompt, build_topic_user_prompt


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


def _to_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _build_topic_card(data: dict[str, Any]) -> TopicCard:
    title = str(data.get("title", "")).strip()
    topic_candidates = _to_string_list(data.get("topic_candidates", []))
    if title and title not in topic_candidates:
        topic_candidates = [title] + topic_candidates
    topic_candidates = topic_candidates[:5]

    return TopicCard(
        title=title,
        topic_candidates=topic_candidates,
        research_problem=str(data.get("research_problem", "")).strip(),
        research_questions=_to_string_list(data.get("research_questions", [])),
        target_population=str(data.get("target_population", "")).strip(),
        context=str(data.get("context", "")).strip(),
        keywords=_to_string_list(data.get("keywords", [])),
        recommended_methods=_to_string_list(data.get("recommended_methods", [])),
        mentor_analysis=str(data.get("mentor_analysis", "")).strip(),
    )


def generate_topic_card(
    research_object: str,
    school_stage: str,
    subject: str,
    teaching_problem: str,
    research_context: str,
    existing_materials: str,
    paper_type: str,
    settings: Settings,
) -> TopicCard:
    llm_client = build_llm_client(settings)
    system_prompt = build_mentor_system_prompt()
    enriched_teaching_problem = (
        f"{teaching_problem.strip()}\n"
        f"研究对象：{research_object.strip()}\n"
        f"论文类型：{paper_type.strip()}"
    )
    enriched_context = (
        f"{research_context.strip()}\n"
        f"已有材料或案例基础：{existing_materials.strip() or '暂无'}"
    )
    user_prompt = build_topic_user_prompt(
        school_stage=school_stage,
        subject=subject,
        teaching_problem=enriched_teaching_problem,
        research_context=enriched_context,
    )

    response_text = llm_client.chat(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.4,
        max_tokens=1400,
    )
    data = _extract_json_object(response_text)
    return _build_topic_card(data)
