import streamlit as st


WORKFLOW_PAGES = [
    "选题助手",
    "文献工作台",
    "写作工作台",
    "润色与导出",
]
SETTINGS_PAGE = "设置"
ALL_PAGE_NAMES = WORKFLOW_PAGES + [SETTINGS_PAGE]


def _workflow_button(container, label: str, current_page: str) -> None:
    button_type = "primary" if current_page == label else "secondary"
    if container.button(
        label,
        key=f"workflow_{label}",
        use_container_width=False,
        type=button_type,
    ):
        st.session_state.current_page = label


def _settings_button(container, current_page: str) -> None:
    is_active = current_page == SETTINGS_PAGE
    left, center, right = container.columns([0.1, 0.22, 0.68])
    with center:
        if st.button(
            "⚙ 设置" if is_active else "⚙",
            key="settings_entry_button",
            use_container_width=False,
            type="primary" if is_active else "secondary",
            help="打开设置",
        ):
            st.session_state.current_page = SETTINGS_PAGE


def render_sidebar(container, current_page: str) -> str:
    with container:
        outer = st.container(border=True)
        with outer:
            st.markdown(
                """
                <style>
                div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:has(.trw-nav-root) {
                    border-radius: 14px !important;
                    border: 1px solid #dbe5f1 !important;
                    background: #eef4fb !important;
                    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.035) !important;
                }

                .trw-nav-root {
                    padding: 0.12rem 0.08rem 0.08rem 0.08rem;
                }

                .trw-nav-title {
                    margin: 0 0 0.45rem 0;
                    font-size: 1rem;
                    font-weight: 800;
                    color: #0f172a;
                    line-height: 1.25;
                }

                .trw-nav-note {
                    margin: 0.45rem 0 0 0;
                    font-size: 0.8rem;
                    line-height: 1.45;
                    color: #5b6b7f;
                }

                .trw-settings-section {
                    margin-top: 0.7rem;
                    padding-top: 0.65rem;
                    border-top: 1px solid #d7e1ee;
                }

                .trw-settings-label {
                    margin: 0 0 0.35rem 0;
                    font-size: 0.78rem;
                    color: #6b7280;
                }

            .trw-nav-root div[data-testid="stButton"] {
                margin-bottom: 0.36rem !important;
                display: flex !important;
                justify-content: flex-start !important;
            }

            .trw-nav-root div[data-testid="stButton"] > button {
                width: 178px !important;
                min-height: 38px !important;
                border-radius: 9px !important;
                padding: 0.38rem 0.8rem !important;
                font-size: 0.93rem !important;
                font-weight: 600 !important;
                line-height: 1.2 !important;
                text-align: left !important;
                justify-content: flex-start !important;
                box-shadow: none !important;
            }

                .trw-settings-section div[data-testid="stButton"] > button {
                    min-width: 2.5rem !important;
                    min-height: 34px !important;
                    padding: 0.38rem 0.65rem !important;
                    width: auto !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="trw-nav-root">', unsafe_allow_html=True)
            st.markdown('<div class="trw-nav-title">工作流导航</div>', unsafe_allow_html=True)

            for page in WORKFLOW_PAGES:
                _workflow_button(st, page, current_page)

            st.markdown(
                '<div class="trw-nav-note">建议按“选题 → 文献 → 写作 → 润色与导出”的顺序完成。</div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="trw-settings-section">', unsafe_allow_html=True)
            st.markdown('<div class="trw-settings-label">系统区</div>', unsafe_allow_html=True)
            _settings_button(st, current_page)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    return st.session_state.current_page
