import streamlit as st

from components.writing_panel import render_writing_assets
from config.settings import load_settings
from core.state import (
    clear_busy_action,
    get_busy_action,
    get_current_paper_type,
    get_literature_items,
    get_literature_review_pack,
    get_missing_writing_inputs,
    get_preferred_writing_sections,
    get_selected_research_gaps,
    get_selected_review_themes,
    get_selected_topic,
    get_selected_writing_angles,
    get_topic_card,
    get_writing_assets,
    get_writing_background_info,
    get_writing_build_plan,
    get_writing_context_notes,
    get_writing_evidence_notes,
    get_writing_existing_practice,
    get_writing_input_snapshot,
    get_writing_scope_limits,
    pop_page_message,
    set_busy_action,
    set_current_paper_type,
    set_page_message,
    set_preferred_writing_sections,
    set_selected_research_gaps,
    set_selected_review_themes,
    set_selected_writing_angles,
    set_writing_assets,
    set_writing_background_info,
    set_writing_build_plan,
    set_writing_context_notes,
    set_writing_evidence_notes,
    set_writing_existing_practice,
    set_writing_scope_limits,
    update_writing_asset,
)
from services.writing_service import (
    GOAL_ASSET_TYPES,
    PAPER_TYPE_GUIDANCE,
    PAPER_TYPE_LABELS,
    WRITING_GOAL_LABELS,
    build_star_prompt,
    generate_ai_build_suggestion,
    generate_writing_assets,
    get_goal_expected_content_points,
    get_goal_hold_points,
    get_goal_module_category,
    get_goal_module_summary,
    get_goal_write_now_reason,
    get_primary_asset_type_for_goal,
    get_rule_based_build_suggestion,
    get_writing_goals_for_paper_type,
    sort_writing_assets,
    upsert_writing_assets,
)


PAPER_TYPE_OPTIONS = [
    ("teaching_reform", "教改论文"),
    ("teaching_case", "教学案例研究"),
    ("general_research", "一般教育研究论文"),
]

STAGE_OPTIONS = [
    ("basis", "第 1 步：确定本次写作依据"),
    ("materials", "第 2 步：补充本次写作材料"),
    ("plan", "第 3 步：选择本次要写的论文部分"),
    ("draft", "第 4 步：生成并编辑这一部分"),
    ("progress", "第 5 步：查看整篇论文进度"),
]

STAGE_DESCRIPTIONS = {
    "basis": "先确认这次论文写作真正采用哪些文献依据和真实背景，避免后续生成内容空泛或跑偏。",
    "materials": "继续补充这次写作真正能用上的材料，让系统知道你手头已经有哪些做法、证据和研究边界。",
    "plan": "先看 AI 的搭建建议，再明确“这一次到底先写哪一部分”。AI 推荐只是辅助，最终由你决定。",
    "draft": "只围绕当前这一部分起草、编辑和保存，不一次性铺开整篇论文。",
    "progress": "从整篇论文视角检查哪些部分已完成、当前写到哪里、下一步先补什么。",
}


def _request_stage_change(stage_id: str) -> None:
    st.session_state["writing_workspace_stage_pending"] = stage_id


def _apply_pending_stage_change(valid_stage_ids: list[str]) -> None:
    pending_stage = st.session_state.pop("writing_workspace_stage_pending", None)
    if pending_stage in valid_stage_ids:
        st.session_state["writing_workspace_stage"] = pending_stage
    if st.session_state.get("writing_workspace_stage") not in valid_stage_ids:
        st.session_state["writing_workspace_stage"] = "basis"


def _paper_type_label(paper_type: str) -> str:
    return PAPER_TYPE_LABELS.get(paper_type, paper_type)


def _goal_label(goal_id: str) -> str:
    return WRITING_GOAL_LABELS.get(goal_id, goal_id)


def _goal_asset_types(goal_id: str) -> list[str]:
    return sorted(GOAL_ASSET_TYPES.get(goal_id, {get_primary_asset_type_for_goal(goal_id)}))


def _format_items(items: list[str], empty_text: str = "本次未选择") -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    return "；".join(cleaned) if cleaned else empty_text


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


