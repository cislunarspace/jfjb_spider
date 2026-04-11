# 解放军报爬虫

通过 81.cn 的 JSON API 抓取解放军报各版面文章。

## 基本用法

```bash
# 抓取今天的报纸
python jfjb.py

# 抓取指定日期
python jfjb.py --date 2026-03-10
```

## 批量抓取

解放军报支持批量日期范围抓取，适合归档用途：

```bash
# 抓取一个月的报纸
python jfjb.py --start-date 2026-03-01 --end-date 2026-03-31

# 自定义请求间隔（避免被限流）
python jfjb.py --start-date 2026-03-01 --delay 3

# 不指定结束日期时，默认抓取到今天
python jfjb.py --start-date 2026-03-01
```

批量抓取的行为：

- 按日期顺序逐天抓取
- 默认每天间隔 2 秒（可通过 `--delay` 调整）
- 已下载的日期自动跳过（`--skip-existing`，默认启用）
- 单日失败不影响后续日期

!!! tip "断点续爬"

    如果批量抓取中途中断，重新运行相同命令即可。已下载的日期会被自动跳过。

## 专用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--start-date` | 批量起始日期（含） | - |
| `--end-date` | 批量结束日期（含） | 今天 |
| `--base-url` | 站点根地址 | `https://www.81.cn` |
| `--delay` | 批量抓取间隔（秒） | 2.0 |
| `--skip-existing` | 跳过已下载日期 | 启用 |
| `--no-skip-existing` | 不跳过已下载日期 | - |

## 数据源说明

解放军报使用 81.cn 提供的 JSON API：

- 入口：`https://www.81.cn/_szb/jfjb/{year}/{month}/{day}/index.json`
- 返回每个版面的文章列表，包含标题、作者、正文 HTML
- 爬虫自动解析 JSON，提取文章并生成 PDF
