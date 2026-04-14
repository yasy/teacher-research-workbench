import json
from pathlib import Path
from typing import Any

from config.settings import Settings
from core.schemas import LiteratureItem, LiteratureReviewPack, TopicCard, WritingAsset
from llm.factory import build_llm_client


PROMPT_PATH = Path(__file__).resolve().parent.parent / "assets" / "prompts" / "writing_star_prompt.md"

PAPER_TYPE_LABELS = {
    "teaching_reform": "教改论文",
    "teaching_case": "教学案例研究",
    "general_research": "一般教育研究论文",
}

PAPER_TYPE_GUIDANCE = {
    "teaching_reform": "围绕改革缘起、改革路径、实施效果与反思建议展开，适合课程改革、教学改革与专业改革类论文。",
    "teaching_case": "围绕真实教学案例、干预过程、案例分析与启示展开，适合案例研究与实践反思类论文。",
    "general_research": "围绕问题提出、文献综述、研究方法、结论与展望展开，适合一般教育科研论文写法。",
}

PAPER_TYPE_BUILD_PLAN_FOCUS = {
    "teaching_reform": {
        "planning_view": "把论文看成一条“改革缘起 -> 改革路径 -> 实施效果 -> 反思建议”的改革叙事链。",
        "material_priority": "优先检查是否已经具备真实改革背景、改革措施、过程材料与效果证据。",
        "recommendation_style": "推荐理由要像教改论文写法，突出为什么此刻先写背景、路径或效果，而不是泛泛给科研建议。",
    },
    "teaching_case": {
        "planning_view": "把论文看成一条“案例背景 -> 干预过程 -> 案例分析 -> 启示”的案例复盘链。",
        "material_priority": "优先检查是否已经具备具体案例场景、干预过程、课堂材料与观察记录。",
        "recommendation_style": "推荐理由要像案例研究写法，突出先交代情境还是先整理过程、分析。",
    },
    "general_research": {
        "planning_view": "把论文看成一条“问题提出 -> 文献综述 -> 研究方法 -> 结论与展望”的常规科研论证链。",
        "material_priority": "优先检查是否已经具备研究问题、综述依据、方法设计与论证边界。",
        "recommendation_style": "推荐理由要像一般教育科研论文写法，说明为什么先搭提纲、问题提出、综述或方法。",
    },
}

PAPER_TYPE_GOALS = {
    "teaching_reform": [
        "paper_outline",
        "reform_background_problem",
        "reform_measures_path",
        "reform_effects",
        "reform_reflection_suggestions",
        "abstract",
    ],
    "teaching_case": [
        "paper_outline",
        "case_background",
        "case_intervention_process",
        "case_analysis",
        "case_insights",
        "abstract",
    ],
    "general_research": [
        "paper_outline",
        "introduction_problem",
        "literature_outline",
        "method",
        "conclusion_outlook",
        "abstract",
    ],
}

WRITING_GOAL_LABELS = {
    "paper_outline": "论文整体提纲",
    "reform_background_problem": "改革背景与问题",
    "reform_measures_path": "改革措施/实施路径",
    "reform_effects": "实施效果",
    "reform_reflection_suggestions": "反思与建议",
    "case_background": "案例背景",
    "case_intervention_process": "干预过程",
    "case_analysis": "案例分析",
    "case_insights": "启示",
    "introduction_problem": "引言/问题提出",
    "literature_outline": "文献综述提纲",
    "method": "研究方法",
    "conclusion_outlook": "结论与展望",
    "abstract": "摘要",
}

GOAL_ASSET_TYPES = {
    "paper_outline": {"paper_outline"},
    "reform_background_problem": {"reform_background_problem"},
    "reform_measures_path": {"reform_measures_path"},
    "reform_effects": {"reform_effects"},
    "reform_reflection_suggestions": {"reform_reflection_suggestions"},
    "case_background": {"case_background"},
    "case_intervention_process": {"case_intervention_process"},
    "case_analysis": {"case_analysis"},
    "case_insights": {"case_insights"},
    "introduction_problem": {"introduction_problem"},
    "literature_outline": {"literature_outline"},
    "method": {"method_draft", "tech_route_text"},
    "conclusion_outlook": {"conclusion_outlook"},
    "abstract": {"abstract_draft", "keywords"},
}

