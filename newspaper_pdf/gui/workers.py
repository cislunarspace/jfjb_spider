"""GUI 后台任务模块。

提供 QThread 子类，在后台线程运行爬虫逻辑，
通过 Qt 信号通知 UI 线程更新进度和日志。

信号：
    progress(current, total, message) — 进度更新
    log(level, message) — 日志消息
    finished(success_count, fail_count, skip_count, total) — 全部完成
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from newspaper_pdf.jfjb_spider import JFJBSpider, crawl_single_date, generate_date_range
from newspaper_pdf.pdf import PDFExporter
from newspaper_pdf.rmrb_spider import RMRBSpider

logger = logging.getLogger(__name__)


class CrawlWorker(QThread):
    """后台抓取任务。

    支持单日和批量模式，通过信号向 UI 报告进度。
    使用 _cancel_flag 属性支持取消操作。

    Attributes:
        paper_type: 报纸类型 ("jfjb" 或 "rmrb")
        paper_date: 单日模式的日期 (YYYY-MM-DD)，为 None 时自动获取当天
        start_date: 批量模式起始日期 (YYYY-MM-DD)
        end_date: 批量模式结束日期 (YYYY-MM-DD)
        output_dir: 输出根目录
        export_individual: 是否导出单篇 PDF
        export_combined: 是否导出合集 PDF
        skip_existing: 是否跳过已存在的日期目录
    """

    progress = pyqtSignal(int, int, str)
    log = pyqtSignal(str, str)
    finished = pyqtSignal(int, int, int, int)

    def __init__(
        self,
        paper_type: str,
        paper_date: str | None,
        start_date: str | None,
        end_date: str | None,
        output_dir: Path,
        export_individual: bool,
        export_combined: bool,
        skip_existing: bool,
    ) -> None:
        super().__init__()
        self.paper_type = paper_type
        self.paper_date = paper_date
        self.start_date = start_date
        self.end_date = end_date
        self.output_dir = output_dir
        self.export_individual = export_individual
        self.export_combined = export_combined
        self.skip_existing = skip_existing
        self._cancel_flag = False

    def cancel(self) -> None:
        """请求取消任务。"""
        self._cancel_flag = True

    def run(self) -> None:
        """执行抓取任务（在后台线程中运行）。"""
        if self.paper_type == "jfjb":
            self._run_jfjb()
        else:
            self._run_rmrb()

    def _run_jfjb(self) -> None:
        """执行解放军报抓取。"""
        spider = JFJBSpider()
        exporter = PDFExporter(style_prefix="JFJB")

        if self.start_date:
            self._run_batch(spider, exporter)
        else:
            self._run_single_jfjb(spider, exporter)

    def _run_single_jfjb(self, spider: JFJBSpider, exporter: PDFExporter) -> None:
        """执行解放军报单日抓取。"""
        try:
            paper_date = spider.resolve_paper_date(self.paper_date)
            self.log.emit("INFO", f"日期: {paper_date}")

            payload = spider.fetch_index_payload(paper_date)
            articles = spider.parse_articles(payload, paper_date)

            if not articles:
                self.log.emit("WARNING", "当天未解析到任何文章")
                self.progress.emit(1, 1, "无文章")
                self.finished.emit(0, 0, 1, 1)
                return

            output_dir = self.output_dir / paper_date
            output_dir.mkdir(parents=True, exist_ok=True)
            exporter.export_articles(
                articles=articles,
                output_dir=output_dir,
                export_individual=self.export_individual,
                export_combined=self.export_combined,
            )

            self.log.emit("INFO", f"完成: {len(articles)} 篇文章")
            self.progress.emit(1, 1, f"完成 ({len(articles)} 篇)")
            self.finished.emit(1, 0, 0, 1)

        except Exception as e:
            self.log.emit("ERROR", f"抓取失败: {e}")
            self.progress.emit(1, 1, "失败")
            self.finished.emit(0, 1, 0, 1)

    def _run_batch(self, spider: JFJBSpider, exporter: PDFExporter) -> None:
        """执行批量日期范围抓取。"""
        from datetime import date

        end = self.end_date or date.today().strftime("%Y-%m-%d")
        dates = generate_date_range(self.start_date, end)
        total = len(dates)
        success_count = 0
        fail_count = 0
        skip_count = 0

        self.log.emit("INFO", f"批量抓取: {self.start_date} ~ {end}，共 {total} 天")

        for i, paper_date in enumerate(dates, start=1):
            if self._cancel_flag:
                self.log.emit("WARNING", "任务已取消")
                break

            self.progress.emit(i, total, f"抓取中 ({i}/{total})")

            ok = crawl_single_date(
                spider=spider,
                exporter=exporter,
                paper_date=paper_date,
                out_dir=self.output_dir,
                export_individual=self.export_individual,
                export_combined=self.export_combined,
                skip_existing=self.skip_existing,
            )

            if ok:
                success_count += 1
            else:
                fail_count += 1

        self.log.emit(
            "INFO",
            f"抓取完成: 成功 {success_count} | 失败 {fail_count} / 共 {total} 天",
        )
        self.finished.emit(success_count, fail_count, skip_count, total)

    def _run_rmrb(self) -> None:
        """执行人民日报单日抓取。"""
        spider = RMRBSpider()
        exporter = PDFExporter(style_prefix="RMRB")

        try:
            paper_date = spider.resolve_paper_date(self.paper_date)
            self.log.emit("INFO", f"日期: {paper_date}")

            articles = spider.fetch_articles(paper_date)

            if not articles:
                self.log.emit("WARNING", "当天未解析到任何文章")
                self.progress.emit(1, 1, "无文章")
                self.finished.emit(0, 0, 1, 1)
                return

            output_dir = self.output_dir / paper_date
            output_dir.mkdir(parents=True, exist_ok=True)
            exporter.export_articles(
                articles=articles,
                output_dir=output_dir,
                export_individual=self.export_individual,
                export_combined=self.export_combined,
            )

            self.log.emit("INFO", f"完成: {len(articles)} 篇文章")
            self.progress.emit(1, 1, f"完成 ({len(articles)} 篇)")
            self.finished.emit(1, 0, 0, 1)

        except Exception as e:
            self.log.emit("ERROR", f"抓取失败: {e}")
            self.progress.emit(1, 1, "失败")
            self.finished.emit(0, 1, 0, 1)
