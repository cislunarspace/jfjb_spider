"""人民日报爬虫（向后兼容入口）。

此文件保留用于兼容旧的调用方式（python rmrb_spider.py）。
新代码请使用 python rmrb.py 或 from newspaper_pdf.rmrb_spider import main。
"""

from newspaper_pdf.rmrb_spider import main

if __name__ == "__main__":
    main()