def _render_step_header(current_stage: str) -> None:
    stage_map = dict(STAGE_OPTIONS)
    with st.container(border=True):
        st.markdown(f"**当前步骤：{stage_map[current_stage]}**")
        st.caption(STAGE_DESCRIPTIONS[current_stage])


def _render_step_actions(current_stage: str, *, next_target: str | None = None, next_label: str | None = None) -> None:
    stage_ids = [stage_id for stage_id, _ in STAGE_OPTIONS]
    current_index = stage_ids.index(current_stage)
    prev_col, next_col = st.columns(2)
    with prev_col:
        if current_index > 0:
            if st.button(
                f"上一步：{dict(STAGE_OPTIONS)[stage_ids[current_index - 1]]}",
                key=f"writing_stage_prev__{current_stage}",
                use_container_width=True,
            ):
                _request_stage_change(stage_ids[current_index - 1])
                st.rerun()
    with next_col:
        if next_target and next_label:
            if st.button(next_label, key=f"writing_stage_next__{current_stage}", use_container_width=True):
                _request_stage_change(next_target)
                st.rerun()


def _render_input_snapshot(snapshot: dict) -> None:
    with st.container(border=True):
        st.subheader("当前写作输入来源")
        st.markdown(f"**当前选题：** {snapshot['selected_topic'] or '未加载'}")
        st.markdown(f"**研究问题：** {snapshot['research_problem'] or '未加载'}")
        st.markdown(f"**文献速读条目数：** {snapshot['literature_count']}")
        st.markdown(f"**文献综述素材包：** {'已加载' if snapshot['review_pack_loaded'] else '未加载'}")


def _render_missing_inputs(missing_inputs: list[str], existing_assets: list) -> None:
    missing_labels = {
        "selected_topic": "已选题目",
        "topic_card": "研究问题卡",
        "literature_items": "文献速读结果",
        "literature_review_pack": "文献综述素材包",
    }
    with st.container(border=True):
        st.subheader("写作前置条件检查")
        st.warning("当前写作输入未齐全，暂不调用模型。请先回到前面步骤补齐基础材料。")
        for item in missing_inputs:
            st.markdown(f"- 缺少：{missing_labels.get(item, item)}")

    if existing_assets:
        with st.container(border=True):
            st.subheader("当前已生成草稿")
            render_writing_assets(existing_assets, key_prefix="writing_missing_input_overview")


def _first_pending_goal(paper_type: str, assets: list) -> str:
    completed_asset_types = {asset.asset_type for asset in assets}
    for goal_id in get_writing_goals_for_paper_type(paper_type):
        if not any(asset_type in completed_asset_types for asset_type in GOAL_ASSET_TYPES.get(goal_id, set())):
            return goal_id
    return get_writing_goals_for_paper_type(paper_type)[0]


def _render_paper_type_info(current_paper_type: str, has_existing_assets: bool) -> str:
    valid_paper_types = {paper_type_id for paper_type_id, _ in PAPER_TYPE_OPTIONS}
    paper_type = current_paper_type if current_paper_type in valid_paper_types else "general_research"
    if has_existing_assets:
        set_current_paper_type(paper_type)
        with st.container(border=True):
            st.subheader("当前写作基本信息")
            st.markdown(f"**当前论文类型：** {_paper_type_label(paper_type)}")
            st.caption(PAPER_TYPE_GUIDANCE.get(paper_type, ""))
            st.warning("当前已有写作模块，论文类型已锁定。如需切换，请先确认清空当前模块。")
        return paper_type

    labels = [label for _, label in PAPER_TYPE_OPTIONS]
    default_index = next(
        (index for index, (paper_type_id, _) in enumerate(PAPER_TYPE_OPTIONS) if paper_type_id == paper_type),
        0,
    )
    selected_label = st.selectbox("当前论文类型", labels, index=default_index, key="writing_v3_paper_type_select")
    paper_type = next(paper_type_id for paper_type_id, label in PAPER_TYPE_OPTIONS if label == selected_label)
    set_current_paper_type(paper_type)
    with st.container(border=True):
        st.subheader("当前写作基本信息")
        st.markdown(f"**当前论文类型：** {_paper_type_label(paper_type)}")
        st.caption(PAPER_TYPE_GUIDANCE.get(paper_type, ""))
    return paper_type


