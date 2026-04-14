import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    provider: str
    base_url: str
    api_key: str
    model: str
    uploads_dir: str
    outputs_dir: str
    cache_dir: str


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = PROJECT_ROOT / ".env"

SUPPORTED_PROVIDERS = [
    "openai_compatible",
    "siliconflow",
    "groq",
]

PROVIDER_DEFAULTS = {
    "openai_compatible": {
        "label": "OpenAI-Compatible / 自定义兼容接口",
        "base_url": "",
        "models": [],
    },
    "siliconflow": {
        "label": "SiliconFlow",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": [
            "Qwen/Qwen2.5-72B-Instruct",
            "deepseek-ai/DeepSeek-V3",
            "Pro/deepseek-ai/DeepSeek-R1",
        ],
    },
    "groq": {
        "label": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "deepseek-r1-distill-llama-70b",
        ],
    },
}

ENV_FIELD_ORDER = [
    "LLM_PROVIDER",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "LLM_MODEL",
    "UPLOADS_DIR",
    "OUTPUTS_DIR",
    "CACHE_DIR",
]


def load_settings() -> Settings:
    load_dotenv(dotenv_path=DOTENV_PATH, override=False)

    return Settings(
        provider=os.getenv("LLM_PROVIDER", "openai_compatible").strip(),
        base_url=os.getenv("LLM_BASE_URL", "").strip(),
        api_key=os.getenv("LLM_API_KEY", "").strip(),
        model=os.getenv("LLM_MODEL", "").strip(),
        uploads_dir=os.getenv("UPLOADS_DIR", "data/uploads").strip(),
        outputs_dir=os.getenv("OUTPUTS_DIR", "data/outputs").strip(),
        cache_dir=os.getenv("CACHE_DIR", "data/cache").strip(),
    )


def save_settings(
    *,
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    uploads_dir: str,
    outputs_dir: str,
    cache_dir: str,
) -> Settings:
    values = {
        "LLM_PROVIDER": (provider or "openai_compatible").strip(),
        "LLM_BASE_URL": (base_url or "").strip(),
        "LLM_API_KEY": (api_key or "").strip(),
        "LLM_MODEL": (model or "").strip(),
        "UPLOADS_DIR": (uploads_dir or "data/uploads").strip(),
        "OUTPUTS_DIR": (outputs_dir or "data/outputs").strip(),
        "CACHE_DIR": (cache_dir or "data/cache").strip(),
    }

    lines = [f"{key}={values[key]}" for key in ENV_FIELD_ORDER]
    DOTENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    for key, value in values.items():
        os.environ[key] = value

    return Settings(
        provider=values["LLM_PROVIDER"],
        base_url=values["LLM_BASE_URL"],
        api_key=values["LLM_API_KEY"],
        model=values["LLM_MODEL"],
        uploads_dir=values["UPLOADS_DIR"],
        outputs_dir=values["OUTPUTS_DIR"],
        cache_dir=values["CACHE_DIR"],
    )
