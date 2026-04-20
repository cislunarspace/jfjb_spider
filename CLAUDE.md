# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Two Python web spiders that scrape Chinese newspaper articles and export them as formatted PDFs with proper Chinese typography and mixed CJK/Latin font support.

- `jfjb.py` — PLA Daily (解放军报) from `81.cn` (JSON API-based)
- `rmrb.py` — People's Daily (人民日报) from `paper.people.com.cn` (HTML scraping)

## Commands

```bash
# Install dependencies
uv sync

# Run spiders (CLI)
uv run python -m newspaper_pdf.jfjb_spider        # Today's PLA Daily
uv run python -m newspaper_pdf.jfjb_spider --date 2026-03-10
uv run python -m newspaper_pdf.jfjb_spider --start-date 2026-01-01 --delay 2  # Batch
uv run python -m newspaper_pdf.rmrb_spider        # Today's People's Daily
uv run python -m newspaper_pdf.rmrb_spider --date 2026-03-10

# Run GUI
uv run newspaper-pdf-ui

# Lint
uv run ruff check .
```

## Architecture

### Package Structure (`newspaper_pdf/`)

| Module | Responsibility |
|--------|---------------|
| `models.py` | `Article` dataclass (shared DTO) |
| `fonts.py` | Cross-platform font discovery (Windows/Linux/macOS) + ReportLab registration |
| `pdf.py` | `PDFExporter`, `BookmarkDocTemplate`, `BookmarkFlowable` — all PDF generation |
| `utils.py` | `normalize_space`, `html_to_paragraphs`, `safe_filename` |
| `network.py` | HTTP session factory + `retry_get` with exponential backoff |
| `cli.py` | Shared argparse argument factory + `setup_logging` + font path extraction |
| `jfjb_spider.py` | `JFJBSpider` class + batch mode logic + CLI |
| `rmrb_spider.py` | `RMRBSpider` class + CLI |
| `gui/app.py` | PyQt6 主窗口 + QApplication 入口 |
| `gui/crawl_panel.py` | 抓取面板：参数配置、进度条、日志 |
| `gui/result_panel.py` | 结果浏览面板：文件树 + PDF 渲染 |
| `gui/workers.py` | QThread 后台抓取任务 |
| `gui/styles.py` | 全局 QSS 样式表 |

### Key Design Decisions

- Two Spider classes stay independent (no shared base class) — JFJB uses JSON API, RMRB scrapes HTML
- `PDFExporter` is parameterized by `style_prefix` to produce unique style names per newspaper
- Font discovery: CLI args > env vars > system dirs > CJK fallback fonts. Raises `RuntimeError` with Chinese instructions if no CJK font found
- `_MIXED_FONT_PATTERN` is a pre-compiled module-level regex (fixes the divergent regex bug that existed between the two old files)

## Conventions

- All comments, docstrings, user-facing text, and commit messages are in Chinese
- Conventional commits: `feat:`, `chore:`, `fix:`
- Python 3.10+: `from __future__ import annotations`, `str | None`, `slots=True` dataclasses
- Use `logging` module instead of `print()` for all output
- Use `pathlib.Path` exclusively (no `os.path`)
