# Web Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [[]`) syntax for tracking.

**Goal:** Replace PyQt6 GUI with Rust (Axum) backend + Vue 3 frontend web dashboard, keeping Python spider/PDF logic unchanged.

**Architecture:** Rust web server spawns Python subprocesses with `--json-progress` flag, reads structured JSON from stdout, and pushes events to the Vue frontend via SSE. The Vue SPA is served as static files by the Rust server in production.

**Tech Stack:** Rust + Axum + tokio, Vue 3 + Vite + TypeScript, Python subprocess (existing spiders)

---

## File Map

### Files to Create

| File | Purpose |
|------|---------|
| `server/Cargo.toml` | Rust project manifest with Axum, tokio, serde dependencies |
| `server/src/main.rs` | Axum router setup, static file serving, server entry |
| `server/src/api.rs` | REST API handlers (crawl, cancel, status, files) |
| `server/src/crawler.rs` | Python subprocess management, SSE event streaming |
| `server/src/files.rs` | File listing and download handlers |
| `server/src/models.rs` | Shared data types (CrawlRequest, CrawlEvent, FileInfo) |
| `server/src/error.rs` | Error types and IntoResponse impl |
| `frontend/package.json` | Vue 3 + Vite + TS dependencies |
| `frontend/vite.config.ts` | Vite config with API proxy |
| `frontend/index.html` | SPA entry HTML |
| `frontend/src/main.ts` | Vue app bootstrap |
| `frontend/src/App.vue` | Layout shell (sidebar + content) |
| `frontend/src/router.ts` | Vue Router config |
| `frontend/src/api/index.ts` | API client (fetch + SSE) |
| `frontend/src/views/CrawlView.vue` | Crawl page (form + progress) |
| `frontend/src/views/ResultView.vue` | Result page (file list + PDF preview) |
| `frontend/src/components/CrawlForm.vue` | Crawl configuration form |
| `frontend/src/components/ProgressLog.vue` | Progress bar + live log |
| `frontend/src/components/FileTree.vue` | File list by date |
| `frontend/src/components/PdfPreview.vue` | PDF preview panel |
| `frontend/src/styles/global.css` | Global styles |

### Files to Modify

| File | Change |
|------|--------|
| `newspaper_pdf/cli.py` | Add `--json-progress` argument |
| `newspaper_pdf/jfjb_spider.py` | Add JSON progress output in `main()` |
| `newspaper_pdf/rmrb_spider.py` | Add JSON progress output in `main()` |
| `pyproject.toml` | Remove PyQt6 dep, remove `newspaper-pdf-ui` entry point, remove pytest-qt |
| `CLAUDE.md` | Update architecture docs |

### Files to Delete

| File | Reason |
|------|--------|
| `newspaper_pdf/gui/__init__.py` | PyQt6 GUI removed |
| `newspaper_pdf/gui/app.py` | PyQt6 GUI removed |
| `newspaper_pdf/gui/crawl_panel.py` | PyQt6 GUI removed |
| `newspaper_pdf/gui/result_panel.py` | PyQt6 GUI removed |
| `newspaper_pdf/gui/workers.py` | PyQt6 GUI removed |
| `newspaper_pdf/gui/styles.py` | PyQt6 GUI removed |
| `newspaper_pdf/gui/preview_server.py` | Replaced by Rust server |
| `tests/test_gui_styles.py` | PyQt6 tests removed |
| `tests/test_gui_workers.py` | PyQt6 tests removed |
| `tests/test_preview_server.py` | PyQt6 tests removed |
| `tests/test_result_panel.py` | PyQt6 tests removed |

---

## Task 1: Remove PyQt6 GUI and Clean Dependencies

**Files:**
- Delete: `newspaper_pdf/gui/` (entire directory)
- Delete: `tests/test_gui_styles.py`, `tests/test_gui_workers.py`, `tests/test_preview_server.py`, `tests/test_result_panel.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Delete PyQt6 GUI modules**

Delete the entire `newspaper_pdf/gui/` directory:
```bash
rm -rf newspaper_pdf/gui/
```

- [ ] **Step 2: Delete GUI-related tests**

```bash
rm -f tests/test_gui_styles.py tests/test_gui_workers.py tests/test_preview_server.py tests/test_result_panel.py
```

- [ ] **Step 3: Update pyproject.toml**

Edit `pyproject.toml` to remove PyQt6 dependency, pytest-qt, and the GUI entry point:

```toml
[project]
name = "newspaper-pdf"
version = "2.0.0"
description = "解放军报 / 人民日报文章 PDF 爬虫"
requires-python = ">=3.10"
dependencies = [
    "requests>=2.31,<3",
    "beautifulsoup4>=4.12,<5",
    "reportlab>=4.0,<5",
]

[project.optional-dependencies]
test = ["pytest>=8.0", "pytest-cov>=5.0", "pytest-mock>=3.12"]
docs = ["mkdocs>=1.6", "mkdocs-material>=9.5", "mkdocstrings[python]>=0.27"]

[project.scripts]
jfjb = "newspaper_pdf.jfjb_spider:main"
rmrb = "newspaper_pdf.rmrb_spider:main"
```

- [ ] **Step 4: Run existing tests to verify nothing breaks**

```bash
uv sync
uv run pytest tests/ -v --ignore=tests/test_gui_styles.py --ignore=tests/test_gui_workers.py --ignore=tests/test_preview_server.py --ignore=tests/test_result_panel.py
```
Expected: All remaining tests pass.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml newspaper_pdf/ tests/
git commit -m "chore: 移除 PyQt6 GUI，清理依赖"
```

---

## Task 2: Add `--json-progress` to Python CLI

**Files:**
- Modify: `newspaper_pdf/cli.py`
- Create: `tests/test_json_progress.py`

- [ ] **Step 1: Write failing test for JSON progress helper**

Create `tests/test_json_progress.py`:

