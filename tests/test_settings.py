import os
import unittest
from unittest.mock import patch

from config.settings import load_settings


class SettingsTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://example.com/v1",
            "LLM_API_KEY": "test-key",
            "LLM_MODEL": "test-model",
            "UPLOADS_DIR": "data/uploads",
            "OUTPUTS_DIR": "data/outputs",
            "CACHE_DIR": "data/cache",
        },
        clear=False,
    )
    def test_load_settings_reads_env(self) -> None:
        settings = load_settings()
        self.assertEqual(settings.provider, "openai_compatible")
        self.assertEqual(settings.base_url, "https://example.com/v1")
        self.assertEqual(settings.api_key, "test-key")
        self.assertEqual(settings.model, "test-model")


if __name__ == "__main__":
    unittest.main()
