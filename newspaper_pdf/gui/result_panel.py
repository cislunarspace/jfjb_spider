"""结果浏览面板。

提供文件树导航与基于网页架构的 PDF 预览功能。
左侧为目录树，右侧为 PDF 信息预览区，通过内嵌 HTTP 服务器
将 PDF 暴露为本地 URL，调用系统浏览器进行预览，
绕过 PyQt WebEngine 的 PDF 插件限制。
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFileSystemModel
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from newspaper_pdf.gui.preview_server import PreviewServer


class ResultPanel(QWidget):
    """结果浏览面板。

    Attributes:
        root_path: 文件树根目录
        preview_server: 本地 HTTP 预览服务器
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._root_path = Path("output")
        self.preview_server: PreviewServer | None = None
        self._setup_ui()
        self._start_server()

    def _setup_ui(self) -> None:
        """初始化界面控件。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 8, 12, 8)

        self.root_label = QLabel("根目录: output")
        self.root_label.setObjectName("hintLabel")

        self.browse_root_btn = QPushButton("选择目录")
        self.browse_root_btn.setObjectName("btnSecondary")
        self.browse_root_btn.clicked.connect(self._browse_root)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setObjectName("btnSecondary")
        self.refresh_btn.clicked.connect(self._refresh_tree)

        toolbar.addWidget(self.root_label)
        toolbar.addStretch()
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.browse_root_btn)
        layout.addLayout(toolbar)

        # 主内容区：分割器
        splitter = QSplitter()

        # 左侧：文件树
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(str(self._root_path.resolve()))
        self.file_model.setNameFilters(["*.pdf"])
        self.file_model.setNameFilterDisables(False)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(
            self.file_model.index(str(self._root_path.resolve()))
        )
        self.tree_view.setHeaderHidden(True)
        for col in range(1, self.file_model.columnCount()):
            self.tree_view.hideColumn(col)
        self.tree_view.setMinimumWidth(220)
        self.tree_view.setMaximumWidth(400)

        tree_layout.addWidget(self.tree_view)
        splitter.addWidget(tree_container)

        # 右侧：PDF 网页预览信息面板
        self.preview_stack = QStackedWidget()
        self.preview_stack.setStyleSheet("background-color: #f9fafb;")

        # 默认提示页
        self.preview_hint = QLabel(
            "请在左侧选择 PDF 文件\n\n"
            "选中后将在系统浏览器中打开预览"
        )
        self.preview_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_hint.setObjectName("hintLabel")
        self.preview_hint.setStyleSheet(
            "font-size: 16px; color: #9ca3af; background-color: transparent;"
        )
        self.preview_stack.addWidget(self.preview_hint)

        # PDF 信息面板（选中 PDF 后显示）
        self.info_widget = QWidget()
        info_layout = QVBoxLayout(self.info_widget)
        info_layout.setContentsMargins(40, 40, 40, 40)
        info_layout.setSpacing(16)

        self.file_name_label = QLabel()
        self.file_name_label.setWordWrap(True)
        self.file_name_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #111827;"
        )
        info_layout.addWidget(self.file_name_label)

        self.file_meta_label = QLabel()
        self.file_meta_label.setStyleSheet(
            "font-size: 13px; color: #6b7280;"
        )
        info_layout.addWidget(self.file_meta_label)

        self.file_path_label = QLabel()
        self.file_path_label.setWordWrap(True)
        self.file_path_label.setStyleSheet(
            "font-size: 12px; color: #9ca3af;"
        )
        info_layout.addWidget(self.file_path_label)

        info_layout.addSpacing(20)

        self.preview_btn = QPushButton("在浏览器中预览")
        self.preview_btn.setObjectName("btnPrimary")
        self.preview_btn.setMinimumHeight(40)
        self.preview_btn.clicked.connect(self._open_current_in_browser)
        info_layout.addWidget(self.preview_btn)

        self.copy_url_btn = QPushButton("复制预览链接")
        self.copy_url_btn.setObjectName("btnSecondary")
        self.copy_url_btn.setMinimumHeight(36)
        self.copy_url_btn.clicked.connect(self._copy_preview_url)
        info_layout.addWidget(self.copy_url_btn)

        info_layout.addStretch()
        self.preview_stack.addWidget(self.info_widget)

        splitter.addWidget(self.preview_stack)
        splitter.setSizes([280, 800])

        # 连接文件树选择信号
        self.tree_view.selectionModel().currentChanged.connect(
            self._on_file_selected
        )
        layout.addWidget(splitter)

    def _start_server(self) -> None:
        """启动本地 HTTP 预览服务器。"""
        self.preview_server = PreviewServer(self._root_path)
        self.preview_server.start()

    def _stop_server(self) -> None:
        """停止本地 HTTP 预览服务器。"""
        if self.preview_server is not None:
            self.preview_server.stop()
            self.preview_server = None

    def closeEvent(self, event) -> None:  # noqa: ANN001
        """面板关闭时停止服务器。"""
        self._stop_server()
        super().closeEvent(event)

    def _browse_root(self) -> None:
        """浏览选择文件树根目录。"""
        path = QFileDialog.getExistingDirectory(self, "选择输出根目录")
        if path:
            self.set_root_path(Path(path))

    def _refresh_tree(self) -> None:
        """刷新文件树。"""
        self.file_model.setRootPath(str(self._root_path.resolve()))
        self.tree_view.setRootIndex(
            self.file_model.index(str(self._root_path.resolve()))
        )

    def set_root_path(self, path: Path) -> None:
        """设置文件树根目录并刷新。"""
        self._root_path = path
        self.root_label.setText(f"根目录: {path}")
        # 重启服务器指向新目录
        self._stop_server()
        self._start_server()
        self._refresh_tree()

    def _on_file_selected(self, current, previous) -> None:
        """文件树选中项变化时更新预览信息。"""
        if not current.isValid():
            self._show_hint()
            return

        file_path = Path(self.file_model.filePath(current))
        if not file_path.is_file() or file_path.suffix.lower() != ".pdf":
            self._show_hint()
            return

        self._current_pdf = file_path
        self._show_pdf_info(file_path)
        # 自动在浏览器中打开预览
        self._open_in_browser(file_path)

    def _show_hint(self) -> None:
        """显示默认提示页。"""
        self.preview_stack.setCurrentWidget(self.preview_hint)

    def _show_pdf_info(self, file_path: Path) -> None:
        """显示 PDF 文件信息页。"""
        self.preview_stack.setCurrentWidget(self.info_widget)

        self.file_name_label.setText(file_path.name)

        size = file_path.stat().st_size
        size_str = self._format_size(size)
        mtime = file_path.stat().st_mtime
        from datetime import datetime

        time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        self.file_meta_label.setText(f"大小: {size_str}  |  修改时间: {time_str}")

        if self.preview_server is not None:
            try:
                rel = file_path.resolve().relative_to(
                    self.preview_server.root
                )
                url = self.preview_server.get_url(rel)
            except ValueError:
                url = ""
            self.file_path_label.setText(f"预览链接: {url}")
        else:
            self.file_path_label.setText("服务器未启动")

    def _open_current_in_browser(self) -> None:
        """打开当前选中的 PDF（按钮触发）。"""
        if hasattr(self, "_current_pdf"):
            self._open_in_browser(self._current_pdf)

    def _open_in_browser(self, file_path: Path) -> None:
        """通过系统浏览器打开指定 PDF 的 HTTP 预览链接。"""
        if self.preview_server is None:
            return
        try:
            rel = file_path.resolve().relative_to(self.preview_server.root)
        except ValueError:
            return
        url = self.preview_server.get_url(rel)
        QDesktopServices.openUrl(QUrl(url))

    def _copy_preview_url(self) -> None:
        """复制当前 PDF 的预览链接到剪贴板。"""
        if self.preview_server is None or not hasattr(self, "_current_pdf"):
            return
        try:
            rel = self._current_pdf.resolve().relative_to(
                self.preview_server.root
            )
        except ValueError:
            return
        url = self.preview_server.get_url(rel)
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(url)

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小为人类可读字符串。"""
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def expand_latest_dir(self) -> None:
        """展开最新的日期目录。"""
        root = self._root_path.resolve()
        if not root.is_dir():
            return

        date_dirs = sorted(
            [d for d in root.iterdir() if d.is_dir()],
            key=lambda d: d.name,
            reverse=True,
        )
        if date_dirs:
            latest = date_dirs[0]
            index = self.file_model.index(str(latest))
            self.tree_view.expand(index)
            self.tree_view.scrollTo(index)
