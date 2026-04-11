"""Article 数据类测试。"""

from __future__ import annotations

import pytest

from newspaper_pdf.models import Article


@pytest.mark.unit
class TestArticle:
    def test_creation(self) -> None:
        article = Article(
            paper_name="解放军报",
            paper_date="2026-03-10",
            paper_number="01",
            section_name="要闻",
            article_index=1,
            title="测试标题",
            subtitle="测试副标题",
            author="张三",
            paragraphs=["段落一", "段落二"],
            source_url="https://example.com",
        )
        assert article.paper_name == "解放军报"
        assert article.paper_date == "2026-03-10"
        assert article.paper_number == "01"
        assert article.section_name == "要闻"
        assert article.article_index == 1
        assert article.title == "测试标题"
        assert article.subtitle == "测试副标题"
        assert article.author == "张三"
        assert article.paragraphs == ["段落一", "段落二"]
        assert article.source_url == "https://example.com"

    def test_defaults(self) -> None:
        article = Article(
            paper_name="人民日报",
            paper_date="2026-01-01",
            paper_number="02",
            section_name="国内",
            article_index=1,
            title="标题",
            subtitle="",
            author="",
            paragraphs=[],
            source_url="",
        )
        assert article.subtitle == ""
        assert article.author == ""
        assert article.paragraphs == []

    def test_equality(self) -> None:
        kwargs = dict(
            paper_name="解放军报",
            paper_date="2026-03-10",
            paper_number="01",
            section_name="要闻",
            article_index=1,
            title="标题",
            subtitle="",
            author="",
            paragraphs=["p1"],
            source_url="https://example.com",
        )
        assert Article(**kwargs) == Article(**kwargs)

    def test_slots(self) -> None:
        article = Article(
            paper_name="解放军报",
            paper_date="2026-03-10",
            paper_number="01",
            section_name="要闻",
            article_index=1,
            title="标题",
            subtitle="",
            author="",
            paragraphs=[],
            source_url="",
        )
        assert hasattr(article, "__slots__")
        with pytest.raises(AttributeError):
            article.nonexistent = "value"  # type: ignore[attr-defined]
