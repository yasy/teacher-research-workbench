from dataclasses import dataclass

from config.settings import Settings
from core.exceptions import PDFParseError
from core.schemas import LiteratureItem, LiteraturePreprocessResult, LiteratureReviewPack, TopicCard
from llm.factory import build_llm_client
from literature.chunker import select_body_snippets
from literature.gap_detector import detect_research_gaps
from literature.metadata_extractor import (
    extract_abstract_text,
    extract_basic_metadata,
    extract_conclusion_snippets,
    extract_intro_snippets,
)
from literature.pdf_loader import extract_pdf_content
from literature.summarizer import summarize_preprocessed_result
from literature.text_cleaner import clean_pdf_text, filter_noise_paragraphs, split_into_paragraphs
from literature.theme_cluster import build_literature_review_pack, cluster_themes
from storage.file_store import SavedUploadResult, save_uploaded_pdf


@dataclass
class FileProcessStatus:
    original_file_name: str
    stored_file_name: str
    server_received: bool
    file_saved: bool
    preprocess_started: bool
    upload_status: str
    upload_error: str
    preprocess_status: str
    ai_status: str
    stage: str
    message: str
    debug_error: str = ""


@dataclass
class LiteratureProcessResult:
    items: list[LiteratureItem]
    preprocess_results: list[LiteraturePreprocessResult]
    file_statuses: list[FileProcessStatus]
    analysis_warnings: list[str]
    success_count: int
    failed_count: int
    server_received_count: int
    saved_count: int
    summary_notice: str
    preliminary_common_points: list[str]
    preliminary_differences: list[str]
    themes: dict[str, list[str]]
    gaps: list[str]
    review_pack: LiteratureReviewPack


def _classify_processing_error(exc: Exception) -> tuple[str, str, str]:
    message = str(exc).strip() or exc.__class__.__name__
    exc_name = exc.__class__.__name__.lower()

    if isinstance(exc, PDFParseError):
        return (
            "PDF 文本提取失败",
            "预处理失败",
            "该文件无法正常提取文本，可能是扫描版、损坏文件或非标准 PDF。",
        )
    if "badrequest" in exc_name or "api" in exc_name or "400" in message:
        return (
            "模型摘要失败",
            "预处理成功",
            "模型在生成文献速读卡时失败，请稍后重试或更换模型。",
        )
    if "json" in message.lower() or "model response" in message.lower():
        return (
            "模型返回格式异常",
            "预处理成功",
            "模型返回结果格式异常，未能生成可读的文献速读卡。",
        )
    return ("其他失败", "预处理失败", f"处理过程中发生异常：{message}")


def _build_preliminary_insights(items: list[LiteratureItem]) -> tuple[list[str], list[str]]:
    methods = [item.method.strip() for item in items if item.method.strip()]
    findings = [item.findings.strip() for item in items if item.findings.strip()]
    titles = [item.title.strip() for item in items if item.title.strip()]

    common_points: list[str] = []
    differences: list[str] = []

    if methods:
        unique_methods = list(dict.fromkeys(methods))
        if len(unique_methods) == 1:
            common_points.append(f"两篇文献都主要采用了“{unique_methods[0]}”这一研究方法。")
        else:
            common_points.append(f"两篇文献都围绕“{titles[0] if titles else '当前题目'}”相关问题展开研究。")
            differences.append(f"研究方法存在差异，分别涉及：{'、'.join(unique_methods[:3])}。")

    if findings:
        unique_findings = list(dict.fromkeys(findings))
        common_points.append("两篇文献都形成了可用于教学改进的研究结论。")
        if len(unique_findings) > 1:
            differences.append("两篇文献的结论侧重点不同，建议写作时分别比较其结论适用范围。")

    if not common_points:
        common_points.append("两篇文献都与当前题目具有初步相关性，可作为后续写作参考。")
    if not differences:
        differences.append("当前两篇文献差异信息有限，建议继续补充文献后再做正式归纳。")

    return common_points[:3], differences[:3]


def _looks_garbled_text(text: str) -> bool:
    stripped = "".join((text or "").split())
    if not stripped:
        return False

    latin1_chars = [char for char in stripped if "\u00C0" <= char <= "\u00FF"]
    box_chars = sum(stripped.count(char) for char in ("■", "□", "▪", "▢", "▣", "�"))
    chinese_chars = sum(1 for char in stripped if "\u4e00" <= char <= "\u9fff")

    return (
        len(latin1_chars) / len(stripped) > 0.05
        or box_chars / len(stripped) > 0.03
        or (len(stripped) > 80 and chinese_chars == 0 and any(ord(char) > 127 for char in stripped))
    )


