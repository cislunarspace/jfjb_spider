"""解放军报爬虫（向后兼容入口）。

此文件保留用于兼容旧的调用方式（python jfjb_spider.py）。
新代码请使用 python jfjb.py 或 from newspaper_pdf.jfjb_spider import main。
"""

from newspaper_pdf.jfjb_spider import main

if __name__ == "__main__":
    main()
