# 安装指南

## 环境要求

- Python 3.10+
- Rust（cargo）— 用于 Web Dashboard 后端
- Node.js（npm）— 用于 Web Dashboard 前端
- 操作系统：Windows / Linux / macOS

## 安装步骤

### 1. 克隆项目

```bash
git clone <仓库地址>
cd jfjb_spider
```

### 2. 安装 Python 依赖

```bash
uv sync
```

依赖包：

| 包 | 用途 |
|----|------|
| `requests` | HTTP 请求 |
| `beautifulsoup4` | HTML 解析 |
| `reportlab` | PDF 生成 |

### 3. 安装 Web Dashboard（可选）

```bash
# 构建 Rust 后端
cd server && cargo build

# 安装前端依赖
cd ../frontend && npm install
```

### 4. 安装中文字体

程序需要中文字体来渲染 PDF。按优先级自动查找：

1. 命令行参数指定（`--font-simhei`）
2. 环境变量（`NEWSPAPER_FONT_SIMHEI`）
3. 系统字体目录自动搜索
4. 开源 CJK 回退字体（Noto CJK、文泉驿等）

=== "Linux"

    ```bash
    # Ubuntu/Debian
    sudo apt install fonts-noto-cjk

    # CentOS/RHEL
    sudo yum install google-noto-sans-cjk-fonts
    ```

=== "macOS"

    macOS 自带宋体（STSong），一般可直接使用。如需额外字体：

    ```bash
    brew install --cask font-noto-sans-cjk-sc
    ```

=== "Windows"

    Windows 自带 SimHei（黑体）和 SimSun（宋体），一般可直接使用。

!!! tip "手动指定字体"

    如果自动发现失败，可通过以下方式手动指定：

    ```bash
    # 命令行参数
    uv run python -m newspaper_pdf.jfjb_spider --font-simhei /path/to/simhei.ttf

    # 或环境变量
    export NEWSPAPER_FONT_SIMHEI=/path/to/simhei.ttf
    uv run python -m newspaper_pdf.jfjb_spider
    ```

## 验证安装

```bash
uv run python -m newspaper_pdf.jfjb_spider --help
```

如果看到命令行参数列表，说明安装成功。

## Web Dashboard

安装完成后，可以通过浏览器操作：

```bash
# 开发模式（前后端同时启动，支持热更新）
npm run dev

# 或生产模式（构建前端后启动，只需一个进程）
npm start
```

打开 http://localhost:5173（开发模式）或 http://localhost:8080（生产模式）即可使用。详见 [Web Dashboard 使用说明](usage/web.md)。