def _render_review_pack_overview(review_pack) -> None:
    with st.container(border=True):
        st.subheader("当前综述素材概览")
        st.markdown("**高频主题**")
        st.caption(_format_items(review_pack.high_frequency_themes, "暂无"))
        st.markdown("**研究不足**")
        st.caption(_format_items(review_pack.research_limitations, "暂无"))
        st.markdown("**可写切入点**")
        st.caption(_format_items(review_pack.suggested_angles, "暂无"))


def _render_basis_stage(review_pack, paper_type: str, selected_topic: str) -> None:
    with st.container(border=True):
        st.subheader("本次写作采用依据")
        st.caption("请先选择本次真正采用的高频主题、研究不足和可写切入点，再补充真实背景。系统会按这些依据生成当前论文部分。")

        selected_review_themes = st.multiselect(
            "选择本次采用的高频主题（来自文献工作台）",
            options=review_pack.high_frequency_themes,
            default=get_selected_review_themes(),
            key="writing_basis_review_themes",
            help="用于文献综述、提纲、理论背景。",
        )
        set_selected_review_themes(selected_review_themes)
        st.caption("用途：用于文献综述、提纲、理论背景。")

        selected_research_gaps = st.multiselect(
            "选择本次采用的研究不足（来自文献工作台）",
            options=review_pack.research_limitations,
            default=get_selected_research_gaps(),
            key="writing_basis_research_gaps",
            help="用于问题提出、研究空白、研究价值。",
        )
        set_selected_research_gaps(selected_research_gaps)
        st.caption("用途：用于问题提出、研究空白、研究价值。")

        selected_writing_angles = st.multiselect(
            "选择本次采用的可写切入点（来自文献工作台）",
            options=review_pack.suggested_angles,
            default=get_selected_writing_angles(),
            key="writing_basis_writing_angles",
            help="用于当前论文部分的方向、创新点、研究目标。",
        )
        set_selected_writing_angles(selected_writing_angles)
        st.caption("用途：用于当前论文部分的方向、创新点、研究目标。")

        writing_context_notes = st.text_area(
            "补充我的真实背景信息（用户补充）",
            value=get_writing_context_notes(),
            key="writing_basis_context_notes",
            height=140,
            help="用于增强文章真实性，贴合学校/课程/项目场景。",
        )
        set_writing_context_notes(writing_context_notes)
        st.caption("用途：用于增强文章真实性，贴合学校/课程/项目场景。")

    with st.container(border=True):
        st.subheader("本次生成将基于以下内容")
        st.markdown(f"**当前选题：** {selected_topic}")
        st.markdown(f"**当前论文类型：** {_paper_type_label(paper_type)}")
        st.markdown(f"**已选高频主题（来自文献工作台）：** {_format_items(get_selected_review_themes())}")
        st.markdown(f"**已选研究不足（来自文献工作台）：** {_format_items(get_selected_research_gaps())}")
        st.markdown(f"**已选可写切入点（来自文献工作台）：** {_format_items(get_selected_writing_angles())}")
        st.markdown(f"**用户补充背景说明（来自你自己）：** {get_writing_context_notes() or '本次未补充'}")


def _render_material_stage() -> None:
    with st.container(border=True):
        st.subheader("补充本次写作材料")
        st.caption("这一步只补充老师自己掌握的真实材料，不在这里决定先写哪一部分。")

        background = st.text_area(
            "真实研究/教学背景",
            value=get_writing_background_info(),
            key="writing_materials_background",
            height=120,
            help="例如学校类型、课程名称、对象、场景说明。",
        )
        set_writing_background_info(background)

        existing_practice = st.text_area(
            "已有做法或改革措施",
            value=get_writing_existing_practice(),
            key="writing_materials_practice",
            height=120,
            help="例如已实施了什么、准备怎么做、关键教学设计是什么。",
        )
        set_writing_existing_practice(existing_practice)

        evidence_notes = st.text_area(
            "已有证据或案例材料",
            value=get_writing_evidence_notes(),
            key="writing_materials_evidence",
            height=120,
            help="例如课堂记录、作业样例、学生反馈、阶段性成效。",
        )
        set_writing_evidence_notes(evidence_notes)

        scope_limits = st.text_area(
            "研究边界与限制",
            value=get_writing_scope_limits(),
            key="writing_materials_scope",
            height=100,
            help="例如时间范围、对象范围、数据限制、暂不展开的内容。",
        )
        set_writing_scope_limits(scope_limits)