```python
"""--json-progress 输出格式测试。"""

from __future__ import annotations

import json
from unittest.mock import patch
from io import StringIO

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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_json_progress.py -v
```
Expected: FAIL with ImportError (functions don't exist yet)

- [ ] **Step 3: Add JSON progress helper functions to cli.py**

Add the following to the end of `newspaper_pdf/cli.py`:

```python
import json
import sys


def _json_emit(obj: dict) -> None:
    """输出 JSON 行到 stdout 并立即刷新。"""
    print(json.dumps(obj, ensure_ascii=False), flush=True)


def emit_progress(*, current: int, total: int, message: str) -> None:
    """输出进度事件。"""
    _json_emit({"type": "progress", "current": current, "total": total, "message": message})


def emit_log(*, level: str, message: str) -> None:
    """输出日志事件。"""
    _json_emit({"type": "log", "level": level, "message": message})


def emit_finished(*, success: int, fail: int, skip: int, total: int) -> None:
    """输出完成事件。"""
    _json_emit({"type": "finished", "success": success, "fail": fail, "skip": skip, "total": total})


def emit_error(*, message: str) -> None:
    """输出错误事件。"""
    _json_emit({"type": "error", "message": message})
```

Also add `--json-progress` to `add_common_arguments`:

```python
parser.add_argument(
    "--json-progress",
    action="store_true",
    help="以 JSON 行格式输出进度（供 Web 服务调用）。",
)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_json_progress.py -v
```
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add newspaper_pdf/cli.py tests/test_json_progress.py
git commit -m "feat(cli): 添加 --json-progress 参数和 JSON 输出函数"
```

---

## Task 3: Wire JSON Progress into JFJB Spider main()

**Files:**
- Modify: `newspaper_pdf/jfjb_spider.py`

- [ ] **Step 1: Write failing test for JSON mode in JFJB**

Append to `tests/test_json_progress.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_json_progress.py::test_jfjb_main_json_progress_single_day -v
```
Expected: FAIL — main() still uses logger instead of emit functions.

- [ ] **Step 3: Modify jfjb_spider.py main() to support JSON mode**

In `newspaper_pdf/jfjb_spider.py`, modify the `main()` function. Add imports at the top:

```python
from newspaper_pdf.cli import (
    add_common_arguments,
    build_font_paths,
    setup_logging,
    emit_progress,
    emit_log,
    emit_finished,
    emit_error,
)
```

Replace the `main()` function:

```python
def main() -> None:
    """解放军报爬虫主入口。"""
    setup_logging()

    parser = build_argument_parser()
    args = parser.parse_args()

    if args.combined_only and args.individual_only:
        parser.error("--combined-only 与 --individual-only 不能同时使用")
    if args.date and args.start_date:
        parser.error("--date 与 --start-date 不能同时使用，单日用 --date，批量用 --start-date")

    export_individual = not args.combined_only
    export_combined = not args.individual_only
    out_dir = Path(args.out_dir)
    font_paths = build_font_paths(args)
    json_mode = args.json_progress

    spider = JFJBSpider(base_url=args.base_url)
    exporter = PDFExporter(
        style_prefix="JFJB",
        custom_font_paths=font_paths,
        font_dir=args.font_dir,
    )

    # ==================== 批量模式 ====================
    if args.start_date:
        end_date = args.end_date or date.today().strftime("%Y-%m-%d")
        dates = generate_date_range(args.start_date, end_date)
        total = len(dates)
        success_count = 0
        fail_count = 0
        skip_count = 0

        if not json_mode:
            logger.info("批量抓取: %s ~ %s，共 %d 天", args.start_date, end_date, total)
            logger.info("输出目录: %s", out_dir.resolve())
            logger.info("请求间隔: %ss | 跳过已有: %s", args.delay, args.skip_existing)
            logger.info("=" * 60)

        for i, paper_date in enumerate(dates, start=1):
            if json_mode:
                emit_progress(current=i, total=total, message=f"正在抓取 {paper_date}")
            else:
                logger.info("[%d/%d] ", i)

            # 外层检查跳过已存在日期
            date_dir = out_dir / paper_date
            if args.skip_existing and date_dir.exists() and any(date_dir.iterdir()):
                if json_mode:
                    emit_log(level="INFO", message=f"[跳过] {paper_date} — 已存在")
                else:
                    logger.info("[跳过] %s — 已存在", paper_date)
                skip_count += 1
                continue

            ok = crawl_single_date(
                spider=spider,
                exporter=exporter,
                paper_date=paper_date,
                out_dir=out_dir,
                export_individual=export_individual,
                export_combined=export_combined,
                skip_existing=False,
            )
            if ok:
                success_count += 1
            else:
                fail_count += 1

            # 请求间隔（最后一天不用等）
            if i < total:
                time.sleep(args.delay)

        if json_mode:
            emit_finished(success=success_count, fail=fail_count, skip=skip_count, total=total)
        else:
            logger.info("=" * 60)
            logger.info(
                "抓取完成: 成功 %d | 跳过 %d | 失败 %d / 共 %d 天",
                success_count, skip_count, fail_count, total,
            )
        return

    # ==================== 单日模式 ====================
    paper_date = spider.resolve_paper_date(args.date)

    if json_mode:
        emit_progress(current=1, total=1, message=f"正在抓取 {paper_date}")

    payload = spider.fetch_index_payload(paper_date)
    articles = spider.parse_articles(payload, paper_date)

    if not articles:
        if json_mode:
            emit_error(message="当天未解析到任何文章")
            return
        raise RuntimeError("当天未解析到任何文章")

    output_dir = out_dir / paper_date
    article_paths, combined_path = exporter.export_articles(
        articles=articles,
        output_dir=output_dir,
        export_individual=export_individual,
        export_combined=export_combined,
    )

    if json_mode:
        emit_log(level="INFO", message=f"日期: {paper_date}, 文章数: {len(articles)}")
        emit_finished(success=1, fail=0, skip=0, total=1)
    else:
        logger.info("日期: %s", paper_date)
        logger.info("文章数: %d", len(articles))
        if article_paths:
            logger.info("单篇 PDF: %d 个，输出目录: %s", len(article_paths), output_dir)
        if combined_path:
            logger.info("汇总 PDF: %s", combined_path)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_json_progress.py -v
```
Expected: All tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest tests/ -v
```
Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add newspaper_pdf/jfjb_spider.py tests/test_json_progress.py
git commit -m "feat(jfjb): 支持 --json-progress 模式输出结构化进度"
```

---

## Task 4: Wire JSON Progress into RMRB Spider main()

**Files:**
- Modify: `newspaper_pdf/rmrb_spider.py`

- [ ] **Step 1: Write failing test for JSON mode in RMRB**

Append to `tests/test_json_progress.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_json_progress.py::test_rmrb_main_json_progress -v
```
Expected: FAIL.

- [ ] **Step 3: Modify rmrb_spider.py main() to support JSON mode**

Update imports in `newspaper_pdf/rmrb_spider.py`:

```python
from newspaper_pdf.cli import (
    add_common_arguments,
    build_font_paths,
    setup_logging,
    emit_progress,
    emit_log,
    emit_finished,
    emit_error,
)
```

Replace the `main()` function:

```python
def main() -> None:
    """人民日报爬虫主入口。"""
    setup_logging()

    parser = build_argument_parser()
    args = parser.parse_args()

    if args.combined_only and args.individual_only:
        parser.error("--combined-only 与 --individual-only 不能同时使用")

    export_individual = not args.combined_only
    export_combined = not args.individual_only
    font_paths = build_font_paths(args)
    json_mode = args.json_progress

    spider = RMRBSpider(base_url=args.base_url)

    try:
        paper_date = spider.resolve_paper_date(args.date)
        if json_mode:
            emit_progress(current=1, total=1, message=f"正在抓取 {paper_date}")
        articles = spider.fetch_articles(paper_date)
    except requests.exceptions.HTTPError as e:
        if json_mode:
            emit_error(message=f"HTTP 错误: {e}")
        else:
            logger.error("HTTP 错误: %s", e)
        return
    except requests.exceptions.ConnectionError as e:
        if json_mode:
            emit_error(message=f"连接错误: {e}")
        else:
            logger.error("连接错误: %s", e)
        return
    except requests.exceptions.Timeout:
        if json_mode:
            emit_error(message="请求超时")
        else:
            logger.error("请求超时")
        return
    except Exception as e:
        if json_mode:
            emit_error(message=f"抓取失败: {e}")
        else:
            logger.error("抓取失败: %s", e)
        return

    if not articles:
        if json_mode:
            emit_error(message="当天未解析到任何文章")
            return
        raise RuntimeError("当天未解析到任何文章")

    output_dir = Path(args.out_dir) / paper_date
    exporter = PDFExporter(
        style_prefix="RMRB",
        custom_font_paths=font_paths,
        font_dir=args.font_dir,
    )
    article_paths, combined_path = exporter.export_articles(
        articles=articles,
        output_dir=output_dir,
        export_individual=export_individual,
        export_combined=export_combined,
    )

    if json_mode:
        emit_log(level="INFO", message=f"日期: {paper_date}, 文章数: {len(articles)}")
        emit_finished(success=1, fail=0, skip=0, total=1)
    else:
        logger.info("日期: %s", paper_date)
        logger.info("文章数: %d", len(articles))
        if article_paths:
            logger.info("单篇 PDF: %d 个，输出目录: %s", len(article_paths), output_dir)
        if combined_path:
            logger.info("汇总 PDF: %s", combined_path)
```

- [ ] **Step 4: Run tests to verify**

```bash
uv run pytest tests/test_json_progress.py -v
```
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add newspaper_pdf/rmrb_spider.py tests/test_json_progress.py
git commit -m "feat(rmrb): 支持 --json-progress 模式输出结构化进度"
```

---

## Task 5: Initialize Rust Backend Project

**Files:**
- Create: `server/Cargo.toml`
- Create: `server/src/main.rs`
- Create: `server/src/models.rs`
- Create: `server/src/error.rs`

- [ ] **Step 1: Create Cargo.toml**

```toml
[package]
name = "jfjb-server"
version = "0.1.0"
edition = "2021"

[dependencies]
axum = { version = "0.8", features = ["macros"] }
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tower-http = { version = "0.6", features = ["cors", "fs"] }
uuid = { version = "1", features = ["v4"] }
chrono = { version = "0.4", features = ["serde"] }
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
tokio-stream = { version = "0.1", features = ["sync"] }
```

- [ ] **Step 2: Create error.rs**

```rust
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};

pub type Result<T> = std::result::Result<T, AppError>;

#[derive(Debug)]
pub enum AppError {
    BadRequest(String),
    NotFound(String),
    Internal(String),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            AppError::BadRequest(msg) => (StatusCode::BAD_REQUEST, msg),
            AppError::NotFound(msg) => (StatusCode::NOT_FOUND, msg),
            AppError::Internal(msg) => (StatusCode::INTERNAL_SERVER_ERROR, msg),
        };
        let body = serde_json::json!({ "error": message });
        (status, axum::Json(body)).into_response()
    }
}

impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self {
        AppError::Internal(err.to_string())
    }
}
```

- [ ] **Step 3: Create models.rs**

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct CrawlRequest {
    pub paper_type: String,
    pub paper_date: Option<String>,
    pub start_date: Option<String>,
    pub end_date: Option<String>,
    #[serde(default = "default_output_dir")]
    pub output_dir: String,
    #[serde(default = "default_true")]
    pub export_individual: bool,
    #[serde(default = "default_true")]
    pub export_combined: bool,
    pub font_dir: Option<String>,
}

fn default_output_dir() -> String {
    "output".to_string()
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
#[serde(rename_all = "lowercase")]
pub enum CrawlEvent {
    Progress {
        current: u32,
        total: u32,
        message: String,
    },
    Log {
        level: String,
        message: String,
    },
    Finished {
        success: u32,
        fail: u32,
        skip: u32,
        total: u32,
    },
    Error {
        message: String,
    },
}

#[derive(Debug, Serialize)]
pub struct FileInfo {
    pub name: String,
    pub path: String,
    pub size: u64,
    pub modified: String,
    pub is_dir: bool,
}

#[derive(Debug, Serialize)]
pub struct CrawlStatus {
    pub running: bool,
    pub task_id: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct TaskResponse {
    pub task_id: String,
}
```

- [ ] **Step 4: Create minimal main.rs**

```rust
mod api;
mod crawler;
mod error;
mod files;
mod models;

use axum::Router;
use std::sync::Arc;
use tokio::sync::broadcast;
use tower_http::cors::CorsLayer;

pub struct AppState {
    pub crawl_tx: broadcast::Sender<models::CrawlEvent>,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "jfjb_server=debug,tower_http=debug".into()),
        )
        .init();

    let (crawl_tx, _) = broadcast::channel::<models::CrawlEvent>(100);
    let state = Arc::new(AppState { crawl_tx });

    let app = Router::new()
        .merge(api::routes())
        .merge(files::routes())
        .layer(CorsLayer::permissive())
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3000")
        .await
        .unwrap();
    tracing::info!("Server listening on http://127.0.0.1:3000");
    axum::serve(listener, app).await.unwrap();
}
```

- [ ] **Step 5: Create stub api.rs**

```rust
use axum::{
    extract::State,
    routing::{get, post},
    Json, Router,
};
use std::sync::Arc;

use crate::error::Result;
use crate::models::{CrawlRequest, CrawlStatus, TaskResponse};
use crate::AppState;

pub fn routes() -> Router<Arc<AppState>> {
    Router::new()
        .route("/api/crawl", post(start_crawl))
        .route("/api/crawl/stream", get(stream_events))
        .route("/api/crawl/cancel", post(cancel_crawl))
        .route("/api/status", get(get_status))
}

async fn start_crawl(
    State(_state): State<Arc<AppState>>,
    Json(_req): Json<CrawlRequest>,
) -> Result<Json<TaskResponse>> {
    Ok(Json(TaskResponse {
        task_id: "todo".to_string(),
    }))
}

async fn stream_events(
    State(_state): State<Arc<AppState>>,
) -> Result<axum::response::Sse<axum::body::Body>> {
    Err(crate::error::AppError::Internal("not implemented".into()))
}

async fn cancel_crawl(
    State(_state): State<Arc<AppState>>,
) -> Result<Json<serde_json::Value>> {
    Ok(Json(serde_json::json!({ "ok": true })))
}

async fn get_status(
    State(_state): State<Arc<AppState>>,
) -> Json<CrawlStatus> {
    Json(CrawlStatus {
        running: false,
        task_id: None,
    })
}
```

- [ ] **Step 6: Create stub files.rs**

```rust
use axum::{
    routing::get,
    Router,
};
use std::sync::Arc;

use crate::AppState;

pub fn routes() -> Router<Arc<AppState>> {
    Router::new()
        .route("/api/files", get(list_files))
        .route("/api/files/{*path}", get(get_file))
}

async fn list_files() -> axum::Json<Vec<crate::models::FileInfo>> {
    axum::Json(vec![])
}

async fn get_file() -> crate::error::Result<String> {
    Err(crate::error::AppError::NotFound("not implemented".into()))
}
```

- [ ] **Step 7: Verify it compiles**

```bash
cd server && cargo build
```
Expected: Compiles successfully.

- [ ] **Step 8: Commit**

```bash
git add server/
git commit -m "feat(server): 初始化 Rust 后端项目骨架"
```

---

## Task 6: Implement Crawler Subprocess Management

**Files:**
- Modify: `server/src/crawler.rs`
- Modify: `server/src/api.rs`
- Modify: `server/src/main.rs`

- [ ] **Step 1: Implement crawler.rs**

```rust
use std::process::Stdio;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::{Child, Command};
use tokio::sync::broadcast;
use tokio_stream::wrappers::BroadcastStream;

use crate::models::{CrawlEvent, CrawlRequest};

pub struct CrawlHandle {
    pub task_id: String,
    child: Child,
}

impl CrawlHandle {
    pub async fn spawn(
        request: &CrawlRequest,
        tx: &broadcast::Sender<CrawlEvent>,
    ) -> Result<Self, String> {
        let task_id = uuid::Uuid::new_v4().to_string();

        let mut cmd = Command::new("uv");
        cmd.arg("run");

        // 选择爬虫模块
        match request.paper_type.as_str() {
            "jfjb" => cmd.arg("python").arg("-m").arg("newspaper_pdf.jfjb_spider"),
            "rmrb" => cmd.arg("python").arg("-m").arg("newspaper_pdf.rmrb_spider"),
            other => return Err(format!("未知报纸类型: {other}")),
        };

        cmd.arg("--json-progress");
        cmd.arg("--out-dir").arg(&request.output_dir);

        if let Some(date) = &request.paper_date {
            cmd.arg("--date").arg(date);
        }
        if let Some(start) = &request.start_date {
            cmd.arg("--start-date").arg(start);
        }
        if let Some(end) = &request.end_date {
            cmd.arg("--end-date").arg(end);
        }
        if !request.export_individual {
            cmd.arg("--combined-only");
        }
        if !request.export_combined {
            cmd.arg("--individual-only");
        }
        if let Some(font_dir) = &request.font_dir {
            cmd.arg("--font-dir").arg(font_dir);
        }

        cmd.stdout(Stdio::piped());
        cmd.stderr(Stdio::piped());

        let mut child = cmd.spawn().map_err(|e| format!("启动 Python 进程失败: {e}"))?;

        let stdout = child.stdout.take().ok_or("无法获取 stdout")?;
        let tx_clone = tx.clone();

        tokio::spawn(async move {
            let reader = BufReader::new(stdout);
            let mut lines = reader.lines();
            while let Ok(Some(line)) = lines.next_line().await {
                if let Ok(event) = serde_json::from_str::<CrawlEvent>(&line) {
                    let _ = tx_clone.send(event);
                }
            }
        });

        // 读取 stderr 用于调试
        if let Some(stderr) = child.stderr.take() {
            let tx_err = tx.clone();
            tokio::spawn(async move {
                let reader = BufReader::new(stderr);
                let mut lines = reader.lines();
                while let Ok(Some(line)) = lines.next_line().await {
                    if !line.is_empty() {
                        let _ = tx_err.send(CrawlEvent::Log {
                            level: "ERROR".to_string(),
                            message: line,
                        });
                    }
                }
            });
        }

        Ok(Self { task_id, child })
    }

    pub fn kill(&mut self) {
        let _ = self.child.start_kill();
    }

    pub async fn wait(&mut self) -> std::io::Result<std::process::ExitStatus> {
        self.child.wait().await
    }
}
```

- [ ] **Step 2: Update api.rs with real implementations**

Replace `server/src/api.rs`:

```rust
use axum::{
    extract::State,
    response::sse::{Event, Sse},
    routing::{get, post},
    Json, Router,
};
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio_stream::wrappers::BroadcastStream;
use tokio_stream::StreamExt;

use crate::crawler::CrawlHandle;
use crate::error::Result;
use crate::models::{CrawlRequest, CrawlStatus, TaskResponse};
use crate::AppState;

pub fn routes() -> Router<Arc<AppState>> {
    Router::new()
        .route("/api/crawl", post(start_crawl))
        .route("/api/crawl/stream", get(stream_events))
        .route("/api/crawl/cancel", post(cancel_crawl))
        .route("/api/status", get(get_status))
}

async fn start_crawl(
    State(state): State<Arc<AppState>>,
    Json(req): Json<CrawlRequest>,
) -> Result<Json<TaskResponse>> {
    // 检查是否已有任务在运行
    if let Some(ref handle) = *state.crawl_handle.lock().await {
        return Err(crate::error::AppError::BadRequest(
            format!("已有任务在运行: {}", handle.task_id),
        ));
    }

    let handle = CrawlHandle::spawn(&req, &state.crawl_tx)
        .await
        .map_err(crate::error::AppError::Internal)?;

    let task_id = handle.task_id.clone();
    *state.crawl_handle.lock().await = Some(handle);

    Ok(Json(TaskResponse { task_id }))
}

async fn stream_events(
    State(state): State<Arc<AppState>>,
) -> Sse<impl tokio_stream::Stream<Item = std::result::Result<Event, std::io::Error>>> {
    let rx = state.crawl_tx.subscribe();
    let stream = BroadcastStream::new(rx).filter_map(|result| {
        result.ok().map(|event| {
            Ok(Event::default()
                .json_data(&event)
                .unwrap_or_else(|_| Event::default().data("error")))
        })
    });
    Sse::new(stream)
}

async fn cancel_crawl(
    State(state): State<Arc<AppState>>,
) -> Result<Json<serde_json::Value>> {
    let mut handle = state.crawl_handle.lock().await;
    match handle.as_mut() {
        Some(h) => {
            h.kill();
            *handle = None;
            Ok(Json(serde_json::json!({ "ok": true })))
        }
        None => Err(crate::error::AppError::BadRequest("没有正在运行的任务".into())),
    }
}

async fn get_status(
    State(state): State<Arc<AppState>>,
) -> Json<CrawlStatus> {
    let handle = state.crawl_handle.lock().await;
    Json(CrawlStatus {
        running: handle.is_some(),
        task_id: handle.as_ref().map(|h| h.task_id.clone()),
    })
}
```

- [ ] **Step 3: Update main.rs to add crawl_handle to state**

Update `server/src/main.rs`:

```rust
pub struct AppState {
    pub crawl_tx: broadcast::Sender<models::CrawlEvent>,
    pub crawl_handle: Mutex<Option<crawler::CrawlHandle>>,
}
```

Update the state construction:

```rust
use tokio::sync::Mutex;

let state = Arc::new(AppState {
    crawl_tx,
    crawl_handle: Mutex::new(None),
});
```

- [ ] **Step 4: Verify compilation**

```bash
cd server && cargo build
```
Expected: Compiles.

- [ ] **Step 5: Commit**

```bash
git add server/src/
git commit -m "feat(server): 实现 Python 子进程管理和 SSE 事件流"
```

---

## Task 7: Implement File Listing and Serving

**Files:**
- Modify: `server/src/files.rs`

- [ ] **Step 1: Implement file listing**

Replace `server/src/files.rs`:

```rust
use axum::{
    extract::{Path, Query, State},
    routing::get,
    Json, Router,
};
use serde::Deserialize;
use std::path::PathBuf;
use std::sync::Arc;
use tower_http::services::ServeFile;

use crate::error::{AppError, Result};
use crate::models::FileInfo;
use crate::AppState;

#[derive(Deserialize)]
pub struct ListQuery {
    path: Option<String>,
}

pub fn routes() -> Router<Arc<AppState>> {
    Router::new()
        .route("/api/files", get(list_files))
        .route("/api/files/{*path}", get(get_file))
}

async fn list_files(
    Query(query): Query<ListQuery>,
) -> Result<Json<Vec<FileInfo>>> {
    let base = PathBuf::from("output");
    let target = if let Some(sub) = &query.path {
        base.join(sub)
    } else {
        base
    };

    if !target.exists() {
        return Ok(Json(vec![]));
    }

    let mut entries = Vec::new();
    let mut dir = tokio::fs::read_dir(&target).await?;
    while let Some(entry) = dir.next_entry().await? {
        let metadata = entry.metadata().await?;
        let name = entry.file_name().to_string_lossy().to_string();
        let path = entry.path();
        let rel_path = path
            .strip_prefix(&base)
            .unwrap_or(&path)
            .to_string_lossy()
            .to_string();

        let modified = metadata
            .modified()
            .map(|t| {
                let datetime: chrono::DateTime<chrono::Local> = t.into();
                datetime.format("%Y-%m-%d %H:%M").to_string()
            })
            .unwrap_or_default();

        entries.push(FileInfo {
            name,
            path: rel_path,
            size: metadata.len(),
            modified,
            is_dir: metadata.is_dir(),
        });
    }

    // 目录在前，按名称排序
    entries.sort_by(|a, b| {
        b.is_dir
            .cmp(&a.is_dir)
            .then_with(|| a.name.cmp(&b.name))
    });

    Ok(Json(entries))
}

async fn get_file(
    Path(file_path): Path<String>,
) -> Result<axum::response::Response> {
    let base = PathBuf::from("output");
    let full_path = base.join(&file_path);

    if !full_path.exists() {
        return Err(AppError::NotFound(format!("文件不存在: {file_path}")));
    }

    if full_path.is_dir() {
        return Err(AppError::BadRequest("路径是目录，不是文件".into()));
    }

    // 确保路径在 base 目录内（防止路径遍历）
    let canonical = full_path.canonicalize()?;
    let canonical_base = base.canonicalize()?;
    if !canonical.starts_with(&canonical_base) {
        return Err(AppError::BadRequest("非法路径".into()));
    }

    let content = tokio::fs::read(&full_path).await?;
    let mime = if full_path.extension().is_some_and(|e| e == "pdf") {
        "application/pdf"
    } else {
        "application/octet-stream"
    };

    Ok((
        axum::http::header::CONTENT_TYPE,
        axum::http::header::CONTENT_DISPOSITION,
        axum::body::Body::from(content),
    )
        .into_response())
}
```

- [ ] **Step 2: Verify compilation**

```bash
cd server && cargo build
```
Expected: Compiles.

- [ ] **Step 3: Commit**

```bash
git add server/src/files.rs
git commit -m "feat(server): 实现文件列表和下载 API"
```

---

## Task 8: Add Static File Serving for Vue SPA

**Files:**
- Modify: `server/src/main.rs`

- [ ] **Step 1: Update main.rs to serve static files**

Add to `server/src/main.rs`:

```rust
use axum::routing::get_service;
use tower_http::services::ServeDir;

// In the routes setup, add static file serving as fallback:
let app = Router::new()
    .merge(api::routes())
    .merge(files::routes())
    .fallback_service(get_service(ServeDir::new("frontend/dist")))
    .layer(CorsLayer::permissive())
    .with_state(state);
```

- [ ] **Step 2: Verify compilation**

```bash
cd server && cargo build
```

- [ ] **Step 3: Commit**

```bash
git add server/src/main.rs
git commit -m "feat(server): 添加 Vue SPA 静态文件服务"
```

---

## Task 9: Initialize Vue 3 Frontend Project

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/tsconfig.json`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "jfjb-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5",
    "vue-router": "^4.5"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2",
    "typescript": "^5.7",
    "vite": "^6.2",
    "vue-tsc": "^2.2"
  }
}
```

- [ ] **Step 2: Create vite.config.ts**

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "preserve",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "lib": ["ESNext", "DOM"],
    "skipLibCheck": true,
    "noEmit": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.vue", "src/**/*.d.ts"]
}
```

