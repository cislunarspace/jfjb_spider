"""解放军报（81.cn）爬虫模块。

通过 81.cn 提供的 JSON API 抓取解放军报各版面文章，
并导出为格式化的 PDF 文件。

数据源特点：
- 使用 JSON API（index.json 端点）获取版面和文章元数据
- 支持单日抓取和批量日期范围抓取
- 支持断点续爬（跳过已下载日期）

使用方式：
    python jfjb.py                         # 抓取当天
    python jfjb.py --date 2026-03-10       # 指定日期
    python jfjb.py --start-date 2026-01-01 --end-date 2026-03-31 --delay 2  # 批量
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from collections.abc import Iterable
from urllib.parse import parse_qs, urlparse

import requests

from newspaper_pdf.cli import add_common_arguments, build_font_paths
from newspaper_pdf.models import Article
from newspaper_pdf.network import create_session, retry_get
from newspaper_pdf.pdf import PDFExporter
from newspaper_pdf.utils import html_to_paragraphs, normalize_space

logger = logging.getLogger(__name__)

# 81.cn 最新报纸查询接口
NEWEST_PAPER_API = "https://rmt-zuul.81.cn/api-paper/api/newestPaper"

# 解放军报站点默认根地址
DEFAULT_BASE_URL = "https://www.81.cn"


class JFJBSpider:
    """解放军报爬虫。

    通过 81.cn 的 JSON API 获取报纸版面数据，解析文章标题、作者和正文。

    Attributes:
        base_url: 站点根地址
        session: HTTP 会话对象
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = create_session()

    def resolve_paper_date(self, target_date: str | None) -> str:
        """解析目标报纸日期。

        如果用户指定了日期，验证格式后直接返回。
        如果未指定，通过 newestPaper API 自动获取最新版面日期。

        Args:
            target_date: 用户指定的日期字符串（YYYY-MM-DD），为 None 时自动获取

        Returns:
            报纸日期字符串（YYYY-MM-DD）

        Raises:
            ValueError: 日期格式不正确
            RuntimeError: 无法从 API 获取最新版面日期
        """
        if target_date:
            datetime.strptime(target_date, "%Y-%m-%d")
            return target_date

        # 查询最新报纸列表，找到解放军报对应的日期
        response = retry_get(self.session, NEWEST_PAPER_API)
        payload = response.json()
        papers = payload.get("data") or []

        jfjb_item = None
        for item in papers:
            web_url = str(item.get("webUrl") or "")
            paper_name = str(item.get("paperName") or "")
            if "paperName=jfjb" in web_url or "解放军报" in paper_name:
                jfjb_item = item
                break

        if not jfjb_item:
            raise RuntimeError("未能从 newestPaper 接口定位到解放军报当天版面")

        # 优先从 paperData 字段获取日期
        paper_date = str(jfjb_item.get("paperData") or "").strip()
        if paper_date:
            return paper_date

        # 回退：从 webUrl 查询参数中提取日期
        web_url = str(jfjb_item.get("webUrl") or "")
        query = parse_qs(urlparse(web_url).query)
        date_from_query = (query.get("paperDate") or [""])[0].strip()
        if not date_from_query:
            raise RuntimeError("当天版面已找到，但未能解析 paperDate")
        return date_from_query

    def fetch_index_payload(self, paper_date: str) -> dict:
        """获取指定日期的报纸版面索引数据。

        通过访问 index.json 端点获取该日所有版面和文章的元数据。

        Args:
            paper_date: 报纸日期（YYYY-MM-DD）

        Returns:
            JSON 响应数据（包含 paperInfo 列表）
        """
        year, month, day = paper_date.split("-")
        url = f"{self.base_url}/_szb/jfjb/{year}/{month}/{day}/index.json"
        response = retry_get(self.session, url)
        return response.json()

    def parse_articles(self, payload: dict, paper_date: str) -> list[Article]:
        """从 JSON 数据中解析所有版面的文章。

        Args:
            payload: fetch_index_payload 返回的 JSON 数据
            paper_date: 报纸日期

        Returns:
            文章列表，按版面和序号排列
        """
        paper_info = payload.get("paperInfo") or []
        articles: list[Article] = []

        for paper in self._sorted_papers(paper_info):
            paper_number = str(paper.get("paperNumber") or "00").zfill(2)
            section_name = normalize_space(
                str(paper.get("paperBk") or f"第{paper_number}版")
            )
            xy_list = paper.get("xyList") or []

            for article_index, raw_article in enumerate(xy_list, start=1):
                title = normalize_space(
                    str(raw_article.get("title") or "未命名文章")
                )
                subtitle = self._pick_subtitle(raw_article)
                author = normalize_space(str(raw_article.get("author") or ""))
                paragraphs = html_to_paragraphs(
                    str(raw_article.get("content") or "")
                )
                if author:
                    paragraphs.insert(0, f"作者：{author}")

                source_url = (
                    f"{self.base_url}/szb_223187/szbxq/index.html"
                    f"?paperName=jfjb&paperDate={paper_date}"
                    f"&paperNumber={paper_number}&articleid={raw_article.get('id', '')}"
                )

                articles.append(
                    Article(
                        paper_name="解放军报",
                        paper_date=paper_date,
                        paper_number=paper_number,
                        section_name=section_name,
                        article_index=article_index,
                        title=title,
                        subtitle=subtitle,
                        author=author,
                        paragraphs=paragraphs,
                        source_url=source_url,
                    )
                )

        return articles

    @staticmethod
    def _sorted_papers(paper_info: Iterable[dict]) -> list[dict]:
        """按版面编号排序报纸版面数据。

        Args:
            paper_info: 版面信息列表

        Returns:
            按版面编号排序后的列表
        """
        def sort_key(item: dict) -> tuple[int, str]:
            paper_number = str(item.get("paperNumber") or "999")
            if paper_number.isdigit():
                return (int(paper_number), paper_number)
            return (999, paper_number)

        return sorted(paper_info, key=sort_key)

    def _pick_subtitle(self, raw_article: dict) -> str:
        """从文章数据中提取副标题。

        依次尝试 title2 和 guideTitle 字段，返回第一个非空值。

        Args:
            raw_article: 文章原始 JSON 数据

        Returns:
            副标题文本，无则为空字符串
        """
        candidates = [
            str(raw_article.get("title2") or ""),
            str(raw_article.get("guideTitle") or ""),
        ]
        for candidate in candidates:
            normalized = normalize_space(candidate)
            if normalized:
                return normalized
        return ""


