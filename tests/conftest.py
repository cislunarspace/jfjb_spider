"""共享测试 fixtures。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from newspaper_pdf.models import Article

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_article() -> Article:
    """返回一个完全填充的 Article 实例。"""
    return Article(
        paper_name="解放军报",
        paper_date="2026-03-10",
        paper_number="01",
        section_name="要闻",
        article_index=1,
        title="测试文章标题",
        subtitle="测试副标题",
        author="测试作者",
        paragraphs=["第一段内容。", "第二段内容。"],
        source_url="https://www.81.cn/szb_223187/szbxq/index.html?paperName=jfjb&paperDate=2026-03-10&paperNumber=01",
    )


@pytest.fixture
def jfjb_payload() -> dict:
    """加载 JFJB API 响应 fixture。"""
    path = FIXTURES_DIR / "jfjb_index.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def rmrb_section_html() -> str:
    """加载 RMRB 版面页 HTML fixture。"""
    return (FIXTURES_DIR / "rmrb_section.html").read_text(encoding="utf-8")


@pytest.fixture
def rmrb_article_html() -> str:
    """加载 RMRB 文章页 HTML fixture。"""
    return (FIXTURES_DIR / "rmrb_article.html").read_text(encoding="utf-8")
