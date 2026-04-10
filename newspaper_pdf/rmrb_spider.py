"""人民日报（people.com.cn）爬虫模块。

通过 HTML 页面抓取人民日报各版面文章，并导出为格式化的 PDF 文件。

数据源特点：
- 通过 HTML 页面解析获取版面和文章数据
- 从版面导航页提取版面链接，再从各版面页提取文章链接
- 支持自动编码检测（charset 元标签 + requests 的 apparent_encoding）

使用方式：
    python rmrb.py                         # 抓取当天
    python rmrb.py --date 2026-03-10       # 指定日期
"""

from __future__ import annotations

import argparse
import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from newspaper_pdf.cli import add_common_arguments, build_font_paths, setup_logging
from newspaper_pdf.models import Article
from newspaper_pdf.network import create_session, retry_get
from newspaper_pdf.pdf import PDFExporter
from newspaper_pdf.utils import html_to_paragraphs, normalize_space

logger = logging.getLogger(__name__)

# 人民日报站点默认根地址
DEFAULT_BASE_URL = "https://paper.people.com.cn"

# 版面导航入口 URL
LAYOUT_ENTRY_URL = f"{DEFAULT_BASE_URL}/rmrb/pc/layout/"


class RMRBSpider:
    """人民日报爬虫。

    通过 HTML 页面解析获取报纸版面和文章数据。
    由于人民日报网站使用 HTML 而非 JSON API，需要多步解析：
    1. 从入口页获取当天日期和版面列表
    2. 从各版面页提取文章链接
    3. 从各文章页提取标题、作者和正文

    Attributes:
        paper_name: 报纸名称，固定为 "人民日报"
        base_url: 站点根地址
        session: HTTP 会话对象
    """

    _PAPER_NAME = "人民日报"

    # 从 HTML meta 标签或 HTTP 头部提取字符集的正则
    _HTML_CHARSET_PATTERN = re.compile(rb"charset=([A-Za-z0-9_\-]+)", re.IGNORECASE)

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = create_session()

    def resolve_paper_date(self, target_date: str | None) -> str:
        """解析目标报纸日期。

        如果用户指定了日期，验证格式后直接返回。
        如果未指定，从版面导航入口页的 URL 模式中提取当天日期。

        Args:
            target_date: 用户指定的日期字符串（YYYY-MM-DD），为 None 时自动获取

        Returns:
            报纸日期字符串（YYYY-MM-DD）

        Raises:
            ValueError: 日期格式不正确
            RuntimeError: 无法从入口页解析日期
        """
        if target_date:
            datetime.strptime(target_date, "%Y-%m-%d")
            return target_date

        # 从版面导航入口页的链接中提取日期
        # 链接格式如：202603/10/node_01.html
        html_text = self._fetch_html(LAYOUT_ENTRY_URL)
        match = re.search(r"(\d{6})/(\d{2})/node_\d+\.html", html_text)
        if not match:
            raise RuntimeError("未能从人民日报入口页解析出当天版面日期")

        year_month = match.group(1)
        day = match.group(2)
        return f"{year_month[:4]}-{year_month[4:]}-{day}"

    def fetch_articles(self, paper_date: str) -> list[Article]:
        """获取指定日期的所有文章。

        处理流程：
        1. 发现所有版面页 URL
        2. 从每个版面页提取文章链接
        3. 逐个解析文章内容

        Args:
            paper_date: 报纸日期（YYYY-MM-DD）

        Returns:
            文章列表
        """
        section_urls = self._discover_section_urls(paper_date)
        articles: list[Article] = []

        for section_url in section_urls:
            articles.extend(self._parse_section_articles(section_url, paper_date))

        return articles

    def _discover_section_urls(self, paper_date: str) -> list[str]:
        """发现指定日期的所有版面页 URL。

        通过访问第一个版面页（node_01），解析页面中的所有版面链接。

        Args:
            paper_date: 报纸日期

        Returns:
            版面页 URL 列表（按版面编号排序）

        Raises:
            RuntimeError: 未找到任何版面链接
        """
        first_node_url = self._build_node_url(paper_date, "01")
        soup = self._fetch_soup(first_node_url)

        # 提取所有版面链接中的版面编号
        section_numbers: set[str] = set()
        for anchor in soup.select("a[href]"):
            href = _attr_to_text(anchor.get("href"))
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
        """从版面页解析所有文章。

        Args:
            section_url: 版面页 URL
            paper_date: 报纸日期

        Returns:
            该版面的文章列表
        """
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
        """从版面页提取版面编号和名称。

        Args:
            soup: 版面页 BeautifulSoup 对象
            section_url: 版面页 URL

        Returns:
            (版面编号, 版面名称) 元组
        """
        section_label = normalize_space(
            _extract_text(soup.select_one(".paper-bot .left.ban"))
        )
        url_match = re.search(r"node_(\d+)\.html$", section_url)
        paper_number = url_match.group(1) if url_match else "00"
        paper_number = paper_number.zfill(2)

        if section_label:
            normalized_label = section_label.replace(":", "：")
            if "：" in normalized_label:
                _, raw_section_name = normalized_label.split("：", 1)
                section_name = normalize_space(raw_section_name)
                return paper_number, section_name or f"第{paper_number}版"

        return paper_number, f"第{paper_number}版"

    def _extract_article_urls(self, soup: BeautifulSoup, section_url: str) -> list[str]:
        """从版面页提取文章链接列表。

        优先从 .news-list 中的链接提取，回退到 <area> 标签。

        Args:
            soup: 版面页 BeautifulSoup 对象
            section_url: 版面页 URL（用于解析相对链接）

        Returns:
            去重后的文章 URL 列表
        """
        article_urls: list[str] = []
        seen: set[str] = set()

        # 优先：文章列表中的链接
        for anchor in soup.select(".news-list a[href]"):
            href = _attr_to_text(anchor.get("href"))
            if "content_" not in href:
                continue
            article_url = urljoin(section_url, href)
            if article_url in seen:
                continue
            seen.add(article_url)
            article_urls.append(article_url)

        if article_urls:
            return article_urls

        # 回退：图片热区链接（部分旧版版面使用 <area> 标签）
        for anchor in soup.select("area[href]"):
            href = _attr_to_text(anchor.get("href"))
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
        """从文章页解析单篇文章。

        Args:
            article_url: 文章页 URL
            paper_date: 报纸日期
            paper_number: 版面编号
            section_name: 版面名称
            article_index: 文章序号

        Returns:
            文章数据对象

        Raises:
            RuntimeError: 无法解析标题或正文
        """
        soup = self._fetch_soup(article_url)

        title = normalize_space(
            _extract_text(soup.select_one(".article h1"))
        )
        if not title:
            raise RuntimeError(f"未能解析文章标题: {article_url}")

        subtitle = self._extract_subtitle(soup)
        author = self._extract_author(soup)

        # 查找正文容器（优先 #articleContent，回退 #ozoom）
        body_container = soup.select_one("#articleContent") or soup.select_one("#ozoom")
        if body_container is None:
            raise RuntimeError(f"未能解析正文容器: {article_url}")
        paragraphs = html_to_paragraphs(str(body_container))
        if author:
            paragraphs.insert(0, f"作者：{author}")

        return Article(
            paper_name=self._PAPER_NAME,
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
        """从文章页提取副标题。

        Args:
            soup: 文章页 BeautifulSoup 对象

        Returns:
            副标题文本，无则为空字符串
        """
        subtitle_node = soup.select_one(".article h2")
        if subtitle_node is None:
            return ""

        lines: list[str] = []
        paragraphs = subtitle_node.find_all("p")
        if paragraphs:
            for paragraph in paragraphs:
                text = normalize_space(paragraph.get_text(" ", strip=True))
                if text:
                    lines.append(text)
        else:
            text = normalize_space(subtitle_node.get_text("\n", strip=True))
            if text:
                lines.append(text)

        return "\n".join(lines)

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """从文章页提取作者信息。

        依次尝试 <h3> 标签和 <meta name="author"> 标签。

        Args:
            soup: 文章页 BeautifulSoup 对象

        Returns:
            作者信息，无则为空字符串
        """
        author = normalize_space(
            _extract_text(soup.select_one(".article h3"))
        )
        if author:
            return author

        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author is not None:
            return normalize_space(_attr_to_text(meta_author.get("content")))

        return ""

    def _build_node_url(self, paper_date: str, paper_number: str) -> str:
        """构建版面页 URL。

        Args:
            paper_date: 报纸日期（YYYY-MM-DD）
            paper_number: 版面编号

        Returns:
            版面页完整 URL
        """
        year, month, day = paper_date.split("-")
        return (
            f"{self.base_url}/rmrb/pc/layout/{year}{month}/{day}/"
            f"node_{paper_number.zfill(2)}.html"
        )

    def _fetch_soup(self, url: str) -> BeautifulSoup:
        """获取 URL 内容并解析为 BeautifulSoup 对象。"""
        return BeautifulSoup(self._fetch_html(url), "html.parser")

    def _fetch_html(self, url: str) -> str:
        """获取 URL 内容，自动处理编码。"""
        response = retry_get(self.session, url)
        return self._decode_html(response)

    def _decode_html(self, response: requests.Response) -> str:
        """解码 HTTP 响应内容。

        按优先级尝试以下编码来源：
        1. HTML 内容中的 charset 声明
        2. requests 库的 apparent_encoding（chardet 检测）
        3. HTTP 响应头中的编码，默认 UTF-8

        Args:
            response: HTTP 响应对象

        Returns:
            解码后的文本
        """
        raw = response.content
        charset = self._detect_charset(raw)
        if charset:
            try:
                return raw.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                logger.warning("无效的字符集声明: %s，回退到自动检测", charset)

        apparent_encoding = response.apparent_encoding
        if apparent_encoding:
            try:
                return raw.decode(apparent_encoding, errors="replace")
            except (LookupError, UnicodeDecodeError):
                pass

        encoding = response.encoding or "utf-8"
        return raw.decode(encoding, errors="replace")

    def _detect_charset(self, raw: bytes) -> str | None:
        """从 HTML 内容前 4096 字节中检测字符集声明。

        Args:
            raw: HTML 原始字节

        Returns:
            字符集名称（小写），未检测到则返回 None
        """
        match = self._HTML_CHARSET_PATTERN.search(raw[:4096])
        if not match:
            return None

        charset = match.group(1).decode("ascii", errors="ignore").lower()
        return charset or None


def _extract_text(node: Tag | None) -> str:
    """从 BeautifulSoup 节点提取文本。"""
    if node is None:
        return ""
    return node.get_text(" ", strip=True)


def _attr_to_text(value: object) -> str:
    """将 BeautifulSoup 属性值转为字符串。

    BeautifulSoup 的多值属性（如 class）可能返回列表。"""
    if isinstance(value, list):
        return " ".join(str(item) for item in value).strip()
    if value is None:
        return ""
    return str(value).strip()


def build_argument_parser() -> argparse.ArgumentParser:
    """构建人民日报爬虫的命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="抓取人民日报当天所有版面文章，并导出为 PDF。"
    )
    add_common_arguments(parser)

    # 人民日报专用参数
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"站点根地址，默认 {DEFAULT_BASE_URL}",
    )
    parser.set_defaults(out_dir="output/rmrb")
    return parser


def main() -> None:
    """人民日报爬虫主入口。"""
    setup_logging()

    parser = build_argument_parser()
    args = parser.parse_args()

    if args.combined_only and args.individual_only:
        parser.error("--combined-only 与 --individual-only 不能同时使用")

    export_individual = not args.combined_only
    export_combined = not args.individual_only
    font_paths = build_font_paths(args)

    spider = RMRBSpider(base_url=args.base_url)

    try:
        paper_date = spider.resolve_paper_date(args.date)
        articles = spider.fetch_articles(paper_date)
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP 错误: %s", e)
        return
    except requests.exceptions.ConnectionError as e:
        logger.error("连接错误: %s", e)
        return
    except requests.exceptions.Timeout:
        logger.error("请求超时")
        return
    except Exception as e:
        logger.error("抓取失败: %s", e)
        return

    if not articles:
        raise RuntimeError("当天未解析到任何文章")

    output_dir = Path(args.out_dir) / paper_date
    exporter = PDFExporter(
        style_prefix="RMRB",
        custom_font_paths=font_paths,
        font_dir=args.font_dir,
    )
    article_paths, combined_path = exporter.export_articles(
        articles=articles,
        output_dir=output_dir,
        export_individual=export_individual,
        export_combined=export_combined,
    )

    logger.info("日期: %s", paper_date)
    logger.info("文章数: %d", len(articles))
    if article_paths:
        logger.info("单篇 PDF: %d 个，输出目录: %s", len(article_paths), output_dir)
    if combined_path:
        logger.info("汇总 PDF: %s", combined_path)


if __name__ == "__main__":
    main()