WRITING_GOAL_GUIDANCE = {
    "paper_outline": "先搭论文骨架，输出应能直接指导后续逐部分写作，而不是只给几句概述。",
    "reform_background_problem": "交代改革缘起、现实问题和改革必要性，形成正文开头部分。",
    "reform_measures_path": "说明改革措施、实施步骤和推进路径，形成正文核心部分。",
    "reform_effects": "呈现改革后的效果、证据和阶段性成果。",
    "reform_reflection_suggestions": "总结反思、局限与改进建议，形成结尾部分。",
    "case_background": "说明案例来源、对象、课程与情境，形成案例研究开头部分。",
    "case_intervention_process": "交代具体干预过程、关键设计和实施步骤。",
    "case_analysis": "分析案例结果、关键机制和经验意义。",
    "case_insights": "提炼启示、迁移价值与推广建议。",
    "introduction_problem": "说明研究背景、问题提出和研究价值，形成正文开头部分。",
    "literature_outline": "组织文献综述的分层结构和归纳逻辑。",
    "method": "说明研究方法、研究过程与技术路线，形成方法部分。",
    "conclusion_outlook": "总结研究结论并提出后续展望，形成结尾部分。",
    "abstract": "在主体内容基本成形后，生成摘要初稿和关键词。",
}

GOAL_MODULE_CATEGORY = {
    "paper_outline": "结构骨架",
    "reform_background_problem": "正文模块",
    "reform_measures_path": "正文模块",
    "reform_effects": "正文模块",
    "reform_reflection_suggestions": "结论模块",
    "case_background": "正文模块",
    "case_intervention_process": "正文模块",
    "case_analysis": "正文模块",
    "case_insights": "结论模块",
    "introduction_problem": "正文模块",
    "literature_outline": "正文模块",
    "method": "方法模块",
    "conclusion_outlook": "结论模块",
    "abstract": "摘要模块",
}

GOAL_MODULE_SUMMARIES = {
    "paper_outline": "当前这部分是论文整体提纲，用来搭起整篇论文的结构骨架，方便后续一部分一部分往下写。",
    "reform_background_problem": "当前这部分是改革背景与问题，用来交代为什么要做这项改革、当前痛点是什么。",
    "reform_measures_path": "当前这部分是改革措施/实施路径，用来说明具体做法、推进步骤和实施逻辑。",
    "reform_effects": "当前这部分是实施效果，用来呈现实践后的变化、成效和证据。",
    "reform_reflection_suggestions": "当前这部分是反思与建议，用来收束全文并提出后续改进方向。",
    "case_background": "当前这部分是案例背景，用来交代案例场景、对象和课程情境。",
    "case_intervention_process": "当前这部分是干预过程，用来说明教学干预或实践实施的关键步骤。",
    "case_analysis": "当前这部分是案例分析，用来解释案例结果和关键机制。",
    "case_insights": "当前这部分是启示，用来提炼经验、启发和迁移价值。",
    "introduction_problem": "当前这部分是引言/问题提出，用来说明研究背景、问题和价值。",
    "literature_outline": "当前这部分是文献综述提纲，用来搭起综述结构和归纳逻辑。",
    "method": "当前这部分是研究方法，用来交代研究对象、方法设计和实施路径。",
    "conclusion_outlook": "当前这部分是结论与展望，用来总结研究发现并提出后续方向。",
    "abstract": "当前这部分是摘要，用来在主体内容成形后收束成一段高度概括的论文摘要。",
}

GOAL_WRITE_NOW_REASONS = {
    "paper_outline": "适合作为起步动作，先把整篇论文的骨架搭起来，后续每一部分都会更顺。",
    "reform_background_problem": "适合在提纲之后优先写，用来明确改革缘起、现实问题和研究价值。",
    "reform_measures_path": "适合在背景问题明确后再写，用来展开你的具体改革设计和实施逻辑。",
    "reform_effects": "适合在路径写清楚后再写，用来呈现实践后的变化和证据。",
    "reform_reflection_suggestions": "适合在主体成形后再写，用来总结经验、局限和建议。",
    "case_background": "适合在提纲之后优先写，用来把案例情境和对象交代清楚。",
    "case_intervention_process": "适合在案例背景明确后再写，用来还原你的教学干预过程。",
    "case_analysis": "适合在过程部分之后再写，用来解释结果和关键机制。",
    "case_insights": "适合在案例主体成形后再写，用来提炼启示和推广价值。",
    "introduction_problem": "适合在提纲之后优先写，用来说明研究背景、问题和价值。",
    "literature_outline": "适合在问题提出之后再写，用来组织相关研究并为后续论证打底。",
    "method": "适合在研究问题和综述结构明确后再写，用来交代研究设计和路径。",
    "conclusion_outlook": "适合在主体内容大致成形后再写，用来总结结论并展开展望。",
    "abstract": "通常建议最后再写，等主体内容基本成形后，摘要会更准确、更稳。",
}

