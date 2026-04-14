from pathlib import Path

from config.settings import Settings
from core.schemas import LiteratureReviewPack, WritingAsset
from llm.factory import build_llm_client


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "prompts"

POLISH_ACTIONS = {
    "academic_polish": (
        "学术化优化",
        "请将以下内容优化为更符合中国教师科研论文写作风格的正式学术表达。",
    ),
    "compress": (
        "精简压缩",
        "请在保留核心信息的前提下，精简压缩以下内容，使表达更紧凑。",
    ),
    "style_unify": (
        "风格统一",
        "请统一以下内容的表达风格，使其更连贯、一致、稳定。",
    ),
}


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _build_review_pack_context(review_pack: LiteratureReviewPack | None) -> str:
    if review_pack is None:
        return "当前未加载综述素材。"

    lines = []
    if review_pack.high_frequency_themes:
        lines.append(f"高频研究主题：{'；'.join(review_pack.high_frequency_themes)}")
    if review_pack.major_disagreements:
        lines.append(f"主要分歧：{'；'.join(review_pack.major_disagreements)}")
    if review_pack.research_limitations:
        lines.append(f"研究不足：{'；'.join(review_pack.research_limitations)}")
    if review_pack.suggested_angles:
        lines.append(f"可写切入点：{'；'.join(review_pack.suggested_angles)}")
    return "\n".join(lines) if lines else "当前未加载综述素材。"


def _build_generic_polish_prompt(
    asset: WritingAsset,
    action: str,
    review_pack: LiteratureReviewPack | None = None,
) -> str:
    action_label, action_instruction = POLISH_ACTIONS[action]
    use_review_context = action in {"academic_polish", "style_unify"}
    review_context = _build_review_pack_context(review_pack) if use_review_context else "本次动作不额外使用综述素材上下文。"
    return (
        f"你正在处理的内容类型：{asset.title or asset.asset_type}\n"
        f"优化动作：{action_label}\n\n"
        f"{action_instruction}\n\n"
        f"综述素材支持：\n{review_context}\n\n"
        f"要求：\n"
        f"- 保持原意，不虚构数据\n"
        f"- 如果已加载综述素材，请适度增强研究逻辑一致性，使表述更贴合当前研究主题、研究不足和可写切入点\n"
        f"- 输出仅保留优化后的正文\n\n"
        f"原文：\n{asset.content.strip()}"
    )


def optimize_writing_asset(
    asset: WritingAsset,
    action: str,
    settings: Settings,
    review_pack: LiteratureReviewPack | None = None,
) -> WritingAsset:
    if action not in POLISH_ACTIONS:
        raise ValueError(f"Unsupported polish action: {action}")

    llm_client = build_llm_client(settings)
    prompt = _build_generic_polish_prompt(asset, action, review_pack=review_pack)
    content = llm_client.chat(
        user_prompt=prompt,
        system_prompt="You are an academic writing optimization assistant.",
        temperature=0.3,
        max_tokens=1400,
    ).strip()

    action_label, _ = POLISH_ACTIONS[action]
    return WritingAsset(
        asset_type=f"{asset.asset_type}_{action}",
        title=f"{asset.title or asset.asset_type} - {action_label}",
        content=content,
        source_refs=[asset.asset_type],
    )


def polish_chinese_abstract(
    asset: WritingAsset,
    settings: Settings,
    review_pack: LiteratureReviewPack | None = None,
) -> WritingAsset:
    llm_client = build_llm_client(settings)
    prompt = _load_prompt("abstract_polish_prompt.md").format(
        abstract_text=asset.content.strip(),
        review_pack_context=_build_review_pack_context(review_pack),
    )
    content = llm_client.chat(
        user_prompt=prompt,
        system_prompt="You are an academic abstract polishing assistant.",
        temperature=0.3,
        max_tokens=1200,
    ).strip()
    return WritingAsset(
        asset_type="polished_abstract_cn",
        title="中文润色摘要",
        content=content,
        source_refs=[asset.asset_type],
    )


def optimize_keywords_from_abstract(asset: WritingAsset, settings: Settings) -> WritingAsset:
    llm_client = build_llm_client(settings)
    prompt = (
        "请基于以下中文摘要，给出 4-6 个更适合中国教师科研论文使用的关键词建议。"
        "只输出关键词结果，使用中文顿号分隔。\n\n摘要：\n"
        f"{asset.content.strip()}"
    )
    content = llm_client.chat(
        user_prompt=prompt,
        system_prompt="You are a keyword optimization assistant.",
        temperature=0.2,
        max_tokens=300,
    ).strip()
    return WritingAsset(
        asset_type="keywords_optimized",
        title="关键词优化建议",
        content=content,
        source_refs=[asset.asset_type],
    )