- [ ] **Step 4: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>报刊 PDF 助手</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

- [ ] **Step 5: Create main.ts**

```ts
import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import './styles/global.css'

const app = createApp(App)
app.use(router)
app.mount('#app')
```

- [ ] **Step 6: Install dependencies and verify**

```bash
cd frontend && npm install && npm run dev
```
Expected: Vite dev server starts on port 5173.

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/vite.config.ts frontend/tsconfig.json frontend/index.html frontend/src/main.ts
git commit -m "feat(frontend): 初始化 Vue 3 + Vite + TypeScript 项目"
```

---

## Task 10: Create API Client and Router

**Files:**
- Create: `frontend/src/api/index.ts`
- Create: `frontend/src/router.ts`
- Create: `frontend/src/env.d.ts`

- [ ] **Step 1: Create api/index.ts**

```ts
export interface CrawlRequest {
  paper_type: 'jfjb' | 'rmrb'
  paper_date?: string
  start_date?: string
  end_date?: string
  output_dir: string
  export_individual: boolean
  export_combined: boolean
  font_dir?: string
}

export interface CrawlEvent {
  type: 'progress' | 'log' | 'finished' | 'error'
  current?: number
  total?: number
  message?: string
  level?: string
  success?: number
  fail?: number
  skip?: number
}