def generate_date_range(start_date: str, end_date: str) -> list[str]:
    """生成从 start_date 到 end_date（含）的所有日期列表。

    Args:
        start_date: 起始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）

    Returns:
        日期字符串列表

    Raises:
        ValueError: 起始日期晚于结束日期
    """
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if start > end:
        raise ValueError(f"起始日期 {start_date} 晚于结束日期 {end_date}")
    dates: list[str] = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


def crawl_single_date(
    spider: JFJBSpider,
    exporter: PDFExporter,
    paper_date: str,
    out_dir: Path,
    export_individual: bool,
    export_combined: bool,
    skip_existing: bool,
) -> bool:
    """抓取单日的解放军报，返回是否成功。

    Args:
        spider: 爬虫实例
        exporter: PDF 导出器实例
        paper_date: 报纸日期
        out_dir: 输出根目录
        export_individual: 是否导出单篇 PDF
        export_combined: 是否导出合集 PDF
        skip_existing: 是否跳过已存在的输出目录

    Returns:
        True 表示成功或跳过，False 表示失败
    """
    output_dir = out_dir / paper_date

    # 跳过已下载的日期
    if skip_existing and output_dir.exists():
        if any(output_dir.iterdir()):
            logger.info("[跳过] %s — 已存在于 %s", paper_date, output_dir)
            return True

    try:
        payload = spider.fetch_index_payload(paper_date)
        articles = spider.parse_articles(payload, paper_date)
    except requests.exceptions.HTTPError as e:
        logger.error("[失败] %s — HTTP 错误: %s", paper_date, e)
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error("[失败] %s — 连接错误: %s", paper_date, e)
        return False
    except requests.exceptions.Timeout:
        logger.error("[失败] %s — 请求超时", paper_date)
        return False
    except Exception as e:
        logger.error("[失败] %s — %s", paper_date, e)
        return False

    if not articles:
        logger.info("[跳过] %s — 当天无文章", paper_date)
        return True

    try:
        article_paths, combined_path = exporter.export_articles(
            articles=articles,
            output_dir=output_dir,
            export_individual=export_individual,
            export_combined=export_combined,
        )
        logger.info("[完成] %s — %d 篇文章", paper_date, len(articles))
        return True
    except Exception as e:
        logger.error("[失败] %s — 导出 PDF 出错: %s", paper_date, e)
        return False


