import streamlit as st

from components.topic_card import render_topic_card
from config.settings import load_settings
from core.state import (
    clear_busy_action,
    get_busy_action,
    get_selected_topic,
    get_topic_card,
    pop_page_message,
    set_busy_action,
    set_page_message,
    set_selected_topic,
    set_topic_card,
)
from services.topic_service import generate_topic_card


TOPIC_EXAMPLES = {
    "中小学教研论文示例": {
        "research_object": "初中语文教师与七年级学生",
        "school_stage": "中小学",
        "subject": "语文",
        "research_problem": "AI支持下，如何优化初中语文阅读教学中的单元作业设计与课堂评价方式？",
        "research_context": "围绕七年级阅读单元教学，学校正在推进课堂提质与作业设计优化，教师希望形成可写成论文的改进路径。",
        "existing_materials": "已有单元教学设计、学生作业样本、课堂观察记录、阶段评价表。",
        "paper_type": "教改论文",
    },
    "高校科研论文示例": {
        "research_object": "本科教师与本科生",
        "school_stage": "本科高校",
        "subject": "教育技术 / 人才培养 / 课程建设",
        "research_problem": "AIGC背景下，如何重构本科课程体系并提升教师数字素养与学生高阶学习能力？",
        "research_context": "某本科院校正在推进智慧课程建设与专业改革，希望围绕课程体系重构形成一篇规范科研论文。",
        "existing_materials": "已有课程改革方案、教师培训记录、学生学习反馈、课程运行数据。",
        "paper_type": "一般教育研究论文",
    },
    "教学案例研究示例": {
        "research_object": "某门课程教师与学生",
        "school_stage": "本科高校",
        "subject": "市场营销 / 教育技术 / 专业核心课程",
        "research_problem": "在项目式教学中引入 AIGC 支持后，教学干预如何实施、效果如何、能得到哪些教学启示？",
        "research_context": "围绕一门具体课程中的某次教学改革实践，聚焦一次完整教学干预案例及其结果分析。",
        "existing_materials": "已有课程项目任务书、课堂录像、学生作品、访谈记录、教师反思日志。",
        "paper_type": "教学案例研究",
    },
}


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


