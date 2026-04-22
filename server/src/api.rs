use axum::{
    extract::State,
    response::sse::{Event, Sse},
    routing::{get, post},
    Json, Router,
};
use std::sync::Arc;
use tokio_stream::wrappers::BroadcastStream;
use tokio_stream::StreamExt;

use crate::crawler::CrawlHandle;
use crate::error::Result;
use crate::models::{CrawlRequest, CrawlStatus, TaskResponse};
use crate::AppState;

pub fn routes() -> Router<Arc<AppState>> {
    Router::new()
        .route("/api/crawl", post(start_crawl))
        .route("/api/crawl/stream", get(stream_events))
        .route("/api/crawl/cancel", post(cancel_crawl))
        .route("/api/status", get(get_status))
}

async fn start_crawl(
    State(state): State<Arc<AppState>>,
    Json(req): Json<CrawlRequest>,
) -> Result<Json<TaskResponse>> {
    // 检查是否已有任务在运行
    if state.crawl_handle.lock().await.is_some() {
        return Err(crate::error::AppError::BadRequest(
            "已有任务在运行".to_string(),
        ));
    }

    let handle = CrawlHandle::spawn(&req, &state.crawl_tx, &state.crawl_handle)
        .await
        .map_err(crate::error::AppError::Internal)?;

    let task_id = handle.task_id.clone();
    *state.crawl_handle.lock().await = Some(handle);

    Ok(Json(TaskResponse { task_id }))
}

async fn stream_events(
    State(state): State<Arc<AppState>>,
) -> Sse<impl tokio_stream::Stream<Item = std::result::Result<Event, std::io::Error>>> {
    let rx = state.crawl_tx.subscribe();
    let stream = BroadcastStream::new(rx).filter_map(|result| {
        result.ok().map(|event| {
            Ok(Event::default()
                .json_data(&event)
                .unwrap_or_else(|_| Event::default().data("error")))
        })
    });
    Sse::new(stream)
}

async fn cancel_crawl(
    State(state): State<Arc<AppState>>,
) -> Result<Json<serde_json::Value>> {
    let handle = state.crawl_handle.lock().await.take();
    match handle {
        Some(h) => {
            h.kill();
            Ok(Json(serde_json::json!({ "ok": true })))
        }
        None => Err(crate::error::AppError::BadRequest(
            "没有正在运行的任务".into(),
        )),
    }
}

async fn get_status(State(state): State<Arc<AppState>>) -> Json<CrawlStatus> {
    let handle = state.crawl_handle.lock().await;
    Json(CrawlStatus {
        running: handle.is_some(),
        task_id: handle.as_ref().map(|h| h.task_id.clone()),
    })
}