def _prepare_preprocess_payload(
    file_path: str,
    original_file_name: str,
    selected_topic: str | None,
    backend: str,
):
    extraction_result = extract_pdf_content(file_path, backend=backend)
    cleaned_text = clean_pdf_text(extraction_result.text)
    paragraphs = filter_noise_paragraphs(split_into_paragraphs(cleaned_text))
    metadata = extract_basic_metadata(cleaned_text, original_file_name)
    abstract_text = extract_abstract_text(paragraphs)
    intro_snippets = extract_intro_snippets(paragraphs)
    conclusion_snippets = extract_conclusion_snippets(paragraphs)
    excluded = set(intro_snippets + conclusion_snippets)
    body_candidates = [paragraph for paragraph in paragraphs if paragraph not in excluded]
    body_snippets = select_body_snippets(body_candidates, selected_topic=selected_topic)
    return extraction_result, metadata, abstract_text, intro_snippets, conclusion_snippets, body_snippets


def _build_preprocess_result(
    save_result: SavedUploadResult,
    selected_topic: str | None = None,
) -> LiteraturePreprocessResult:
    extraction_result, metadata, abstract_text, intro_snippets, conclusion_snippets, body_snippets = _prepare_preprocess_payload(
        save_result.file_path,
        save_result.original_file_name,
        selected_topic,
        "auto",
    )

    title_text = str(metadata.get("title", ""))
    author_text = " ".join(list(metadata.get("authors", [])))
    sample_text = " ".join(
        [title_text, abstract_text, *intro_snippets[:1], *conclusion_snippets[:1], *body_snippets[:1]]
    )
    has_garbled_content = any(
        _looks_garbled_text(text)
        for text in (title_text, author_text, sample_text)
        if text
    )

    if extraction_result.backend_name == "basic_python" and has_garbled_content:
        for fallback_backend in ("pymupdf", "pymupdf4llm"):
            try:
                candidate_result, candidate_metadata, candidate_abstract, candidate_intro, candidate_conclusion, candidate_body = _prepare_preprocess_payload(
                    save_result.file_path,
                    save_result.original_file_name,
                    selected_topic,
                    fallback_backend,
                )
            except Exception:
                continue

            candidate_title = str(candidate_metadata.get("title", ""))
            candidate_author_text = " ".join(list(candidate_metadata.get("authors", [])))
            candidate_sample = " ".join(
                [candidate_title, candidate_abstract, *candidate_intro[:1], *candidate_conclusion[:1], *candidate_body[:1]]
            )
            candidate_has_garbled_content = any(
                _looks_garbled_text(text)
                for text in (candidate_title, candidate_author_text, candidate_sample)
                if text
            )
            if not candidate_has_garbled_content:
                extraction_result = candidate_result
                metadata = candidate_metadata
                abstract_text = candidate_abstract
                intro_snippets = candidate_intro
                conclusion_snippets = candidate_conclusion
                body_snippets = candidate_body
                break

    is_ai_ready = bool(abstract_text or intro_snippets or conclusion_snippets or body_snippets)
    preprocess_error = "" if is_ai_ready else "未能提取到足够的有效分析材料。"

    return LiteraturePreprocessResult(
        file_name=save_result.stored_file_name or save_result.original_file_name,
        original_file_name=save_result.original_file_name,
        stored_file_name=save_result.stored_file_name,
        title=str(metadata.get("title", "")),
        authors=list(metadata.get("authors", [])),
        year=str(metadata.get("year", "")),
        abstract_text=abstract_text,
        intro_snippets=intro_snippets,
        conclusion_snippets=conclusion_snippets,
        body_snippets=body_snippets,
        extraction_backend=extraction_result.backend_name,
        is_ai_ready=is_ai_ready,
        preprocess_error=preprocess_error,
    )


