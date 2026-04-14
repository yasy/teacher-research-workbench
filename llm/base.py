class BaseLLMClient:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    def chat(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        raise NotImplementedError("Subclasses must implement chat().")
