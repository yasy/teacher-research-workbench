from pathlib import Path

from core.schemas import LiteratureItem, TopicCard, WritingAsset
from core.utils import ensure_dir, now_ts, safe_filename
from exporters.docx_exporter import export_assets_to_docx
from exporters.markdown_exporter import export_assets_to_markdown


EXPORT_TEMPLATE_LABELS = {
    "teaching_reform": "教改论文模板",
    "teaching_case": "教学案例研究模板",
    "general_research": "一般教育研究论文模板",
}

EXPORT_SECTION_TEMPLATES = {
    "teaching_reform": [
        ("reform_background_problem", "改革背景与问题"),
        ("reform_measures_path", "改革措施/实施路径"),
        ("reform_effects", "实施效果"),
        ("reform_reflection_suggestions", "反思与建议"),
    ],
    "teaching_case": [
        ("case_background", "案例背景"),
        ("case_intervention_process", "干预过程"),
        ("case_analysis", "案例分析"),
        ("case_insights", "启示"),
    ],
    "general_research": [
        ("paper_outline", "论文整体提纲"),
        ("abstract_draft", "摘要"),
        ("introduction_problem", "引言/问题提出"),
        ("literature_outline", "文献综述提纲"),
        ("method_draft", "研究方法"),
        ("conclusion_outlook", "结论与展望"),
    ],
}


def build_export_filename(topic_card: TopicCard | None, suffix: str) -> str:
    base = safe_filename(topic_card.title if topic_card and topic_card.title else "teacher_research_workbench")
    return f"{base}_{now_ts()}.{suffix}"


def infer_paper_type(writing_assets: list[WritingAsset]) -> str:
    asset_types = {asset.asset_type for asset in writing_assets}

    if asset_types & {
        "reform_background_problem",
        "reform_measures_path",
        "reform_effects",
        "reform_reflection_suggestions",
    }:
        return "teaching_reform"

    if asset_types & {
        "case_background",
        "case_intervention_process",
        "case_analysis",
        "case_insights",
    }:
        return "teaching_case"

    return "general_research"


def get_export_template_label(paper_type: str) -> str:
    return EXPORT_TEMPLATE_LABELS.get(paper_type, EXPORT_TEMPLATE_LABELS["general_research"])


def get_export_section_template(paper_type: str) -> list[tuple[str, str]]:
    return EXPORT_SECTION_TEMPLATES.get(paper_type, EXPORT_SECTION_TEMPLATES["general_research"])


def get_project_module_status(writing_assets: list[WritingAsset]) -> tuple[str, str, list[tuple[str, str, bool]], list[str]]:
    paper_type = infer_paper_type(writing_assets)
    template_label = get_export_template_label(paper_type)
    section_template = get_export_section_template(paper_type)
    asset_types = {asset.asset_type for asset in writing_assets}
    module_rows: list[tuple[str, str, bool]] = []
    missing_modules: list[str] = []

    for asset_type, section_title in section_template:
        exists = asset_type in asset_types
        module_rows.append((asset_type, section_title, exists))
        if not exists:
            missing_modules.append(section_title)

    return paper_type, template_label, module_rows, missing_modules


def get_export_completeness(writing_assets: list[WritingAsset]) -> dict:
    paper_type, template_label, module_rows, missing_modules = get_project_module_status(writing_assets)
    required_modules = [section_title for _, section_title, _ in module_rows]
    existing_modules = [section_title for _, section_title, exists in module_rows if exists]
    return {
        "paper_type": paper_type,
        "template_label": template_label,
        "required_modules": required_modules,
        "existing_modules": existing_modules,
        "missing_modules": missing_modules,
        "is_complete": len(missing_modules) == 0,
    }


def export_project_to_markdown(
    topic_card: TopicCard | None,
    literature_items: list[LiteratureItem],
    writing_assets: list[WritingAsset],
    polish_assets: list[WritingAsset],
    outputs_dir: str,
) -> str:
    ensure_dir(outputs_dir)
    paper_type = infer_paper_type(writing_assets)
    template_label = get_export_template_label(paper_type)
    section_template = get_export_section_template(paper_type)
    output_path = str(Path(outputs_dir) / build_export_filename(topic_card, "md"))
    return export_assets_to_markdown(
        topic_card,
        literature_items,
        writing_assets,
        polish_assets,
        output_path,
        template_label=template_label,
        section_template=section_template,
    )


def export_project_to_docx(
    topic_card: TopicCard | None,
    literature_items: list[LiteratureItem],
    writing_assets: list[WritingAsset],
    polish_assets: list[WritingAsset],
    outputs_dir: str,
) -> str:
    ensure_dir(outputs_dir)
    paper_type = infer_paper_type(writing_assets)
    template_label = get_export_template_label(paper_type)
    section_template = get_export_section_template(paper_type)
    output_path = str(Path(outputs_dir) / build_export_filename(topic_card, "docx"))
    return export_assets_to_docx(
        topic_card,
        literature_items,
        writing_assets,
        polish_assets,
        output_path,
        template_label=template_label,
        section_template=section_template,
    )
