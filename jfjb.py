"""解放军报文章 PDF 爬虫。

用法:
    python jfjb.py                         # 抓取今天
    python jfjb.py --date 2026-03-10       # 指定日期
    python jfjb.py --start-date 2026-01-01 --end-date 2026-03-31 --delay 2  # 批量
    python jfjb.py --help                  # 查看所有参数
"""

from newspaper_pdf.jfjb_spider import main

if __name__ == "__main__":
    main()
