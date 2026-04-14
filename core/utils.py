from datetime import datetime
import re
import unicodedata


def safe_filename(name: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(name))
    normalized = re.sub(r"[\x00-\x1f]+", "", normalized)
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", normalized)
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    cleaned = cleaned.strip(" ._")
    return cleaned or "untitled"


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: str) -> str:
    import os

    os.makedirs(path, exist_ok=True)
    return path
