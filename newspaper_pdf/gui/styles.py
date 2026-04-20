"""全局 QSS 样式表。

定义简约实用风格的统一样式，包含：
- 灰色背景 + 白色面板 + 蓝色强调色
- 圆角按钮、扁平输入框
- Tab 栏下划线指示器
"""

from __future__ import annotations

APP_STYLESHEET = """
/* ===== 全局 ===== */
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    font-family: "Microsoft YaHei", "SimHei", "PingFang SC", sans-serif;
    font-size: 14px;
    color: #1f2937;
}

/* ===== Tab 栏 ===== */
QTabWidget::pane {
    border: 1px solid #e5e7eb;
    background-color: #ffffff;
    border-radius: 4px;
}

QTabBar::tab {
    background: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 10px 24px;
    color: #6b7280;
    font-size: 15px;
}

QTabBar::tab:selected {
    color: #2563eb;
    border-bottom: 3px solid #2563eb;
}

QTabBar::tab:hover:!selected {
    color: #374151;
    border-bottom: 3px solid #d1d5db;
}

/* ===== 按钮 ===== */
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 14px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #93c5fd;
    color: #e5e7eb;
}

QPushButton#btnSecondary {
    background-color: #ffffff;
    color: #374151;
    border: 1px solid #d1d5db;
}

QPushButton#btnSecondary:hover {
    background-color: #f9fafb;
    border-color: #9ca3af;
}

/* ===== 输入框 ===== */
QLineEdit, QDateEdit, QComboBox {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 6px 12px;
    background-color: #ffffff;
    min-height: 22px;
}

QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
    border-color: #2563eb;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

/* ===== 复选框 / 单选按钮 ===== */
QCheckBox, QRadioButton {
    spacing: 8px;
    color: #374151;
}

/* ===== 进度条 ===== */
QProgressBar {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background-color: #f3f4f6;
    height: 20px;
    text-align: center;
    color: #374151;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 5px;
}

/* ===== 日志文本区 ===== */
QTextEdit {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #334155;
    border-radius: 6px;
    font-family: "Consolas", "Source Code Pro", monospace;
    font-size: 13px;
    padding: 8px;
}

QTextEdit#logError {
    color: #f87171;
}

/* ===== 文件树 ===== */
QTreeView {
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    background-color: #ffffff;
    alternate-background-color: #f9fafb;
}

QTreeView::item:selected {
    background-color: #dbeafe;
    color: #1e40af;
}

/* ===== 分割器 ===== */
QSplitter::handle {
    background-color: #e5e7eb;
    width: 1px;
}

/* ===== 标签 ===== */
QLabel#headingLabel {
    font-size: 16px;
    font-weight: bold;
    color: #111827;
}

QLabel#hintLabel {
    color: #9ca3af;
    font-size: 13px;
}
"""