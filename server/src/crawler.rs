use std::process::Stdio;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command;
use tokio::sync::{broadcast, oneshot, Mutex};

use crate::models::{CrawlEvent, CrawlRequest};

#[derive(Debug)]
pub struct CrawlHandle {
    pub task_id: String,
    kill_tx: oneshot::Sender<()>,
}

impl CrawlHandle {
    pub async fn spawn(
        request: &CrawlRequest,
        tx: &broadcast::Sender<CrawlEvent>,
        crawl_handle: &Arc<Mutex<Option<CrawlHandle>>>,
    ) -> Result<Self, String> {
        let task_id = uuid::Uuid::new_v4().to_string();

        let mut cmd = Command::new("uv");
        cmd.arg("run");

        // 选择爬虫模块
        match request.paper_type.as_str() {
            "jfjb" => cmd.arg("python").arg("-m").arg("newspaper_pdf.jfjb_spider"),
            "rmrb" => cmd.arg("python").arg("-m").arg("newspaper_pdf.rmrb_spider"),
            "gmrb" => cmd.arg("python").arg("-m").arg("newspaper_pdf.gmrb_spider"),
            other => return Err(format!("未知报纸类型: {other}")),
        };

        cmd.arg("--json-progress");
        cmd.arg("--out-dir").arg(&request.output_dir);

        if let Some(date) = &request.paper_date {
            cmd.arg("--date").arg(date);
        }
        if let Some(start) = &request.start_date {
            cmd.arg("--start-date").arg(start);
        }
        if let Some(end) = &request.end_date {
            cmd.arg("--end-date").arg(end);
        }
        if !request.export_individual {
            cmd.arg("--combined-only");
        }
        if !request.export_combined {
            cmd.arg("--individual-only");
        }
        if let Some(font_dir) = &request.font_dir {
            cmd.arg("--font-dir").arg(font_dir);
        }

        cmd.stdout(Stdio::piped());
        cmd.stderr(Stdio::piped());

        let mut child = cmd.spawn().map_err(|e| format!("启动 Python 进程失败: {e}"))?;
        let stdout = child.stdout.take().ok_or("无法获取 stdout")?;
        let stderr = child.stderr.take().ok_or("无法获取 stderr")?;

        let (kill_tx, kill_rx) = oneshot::channel::<()>();

        let tx_stdout = tx.clone();
        let tx_stderr = tx.clone();
        let handle_ref = Arc::clone(crawl_handle);

        tokio::spawn(async move {
            // 读取 stdout（JSON 事件）
            let stdout_handle = tokio::spawn(async move {
                let reader = BufReader::new(stdout);
                let mut lines = reader.lines();
                while let Ok(Some(line)) = lines.next_line().await {
                    if let Ok(event) = serde_json::from_str::<CrawlEvent>(&line) {
                        let _ = tx_stdout.send(event);
                    }
                }
            });

            // 读取 stderr（调试日志）
            let stderr_handle = tokio::spawn(async move {
                let reader = BufReader::new(stderr);
                let mut lines = reader.lines();
                while let Ok(Some(line)) = lines.next_line().await {
                    if !line.is_empty() {
                        let _ = tx_stderr.send(CrawlEvent::Log {
                            level: "STDERR".to_string(),
                            message: line,
                        });
                    }
                }
            });

            // 等待进程退出或收到 kill 信号
            tokio::select! {
                _ = kill_rx => {
                    tracing::info!("收到取消信号，正在终止子进程");
                    let _ = child.start_kill();
                    // 等待进程实际退出，释放资源
                    let _ = child.wait().await;
                }
                status = child.wait() => {
                    match status {
                        Ok(s) if s.success() => {
                            tracing::info!("子进程正常退出");
                        }
                        Ok(s) => {
                            tracing::warn!("子进程异常退出，代码: {:?}", s.code());
                        }
                        Err(e) => {
                            tracing::error!("等待子进程失败: {e}");
                        }
                    }
                }
            }

            // 确保 reader 任务完成
            let _ = stdout_handle.await;
            let _ = stderr_handle.await;

            // 清理：将 handle 设为 None，允许启动新任务
            *handle_ref.lock().await = None;
            tracing::info!("爬取任务已清理，可以启动新任务");
        });

        Ok(Self { task_id, kill_tx })
    }

    pub fn kill(self) {
        let _ = self.kill_tx.send(());
    }
}
