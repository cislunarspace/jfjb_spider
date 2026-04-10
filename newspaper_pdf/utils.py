"""共享工具函数。

提取自两个爬虫中完全相同的工具方法，避免代码重复。
所有函数均为纯函数（无副作用），可直接作为模块级函数调用。
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup


def normalize_space(text: str) -> str:
    """标准化空白字符。

    将所有连续空白（包括 \\xa0 不换行空格）替换为单个空格，并去除首尾空白。
    报纸网页中的文本经常包含不规则的空白字符，需要在处理前统一标准化。

    Args:
        text: 待处理的原始文本

    Returns:
        标准化后的文本
    """
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def html_to_paragraphs(raw_html: str) -> list[str]:
    """将 HTML 片段转换为纯文本段落列表。

    处理流程：
    1. 去除 <script> 和 <style> 标签
    2. 提取所有 <p> 标签的文本内容
    3. 如果没有 <p> 标签，则提取整个 HTML 的纯文本作为回退

    Args:
        raw_html: HTML 片段字符串

    Returns:
        段落文本列表。如果内容为空则返回 ["正文为空"]
    """
    if not raw_html.strip():
        return ["正文为空"]

    soup = BeautifulSoup(raw_html, "html.parser")
    # 移除脚本和样式标签，避免其内容混入正文
    for tag in soup(["script", "style"]):
        tag.decompose()

    paragraphs: list[str] = []
    for paragraph in soup.find_all("p"):
        text = normalize_space(paragraph.get_text(" ", strip=True))
        if text:
            paragraphs.append(text)

    if paragraphs:
        return paragraphs

    # 回退：直接提取整个 HTML 的纯文本
    fallback = normalize_space(soup.get_text("\n", strip=True))
    return [fallback] if fallback else ["正文为空"]


def safe_filename(value: str) -> str:
    """将字符串转换为安全的文件名。

    处理规则：
    1. 将 Windows/Linux 文件名中不允许的字符替换为下划线
    2. 合并多余空白
    3. 去除末尾的点号（Windows 不允许）
    4. 截断至 180 个字符以内

    Args:
        value: 原始字符串

    Returns:
        安全的文件名字符串
    """
    value = re.sub(r"[\\/:*?\"<>|]", "_", value)
    value = re.sub(r"\s+", " ", value).strip().rstrip(".")
    return value[:180] if len(value) > 180 else value
