# 报纸文章 PDF 爬虫

抓取解放军报（81.cn）、人民日报（people.com.cn）的文章，导出为排版精美的 PDF 文件。

## 功能特性

- 双源支持：解放军报 / 人民日报
- PDF 排版：黑体标题 + 宋体正文 + Times New Roman 英文混排
- PDF 书签目录：版面和文章两级导航
- 单日抓取 / 批量日期范围抓取（仅解放军报）
- 断点续爬：跳过已下载日期
- 网络重试：自动指数退避重试
- 跨平台字体发现：Windows / Linux / macOS

## 安装

### 依赖

- Python 3.10+
- 中文字体（SimHei 黑体、SimSun 宋体）或开源替代（Noto CJK、文泉驿等）

### 安装步骤

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
# 抓取今天解放军报
python jfjb.py

# 抓取今天人民日报
python rmrb.py

# 指定日期
python jfjb.py --date 2026-03-10
python rmrb.py --date 2026-03-10

# 批量抓取（仅解放军报支持）
python jfjb.py --start-date 2026-01-01 --end-date 2026-03-31 --delay 2
```

## 命令行参数

### 通用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date YYYY-MM-DD` | 指定日期 | 自动获取当天 |
| `--out-dir PATH` | 输出目录 | `output`（解放军报）/ `output/rmrb`（人民日报） |
| `--combined-only` | 仅输出合集 PDF | 默认输出合集+单篇 |
| `--individual-only` | 仅输出单篇 PDF | 默认输出合集+单篇 |
| `--font-simhei PATH` | SimHei（黑体）字体路径 | 自动发现 |
| `--font-simsun PATH` | SimSun（宋体）字体路径 | 自动发现 |
| `--font-times PATH` | Times New Roman 字体路径 | 自动发现 |
| `--font-dir PATH` | 字体文件目录 | 自动发现 |

### 解放军报专用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--start-date YYYY-MM-DD` | 批量起始日期（含） | - |
| `--end-date YYYY-MM-DD` | 批量结束日期（含） | 今天 |
| `--base-url URL` | 站点根地址 | `https://www.81.cn` |
| `--delay SECONDS` | 批量抓取间隔 | 2.0 |
| `--skip-existing` | 跳过已下载日期 | 默认启用 |
| `--no-skip-existing` | 不跳过已下载日期 | - |

### 人民日报专用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--base-url URL` | 站点根地址 | `https://paper.people.com.cn` |

## 输出目录结构

```
output/
  2026-03-10/                          # 解放军报
    第01版_要闻/
      01_文章标题.pdf
      02_另一篇文章.pdf
    第02版_国内新闻/
      ...
    解放军报_2026-03-10_全集.pdf
  rmrb/
    2026-03-10/                        # 人民日报
      第01版_要闻/
        ...
      人民日报_2026-03-10_全集.pdf
```

## 跨平台字体配置

程序会按以下优先级查找字体：

1. **命令行参数**：`--font-simhei /path/to/font.ttf`
2. **环境变量**：`NEWSPAPER_FONT_SIMHEI`、`NEWSPAPER_FONT_SIMSUN`、`NEWSPAPER_FONT_TIMES`
3. **系统字体目录自动搜索**：
   - Windows: `C:\Windows\Fonts\`、`%LOCALAPPDATA%\Microsoft\Windows\Fonts\`
   - Linux: `/usr/share/fonts/`、`~/.local/share/fonts/`
   - macOS: `/Library/Fonts/`、`~/Library/Fonts/`
4. **开源 CJK 回退字体**：Noto Sans/Serif CJK、文泉驿等

### Linux 安装中文字体示例

```bash
# Ubuntu/Debian
sudo apt install fonts-noto-cjk

# CentOS/RHEL
sudo yum install google-noto-sans-cjk-fonts
```

## 向后兼容

旧的调用方式仍然可用：

```bash
python jfjb_spider.py --date 2026-03-10
python rmrb_spider.py --date 2026-03-10
```

## 项目结构

```
newspaper_pdf/          # Python 包
  __init__.py           # 版本号
  models.py             # Article 统一数据模型
  fonts.py              # 跨平台字体发现与注册
  pdf.py                # PDF 导出器
  utils.py              # 共享工具函数
  network.py            # HTTP 会话 + 重试逻辑
  cli.py                # 命令行参数工厂
  jfjb_spider.py        # 解放军报爬虫
  rmrb_spider.py        # 人民日报爬虫
jfjb.py                 # 解放军报入口
rmrb.py                 # 人民日报入口
```
