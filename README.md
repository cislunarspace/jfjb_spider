# 报纸文章 PDF 爬虫

抓取 [解放军报](https://www.81.cn)（81.cn）和 [人民日报](https://paper.people.com.cn)（people.com.cn）的文章，导出为排版精美的 PDF 文件。

## 30 秒上手

```bash
# 1. 安装依赖（需要 Python 3.10+）
pip install -r requirements.txt

# 2. 抓取今天的解放军报
python jfjb.py

# 3. 查看输出
ls output/$(date +%Y-%m-%d)/
```

就这么简单。PDF 文件会自动生成在 `output/日期/` 目录下。

## 两个爬虫

| 爬虫 | 数据源 | 入口 | 抓取范围 |
|------|--------|------|----------|
| 解放军报 | 81.cn JSON API | `python jfjb.py` | 单日 / 批量日期范围 |
| 人民日报 | paper.people.com.cn HTML | `python rmrb.py` | 单日 |

## 常用命令

```bash
# 抓取今天
python jfjb.py
python rmrb.py

# 指定日期
python jfjb.py --date 2026-03-10
python rmrb.py --date 2026-03-10

# 批量抓取（仅解放军报）
python jfjb.py --start-date 2026-01-01 --end-date 2026-03-31 --delay 2

# 只生成一个合集 PDF（不分单篇）
python jfjb.py --combined-only

# 查看完整参数列表
python jfjb.py --help
python rmrb.py --help
```

## 输出说明

运行后会创建以下文件：

```
output/
  2026-03-10/                          ← 解放军报（日期目录）
    第01版_要闻/                        ← 按版面分目录
      01_文章标题.pdf                   ← 单篇文章 PDF
    解放军报_2026-03-10_全集.pdf        ← 当日合集（含书签目录）
  rmrb/
    2026-03-10/                        ← 人民日报
      第01版_要闻/
        ...
      人民日报_2026-03-10_全集.pdf
```

每个 PDF 包含：
- 黑体标题 + 宋体正文 + Times New Roman 英文混排
- PDF 书签目录（版面 → 文章两级导航）

## 命令行参数

### 通用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date YYYY-MM-DD` | 指定日期 | 自动获取当天 |
| `--out-dir PATH` | 输出目录 | `output`（解放军报）/ `output/rmrb`（人民日报） |
| `--combined-only` | 仅输出合集 PDF | 默认输出合集+单篇 |
| `--individual-only` | 仅输出单篇 PDF | 默认输出合集+单篇 |
| `--font-simhei PATH` | 黑体字体路径 | 自动发现 |
| `--font-simsun PATH` | 宋体字体路径 | 自动发现 |
| `--font-times PATH` | Times New Roman 字体路径 | 自动发现 |
| `--font-dir PATH` | 字体文件目录 | 自动发现 |

### 解放军报专用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--start-date YYYY-MM-DD` | 批量起始日期（含） | - |
| `--end-date YYYY-MM-DD` | 批量结束日期（含） | 今天 |
| `--base-url URL` | 站点根地址 | `https://www.81.cn` |
| `delay SECONDS` | 批量抓取间隔 | 2.0 |
| `--skip-existing` | 跳过已下载日期 | 默认启用 |
| `--no-skip-existing` | 不跳过已下载日期 | - |

### 人民日报专用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--base-url URL` | 站点根地址 | `https://paper.people.com.cn` |

## 跨平台字体

程序自动在系统中查找中文字体，按以下优先级：

1. 命令行参数（`--font-simhei /path/to/font.ttf`）
2. 环境变量（`NEWSPAPER_FONT_SIMHEI`、`NEWSPAPER_FONT_SIMSUN`、`NEWSPAPER_FONT_TIMES`）
3. 系统字体目录自动搜索（Windows / Linux / macOS）
4. 开源 CJK 回退字体（Noto CJK、文泉驿等）

如果找不到中文字体，程序会报错并给出安装提示。

### Linux 安装中文字体

```bash
# Ubuntu/Debian
sudo apt install fonts-noto-cjk

# CentOS/RHEL
sudo yum install google-noto-sans-cjk-fonts
```

## 项目结构

```
newspaper_pdf/          ← Python 包
  models.py             Article 数据模型
  fonts.py              跨平台字体发现
  pdf.py                PDF 导出器
  utils.py              工具函数
  network.py            HTTP 会话 + 重试
  cli.py                命令行参数
  jfjb_spider.py        解放军报爬虫
  rmrb_spider.py        人民日报爬虫
jfjb.py                 解放军报入口
rmrb.py                 人民日报入口
```
