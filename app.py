import streamlit as st

from components.sidebar import ALL_PAGE_NAMES, render_sidebar
from config.logging_config import setup_logging
from core.state import init_app_state
from pages.ai_mentor_page import render_ai_mentor_page
from pages.literature_workspace_page import render_literature_workspace_page
from pages.polish_export_page import render_polish_export_page
from pages.settings_page import render_settings_page
from pages.writing_workspace_page import render_writing_workspace_page


def apply_app_shell() -> None:
    st.markdown(
        """
        <style>
        #MainMenu { visibility: hidden; }
        header { visibility: hidden; }
        footer { visibility: hidden; }
        [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        [data-testid="stSidebarNavSeparator"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        button[title="Close sidebar"],
        button[title="Open sidebar"],
        [aria-label="Close sidebar"],
        [aria-label="Open sidebar"] {
            display: none !important;
        }

        .stApp {
            background: #f4f7fb;
            color: #1f2937;
        }

        .main .block-container {
            max-width: 1280px !important;
            padding-top: 0.05rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 1rem !important;
        }

        div[data-testid="column"] {
            padding-top: 0 !important;
        }

        .trw-global-header {
            width: 100%;
            margin: 0 0 0.35rem 0;
            background: linear-gradient(90deg, #edf4ff 0%, #f7faff 65%, #ffffff 100%);
            border: 1px solid #d8e3f2;
            border-radius: 13px;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.045);
        }

        .trw-global-header__inner {
            padding: 0.6rem 0.95rem 0.52rem 0.95rem;
        }

        .trw-global-header__title {
            margin: 0;
            color: #0f172a;
            font-size: 32px;
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: 0.01em;
        }

        .trw-global-header__subtitle {
            margin-top: 0.1rem;
            color: #526174;
            font-size: 14px;
            line-height: 1.35;
        }

        .trw-main-panel {
            background: #ffffff;
            border: 1px solid #e3e8ef;
            border-radius: 13px;
            padding: 0.62rem 0.95rem 0.9rem 0.95rem;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.035);
        }

        .trw-main-panel h1 {
            font-size: 21px !important;
            line-height: 1.25 !important;
            margin-top: 0 !important;
            margin-bottom: 0.55rem !important;
            font-weight: 700 !important;
        }

        .trw-section-title {
            font-size: 19px !important;
            line-height: 1.2 !important;
            margin: 0 0 0.28rem 0 !important;
            font-weight: 700 !important;
            color: #0f172a;
        }

        .trw-section-desc {
            margin: 0 0 0.55rem 0 !important;
            font-size: 0.9rem !important;
            line-height: 1.45 !important;
            color: #5b6b7f;
        }

        .trw-main-panel h2,
        .trw-main-panel h3 {
            font-size: 18px !important;
            line-height: 1.35 !important;
            margin-top: 0.1rem !important;
            margin-bottom: 0.46rem !important;
            font-weight: 700 !important;
        }

        .trw-main-panel p,
        .trw-main-panel li,
        .trw-main-panel label,
        .trw-main-panel [data-testid="stMarkdownContainer"] {
            font-size: 15px;
            line-height: 1.56;
        }

        .trw-main-panel [data-testid="stVerticalBlock"] > div {
            margin-top: 0.28rem;
            margin-bottom: 0.28rem;
        }

        .trw-main-panel [data-testid="stVerticalBlock"] > div:has(> [data-testid="stAlert"]),
        .trw-main-panel [data-testid="stVerticalBlock"] > div:has(> div[data-testid="stForm"]),
        .trw-main-panel [data-testid="stVerticalBlock"] > div:has(> [data-testid="stMarkdownContainer"]),
        .trw-main-panel [data-testid="stVerticalBlock"] > div:has(> div[data-testid="stVerticalBlockBorderWrapper"]) {
            margin-top: 0.45rem;
            margin-bottom: 0.45rem;
        }

        .trw-main-panel [data-testid="stTextInput"] input,
        .trw-main-panel [data-testid="stNumberInput"] input,
        .trw-main-panel [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        .trw-main-panel [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
            min-height: 44px !important;
            border-radius: 10px !important;
            border-color: #d7deea !important;
            background: #ffffff !important;
            font-size: 0.95rem !important;
        }

        .trw-main-panel [data-testid="stTextArea"] textarea {
            min-height: 120px !important;
            border-radius: 10px !important;
            border-color: #d7deea !important;
            background: #ffffff !important;
            font-size: 0.95rem !important;
            line-height: 1.55 !important;
            padding: 0.75rem 0.9rem !important;
        }

        .trw-main-panel label {
            margin-bottom: 0.28rem !important;
            font-size: 14px !important;
            color: #334155 !important;
        }

        .trw-main-panel .stSelectbox,
        .trw-main-panel .stTextInput,
        .trw-main-panel .stTextArea,
        .trw-main-panel .stFileUploader,
        .trw-main-panel .stRadio,
        .trw-main-panel .stMultiSelect {
            margin-bottom: 0.12rem !important;
        }

        .trw-main-panel [data-testid="stCaptionContainer"] {
            font-size: 13px !important;
            color: #64748b !important;
            line-height: 1.45 !important;
        }

        .trw-main-panel .stButton > button,
        .trw-main-panel button[kind="primary"],
        .trw-main-panel button[kind="secondary"] {
            min-height: 44px !important;
            border-radius: 10px !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            padding: 0.45rem 0.95rem !important;
        }

        .trw-main-panel [data-testid="stAlert"] {
            border-radius: 12px !important;
            padding-top: 0.6rem !important;
            padding-bottom: 0.6rem !important;
        }

        .trw-main-panel div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 13px !important;
            border-color: #e4e9f1 !important;
            background: #fbfcfe !important;
            padding: 0.62rem 0.78rem 0.72rem 0.78rem !important;
        }

        .trw-main-panel div[data-testid="stForm"] {
            border: 1px solid #e4e9f1;
            border-radius: 13px;
            padding: 0.72rem 0.82rem 0.82rem 0.82rem;
            background: #fbfcfe;
        }

        .trw-main-panel [data-testid="stForm"] h3,
        .trw-main-panel div[data-testid="stVerticalBlockBorderWrapper"] h3 {
            margin-top: 0 !important;
        }

        .trw-main-panel [data-testid="stFileUploader"] section {
            border-radius: 12px !important;
            border: 1px dashed #cfd8e6 !important;
            background: #f9fbfe !important;
            padding: 0.28rem !important;
        }

        .trw-main-panel [data-testid="stFileUploaderDropzone"] {
            padding: 0.85rem 0.75rem !important;
        }

        .trw-compact-card {
            border: 1px solid #e4e9f1;
            border-radius: 13px;
            padding: 0.2rem 0.12rem 0.12rem 0.12rem;
            background: #fbfcfe;
            margin: 0.15rem 0 0.45rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_global_header() -> None:
    st.markdown(
        """
        <div class="trw-global-header">
            <div class="trw-global-header__inner">
                <div class="trw-global-header__title">AIGC 科研写作工作台 2.0</div>
                <div class="trw-global-header__subtitle">教师科研训练与写作加速平台</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_current_page() -> None:
    page = st.session_state.current_page

    if page == "选题助手":
        render_ai_mentor_page()
    elif page == "文献工作台":
        render_literature_workspace_page()
    elif page == "写作工作台":
        render_writing_workspace_page()
    elif page == "润色与导出":
        render_polish_export_page()
    elif page == "设置":
        render_settings_page()
    else:
        st.error(f"未知页面：{page}")


def run_app() -> None:
    setup_logging()

    st.set_page_config(
        page_title="AIGC 科研写作工作台 2.0",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_app_shell()

    init_app_state()
    if st.session_state.current_page not in ALL_PAGE_NAMES:
        st.session_state.current_page = "选题助手"

    render_global_header()

    nav_col, main_col = st.columns([0.98, 3.9], gap="medium")

    with nav_col:
        render_sidebar(st.container(), st.session_state.current_page)

    with main_col:
        st.markdown('<div class="trw-main-panel">', unsafe_allow_html=True)
        render_current_page()
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    run_app()
