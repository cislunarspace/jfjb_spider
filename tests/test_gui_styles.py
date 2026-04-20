"""GUI 样式表单元测试。"""

from __future__ import annotations

from newspaper_pdf.gui.styles import APP_STYLESHEET


def test_stylesheet_is_non_empty_string() -> None:
    """样式表应该是非空字符串。"""
    assert isinstance(APP_STYLESHEET, str)
    assert len(APP_STYLESHEET) > 0


def test_stylesheet_contains_key_selectors() -> None:
    """样式表应包含关键选择器。"""
    selectors = [
        "QMainWindow",
        "QTabWidget",
        "QPushButton",
        "QLineEdit",
        "QComboBox",
        "QProgressBar",
        "QTextEdit",
    ]
    for selector in selectors:
        assert selector in APP_STYLESHEET, f"缺少选择器: {selector}"


def test_stylesheet_uses_accent_color() -> None:
    """样式表应使用设计指定的蓝色强调色。"""
    assert "#2563eb" in APP_STYLESHEET