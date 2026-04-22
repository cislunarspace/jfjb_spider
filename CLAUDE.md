# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Two Python web spiders that scrape Chinese newspaper articles and export them as formatted PDFs. A Rust + Vue web dashboard provides a browser-based UI for configuring crawls, monitoring progress, and browsing results.

- `jfjb.py` — PLA Daily (解放军报) from `81.cn` (JSON API-based)
- `rmrb.py` — People's Daily (人民日报) from `paper.people.com.cn` (HTML scraping)
- `server/` — Rust (Axum) web backend
- `frontend/` — Vue 3 + TypeScript SPA

## Commands

```bash
# Install dependencies
uv sync
cd server && cargo build
cd frontend && npm install

# Run spiders (CLI)
uv run python -m newspaper_pdf.jfjb_spider        # Today's PLA Daily
uv run python -m newspaper_pdf.jfjb_spider --date 2026-03-10
uv run python -m newspaper_pdf.jfjb_spider --start-date 2026-01-01 --delay 2  # Batch
uv run python -m newspaper_pdf.rmrb_spider        # Today's People's Daily
uv run python -m newspaper_pdf.rmrb_spider --date 2026-03-10

# Run web dashboard
cd server && cargo run                              # Start Rust backend
cd frontend && npm run dev                          # Start Vite dev server

# Production build
cd frontend && npm run build && cd ../server && cargo build --release

# Lint
uv run ruff check .
cd server && cargo clippy
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
| `cli.py` | Shared argparse argument factory + `setup_logging` + `--json-progress` JSON 输出 |

### Rust Server (`server/src/`)

| Module | Responsibility |
|--------|---------------|
| `main.rs` | Axum router, AppState, broadcast channel, static file serving |
| `api.rs` | REST handlers: start crawl, SSE stream, cancel, status |
| `crawler.rs` | Python subprocess management with kill/cancel support |
| `files.rs` | File listing and download from `output/` directory |
| `models.rs` | Shared types: CrawlRequest, CrawlEvent, FileInfo |
| `error.rs` | AppError enum with IntoResponse |

### Vue Frontend (`frontend/src/`)

| Module | Responsibility |
|--------|---------------|
| `api/index.ts` | API client: fetch helpers + SSE EventSource |
| `App.vue` | Layout shell: sidebar nav + router-view |
| `router.ts` | Vue Router: /crawl, /results |
| `views/CrawlView.vue` | Crawl page: form + progress log |
| `views/ResultView.vue` | Result page: file tree + PDF preview |
| `components/CrawlForm.vue` | Crawl configuration form |
| `components/ProgressLog.vue` | Progress bar + live log display |
| `components/FileTree.vue` | Collapsible file tree by date |
| `components/PdfPreview.vue` | PDF preview via iframe |

### Key Design Decisions

- Two Spider classes stay independent (no shared base class) — JFJB uses JSON API, RMRB scrapes HTML
- `PDFExporter` is parameterized by `style_prefix` to produce unique style names per newspaper
- Font discovery: CLI args > env vars > system dirs > CJK fallback fonts. Raises `RuntimeError` with Chinese instructions if no CJK font found
- `_MIXED_FONT_PATTERN` is a pre-compiled module-level regex (fixes the divergent regex bug that existed between the two old files)
- Rust server spawns Python via `uv run` with `--json-progress` flag; reads structured JSON from stdout
- SSE (Server-Sent Events) via broadcast channel for real-time crawl progress streaming
- Vue SPA served as static files by Rust server in production (`frontend/dist/`)

## Conventions

- All comments, docstrings, user-facing text, and commit messages are in Chinese
- Conventional commits: `feat:`, `chore:`, `fix:`
- Python 3.10+: `from __future__ import annotations`, `str | None`, `slots=True` dataclasses
- Use `logging` module instead of `print()` for all output
- Use `pathlib.Path` exclusively (no `os.path`)
