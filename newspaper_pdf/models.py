"""统一数据模型。

定义了 Article 数据类，作为爬虫与 PDF 导出器之间的数据传输对象。
两个爬虫（解放军报、人民日报）共用同一个数据模型。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Article:
    """报纸文章数据模型。

    Attributes:
        paper_name: 报纸名称（如 "解放军报"、"人民日报"）
        paper_date: 报纸日期，格式 YYYY-MM-DD
        paper_number: 版面编号（如 "01"、"02"）
        section_name: 版面名称（如 "要闻"、"国内新闻"）
        article_index: 文章在版面中的序号（从 1 开始）
        title: 文章标题
        subtitle: 文章副标题，无则为空字符串
        author: 作者信息，无则为空字符串
        paragraphs: 正文段落列表
        source_url: 文章原始链接
    """

    paper_name: str
    paper_date: str
    paper_number: str
    section_name: str
    article_index: int
    title: str
    subtitle: str
    author: str
    paragraphs: list[str]
    source_url: str
