# uv 环境迁移 + PyQt6 GUI 设计方案

日期：2026-04-20

## 概述

为报刊 PDF 爬虫项目做两项改造：
1. 将 Python 环境管理从 pip + requirements.txt 迁移到 uv
2. 新增基于 PyQt6 的 GUI 界面，支持单日/批量抓取（带进度）、文章列表浏览、内嵌 PDF 渲染

CLI 入口保持不变，GUI 是额外的入口点。

## 1. uv 环境迁移

- 删除 `requirements.txt`，依赖统一由 `pyproject.toml` 管理
- 新增依赖：`PyQt6`、`PyQt6-WebEngine`（Chromium 内核 PDF 渲染）
- 新增入口点：`newspaper-pdf-ui = "newspaper_pdf.gui.app:main"`
- 使用 `uv sync` 安装依赖，生成 `uv.lock`

## 2. 新增模块结构

```
newspaper_pdf/
├── gui/                    # 新增 GUI 包
│   ├── __init__.py
│   ├── app.py              # QApplication 入口 + 主窗口
│   ├── crawl_panel.py      # 抓取面板（参数配置 + 进度）
│   ├── result_panel.py     # 结果浏览面板（文件树 + PDF 渲染）
│   ├── workers.py          # QThread 后台任务（抓取、PDF 导出）
│   └── styles.py           # 统一 QSS 样式表
├── (现有 8 个模块不变)
```

## 3. 主窗口结构

- 窗口标题：「报刊 PDF 助手」
- 顶部 Tab 栏：「抓取」 / 「结果浏览」
- 默认显示「抓取」Tab
- 窗口最小尺寸 900x600，默认 1100x700

## 4. 抓取面板（crawl_panel.py）

上半部分 — 参数配置区（QFormLayout）：

| 控件 | 类型 | 说明 |
|------|------|------|
| 报纸类型 | QComboBox | 解放军报 / 人民日报 |
| 抓取模式 | QRadioButton 组 | 单日 / 批量 |
| 日期选择 | QDateEdit | 单日一个，批量两个（起止） |
| 输出目录 | QLineEdit + QPushButton | 文本框 + 浏览按钮 |
| 导出模式 | QCheckBox | 单篇 PDF / 合集 PDF |
| 字体目录 | QLineEdit + QPushButton | 可选 |

下半部分 — 操作与进度区：
- 「开始抓取」/「停止」按钮
- 进度条（批量显示 X/N 天，单日显示旋转等待）
- 日志文本区（QTextEdit，只读，滚动显示抓取日志）

切换报纸类型时动态显示/隐藏批量参数（人民日报无批量模式）。

## 5. 结果浏览面板（result_panel.py）

左侧 — 文件导航区（QTreeView，约 280px 宽）：
- 以输出根目录为起点，显示目录树
- 层级：日期目录 → 版面子目录 → 单篇 PDF
- 底部「刷新」按钮
- 点击 PDF 文件时右侧渲染区加载

右侧 — PDF 渲染区（QWebEngineView）：
- 使用 Chromium 内核原生 PDF 查看器
- 支持缩放、翻页、搜索
- 未选中文件时显示「请在左侧选择 PDF 文件」

交互流程：
1. 抓取完成后提示切换到「结果浏览」Tab
2. 文件树自动展开最新抓取的日期目录
3. 点击任意 PDF 即可预览

## 6. 后台任务（workers.py）

- `CrawlWorker(QThread)` 在后台线程运行爬虫逻辑
- 通过 Qt 信号发射进度更新和日志消息
- 不阻塞 UI 主线程
- PDF 渲染由 QWebEngineView 内部处理

## 7. 样式（styles.py）

全局 QSS 样式表：
- 背景：`#f5f5f5`
- 卡片/面板：`#ffffff`，1px 浅灰边框
- 强调色：`#2563eb`（蓝色）
- 圆角按钮、扁平输入框
- Tab 栏使用下划线指示器
- 跨平台一致的视觉表现

## 8. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 抓取失败 | 日志区显示红色错误，不弹窗 |
| 网络异常 | 进度条标记失败天数，继续剩余日期 |
| 字体缺失 | 启动时警告，不阻止运行（沿用 CLI 降级逻辑） |
| PDF 加载失败 | 渲染区显示「文件加载失败」 |

## 9. 测试策略

- `workers.py` 信号发射逻辑可脱离 GUI 做单元测试
- GUI 组件用 `pytest-qt` 做基础交互测试（按钮点击、Tab 切换）
- 不做视觉回归测试，重点覆盖业务逻辑

## 10. 不包含的功能（YAGNI）

- 设置持久化（QSettings）
- 自动更新
- 拖拽排序
- 暗色主题切换
- 多语言支持
