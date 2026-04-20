"""结果浏览面板。

提供文件树导航和内嵌 PDF 渲染功能。
左侧为目录树，右侧为基于 QWebEngineView 的 PDF 查看器。
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QFileSystemModel

from PyQt6.QtCore import Qt


class ResultPanel(QWidget):
    """结果浏览面板。

    Attributes:
        root_path: 文件树根目录
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._root_path = Path("output")
        self._web_view = None
        self._setup_ui()

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
        self.tree_view.clicked.connect(self._on_file_clicked)
        self.tree_view.setHeaderHidden(True)
        for col in range(1, self.file_model.columnCount()):
            self.tree_view.hideColumn(col)
        self.tree_view.setMinimumWidth(220)
        self.tree_view.setMaximumWidth(400)

        tree_layout.addWidget(self.tree_view)
        splitter.addWidget(tree_container)

        # 右侧：PDF 渲染区
        self.pdf_container = QWidget()
        pdf_layout = QVBoxLayout(self.pdf_container)
        pdf_layout.setContentsMargins(0, 0, 0, 0)

        self._placeholder = QLabel("请在左侧选择 PDF 文件")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setObjectName("hintLabel")
        self._placeholder.setStyleSheet(
            "font-size: 16px; color: #9ca3af; background-color: #f9fafb;"
        )
        pdf_layout.addWidget(self._placeholder)

        splitter.addWidget(self.pdf_container)

        splitter.setSizes([280, 800])
        layout.addWidget(splitter)

    def _on_file_clicked(self, index) -> None:
        """文件树点击事件处理。"""
        file_path = Path(self.file_model.filePath(index))
        if file_path.suffix.lower() == ".pdf" and file_path.is_file():
            self._load_pdf(file_path)

    def _load_pdf(self, pdf_path: Path) -> None:
        """加载并渲染 PDF 文件。"""
        self._ensure_web_view()
        if self._web_view is None:
            return

        url = QUrl.fromLocalFile(str(pdf_path.resolve()))
        self._web_view.setUrl(url)

    def _ensure_web_view(self) -> None:
        """延迟创建 QWebEngineView。"""
        if self._web_view is not None:
            return

        from PyQt6.QtWebEngineWidgets import QWebEngineView

        self._placeholder.hide()

        self._web_view = QWebEngineView()
        pdf_layout = self.pdf_container.layout()
        pdf_layout.insertWidget(0, self._web_view)

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
        self._refresh_tree()

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
