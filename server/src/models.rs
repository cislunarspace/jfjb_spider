use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct CrawlRequest {
    pub paper_type: String,
    pub paper_date: Option<String>,
    pub start_date: Option<String>,
    pub end_date: Option<String>,
    #[serde(default = "default_output_dir")]
    pub output_dir: String,
    #[serde(default = "default_true")]
    pub export_individual: bool,
    #[serde(default = "default_true")]
    pub export_combined: bool,
    pub font_dir: Option<String>,
}

fn default_output_dir() -> String {
    "output".to_string()
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
#[serde(rename_all = "lowercase")]
pub enum CrawlEvent {
    Progress {
        current: u32,
        total: u32,
        message: String,
    },
    Log {
        level: String,
        message: String,
    },
    Finished {
        success: u32,
        fail: u32,
        skip: u32,
        total: u32,
    },
    Error {
        message: String,
    },
}

#[derive(Debug, Serialize)]
pub struct FileInfo {
    pub name: String,
    pub path: String,
    pub size: u64,
    pub modified: String,
    pub is_dir: bool,
}

#[derive(Debug, Serialize)]
pub struct CrawlStatus {
    pub running: bool,
    pub task_id: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct TaskResponse {
    pub task_id: String,
}
