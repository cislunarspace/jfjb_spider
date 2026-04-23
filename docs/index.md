# newspaper-pdf

抓取 [解放军报](https://www.81.cn) 和 [人民日报](https://paper.people.com.cn) 的文章，导出为排版精美的 PDF 文件。

## 这是什么？

一个 Python 爬虫工具包，自动抓取报纸文章并生成格式化 PDF。每篇 PDF 包含：

- **黑体标题 + 宋体正文 + Times New Roman 英文混排** — 排版效果接近原版报纸
- **PDF 书签目录** — 按版面 → 文章两级导航，方便在阅读器中跳转
- **单篇导出 + 合集导出** — 可选按版面分目录存放，或合并为一个带目录的合集

配套 Rust + Vue Web Dashboard，可通过浏览器配置抓取、监控进度、浏览结果。

## 30 秒上手

```bash
# 安装依赖
uv sync && cd frontend && npm install && cd ..

# 一键启动 Web Dashboard（开发模式）
npm run dev
```

打开 http://localhost:5173 即可通过浏览器操作：选择报纸、日期，一键抓取，实时查看进度，浏览和预览 PDF。

也可以用命令行直接抓取：

```bash
uv run python -m newspaper_pdf.jfjb_spider        # 今天的解放军报
uv run python -m newspaper_pdf.rmrb_spider        # 今天的人民日报
```

## 两个爬虫

| 爬虫 | 数据源 | 入口命令 | 抓取范围 |
|------|--------|----------|----------|
| 解放军报 | 81.cn JSON API | `uv run python -m newspaper_pdf.jfjb_spider` | 单日 / 批量日期范围 |
| 人民日报 | paper.people.com.cn HTML | `uv run python -m newspaper_pdf.rmrb_spider` | 单日 |

## 快速导航

- **[安装指南](installation.md)** — 依赖安装和字体配置
- **[快速上手](quickstart.md)** — 常用命令速查
- **[使用指南](usage/jfjb.md)** — 各爬虫的详细用法
- **[Web Dashboard](usage/web.md)** — 浏览器界面使用方法
- **[API 参考](api/models.md)** — 模块接口文档
