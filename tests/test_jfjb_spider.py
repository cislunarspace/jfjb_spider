"""解放军报爬虫解析逻辑测试。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from newspaper_pdf.jfjb_spider import JFJBSpider, generate_date_range


# ── generate_date_range ─────────────────────────────────────────────────────


@pytest.mark.unit
class TestGenerateDateRange:
    def test_single_day(self) -> None:
        result = generate_date_range("2026-03-10", "2026-03-10")
        assert result == ["2026-03-10"]

    def test_multiple_days(self) -> None:
        result = generate_date_range("2026-03-01", "2026-03-05")
        assert len(result) == 5
        assert result[0] == "2026-03-01"
        assert result[-1] == "2026-03-05"

    def test_start_after_end(self) -> None:
        with pytest.raises(ValueError, match="晚于"):
            generate_date_range("2026-03-10", "2026-03-05")

    def test_format(self) -> None:
        result = generate_date_range("2026-03-01", "2026-03-03")
        for d in result:
            datetime.strptime(d, "%Y-%m-%d")  # 验证格式

    def test_cross_month(self) -> None:
        result = generate_date_range("2026-03-30", "2026-04-02")
        assert len(result) == 4
        assert result == ["2026-03-30", "2026-03-31", "2026-04-01", "2026-04-02"]


# ── JFJBSpider._sorted_papers ───────────────────────────────────────────────


@pytest.mark.unit
class TestSortedPapers:
    def test_numeric(self) -> None:
        papers = [
            {"paperNumber": "02"},
            {"paperNumber": "01"},
            {"paperNumber": "10"},
        ]
        result = JFJBSpider._sorted_papers(papers)
        numbers = [p["paperNumber"] for p in result]
        assert numbers == ["01", "02", "10"]

    def test_non_numeric_fallback(self) -> None:
        papers = [{"paperNumber": "special"}, {"paperNumber": "01"}]
        result = JFJBSpider._sorted_papers(papers)
        assert result[0]["paperNumber"] == "01"
        assert result[1]["paperNumber"] == "special"

    def test_missing_paper_number(self) -> None:
        papers = [{}, {"paperNumber": "01"}]
        result = JFJBSpider._sorted_papers(papers)
        assert result[0]["paperNumber"] == "01"

    def test_empty(self) -> None:
        assert JFJBSpider._sorted_papers([]) == []


# ── JFJBSpider._pick_subtitle ───────────────────────────────────────────────


@pytest.mark.unit
class TestPickSubtitle:
    def setup_method(self) -> None:
        self.spider = JFJBSpider.__new__(JFJBSpider)

    def test_from_title2(self) -> None:
        result = self.spider._pick_subtitle({"title2": "副标题", "guideTitle": ""})
        assert result == "副标题"

    def test_from_guide_title(self) -> None:
        result = self.spider._pick_subtitle({"title2": "", "guideTitle": "导读内容"})
        assert result == "导读内容"

    def test_title2_priority(self) -> None:
        result = self.spider._pick_subtitle({"title2": "副标题", "guideTitle": "导读"})
        assert result == "副标题"

    def test_empty(self) -> None:
        result = self.spider._pick_subtitle({"title2": "", "guideTitle": ""})
        assert result == ""

    def test_whitespace_only(self) -> None:
        result = self.spider._pick_subtitle({"title2": "   ", "guideTitle": ""})
        assert result == ""


# ── JFJBSpider.parse_articles ───────────────────────────────────────────────


@pytest.mark.unit
class TestParseArticles:
    def setup_method(self) -> None:
        self.spider = JFJBSpider.__new__(JFJBSpider)
        self.spider.base_url = "https://www.81.cn"

    def test_returns_articles(self, jfjb_payload: dict) -> None:
        articles = self.spider.parse_articles(jfjb_payload, "2026-03-10")
        assert len(articles) > 0

    def test_correct_paper_name(self, jfjb_payload: dict) -> None:
        articles = self.spider.parse_articles(jfjb_payload, "2026-03-10")
        for article in articles:
            assert article.paper_name == "解放军报"

    def test_correct_date(self, jfjb_payload: dict) -> None:
        articles = self.spider.parse_articles(jfjb_payload, "2026-03-10")
        for article in articles:
            assert article.paper_date == "2026-03-10"

    def test_author_inserted(self, jfjb_payload: dict) -> None:
        articles = self.spider.parse_articles(jfjb_payload, "2026-03-10")
        # 第一篇文章有作者 "张三"
        first = articles[0]
        assert first.paragraphs[0].startswith("作者：")

    def test_empty_payload(self) -> None:
        articles = self.spider.parse_articles({}, "2026-03-10")
        assert articles == []

    def test_empty_paper_info(self) -> None:
        articles = self.spider.parse_articles({"paperInfo": []}, "2026-03-10")
        assert articles == []

    def test_source_url_format(self, jfjb_payload: dict) -> None:
        articles = self.spider.parse_articles(jfjb_payload, "2026-03-10")
        for article in articles:
            assert "paperName=jfjb" in article.source_url
            assert "paperDate=2026-03-10" in article.source_url

    def test_subtitle_from_title2(self, jfjb_payload: dict) -> None:
        articles = self.spider.parse_articles(jfjb_payload, "2026-03-10")
        # 第一篇文章有 title2 "测试副标题一"
        assert articles[0].subtitle == "测试副标题一"

    def test_subtitle_from_guide_title(self, jfjb_payload: dict) -> None:
        articles = self.spider.parse_articles(jfjb_payload, "2026-03-10")
        # 第二篇文章有 guideTitle "导读内容"
        assert articles[1].subtitle == "导读内容"

    def test_sorted_by_paper_number(self, jfjb_payload: dict) -> None:
        articles = self.spider.parse_articles(jfjb_payload, "2026-03-10")
        paper_numbers = [a.paper_number for a in articles]
        # 应该先 01 版的文章，然后 02 版
        assert paper_numbers[0] == "01"
        assert paper_numbers[-1] == "02"

    def test_article_index_per_section(self, jfjb_payload: dict) -> None:
        articles = self.spider.parse_articles(jfjb_payload, "2026-03-10")
        # 01 版有 2 篇文章，02 版有 1 篇
        section_01 = [a for a in articles if a.paper_number == "01"]
        section_02 = [a for a in articles if a.paper_number == "02"]
        assert section_01[0].article_index == 1
        assert section_01[1].article_index == 2
        assert section_02[0].article_index == 1