GOAL_EXPECTED_CONTENT_POINTS = {
    "paper_outline": [
        "先列出整篇论文的一级部分顺序，建议至少体现“引言/问题提出、文献综述、研究设计或实践路径、结果/分析、结论与展望”这类骨架。",
        "每个一级部分后补一句“这一部分要解决什么问题”或“准备写什么内容”，让提纲能直接指导后续分块写作。",
        "如果适合，可继续细分二级小点，但重点始终是结构清晰、逻辑推进明确，而不是写成长段正文。",
        "整体结构要体现“问题提出 -> 分析论证 -> 结论收束”的推进关系。",
    ],
    "reform_background_problem": [
        "交代改革发生的现实背景、政策要求或课程建设需求。",
        "说明当前教学/课程/专业改革中的具体痛点与不足。",
        "引出本文为何要做这项改革实践，以及研究价值在哪里。",
    ],
    "reform_measures_path": [
        "写清改革的总体思路和实施框架。",
        "分点说明具体改革措施、关键环节和推进步骤。",
        "交代实施过程中的角色分工、资源支持或课程安排。",
    ],
    "reform_effects": [
        "呈现改革实施后的阶段性结果或变化。",
        "结合课堂、作业、反馈、表现等证据说明成效。",
        "必要时区分“已有改进”和“仍待提升”的部分。",
    ],
    "reform_reflection_suggestions": [
        "总结本次改革实践的主要经验和有效做法。",
        "指出当前改革中的局限、难点或尚未解决的问题。",
        "提出后续优化建议或可推广方向。",
    ],
    "case_background": [
        "交代案例发生的学校、课程、对象和教学情境。",
        "说明为什么选择这个案例，它有什么代表性或特殊性。",
        "简要引出案例中要解决的核心问题。",
    ],
    "case_intervention_process": [
        "按时间或步骤写清案例干预的实施过程。",
        "说明关键教学设计、资源使用和课堂推进方式。",
        "突出案例中真正影响结果的关键动作。",
    ],
    "case_analysis": [
        "分析案例实施后出现的主要结果与变化。",
        "解释为什么会产生这些结果，背后的机制是什么。",
        "把个案经验上升为具有分析价值的认识。",
    ],
    "case_insights": [
        "提炼本案例对类似课程或教学改革的启示。",
        "说明哪些经验可迁移、哪些条件下才适用。",
        "提出后续推广或改进建议。",
    ],
    "introduction_problem": [
        "从现实背景或研究场景切入，引出研究主题。",
        "明确当前存在的核心问题和研究空白。",
        "说明本文研究的意义、价值和基本关注点。",
    ],
    "literature_outline": [
        "按主题、视角或问题线索组织已有研究。",
        "归纳已有研究的主要观点、方法或共识。",
        "指出当前文献中的不足，并自然过渡到本文研究。",
    ],
    "method": [
        "说明研究对象、研究方法和资料来源。",
        "交代研究实施过程、观察维度或分析路径。",
        "必要时补充技术路线、工具使用或数据处理方式。",
    ],
    "conclusion_outlook": [
        "总结全文最核心的研究结论。",
        "回应前文提出的问题，说明本文贡献。",
        "提出后续研究或实践改进方向。",
    ],
    "abstract": [
        "用简洁语言概括研究背景、研究问题和研究方法。",
        "交代最核心的结果、结论或实践发现。",
        "提炼可对应全文的关键词，不重复正文细节。",
    ],
}

GOAL_HOLD_POINTS = {
    "paper_outline": [
        "先不要把提纲写成长段正文，重点是结构和各部分任务。",
        "先不要急着写摘要式总结，提纲阶段只搭骨架。",
    ],
    "reform_background_problem": [
        "先不要在这里展开过多实施细节，实施路径留到下一部分。",
        "先不要把结果和反思提前写进开头。",
    ],
    "reform_measures_path": [
        "先不要把效果判断写得过满，成效部分单独展开。",
        "先不要把结尾式反思提前塞进实施路径。",
    ],
    "reform_effects": [
        "先不要在结果部分过度重复前文实施过程。",
        "先不要把后续建议写成这一部分主体。",
    ],
    "reform_reflection_suggestions": [
        "先不要重新铺陈改革背景，重点放在总结和建议。",
        "先不要把未验证的新措施写成既有结果。",
    ],
    "case_background": [
        "先不要在背景部分写完整分析结论。",
        "先不要把干预步骤提前写得过细。",
    ],
    "case_intervention_process": [
        "先不要把分析判断写成过程描述。",
        "先不要提前下启示式结论。",
    ],
    "case_analysis": [
        "先不要把背景和过程大段重复一遍。",
        "先不要把推广建议写成分析主体。",
    ],
    "case_insights": [
        "先不要重述案例细节，重点放在启示提炼。",
        "先不要把尚未验证的推广效果写得过实。",
    ],
    "introduction_problem": [
        "先不要在引言里展开完整文献综述主体。",
        "先不要提前写研究结果和结论。",
    ],
    "literature_outline": [
        "先不要把方法设计和结果讨论混入综述结构。",
        "先不要把综述写成资料堆砌，重点是归纳与过渡。",
    ],
    "method": [
        "先不要在方法部分提前讨论最终研究结论。",
        "先不要把背景和综述内容大量重复到方法里。",
    ],
    "conclusion_outlook": [
        "先不要在结论部分重新铺开全文正文细节。",
        "先不要把摘要式概括和展望混得没有层次。",
    ],
    "abstract": [
        "先不要加入正文里没有出现的新观点。",
        "先不要把摘要写成提纲或长段背景介绍。",
    ],
}

