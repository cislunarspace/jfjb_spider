use axum::{
    routing::get,
    Router,
};
use std::sync::Arc;

use crate::AppState;

pub fn routes() -> Router<Arc<AppState>> {
    Router::new()
        .route("/api/files", get(list_files))
        .route("/api/files/{*path}", get(get_file))
}

async fn list_files() -> axum::Json<Vec<crate::models::FileInfo>> {
    axum::Json(vec![])
}

async fn get_file() -> crate::error::Result<String> {
    Err(crate::error::AppError::NotFound("not implemented".into()))
}
