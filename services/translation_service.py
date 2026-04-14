from pathlib import Path

from config.settings import Settings
from core.schemas import WritingAsset
from llm.factory import build_llm_client


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "prompts"


def split_long_text(text: str, max_chars: int = 1200) -> list[str]:
    if not text.strip():
        return []

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 <= max_chars:
            current = f"{current}\n{paragraph}".strip()
        else:
            if current:
                chunks.append(current)
            if len(paragraph) <= max_chars:
                current = paragraph
            else:
                start = 0
                while start < len(paragraph):
                    end = start + max_chars
                    chunks.append(paragraph[start:end].strip())
                    start = end
                current = ""
    if current:
        chunks.append(current)
    return chunks


def _load_translate_prompt() -> str:
    return (PROMPTS_DIR / "translate_prompt.md").read_text(encoding="utf-8")


def translate_abstract_chunk_to_english(chunk: str, llm_client) -> str:
    prompt = _load_translate_prompt().format(abstract_chunk=chunk.strip())
    return llm_client.chat(
        user_prompt=prompt,
        system_prompt="You are an academic abstract translation assistant.",
        temperature=0.2,
        max_tokens=1200,
    ).strip()


def translate_abstract_to_english(
    asset: WritingAsset,
    settings: Settings,
    max_chars: int = 1200,
) -> WritingAsset:
    llm_client = build_llm_client(settings)
    chunks = split_long_text(asset.content, max_chars=max_chars)
    translated_chunks = [translate_abstract_chunk_to_english(chunk, llm_client) for chunk in chunks]
    content = "\n\n".join(part for part in translated_chunks if part.strip()).strip()
    return WritingAsset(
        asset_type="abstract_en",
        title="英文摘要",
        content=content,
        source_refs=[asset.asset_type],
    )
