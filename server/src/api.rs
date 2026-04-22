use axum::{
    extract::State,
    routing::{get, post},
    Json, Router,
};
use std::sync::Arc;

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
    State(_state): State<Arc<AppState>>,
    Json(_req): Json<CrawlRequest>,
) -> Result<Json<TaskResponse>> {
    Ok(Json(TaskResponse {
        task_id: "todo".to_string(),
    }))
}

async fn stream_events(
    State(_state): State<Arc<AppState>>,
) -> Result<String> {
    Err(crate::error::AppError::Internal("not implemented".into()))
}

async fn cancel_crawl(
    State(_state): State<Arc<AppState>>,
) -> Result<Json<serde_json::Value>> {
    Ok(Json(serde_json::json!({ "ok": true })))
}

async fn get_status(
    State(_state): State<Arc<AppState>>,
) -> Json<CrawlStatus> {
    Json(CrawlStatus {
        running: false,
        task_id: None,
    })
}
