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
