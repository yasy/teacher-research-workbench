import streamlit as st

from config.settings import load_settings
from core.schemas import WritingAsset
from core.state import (
    clear_busy_action,
    get_busy_action,
    get_literature_items,
    get_literature_review_pack,
    get_polish_assets,
    get_topic_card,
    get_writing_assets,
    pop_page_message,
    set_busy_action,
    set_page_message,
    set_polish_assets,
)
from services.export_service import (
    export_project_to_docx,
    export_project_to_markdown,
    get_export_completeness,
    get_project_module_status,
)
from services.polish_service import optimize_keywords_from_abstract, optimize_writing_asset, polish_chinese_abstract
from services.translation_service import translate_abstract_to_english


def _render_flash_message() -> None:
    message = pop_page_message()
    if not message:
        return
    if message["type"] == "success":
        st.success(message["text"])
    elif message["type"] == "warning":
        st.warning(message["text"])
    else:
        st.error(message["text"])


def _is_abstract_asset(asset: WritingAsset) -> bool:
    return asset.asset_type == "abstract_draft" or "摘要" in (asset.title or "") or "abstract" in asset.asset_type.lower()


def _find_related_results(asset: WritingAsset, polish_assets: list[WritingAsset]) -> list[WritingAsset]:
    return [item for item in polish_assets if asset.asset_type in item.source_refs]


def _upsert_polish_asset(existing_assets: list[WritingAsset], new_asset: WritingAsset) -> list[WritingAsset]:
    updated = [
        item
        for item in existing_assets
        if not (item.asset_type == new_asset.asset_type and item.source_refs == new_asset.source_refs)
    ]
    updated.append(new_asset)
    return updated


def _has_review_pack_support(review_pack) -> bool:
    return any(
        [
            review_pack.high_frequency_themes,
            review_pack.major_disagreements,
            review_pack.research_limitations,
            review_pack.suggested_angles,
        ]
    )


def _render_review_pack_support(review_pack) -> None:
    st.subheader("当前综述素材支持")
    if _has_review_pack_support(review_pack):
        st.success("已加载综述素材支持，学术化优化和风格统一会参考文献归纳上下文。")
        if review_pack.high_frequency_themes:
            st.caption(f"高频研究主题：{'；'.join(review_pack.high_frequency_themes[:3])}")
        if review_pack.research_limitations:
            st.caption(f"研究不足：{'；'.join(review_pack.research_limitations[:3])}")
        if review_pack.suggested_angles:
            st.caption(f"可写切入点：{'；'.join(review_pack.suggested_angles[:3])}")
    else:
        st.info("当前未加载综述素材，优化将不含文献归纳上下文，但仍可进行基础润色。")