def _render_plan_stage(
    paper_type: str,
    selected_topic: str,
    topic_card,
    literature_items,
    review_pack,
    existing_assets,
) -> str:
    with st.container(border=True):
        st.subheader("选择本次要写的论文部分")
        st.caption("这一步先看 AI 推荐，再明确“这一次到底先写哪一部分”。AI 推荐只是辅助，最终由你决定。")

        preferred_sections = st.multiselect(
            "如果你有明确想法，可先勾选你更想优先完成的论文部分（可多选）",
            options=get_writing_goals_for_paper_type(paper_type),
            default=get_preferred_writing_sections(),
            format_func=_goal_label,
            key=f"writing_plan_preferred_sections__{paper_type}",
        )
        set_preferred_writing_sections(preferred_sections)

        is_generating_plan = bool(get_busy_action("writing_build_plan_generation"))
        if st.button(
            "正在获取 AI 搭建建议…" if is_generating_plan else "获取 AI 搭建建议",
            key=f"writing_plan_generate__{paper_type}",
            use_container_width=True,
            disabled=is_generating_plan,
        ):
            set_busy_action("writing_build_plan_generation", {"paper_type": paper_type})
            st.rerun()

    build_plan = get_writing_build_plan()
    if build_plan:
        with st.container(border=True):
            st.subheader("AI 推荐搭建顺序")
            st.caption("这是更贴近当前论文类型写法的搭建建议。你可以采用，也可以自己决定先写哪一部分。")
            st.markdown(f"**当前判断：** {build_plan.get('readiness_summary') or '暂无'}")

            strengths = build_plan.get("material_strengths", [])
            gaps = build_plan.get("material_gaps", [])
            if strengths:
                st.markdown("**当前材料优势**")
                for item in strengths:
                    st.markdown(f"- {item}")
            if gaps:
                st.markdown("**当前仍偏弱的材料**")
                for item in gaps:
                    st.markdown(f"- {item}")

            st.markdown("**推荐优先搭建的论文部分**")
            recommended_sections = build_plan.get("recommended_sections", [])
            if recommended_sections:
                for index, goal_id in enumerate(recommended_sections, start=1):
                    with st.container(border=True):
                        st.markdown(f"**{index}. {_goal_label(goal_id)}**")
                        st.caption(get_goal_write_now_reason(goal_id))
                        for point in get_goal_expected_content_points(goal_id)[:3]:
                            st.markdown(f"- {point}")
                        if st.button(
                            f"采用并开始写：{_goal_label(goal_id)}",
                            key=f"writing_plan_adopt__{paper_type}__{goal_id}__{index}",
                            use_container_width=True,
                        ):
                            st.session_state[f"writing_current_goal__{paper_type}"] = goal_id
                            _request_stage_change("draft")
                            st.rerun()
            else:
                st.caption("暂无 AI 推荐部分。")

            deferred_sections = build_plan.get("deferred_sections", [])
            if deferred_sections:
                st.markdown("**建议暂后处理的部分**")
                for goal_id in deferred_sections:
                    st.markdown(f"- {_goal_label(goal_id)}：{get_goal_write_now_reason(goal_id)}")

            if build_plan.get("reasoning_notes"):
                st.markdown("**推荐理由**")
                st.write(build_plan["reasoning_notes"])
            if build_plan.get("recommended_sequence_note"):
                st.caption(build_plan["recommended_sequence_note"])

    current_goal_key = f"writing_current_goal__{paper_type}"
    goal_ids = get_writing_goals_for_paper_type(paper_type)
    if st.session_state.get(current_goal_key) not in goal_ids:
        st.session_state[current_goal_key] = _first_pending_goal(paper_type, existing_assets)

    with st.container(border=True):
        st.subheader("如果你自己决定，这次先写哪一部分")
        selected_goal = st.selectbox(
            "本次要写的论文部分",
            options=goal_ids,
            format_func=_goal_label,
            key=current_goal_key,
        )
        st.markdown(f"**当前拟写部分：** {_goal_label(selected_goal)}")
        st.markdown(f"**系统内部模块：** `{get_primary_asset_type_for_goal(selected_goal)}`")
        st.markdown(f"**这一部分属于：** `{get_goal_module_category(selected_goal)}`")
        st.caption(get_goal_module_summary(selected_goal))
        if st.button(
            f"确定本次先写：{_goal_label(selected_goal)}",
            key=f"writing_plan_confirm_goal__{paper_type}",
            use_container_width=True,
        ):
            _request_stage_change("draft")
            st.rerun()

    return st.session_state[current_goal_key]


