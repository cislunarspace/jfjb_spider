# 快速上手

## 抓取今天的报纸

```bash
# 解放军报
python jfjb.py

# 人民日报
python rmrb.py
```

## 指定日期

```bash
python jfjb.py --date 2026-03-10
python rmrb.py --date 2026-03-10
```

## 批量抓取（解放军报）

```bash
# 抓取 2026 年 1 月到 3 月，每天间隔 2 秒
python jfjb.py --start-date 2026-01-01 --end-date 2026-03-31 --delay 2
```

批量模式下会自动跳过已下载的日期（断点续爬）。

## 控制输出格式

```bash
# 只生成一个合集 PDF（含书签目录）
python jfjb.py --combined-only

# 只生成单篇 PDF（按版面分目录）
python jfjb.py --individual-only
```

## 自定义输出目录

```bash
python jfjb.py --out-dir my_output
```

## 查看完整参数

```bash
python jfjb.py --help
python rmrb.py --help
```

## 常见问题

!!! warning "找不到中文字体"

    程序启动时报错 `未找到任何中文字体`？

    请安装中文字体或手动指定路径。参见 [字体配置](usage/fonts.md)。

!!! info "抓取失败"

    如果某天的报纸尚未上线（如当天尚未出版），程序会报告 HTTP 错误但不会中断批量抓取。

    检查日期格式是否为 `YYYY-MM-DD`。
