import unittest

from services.translation_service import split_long_text


class TranslationServiceTests(unittest.TestCase):
    def test_split_long_text_returns_multiple_chunks_for_long_input(self) -> None:
        text = "第一段。" * 400
        chunks = split_long_text(text, max_chars=120)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 120 for chunk in chunks))

    def test_split_long_text_preserves_order_when_joined(self) -> None:
        text = "甲乙丙丁" * 100
        chunks = split_long_text(text, max_chars=50)
        joined = "".join(chunks)
        self.assertEqual(joined, text)


if __name__ == "__main__":
    unittest.main()
