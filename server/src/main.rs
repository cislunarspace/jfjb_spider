mod api;
mod crawler;
mod error;
mod files;
mod models;

use axum::Router;
use std::sync::Arc;
use tokio::sync::{broadcast, Mutex};
use tower_http::cors::CorsLayer;

pub struct AppState {
    pub crawl_tx: broadcast::Sender<models::CrawlEvent>,
    pub crawl_handle: Mutex<Option<crawler::CrawlHandle>>,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "jfjb_server=debug,tower_http=debug".into()),
        )
        .init();

    let (crawl_tx, _) = broadcast::channel::<models::CrawlEvent>(100);
    let state = Arc::new(AppState {
        crawl_tx,
        crawl_handle: Mutex::new(None),
    });

    let app = Router::new()
        .merge(api::routes())
        .merge(files::routes())
        .layer(CorsLayer::permissive())
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3000")
        .await
        .unwrap();
    tracing::info!("Server listening on http://127.0.0.1:3000");
    axum::serve(listener, app).await.unwrap();
}
