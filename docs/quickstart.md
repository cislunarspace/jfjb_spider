# 快速上手

## Web Dashboard（推荐）

```bash
# 开发模式（前后端同时启动，支持热更新）
npm run dev

# 或生产模式（构建前端后启动，只需一个进程）
npm start
```

打开 http://localhost:5173（开发模式）或 http://localhost:8080（生产模式）即可使用。

## 命令行抓取

### 抓取今天的报纸

```bash
# 解放军报
uv run python -m newspaper_pdf.jfjb_spider

# 人民日报
uv run python -m newspaper_pdf.rmrb_spider
```

### 指定日期

```bash
uv run python -m newspaper_pdf.jfjb_spider --date 2026-03-10
uv run python -m newspaper_pdf.rmrb_spider --date 2026-03-10
```

### 批量抓取（解放军报）

```bash
# 抓取 2026 年 1 月到 3 月，每天间隔 2 秒
uv run python -m newspaper_pdf.jfjb_spider --start-date 2026-01-01 --end-date 2026-03-31 --delay 2
```

批量模式下会自动跳过已下载的日期（断点续爬）。

### 控制输出格式

```bash
# 只生成一个合集 PDF（含书签目录）
uv run python -m newspaper_pdf.jfjb_spider --combined-only

# 只生成单篇 PDF（按版面分目录）
uv run python -m newspaper_pdf.jfjb_spider --individual-only
```

### 自定义输出目录

```bash
uv run python -m newspaper_pdf.jfjb_spider --out-dir my_output
```

### 查看完整参数

```bash
uv run python -m newspaper_pdf.jfjb_spider --help
uv run python -m newspaper_pdf.rmrb_spider --help
```

## 常见问题

!!! warning "找不到中文字体"

    程序启动时报错 `未找到任何中文字体`？

    请安装中文字体或手动指定路径。参见 [字体配置](usage/fonts.md)。

!!! info "抓取失败"

    如果某天的报纸尚未上线（如当天尚未出版），程序会报告 HTTP 错误但不会中断批量抓取。

    检查日期格式是否为 `YYYY-MM-DD`。
