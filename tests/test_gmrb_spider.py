"""光明日报爬虫解析逻辑测试。"""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from newspaper_pdf.gmrb_spider import GMRBSpider


def _make_spider() -> GMRBSpider:
    return GMRBSpider()


# ── GMRBSpider._build_node_url ──────────────────────────────────────────────


@pytest.mark.unit
class TestBuildNodeUrl:
    def test_builds_layout_url(self) -> None:
        spider = _make_spider()
        url = spider._build_node_url("2026-09-06", "1")
        assert url == "https://epaper.gmw.cn/gmrb/html/layout/202609/06/node_01.html"

    def test_zero_pads_number(self) -> None:
        spider = _make_spider()
        url = spider._build_node_url("2026-09-06", "12")
        assert url.endswith("node_12.html")


# ── GMRBSpider.resolve_paper_date ───────────────────────────────────────────


@pytest.mark.unit
class TestResolvePaperDate:
    def test_explicit_date_passthrough(self) -> None:
        spider = _make_spider()
        assert spider.resolve_paper_date("2026-09-06") == "2026-09-06"

    def test_invalid_date_raises(self) -> None:
        spider = _make_spider()
        with pytest.raises(ValueError):
            spider.resolve_paper_date("2026/09/06")

    def test_extracts_latest_date_from_entry(self, mocker) -> None:
        spider = _make_spider()
        mocker.patch.object(
            spider,
            "_fetch_html",
            return_value='<a href="202609/06/node_01.html">头版</a>',
        )
        assert spider.resolve_paper_date(None) == "2026-09-06"

    def test_no_date_in_entry_raises(self, mocker) -> None:
        spider = _make_spider()
        mocker.patch.object(spider, "_fetch_html", return_value="<html></html>")
        with pytest.raises(RuntimeError):
            spider.resolve_paper_date(None)


# ── GMRBSpider._extract_section_meta ────────────────────────────────────────


@pytest.mark.unit
class TestExtractSectionMeta:
    def setup_method(self) -> None:
        self.spider = _make_spider()
        self.section_url = "https://epaper.gmw.cn/gmrb/html/layout/202609/06/node_01.html"

    def _soup_with_label(self, label_html: str) -> BeautifulSoup:
        html = f'<html><body><div class="m-title-list"><div class="m-type">{label_html}</div></div></body></html>'
        return BeautifulSoup(html, "html.parser")

    def test_extracts_number_and_name(self) -> None:
        soup = self._soup_with_label("<span>01版:</span><span>头版</span>")
        number, name = self.spider._extract_section_meta(soup, self.section_url)
        assert number == "01"
        assert name == "头版"

    def test_missing_label_falls_back(self) -> None:
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        number, name = self.spider._extract_section_meta(soup, self.section_url)
        assert number == "01"
        assert name == "第01版"

    def test_url_without_number_uses_default(self) -> None:
        soup = self._soup_with_label("<span>01版:</span><span>头版</span>")
        number, _ = self.spider._extract_section_meta(soup, "https://epaper.gmw.cn/other.html")
        assert number == "00"


# ── GMRBSpider._extract_article_urls ────────────────────────────────────────


@pytest.mark.unit
class TestExtractArticleUrls:
    def setup_method(self) -> None:
        self.spider = _make_spider()
        self.section_url = "https://epaper.gmw.cn/gmrb/html/layout/202609/06/node_01.html"

    def _soup_with_list(self, items: list[str]) -> BeautifulSoup:
        lis = "".join(f'<li><a href="{href}"><p>{text}</p></a></li>' for href, text in items)
        html = f'<html><body><div class="m-title-list"><ul>{lis}</ul></div></body></html>'
        return BeautifulSoup(html, "html.parser")

    def test_extracts_and_resolves_relative_links(self) -> None:
        soup = self._soup_with_list(
            [("../../../content/202609/06/content_24110.html", "文章一")]
        )
        urls = self.spider._extract_article_urls(soup, self.section_url)
        assert urls == [
            "https://epaper.gmw.cn/gmrb/html/content/202609/06/content_24110.html"
        ]

    def test_ignores_non_article_links(self) -> None:
        soup = self._soup_with_list(
            [
                ("node_02.html", "其他版面"),
                ("javascript:;", "占位"),
                ("../../../content/202609/06/content_24111.html", "文章二"),
            ]
        )
        urls = self.spider._extract_article_urls(soup, self.section_url)
        assert len(urls) == 1
        assert urls[0].endswith("content_24111.html")

    def test_deduplicates(self) -> None:
        href = "../../../content/202609/06/content_24110.html"
        soup = self._soup_with_list([(href, "文章一"), (href, "文章一重复")])
        urls = self.spider._extract_article_urls(soup, self.section_url)
        assert len(urls) == 1

    def test_empty_list_returns_empty(self) -> None:
        soup = BeautifulSoup('<div class="m-title-list"><ul></ul></div>', "html.parser")
        assert self.spider._extract_article_urls(soup, self.section_url) == []


# ── GMRBSpider._extract_subtitle ────────────────────────────────────────────


@pytest.mark.unit
class TestExtractSubtitle:
    def setup_method(self) -> None:
        self.spider = _make_spider()

    def test_merges_intro_and_subtitle(self) -> None:
        html = "<html><body><h3>引题文字</h3><h1>主标题</h1><h2>副题文字</h2></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        assert self.spider._extract_subtitle(soup) == "引题文字\n副题文字"

    def test_subtitle_only(self) -> None:
        html = "<html><body><h1>主标题</h1><h2>副题文字</h2></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        assert self.spider._extract_subtitle(soup) == "副题文字"

    def test_empty_when_no_headers(self) -> None:
        html = "<html><body><h1>主标题</h1></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        assert self.spider._extract_subtitle(soup) == ""


# ── GMRBSpider._extract_author ──────────────────────────────────────────────


@pytest.mark.unit
class TestExtractAuthor:
    def setup_method(self) -> None:
        self.spider = _make_spider()

    def _soup_with_author(self, author_html: str) -> BeautifulSoup:
        html = f'<html><body><span class="m-article-author">{author_html}</span></body></html>'
        return BeautifulSoup(html, "html.parser")

    def test_strips_prefix(self) -> None:
        soup = self._soup_with_author("作者：本报记者 张三")
        assert self.spider._extract_author(soup) == "本报记者 张三"

    def test_handles_halfwidth_colon(self) -> None:
        soup = self._soup_with_author("作者: 李四")
        assert self.spider._extract_author(soup) == "李四"

    def test_missing_author_returns_empty(self) -> None:
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        assert self.spider._extract_author(soup) == ""
