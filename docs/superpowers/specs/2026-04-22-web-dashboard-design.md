# Web Dashboard 设计文档

> 将 PyQt6 GUI 替换为 Rust 后端 + Vue 3 前端的 Web Dashboard

## 背景

当前项目使用 PyQt6 构建桌面 GUI，提供抓取配置和结果浏览功能。PyQt6 依赖重、跨平台打包复杂、UI 迭代慢。用户希望用 Web 技术栈获得更好的开发体验。

## 技术选型

| 层 | 技术 | 理由 |
|---|---|---|
| 后端 | Rust + Axum | 轻量异步、生态成熟、性能好 |
| 前端 | Vue 3 + Vite + TypeScript | 用户偏好、开发体验好 |
| Python 集成 | subprocess + JSON stdout | 最简单可靠的进程隔离 |
| 实时通信 | SSE (Server-Sent Events) | 单向推送足够，比 WebSocket 简单 |
| PDF 预览 | 浏览器内置 PDF.js | 零额外依赖 |

## 架构

```
┌─────────────────────────────────────────┐
│  Vue 3 SPA (前端)                        │
│  Vite dev server (开发) / 静态构建 (生产) │
└──────────────┬──────────────────────────┘
               │ HTTP + SSE
┌──────────────▼──────────────────────────┐
│  Rust Web Server (Axum)                 │
│  - REST API                             │
│  - SPA 静态文件服务                       │
│  - SSE 实时进度推送                       │
│  - subprocess 管理 Python 进程            │
└──────────────┬──────────────────────────┘
               │ spawn subprocess
┌──────────────▼──────────────────────────┐
│  Python 爬虫 (保留不变)                   │
│  - jfjb_spider / rmrb_spider            │
│  - pdf.py (ReportLab)                   │
│  - --json-progress 参数输出结构化进度     │
└─────────────────────────────────────────┘
```

## 项目结构

```
jfjb/
├── server/                    # Rust 后端
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs            # 入口 + Axum 路由 + 静态文件
│       ├── api.rs             # API handler 实现
│       ├── crawler.rs         # subprocess 管理 + SSE 事件
│       └── files.rs           # 文件列表 + 下载服务
├── frontend/                  # Vue 3 前端
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.ts
│       ├── App.vue            # 布局壳 (侧边栏 + 内容区)
│       ├── router.ts
│       ├── views/
│       │   ├── CrawlView.vue  # 抓取配置 + 进度
│       │   └── ResultView.vue # 结果浏览 + PDF 预览
│       ├── components/
│       │   ├── CrawlForm.vue  # 抓取表单
│       │   ├── ProgressLog.vue # 进度条 + 日志流
│       │   ├── FileTree.vue   # 文件树/列表
│       │   └── PdfPreview.vue # PDF 预览面板
│       └── api/
│           └── index.ts       # API 调用封装
├── newspaper_pdf/             # Python 包 (保留)
│   ├── jfjb_spider.py
│   ├── rmrb_spider.py
│   ├── pdf.py
│   ├── models.py
│   ├── fonts.py
│   ├── utils.py
│   ├── network.py
│   ├── cli.py
│   └── __main__.py
├── tests/                     # Python 测试 (保留非 GUI 测试)
├── pyproject.toml             # 移除 PyQt6, 保留核心依赖
├── output/                    # 生成的 PDF
└── CLAUDE.md
```

## Rust 后端 API

### 端点设计

| 端点 | 方法 | 功能 | 请求体/响应 |
|------|------|------|------------|
| `/api/crawl` | POST | 启动抓取任务 | 请求: `CrawlRequest` → 响应: `{"task_id": "..."}` |
| `/api/crawl/stream` | GET | SSE 进度流 | `text/event-stream`，每行 `data: {...}` |
| `/api/crawl/cancel` | POST | 取消当前任务 | 请求: `{"task_id": "..."}` → 响应: `{"ok": true}` |
| `/api/status` | GET | 当前任务状态 | 响应: `CrawlStatus` |
| `/api/files` | GET | 列出输出文件 | ?path=子目录 → `FileList` |
| `/api/files/{path}` | GET | 下载/预览文件 | 返回文件内容 (PDF 直接在浏览器预览) |
| `/*` | GET | SPA 静态文件 | 服务 `frontend/dist/` |

### 数据模型