GOAL_ORDER = {
    paper_type: {goal_id: index for index, goal_id in enumerate(goal_ids)}
    for paper_type, goal_ids in PAPER_TYPE_GOALS.items()
}

GOAL_PRIMARY_ASSET_TYPE = {
    goal_id: sorted(asset_types)[0] for goal_id, asset_types in GOAL_ASSET_TYPES.items()
}


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


def get_writing_goals_for_paper_type(paper_type: str) -> list[str]:
    return PAPER_TYPE_GOALS.get(paper_type, PAPER_TYPE_GOALS["general_research"])


def get_primary_asset_type_for_goal(writing_goal: str) -> str:
    return GOAL_PRIMARY_ASSET_TYPE.get(writing_goal, writing_goal)


def get_goal_label_from_asset_type(asset_type: str) -> str:
    for goal_id, asset_types in GOAL_ASSET_TYPES.items():
        if asset_type in asset_types:
            return WRITING_GOAL_LABELS.get(goal_id, asset_type)
    return asset_type


def get_goal_module_summary(writing_goal: str) -> str:
    return GOAL_MODULE_SUMMARIES.get(writing_goal, "当前这部分是本次写作目标对应的正文模块。")


def get_goal_module_category(writing_goal: str) -> str:
    return GOAL_MODULE_CATEGORY.get(writing_goal, "正文模块")


def get_goal_write_now_reason(writing_goal: str) -> str:
    return GOAL_WRITE_NOW_REASONS.get(writing_goal, "这是当前论文搭建顺序里适合优先推进的一部分。")


def get_goal_expected_content_points(writing_goal: str) -> list[str]:
    return GOAL_EXPECTED_CONTENT_POINTS.get(writing_goal, ["围绕当前论文部分写清这一段应承担的核心任务。"])


def get_goal_hold_points(writing_goal: str) -> list[str]:
    return GOAL_HOLD_POINTS.get(writing_goal, ["当前先不要把其他部分的大段内容提前写进这一部分。"])


def sort_writing_assets(assets: list[WritingAsset], paper_type: str) -> list[WritingAsset]:
    goal_order = GOAL_ORDER.get(paper_type, GOAL_ORDER["general_research"])

    def _sort_key(asset: WritingAsset) -> tuple[int, str]:
        for goal_id, asset_types in GOAL_ASSET_TYPES.items():
            if asset.asset_type in asset_types:
                return goal_order.get(goal_id, 999), asset.title or asset.asset_type
        return 999, asset.title or asset.asset_type

    return sorted(assets, key=_sort_key)


def upsert_writing_assets(
    existing_assets: list[WritingAsset],
    new_assets: list[WritingAsset],
    paper_type: str,
) -> list[WritingAsset]:
    merged = {asset.asset_type: asset for asset in existing_assets}
    for asset in new_assets:
        merged[asset.asset_type] = asset
    return sort_writing_assets(list(merged.values()), paper_type)


def build_literature_digest(items: list[LiteratureItem]) -> str:
    if not items:
        return "暂无文献速读结果。"

    blocks = []
    for item in items:
        blocks.append(
            f"文件: {item.file_name}\n"
            f"标题: {item.title}\n"
            f"摘要: {item.abstract}\n"
            f"方法: {item.method}\n"
            f"结论: {item.findings}"
        )
    return "\n\n".join(blocks)


