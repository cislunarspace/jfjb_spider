# Web Dashboard

通过浏览器配置抓取任务、监控进度和浏览结果。

## 启动方式

```bash
# 终端 1：启动 Rust 后端（默认 http://127.0.0.1:3000）
cd server && cargo run

# 终端 2：启动前端开发服务器（默认 http://localhost:5173，自动代理 API）
cd frontend && npm run dev
```

打开 http://localhost:5173 即可使用。

## 生产部署

```bash
cd frontend && npm run build
cd ../server && cargo build --release
cd .. && ./server/target/release/jfjb-server
```

生产模式下 Rust 服务器直接托管前端静态文件，只需一个端口（3000）。

## 界面布局

### 抓取页面

- **报纸类型**：选择解放军报或人民日报
- **抓取模式**：单日抓取或批量抓取（批量仅限解放军报）
- **日期选择**：选择目标日期（单日）或起止日期（批量）
- **输出目录**：指定 PDF 文件的输出位置
- **导出选项**：选择输出单篇 PDF、合集 PDF 或两者
- **开始抓取**：启动后端抓取任务
- **实时进度**：进度条 + 滚动日志，通过 SSE 实时推送

### 结果页面

- **文件列表**：按日期分组显示输出目录，可展开/折叠
- **PDF 预览**：选中 PDF 文件后在 iframe 中预览
- **操作**：新窗口打开、复制下载链接

## API 接口

后端提供以下 REST 接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/crawl` | 启动抓取任务 |
| GET | `/api/crawl/stream` | SSE 实时事件流 |
| POST | `/api/crawl/cancel` | 取消当前任务 |
| GET | `/api/status` | 查询任务状态 |
| GET | `/api/files` | 列出输出文件 |
| GET | `/api/files/:path` | 下载指定文件 |

### 启动抓取

```bash
curl -X POST http://127.0.0.1:3000/api/crawl \
  -H 'Content-Type: application/json' \
  -d '{"paper_type":"jfjb","paper_date":"2026-03-10","output_dir":"output","export_individual":true,"export_combined":true}'
```

### 监听事件流

```bash
curl http://127.0.0.1:3000/api/crawl/stream
```

事件格式（JSON Lines）：

- `{"type":"progress","current":1,"total":30,"message":"正在抓取 2026-03-10"}`
- `{"type":"log","level":"INFO","message":"日期: 2026-03-10, 文章数: 42"}`
- `{"type":"finished","success":1,"fail":0,"skip":0,"total":1}`
- `{"type":"error","message":"错误信息"}`
