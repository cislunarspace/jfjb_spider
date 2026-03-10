from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer


DEFAULT_BASE_URL = "https://paper.people.com.cn"
LAYOUT_ENTRY_URL = f"{DEFAULT_BASE_URL}/rmrb/pc/layout/"
REQUEST_TIMEOUT = 30


@dataclass(slots=True)
class Article:
    paper_name: str
    paper_date: str
    paper_number: str
    section_name: str
    article_index: int
    title: str
    subtitle: str
    author: str
    paragraphs: list[str]
    source_url: str


class RMRBSpider:
    paper_name = "人民日报"
    HTML_CHARSET_PATTERN = re.compile(rb"charset=([A-Za-z0-9_\-]+)", re.IGNORECASE)

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/136.0.0.0 Safari/537.36"
                )
            }
        )

    def resolve_paper_date(self, target_date: str | None) -> str:
        if target_date:
            datetime.strptime(target_date, "%Y-%m-%d")
            return target_date

        html_text = self._fetch_html(LAYOUT_ENTRY_URL)
        match = re.search(r"(\d{6})/(\d{2})/node_\d+\.html", html_text)
        if not match:
            raise RuntimeError("未能从人民日报入口页解析出当天版面日期")

        year_month = match.group(1)
        day = match.group(2)
        return f"{year_month[:4]}-{year_month[4:]}-{day}"

    def fetch_articles(self, paper_date: str) -> list[Article]:
        section_urls = self._discover_section_urls(paper_date)
        articles: list[Article] = []

        for section_url in section_urls:
            articles.extend(self._parse_section_articles(section_url, paper_date))

        return articles

    def _discover_section_urls(self, paper_date: str) -> list[str]:
        first_node_url = self._build_node_url(paper_date, "01")
        soup = self._fetch_soup(first_node_url)

        section_numbers: set[str] = set()
        for anchor in soup.select("a[href]"):
            href = self._attr_to_text(anchor.get("href"))
            match = re.search(r"node_(\d+)\.html$", href)
            if not match:
                continue
            section_numbers.add(match.group(1))

        if not section_numbers:
            raise RuntimeError("未能从人民日报版面页提取版面链接")

        return [
            self._build_node_url(paper_date, key)
            for key in sorted(section_numbers, key=lambda item: int(item))
        ]

    def _parse_section_articles(
        self, section_url: str, paper_date: str
    ) -> list[Article]:
        soup = self._fetch_soup(section_url)

        paper_number, section_name = self._extract_section_meta(soup, section_url)
        article_urls = self._extract_article_urls(soup, section_url)

        articles: list[Article] = []
        for article_index, article_url in enumerate(article_urls, start=1):
            articles.append(
                self._parse_article(
                    article_url=article_url,
                    paper_date=paper_date,
                    paper_number=paper_number,
                    section_name=section_name,
                    article_index=article_index,
                )
            )

        return articles

    def _extract_section_meta(
        self, soup: BeautifulSoup, section_url: str
    ) -> tuple[str, str]:
        section_label = self._normalize_space(
            self._extract_text(soup.select_one(".paper-bot .left.ban"))
        )
        url_match = re.search(r"node_(\d+)\.html$", section_url)
        paper_number = url_match.group(1) if url_match else "00"
        paper_number = paper_number.zfill(2)

        if section_label:
            normalized_label = section_label.replace(":", "：")
            if "：" in normalized_label:
                _, raw_section_name = normalized_label.split("：", 1)
                section_name = self._normalize_space(raw_section_name)
                return paper_number, section_name or f"第{paper_number}版"

        return paper_number, f"第{paper_number}版"

    def _extract_article_urls(self, soup: BeautifulSoup, section_url: str) -> list[str]:
        article_urls: list[str] = []
        seen: set[str] = set()

        for anchor in soup.select(".news-list a[href]"):
            href = self._attr_to_text(anchor.get("href"))
            if "content_" not in href:
                continue
            article_url = urljoin(section_url, href)
            if article_url in seen:
                continue
            seen.add(article_url)
            article_urls.append(article_url)

        if article_urls:
            return article_urls

        for anchor in soup.select("area[href]"):
            href = self._attr_to_text(anchor.get("href"))
            if "content_" not in href:
                continue
            article_url = urljoin(section_url, href)
            if article_url in seen:
                continue
            seen.add(article_url)
            article_urls.append(article_url)

        return article_urls

    def _parse_article(
        self,
        article_url: str,
        paper_date: str,
        paper_number: str,
        section_name: str,
        article_index: int,
    ) -> Article:
        soup = self._fetch_soup(article_url)

        title = self._normalize_space(
            self._extract_text(soup.select_one(".article h1"))
        )
        if not title:
            raise RuntimeError(f"未能解析文章标题: {article_url}")

        subtitle = self._extract_subtitle(soup)
        author = self._extract_author(soup)

        body_container = soup.select_one("#articleContent") or soup.select_one("#ozoom")
        if body_container is None:
            raise RuntimeError(f"未能解析正文容器: {article_url}")
        paragraphs = self._html_to_paragraphs(str(body_container))
        if author:
            paragraphs.insert(0, f"作者：{author}")

        return Article(
            paper_name=self.paper_name,
            paper_date=paper_date,
            paper_number=paper_number,
            section_name=section_name,
            article_index=article_index,
            title=title,
            subtitle=subtitle,
            author=author,
            paragraphs=paragraphs,
            source_url=article_url,
        )

    def _extract_subtitle(self, soup: BeautifulSoup) -> str:
        subtitle_node = soup.select_one(".article h2")
        if subtitle_node is None:
            return ""

        lines = []
        paragraphs = subtitle_node.find_all("p")
        if paragraphs:
            for paragraph in paragraphs:
                text = self._normalize_space(paragraph.get_text(" ", strip=True))
                if text:
                    lines.append(text)
        else:
            text = self._normalize_space(subtitle_node.get_text("\n", strip=True))
            if text:
                lines.append(text)

        return "\n".join(lines)

    def _extract_author(self, soup: BeautifulSoup) -> str:
        author = self._normalize_space(
            self._extract_text(soup.select_one(".article h3"))
        )
        if author:
            return author

        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author is not None:
            return self._normalize_space(self._attr_to_text(meta_author.get("content")))

        return ""

    def _build_node_url(self, paper_date: str, paper_number: str) -> str:
        year, month, day = paper_date.split("-")
        return (
            f"{self.base_url}/rmrb/pc/layout/{year}{month}/{day}/"
            f"node_{paper_number.zfill(2)}.html"
        )

    def _fetch_soup(self, url: str) -> BeautifulSoup:
        return BeautifulSoup(self._fetch_html(url), "html.parser")

    def _fetch_html(self, url: str) -> str:
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return self._decode_html(response)

    def _decode_html(self, response: requests.Response) -> str:
        raw = response.content
        charset = self._detect_charset(raw)
        if charset:
            return raw.decode(charset, errors="replace")

        apparent_encoding = response.apparent_encoding
        if apparent_encoding:
            return raw.decode(apparent_encoding, errors="replace")

        encoding = response.encoding or "utf-8"
        return raw.decode(encoding, errors="replace")

    def _detect_charset(self, raw: bytes) -> str | None:
        match = self.HTML_CHARSET_PATTERN.search(raw[:4096])
        if not match:
            return None

        charset = match.group(1).decode("ascii", errors="ignore").lower()
        return charset or None

    @staticmethod
    def _extract_text(node: Tag | None) -> str:
        if node is None:
            return ""
        return node.get_text(" ", strip=True)

    @staticmethod
    def _attr_to_text(value: object) -> str:
        if isinstance(value, list):
            return " ".join(str(item) for item in value).strip()
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _normalize_space(text: str) -> str:
        return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()

    def _html_to_paragraphs(self, raw_html: str) -> list[str]:
        if not raw_html.strip():
            return ["正文为空"]

        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()

        paragraphs: list[str] = []
        for paragraph in soup.find_all("p"):
            text = self._normalize_space(paragraph.get_text(" ", strip=True))
            if text:
                paragraphs.append(text)

        if paragraphs:
            return paragraphs

        fallback = self._normalize_space(soup.get_text("\n", strip=True))
        return [fallback] if fallback else ["正文为空"]