def _build_progress_rows(paper_type: str, existing_assets: list) -> list[dict]:
    completed_asset_types = {asset.asset_type for asset in existing_assets}
    rows = []
    for goal_id in get_writing_goals_for_paper_type(paper_type):
        goal_asset_types = _goal_asset_types(goal_id)
        is_completed = any(asset_type in completed_asset_types for asset_type in goal_asset_types)
        rows.append(
            {
                "goal_id": goal_id,
                "label": _goal_label(goal_id),
                "asset_types": goal_asset_types,
                "completed": is_completed,
            }
        )
    return rows


def _render_progress_dashboard(existing_assets, paper_type: str, current_goal: str) -> None:
    rows = _build_progress_rows(paper_type, existing_assets)
    completed_rows = [row for row in rows if row["completed"]]
    pending_rows = [row for row in rows if not row["completed"]]
    next_row = pending_rows[0] if pending_rows else None

    with st.container(border=True):
        st.subheader("整篇论文进度面板")
        st.markdown(f"**当前论文类型：** {_paper_type_label(paper_type)}")
        st.markdown(f"**已完成部分：** {len(completed_rows)} / {len(rows)}")
        st.markdown(f"**当前正在写：** {_goal_label(current_goal)}")
        st.markdown(f"**下一步建议：** {next_row['label'] if next_row else '可转入整篇润色与导出'}")
        st.caption("这里是整篇论文视角，不是单个模块视角。你可以判断已经完成到哪里、下一步该接着写什么。")

    with st.container(border=True):
        st.subheader("当前论文标准顺序")
        for index, row in enumerate(rows, start=1):
            status = "已完成" if row["completed"] else ("当前正在写" if row["goal_id"] == current_goal else "未开始")
            st.markdown(
                f"{index}. **{row['label']}** ｜ 状态：`{status}` ｜ 模块：`{', '.join(row['asset_types'])}`"
            )


def _render_current_part_expectations(current_goal: str) -> None:
    with st.container(border=True):
        st.subheader("这一部分建议怎么写")
        st.markdown("**建议至少写出这些内容：**")
        for point in get_goal_expected_content_points(current_goal):
            st.markdown(f"- {point}")
        st.markdown("**这一阶段先不要急着展开：**")
        for point in get_goal_hold_points(current_goal):
            st.markdown(f"- {point}")


