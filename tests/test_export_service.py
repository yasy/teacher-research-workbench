from pathlib import Path
import tempfile
import unittest

import docx

from core.schemas import LiteratureItem, TopicCard, WritingAsset
from services.export_service import export_project_to_docx, export_project_to_markdown


class ExportServiceTests(unittest.TestCase):
    def _sample_data(self):
        topic = TopicCard(
            title="课堂提问改进研究",
            research_problem="课堂提问质量不足",
            target_population="小学数学教师",
            context="课堂教学",
            keywords=["课堂提问", "教学改进"],
            recommended_methods=["课堂观察", "行动研究"],
            mentor_analysis="适合教师科研起步。",
        )
        literature = [
            LiteratureItem(
                file_name="a.pdf",
                title="文献A",
                authors=["张三"],
                year="2024",
                abstract="摘要A",
                method="课堂观察",
                findings="结论A",
                theme="",
            )
        ]
        writing = [
            WritingAsset(asset_type="abstract_draft", title="摘要初稿", content="这是摘要初稿。", source_refs=["a.pdf"])
        ]
        polish = [
            WritingAsset(asset_type="abstract_en", title="英文摘要", content="This is the English abstract.", source_refs=[])
        ]
        return topic, literature, writing, polish

    def test_export_project_to_markdown_creates_file(self) -> None:
        topic, literature, writing, polish = self._sample_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = export_project_to_markdown(topic, literature, writing, polish, tmpdir)
            self.assertTrue(Path(path).exists())
            content = Path(path).read_text(encoding="utf-8")
            self.assertIn("选题卡", content)
            self.assertIn("文献速读摘要", content)
            self.assertIn("写作资产", content)

    def test_export_project_to_docx_creates_file(self) -> None:
        topic, literature, writing, polish = self._sample_data()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = export_project_to_docx(topic, literature, writing, polish, tmpdir)
            self.assertTrue(Path(path).exists())
            document = docx.Document(path)
            full_text = "\n".join(p.text for p in document.paragraphs)
            self.assertIn("选题卡", full_text)
            self.assertIn("写作资产", full_text)


if __name__ == "__main__":
    unittest.main()
