use axum::{
    body::Body,
    extract::{Path, Query},
    http::header,
    response::{IntoResponse, Response},
    routing::get,
    Json, Router,
};
use serde::Deserialize;
use std::path::PathBuf;
use std::sync::Arc;

use crate::error::{AppError, Result};
use crate::models::FileInfo;
use crate::AppState;

#[derive(Deserialize)]
pub struct ListQuery {
    path: Option<String>,
}

pub fn routes() -> Router<Arc<AppState>> {
    Router::new()
        .route("/api/files", get(list_files))
        .route("/api/files/{*path}", get(get_file))
}

async fn list_files(Query(query): Query<ListQuery>) -> Result<Json<Vec<FileInfo>>> {
    let base = PathBuf::from("output");
    let target = if let Some(sub) = &query.path {
        base.join(sub)
    } else {
        base.clone()
    };

    if !target.exists() {
        return Ok(Json(vec![]));
    }

    let mut entries = Vec::new();
    let mut dir = tokio::fs::read_dir(&target).await?;
    while let Some(entry) = dir.next_entry().await? {
        let metadata = entry.metadata().await?;
        let name = entry.file_name().to_string_lossy().to_string();
        let path = entry.path();
        let rel_path = path
            .strip_prefix(&base)
            .unwrap_or(&path)
            .to_string_lossy()
            .to_string();

        let modified = metadata
            .modified()
            .map(|t| {
                let datetime: chrono::DateTime<chrono::Local> = t.into();
                datetime.format("%Y-%m-%d %H:%M").to_string()
            })
            .unwrap_or_default();

        entries.push(FileInfo {
            name,
            path: rel_path,
            size: metadata.len(),
            modified,
            is_dir: metadata.is_dir(),
        });
    }

    // 目录在前，按名称排序
    entries.sort_by(|a, b| {
        b.is_dir
            .cmp(&a.is_dir)
            .then_with(|| a.name.cmp(&b.name))
    });

    Ok(Json(entries))
}

async fn get_file(Path(file_path): Path<String>) -> Result<impl IntoResponse> {
    let base = PathBuf::from("output");
    let full_path = base.join(&file_path);

    if !full_path.exists() {
        return Err(AppError::NotFound(format!("文件不存在: {file_path}")));
    }

    if full_path.is_dir() {
        return Err(AppError::BadRequest("路径是目录，不是文件".into()));
    }

    // 防止路径遍历
    let canonical = full_path.canonicalize()?;
    let canonical_base = base.canonicalize()?;
    if !canonical.starts_with(&canonical_base) {
        return Err(AppError::BadRequest("非法路径".into()));
    }

    let content = tokio::fs::read(&full_path).await?;
    let mime = if full_path.extension().is_some_and(|e| e == "pdf") {
        "application/pdf"
    } else {
        "application/octet-stream"
    };

    let response = Response::builder()
        .header(header::CONTENT_TYPE, mime)
        .body(Body::from(content))
        .map_err(|e| AppError::Internal(e.to_string()))?;

    Ok(response)
}
