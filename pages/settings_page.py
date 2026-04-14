import streamlit as st

from components.model_selector import render_model_selector
from config.settings import load_settings, save_settings
from core.state import (
    export_project_state,
    get_current_project_meta,
    get_selected_topic,
    get_topic_card,
    import_project_state,
    set_current_project_meta,
)
from storage.project_store import list_projects, load_project, save_project


def render_settings_page() -> None:
    st.title("设置")
    st.info("在这里配置模型接口、保存当前项目，或重新打开已有项目。")
    settings = load_settings()
    config_values = render_model_selector(settings)

    with st.container(border=True):
        st.subheader("保存模型配置")
        st.caption("保存后会立即写入 .env，并在当前运行进程中生效。建议先确认 Provider、Model 和 API Key 填写正确。")
        if st.button("保存模型与接口配置", use_container_width=True, key="save_runtime_settings"):
            try:
                if not config_values["provider"]:
                    raise ValueError("请先选择模型服务商。")
                if not config_values["model"]:
                    raise ValueError("请先填写模型名称。")
                if not config_values["api_key"]:
                    raise ValueError("请先填写 API Key。")
                saved_settings = save_settings(**config_values)
                st.success(
                    "模型配置已保存。"
                    f" 当前服务商：{saved_settings.provider}；当前模型：{saved_settings.model}"
                )
            except Exception as exc:
                st.error(f"保存模型配置失败：{exc}")

    topic_card = get_topic_card()
    default_project_name = get_selected_topic() or (topic_card.title if topic_card else "") or "未命名项目"
    current_project_meta = get_current_project_meta()

    with st.container(border=True):
        st.subheader("项目管理")
        if current_project_meta.get("saved_at"):
            st.caption(
                f"当前项目：{current_project_meta.get('project_name') or '未命名项目'}｜"
                f"上次保存时间：{current_project_meta.get('saved_at')}"
            )
        project_name = st.text_input("项目名称", value=default_project_name, key="project_name_input")
        if st.button("保存当前项目", use_container_width=True):
            try:
                project_info = save_project(project_name, export_project_state())
                set_current_project_meta(
                    project_name=project_info["project_name"],
                    project_path=project_info["path"],
                    saved_at=project_info["saved_at"],
                )
                st.success(f"项目已保存：{project_info['path']}")
            except Exception as exc:
                st.error(f"保存项目失败：{exc}")

        projects = list_projects()
        if not projects:
            st.caption("暂无历史项目。保存一次后会在这里显示。")
        else:
            options = [f"{item['project_name']} | {item['saved_at']}" for item in projects]
            selected_label = st.selectbox("最近项目", options, index=0)
            selected_project = projects[options.index(selected_label)]
            if st.button("加载选中项目", use_container_width=True):
                try:
                    project_info = load_project(selected_project["path"])
                    import_project_state(project_info["state"])
                    set_current_project_meta(
                        project_name=project_info["project_name"],
                        project_path=project_info["path"],
                        saved_at=project_info["saved_at"],
                    )
                    st.success(f"已加载项目：{selected_project['project_name']}")
                except Exception as exc:
                    st.error(f"加载项目失败：{exc}")
