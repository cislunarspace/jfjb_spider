# 文档全面更新设计方案

日期：2026-04-21

## 概述

将项目中所有引用旧命令（pip + requirements.txt、python jfjb.py）的文档全面更新为新环境（uv + GUI）。

## 更新范围

| 文件 | 更新内容 |
|------|----------|
| `README.md` | 安装命令、入口方式、GUI 说明、项目结构图 |
| `docs/installation.md` | 安装命令改为 uv sync，添加 PyQt6 说明 |
| `docs/quickstart.md` | 更新命令速查，加入 GUI 启动命令 |
| `docs/usage/jfjb.md` | 更新命令格式 |
| `docs/usage/rmrb.md` | 更新命令格式 |
| `docs/usage/output.md` | 更新输出目录说明 |
| `docs/index.md` | 更新导航，加入 GUI 相关文档 |

## README.md 更新要点

### 安装命令
```bash
# 旧
pip install -r requirements.txt

# 新
uv sync
```

### 入口命令
```bash
# 旧
python jfjb.py
python rmrb.py

# 新
uv run python -m newspaper_pdf.jfjb_spider
uv run python -m newspaper_pdf.rmrb_spider
uv run newspaper-pdf-ui   # GUI
```

### 项目结构（加入 gui/）
```
newspaper_pdf/
  ...
  gui/
    app.py            # 主窗口
    crawl_panel.py    # 抓取面板
    result_panel.py   # 结果浏览面板
    workers.py        # 后台任务
    styles.py         # 样式表
```

### 新增 GUI 说明章节
- GUI 入口命令
- GUI 主要功能（抓取配置、进度显示、PDF 预览）
