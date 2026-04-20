"""GUI 后台任务 Worker 单元测试。

测试 CrawlWorker 的信号发射逻辑，无需真实 GUI 环境。
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from newspaper_pdf.gui.workers import CrawlWorker


class TestCrawlWorkerSignals:
    """验证 CrawlWorker 定义了必要的信号。"""

    def test_has_progress_signal(self) -> None:
        """应定义 progress 信号（current, total, message）。"""
        assert hasattr(CrawlWorker, "progress")

    def test_has_log_signal(self) -> None:
        """应定义 log 信号（level, message）。"""
        assert hasattr(CrawlWorker, "log")

    def test_has_finished_signal(self) -> None:
        """应定义 finished 信号（success_count, fail_count, skip_count, total）。"""
        assert hasattr(CrawlWorker, "finished")


class TestCrawlWorkerConfig:
    """验证 CrawlWorker 的配置参数。"""

    def test_single_date_config(self) -> None:
        """单日模式应正确存储参数。"""
        worker = CrawlWorker(
            paper_type="jfjb",
            paper_date="2026-03-10",
            start_date=None,
            end_date=None,
            output_dir=Path("output"),
            export_individual=True,
            export_combined=True,
            skip_existing=True,
        )
        assert worker.paper_type == "jfjb"
        assert worker.paper_date == "2026-03-10"
        assert worker.start_date is None

    def test_batch_mode_config(self) -> None:
        """批量模式应正确存储参数。"""
        worker = CrawlWorker(
            paper_type="jfjb",
            paper_date=None,
            start_date="2026-01-01",
            end_date="2026-01-31",
            output_dir=Path("output"),
            export_individual=True,
            export_combined=True,
            skip_existing=True,
        )
        assert worker.start_date == "2026-01-01"
        assert worker.end_date == "2026-01-31"

    def test_rmrb_paper_type(self) -> None:
        """人民日报类型应正确存储。"""
        worker = CrawlWorker(
            paper_type="rmrb",
            paper_date="2026-03-10",
            start_date=None,
            end_date=None,
            output_dir=Path("output/rmrb"),
            export_individual=True,
            export_combined=True,
            skip_existing=True,
        )
        assert worker.paper_type == "rmrb"


class TestCrawlWorkerSingleDate:
    """验证单日抓取流程。"""

    @patch("newspaper_pdf.gui.workers.PDFExporter")
    @patch("newspaper_pdf.gui.workers.JFJBSpider")
    def test_jfjb_single_date_emits_progress(
        self, mock_spider_cls: MagicMock, mock_exporter_cls: MagicMock
    ) -> None:
        """解放军报单日模式应发射 progress(1, 1, ...) 信号。"""
        mock_spider = MagicMock()
        mock_spider.resolve_paper_date.return_value = "2026-03-10"
        mock_spider.fetch_index_payload.return_value = {"paperInfo": []}
        mock_spider_cls.return_value = mock_spider

        worker = CrawlWorker(
            paper_type="jfjb",
            paper_date="2026-03-10",
            start_date=None,
            end_date=None,
            output_dir=Path("output"),
            export_individual=True,
            export_combined=True,
            skip_existing=True,
        )

        emitted: list[tuple[int, int, str]] = []
        worker.progress.connect(lambda *args: emitted.append(args))
        worker.run()

        assert any(current == 1 and total == 1 for current, total, _ in emitted)

    @patch("newspaper_pdf.gui.workers.PDFExporter")
    @patch("newspaper_pdf.gui.workers.RMRBSpider")
    def test_rmrb_single_date_emits_log(
        self, mock_spider_cls: MagicMock, mock_exporter_cls: MagicMock
    ) -> None:
        """人民日报单日模式应发射日志信号。"""
        mock_spider = MagicMock()
        mock_spider.resolve_paper_date.return_value = "2026-03-10"
        mock_spider.fetch_articles.return_value = []
        mock_spider_cls.return_value = mock_spider

        worker = CrawlWorker(
            paper_type="rmrb",
            paper_date="2026-03-10",
            start_date=None,
            end_date=None,
            output_dir=Path("output/rmrb"),
            export_individual=True,
            export_combined=True,
            skip_existing=True,
        )

        emitted: list[tuple[str, str]] = []
        worker.log.connect(lambda *args: emitted.append(args))
        worker.run()

        assert len(emitted) > 0


class TestCrawlWorkerCancel:
    """验证取消机制。"""

    def test_cancel_sets_flag(self) -> None:
        """调用 cancel() 应设置取消标志。"""
        worker = CrawlWorker(
            paper_type="jfjb",
            paper_date="2026-03-10",
            start_date=None,
            end_date=None,
            output_dir=Path("output"),
            export_individual=True,
            export_combined=True,
            skip_existing=True,
        )
        assert worker._cancel_flag is False
        worker.cancel()
        assert worker._cancel_flag is True