def process_uploaded_pdfs(
    uploaded_files: list,
    settings: Settings,
    selected_topic: str | None = None,
    topic_card: TopicCard | None = None,
) -> LiteratureProcessResult:
    llm_client = None
    preprocess_results: list[LiteraturePreprocessResult] = []
    file_statuses: list[FileProcessStatus] = []
    items: list[LiteratureItem] = []
    analysis_warnings: list[str] = []

    for uploaded_file in uploaded_files:
        save_result = save_uploaded_pdf(uploaded_file, settings.uploads_dir)
        if not save_result.file_saved:
            file_statuses.append(
                FileProcessStatus(
                    original_file_name=save_result.original_file_name,
                    stored_file_name=save_result.stored_file_name,
                    server_received=save_result.server_received,
                    file_saved=False,
                    preprocess_started=False,
                    upload_status=save_result.upload_status,
                    upload_error=save_result.upload_error,
                    preprocess_status="未开始",
                    ai_status="AI 分析尚未开始",
                    stage="上传失败",
                    message=save_result.upload_error or "文件未成功上传到服务端，请重新选择后再试。",
                    debug_error=save_result.debug_error,
                )
            )
            continue

        try:
            preprocess_result = _build_preprocess_result(save_result, selected_topic=selected_topic)
            preprocess_results.append(preprocess_result)
        except Exception as exc:
            stage, preprocess_status, friendly_message = _classify_processing_error(exc)
            file_statuses.append(
                FileProcessStatus(
                    original_file_name=save_result.original_file_name,
                    stored_file_name=save_result.stored_file_name,
                    server_received=save_result.server_received,
                    file_saved=True,
                    preprocess_started=True,
                    upload_status=save_result.upload_status,
                    upload_error=save_result.upload_error,
                    preprocess_status=preprocess_status,
                    ai_status="AI 分析尚未开始",
                    stage=stage,
                    message=friendly_message,
                    debug_error=str(exc),
                )
            )
            continue

        if not preprocess_result.is_ai_ready:
            file_statuses.append(
                FileProcessStatus(
                    original_file_name=save_result.original_file_name,
                    stored_file_name=save_result.stored_file_name,
                    server_received=save_result.server_received,
                    file_saved=True,
                    preprocess_started=True,
                    upload_status=save_result.upload_status,
                    upload_error=save_result.upload_error,
                    preprocess_status="预处理失败",
                    ai_status="AI 分析尚未开始",
                    stage="预处理失败",
                    message=preprocess_result.preprocess_error or "文件已上传，但预处理失败。",
                )
            )
            continue

        if llm_client is None:
            llm_client = build_llm_client(settings)

        try:
            item = summarize_preprocessed_result(preprocess_result, llm_client)
            items.append(item)
            file_statuses.append(
                FileProcessStatus(
                    original_file_name=save_result.original_file_name,
                    stored_file_name=save_result.stored_file_name,
                    server_received=save_result.server_received,
                    file_saved=True,
                    preprocess_started=True,
                    upload_status=save_result.upload_status,
                    upload_error=save_result.upload_error,
                    preprocess_status="预处理成功",
                    ai_status="AI 分析成功",
                    stage="完成",
                    message=f"已使用 {preprocess_result.extraction_backend} 后端生成文献速读卡。",
                )
            )
        except Exception as exc:
            stage, _, friendly_message = _classify_processing_error(exc)
            file_statuses.append(
                FileProcessStatus(
                    original_file_name=save_result.original_file_name,
                    stored_file_name=save_result.stored_file_name,
                    server_received=save_result.server_received,
                    file_saved=True,
                    preprocess_started=True,
                    upload_status=save_result.upload_status,
                    upload_error=save_result.upload_error,
                    preprocess_status="预处理成功",
                    ai_status="AI 分析失败",
                    stage=stage,
                    message=friendly_message,
                    debug_error=str(exc),
                )
            )

    success_count = len(items)
    server_received_count = len([status for status in file_statuses if status.server_received])
    saved_count = len([status for status in file_statuses if status.file_saved])
    failed_count = len([status for status in file_statuses if status.ai_status != "AI 分析成功"])
    themes: dict[str, list[str]] = {}
    gaps: list[str] = []
    review_pack = LiteratureReviewPack()
    preliminary_common_points: list[str] = []
    preliminary_differences: list[str] = []

    if success_count <= 1:
        summary_notice = "当前成功文献不足 2 篇，暂不生成多篇归纳结果，只展示单篇速读卡。"
    elif success_count == 2:
        summary_notice = "当前成功文献为 2 篇，可做初步共同点与差异比较；研究空白和综述素材包暂不正式生成。"
        preliminary_common_points, preliminary_differences = _build_preliminary_insights(items)
    else:
        summary_notice = "当前成功文献达到 3 篇及以上，开始生成主题簇、研究空白和综述素材包。"
        effective_topic_card = topic_card
        if effective_topic_card is None and selected_topic:
            effective_topic_card = TopicCard(title=selected_topic)

        try:
            themes = cluster_themes(items, llm_client)
        except Exception:
            analysis_warnings.append("多篇主题归纳暂未生成，请稍后重试。")

        try:
            gaps = detect_research_gaps(items, llm_client, topic_card=effective_topic_card)
        except Exception:
            analysis_warnings.append("当前成功文献已达门槛，但研究空白暂未生成。")

        try:
            review_pack = build_literature_review_pack(items, llm_client, topic_card=effective_topic_card)
        except Exception:
            analysis_warnings.append("当前成功文献已达门槛，但综述素材包暂未生成。")

    return LiteratureProcessResult(
        items=items,
        preprocess_results=preprocess_results,
        file_statuses=file_statuses,
        analysis_warnings=analysis_warnings,
        success_count=success_count,
        failed_count=failed_count,
        server_received_count=server_received_count,
        saved_count=saved_count,
        summary_notice=summary_notice,
        preliminary_common_points=preliminary_common_points,
        preliminary_differences=preliminary_differences,
        themes=themes,
        gaps=gaps,
        review_pack=review_pack,
    )
