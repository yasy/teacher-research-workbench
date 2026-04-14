import streamlit as st

from core.schemas import WritingAsset


def render_writing_assets(assets: list[WritingAsset], key_prefix: str = "writing_panel") -> None:
    if not assets:
        st.caption("暂无写作资产。")
        return

    for index, asset in enumerate(assets, start=1):
        title = asset.title or asset.asset_type
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(f"模块类型：{asset.asset_type}")
            st.text_area(
                "内容",
                value=asset.content,
                height=180,
                disabled=True,
                key=f"{key_prefix}__{asset.asset_type}__{title}__{index}__readonly",
            )
