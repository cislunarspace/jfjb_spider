"""纯工具函数测试。"""

from __future__ import annotations

import pytest

from newspaper_pdf.utils import html_to_paragraphs, normalize_space, safe_filename


# ── normalize_space ──────────────────────────────────────────────────────────


@pytest.mark.unit
class TestNormalizeSpace:
    def test_collapses_whitespace(self) -> None:
        assert normalize_space("hello   world") == "hello world"

    def test_replaces_nbsp(self) -> None:
        assert normalize_space("hello\xa0world") == "hello world"

    def test_strips_edges(self) -> None:
        assert normalize_space("  hello  ") == "hello"

    def test_empty_string(self) -> None:
        assert normalize_space("") == ""

    def test_only_whitespace(self) -> None:
        assert normalize_space("   \t\n  ") == ""

    def test_mixed_nbsp_and_spaces(self) -> None:
        assert normalize_space("a\xa0 \xa0b") == "a b"

    def test_tabs_and_newlines(self) -> None:
        assert normalize_space("a\t\nb") == "a b"


# ── html_to_paragraphs ──────────────────────────────────────────────────────


@pytest.mark.unit
class TestHtmlToParagraphs:
    def test_basic_p_tags(self) -> None:
        result = html_to_paragraphs("<p>one</p><p>two</p>")
        assert result == ["one", "two"]

    def test_strips_script(self) -> None:
        result = html_to_paragraphs('<script>alert(1)</script><p>text</p>')
        assert result == ["text"]

    def test_strips_style(self) -> None:
        result = html_to_paragraphs('<style>.x{color:red}</style><p>text</p>')
        assert result == ["text"]

    def test_empty_html(self) -> None:
        assert html_to_paragraphs("") == ["正文为空"]

    def test_whitespace_only(self) -> None:
        assert html_to_paragraphs("   ") == ["正文为空"]

    def test_no_p_tags_fallback(self) -> None:
        result = html_to_paragraphs("<div>hello<br/>world</div>")
        assert len(result) == 1
        assert "hello" in result[0]

    def test_empty_p_tags_skipped(self) -> None:
        result = html_to_paragraphs("<p></p><p>real</p>")
        assert result == ["real"]

    def test_nested_tags(self) -> None:
        result = html_to_paragraphs("<p>outer <span>inner</span> end</p>")
        assert result == ["outer inner end"]

    def test_multiple_paragraphs(self) -> None:
        result = html_to_paragraphs("<p>第一段</p><p>第二段</p><p>第三段</p>")
        assert len(result) == 3

    def test_script_between_paragraphs(self) -> None:
        html = "<p>before</p><script>bad()</script><p>after</p>"
        result = html_to_paragraphs(html)
        assert result == ["before", "after"]


# ── safe_filename ────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestSafeFilename:
    def test_basic(self) -> None:
        assert safe_filename("hello.pdf") == "hello.pdf"

    def test_replaces_special_chars(self) -> None:
        result = safe_filename('a/b\\c:d*e?f')
        assert "/" not in result
        assert "\\" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result

    def test_collapses_whitespace(self) -> None:
        result = safe_filename("a   b")
        assert "  " not in result
        assert result == "a b"

    def test_strips_trailing_dot(self) -> None:
        assert safe_filename("hello.").rstrip() == "hello"

    def test_truncates_long(self) -> None:
        long_name = "a" * 200
        result = safe_filename(long_name)
        assert len(result) <= 180

    def test_preserves_short(self) -> None:
        short = "a" * 50
        assert safe_filename(short) == short

    def test_unicode(self) -> None:
        result = safe_filename("解放军报_要闻")
        assert result == "解放军报_要闻"

    def test_mixed_special(self) -> None:
        result = safe_filename("第1版: 要闻|新闻")
        assert ":" not in result
        assert "|" not in result

    def test_replaces_angle_brackets(self) -> None:
        result = safe_filename("a<b>c")
        assert "<" not in result
        assert ">" not in result
