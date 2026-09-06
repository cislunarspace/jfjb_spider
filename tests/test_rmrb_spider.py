"""人民日报爬虫解析逻辑测试。"""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from newspaper_pdf.rmrb_spider import (
    RMRBSpider,
    _attr_to_text,
    _extract_text,
)


# ── 模块级辅助函数 ──────────────────────────────────────────────────────────


@pytest.mark.unit
class TestExtractText:
    def test_with_node(self) -> None:
        soup = BeautifulSoup("<p>hello world</p>", "html.parser")
        assert _extract_text(soup.find("p")) == "hello world"

    def test_with_none(self) -> None:
        assert _extract_text(None) == ""

    def test_strips_whitespace(self) -> None:
        soup = BeautifulSoup("<p>  text  </p>", "html.parser")
        assert _extract_text(soup.find("p")) == "text"


@pytest.mark.unit
class TestAttrToText:
    def test_string(self) -> None:
        assert _attr_to_text("href") == "href"

    def test_list(self) -> None:
        assert _attr_to_text(["a", "b"]) == "a b"

    def test_none(self) -> None:
        assert _attr_to_text(None) == ""

    def test_strips(self) -> None:
        assert _attr_to_text("  value  ") == "value"


# ── RMRBSpider._build_node_url ──────────────────────────────────────────────


@pytest.mark.unit
class TestBuildNodeUrl:
    def setup_method(self) -> None:
        self.spider = RMRBSpider.__new__(RMRBSpider)
        self.spider.base_url = "https://paper.people.com.cn"

    def test_format(self) -> None:
        url = self.spider._build_node_url("2026-03-10", "01")
        assert url == "https://paper.people.com.cn/rmrb/pc/layout/202603/10/node_01.html"

    def test_pads_number(self) -> None:
        url = self.spider._build_node_url("2026-03-10", "1")
        assert "node_01.html" in url


# ── RMRBSpider._extract_article_urls ────────────────────────────────────────


@pytest.mark.unit
class TestExtractArticleUrls:
    def setup_method(self) -> None:
        self.spider = RMRBSpider.__new__(RMRBSpider)

    def test_from_news_list(self, rmrb_section_html: str) -> None:
        soup = BeautifulSoup(rmrb_section_html, "html.parser")
        urls = self.spider._extract_article_urls(
            soup, "https://paper.people.com.cn/rmrb/pc/layout/202603/10/node_01.html"
        )
        assert len(urls) == 7
        assert all("content_" in url for url in urls)

    def test_dedup(self) -> None:
        html = '''
        <div class="news-list">
            <a href="content_1.html">Article 1</a>
            <a href="content_1.html">Article 1 Duplicate</a>
            <a href="content_2.html">Article 2</a>
        </div>
        '''
        soup = BeautifulSoup(html, "html.parser")
        urls = self.spider._extract_article_urls(soup, "https://example.com/page.html")
        assert len(urls) == 2

    def test_fallback_to_area(self) -> None:
        html = '''
        <map><area href="content_1.html"><area href="content_2.html"></map>
        '''
        soup = BeautifulSoup(html, "html.parser")
        urls = self.spider._extract_article_urls(soup, "https://example.com/page.html")
        assert len(urls) == 2

    def test_empty(self) -> None:
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        urls = self.spider._extract_article_urls(soup, "https://example.com/page.html")
        assert urls == []

    def test_skips_non_content_links(self) -> None:
        html = '''
        <div class="news-list">
            <a href="other_page.html">Not an article</a>
            <a href="content_1.html">Article 1</a>
        </div>
        '''
        soup = BeautifulSoup(html, "html.parser")
        urls = self.spider._extract_article_urls(soup, "https://example.com/page.html")
        assert len(urls) == 1


# ── RMRBSpider._extract_section_meta ────────────────────────────────────────


@pytest.mark.unit
class TestExtractSectionMeta:
    def setup_method(self) -> None:
        self.spider = RMRBSpider.__new__(RMRBSpider)

    def test_with_label(self) -> None:
        html = '<div class="paper-bot"><span class="left ban">第01版：要闻</span></div>'
        soup = BeautifulSoup(html, "html.parser")
        number, name = self.spider._extract_section_meta(
            soup, "https://example.com/rmrb/pc/layout/202603/10/node_01.html"
        )
        assert number == "01"
        assert name == "要闻"

    def test_no_label(self) -> None:
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        number, name = self.spider._extract_section_meta(
            soup, "https://example.com/rmrb/pc/layout/202603/10/node_05.html"
        )
        assert number == "05"
        assert name == "第05版"

    def test_from_url(self) -> None:
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        number, name = self.spider._extract_section_meta(
            soup, "https://example.com/rmrb/pc/layout/202603/10/node_12.html"
        )
        assert number == "12"


# ── RMRBSpider._extract_subtitle ────────────────────────────────────────────


@pytest.mark.unit
class TestExtractSubtitle:
    def setup_method(self) -> None:
        self.spider = RMRBSpider.__new__(RMRBSpider)

    def test_with_p_tags(self) -> None:
        html = '<div class="article"><h2><p>副标题第一行</p><p>副标题第二行</p></h2></div>'
        soup = BeautifulSoup(html, "html.parser")
        result = self.spider._extract_subtitle(soup)
        assert "副标题第一行" in result
        assert "副标题第二行" in result

    def test_plain_text(self) -> None:
        html = '<div class="article"><h2>纯文本副标题</h2></div>'
        soup = BeautifulSoup(html, "html.parser")
        result = self.spider._extract_subtitle(soup)
        assert result == "纯文本副标题"

    def test_missing(self) -> None:
        html = '<div class="article"><h1>标题</h1></div>'
        soup = BeautifulSoup(html, "html.parser")
        result = self.spider._extract_subtitle(soup)
        assert result == ""


# ── RMRBSpider._extract_author ──────────────────────────────────────────────


@pytest.mark.unit
class TestExtractAuthor:
    def setup_method(self) -> None:
        self.spider = RMRBSpider.__new__(RMRBSpider)

    def test_from_h3(self) -> None:
        html = '<div class="article"><h3>人民日报记者 王五</h3></div>'
        soup = BeautifulSoup(html, "html.parser")
        result = self.spider._extract_author(soup)
        assert result == "人民日报记者 王五"

    def test_from_meta(self) -> None:
        html = '<meta name="author" content="张三">'
        soup = BeautifulSoup(html, "html.parser")
        result = self.spider._extract_author(soup)
        assert result == "张三"

    def test_missing(self) -> None:
        html = '<div class="article"><h1>标题</h1></div>'
        soup = BeautifulSoup(html, "html.parser")
        result = self.spider._extract_author(soup)
        assert result == ""

    def test_h3_priority_over_meta(self) -> None:
        html = '''
        <div class="article"><h3>李四</h3></div>
        <meta name="author" content="张三">
        '''
        soup = BeautifulSoup(html, "html.parser")
        result = self.spider._extract_author(soup)
        assert result == "李四"