def _render_generation_task_sheet(
    paper_type: str,
    current_goal: str,
    selected_topic: str,
    prompt_preview: str,
) -> None:
    with st.container(border=True):
        st.subheader("本次生成任务单")
        st.markdown(f"**当前论文类型：** {_paper_type_label(paper_type)}")
        st.markdown(f"**本次要写的论文部分：** {_goal_label(current_goal)}")
        st.markdown(f"**系统内部模块：** `{get_primary_asset_type_for_goal(current_goal)}`")
        st.markdown(f"**输出类型：** `{get_goal_module_category(current_goal)}`")
        st.markdown(f"**本次生成的核心任务：** {get_goal_module_summary(current_goal)}")
        st.markdown(f"**为什么现在先写这一部分：** {get_goal_write_now_reason(current_goal)}")
        st.markdown(f"**当前选题：** {selected_topic}")
        st.markdown(f"**已选高频主题：** {_format_items(get_selected_review_themes())}")
        st.markdown(f"**已选研究不足：** {_format_items(get_selected_research_gaps())}")
        st.markdown(f"**已选可写切入点：** {_format_items(get_selected_writing_angles())}")
        st.markdown(f"**老师补充背景：** {get_writing_context_notes() or '本次未补充'}")
        st.markdown(f"**真实研究/教学背景：** {get_writing_background_info() or '未补充'}")
        if get_writing_existing_practice():
            st.markdown(f"**已有做法/措施：** {get_writing_existing_practice()}")
        if get_writing_evidence_notes():
            st.markdown(f"**已有证据/案例材料：** {get_writing_evidence_notes()}")
        if get_writing_scope_limits():
            st.markdown(f"**研究边界与限制：** {get_writing_scope_limits()}")

        with st.expander("查看系统原始生成指令（调试）", expanded=False):
            st.text_area(
                "系统原始生成指令",
                value=prompt_preview,
                height=260,
                disabled=True,
                key=f"writing_prompt_preview__{paper_type}__{current_goal}",
            )


def _render_current_part_editor(existing_assets, current_goal: str, paper_type: str) -> None:
    current_asset_types = _goal_asset_types(current_goal)
    matched_assets = [asset for asset in existing_assets if asset.asset_type in current_asset_types]
    if not matched_assets:
        st.info("当前这一部分还没有生成内容。请先点击上方按钮起草，再进入编辑。")
        return

    with st.container(border=True):
        st.subheader("编辑当前论文部分")
        for index, asset in enumerate(matched_assets, start=1):
            title = asset.title or _goal_label(current_goal)
            editor_key = f"writing_module_editor__{paper_type}__{asset.asset_type}__{index}"
            save_key = f"writing_module_save__{paper_type}__{asset.asset_type}__{index}"
            content = st.text_area(
                f"编辑：{title}",
                value=asset.content,
                height=260,
                key=editor_key,
            )
            is_saving = bool(get_busy_action("writing_module_save"))
            if st.button(
                "正在保存当前部分…" if is_saving else f"保存当前部分：{title}",
                key=save_key,
                use_container_width=True,
                disabled=is_saving,
            ):
                set_busy_action("writing_module_save", {"asset_type": asset.asset_type, "content": content, "title": title})
                st.rerun()