export interface FileInfo {
  name: string
  path: string
  size: number
  modified: string
  is_dir: boolean
}

export interface CrawlStatus {
  running: boolean
  task_id: string | null
}

const BASE = '/api'

export async function startCrawl(req: CrawlRequest): Promise<{ task_id: string }> {
  const res = await fetch(`${BASE}/crawl`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.error || '启动抓取失败')
  }
  return res.json()
}

export async function cancelCrawl(): Promise<void> {
  const res = await fetch(`${BASE}/crawl/cancel`, { method: 'POST' })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.error || '取消失败')
  }
}

export async function getStatus(): Promise<CrawlStatus> {
  const res = await fetch(`${BASE}/status`)
  return res.json()
}

export async function listFiles(subPath?: string): Promise<FileInfo[]> {
  const url = subPath ? `${BASE}/files?path=${encodeURIComponent(subPath)}` : `${BASE}/files`
  const res = await fetch(url)
  return res.json()
}

export function getFileUrl(filePath: string): string {
  return `${BASE}/files/${encodeURIComponent(filePath)}`
}

export function createEventSource(): EventSource {
  return new EventSource(`${BASE}/crawl/stream`)
}
```

- [ ] **Step 2: Create router.ts**

```ts
import { createRouter, createWebHistory } from 'vue-router'
import CrawlView from './views/CrawlView.vue'
import ResultView from './views/ResultView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/crawl' },
    { path: '/crawl', component: CrawlView },
    { path: '/results', component: ResultView },
  ],
})
```

- [ ] **Step 3: Create env.d.ts**

```ts
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}
```

- [ ] **Step 4: Verify TypeScript compilation**

```bash
cd frontend && npx vue-tsc --noEmit
```
Expected: No errors (after views are created in next tasks).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/index.ts frontend/src/router.ts frontend/src/env.d.ts
git commit -m "feat(frontend): 添加 API 客户端和路由配置"
```

