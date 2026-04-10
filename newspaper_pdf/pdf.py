"""PDF 导出模块。

提供将报纸文章导出为 PDF 文件的核心功能，包括：
- PDFExporter: 主导出类，负责生成单篇和合集 PDF
- BookmarkDocTemplate: 支持书签目录的 PDF 文档模板
- BookmarkFlowable: 不可见的书签占位元素

PDF 使用 ReportLab Platypus 框架构建。
排版风格：黑体标题 + 宋体正文 + Times New Roman 英文混排。
"""

from __future__ import annotations

import html
import logging
import re
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer

from newspaper_pdf.fonts import register_fonts
from newspaper_pdf.models import Article
from newspaper_pdf.utils import safe_filename

logger = logging.getLogger(__name__)

# 预编译正则：匹配连续的英文字母、数字、空格和英文标点
# 用于中英文混排时将英文片段用 <font> 标签包裹
# 注意：包含下划线 _ 和反斜杠 \，以正确处理 URL 和技术文本
_MIXED_FONT_PATTERN = re.compile(
    r"([a-zA-Z0-9\s.,!?;:'\"()\-@#$%^&*+=_|~`/<>\[\]{}\\]+)"
)


class BookmarkDocTemplate(SimpleDocTemplate):
    """支持 PDF 书签（大纲）的文档模板。

    继承自 ReportLab 的 SimpleDocTemplate，重写 afterFlowable 方法，
    在构建 PDF 过程中自动处理书签注册。当文档中的 Flowable 对象
    携带 bookmark_title、bookmark_key、bookmark_level 属性时，
    自动将其添加到 PDF 大纲中。
    """

    def afterFlowable(self, flowable: object) -> None:
        """在每个 Flowable 渲染后检查是否需要添加书签。"""
        bookmark_title = getattr(flowable, "bookmark_title", None)
        bookmark_key = getattr(flowable, "bookmark_key", None)
        bookmark_level = getattr(flowable, "bookmark_level", None)

        if not bookmark_title or not bookmark_key or bookmark_level is None:
            return

        # 首次添加书签时激活 PDF 大纲视图
        if not getattr(self, "_outline_enabled", False):
            self.canv.showOutline()
            self._outline_enabled = True

        self.canv.bookmarkPage(bookmark_key)
        self.canv.addOutlineEntry(bookmark_title, bookmark_key, bookmark_level)


class BookmarkFlowable(Flowable):
    """不可见的书签占位元素。

    在 PDF 文档中不占用空间，仅用于在特定位置插入书签。
    配合 BookmarkDocTemplate 使用，实现 PDF 大纲的层级结构。

    Attributes:
        bookmark_title: 书签显示标题
        bookmark_key: 书签唯一标识
        bookmark_level: 书签层级（0 为顶层，1 为子项）
    """

    def __init__(self, title: str, key: str, level: int) -> None:
        super().__init__()
        self.bookmark_title = title
        self.bookmark_key = key
        self.bookmark_level = level

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:
        """返回 (0, 0)，不占空间。"""
        return (0, 0)

    def draw(self) -> None:
        """不绘制任何内容。"""
        return None


