import unittest

from config.settings import Settings
from llm.factory import build_llm_client
from llm.openai_compatible import OpenAICompatibleClient


class ModelFactoryTests(unittest.TestCase):
    def build_settings(self, provider: str) -> Settings:
        return Settings(
            provider=provider,
            base_url="https://example.com/v1",
            api_key="test-key",
            model="test-model",
            uploads_dir="data/uploads",
            outputs_dir="data/outputs",
            cache_dir="data/cache",
        )

    def test_build_llm_client_returns_openai_compatible(self) -> None:
        settings = self.build_settings("openai_compatible")

        client = build_llm_client(settings)

        self.assertIsInstance(client, OpenAICompatibleClient)
        self.assertEqual(client.model, "test-model")

    def test_build_llm_client_returns_siliconflow_client(self) -> None:
        settings = self.build_settings("siliconflow")

        client = build_llm_client(settings)

        self.assertIsInstance(client, OpenAICompatibleClient)
        self.assertEqual(client.model, "test-model")

    def test_build_llm_client_returns_groq_client(self) -> None:
        settings = self.build_settings("groq")

        client = build_llm_client(settings)

        self.assertIsInstance(client, OpenAICompatibleClient)
        self.assertEqual(client.model, "test-model")

    def test_build_llm_client_rejects_unsupported_provider(self) -> None:
        settings = self.build_settings("unknown")

        with self.assertRaises(Exception):
            build_llm_client(settings)


if __name__ == "__main__":
    unittest.main()