def build_argument_parser() -> argparse.ArgumentParser:
    """构建解放军报爬虫的命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="抓取解放军报所有版面文章，并导出为 PDF。支持单日或日期范围批量抓取。"
    )
    add_common_arguments(parser)

    # 解放军报专用参数
    parser.add_argument(
        "--start-date",
        help="批量抓取的起始日期（含），格式 YYYY-MM-DD。需与 --end-date 配合使用。",
    )
    parser.add_argument(
        "--end-date",
        help="批量抓取的结束日期（含），格式 YYYY-MM-DD。不传则默认为今天。",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"站点根地址，默认 {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="批量抓取时每天之间的请求间隔秒数，默认 2.0 秒。",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="跳过已下载的日期（输出目录已存在则跳过），默认启用。",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_false",
        dest="skip_existing",
        help="不跳过已下载的日期，重新抓取。",
    )
    return parser


def main() -> None:
    """解放军报爬虫主入口。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    parser = build_argument_parser()
    args = parser.parse_args()

    if args.combined_only and args.individual_only:
        parser.error("--combined-only 与 --individual-only 不能同时使用")
    if args.date and args.start_date:
        parser.error("--date 与 --start-date 不能同时使用，单日用 --date，批量用 --start-date")

    export_individual = not args.combined_only
    export_combined = not args.individual_only
    out_dir = Path(args.out_dir)
    font_paths = build_font_paths(args)

    spider = JFJBSpider(base_url=args.base_url)
    exporter = PDFExporter(
        style_prefix="JFJB",
        custom_font_paths=font_paths,
        font_dir=args.font_dir,
    )

    # ==================== 批量模式 ====================
    if args.start_date:
        end_date = args.end_date or date.today().strftime("%Y-%m-%d")
        dates = generate_date_range(args.start_date, end_date)
        total = len(dates)
        success_count = 0
        fail_count = 0
        skip_count = 0

        logger.info("批量抓取: %s ~ %s，共 %d 天", args.start_date, end_date, total)
        logger.info("输出目录: %s", out_dir.resolve())
        logger.info("请求间隔: %ss | 跳过已有: %s", args.delay, args.skip_existing)
        logger.info("=" * 60)

        for i, paper_date in enumerate(dates, start=1):
            logger.info("[%d/%d] ", i)

            # 外层检查跳过已存在日期
            date_dir = out_dir / paper_date
            if args.skip_existing and date_dir.exists() and any(date_dir.iterdir()):
                logger.info("[跳过] %s — 已存在", paper_date)
                skip_count += 1
                continue

            ok = crawl_single_date(
                spider=spider,
                exporter=exporter,
                paper_date=paper_date,
                out_dir=out_dir,
                export_individual=export_individual,
                export_combined=export_combined,
                skip_existing=False,  # 已在外层检查
            )
            if ok:
                success_count += 1
            else:
                fail_count += 1

            # 请求间隔（最后一天不用等）
            if i < total:
                time.sleep(args.delay)

        logger.info("=" * 60)
        logger.info(
            "抓取完成: 成功 %d | 跳过 %d | 失败 %d / 共 %d 天",
            success_count, skip_count, fail_count, total,
        )
        return

    # ==================== 单日模式 ====================
    paper_date = spider.resolve_paper_date(args.date)
    payload = spider.fetch_index_payload(paper_date)
    articles = spider.parse_articles(payload, paper_date)

    if not articles:
        raise RuntimeError("当天未解析到任何文章")

    output_dir = out_dir / paper_date
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