def build_review_pack_digest(review_pack: LiteratureReviewPack | None) -> str:
    if review_pack is None:
        return "暂无文献综述素材包。"

    sections = [
        ("高频主题", review_pack.high_frequency_themes),
        ("常用研究方法", review_pack.common_methods),
        ("共同结论", review_pack.common_findings),
        ("主要分歧", review_pack.major_disagreements),
        ("研究不足", review_pack.research_limitations),
        ("可写切入点", review_pack.suggested_angles),
    ]
    lines = []
    for title, values in sections:
        if values:
            lines.append(f"{title}: {'；'.join(values)}")
    return "\n".join(lines) if lines else "暂无文献综述素材包。"


def build_writing_bridge_digest(
    selected_review_themes: list[str] | None = None,
    selected_research_gaps: list[str] | None = None,
    selected_writing_angles: list[str] | None = None,
    writing_context_notes: str = "",
) -> str:
    lines = []
    if selected_review_themes:
        lines.append(f"本次采用的高频主题（用于文献综述、提纲、理论背景）: {'；'.join(selected_review_themes)}")
    if selected_research_gaps:
        lines.append(f"本次采用的研究不足（用于问题提出、研究空白、研究价值）: {'；'.join(selected_research_gaps)}")
    if selected_writing_angles:
        lines.append(f"本次采用的可写切入点（用于当前部分方向、创新点、研究目标）: {'；'.join(selected_writing_angles)}")
    if writing_context_notes.strip():
        lines.append(f"额外背景说明（用于增强真实性与场景贴合）: {writing_context_notes.strip()}")
    return "\n".join(lines) if lines else "暂无额外写作依据。"


def build_teacher_material_digest(
    writing_background_info: str = "",
    writing_existing_practice: str = "",
    writing_evidence_notes: str = "",
    writing_scope_limits: str = "",
    preferred_writing_sections: list[str] | None = None,
) -> str:
    lines = []
    if writing_background_info.strip():
        lines.append(f"真实研究/教学背景: {writing_background_info.strip()}")
    if writing_existing_practice.strip():
        lines.append(f"已有做法或改革措施: {writing_existing_practice.strip()}")
    if writing_evidence_notes.strip():
        lines.append(f"已有证据或案例材料: {writing_evidence_notes.strip()}")
    if writing_scope_limits.strip():
        lines.append(f"研究边界与限制: {writing_scope_limits.strip()}")
    if preferred_writing_sections:
        labels = [WRITING_GOAL_LABELS.get(item, item) for item in preferred_writing_sections]
        lines.append(f"老师当前更想优先完成的论文部分: {'；'.join(labels)}")
    return "\n".join(lines) if lines else "暂无老师补充的写作材料。"


def build_existing_draft_digest(existing_assets: list[WritingAsset], paper_type: str) -> str:
    ordered_assets = sort_writing_assets(existing_assets, paper_type)
    if not ordered_assets:
        return "当前还没有已生成的论文部分。"

    blocks = []
    for asset in ordered_assets:
        preview = asset.content.strip().replace("\n", " ")
        preview = preview[:120] + ("…" if len(preview) > 120 else "")
        blocks.append(f"- {asset.title or asset.asset_type}（{asset.asset_type}）：{preview}")
    return "\n".join(blocks)