class PDFExporter:
    """报纸文章 PDF 导出器。

    将 Article 列表导出为格式化的 PDF 文件，支持：
    - 单篇导出：每篇文章生成独立的 PDF 文件，按版面分目录存放
    - 合集导出：所有文章合并为一个 PDF，含书签目录

    PDF 排版风格：
    - 标题：黑体（SimHei），20pt，居中
    - 副标题：黑体，11.5pt，居中
    - 元信息（版面、来源）：宋体（SimSun），9.5pt
    - 正文：宋体，11.5pt，首行缩进 24pt
    - 英文字符自动切换为 Times New Roman
    """

    def __init__(
        self,
        style_prefix: str = "Newspaper",
        custom_font_paths: dict[str, Path] | None = None,
        font_dir: Path | None = None,
    ) -> None:
        """初始化 PDF 导出器。

        Args:
            style_prefix: 段落样式名称前缀，用于区分不同报纸
            custom_font_paths: 用户指定的字体路径映射
            font_dir: 用户指定的字体目录
        """
        self._style_prefix = style_prefix
        self._registered_fonts = register_fonts(custom_font_paths, font_dir)
        self.styles = self._build_styles()

    def export_articles(
        self,
        articles: list[Article],
        output_dir: Path,
        export_individual: bool,
        export_combined: bool,
    ) -> tuple[list[Path], Path | None]:
        """导出文章为 PDF 文件。

        Args:
            articles: 文章列表
            output_dir: 输出根目录
            export_individual: 是否导出单篇 PDF
            export_combined: 是否导出合集 PDF

        Returns:
            (单篇 PDF 路径列表, 合集 PDF 路径)。合集未生成时为 None。
        """
        if not articles:
            logger.warning("文章列表为空，跳过导出")
            return ([], None)

        output_dir.mkdir(parents=True, exist_ok=True)
        article_paths: list[Path] = []

        # 导出单篇 PDF
        if export_individual:
            for article in articles:
                section_dir = output_dir / safe_filename(
                    f"第{article.paper_number}版_{article.section_name}"
                )
                section_dir.mkdir(parents=True, exist_ok=True)
                filename = safe_filename(
                    f"{article.article_index:02d}_{article.title}.pdf"
                )
                pdf_path = section_dir / filename
                self._build_pdf(
                    pdf_path, self._build_article_story(article, include_header=True)
                )
                article_paths.append(pdf_path)

        # 导出合集 PDF
        combined_path: Path | None = None
        if export_combined:
            combined_path = output_dir / safe_filename(
                f"{articles[0].paper_name}_{articles[0].paper_date}_全集.pdf"
            )
            story: list = []
            current_section: tuple[str, str] | None = None

            for index, article in enumerate(articles):
                # 版面变化时插入版面书签
                section = (article.paper_number, article.section_name)
                if section != current_section:
                    story.append(
                        BookmarkFlowable(
                            title=f"第{article.paper_number}版 {article.section_name}",
                            key=f"section-{article.paper_number}",
                            level=0,
                        )
                    )
                    current_section = section

                # 插入文章内容（带文章级书签）
                story.extend(
                    self._build_article_story(
                        article,
                        include_header=True,
                        bookmark_title=article.title,
                        bookmark_key=f"article-{index + 1:04d}",
                    )
                )

                # 文章之间插入分页符（最后一篇除外）
                if index != len(articles) - 1:
                    story.append(PageBreak())

            self._build_pdf(combined_path, story)

        return article_paths, combined_path

    def _build_styles(self) -> dict[str, ParagraphStyle]:
        """构建 PDF 段落样式集合。

        使用 ReportLab 的 ParagraphStyle 定义标题、副标题、元信息和正文四种样式。
        所有样式均启用 wordWrap="CJK" 以支持中文自动换行。

        Returns:
            样式名称到 ParagraphStyle 对象的映射
        """
        sample = getSampleStyleSheet()
        prefix = self._style_prefix

        return {
            "title": ParagraphStyle(
                f"{prefix}Title",
                parent=sample["Title"],
                fontName="SimHei",
                fontSize=20,
                leading=28,
                alignment=TA_CENTER,
                textColor=HexColor("#111827"),
                wordWrap="CJK",
                spaceAfter=8,
            ),
            "subtitle": ParagraphStyle(
                f"{prefix}Subtitle",
                parent=sample["Normal"],
                fontName="SimHei",
                fontSize=11.5,
                leading=18,
                alignment=TA_CENTER,
                textColor=HexColor("#4b5563"),
                wordWrap="CJK",
                spaceAfter=10,
            ),
            "meta": ParagraphStyle(
                f"{prefix}Meta",
                parent=sample["Normal"],
                fontName="SimSun",
                fontSize=9.5,
                leading=14,
                textColor=HexColor("#6b7280"),
                wordWrap="CJK",
                spaceAfter=6,
            ),
            "body": ParagraphStyle(
                f"{prefix}Body",
                parent=sample["BodyText"],
                fontName="SimSun",
                fontSize=11.5,
                leading=20,
                firstLineIndent=24,
                textColor=HexColor("#111827"),
                wordWrap="CJK",
                spaceAfter=6,
            ),
        }

    def _build_article_story(
        self,
        article: Article,
        include_header: bool,
        bookmark_title: str | None = None,
        bookmark_key: str | None = None,
    ) -> list:
        """构建单篇文章的 PDF 故事流。

        Args:
            article: 文章数据
            include_header: 是否包含标题区域
            bookmark_title: 书签标题（合集模式下用于二级书签）
            bookmark_key: 书签唯一键

        Returns:
            ReportLab Flowable 列表
        """
        story: list = []
        title = _escape(article.title)
        subtitle = _escape(article.subtitle)
        page_label = _escape(
            f"第{article.paper_number}版 | {article.section_name}"
        )
        source_url = _escape(article.source_url)
        has_english_font = "TimesNewRoman" in self._registered_fonts

        if include_header:
            # 标题（黑体，不需要英文字体混排）
            title_paragraph = Paragraph(title, self.styles["title"])
            if bookmark_title and bookmark_key:
                setattr(title_paragraph, "bookmark_title", bookmark_title)
                setattr(title_paragraph, "bookmark_key", bookmark_key)
                setattr(title_paragraph, "bookmark_level", 1)
            story.append(title_paragraph)

            if subtitle:
                story.append(Paragraph(subtitle, self.styles["subtitle"]))

            # 元信息（宋体 + Times New Roman 混排）
            if has_english_font:
                story.append(
                    Paragraph(format_mixed_font(page_label), self.styles["meta"])
                )
                story.append(
                    Paragraph(format_mixed_font(f"来源：{source_url}"), self.styles["meta"])
                )
            else:
                story.append(Paragraph(page_label, self.styles["meta"]))
                story.append(Paragraph(f"来源：{source_url}", self.styles["meta"]))
            story.append(Spacer(1, 4 * mm))

        # 正文段落（宋体 + Times New Roman 混排）
        for paragraph in article.paragraphs:
            escaped = _escape(paragraph)
            if has_english_font:
                formatted_text = format_mixed_font(escaped)
            else:
                formatted_text = escaped
            story.append(Paragraph(formatted_text, self.styles["body"]))

        return story

    def _build_pdf(self, pdf_path: Path, story: list) -> None:
        """将故事流构建为 PDF 文件。

        Args:
            pdf_path: 输出 PDF 文件路径
            story: ReportLab Flowable 列表
        """
        document = BookmarkDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=pdf_path.stem,
        )
        document.build(story)