---

## Task 11: Create App Layout and Global Styles

**Files:**
- Create: `frontend/src/App.vue`
- Create: `frontend/src/styles/global.css`

- [ ] **Step 1: Create global.css**

```css
:root {
  --bg: #f5f5f5;
  --surface: #ffffff;
  --text: #1e293b;
  --text-secondary: #64748b;
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --border: #e2e8f0;
  --error: #ef4444;
  --warning: #f59e0b;
  --success: #10b981;
  --log-bg: #1e293b;
  --log-text: #e2e8f0;
  --radius: 6px;
  --font-sans: "Microsoft YaHei", "SimHei", "PingFang SC", system-ui, sans-serif;
  --font-mono: "Cascadia Code", "Fira Code", "Consolas", monospace;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.6;
}

button {
  font-family: var(--font-sans);
  cursor: pointer;
}

input, select {
  font-family: var(--font-sans);
}
```

- [ ] **Step 2: Create App.vue**

```vue
<template>
  <div class="app-layout">
    <nav class="sidebar">
      <div class="sidebar-title">报刊 PDF 助手</div>
      <router-link to="/crawl" class="nav-link" active-class="active">
        <span class="nav-icon">&#x1F4E1;</span>
        抓取
      </router-link>
      <router-link to="/results" class="nav-link" active-class="active">
        <span class="nav-icon">&#x1F4C4;</span>
        结果
      </router-link>
    </nav>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 200px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 16px 0;
  flex-shrink: 0;
}

.sidebar-title {
  padding: 8px 20px 20px;
  font-size: 16px;
  font-weight: 700;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  transition: all 0.15s;
}

.nav-link:hover {
  background: var(--bg);
  color: var(--text);
}

.nav-link.active {
  color: var(--accent);
  background: #eff6ff;
  font-weight: 600;
}

.nav-icon {
  font-size: 18px;
}

.content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}
</style>
```

