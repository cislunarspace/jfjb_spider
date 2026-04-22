# 文档全面更新设计

## 目标

更新所有说明文档，移除已删除的 PyQt6 GUI 引用，补充 Rust + Vue Web Dashboard 内容，确保文档与当前代码一致。

## 改动清单

### 1. `README.md`

- 替换「GUI 界面」章节 → 「Web Dashboard」章节（含启动命令）
- 更新「项目结构」：移除 `gui/` 目录，添加 `server/`（Rust 后端）和 `frontend/`（Vue 前端）
- 移除 `uv run newspaper-pdf-ui` 引用

### 2. `docs/index.md`

- 替换 GUI 描述为 Web Dashboard
- 更新导航链接：`usage/gui.md` → `usage/web.md`
- 更新项目简介

### 3. `docs/installation.md`

- 环境要求新增：Rust（cargo）、Node.js（npm）
- 依赖表移除 PyQt6、PyQt6-WebEngine
- 新增 Web Dashboard 安装步骤（`cd server && cargo build`，`cd frontend && npm install`）
- 移除 GUI 启动说明

### 4. `docs/quickstart.md`

- 替换 `uv run newspaper-pdf-ui` 为 Web Dashboard 启动命令
- 保留 CLI 命令不变

### 5. `docs/usage/gui.md` → `docs/usage/web.md`

- 删除旧 gui.md
- 新建 web.md，内容涵盖：启动方式、界面布局（抓取页面、结果页面）、API 说明

## 不改动的文件

- `docs/api/*.md` — 使用 mkdocs autodoc，从 docstring 自动生成，无需手动改
- `docs/usage/jfjb.md`、`docs/usage/rmrb.md` — 内容仍然准确
- `docs/usage/fonts.md`、`docs/usage/output.md` — 内容仍然准确
