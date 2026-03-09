# 解放军报当天文章 PDF 爬虫

这个脚本会自动定位解放军报当天版面，抓取当天所有版面的全部文章，并导出为 PDF。

## 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 运行

默认抓取当天最新版，同时输出单篇 PDF 和汇总 PDF：

```powershell
.\.venv\Scripts\python.exe .\jfjb_spider.py
```

指定日期：

```powershell
.\.venv\Scripts\python.exe .\jfjb_spider.py --date 2026-03-10
```

仅输出汇总 PDF：

```powershell
.\.venv\Scripts\python.exe .\jfjb_spider.py --combined-only
```

仅输出单篇 PDF：

```powershell
.\.venv\Scripts\python.exe .\jfjb_spider.py --individual-only
```

输出文件默认在 `output/日期/` 下。