- [ ] **Step 3: Verify rendering**

```bash
cd frontend && npm run dev
```
Open browser, verify sidebar layout renders with navigation links.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.vue frontend/src/styles/global.css
git commit -m "feat(frontend): 添加应用布局和全局样式"
```

---

## Task 12: Create CrawlForm Component

**Files:**
- Create: `frontend/src/components/CrawlForm.vue`

- [ ] **Step 1: Create CrawlForm.vue**

```vue
<template>
  <div class="crawl-form">
    <h2>抓取配置</h2>

    <div class="form-group">
      <label>报纸类型</label>
      <select v-model="form.paper_type" @change="onPaperTypeChange">
        <option value="jfjb">解放军报</option>
        <option value="rmrb">人民日报</option>
      </select>
    </div>

    <div class="form-group">
      <label>抓取模式</label>
      <div class="radio-group">
        <label>
          <input type="radio" value="single" v-model="mode" /> 单日
        </label>
        <label v-if="form.paper_type === 'jfjb'">
          <input type="radio" value="batch" v-model="mode" /> 批量
        </label>
      </div>
    </div>

    <div class="form-group" v-if="mode === 'single'">
      <label>日期</label>
      <input type="date" v-model="form.paper_date" />
    </div>

    <template v-if="mode === 'batch'">
      <div class="form-group">
        <label>起始日期</label>
        <input type="date" v-model="form.start_date" />
      </div>
      <div class="form-group">
        <label>结束日期</label>
        <input type="date" v-model="form.end_date" />
      </div>
    </template>

    <div class="form-group">
      <label>输出目录</label>
      <input type="text" v-model="form.output_dir" placeholder="output" />
    </div>

    <div class="form-group">
      <label>导出选项</label>
      <div class="checkbox-group">
        <label>
          <input type="checkbox" v-model="form.export_individual" /> 单篇 PDF
        </label>
        <label>
          <input type="checkbox" v-model="form.export_combined" /> 合集 PDF
        </label>
      </div>
    </div>

    <div class="form-group">
      <label>字体目录 <span class="optional">（可选）</span></label>
      <input type="text" v-model="form.font_dir" placeholder="留空则自动发现系统字体" />
    </div>

    <div class="form-actions">
      <button class="btn-primary" :disabled="running || !isValid" @click="onSubmit">
        {{ running ? '抓取中...' : '开始抓取' }}
      </button>
      <button class="btn-secondary" :disabled="!running" @click="onCancel">
        停止
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import type { CrawlRequest } from '../api'

const emit = defineEmits<{
  submit: [req: CrawlRequest]
  cancel: []
}>()

defineProps<{ running: boolean }>()

const mode = ref<'single' | 'batch'>('single')

const form = reactive({
  paper_type: 'jfjb' as 'jfjb' | 'rmrb',
  paper_date: new Date().toISOString().slice(0, 10),
  start_date: '',
  end_date: '',
  output_dir: 'output',
  export_individual: true,
  export_combined: true,
  font_dir: '',
})

const isValid = computed(() => {
  if (mode.value === 'single') {
    return !!form.paper_date
  }
  return !!form.start_date && !!form.end_date
})

function onPaperTypeChange() {
  if (form.paper_type === 'rmrb') {
    mode.value = 'single'
    form.output_dir = 'output/rmrb'
  } else {
    form.output_dir = 'output'
  }
}

function onSubmit() {
  const req: CrawlRequest = {
    paper_type: form.paper_type,
    output_dir: form.output_dir,
    export_individual: form.export_individual,
    export_combined: form.export_combined,
  }
  if (mode.value === 'single') {
    req.paper_date = form.paper_date
  } else {
    req.start_date = form.start_date
    req.end_date = form.end_date
  }
  if (form.font_dir) {
    req.font_dir = form.font_dir
  }
  emit('submit', req)
}

function onCancel() {
  emit('cancel')
}
</script>

<style scoped>
.crawl-form {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 24px;
  border: 1px solid var(--border);
}

.crawl-form h2 {
  font-size: 18px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group > label {
  display: block;
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.optional {
  font-weight: 400;
  color: var(--text-secondary);
}

input[type='text'],
input[type='date'],
select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}

input:focus,
select:focus {
  border-color: var(--accent);
}

.radio-group,
.checkbox-group {
  display: flex;
  gap: 16px;
}

.radio-group label,
.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 400;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  padding: 10px 24px;
  border-radius: var(--radius);
  font-size: 14px;
  transition: all 0.15s;
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg);
  color: var(--text);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

- [ ] **Step 2: Verify rendering**

```bash
cd frontend && npm run dev
```
Navigate to /crawl, verify form renders with all fields.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/CrawlForm.vue
git commit -m "feat(frontend): 添加抓取配置表单组件"
```

---

## Task 13: Create ProgressLog Component

**Files:**
- Create: `frontend/src/components/ProgressLog.vue`

- [ ] **Step 1: Create ProgressLog.vue**

```vue
<template>
  <div class="progress-log">
    <h2>抓取进度</h2>

    <div class="progress-bar-container">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: percent + '%' }"></div>
      </div>
      <div class="progress-text">{{ statusText }}</div>
    </div>

    <div class="log-area" ref="logArea">
      <div
        v-for="(entry, i) in logs"
        :key="i"
        class="log-line"
        :class="'log-' + entry.level"
      >
        <span class="log-time">{{ entry.time }}</span>
        <span class="log-level">[{{ entry.level }}]</span>
        {{ entry.message }}
      </div>
      <div v-if="logs.length === 0" class="log-empty">
        等待抓取任务...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import type { CrawlEvent } from '../api'

interface LogEntry {
  time: string
  level: string
  message: string
}

const props = defineProps<{ events: CrawlEvent[] }>()

