import streamlit as st

from config.settings import load_settings
from core.schemas import LiteratureItem, LiteraturePreprocessResult, LiteratureReviewPack
from core.state import (
    add_literature_upload,
    bump_literature_uploader_nonce,
    clear_busy_action,
    clear_literature_upload_queue,
    get_busy_action,
    get_literature_upload_queue,
    get_literature_uploader_nonce,
    get_selected_topic,
    get_topic_card,
    pop_page_message,
    remove_literature_upload,
    set_busy_action,
    set_literature_items,
    set_literature_review_pack,
    set_page_message,
)
from services.literature_service import FileProcessStatus, process_uploaded_pdfs
from storage.file_store import assess_browser_upload_risk, buffer_local_pdf_path, buffer_uploaded_file


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


def _render_preprocess_result(item: LiteraturePreprocessResult) -> None:
    st.markdown(f"**原始文件名：** {item.original_file_name or item.file_name}")
    st.markdown(f"**存储文件名：** {item.stored_file_name or '暂无'}")
    st.markdown(f"**标题：** {item.title or '暂无'}")
    st.markdown(f"**作者：** {', '.join(item.authors) if item.authors else '暂无'}")
    st.markdown(f"**年份：** {item.year or '暂无'}")
    st.markdown(f"**提取后端：** {item.extraction_backend or 'basic_python'}")
    st.markdown(f"**是否满足 AI 分析条件：** {'是' if item.is_ai_ready else '否'}")

    st.markdown("**摘要片段**")
    st.caption(item.abstract_text or "暂无")

    st.markdown("**前言关键段**")
    if item.intro_snippets:
        for text in item.intro_snippets:
            st.markdown(f"- {text}")
    else:
        st.caption("暂无")

    st.markdown("**结论关键段**")
    if item.conclusion_snippets:
        for text in item.conclusion_snippets:
            st.markdown(f"- {text}")
    else:
        st.caption("暂无")

    st.markdown("**正文关键片段**")
    if item.body_snippets:
        for text in item.body_snippets:
            st.markdown(f"- {text}")
    else:
        st.caption("暂无")

    if item.preprocess_error:
        st.warning(item.preprocess_error)


def _render_literature_item(item: LiteratureItem) -> None:
    st.markdown(f"**文件：** {item.file_name}")
    st.markdown(f"**标题：** {item.title or '暂无'}")
    st.markdown(f"**方法：** {item.method or '暂无'}")
    st.markdown(f"**主要结论：** {item.findings or '暂无'}")
    st.markdown("**摘要速读**")
    st.caption(item.abstract or "暂无")


def _render_status(status: FileProcessStatus) -> None:
    st.markdown(f"**原始文件名：** {status.original_file_name}")
    st.markdown(f"**存储文件名：** {status.stored_file_name or '尚未保存'}")
    st.markdown("**浏览器已选择：** 是")
    st.markdown(f"**服务器已接收：** {'是' if status.server_received else '否'}")
    st.markdown(f"**文件已保存：** {'是' if status.file_saved else '否'}")
    st.markdown(f"**预处理已开始：** {'是' if status.preprocess_started else '否'}")
    st.markdown(f"**上传状态：** {status.upload_status}")
    st.markdown(f"**本地预处理：** {status.preprocess_status}")
    st.markdown(f"**AI 分析：** {status.ai_status}")
    st.markdown(f"**阶段说明：** {status.stage}")
    if status.upload_error:
        st.warning(f"老师可读提示：{status.upload_error}")
    st.caption(status.message)
    if status.debug_error:
        with st.expander("调试信息"):
            st.code(status.debug_error)


def _render_review_pack(review_pack: LiteratureReviewPack) -> None:
    sections = [
        ("高频研究主题", review_pack.high_frequency_themes),
        ("常用研究方法", review_pack.common_methods),
        ("共同结论", review_pack.common_findings),
        ("主要分歧", review_pack.major_disagreements),
        ("研究不足", review_pack.research_limitations),
        ("可写切入点", review_pack.suggested_angles),
    ]
    for title, values in sections:
        st.markdown(f"**{title}**")
        if values:
            for value in values:
                st.markdown(f"- {value}")
        else:
            st.caption("暂无")


