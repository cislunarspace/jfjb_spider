"""集成测试：爬虫流程和 PDF 导出。"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from newspaper_pdf.jfjb_spider import JFJBSpider, crawl_single_date
from newspaper_pdf.models import Article
from newspaper_pdf.pdf import PDFExporter


# ── crawl_single_date 集成测试 ──────────────────────────────────────────────


@pytest.mark.integration
class TestCrawlSingleDate:
    def _make_spider(self, articles: list[Article] | None = None) -> JFJBSpider:
        spider = MagicMock(spec=JFJBSpider)
        spider.fetch_index_payload.return_value = {"paperInfo": []}
        spider.parse_articles.return_value = articles or []
        return spider

    def _make_exporter(self) -> PDFExporter:
        exporter = MagicMock(spec=PDFExporter)
        exporter.export_articles.return_value = ([], None)
        return exporter

    def test_success(self, tmp_path: Path) -> None:
        article = Article(
            paper_name="解放军报",
            paper_date="2026-03-10",
            paper_number="01",
            section_name="要闻",
            article_index=1,
            title="测试",
            subtitle="",
            author="",
            paragraphs=["正文"],
            source_url="https://example.com",
        )
        spider = self._make_spider([article])
        exporter = self._make_exporter()

        result = crawl_single_date(
            spider=spider,
            exporter=exporter,
            paper_date="2026-03-10",
            out_dir=tmp_path,
            export_individual=True,
            export_combined=True,
            skip_existing=False,
        )
        assert result is True
        exporter.export_articles.assert_called_once()

    def test_skip_existing(self, tmp_path: Path) -> None:
        # 创建已存在的输出目录并放入文件
        date_dir = tmp_path / "2026-03-10"
        date_dir.mkdir()
        (date_dir / "existing.pdf").write_text("fake")

        spider = self._make_spider()
        exporter = self._make_exporter()

        result = crawl_single_date(
            spider=spider,
            exporter=exporter,
            paper_date="2026-03-10",
            out_dir=tmp_path,
            export_individual=True,
            export_combined=True,
            skip_existing=True,
        )
        assert result is True
        spider.fetch_index_payload.assert_not_called()

    def test_http_error(self, tmp_path: Path) -> None:
        spider = self._make_spider()
        spider.fetch_index_payload.side_effect = requests.exceptions.HTTPError()
        exporter = self._make_exporter()

        result = crawl_single_date(
            spider=spider,
            exporter=exporter,
            paper_date="2026-03-10",
            out_dir=tmp_path,
            export_individual=True,
            export_combined=True,
            skip_existing=False,
        )
        assert result is False

    def test_empty_articles(self, tmp_path: Path) -> None:
        spider = self._make_spider([])
        exporter = self._make_exporter()

        result = crawl_single_date(
            spider=spider,
            exporter=exporter,
            paper_date="2026-03-10",
            out_dir=tmp_path,
            export_individual=True,
            export_combined=True,
            skip_existing=False,
        )
        assert result is True
        exporter.export_articles.assert_not_called()

    def test_export_error(self, tmp_path: Path) -> None:
        article = Article(
            paper_name="解放军报",
            paper_date="2026-03-10",
            paper_number="01",
            section_name="要闻",
            article_index=1,
            title="测试",
            subtitle="",
            author="",
            paragraphs=["正文"],
            source_url="https://example.com",
        )
        spider = self._make_spider([article])
        exporter = self._make_exporter()
        exporter.export_articles.side_effect = Exception("PDF 生成失败")

        result = crawl_single_date(
            spider=spider,
            exporter=exporter,
            paper_date="2026-03-10",
            out_dir=tmp_path,
            export_individual=True,
            export_combined=True,
            skip_existing=False,
        )
        assert result is False

    def test_connection_error(self, tmp_path: Path) -> None:
        spider = self._make_spider()
        spider.fetch_index_payload.side_effect = requests.exceptions.ConnectionError()
        exporter = self._make_exporter()

        result = crawl_single_date(
            spider=spider,
            exporter=exporter,
            paper_date="2026-03-10",
            out_dir=tmp_path,
            export_individual=True,
            export_combined=True,
            skip_existing=False,
        )
        assert result is False

    def test_timeout_error(self, tmp_path: Path) -> None:
        spider = self._make_spider()
        spider.fetch_index_payload.side_effect = requests.exceptions.Timeout()
        exporter = self._make_exporter()

        result = crawl_single_date(
            spider=spider,
            exporter=exporter,
            paper_date="2026-03-10",
            out_dir=tmp_path,
            export_individual=True,
            export_combined=True,
            skip_existing=False,
        )
        assert result is False


# ── PDFExporter._build_styles 集成测试 ───────────────────────────────────────


@pytest.mark.integration
class TestPDFExporterBuildStyles:
    @patch("newspaper_pdf.pdf.register_fonts", return_value={"SimHei", "SimSun", "TimesNewRoman"})
    def test_returns_dict(self, mock_register) -> None:
        exporter = PDFExporter()
        assert "title" in exporter.styles
        assert "subtitle" in exporter.styles
        assert "meta" in exporter.styles
        assert "body" in exporter.styles

    @patch("newspaper_pdf.pdf.register_fonts", return_value={"SimHei", "SimSun", "TimesNewRoman"})
    def test_title_style(self, mock_register) -> None:
        exporter = PDFExporter()
        title_style = exporter.styles["title"]
        assert title_style.fontName == "SimHei"
        assert title_style.fontSize == 20

    @patch("newspaper_pdf.pdf.register_fonts", return_value={"SimHei", "SimSun", "TimesNewRoman"})
    def test_body_style(self, mock_register) -> None:
        exporter = PDFExporter()
        body_style = exporter.styles["body"]
        assert body_style.fontName == "SimSun"
        assert body_style.fontSize == 11.5
        assert body_style.firstLineIndent == 24

    @patch("newspaper_pdf.pdf.register_fonts", return_value={"SimHei", "SimSun", "TimesNewRoman"})
    def test_style_prefix(self, mock_register) -> None:
        exporter = PDFExporter(style_prefix="JFJB")
        assert exporter.styles["title"].name.startswith("JFJB")


# ── PDFExporter.export_articles 集成测试 ─────────────────────────────────────


@pytest.mark.integration
class TestPDFExporterExportArticles:
    def _make_exporter(self) -> PDFExporter:
        """创建使用可用 TTF 字体的 PDFExporter（集成测试需要）。

        使用系统上可用的韩文字体作为 CJK 字体替代。
        """
        return PDFExporter(
            style_prefix="Test",
            custom_font_paths={
                "SimHei": Path("/usr/share/fonts/truetype/unfonts-core/UnBatangBold.ttf"),
                "SimSun": Path("/usr/share/fonts/truetype/unfonts-core/UnBatang.ttf"),
                "TimesNewRoman": Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
            },
        )

    def test_export_empty_list(self, tmp_path: Path) -> None:
        exporter = self._make_exporter()
        paths, combined = exporter.export_articles(
            articles=[],
            output_dir=tmp_path,
            export_individual=True,
            export_combined=True,
        )
        assert paths == []
        assert combined is None

    def test_export_individual_creates_files(self, tmp_path: Path) -> None:
        articles = [
            Article(
                paper_name="解放军报",
                paper_date="2026-03-10",
                paper_number="01",
                section_name="要闻",
                article_index=1,
                title="测试文章",
                subtitle="",
                author="",
                paragraphs=["正文内容。"],
                source_url="https://example.com",
            ),
        ]
        exporter = self._make_exporter()
        paths, combined = exporter.export_articles(
            articles=articles,
            output_dir=tmp_path,
            export_individual=True,
            export_combined=False,
        )
        assert len(paths) == 1
        assert paths[0].exists()
        assert paths[0].suffix == ".pdf"
        assert combined is None

    def test_export_combined_creates_file(self, tmp_path: Path) -> None:
        articles = [
            Article(
                paper_name="解放军报",
                paper_date="2026-03-10",
                paper_number="01",
                section_name="要闻",
                article_index=1,
                title="文章一",
                subtitle="",
                author="",
                paragraphs=["正文一。"],
                source_url="https://example.com/1",
            ),
            Article(
                paper_name="解放军报",
                paper_date="2026-03-10",
                paper_number="02",
                section_name="军事新闻",
                article_index=1,
                title="文章二",
                subtitle="",
                author="",
                paragraphs=["正文二。"],
                source_url="https://example.com/2",
            ),
        ]
        exporter = self._make_exporter()
        paths, combined = exporter.export_articles(
            articles=articles,
            output_dir=tmp_path,
            export_individual=False,
            export_combined=True,
        )
        assert paths == []
        assert combined is not None
        assert combined.exists()
        assert combined.suffix == ".pdf"

    def test_export_creates_section_dirs(self, tmp_path: Path) -> None:
        articles = [
            Article(
                paper_name="解放军报",
                paper_date="2026-03-10",
                paper_number="01",
                section_name="要闻",
                article_index=1,
                title="文章",
                subtitle="",
                author="",
                paragraphs=["正文。"],
                source_url="https://example.com",
            ),
        ]
        exporter = self._make_exporter()
        exporter.export_articles(
            articles=articles,
            output_dir=tmp_path,
            export_individual=True,
            export_combined=False,
        )
        # 应该创建按版面分的子目录
        section_dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
        assert len(section_dirs) >= 1