def _escape(text: str) -> str:
    """转义文本中的 XML 特殊字符，并处理换行。

    ReportLab 的 Paragraph 使用类似 XML 的标记语法，
    需要转义 <、>、& 等字符。换行符转换为 <br/> 标签。

    Args:
        text: 原始文本

    Returns:
        转义后的安全文本
    """
    return html.escape(text, quote=False).replace("\n", "<br/>")


def format_mixed_font(
    text: str,
    chinese_font: str = "SimSun",
    english_font: str = "TimesNewRoman",
) -> str:
    """处理中英文混排文本的字体切换。

    通过正则表达式识别连续的英文字符片段（包括数字和英文标点），
    用 ReportLab 的 <font> 标签包裹，使其渲染时使用英文字体。
    中文片段保持使用中文字体。

    这种方法避免了中文字体渲染英文字符时的字形不美观问题。

    Args:
        text: 待处理的文本（已转义）
        chinese_font: 中文字体注册名，默认宋体
        english_font: 英文字体注册名，默认 Times New Roman

    Returns:
        带有 <font> 标签的混合字体文本
    """
    parts = _MIXED_FONT_PATTERN.split(text)
    result: list[str] = []

    for part in parts:
        if not part:
            continue
        if _MIXED_FONT_PATTERN.fullmatch(part):
            # 跳过纯空白片段，避免无意义的 <font> 包裹
            if part.strip():
                result.append(f'<font name="{english_font}">{part}</font>')
            else:
                result.append(part)
        else:
            result.append(part)

    return "".join(result)