def render_literature_workspace_page() -> None:
    _render_flash_message()

    st.title("文献工作台")
    st.info("本轮优先优化上传稳定性与 PDF 本地预处理质量，再进入 AI 分析。")

    selected_topic = get_selected_topic()
    topic_card = get_topic_card()
    is_processing = bool(get_busy_action("literature_processing"))

    with st.container(border=True):
        st.subheader("当前研究题目")
        if selected_topic:
            st.success(selected_topic)
        else:
            st.warning("请先到选题助手确定题目。")

    with st.container(border=True):
        st.subheader("加入文献的两种方式")
        left_col, right_col = st.columns(2)
        with left_col:
            st.markdown("**推荐入口：浏览器上传**")
            st.caption("现在支持一次多选多个 PDF。选中后会自动加入待处理列表，适合大多数正常 PDF。Windows 下可在文件选择框里按 Ctrl 或 Shift 一次选多篇。")
            st.markdown("- 支持一次性把多篇 PDF 一起加入待处理列表。")
            st.markdown("- 如个别文件持续报 400，可改用右侧本地路径导入。")
        with right_col:
            st.markdown("**兜底入口：本地路径加入**")
            st.caption("适合浏览器出现红色 400、文件名特殊、或你希望按本地路径一次批量导入多篇文献时使用。")
            st.markdown("- 支持 Windows 路径和 WSL 路径。")
            st.markdown("- 一行一个 PDF，可一次加入多篇。")

        st.markdown("---")
        st.caption("浏览器里出现红色 400，一般发生在“文件发送到服务端之前”，还没进入 PDF 解析。若个别文件持续上传失败，可优先缩短文件名、减少特殊符号，或直接改用下方“本地路径加入”兜底。")
        st.markdown("- 浏览器上传现在支持一次多选多个 PDF。")
        st.markdown("- 文件名过长、含全角标点或长破折号时，浏览器上传更容易失败。")
        st.markdown("- 如果同一文件反复出现红色 400，建议先简化文件名后重试，或直接走本地路径导入。")

    uploader_key = f"literature_pdf_uploader_{get_literature_uploader_nonce()}"
    selected_uploads = st.file_uploader(
        "上传 PDF 文献",
        type=["pdf"],
        accept_multiple_files=True,
        key=uploader_key,
        disabled=is_processing,
        help="支持一次多选多个 PDF；Windows 下可在文件选择框里按 Ctrl 或 Shift 一次选多篇。选中后会自动加入待处理列表。如果个别文件浏览器上传失败，再使用下方“本地路径批量加入”。",
    )

    if selected_uploads:
        queue_signatures = {getattr(item, "signature", "") for item in get_literature_upload_queue()}
        newly_added = []
        upload_errors = []

        for selected_upload in selected_uploads:
            try:
                buffered_upload = buffer_uploaded_file(selected_upload)
                if buffered_upload.signature not in queue_signatures:
                    add_literature_upload(buffered_upload)
                    newly_added.append(buffered_upload)
                    queue_signatures.add(buffered_upload.signature)
            except Exception as exc:
                upload_errors.append(f"{getattr(selected_upload, 'name', 'uploaded.pdf')}：{exc}")

        if newly_added:
            st.session_state.literature_local_path_errors = []
            joined_names = "；".join(upload.name for upload in newly_added[:6])
            if len(newly_added) > 6:
                joined_names += " 等"
            set_page_message("success", f"已加入待处理列表：{joined_names}")
            bump_literature_uploader_nonce()
            st.rerun()

        if upload_errors:
            set_page_message("error", "；".join(upload_errors))

        for upload in selected_uploads:
            for risk_text in assess_browser_upload_risk(getattr(upload, "name", ""), getattr(upload, "size", 0)):
                st.warning(f"上传风险提示：{risk_text}")

    with st.expander("如果浏览器上传失败，可直接从本地路径加入", expanded=False):
        st.caption("适用于浏览器上传出现 AxiosError 400 时的稳定兜底方案。支持 Windows 路径或 WSL 路径，每行一个，可一次加入多个 PDF。")
        local_pdf_paths = st.text_area(
            "本地 PDF 路径",
            height=100,
            placeholder="例如：\nD:\\sync-folder0\\00教学案例\\科研论文\\某篇论文.pdf",
            disabled=is_processing,
            key="literature_local_pdf_paths",
        )
        import_from_path_clicked = st.button(
            "从本地路径加入待处理列表",
            key="literature_add_local_paths",
            use_container_width=True,
            disabled=is_processing,
        )
        if import_from_path_clicked:
            lines = [line.strip() for line in local_pdf_paths.splitlines() if line.strip()]
            if not lines:
                set_page_message("warning", "请至少输入一个本地 PDF 路径。")
            else:
                success_names = []
                errors = []
                for line in lines:
                    try:
                        buffered_upload = buffer_local_pdf_path(line)
                        add_literature_upload(buffered_upload)
                        success_names.append(buffered_upload.name)
                    except Exception as exc:
                        errors.append(f"{line}：{exc}")
                if success_names:
                    bump_literature_uploader_nonce()
                    set_page_message("success", f"已从本地路径加入待处理列表：{'；'.join(success_names)}")
                st.session_state.literature_local_path_errors = errors
                st.rerun()

    uploaded_files = get_literature_upload_queue()
    local_path_errors = st.session_state.get("literature_local_path_errors", [])

    with st.container(border=True):
        st.subheader("浏览器已选择文件")
        if not uploaded_files:
            st.caption("暂未选择文件。你可以在上方一次选择多篇 PDF，或在浏览器上传失败时改用下方“本地路径批量加入”。")
        else:
            st.caption("下列文件已成功进入待处理列表。你可以继续补充更多 PDF，再统一开始处理。")
            for file in uploaded_files:
                file_name = getattr(file, "name", "uploaded.pdf")
                file_signature = getattr(file, "signature", file_name)
                file_source = getattr(file, "source", "browser")
                left_col, right_col = st.columns([0.88, 0.12])
                with left_col:
                    source_text = "浏览器上传" if file_source == "browser" else "本地路径导入"
                    st.markdown(f"- {file_name}：已加入待处理列表（{source_text}），等待开始处理")
                    for risk_text in assess_browser_upload_risk(file_name, getattr(file, "size", 0)):
                        st.caption(f"风险提示：{risk_text}")
                with right_col:
                    if st.button("移除", key=f"remove_upload_{file_signature}", disabled=is_processing):
                        remove_literature_upload(file_signature)
                        st.rerun()

    if local_path_errors:
        with st.container(border=True):
            st.subheader("本地路径导入失败")
            for error_text in local_path_errors:
                st.warning(error_text)
        st.session_state.literature_local_path_errors = []

    start_clicked = st.button(
        "正在处理文献…" if is_processing else "开始文献处理",
        use_container_width=True,
        disabled=is_processing,
        key="literature_start_processing",
    )
    if start_clicked and not is_processing:
        set_busy_action("literature_processing", True)
        st.rerun()

    if is_processing:
        if not selected_topic:
            clear_busy_action("literature_processing")
            set_page_message("warning", "请先到选题助手确定题目，再开始文献分析。")
            st.rerun()
        if not uploaded_files:
            clear_busy_action("literature_processing")
            set_page_message("warning", "请先把至少一个 PDF 加入待处理列表，再开始文献处理。")
            st.rerun()

        try:
            settings = load_settings()
            with st.spinner("正在处理文献…"):
                result = process_uploaded_pdfs(
                    uploaded_files,
                    settings,
                    selected_topic=selected_topic,
                    topic_card=topic_card,
                )

            st.session_state.literature_preprocess_results = result.preprocess_results
            st.session_state.literature_file_statuses = result.file_statuses
            st.session_state.literature_success_count = result.success_count
            st.session_state.literature_failed_count = result.failed_count
            st.session_state.literature_server_received_count = result.server_received_count
            st.session_state.literature_saved_count = result.saved_count
            st.session_state.literature_summary_notice = result.summary_notice
            st.session_state.literature_themes = result.themes
            st.session_state.literature_gaps = result.gaps
            st.session_state.literature_analysis_warnings = result.analysis_warnings
            st.session_state.literature_review_pack = result.review_pack
            st.session_state.literature_preliminary_common_points = result.preliminary_common_points
            st.session_state.literature_preliminary_differences = result.preliminary_differences
            set_literature_items(result.items)
            set_literature_review_pack(result.review_pack)

            set_page_message(
                "success",
                f"处理完成：服务器已接收 {result.server_received_count} 个文件，成功保存 {result.saved_count} 个，AI 成功分析 {result.success_count} 篇。",
            )
            clear_literature_upload_queue()
            bump_literature_uploader_nonce()
        except Exception as exc:
            set_page_message("error", f"文献处理失败：{exc}")
        finally:
            clear_busy_action("literature_processing")
        st.rerun()

    preprocess_results = st.session_state.get("literature_preprocess_results", [])
    file_statuses = st.session_state.get("literature_file_statuses", [])
    success_count = st.session_state.get("literature_success_count", 0)
    failed_count = st.session_state.get("literature_failed_count", 0)
    server_received_count = st.session_state.get("literature_server_received_count", 0)
    saved_count = st.session_state.get("literature_saved_count", 0)
    summary_notice = st.session_state.get("literature_summary_notice", "")
    themes = st.session_state.get("literature_themes", {})
    gaps = st.session_state.get("literature_gaps", [])
    analysis_warnings = st.session_state.get("literature_analysis_warnings", [])
    review_pack = st.session_state.get("literature_review_pack", LiteratureReviewPack())
    preliminary_common_points = st.session_state.get("literature_preliminary_common_points", [])
    preliminary_differences = st.session_state.get("literature_preliminary_differences", [])
    literature_items = st.session_state.get("literature_items", [])

    with st.container(border=True):
        st.subheader("处理概况")
        st.markdown(f"**浏览器已选择并成功发送：** {len(uploaded_files) if uploaded_files else 0}")
        st.markdown(f"**服务器已接收：** {server_received_count}")
        st.markdown(f"**文件已保存：** {saved_count}")
        st.markdown(f"**成功文献篇数：** {success_count}")
        st.markdown(f"**失败文件篇数：** {failed_count}")
        if summary_notice:
            st.info(summary_notice)
        if uploaded_files and server_received_count < len(uploaded_files):
            st.warning("有文件尚未完成服务端接收，请重新加入待处理列表后再试。")

    with st.container(border=True):
        st.subheader("文件处理状态")
        if not file_statuses:
            st.caption("暂无文件处理记录。上传并处理 PDF 后会在这里显示。")
        else:
            for status in file_statuses:
                with st.container(border=True):
                    _render_status(status)

    with st.container(border=True):
        st.subheader("本地预处理成功文件")
        success_items = [item for item in preprocess_results if item.is_ai_ready]
        if not success_items:
            st.caption("暂无本地预处理成功文件。")
        else:
            for item in success_items:
                with st.container(border=True):
                    _render_preprocess_result(item)

    with st.container(border=True):
        st.subheader("成功文献")
        if not literature_items:
            st.caption("暂无成功生成的文献速读卡。")
        else:
            for item in literature_items:
                with st.container(border=True):
                    _render_literature_item(item)

    with st.container(border=True):
        st.subheader("失败文件")
        failed_statuses = [status for status in file_statuses if status.ai_status != "AI 分析成功"]
        if not failed_statuses:
            st.caption("暂无失败文件。")
        else:
            for status in failed_statuses:
                st.warning(f"{status.original_file_name} | {status.stage} | {status.message}")

    if success_count == 2:
        with st.container(border=True):
            st.subheader("初步共同点与差异")
            st.markdown("**初步共同点**")
            for text in preliminary_common_points or ["暂无"]:
                st.markdown(f"- {text}")
            st.markdown("**初步差异**")
            for text in preliminary_differences or ["暂无"]:
                st.markdown(f"- {text}")

    if success_count >= 3:
        with st.container(border=True):
            st.subheader("主题簇")
            if themes:
                for theme_name, files in themes.items():
                    st.markdown(f"**{theme_name}**")
                    for file_name in files:
                        st.markdown(f"- {file_name}")
            else:
                st.caption("暂无主题簇结果。")

        with st.container(border=True):
            st.subheader("研究空白提示")
            if gaps:
                for text in gaps:
                    st.markdown(f"- {text}")
            else:
                st.caption("暂无研究空白结果。")

        with st.container(border=True):
            st.subheader("文献综述素材包")
            _render_review_pack(review_pack)

    if analysis_warnings:
        with st.container(border=True):
            st.subheader("分析提醒")
            for warning_text in analysis_warnings:
                st.warning(warning_text)

    st.markdown("---")
    if st.button("下一步：去写作工作台", use_container_width=True, key="literature_next_to_writing"):
        st.session_state.current_page = "写作工作台"
        st.rerun()
