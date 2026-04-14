import streamlit as st

from core.schemas import TopicCard


def render_topic_card(topic_card: TopicCard | None) -> None:
    if topic_card is None:
        st.caption("暂无选题卡。Phase 3 将在这里展示 TopicCard。")
        return

    st.markdown(f"**题目**：{topic_card.title}")
    st.markdown(f"**研究问题**：{topic_card.research_problem}")
    st.markdown(f"**研究对象**：{topic_card.target_population}")
    st.markdown(f"**研究场景**：{topic_card.context}")
    st.markdown(f"**关键词**：{', '.join(topic_card.keywords)}")
