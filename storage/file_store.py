from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import unicodedata
from uuid import uuid4

from core.utils import ensure_dir, safe_filename


@dataclass
class SavedUploadResult:
    original_file_name: str
    stored_file_name: str
    file_path: str
    server_received: bool
    file_saved: bool
    upload_status: str
    upload_error: str
    debug_error: str


@dataclass
class BufferedUpload:
    name: str
    data: bytes
    size: int
    signature: str
    source: str = "browser"

    def getbuffer(self):
        return memoryview(self.data)


def assess_browser_upload_risk(file_name: str, file_size: int) -> list[str]:
    risks: list[str] = []
    normalized_name = str(file_name or "").strip()

    if len(normalized_name) > 48:
        risks.append("文件名偏长，浏览器上传阶段更容易失败。")

    risky_chars = ["：", "《", "》", "【", "】", "（", "）", "“", "”", "‘", "’", "—", "…"]
    has_non_ascii_punctuation = any(
        (char in risky_chars) or (not char.isascii() and unicodedata.category(char).startswith("P"))
        for char in normalized_name
    )
    if has_non_ascii_punctuation:
        risks.append("文件名包含中文标点、全角符号或长破折号，浏览器上传时可能更不稳定。")

    if file_size >= 15 * 1024 * 1024:
        risks.append("文件体积较大，浏览器上传更容易超时或中断。")

    return risks


def _build_upload_signature(original_file_name: str, file_bytes: bytes) -> str:
    digest = hashlib.sha1(file_bytes).hexdigest()[:12]
    safe_name = safe_filename(Path(original_file_name or "uploaded.pdf").stem)[:24] or "uploaded"
    return f"{safe_name}_{digest}"


def _validate_pdf_bytes(file_bytes: bytes) -> None:
    if not file_bytes:
        raise ValueError("文件内容为空，未能成功上传，请重新选择文件后再试。")
    if not file_bytes.startswith(b"%PDF"):
        raise ValueError("该文件不是可识别的 PDF，或上传内容已损坏，请重新导出 PDF 后再试。")


def build_stored_pdf_name(original_file_name: str) -> str:
    original_path = Path(original_file_name or "uploaded.pdf")
    normalized_stem = safe_filename(original_path.stem)
    ascii_stem = re.sub(r"[^A-Za-z0-9_-]+", "", normalized_stem)[:20]
    safe_stem = ascii_stem or "pdf"
    return f"{safe_stem}_{uuid4().hex[:8]}.pdf"


def buffer_uploaded_file(uploaded_file) -> BufferedUpload:
    original_file_name = getattr(uploaded_file, "name", "uploaded.pdf") or "uploaded.pdf"
    try:
        buffer = uploaded_file.getbuffer()
        file_bytes = bytes(buffer)
    except Exception as exc:
        raise ValueError("文件未成功上传到服务端，请重新选择后再试。") from exc
    _validate_pdf_bytes(file_bytes)
    return BufferedUpload(
        name=original_file_name,
        data=file_bytes,
        size=len(file_bytes),
        signature=_build_upload_signature(original_file_name, file_bytes),
        source="browser",
    )


def _resolve_local_pdf_path(file_path: str) -> Path:
    raw = str(file_path or "").strip().strip('"').strip("'")
    if not raw:
        raise ValueError("文件路径为空。")

    path = Path(raw)
    if path.exists():
        return path

    if os.name != "nt" and len(raw) >= 3 and raw[1:3] == ":\\":
        drive = raw[0].lower()
        suffix = raw[2:].replace("\\", "/")
        wsl_path = Path(f"/mnt/{drive}{suffix}")
        if wsl_path.exists():
            return wsl_path

    raise ValueError(f"找不到文件：{raw}")


def buffer_local_pdf_path(file_path: str) -> BufferedUpload:
    resolved_path = _resolve_local_pdf_path(file_path)
    if resolved_path.suffix.lower() != ".pdf":
        raise ValueError("当前只支持导入 PDF 文件。")

    try:
        file_bytes = resolved_path.read_bytes()
    except Exception as exc:
        raise ValueError("文件存在，但读取失败，请检查文件是否损坏或被其他程序占用。") from exc

    _validate_pdf_bytes(file_bytes)

    return BufferedUpload(
        name=resolved_path.name,
        data=file_bytes,
        size=len(file_bytes),
        signature=_build_upload_signature(resolved_path.name, file_bytes),
        source="local_path",
    )


def save_uploaded_pdf(uploaded_file, uploads_dir: str) -> SavedUploadResult:
    ensure_dir(uploads_dir)

    original_file_name = getattr(uploaded_file, "name", "uploaded.pdf") or "uploaded.pdf"
    stored_file_name = build_stored_pdf_name(original_file_name)
    target_path = Path(uploads_dir) / stored_file_name

    try:
        if hasattr(uploaded_file, "data"):
            file_bytes = bytes(uploaded_file.data)
        else:
            buffer = uploaded_file.getbuffer()
            file_bytes = bytes(buffer)
    except Exception as exc:
        return SavedUploadResult(
            original_file_name=original_file_name,
            stored_file_name="",
            file_path="",
            server_received=True,
            file_saved=False,
            upload_status="服务器已接收，但文件内容读取失败",
            upload_error="文件已上传到服务端，但未能正确读取上传内容，请重新选择文件后再试。",
            debug_error=str(exc),
        )

    try:
        target_path.write_bytes(file_bytes)
    except Exception as exc:
        return SavedUploadResult(
            original_file_name=original_file_name,
            stored_file_name=stored_file_name,
            file_path="",
            server_received=True,
            file_saved=False,
            upload_status="本地保存失败",
            upload_error="文件名或文件内容异常，未能成功保存，请更换文件名或重新导出 PDF 后再试。",
            debug_error=str(exc),
        )

    return SavedUploadResult(
        original_file_name=original_file_name,
        stored_file_name=stored_file_name,
        file_path=str(target_path),
        server_received=True,
        file_saved=True,
        upload_status="文件已保存",
        upload_error="",
        debug_error="",
    )


def list_uploaded_files(uploads_dir: str) -> list[str]:
    path = Path(uploads_dir)
    if not path.exists():
        return []
    return [str(item) for item in path.glob("*.pdf")]
