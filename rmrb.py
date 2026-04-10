"""人民日报文章 PDF 爬虫。

用法:
    python rmrb.py                         # 抓取今天
    python rmrb.py --date 2026-03-10       # 指定日期
    python rmrb.py --help                  # 查看所有参数
"""

from newspaper_pdf.rmrb_spider import main

if __name__ == "__main__":
    main()
