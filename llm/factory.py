from config.settings import Settings
from core.exceptions import LLMConfigError
from llm.base import BaseLLMClient
from llm.openai_compatible import OpenAICompatibleClient


def build_llm_client(settings: Settings) -> BaseLLMClient:
    provider = (settings.provider or "").strip().lower()
    supported_providers = {"openai_compatible", "siliconflow", "groq"}

    if provider not in supported_providers:
        raise LLMConfigError(f"Unsupported provider for P0: {settings.provider}")

    if not settings.model:
        raise LLMConfigError("LLM_MODEL is required.")

    return OpenAICompatibleClient(
        base_url=settings.base_url,
        api_key=settings.api_key,
        model=settings.model,
    )
