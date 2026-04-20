"""抓取参数配置面板。

提供报纸类型选择、日期配置、输出目录等参数控件，
以及开始/停止按钮和进度/日志显示区。
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QDate, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from newspaper_pdf.gui.workers import CrawlWorker


class CrawlPanel(QWidget):
    """抓取面板。

    Signals:
        crawl_completed: 抓取完成时发射，通知主窗口切换到结果浏览
    """

    crawl_completed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._worker: CrawlWorker | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """初始化界面控件。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ===== 参数配置区 =====
        config_group = QGroupBox("抓取配置")
        form = QFormLayout()
        form.setSpacing(12)

        # 报纸类型
        self.paper_type_combo = QComboBox()
        self.paper_type_combo.addItems(["解放军报", "人民日报"])
        self.paper_type_combo.currentIndexChanged.connect(self._on_paper_type_changed)
        form.addRow("报纸类型:", self.paper_type_combo)

        # 抓取模式
        mode_layout = QHBoxLayout()
        self.mode_single = QRadioButton("单日")
        self.mode_batch = QRadioButton("批量")
        self.mode_single.setChecked(True)
        self.mode_single.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_single)
        mode_layout.addWidget(self.mode_batch)
        mode_layout.addStretch()
        form.addRow("抓取模式:", mode_layout)

        # 日期选择
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form.addRow("日期:", self.date_edit)

        # 批量日期范围
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addMonths(-1))
        self.date_start.setDisplayFormat("yyyy-MM-dd")

        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setDisplayFormat("yyyy-MM-dd")

        self.batch_range_layout = QHBoxLayout()
        self.batch_range_layout.addWidget(self.date_start)
        self.batch_range_layout.addWidget(QLabel("至"))
        self.batch_range_layout.addWidget(self.date_end)
        self.batch_range_layout.addStretch()

        self.batch_range_widget = QWidget()
        self.batch_range_widget.setLayout(self.batch_range_layout)
        self.batch_range_widget.hide()
        form.addRow("日期范围:", self.batch_range_widget)

        # 输出目录
        out_dir_layout = QHBoxLayout()
        self.out_dir_edit = QLineEdit("output")
        self.out_dir_btn = QPushButton("浏览...")
        self.out_dir_btn.setObjectName("btnSecondary")
        self.out_dir_btn.clicked.connect(self._browse_output_dir)
        out_dir_layout.addWidget(self.out_dir_edit)
        out_dir_layout.addWidget(self.out_dir_btn)
        form.addRow("输出目录:", out_dir_layout)

        # 导出模式
        export_layout = QHBoxLayout()
        self.check_individual = QCheckBox("单篇 PDF")
        self.check_combined = QCheckBox("合集 PDF")
        self.check_individual.setChecked(True)
        self.check_combined.setChecked(True)
        export_layout.addWidget(self.check_individual)
        export_layout.addWidget(self.check_combined)
        export_layout.addStretch()
        form.addRow("导出模式:", export_layout)

        # 字体目录（可选）
        font_dir_layout = QHBoxLayout()
        self.font_dir_edit = QLineEdit()
        self.font_dir_edit.setPlaceholderText("留空则自动发现系统字体")
        self.font_dir_btn = QPushButton("浏览...")
        self.font_dir_btn.setObjectName("btnSecondary")
        self.font_dir_btn.clicked.connect(self._browse_font_dir)
        font_dir_layout.addWidget(self.font_dir_edit)
        font_dir_layout.addWidget(self.font_dir_btn)
        form.addRow("字体目录:", font_dir_layout)

        config_group.setLayout(form)
        layout.addWidget(config_group)

        # ===== 操作与进度区 =====
        action_layout = QHBoxLayout()

        self.start_btn = QPushButton("开始抓取")
        self.start_btn.clicked.connect(self._start_crawl)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setObjectName("btnSecondary")
        self.stop_btn.clicked.connect(self._stop_crawl)
        self.stop_btn.setEnabled(False)

        action_layout.addWidget(self.start_btn)
        action_layout.addWidget(self.stop_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # 进度条
        self.progress_bar = self._create_progress_bar()
        layout.addWidget(self.progress_bar)

        # 日志区
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(200)
        self.log_area.setPlaceholderText("抓取日志将在此显示...")
        layout.addWidget(self.log_area)

        layout.addStretch()

        # 初始化模式
        self._on_mode_changed(self.mode_single.isChecked())
        self._on_paper_type_changed(0)

    def _create_progress_bar(self) -> QWidget:
        """创建带标签的进度条容器。"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.progress_label = QLabel("就绪")
        self.progress_label.setObjectName("hintLabel")

        from PyQt6.QtWidgets import QProgressBar
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(1)
        self.progress.setValue(0)
        self.progress.setFormat("%v / %m")

        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress, stretch=1)

        return container

    def _on_paper_type_changed(self, index: int) -> None:
        """报纸类型切换时更新 UI。"""
        is_rmrb = index == 1  # 人民日报
        self.mode_batch.setEnabled(not is_rmrb)

        if is_rmrb:
            self.mode_single.setChecked(True)
            self.out_dir_edit.setText("output/rmrb")
        else:
            self.out_dir_edit.setText("output")

    def _on_mode_changed(self, is_single: bool) -> None:
        """抓取模式切换时显示/隐藏日期范围。"""
        self.date_edit.setVisible(is_single)
        self.batch_range_widget.setVisible(not is_single)

    def _browse_output_dir(self) -> None:
        """浏览选择输出目录。"""
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.out_dir_edit.setText(path)

    def _browse_font_dir(self) -> None:
        """浏览选择字体目录。"""
        path = QFileDialog.getExistingDirectory(self, "选择字体目录")
        if path:
            self.font_dir_edit.setText(path)

    def _start_crawl(self) -> None:
        """启动抓取任务。"""
        if not self.check_individual.isChecked() and not self.check_combined.isChecked():
            QMessageBox.warning(self, "配置错误", "请至少选择一种导出模式。")
            return

        paper_type = "jfjb" if self.paper_type_combo.currentIndex() == 0 else "rmrb"
        is_batch = self.mode_batch.isChecked() and self.mode_batch.isEnabled()

        if is_batch:
            start_date = self.date_start.date().toString("yyyy-MM-dd")
            end_date = self.date_end.date().toString("yyyy-MM-dd")
            paper_date = None
        else:
            start_date = None
            end_date = None
            paper_date = self.date_edit.date().toString("yyyy-MM-dd")

        self._worker = CrawlWorker(
            paper_type=paper_type,
            paper_date=paper_date,
            start_date=start_date,
            end_date=end_date,
            output_dir=Path(self.out_dir_edit.text()),
            export_individual=self.check_individual.isChecked(),
            export_combined=self.check_combined.isChecked(),
            skip_existing=True,
        )

        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._on_log)
        self._worker.finished.connect(self._on_finished)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_area.clear()
        self.progress.setMaximum(0 if not is_batch else 1)
        self.progress.setValue(0)
        self.progress_label.setText("抓取中...")

        self._worker.start()

    def _stop_crawl(self) -> None:
        """请求停止抓取。"""
        if self._worker:
            self._worker.cancel()
            self.stop_btn.setEnabled(False)
            self.progress_label.setText("正在停止...")

    def _on_progress(self, current: int, total: int, message: str) -> None:
        """更新进度显示。"""
        self.progress.setMaximum(total)
        self.progress.setValue(current)
        self.progress_label.setText(message)

    def _on_log(self, level: str, message: str) -> None:
        """追加日志消息。"""
        color_map = {"ERROR": "#f87171", "WARNING": "#fbbf24", "INFO": "#94a3b8"}
        color = color_map.get(level, "#94a3b8")
        self.log_area.append(f'<span style="color:{color}">[{level}] {message}</span>')

    def _on_finished(
        self, success: int, fail: int, skip: int, total: int
    ) -> None:
        """抓取完成时恢复 UI 状态。"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setMaximum(total)
        self.progress.setValue(total)
        self.progress_label.setText(
            f"完成: 成功 {success} | 失败 {fail} | 共 {total} 天"
        )

        if fail == 0:
            self.log_area.append(
                '<span style="color:#4ade80">抓取全部完成！</span>'
            )
            self.crawl_completed.emit()
        else:
            self.log_area.append(
                f'<span style="color:#fbbf24">抓取完成，有 {fail} 天失败。</span>'
            )
