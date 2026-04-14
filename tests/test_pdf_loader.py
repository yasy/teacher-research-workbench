from pathlib import Path
import tempfile
import unittest

from PyPDF2 import PdfWriter

from literature.pdf_loader import extract_text_from_pdf


class PdfLoaderTests(unittest.TestCase):
    def test_extract_text_from_pdf_returns_string(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "blank.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=300, height=300)
            with file_path.open("wb") as f:
                writer.write(f)

            text = extract_text_from_pdf(str(file_path))

            self.assertIsInstance(text, str)


if __name__ == "__main__":
    unittest.main()
