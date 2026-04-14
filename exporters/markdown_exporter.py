from core.schemas import LiteratureItem, TopicCard, WritingAsset


def _asset_map(items: list[WritingAsset]) -> dict[str, WritingAsset]:
    return {item.asset_type: item for item in items}


def _related_polish_assets(asset_type: str, polish_assets: list[WritingAsset]) -> list[WritingAsset]:
    return [item for item in polish_assets if asset_type in item.source_refs]


def export_assets_to_markdown(
    topic_card: TopicCard | None,
    literature_items: list[LiteratureItem],
    writing_assets: list[WritingAsset],
    polish_assets: list[WritingAsset],
    output_path: str,
    template_label: str,
    section_template: list[tuple[str, str]],
) -> str:
    writing_asset_map = _asset_map(writing_assets)

    lines: list[str] = [f"# {template_label}", ""]

    lines.extend(["## 选题卡", ""])
    if topic_card:
        lines.extend(
            [
                f"- 题目：{topic_card.title}",
                f"- 研究问题：{topic_card.research_problem}",
                f"- 研究对象：{topic_card.target_population}",
                f"- 研究场景：{topic_card.context}",
                f"- 关键词：{'、'.join(topic_card.keywords)}",
                f"- 推荐方法：{'、'.join(topic_card.recommended_methods)}",
                f"- 导师分析：{topic_card.mentor_analysis}",
                "",
            ]
        )
    else:
        lines.extend(["暂无选题卡", ""])

    lines.extend(["## 文献速读摘要", ""])
    if literature_items:
        for item in literature_items:
            lines.extend(
                [
                    f"### {item.file_name}",
                    f"- 标题：{item.title}",
                    f"- 作者：{', '.join(item.authors)}",
                    f"- 年份：{item.year}",
                    f"- 摘要：{item.abstract}",
                    f"- 方法：{item.method}",
                    f"- 结论：{item.findings}",
                    "",
                ]
            )
    else:
        lines.extend(["暂无文献速读内容", ""])

    lines.extend(["## 写作资产", ""])
    lines.extend([f"当前导出模板：{template_label}", ""])
    lines.extend([f"## {template_label}正文结构", ""])
    for asset_type, section_title in section_template:
        lines.extend([f"### {section_title}", ""])
        asset = writing_asset_map.get(asset_type)
        if asset:
            lines.extend([asset.content, ""])
            related = _related_polish_assets(asset_type, polish_assets)
            for result in related:
                lines.extend([f"#### {result.title}", result.content, ""])
        else:
            lines.extend(["暂无该部分内容", ""])

    extras = [
        asset for asset in writing_assets if asset.asset_type not in {asset_type for asset_type, _ in section_template}
    ]
    if extras:
        lines.extend(["## 其他写作资产", ""])
        for asset in extras:
            lines.extend([f"### {asset.title or asset.asset_type}", asset.content, ""])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path
