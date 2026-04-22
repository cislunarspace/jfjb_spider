"""结果浏览面板单元测试（网页架构）。"""

from __future__ import annotations


from PyQt6.QtCore import QUrl

from newspaper_pdf.gui.result_panel import ResultPanel


class TestResultPanelPreview:
    """验证基于网页架构的 PDF 预览交互逻辑。"""

    def test_initial_state_shows_hint(self, qtbot, tmp_path):
        """初始状态应显示提示页。"""
        panel = ResultPanel()
        qtbot.addWidget(panel)
        panel.set_root_path(tmp_path)

        assert panel.preview_stack.currentWidget() is panel.preview_hint

    def test_select_non_pdf_shows_hint(self, qtbot, tmp_path):
        """选中非 PDF 文件时应显示提示页。"""
        txt = tmp_path / "readme.txt"
        txt.write_text("hello")

        panel = ResultPanel()
        qtbot.addWidget(panel)
        panel.set_root_path(tmp_path)

        index = panel.file_model.index(str(txt))
        panel._on_file_selected(index, None)

        assert panel.preview_stack.currentWidget() is panel.preview_hint

    def test_select_directory_shows_hint(self, qtbot, tmp_path):
        """选中目录时应显示提示页。"""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        panel = ResultPanel()
        qtbot.addWidget(panel)
        panel.set_root_path(tmp_path)

        index = panel.file_model.index(str(subdir))
        panel._on_file_selected(index, None)

        assert panel.preview_stack.currentWidget() is panel.preview_hint

    def test_select_pdf_shows_info_and_opens_browser(
        self, qtbot, tmp_path, monkeypatch
    ):
        """选中 PDF 时应显示信息并自动调用系统浏览器打开。"""
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake pdf content")

        panel = ResultPanel()
        qtbot.addWidget(panel)
        panel.set_root_path(tmp_path)

        opened_urls: list[QUrl] = []
        monkeypatch.setattr(
            "newspaper_pdf.gui.result_panel.QDesktopServices.openUrl",
            lambda url: opened_urls.append(url),
        )

        index = panel.file_model.index(str(pdf))
        panel._on_file_selected(index, None)

        assert panel.preview_stack.currentWidget() is panel.info_widget
        assert panel.file_name_label.text() == "test.pdf"
        assert "在浏览器中预览" in panel.preview_btn.text()
        assert len(opened_urls) == 1
        assert opened_urls[0].toString().endswith("test.pdf")

    def test_copy_preview_url(self, qtbot, tmp_path, monkeypatch):
        """复制预览链接应将正确 URL 写入剪贴板。"""
        pdf = tmp_path / "report.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        panel = ResultPanel()
        qtbot.addWidget(panel)
        panel.set_root_path(tmp_path)

        index = panel.file_model.index(str(pdf))
        panel._on_file_selected(index, None)

        clipboard_texts: list[str] = []

        class FakeClipboard:
            def setText(self, text: str) -> None:
                clipboard_texts.append(text)

        monkeypatch.setattr(
            "PyQt6.QtWidgets.QApplication.clipboard",
            staticmethod(lambda: FakeClipboard()),
        )

        panel._copy_preview_url()

        assert len(clipboard_texts) == 1
        assert "report.pdf" in clipboard_texts[0]
        assert clipboard_texts[0].startswith("http://127.0.0.1:")

    def test_server_restarted_on_root_change(self, qtbot, tmp_path):
        """切换根目录时应重启服务器指向新目录。"""
        panel = ResultPanel()
        qtbot.addWidget(panel)
        panel.set_root_path(tmp_path)

        new_path = tmp_path / "other"
        new_path.mkdir()
        panel.set_root_path(new_path)

        assert panel.preview_server is not None
        assert panel.preview_server.root == new_path.resolve()

    def test_invalid_index_shows_hint(self, qtbot, tmp_path):
        """传入无效索引时应显示提示页。"""
        panel = ResultPanel()
        qtbot.addWidget(panel)
        panel.set_root_path(tmp_path)

        from PyQt6.QtGui import QStandardItemModel

        invalid_index = QStandardItemModel().index(-1, -1)
        panel._on_file_selected(invalid_index, None)

        assert panel.preview_stack.currentWidget() is panel.preview_hint

    def test_format_size(self):
        """文件大小格式化应正确。"""
        assert ResultPanel._format_size(512) == "512.0 B"
        assert ResultPanel._format_size(1536) == "1.5 KB"
        assert "MB" in ResultPanel._format_size(2 * 1024 * 1024)
