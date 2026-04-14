from openai import OpenAI

from llm.base import BaseLLMClient


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        super().__init__(base_url=base_url, api_key=api_key, model=model)
        self.client = OpenAI(
            api_key=api_key or "dummy-key",
            base_url=base_url or None,
        )

    def chat(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