def render_ai_mentor_page() -> None:
    _render_flash_message()

    st.markdown('<div class="trw-section-title">选题助手</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="trw-section-desc">先按真实论文写作起步逻辑填写研究对象、问题与场景，再生成 TopicCard，并从候选题目中确定一个正式研究题目。</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.subheader("示例填入")
        example_cols = st.columns(3)
        for idx, (label, payload) in enumerate(TOPIC_EXAMPLES.items()):
            with example_cols[idx]:
                if st.button(label, key=f"example_{idx}", use_container_width=True):
                    st.session_state.topic_research_object = payload["research_object"]
                    st.session_state.topic_school_stage = payload["school_stage"]
                    st.session_state.topic_subject = payload["subject"]
                    st.session_state.topic_research_problem = payload["research_problem"]
                    st.session_state.topic_research_context = payload["research_context"]
                    st.session_state.topic_existing_materials = payload["existing_materials"]
                    st.session_state.topic_paper_type = payload["paper_type"]
                    st.rerun()

    is_generating = bool(get_busy_action("topic_card_generation"))

    st.markdown('<div class="trw-compact-card">', unsafe_allow_html=True)
    with st.form("topic_card_form", clear_on_submit=False):
        st.subheader("输入区")
        research_object = st.text_input(
            "研究对象与学段",
            key="topic_research_object",
            placeholder="例如：高中一年级学生 / 中职护理专业学生 / 小学语文教师",
        )
        st.caption("示例句式：我准备研究“某类学生/教师/课程对象”在某一教学任务中的变化或问题。")

        school_stage_options = ["中小学", "职业院校", "本科高校"]
        default_stage = st.session_state.get("topic_school_stage", "中小学")
        default_stage_index = school_stage_options.index(default_stage) if default_stage in school_stage_options else 0
        school_stage = st.selectbox("学段", school_stage_options, index=default_stage_index, key="topic_school_stage")

        subject = st.text_input(
            "所属学科或专业方向",
            key="topic_subject",
            placeholder="例如：语文 / 数学 / 教育技术 / 护理专业 / 学前教育",
        )
        st.caption("示例句式：我的研究主要发生在“某学科/某专业课程/某课程群”中。")

        teaching_problem = st.text_area(
            "核心研究问题",
            key="topic_research_problem",
            placeholder="例如：如何提升学生课堂参与度？如何优化某课程教学路径？",
            height=140,
        )
        st.caption("示例句式：我最想解决的问题是“如何通过某种做法改善某类教学问题”。")

        research_context = st.text_area(
            "具体教学或实践场景",
            key="topic_research_context",
            placeholder="例如：某年级、某课程、某实训环节、某校本改革场景。",
            height=120,
        )
        st.caption("示例句式：研究准备发生在“某学校/某课程/某教学单元/某实践项目”中。")

        existing_materials = st.text_area(
            "已有材料或案例基础（选填）",
            key="topic_existing_materials",
            placeholder="例如：已有课堂录像、学生作业、案例记录、教学设计、问卷、访谈材料。",
            height=100,
        )
        st.caption("示例句式：我手头已经有“某些教学材料、案例素材或过程记录”，可作为研究基础。")

        paper_type_options = ["教改论文", "教学案例研究", "一般教育研究论文"]
        default_paper_type = st.session_state.get("topic_paper_type", "一般教育研究论文")
        default_paper_type_index = (
            paper_type_options.index(default_paper_type) if default_paper_type in paper_type_options else 2
        )
        paper_type = st.selectbox("论文类型", paper_type_options, index=default_paper_type_index, key="topic_paper_type")
        st.caption("高频场景包括：中小学教研论文、高校科研论文、教学案例研究。")

        submitted = st.form_submit_button(
            "正在生成选题卡…" if is_generating else "生成选题卡",
            use_container_width=True,
            disabled=is_generating,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted and not is_generating:
        set_busy_action("topic_card_generation", True)
        st.rerun()

    if is_generating:
        if not research_object.strip() or not subject.strip() or not teaching_problem.strip() or not research_context.strip():
            clear_busy_action("topic_card_generation")
            set_page_message("warning", "请完整填写研究对象、学科或专业方向、核心研究问题和具体教学或实践场景。")
            st.rerun()

        try:
            settings = load_settings()
            with st.spinner("正在生成选题卡…"):
                topic_card = generate_topic_card(
                    research_object=research_object,
                    school_stage=school_stage,
                    subject=subject,
                    teaching_problem=teaching_problem,
                    research_context=research_context,
                    existing_materials=existing_materials,
                    paper_type=paper_type,
                    settings=settings,
                )
            set_topic_card(topic_card)
            set_page_message("success", "选题卡已生成并写入当前会话。")
        except Exception as exc:
            set_page_message("error", f"生成选题卡失败：{exc}")
        finally:
            clear_busy_action("topic_card_generation")
        st.rerun()

    current_topic_card = get_topic_card()
    selected_topic = get_selected_topic()

    with st.container(border=True):
        st.subheader("最近一次 TopicCard")
        render_topic_card(current_topic_card)

        if not current_topic_card:
            return

        candidates = current_topic_card.topic_candidates or ([current_topic_card.title] if current_topic_card.title else [])

        st.markdown("**候选题目**")
        if candidates:
            default_index = candidates.index(selected_topic) if selected_topic in candidates else 0
            chosen = st.radio("请选择一个候选题目", candidates, index=default_index, key="topic_candidate_choice")
            if st.button("保存候选题目", use_container_width=True):
                set_selected_topic(chosen)
                st.success(f"已保存选题：{chosen}")
        else:
            st.caption("暂无候选题目。")

        custom_topic = st.text_input(
            "或手动输入自己的题目",
            value=selected_topic if selected_topic and selected_topic not in candidates else "",
        )
        if st.button("保存自定义题目", use_container_width=True):
            if custom_topic.strip():
                set_selected_topic(custom_topic)
                st.success(f"已保存自定义题目：{custom_topic.strip()}")
            else:
                st.warning("请输入自定义题目后再保存。")

        final_selected = get_selected_topic()
        if final_selected:
            st.markdown("**当前已选题目**")
            st.write(final_selected)

        if current_topic_card.research_questions:
            st.markdown("**研究问题**")
            for item in current_topic_card.research_questions:
                st.markdown(f"- {item}")

        if current_topic_card.recommended_methods:
            st.markdown("**推荐方法**")
            for item in current_topic_card.recommended_methods:
                st.markdown(f"- {item}")

        if current_topic_card.mentor_analysis:
            st.markdown("**导师分析**")
            st.write(current_topic_card.mentor_analysis)

    st.markdown("---")
    if st.button("下一步：去文献工作台", use_container_width=True):
        st.session_state.current_page = "文献工作台"
        st.rerun()