def render_polish_export_page() -> None:
    _render_flash_message()

    st.title("润色与导出")
    st.info("当前页面面向整篇项目视图：可按模块逐一优化，并基于整个项目的写作资产集合进行导出。")

    topic_card = get_topic_card()
    literature_items = get_literature_items()
    review_pack = get_literature_review_pack()
    writing_assets = get_writing_assets()
    polish_assets = get_polish_assets()

    with st.container(border=True):
        _render_review_pack_support(review_pack)

    if not writing_assets:
        st.warning("当前没有可优化的写作资产。请先到写作工作台生成内容。")
        return

    paper_type, template_label, module_rows, missing_modules = get_project_module_status(writing_assets)
    completeness = get_export_completeness(writing_assets)

    with st.container(border=True):
        st.subheader("当前项目概况")
        st.markdown(f"**当前项目已生成模块数**：{len(writing_assets)}")
        st.markdown(f"**当前论文类型**：{template_label}")
        if topic_card and topic_card.title:
            st.markdown(f"**当前题目**：{topic_card.title}")

    with st.container(border=True):
        st.subheader("导出完整性检查")
        st.markdown(f"**关键模块总数**：{len(completeness['required_modules'])}")
        st.markdown(f"**已有关键模块**：{len(completeness['existing_modules'])}")
        st.markdown(f"**缺失关键模块**：{len(completeness['missing_modules'])}")
        st.markdown("**已有模块**")
        if completeness["existing_modules"]:
            for item in completeness["existing_modules"]:
                st.markdown(f"- {item}")
        else:
            st.caption("暂无已完成的关键模块。")
        st.markdown("**缺失模块**")
        if completeness["missing_modules"]:
            for item in completeness["missing_modules"]:
                st.markdown(f"- {item}")
            st.warning("当前导出内容不完整，但仍可继续导出当前版本。")
        else:
            st.success("关键模块已齐全，当前可作为完整版本导出。")

    with st.container(border=True):
        st.subheader("导出模块清单")
        st.caption("下列清单基于整个项目的 writing_assets 集合，而不是当前单模块。")
        for _, section_title, exists in module_rows:
            status = "已纳入导出" if exists else "缺失"
            st.markdown(f"- **{section_title}**｜{status}")
        extras = [asset for asset in writing_assets if asset.asset_type not in {asset_type for asset_type, _, _ in module_rows}]
        if extras:
            st.markdown("**附加模块**")
            for asset in extras:
                st.markdown(f"- {asset.title or asset.asset_type}")
        if missing_modules:
            st.warning(f"当前缺少模块：{'；'.join(missing_modules)}。继续导出时，缺失部分会以“暂无该部分内容”输出。")
        else:
            st.success("当前模板下的标准模块已齐全，可直接导出整篇项目内容。")

    active_polish = get_busy_action("polish_asset_action")
    if isinstance(active_polish, dict):
        target_asset_type = active_polish["asset_type"]
        action_id = active_polish["action_id"]
        target_asset = next((asset for asset in writing_assets if asset.asset_type == target_asset_type), None)
        if target_asset:
            try:
                settings = load_settings()
                with st.spinner(f"正在执行：{active_polish['label']}…"):
                    if action_id == "translate_abstract":
                        result_asset = translate_abstract_to_english(target_asset, settings)
                    elif action_id == "keywords_opt":
                        result_asset = optimize_keywords_from_abstract(target_asset, settings)
                    elif action_id == "academic_polish" and _is_abstract_asset(target_asset):
                        result_asset = polish_chinese_abstract(target_asset, settings, review_pack=review_pack)
                    else:
                        result_asset = optimize_writing_asset(
                            target_asset,
                            action_id,
                            settings,
                            review_pack=review_pack,
                        )
                polish_assets = _upsert_polish_asset(get_polish_assets(), result_asset)
                set_polish_assets(polish_assets)
                set_page_message("success", f"{active_polish['label']} 已完成。")
            except Exception as exc:
                set_page_message("error", f"{active_polish['label']} 失败：{exc}")
        clear_busy_action("polish_asset_action")
        st.rerun()

    active_export = get_busy_action("project_export")
    if isinstance(active_export, dict):
        try:
            settings = load_settings()
            with st.spinner("正在导出…"):
                if active_export["format"] == "markdown":
                    path = export_project_to_markdown(
                        topic_card,
                        literature_items,
                        writing_assets,
                        get_polish_assets(),
                        settings.outputs_dir,
                    )
                else:
                    path = export_project_to_docx(
                        topic_card,
                        literature_items,
                        writing_assets,
                        get_polish_assets(),
                        settings.outputs_dir,
                    )
            set_page_message("success", f"{active_export['label']}已导出：{path}")
        except Exception as exc:
            set_page_message("error", f"{active_export['label']}导出失败：{exc}")
        clear_busy_action("project_export")
        st.rerun()

    for index, asset in enumerate(writing_assets, start=1):
        with st.container(border=True):
            st.subheader(f"{index}. {asset.title or asset.asset_type}")
            st.caption(f"资产类型：{asset.asset_type}")

            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("**原始内容**")
                st.text_area(
                    f"original_{asset.asset_type}",
                    value=asset.content,
                    height=220,
                    disabled=True,
                )

            with col_right:
                st.markdown("**优化结果**")
                related_assets = _find_related_results(asset, get_polish_assets())
                if related_assets:
                    for result in related_assets:
                        st.markdown(f"**{result.title}**")
                        st.text_area(
                            f"result_{asset.asset_type}_{result.asset_type}",
                            value=result.content,
                            height=120,
                            disabled=True,
                        )
                else:
                    st.caption("暂无优化结果。")

            st.markdown("**优化动作**")
            action_cols = st.columns(5 if _is_abstract_asset(asset) else 3)
            current_polish = get_busy_action("polish_asset_action")
            current_asset_action = None
            if isinstance(current_polish, dict) and current_polish.get("asset_type") == asset.asset_type:
                current_asset_action = current_polish.get("action_id")

            action_specs = [
                ("academic_polish", "学术化优化"),
                ("compress", "精简压缩"),
                ("style_unify", "风格统一"),
            ]
            if _is_abstract_asset(asset):
                action_specs.extend(
                    [
                        ("translate_abstract", "英文摘要翻译"),
                        ("keywords_opt", "关键词优化"),
                    ]
                )

            for idx, (action_id, label) in enumerate(action_specs):
                with action_cols[idx]:
                    clicked = st.button(
                        f"正在执行：{label}…" if current_asset_action == action_id else label,
                        key=f"{asset.asset_type}_{action_id}",
                        use_container_width=True,
                        disabled=current_polish is not None,
                    )
                    if clicked and current_polish is None:
                        set_busy_action(
                            "polish_asset_action",
                            {"asset_type": asset.asset_type, "action_id": action_id, "label": label},
                        )
                        st.rerun()

    with st.container(border=True):
        st.subheader("导出")
        st.caption(f"当前将按“{template_label}”导出整篇项目内容，共纳入 {len(writing_assets)} 个已生成模块。")
        export_cols = st.columns(2)
        current_export = get_busy_action("project_export")
        with export_cols[0]:
            clicked_md = st.button(
                "正在导出…" if isinstance(current_export, dict) and current_export.get("format") == "markdown" else "导出 Markdown",
                use_container_width=True,
                disabled=current_export is not None,
            )
            if clicked_md and current_export is None:
                set_busy_action("project_export", {"format": "markdown", "label": "Markdown "})
                st.rerun()
        with export_cols[1]:
            clicked_docx = st.button(
                "正在导出…" if isinstance(current_export, dict) and current_export.get("format") == "docx" else "导出 DOCX",
                use_container_width=True,
                disabled=current_export is not None,
            )
            if clicked_docx and current_export is None:
                set_busy_action("project_export", {"format": "docx", "label": "DOCX "})
                st.rerun()
