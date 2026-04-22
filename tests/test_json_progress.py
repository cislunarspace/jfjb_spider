"""--json-progress 输出格式测试。"""

from __future__ import annotations

import json

import pytest

from newspaper_pdf.cli import emit_progress, emit_log, emit_finished, emit_error


@pytest.mark.unit
def test_emit_progress_outputs_valid_json(capsys):
    emit_progress(current=3, total=10, message="正在抓取 2026-03-10")
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())
    assert data["type"] == "progress"
    assert data["current"] == 3
    assert data["total"] == 10
    assert data["message"] == "正在抓取 2026-03-10"


@pytest.mark.unit
def test_emit_log_outputs_valid_json(capsys):
    emit_log(level="INFO", message="已获取 15 篇文章")
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())
    assert data["type"] == "log"
    assert data["level"] == "INFO"
    assert data["message"] == "已获取 15 篇文章"


@pytest.mark.unit
def test_emit_finished_outputs_valid_json(capsys):
    emit_finished(success=10, fail=0, skip=2, total=12)
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())
    assert data["type"] == "finished"
    assert data["success"] == 10
    assert data["fail"] == 0
    assert data["skip"] == 2
    assert data["total"] == 12


@pytest.mark.unit
def test_emit_error_outputs_valid_json(capsys):
    emit_error(message="网络超时")
    captured = capsys.readouterr()
    data = json.loads(captured.out.strip())
    assert data["type"] == "error"
    assert data["message"] == "网络超时"


@pytest.mark.unit
def test_jfjb_main_json_progress_single_day(capsys):
    """单日模式 --json-progress 输出包含 progress 和 finished 事件。"""
    from unittest.mock import patch, MagicMock
    from newspaper_pdf.jfjb_spider import main

    mock_article = MagicMock()
    mock_article.title = "测试文章"

    with patch("newspaper_pdf.jfjb_spider.setup_logging"), \
         patch("newspaper_pdf.jfjb_spider.JFJBSpider") as MockSpider, \
         patch("newspaper_pdf.jfjb_spider.PDFExporter") as MockExporter:
        instance = MockSpider.return_value
        instance.resolve_paper_date.return_value = "2026-03-10"
        instance.fetch_index_payload.return_value = {}
        instance.parse_articles.return_value = [mock_article]

        exporter = MockExporter.return_value
        exporter.export_articles.return_value = (["/fake/path.pdf"], None)

        with patch("sys.argv", ["jfjb_spider", "--json-progress", "--date", "2026-03-10"]):
            main()

    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().split("\n") if l]
    types = [json.loads(l)["type"] for l in lines]
    assert "progress" in types
    assert "finished" in types


@pytest.mark.unit
def test_rmrb_main_json_progress(capsys):
    """RMRB --json-progress 输出包含 progress 和 finished 事件。"""
    from unittest.mock import patch, MagicMock
    from newspaper_pdf.rmrb_spider import main

    mock_article = MagicMock()
    mock_article.title = "测试文章"

    with patch("newspaper_pdf.rmrb_spider.setup_logging"), \
         patch("newspaper_pdf.rmrb_spider.RMRBSpider") as MockSpider, \
         patch("newspaper_pdf.rmrb_spider.PDFExporter") as MockExporter:
        instance = MockSpider.return_value
        instance.resolve_paper_date.return_value = "2026-03-10"
        instance.fetch_articles.return_value = [mock_article]

        exporter = MockExporter.return_value
        exporter.export_articles.return_value = (["/fake/path.pdf"], None)

        with patch("sys.argv", ["rmrb_spider", "--json-progress", "--date", "2026-03-10"]):
            main()

    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().split("\n") if l]
    types = [json.loads(l)["type"] for l in lines]
    assert "progress" in types
    assert "finished" in types
