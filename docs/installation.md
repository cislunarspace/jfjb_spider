# 安装指南

## 环境要求

- Python 3.10+
- 操作系统：Windows / Linux / macOS

## 安装步骤

### 1. 克隆项目

```bash
git clone <仓库地址>
cd jfjb_spider
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

依赖包：

| 包 | 用途 |
|----|------|
| `requests` | HTTP 请求 |
| `beautifulsoup4` | HTML 解析 |
| `reportlab` | PDF 生成 |

### 3. 安装中文字体

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
    python jfjb.py --font-simhei /path/to/simhei.ttf

    # 或环境变量
    export NEWSPAPER_FONT_SIMHEI=/path/to/simhei.ttf
    python jfjb.py
    ```

## 验证安装

```bash
python jfjb.py --help
```

如果看到命令行参数列表，说明安装成功。
