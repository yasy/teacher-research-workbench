import streamlit as st


def render_export_panel() -> str | None:
    col1, col2 = st.columns(2)
    selected = None

    with col1:
        st.button("导出 Markdown", disabled=True, use_container_width=True)
    with col2:
        st.button("导出 DOCX", disabled=True, use_container_width=True)

    st.caption("Phase 8 将在这里接入 Markdown / DOCX 导出。")
    return selected