```rust
// 请求
struct CrawlRequest {
    paper_type: String,        // "jfjb" | "rmrb"
    paper_date: Option<String>,// YYYY-MM-DD (单日模式)
    start_date: Option<String>,// YYYY-MM-DD (批量模式)
    end_date: Option<String>,  // YYYY-MM-DD (批量模式)
    output_dir: String,        // 输出目录
    export_individual: bool,   // 单篇 PDF
    export_combined: bool,     // 合集 PDF
    font_dir: Option<String>,  // 字体目录
}

// SSE 事件
enum CrawlEvent {
    Progress { current: u32, total: u32, message: String },
    Log { level: String, message: String },
    Finished { success: u32, fail: u32, skip: u32, total: u32 },
    Error { message: String },
}

// 文件列表
struct FileInfo {
    name: String,
    path: String,
    size: u64,
    modified: String,
    is_dir: bool,
}
```

### subprocess 管理

Rust 后端通过 `tokio::process::Command` 启动 Python 子进程：

```bash
uv run python -m newspaper_pdf.jfjb_spider --json-progress --date 2026-03-10
```

- Python 进程的 stdout 输出 JSON 行，Rust 逐行解析并通过 SSE 推送
- stderr 用于错误日志
- 通过 `child.kill()` 支持取消

## Python 端改动

### 新增 `--json-progress` 参数

在 `cli.py` 中新增参数。当启用时：

1. 禁用 `logging` 的 console handler（不输出人类可读日志）
2. 在关键节点输出 JSON 行到 stdout：

```python
# 进度更新
print(json.dumps({"type": "progress", "current": 3, "total": 10, "message": "正在抓取 2026-03-10"}))

# 日志
print(json.dumps({"type": "log", "level": "INFO", "message": "已获取 15 篇文章"}))

# 完成
print(json.dumps({"type": "finished", "success": 10, "fail": 0, "skip": 0, "total": 10}))

# 错误
print(json.dumps({"type": "error", "message": "网络超时"}))
```

- 每行一个 JSON 对象，`flush=True` 确保实时性
- 现有 CLI 行为不变（不加 `--json-progress` 时输出人类可读格式）

## Vue 前端

### 页面设计

#### 抓取页 (CrawlView)

- 左侧：抓取表单 (`CrawlForm.vue`)
  - 报纸类型下拉（解放军报 / 人民日报）
  - 模式切换（单日 / 批量）
  - 日期选择器
  - 输出目录
  - 导出选项（单篇 / 合集复选框）
  - 字体目录（可选）
  - 开始 / 停止按钮
- 右侧：进度和日志 (`ProgressLog.vue`)
  - 进度条 + 状态文字
  - 实时日志（深色终端风格，彩色级别）

#### 结果页 (ResultView)

- 左侧：文件列表 (`FileTree.vue`)
  - 按日期分组的 PDF 文件列表
  - 文件大小和修改时间
- 右侧：PDF 预览 (`PdfPreview.vue`)
  - 点击文件直接在 iframe 中用浏览器 PDF.js 预览
  - 下载按钮、复制链接按钮

### 布局

- 左侧固定导航栏（图标 + 文字）
- 右侧内容区
- 配色沿用现有设计：`#f5f5f5` 背景、`#2563eb` 强调色
- 中文字体：系统字体栈

## 开发模式

### 开发环境

```bash
# 终端 1: 启动 Rust 后端
cd server && cargo run

# 终端 2: 启动 Vite dev server (带 HMR)
cd frontend && npm run dev
```

Vite 配置代理 `/api` 到 Rust 后端：

```ts
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:3000',
    },
  },
})
```

### 生产构建

```bash
# 构建前端
cd frontend && npm run build

# 构建 Rust (内嵌前端静态文件)
cd server && cargo build --release
```

Rust 后端在 release 模式下通过 `rust-embed` 或 `include_dir` 内嵌 `frontend/dist/`，实现单一二进制分发。

## 移除清单

- `newspaper_pdf/gui/` 整个目录
- `PyQt6>=6.6,<7` 依赖
- `pytest-qt>=4.0` 可选依赖
- `tests/test_gui_styles.py`
- `tests/test_gui_workers.py`
- `tests/test_preview_server.py`
- `pyproject.toml` 中的 `newspaper-pdf-ui` entry point

## 保留清单

- `newspaper_pdf/` 中所有爬虫和 PDF 模块
- CLI 入口：`jfjb`, `rmrb` 命令
- 所有非 GUI 测试
- `output/` 目录结构

## 验收标准

1. `cargo run` 启动 Rust 后端，`npm run dev` 启动前端开发服务器
2. 在抓取页配置参数并启动抓取，能看到实时进度和日志
3. 抓取完成后自动切换到结果页，文件按日期分组显示
4. 点击 PDF 文件能在浏览器中预览
5. 支持取消正在进行的抓取任务
6. 生产构建为单一 Rust 二进制 + 内嵌前端资源
7. Python CLI 命令 (`jfjb`, `rmrb`) 行为不变
8. 所有现有 Python 测试通过