const logArea = ref<HTMLElement | null>(null)

const current = ref(0)
const total = ref(0)
const logs = ref<LogEntry[]>([])

const percent = computed(() => {
  if (total.value === 0) return 0
  return Math.round((current.value / total.value) * 100)
})

const statusText = computed(() => {
  if (total.value === 0) return '空闲'
  if (current.value >= total.value && total.value > 0) return '已完成'
  return `${current.value} / ${total.value}`
})

function now(): string {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

watch(
  () => props.events,
  (newEvents) => {
    const last = newEvents[newEvents.length - 1]
    if (!last) return

    switch (last.type) {
      case 'progress':
        current.value = last.current ?? 0
        total.value = last.total ?? 0
        logs.value.push({ time: now(), level: 'INFO', message: last.message ?? '' })
        break
      case 'log':
        logs.value.push({
          time: now(),
          level: last.level ?? 'INFO',
          message: last.message ?? '',
        })
        break
      case 'finished':
        logs.value.push({
          time: now(),
          level: 'SUCCESS',
          message: `完成: 成功 ${last.success} | 跳过 ${last.skip} | 失败 ${last.fail} / 共 ${last.total}`,
        })
        current.value = last.total ?? 0
        total.value = last.total ?? 0
        break
      case 'error':
        logs.value.push({ time: now(), level: 'ERROR', message: last.message ?? '' })
        break
    }

    nextTick(() => {
      if (logArea.value) {
        logArea.value.scrollTop = logArea.value.scrollHeight
      }
    })
  },
  { deep: true }
)

function reset() {
  current.value = 0
  total.value = 0
  logs.value = []
}

defineExpose({ reset })
</script>

<style scoped>
.progress-log {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 24px;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.progress-log h2 {
  font-size: 18px;
  margin-bottom: 16px;
}

.progress-bar-container {
  margin-bottom: 16px;
}

.progress-bar {
  height: 8px;
  background: var(--border);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 13px;
  color: var(--text-secondary);
}

.log-area {
  flex: 1;
  min-height: 200px;
  max-height: 400px;
  overflow-y: auto;
  background: var(--log-bg);
  border-radius: var(--radius);
  padding: 12px;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
}

.log-line {
  color: var(--log-text);
  white-space: pre-wrap;
  word-break: break-all;
}

.log-time {
  color: #94a3b8;
  margin-right: 8px;
}

.log-level {
  margin-right: 8px;
  font-weight: 600;
}

.log-ERROR .log-level,
.log-ERROR {
  color: var(--error);
}

.log-WARNING .log-level {
  color: var(--warning);
}

.log-SUCCESS .log-level,
.log-SUCCESS {
  color: var(--success);
}

.log-empty {
  color: #64748b;
  text-align: center;
  padding: 40px 0;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ProgressLog.vue
git commit -m "feat(frontend): 添加进度和日志显示组件"
```

---

## Task 14: Create CrawlView Page

**Files:**
- Create: `frontend/src/views/CrawlView.vue`

- [ ] **Step 1: Create CrawlView.vue**

```vue
<template>
  <div class="crawl-view">
    <div class="crawl-left">
      <CrawlForm :running="running" @submit="onSubmit" @cancel="onCancel" />
    </div>
    <div class="crawl-right">
      <ProgressLog ref="progressLog" :events="events" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CrawlForm from '../components/CrawlForm.vue'
import ProgressLog from '../components/ProgressLog.vue'
import {
  startCrawl,
  cancelCrawl,
  createEventSource,
  type CrawlRequest,
  type CrawlEvent,
} from '../api'

const router = useRouter()
const running = ref(false)
const events = ref<CrawlEvent[]>([])
const progressLog = ref<InstanceType<typeof ProgressLog> | null>(null)
let eventSource: EventSource | null = null

async function onSubmit(req: CrawlRequest) {
  try {
    running.value = true
    events.value = []
    progressLog.value?.reset()

    const { task_id } = await startCrawl(req)

    eventSource = createEventSource()
    eventSource.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as CrawlEvent
        events.value.push(event)

        if (event.type === 'finished' || event.type === 'error') {
          eventSource?.close()
          eventSource = null
          running.value = false

          if (event.type === 'finished') {
            setTimeout(() => router.push('/results'), 1000)
          }
        }
      } catch {
        // ignore parse errors
      }
    }

    eventSource.onerror = () => {
      eventSource?.close()
      eventSource = null
      running.value = false
    }
  } catch (err) {
    running.value = false
    events.value.push({
      type: 'error',
      message: err instanceof Error ? err.message : '启动失败',
    })
  }
}

async function onCancel() {
  try {
    await cancelCrawl()
  } catch {
    // ignore
  }
  eventSource?.close()
  eventSource = null
  running.value = false
}
</script>

<style scoped>
.crawl-view {
  display: flex;
  gap: 24px;
  height: 100%;
}

.crawl-left {
  width: 400px;
  flex-shrink: 0;
}

.crawl-right {
  flex: 1;
  min-width: 0;
}

@media (max-width: 900px) {
  .crawl-view {
    flex-direction: column;
  }
  .crawl-left {
    width: 100%;
  }
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/CrawlView.vue
git commit -m "feat(frontend): 添加抓取页面（表单 + 进度）"
```

---

## Task 15: Create FileTree and PdfPreview Components

**Files:**
- Create: `frontend/src/components/FileTree.vue`
- Create: `frontend/src/components/PdfPreview.vue`

- [ ] **Step 1: Create FileTree.vue**

```vue
<template>
  <div class="file-tree">
    <div class="tree-header">
      <h2>输出文件</h2>
      <button class="btn-small" @click="loadFiles">刷新</button>
    </div>

    <div class="tree-content">
      <div v-if="loading" class="tree-loading">加载中...</div>
      <div v-else-if="dirs.length === 0" class="tree-empty">暂无输出文件</div>

      <div v-for="dir in dirs" :key="dir.path" class="dir-group">
        <div class="dir-header" @click="toggleDir(dir.path)">
          <span class="dir-arrow">{{ expanded.has(dir.path) ? '&#9660;' : '&#9654;' }}</span>
          <span class="dir-name">{{ dir.name }}</span>
        </div>
        <div v-if="expanded.has(dir.path)" class="dir-files">
          <div
            v-for="file in dirFiles.get(dir.path) || []"
            :key="file.path"
            class="file-item"
            :class="{ selected: selectedFile === file.path }"
            @click="selectFile(file)"
          >
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">{{ formatSize(file.size) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listFiles, type FileInfo } from '../api'

const emit = defineEmits<{
  select: [file: FileInfo]
}>()

const loading = ref(false)
const dirs = ref<FileInfo[]>([])
const dirFiles = ref<Map<string, FileInfo[]>>(new Map())
const expanded = ref(new Set<string>())
const selectedFile = ref('')

async function loadFiles() {
  loading.value = true
  try {
    const entries = await listFiles()
    dirs.value = entries.filter((e) => e.is_dir).sort((a, b) => b.name.localeCompare(a.name))

    for (const dir of dirs.value) {
      const files = await listFiles(dir.name)
      dirFiles.value.set(
        dir.path,
        files.filter((f) => !f.is_dir && f.name.endsWith('.pdf'))
      )
    }

    // Auto-expand latest dir
    if (dirs.value.length > 0 && expanded.value.size === 0) {
      expanded.value.add(dirs.value[0].path)
    }
  } finally {
    loading.value = false
  }
}

function toggleDir(path: string) {
  if (expanded.value.has(path)) {
    expanded.value.delete(path)
  } else {
    expanded.value.add(path)
  }
  expanded.value = new Set(expanded.value)
}

function selectFile(file: FileInfo) {
  selectedFile.value = file.path
  emit('select', file)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

onMounted(loadFiles)

defineExpose({ loadFiles })
</script>

<style scoped>
.file-tree {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.tree-header h2 {
  font-size: 16px;
}

.btn-small {
  padding: 4px 12px;
  font-size: 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
}

.btn-small:hover {
  background: var(--bg);
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.tree-loading,
.tree-empty {
  text-align: center;
  padding: 40px 16px;
  color: var(--text-secondary);
}

.dir-group {
  margin-bottom: 2px;
}

.dir-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  user-select: none;
}

.dir-header:hover {
  background: var(--bg);
}

.dir-arrow {
  font-size: 10px;
  width: 12px;
  color: var(--text-secondary);
}

.dir-files {
  padding-left: 32px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 16px;
  cursor: pointer;
  border-radius: var(--radius);
  margin: 0 8px;
  font-size: 13px;
}

.file-item:hover {
  background: var(--bg);
}

.file-item.selected {
  background: #eff6ff;
  color: var(--accent);
}

.file-size {
  color: var(--text-secondary);
  font-size: 12px;
}
</style>
```

- [ ] **Step 2: Create PdfPreview.vue**

```vue
<template>
  <div class="pdf-preview">
    <div v-if="!file" class="preview-empty">
      从左侧选择 PDF 文件预览
    </div>
    <div v-else class="preview-content">
      <div class="preview-header">
        <h3>{{ file.name }}</h3>
        <div class="preview-meta">
          {{ file.modified }} | {{ formatSize(file.size) }}
        </div>
        <div class="preview-actions">
          <a :href="fileUrl" target="_blank" class="btn-small">新窗口打开</a>
          <button class="btn-small" @click="copyLink">复制链接</button>
        </div>
      </div>
      <iframe :src="fileUrl" class="preview-frame"></iframe>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getFileUrl, type FileInfo } from '../api'

const props = defineProps<{ file: FileInfo | null }>()

const fileUrl = computed(() => (props.file ? getFileUrl(props.file.path) : ''))

function copyLink() {
  if (props.file) {
    navigator.clipboard.writeText(fileUrl.value)
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<style scoped>
.pdf-preview {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
  font-size: 15px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.preview-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.preview-header h3 {
  font-size: 16px;
  margin-bottom: 4px;
}

.preview-meta {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.btn-small {
  padding: 4px 12px;
  font-size: 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  text-decoration: none;
}

.btn-small:hover {
  background: var(--bg);
}

.preview-frame {
  flex: 1;
  border: none;
  width: 100%;
}
</style>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/FileTree.vue frontend/src/components/PdfPreview.vue
git commit -m "feat(frontend): 添加文件列表和 PDF 预览组件"
```

---

## Task 16: Create ResultView Page

**Files:**
- Create: `frontend/src/views/ResultView.vue`

- [ ] **Step 1: Create ResultView.vue**

```vue
<template>
  <div class="result-view">
    <div class="result-left">
      <FileTree ref="fileTree" @select="onFileSelect" />
    </div>
    <div class="result-right">
      <PdfPreview :file="selectedFile" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FileTree from '../components/FileTree.vue'
import PdfPreview from '../components/PdfPreview.vue'
import type { FileInfo } from '../api'

const selectedFile = ref<FileInfo | null>(null)
const fileTree = ref<InstanceType<typeof FileTree> | null>(null)

function onFileSelect(file: FileInfo) {
  selectedFile.value = file
}
</script>

<style scoped>
.result-view {
  display: flex;
  gap: 24px;
  height: 100%;
}

.result-left {
  width: 300px;
  flex-shrink: 0;
}

.result-right {
  flex: 1;
  min-width: 0;
}

@media (max-width: 900px) {
  .result-view {
    flex-direction: column;
  }
  .result-left {
    width: 100%;
    max-height: 300px;
  }
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/ResultView.vue
git commit -m "feat(frontend): 添加结果浏览页面"
```

---

## Task 17: Build Frontend and Verify Integration

**Files:**
- Modify: `server/src/main.rs`

- [ ] **Step 1: Build frontend**

```bash
cd frontend && npm run build
```
Expected: `dist/` directory created with built assets.

- [ ] **Step 2: Test Rust server serves the SPA**

```bash
cd server && cargo run
```
Open http://127.0.0.1:3000 — verify the Vue SPA loads and navigation works.

- [ ] **Step 3: Test file listing API**

```bash
curl http://127.0.0.1:3000/api/files
```
Expected: JSON array of files in `output/`.

- [ ] **Step 4: Test crawl API (dry run)**

```bash
curl -X POST http://127.0.0.1:3000/api/crawl \
  -H 'Content-Type: application/json' \
  -d '{"paper_type":"jfjb","paper_date":"2026-03-10","output_dir":"output","export_individual":true,"export_combined":true}'
```
Expected: `{"task_id":"..."}` and the Python process starts.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: 前后端集成验证通过"
```

---

## Task 18: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update project overview and commands**

Update the relevant sections in `CLAUDE.md`:

```markdown
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
| `fonts.py` | Cross-platform font discovery + ReportLab registration |
| `pdf.py` | `PDFExporter` — PDF generation |
| `utils.py` | `normalize_space`, `html_to_paragraphs`, `safe_filename` |
| `network.py` | HTTP session factory + `retry_get` with exponential backoff |
| `cli.py` | Shared argparse arguments + `setup_logging` + JSON progress output |
| `jfjb_spider.py` | `JFJBSpider` class + batch mode logic + CLI |
| `rmrb_spider.py` | `RMRBSpider` class + CLI |

### Web Dashboard (`server/` + `frontend/`)

| Module | Responsibility |
|--------|---------------|
| `server/src/main.rs` | Axum router + static file serving |
| `server/src/api.rs` | REST API: crawl start/cancel/status, SSE event stream |
| `server/src/crawler.rs` | Python subprocess management, JSON stdout parsing |
| `server/src/files.rs` | File listing and download API |
| `frontend/src/views/CrawlView.vue` | Crawl configuration + real-time progress |
| `frontend/src/views/ResultView.vue` | File browser + PDF preview |
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: 更新 CLAUDE.md 适配 Rust + Vue 架构"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|---|---|
| Rust backend with Axum | Task 5, 6, 7, 8 |
| Vue 3 frontend | Task 9, 10, 11, 12, 13, 14, 15, 16 |
| subprocess Python integration | Task 6 |
| SSE real-time events | Task 6 |
| `--json-progress` Python CLI | Task 2, 3, 4 |
| Remove PyQt6 | Task 1 |
| PDF preview in browser | Task 15 (PdfPreview.vue iframe) |
| File listing API | Task 7 |
| Cancel support | Task 6 (kill child process) |
| Update docs | Task 18 |
| Production build | Task 8 (static serving), Task 17 |
| Python CLI unchanged | Task 1 (preserves jfjb/rmrb entry points) |