def _handle_busy_actions(
    *,
    selected_topic: str,
    topic_card,
    literature_items,
    review_pack,
    paper_type: str,
) -> None:
    existing_assets = sort_writing_assets(get_writing_assets(), paper_type)

    save_payload = get_busy_action("writing_module_save")
    if isinstance(save_payload, dict):
        if update_writing_asset(save_payload["asset_type"], save_payload["content"], save_payload.get("title")):
            set_page_message("success", f"已保存当前部分：{save_payload.get('title') or save_payload['asset_type']}")
            _request_stage_change("progress")
        else:
            set_page_message("error", "保存失败：未找到对应模块。")
        clear_busy_action("writing_module_save")
        st.rerun()

    plan_payload = get_busy_action("writing_build_plan_generation")
    if isinstance(plan_payload, dict):
        try:
            settings = load_settings()
            suggestion = generate_ai_build_suggestion(
                selected_topic=selected_topic,
                topic_card=topic_card,
                literature_items=literature_items,
                review_pack=review_pack,
                paper_type=paper_type,
                existing_assets=existing_assets,
                settings=settings,
                selected_review_themes=get_selected_review_themes(),
                selected_research_gaps=get_selected_research_gaps(),
                selected_writing_angles=get_selected_writing_angles(),
                writing_context_notes=get_writing_context_notes(),
                writing_background_info=get_writing_background_info(),
                writing_existing_practice=get_writing_existing_practice(),
                writing_evidence_notes=get_writing_evidence_notes(),
                writing_scope_limits=get_writing_scope_limits(),
                preferred_writing_sections=get_preferred_writing_sections(),
            )
            set_writing_build_plan(suggestion)
            set_page_message("success", "已生成 AI 搭建建议。现在请选择这次先写哪一部分。")
        except Exception:
            fallback = get_rule_based_build_suggestion(
                paper_type=paper_type,
                preferred_writing_sections=get_preferred_writing_sections(),
                existing_assets=existing_assets,
            )
            set_writing_build_plan(fallback)
            set_page_message("warning", "AI 建议获取失败，已切换为规则建议。你仍可继续选择本次先写的部分。")
        finally:
            clear_busy_action("writing_build_plan_generation")
        st.rerun()

    draft_payload = get_busy_action("writing_goal_generation")
    if isinstance(draft_payload, dict):
        current_goal = str(draft_payload.get("goal") or _first_pending_goal(paper_type, existing_assets))
        try:
            settings = load_settings()
            new_assets = generate_writing_assets(
                selected_topic=selected_topic,
                topic_card=topic_card,
                literature_items=literature_items,
                review_pack=review_pack,
                selected_review_themes=get_selected_review_themes(),
                selected_research_gaps=get_selected_research_gaps(),
                selected_writing_angles=get_selected_writing_angles(),
                writing_context_notes=get_writing_context_notes(),
                settings=settings,
                writing_goal=current_goal,
                paper_type=paper_type,
                writing_background_info=get_writing_background_info(),
                writing_existing_practice=get_writing_existing_practice(),
                writing_evidence_notes=get_writing_evidence_notes(),
                writing_scope_limits=get_writing_scope_limits(),
                preferred_writing_sections=get_preferred_writing_sections(),
            )
            merged_assets = upsert_writing_assets(existing_assets, new_assets, paper_type)
            set_writing_assets(merged_assets)
            set_page_message("success", f"已生成并更新：{_goal_label(current_goal)}")
        except Exception as exc:
            set_page_message("error", f"生成当前论文部分失败：{exc}")
        finally:
            clear_busy_action("writing_goal_generation")
        st.rerun()


