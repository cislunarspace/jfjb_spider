"""PyQt6 GUI 应用入口和主窗口。

提供 Tab 布局主窗口，包含「抓取」和「结果浏览」两个面板。

入口函数 main() 可通过 pyproject.toml 中的 newspaper-pdf-ui 脚本调用。
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from newspaper_pdf.gui.crawl_panel import CrawlPanel
from newspaper_pdf.gui.result_panel import ResultPanel
from newspaper_pdf.gui.styles import APP_STYLESHEET


class MainWindow(QMainWindow):
    """主窗口。

    顶部 Tab 栏切换「抓取」和「结果浏览」面板。
    抓取完成后自动提示切换到结果浏览。

    Attributes:
        crawl_panel: 抓取面板
        result_panel: 结果浏览面板
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("报刊 PDF 助手")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """初始化界面。"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab 栏
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # 抓取面板
        self.crawl_panel = CrawlPanel()
        self.tabs.addTab(self.crawl_panel, "抓取")

        # 结果浏览面板
        self.result_panel = ResultPanel()
        self.tabs.addTab(self.result_panel, "结果浏览")

        layout.addWidget(self.tabs)

        # 连接信号
        self.crawl_panel.crawl_completed.connect(self._on_crawl_completed)

    def _on_crawl_completed(self) -> None:
        """抓取完成后提示切换并刷新结果。"""
        from pathlib import Path

        output_dir = Path(self.crawl_panel.out_dir_edit.text())
        self.result_panel.set_root_path(output_dir)
        self.result_panel.expand_latest_dir()

        self.tabs.setCurrentIndex(1)


def main() -> None:
    """GUI 应用入口。"""
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())