def get_rule_based_build_suggestion(
    paper_type: str,
    preferred_writing_sections: list[str],
    existing_assets: list[WritingAsset],
) -> dict[str, list[str] | str]:
    ordered_goals = get_writing_goals_for_paper_type(paper_type)
    completed_asset_types = {asset.asset_type for asset in existing_assets}

    completed_goals = [
        goal_id
        for goal_id in ordered_goals
        if any(asset_type in completed_asset_types for asset_type in GOAL_ASSET_TYPES.get(goal_id, set()))
    ]
    pending_goals = [goal_id for goal_id in ordered_goals if goal_id not in completed_goals]
    preferred_valid = [goal_id for goal_id in preferred_writing_sections if goal_id in pending_goals]
    recommended_goals = list(pending_goals)

    # Teachers can express preference, but the fallback planner must still preserve
    # the canonical paper-building order: outline first, abstract last.
    if preferred_valid:
        movable_goals = [goal_id for goal_id in recommended_goals if goal_id not in {"paper_outline", "abstract"}]
        preferred_movable = [goal_id for goal_id in movable_goals if goal_id in preferred_valid]
        remaining_movable = [goal_id for goal_id in movable_goals if goal_id not in preferred_movable]
        reordered = []
        if "paper_outline" in recommended_goals:
            reordered.append("paper_outline")
        reordered.extend(preferred_movable)
        reordered.extend(remaining_movable)
        if "abstract" in recommended_goals:
            reordered.append("abstract")
        recommended_goals = reordered

    deferred_goals: list[str] = []
    if "abstract" in recommended_goals and len(recommended_goals) > 1:
        recommended_goals = [goal_id for goal_id in recommended_goals if goal_id != "abstract"]
        deferred_goals.append("abstract")

    if not pending_goals:
        readiness_summary = "当前各个标准部分都已有草稿，可以进入整体修订和润色阶段。"
        reasoning_notes = "整篇论文的基础模块已初步搭建完成，建议回到整篇视角检查衔接、逻辑和完整性。"
    elif completed_goals:
        readiness_summary = "当前已经有部分论文草稿，适合沿着未完成部分继续逐块搭建。"
        reasoning_notes = "建议优先继续未完成的主体部分，摘要仍建议放到主体较完整之后。"
    else:
        readiness_summary = "当前建议先从提纲或正文开头部分入手，不建议一开始先写摘要。"
        reasoning_notes = "论文起步阶段最重要的是先把结构骨架和前几部分逻辑搭稳，后面再逐块完善。"

    strengths = []
    if preferred_valid:
        strengths.append("你已经明确表达了当前优先想完成的论文部分。")
    if completed_goals:
        strengths.append("当前已有部分草稿，可作为继续往下搭建的基础。")

    gaps = []
    if "abstract" in pending_goals:
        gaps.append("摘要建议放在主体内容相对完整之后再写。")
    if not completed_goals:
        gaps.append("当前尚未形成完整骨架，建议先搭提纲或开头部分。")

    return {
        "paper_type": paper_type,
        "readiness_summary": readiness_summary,
        "material_strengths": strengths,
        "material_gaps": gaps,
        "recommended_sections": recommended_goals[:3],
        "deferred_sections": deferred_goals[:3],
        "reasoning_notes": reasoning_notes,
        "recommended_sequence_note": "先搭骨架，再写主体，最后补摘要，更符合日常论文写作顺序。",
    }


def build_build_plan_prompt(
    selected_topic: str,
    topic_card: TopicCard,
    literature_items: list[LiteratureItem],
    review_pack: LiteratureReviewPack | None,
    paper_type: str,
    existing_assets: list[WritingAsset],
    selected_review_themes: list[str] | None = None,
    selected_research_gaps: list[str] | None = None,
    selected_writing_angles: list[str] | None = None,
    writing_context_notes: str = "",
    writing_background_info: str = "",
    writing_existing_practice: str = "",
    writing_evidence_notes: str = "",
    writing_scope_limits: str = "",
    preferred_writing_sections: list[str] | None = None,
) -> str:
    ordered_goals = get_writing_goals_for_paper_type(paper_type)
    paper_focus = PAPER_TYPE_BUILD_PLAN_FOCUS.get(paper_type, PAPER_TYPE_BUILD_PLAN_FOCUS["general_research"])
    return f"""
你是一名帮助教师分步搭建科研论文的写作规划助手。请不要直接写正文，而是判断：
1. 当前材料是否足够支撑下一步写作
2. 下一步最适合先搭建哪 1-3 个论文部分
3. 哪些部分应暂后处理
4. 为什么这样安排

请严格返回 JSON，不要输出额外解释。JSON 格式如下：
{{
  "readiness_summary": "一句话说明当前材料是否足够",
  "material_strengths": ["材料优势1", "材料优势2"],
  "material_gaps": ["材料缺口1", "材料缺口2"],
  "recommended_sections": ["goal_id1", "goal_id2"],
  "deferred_sections": ["goal_id3"],
  "reasoning_notes": "2-4句推荐理由",
  "recommended_sequence_note": "一句话说明为什么先按这个顺序搭建"
}}

要求：
- recommended_sections 和 deferred_sections 的值只能来自这组 goal_id：{ordered_goals}
- 优先结合老师明确想优先完成的部分，但不能违背论文常规顺序
- 如果当前已有草稿，请基于现有进度继续往下搭建，不要重复建议已完成部分
- 摘要一般放到主体内容成形后再推荐，除非你判断当前已适合写摘要
- 推荐理由必须贴合当前论文类型的真实写法，不要使用空泛套话

【当前论文类型的规划视角】
{paper_focus["planning_view"]}

【当前论文类型优先检查的材料】
{paper_focus["material_priority"]}

【当前论文类型的推荐理由写法】
{paper_focus["recommendation_style"]}

【当前选题】
{selected_topic}

【研究问题】
{topic_card.research_problem}

【当前论文类型】
{PAPER_TYPE_LABELS.get(paper_type, paper_type)}

【论文类型写作导向】
{PAPER_TYPE_GUIDANCE.get(paper_type, "")}

【文献速读摘要】
{build_literature_digest(literature_items)}

【文献综述素材包】
{build_review_pack_digest(review_pack)}

【本次写作采用依据】
{build_writing_bridge_digest(
    selected_review_themes=selected_review_themes,
    selected_research_gaps=selected_research_gaps,
    selected_writing_angles=selected_writing_angles,
    writing_context_notes=writing_context_notes,
)}

【老师补充的写作材料】
{build_teacher_material_digest(
    writing_background_info=writing_background_info,
    writing_existing_practice=writing_existing_practice,
    writing_evidence_notes=writing_evidence_notes,
    writing_scope_limits=writing_scope_limits,
    preferred_writing_sections=preferred_writing_sections,
)}

【当前已生成草稿】
{build_existing_draft_digest(existing_assets, paper_type)}
""".strip()