def render_writing_workspace_page() -> None:
    selected_topic = get_selected_topic()
    topic_card = get_topic_card()
    literature_items = get_literature_items()
    review_pack = get_literature_review_pack()
    input_snapshot = get_writing_input_snapshot()

    current_paper_type = get_current_paper_type() or "general_research"
    existing_assets = sort_writing_assets(get_writing_assets(), current_paper_type or "general_research")

    st.title("写作工作台")
    st.info("这里不是一次性生成整篇论文，而是按真实论文写作顺序，一部分一部分往整篇草稿里搭建。")
    _render_flash_message()
    _render_input_snapshot(input_snapshot)

    missing_inputs = get_missing_writing_inputs()
    if missing_inputs:
        _render_missing_inputs(missing_inputs, existing_assets)
        return

    paper_type = _render_paper_type_info(current_paper_type, bool(existing_assets))
    existing_assets = sort_writing_assets(get_writing_assets(), paper_type)
    _handle_busy_actions(
        selected_topic=selected_topic,
        topic_card=topic_card,
        literature_items=literature_items,
        review_pack=review_pack,
        paper_type=paper_type,
    )

    stage_ids = [stage_id for stage_id, _ in STAGE_OPTIONS]
    _apply_pending_stage_change(stage_ids)
    current_stage = st.radio(
        "步骤切换",
        options=stage_ids,
        format_func=lambda stage_id: dict(STAGE_OPTIONS)[stage_id],
        key="writing_workspace_stage",
        horizontal=True,
    )
    _render_step_header(current_stage)

    current_goal_key = f"writing_current_goal__{paper_type}"
    goal_ids = get_writing_goals_for_paper_type(paper_type)
    if st.session_state.get(current_goal_key) not in goal_ids:
        st.session_state[current_goal_key] = _first_pending_goal(paper_type, existing_assets)

    if current_stage == "basis":
        _render_review_pack_overview(review_pack)
        _render_basis_stage(review_pack, paper_type, selected_topic)
        _render_step_actions(current_stage, next_target="materials", next_label="下一步：补充写作材料")
        return

    if current_stage == "materials":
        _render_material_stage()
        _render_step_actions(current_stage, next_target="plan", next_label="下一步：选择本次要写的论文部分")
        return

    if current_stage == "plan":
        current_goal = _render_plan_stage(
            paper_type=paper_type,
            selected_topic=selected_topic,
            topic_card=topic_card,
            literature_items=literature_items,
            review_pack=review_pack,
            existing_assets=existing_assets,
        )
        _render_step_actions(current_stage, next_target="draft", next_label=f"下一步：开始写 {_goal_label(current_goal)}")
        return

    current_goal = st.session_state.get(current_goal_key, goal_ids[0])

    if current_stage == "draft":
        prompt_preview = build_star_prompt(
            selected_topic=selected_topic,
            topic_card=topic_card,
            literature_items=literature_items,
            review_pack=review_pack,
            selected_review_themes=get_selected_review_themes(),
            selected_research_gaps=get_selected_research_gaps(),
            selected_writing_angles=get_selected_writing_angles(),
            writing_context_notes=get_writing_context_notes(),
            writing_background_info=get_writing_background_info(),
            writing_existing_practice=get_writing_existing_practice(),
            writing_evidence_notes=get_writing_evidence_notes(),
            writing_scope_limits=get_writing_scope_limits(),
            preferred_writing_sections=get_preferred_writing_sections(),
            writing_goal=current_goal,
            paper_type=paper_type,
        )

        with st.container(border=True):
            st.subheader("当前正在搭建的论文部分")
            st.markdown(f"**当前论文类型：** {_paper_type_label(paper_type)}")
            st.markdown(f"**本次要写的论文部分：** {_goal_label(current_goal)}")
            st.markdown(f"**系统内部模块：** `{get_primary_asset_type_for_goal(current_goal)}`")
            st.markdown(f"**这一部分属于：** `{get_goal_module_category(current_goal)}`")
            st.caption(get_goal_module_summary(current_goal))
            st.info(f"为什么现在先写这一部分：{get_goal_write_now_reason(current_goal)}")

        _render_current_part_expectations(current_goal)
        _render_generation_task_sheet(paper_type, current_goal, selected_topic, prompt_preview)

        is_generating = bool(get_busy_action("writing_goal_generation"))
        if st.button(
            "正在生成当前论文部分…" if is_generating else f"生成：{_goal_label(current_goal)}",
            key=f"writing_generate__{paper_type}__{current_goal}",
            use_container_width=True,
            disabled=is_generating,
        ):
            set_busy_action("writing_goal_generation", {"goal": current_goal})
            st.rerun()

        _render_current_part_editor(sort_writing_assets(get_writing_assets(), paper_type), current_goal, paper_type)
        left_col, right_col = st.columns(2)
        with left_col:
            if st.button("上一步：回看搭建建议", key=f"writing_draft_back_plan__{paper_type}", use_container_width=True):
                _request_stage_change("plan")
                st.rerun()
        with right_col:
            if st.button("下一步：查看整篇论文进度", key=f"writing_draft_to_progress__{paper_type}", use_container_width=True):
                _request_stage_change("progress")
                st.rerun()
        return

    _render_progress_dashboard(sort_writing_assets(get_writing_assets(), paper_type), paper_type, current_goal)
    with st.container(border=True):
        st.subheader("已生成草稿总览")
        render_writing_assets(sort_writing_assets(get_writing_assets(), paper_type), key_prefix=f"writing_progress_overview__{paper_type}")

    left_col, right_col = st.columns(2)
    with left_col:
        if st.button("继续选择下一部分", key=f"writing_progress_continue__{paper_type}", use_container_width=True):
            _request_stage_change("plan")
            st.rerun()
    with right_col:
        if st.button("下一步：去润色与导出", key=f"writing_progress_polish__{paper_type}", use_container_width=True):
            st.session_state.current_page = "润色与导出"
            st.rerun()
