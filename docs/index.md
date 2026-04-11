# newspaper-pdf

抓取 [解放军报](https://www.81.cn) 和 [人民日报](https://paper.people.com.cn) 的文章，导出为排版精美的 PDF 文件。

## 这是什么？

一个 Python 爬虫工具包，自动抓取报纸文章并生成格式化 PDF。每篇 PDF 包含：

- **黑体标题 + 宋体正文 + Times New Roman 英文混排** — 排版效果接近原版报纸
- **PDF 书签目录** — 按版面 → 文章两级导航，方便在阅读器中跳转
- **单篇导出 + 合集导出** — 可选按版面分目录存放，或合并为一个带目录的合集

## 30 秒上手

```bash
# 安装依赖（需要 Python 3.10+）
pip install -r requirements.txt

# 抓取今天的解放军报
python jfjb.py

# 查看输出
ls output/$(date +%Y-%m-%d)/
```

就这么简单。PDF 文件会自动生成在 `output/日期/` 目录下。

## 两个爬虫

| 爬虫 | 数据源 | 入口 | 抓取范围 |
|------|--------|------|----------|
| 解放军报 | 81.cn JSON API | `python jfjb.py` | 单日 / 批量日期范围 |
| 人民日报 | paper.people.com.cn HTML | `python rmrb.py` | 单日 |

## 快速导航

- **[安装指南](installation.md)** — 依赖安装和字体配置
- **[快速上手](quickstart.md)** — 常用命令速查
- **[使用指南](usage/jfjb.md)** — 各爬虫的详细用法
- **[API 参考](api/models.md)** — 模块接口文档
