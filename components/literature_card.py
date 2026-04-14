import streamlit as st

from core.schemas import LiteratureItem


def render_literature_card(item: LiteratureItem | None) -> None:
    if item is None:
        st.caption("暂无文献卡片。Phase 4 将在这里展示 LiteratureItem。")
        return

    st.markdown(f"**文件**：{item.file_name}")
    st.markdown(f"**标题**：{item.title}")
    st.markdown(f"**作者**：{', '.join(item.authors)}")
    st.markdown(f"**年份**：{item.year}")
    st.markdown(f"**方法**：{item.method}")
    st.markdown(f"**结论**：{item.findings}")
