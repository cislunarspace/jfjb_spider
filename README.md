# 报纸文章 PDF 爬虫

当前工作区包含两套脚本：

- `jfjb_spider.py`：抓取解放军报当天所有版面文章并导出 PDF
- `rmrb_spider.py`：抓取人民日报当天所有版面文章并导出 PDF

## 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 运行

## 解放军报

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

## 人民日报

默认抓取当天最新版，同时输出单篇 PDF 和汇总 PDF：

```powershell
.\.venv\Scripts\python.exe .\rmrb_spider.py
```

指定日期：

```powershell
.\.venv\Scripts\python.exe .\rmrb_spider.py --date 2026-03-10
```

仅输出汇总 PDF：

```powershell
.\.venv\Scripts\python.exe .\rmrb_spider.py --combined-only
```

仅输出单篇 PDF：

```powershell
.\.venv\Scripts\python.exe .\rmrb_spider.py --individual-only
```

输出文件默认在 `output/rmrb/日期/` 下。