class PDFExporter:
    def __init__(self) -> None:
        self.styles = self._build_styles()

    def export_articles(
        self,
        articles: list[Article],
        output_dir: Path,
        export_individual: bool,
        export_combined: bool,
    ) -> tuple[list[Path], Path | None]:
        output_dir.mkdir(parents=True, exist_ok=True)
        article_paths: list[Path] = []

        if export_individual:
            for article in articles:
                section_dir = output_dir / self._safe_filename(
                    f"第{article.paper_number}版_{article.section_name}"
                )
                section_dir.mkdir(parents=True, exist_ok=True)
                filename = self._safe_filename(
                    f"{article.article_index:02d}_{article.title}.pdf"
                )
                pdf_path = section_dir / filename
                self._build_pdf(
                    pdf_path, self._build_article_story(article, include_header=True)
                )
                article_paths.append(pdf_path)

        combined_path: Path | None = None
        if export_combined:
            combined_path = output_dir / self._safe_filename(
                f"{articles[0].paper_name}_{articles[0].paper_date}_全集.pdf"
            )
            story = []
            current_section: tuple[str, str] | None = None
            for index, article in enumerate(articles):
                section = (article.paper_number, article.section_name)
                if section != current_section:
                    story.append(
                        BookmarkFlowable(
                            title=f"第{article.paper_number}版 {article.section_name}",
                            key=f"section-{article.paper_number}",
                            level=0,
                        )
                    )
                    current_section = section
                story.extend(
                    self._build_article_story(
                        article,
                        include_header=True,
                        bookmark_title=article.title,
                        bookmark_key=f"article-{index + 1:04d}",
                    )
                )
                if index != len(articles) - 1:
                    story.append(PageBreak())
            self._build_pdf(combined_path, story)

        return article_paths, combined_path

    def _build_styles(self) -> dict[str, ParagraphStyle]:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        except KeyError:
            pass

        base_font = "STSong-Light"
        sample = getSampleStyleSheet()
        return {
            "title": ParagraphStyle(
                "RMRBTitle",
                parent=sample["Title"],
                fontName=base_font,
                fontSize=20,
                leading=28,
                alignment=TA_CENTER,
                textColor=HexColor("#111827"),
                wordWrap="CJK",
                spaceAfter=8,
            ),
            "subtitle": ParagraphStyle(
                "RMRBSubtitle",
                parent=sample["Normal"],
                fontName=base_font,
                fontSize=11.5,
                leading=18,
                alignment=TA_CENTER,
                textColor=HexColor("#4b5563"),
                wordWrap="CJK",
                spaceAfter=10,
            ),
            "meta": ParagraphStyle(
                "RMRBMeta",
                parent=sample["Normal"],
                fontName=base_font,
                fontSize=9.5,
                leading=14,
                textColor=HexColor("#6b7280"),
                wordWrap="CJK",
                spaceAfter=6,
            ),
            "body": ParagraphStyle(
                "RMRBBody",
                parent=sample["BodyText"],
                fontName=base_font,
                fontSize=11.5,
                leading=20,
                firstLineIndent=24,
                textColor=HexColor("#111827"),
                wordWrap="CJK",
                spaceAfter=6,
            ),
        }

    def _build_article_story(
        self,
        article: Article,
        include_header: bool,
        bookmark_title: str | None = None,
        bookmark_key: str | None = None,
    ) -> list:
        story = []
        title = self._escape(article.title)
        subtitle = self._escape(article.subtitle)
        page_label = self._escape(
            f"第{article.paper_number}版 | {article.section_name}"
        )
        source_url = self._escape(article.source_url)

        if include_header:
            title_paragraph = Paragraph(title, self.styles["title"])
            if bookmark_title and bookmark_key:
                setattr(title_paragraph, "bookmark_title", bookmark_title)
                setattr(title_paragraph, "bookmark_key", bookmark_key)
                setattr(title_paragraph, "bookmark_level", 1)
            story.append(title_paragraph)
            if subtitle:
                story.append(Paragraph(subtitle, self.styles["subtitle"]))
            story.append(Paragraph(page_label, self.styles["meta"]))
            story.append(Paragraph(f"来源：{source_url}", self.styles["meta"]))
            story.append(Spacer(1, 4 * mm))

        for paragraph in article.paragraphs:
            story.append(Paragraph(self._escape(paragraph), self.styles["body"]))

        return story

    def _build_pdf(self, pdf_path: Path, story: list) -> None:
        document = BookmarkDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=pdf_path.stem,
        )
        document.build(story)

    @staticmethod
    def _escape(text: str) -> str:
        return html.escape(text, quote=False).replace("\n", "<br/>")

    @staticmethod
    def _safe_filename(value: str) -> str:
        value = re.sub(r"[\\/:*?\"<>|]", "_", value)
        value = re.sub(r"\s+", " ", value).strip().rstrip(".")
        return value[:180] if len(value) > 180 else value


class BookmarkDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable: object) -> None:
        bookmark_title = getattr(flowable, "bookmark_title", None)
        bookmark_key = getattr(flowable, "bookmark_key", None)
        bookmark_level = getattr(flowable, "bookmark_level", None)

        if not bookmark_title or not bookmark_key or bookmark_level is None:
            return

        if not getattr(self, "_outline_enabled", False):
            self.canv.showOutline()
            self._outline_enabled = True

        self.canv.bookmarkPage(bookmark_key)
        self.canv.addOutlineEntry(bookmark_title, bookmark_key, bookmark_level)


class BookmarkFlowable(Flowable):
    def __init__(self, title: str, key: str, level: int) -> None:
        super().__init__()
        self.bookmark_title = title
        self.bookmark_key = key
        self.bookmark_level = level

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        return (0, 0)

    def draw(self) -> None:
        return None


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="抓取人民日报当天所有版面文章，并导出为 PDF。"
    )
    parser.add_argument(
        "--date",
        help="指定报纸日期，格式为 YYYY-MM-DD；不传时自动抓取当天最新版。",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"站点根地址，默认 {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--out-dir",
        default="output/rmrb",
        help="输出目录，默认 output/rmrb",
    )
    parser.add_argument(
        "--combined-only",
        action="store_true",
        help="仅输出汇总 PDF。",
    )
    parser.add_argument(
        "--individual-only",
        action="store_true",
        help="仅输出单篇 PDF。",
    )
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.combined_only and args.individual_only:
        parser.error("--combined-only 与 --individual-only 不能同时使用")

    export_individual = not args.combined_only
    export_combined = not args.individual_only

    spider = RMRBSpider(base_url=args.base_url)
    paper_date = spider.resolve_paper_date(args.date)
    articles = spider.fetch_articles(paper_date)

    if not articles:
        raise RuntimeError("当天未解析到任何文章")

    output_dir = Path(args.out_dir) / paper_date
    exporter = PDFExporter()
    article_paths, combined_path = exporter.export_articles(
        articles=articles,
        output_dir=output_dir,
        export_individual=export_individual,
        export_combined=export_combined,
    )

    print(f"日期: {paper_date}")
    print(f"文章数: {len(articles)}")
    if article_paths:
        print(f"单篇 PDF: {len(article_paths)} 个，输出目录: {output_dir}")
    if combined_path:
        print(f"汇总 PDF: {combined_path}")


if __name__ == "__main__":
    main()