def generate_ai_build_suggestion(
    selected_topic: str,
    topic_card: TopicCard,
    literature_items: list[LiteratureItem],
    review_pack: LiteratureReviewPack | None,
    paper_type: str,
    existing_assets: list[WritingAsset],
    settings: Settings,
    selected_review_themes: list[str] | None = None,
    selected_research_gaps: list[str] | None = None,
    selected_writing_angles: list[str] | None = None,
    writing_context_notes: str = "",
    writing_background_info: str = "",
    writing_existing_practice: str = "",
    writing_evidence_notes: str = "",
    writing_scope_limits: str = "",
    preferred_writing_sections: list[str] | None = None,
) -> dict[str, Any]:
    llm_client = build_llm_client(settings)
    prompt = build_build_plan_prompt(
        selected_topic=selected_topic,
        topic_card=topic_card,
        literature_items=literature_items,
        review_pack=review_pack,
        paper_type=paper_type,
        existing_assets=existing_assets,
        selected_review_themes=selected_review_themes,
        selected_research_gaps=selected_research_gaps,
        selected_writing_angles=selected_writing_angles,
        writing_context_notes=writing_context_notes,
        writing_background_info=writing_background_info,
        writing_existing_practice=writing_existing_practice,
        writing_evidence_notes=writing_evidence_notes,
        writing_scope_limits=writing_scope_limits,
        preferred_writing_sections=preferred_writing_sections,
    )
    response_text = llm_client.chat(
        user_prompt=prompt,
        system_prompt="You are an academic writing planner. Return strict JSON only.",
        temperature=0.3,
        max_tokens=1200,
    )
    data = _extract_json_object(response_text)
    allowed_goals = set(get_writing_goals_for_paper_type(paper_type))
    recommended = [goal for goal in data.get("recommended_sections", []) if goal in allowed_goals]
    deferred = [goal for goal in data.get("deferred_sections", []) if goal in allowed_goals]
    return {
        "paper_type": paper_type,
        "readiness_summary": str(data.get("readiness_summary", "")).strip(),
        "material_strengths": [str(item).strip() for item in data.get("material_strengths", []) if str(item).strip()][:5],
        "material_gaps": [str(item).strip() for item in data.get("material_gaps", []) if str(item).strip()][:5],
        "recommended_sections": recommended[:3],
        "deferred_sections": deferred[:3],
        "reasoning_notes": str(data.get("reasoning_notes", "")).strip(),
        "recommended_sequence_note": str(data.get("recommended_sequence_note", "")).strip(),
    }


