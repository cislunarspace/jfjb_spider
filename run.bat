@echo off
chcp 65001 >nul
title 解放军报爬虫

REM ============================================================
REM  解放军报爬虫 - 启动脚本
REM  修改下方参数后双击运行，或在命令行中执行 run.bat
REM ============================================================

REM ---------- 选择模式（取消注释你需要的那一行） ----------

REM --- 模式1：抓取今天的报纸 ---
REM python jfjb_spider.py

REM --- 模式2：抓取指定某一天 ---
REM python jfjb_spider.py --date 2026-03-10

REM --- 模式3：批量抓取 - 按年份分段（推荐，方便断点续爬） ---
REM python jfjb_spider.py --start-date 2010-01-01 --end-date 2010-12-31 --delay 2
REM python jfjb_spider.py --start-date 2011-01-01 --end-date 2011-12-31 --delay 2
REM python jfjb_spider.py --start-date 2012-01-01 --end-date 2012-12-31 --delay 2
REM python jfjb_spider.py --start-date 2013-01-01 --end-date 2013-12-31 --delay 2
REM python jfjb_spider.py --start-date 2014-01-01 --end-date 2014-12-31 --delay 2
REM python jfjb_spider.py --start-date 2015-01-01 --end-date 2015-12-31 --delay 2
REM python jfjb_spider.py --start-date 2016-01-01 --end-date 2016-12-31 --delay 2
REM python jfjb_spider.py --start-date 2017-01-01 --end-date 2017-12-31 --delay 2
REM python jfjb_spider.py --start-date 2018-01-01 --end-date 2018-12-31 --delay 2
REM python jfjb_spider.py --start-date 2019-01-01 --end-date 2019-12-31 --delay 2
REM python jfjb_spider.py --start-date 2020-01-01 --end-date 2020-12-31 --delay 2
REM python jfjb_spider.py --start-date 2021-01-01 --end-date 2021-12-31 --delay 2
REM python jfjb_spider.py --start-date 2022-01-01 --end-date 2022-12-31 --delay 2
REM python jfjb_spider.py --start-date 2023-01-01 --end-date 2023-12-31 --delay 2
REM python jfjb_spider.py --start-date 2024-01-01 --end-date 2024-12-31 --delay 2
REM python jfjb_spider.py --start-date 2025-01-01 --end-date 2025-12-31 --delay 2
REM python jfjb_spider.py --start-date 2026-01-01 --delay 2

REM --- 模式4：一次性抓取 2010 年至今全部（耗时很长） ---
REM python jfjb_spider.py --start-date 2010-01-01 --delay 2

REM --- 模式5：仅生成每日合集 PDF，不生成单篇 ---
REM python jfjb_spider.py --start-date 2010-01-01 --combined-only --delay 2

REM --- 模式6：仅生成单篇 PDF，不生成每日合集 ---
REM python jfjb_spider.py --start-date 2010-01-01 --individual-only --delay 2

REM --- 模式7：强制重新抓取（不跳过已有） ---
REM python jfjb_spider.py --start-date 2026-03-01 --end-date 2026-03-10 --no-skip-existing --delay 2

REM --- 模式8：自定义输出目录 ---
REM python jfjb_spider.py --start-date 2010-01-01 --out-dir D:\jfjb_data --delay 2

REM ============================================================
REM  ↓↓↓ 在此处写你要执行的命令（默认：抓取今天） ↓↓↓
REM ============================================================

python jfjb_spider.py --start-date 2026-01-01 --delay 2

REM ============================================================

pause