def build_star_prompt(
    selected_topic: str,
    topic_card: TopicCard,
    literature_items: list[LiteratureItem],
    review_pack: LiteratureReviewPack | None = None,
    selected_review_themes: list[str] | None = None,
    selected_research_gaps: list[str] | None = None,
    selected_writing_angles: list[str] | None = None,
    writing_context_notes: str = "",
    writing_background_info: str = "",
    writing_existing_practice: str = "",
    writing_evidence_notes: str = "",
    writing_scope_limits: str = "",
    preferred_writing_sections: list[str] | None = None,
    writing_goal: str = "paper_outline",
    paper_type: str = "general_research",
) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    goal_asset_types = sorted(GOAL_ASSET_TYPES.get(writing_goal, {writing_goal}))
    target_asset_type = goal_asset_types[0] if len(goal_asset_types) == 1 else ", ".join(goal_asset_types)
    topic_title = selected_topic.strip() or topic_card.title
    base_prompt = template.format(
        topic_title=topic_title,
        research_problem=topic_card.research_problem,
        context=topic_card.context,
        target_population=topic_card.target_population,
        paper_type_label=PAPER_TYPE_LABELS.get(paper_type, PAPER_TYPE_LABELS["general_research"]),
        paper_type_guidance=PAPER_TYPE_GUIDANCE.get(paper_type, PAPER_TYPE_GUIDANCE["general_research"]),
        writing_goal_label=WRITING_GOAL_LABELS.get(writing_goal, "论文整体提纲"),
        writing_goal_guidance=WRITING_GOAL_GUIDANCE.get(writing_goal, "请围绕当前写作目标输出内容。"),
        research_questions="\n".join(f"- {item}" for item in topic_card.research_questions) or "- 暂无",
        keywords="；".join(topic_card.keywords) or "暂无",
        recommended_methods="；".join(topic_card.recommended_methods) or "暂无",
        literature_digest=build_literature_digest(literature_items),
        review_pack_digest=build_review_pack_digest(review_pack),
        target_asset_type=target_asset_type,
    )
    bridge_prompt = build_writing_bridge_digest(
        selected_review_themes=selected_review_themes,
        selected_research_gaps=selected_research_gaps,
        selected_writing_angles=selected_writing_angles,
        writing_context_notes=writing_context_notes,
    )
    teacher_material_prompt = build_teacher_material_digest(
        writing_background_info=writing_background_info,
        writing_existing_practice=writing_existing_practice,
        writing_evidence_notes=writing_evidence_notes,
        writing_scope_limits=writing_scope_limits,
        preferred_writing_sections=preferred_writing_sections,
    )
    expected_points = "\n".join(f"- {item}" for item in get_goal_expected_content_points(writing_goal))
    hold_points = "\n".join(f"- {item}" for item in get_goal_hold_points(writing_goal))
    return (
        f"{base_prompt}\n\n"
        f"【本次写作采用依据】\n{bridge_prompt}\n\n"
        f"【老师补充的写作材料】\n{teacher_material_prompt}\n\n"
        f"【当前这一部分建议至少写出】\n{expected_points}\n\n"
        f"【当前阶段先不要展开】\n{hold_points}\n\n"
        "要求：优先结合以上文献依据与老师补充的真实材料，围绕当前论文类型和当前写作部分生成内容；"
        "不要把摘要写成先行部分，除非当前写作目标本身就是摘要。"
    )


def _normalize_assets(data: dict[str, Any]) -> list[WritingAsset]:
    assets: list[WritingAsset] = []
    for item in data.get("assets", []):
        if not isinstance(item, dict):
            continue
        assets.append(
            WritingAsset(
                asset_type=str(item.get("asset_type", "")).strip(),
                title=str(item.get("title", "")).strip(),
                content=str(item.get("content", "")).strip(),
                source_refs=[str(ref).strip() for ref in item.get("source_refs", []) if str(ref).strip()],
            )
        )
    return assets


def filter_assets_by_goal(assets: list[WritingAsset], writing_goal: str) -> list[WritingAsset]:
    allowed = GOAL_ASSET_TYPES.get(writing_goal, set())
    return [asset for asset in assets if asset.asset_type in allowed]


def generate_writing_assets(
    selected_topic: str,
    topic_card: TopicCard,
    literature_items: list[LiteratureItem],
    review_pack: LiteratureReviewPack | None,
    selected_review_themes: list[str] | None,
    selected_research_gaps: list[str] | None,
    selected_writing_angles: list[str] | None,
    writing_context_notes: str,
    settings: Settings,
    writing_goal: str = "paper_outline",
    paper_type: str = "general_research",
    writing_background_info: str = "",
    writing_existing_practice: str = "",
    writing_evidence_notes: str = "",
    writing_scope_limits: str = "",
    preferred_writing_sections: list[str] | None = None,
) -> list[WritingAsset]:
    llm_client = build_llm_client(settings)
    prompt = build_star_prompt(
        selected_topic,
        topic_card,
        literature_items,
        review_pack=review_pack,
        selected_review_themes=selected_review_themes,
        selected_research_gaps=selected_research_gaps,
        selected_writing_angles=selected_writing_angles,
        writing_context_notes=writing_context_notes,
        writing_background_info=writing_background_info,
        writing_existing_practice=writing_existing_practice,
        writing_evidence_notes=writing_evidence_notes,
        writing_scope_limits=writing_scope_limits,
        preferred_writing_sections=preferred_writing_sections,
        writing_goal=writing_goal,
        paper_type=paper_type,
    )
    response_text = llm_client.chat(
        user_prompt=prompt,
        system_prompt="You are an academic writing asset generator. Return strict JSON only.",
        temperature=0.4,
        max_tokens=2400,
    )
    data = _extract_json_object(response_text)
    assets = _normalize_assets(data)
    return filter_assets_by_goal(assets, writing_goal)
