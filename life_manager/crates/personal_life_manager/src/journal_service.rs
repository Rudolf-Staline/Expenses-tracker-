use app_core::models::JournalEntry;
use chrono::Utc;
use sqlx::SqlitePool;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum JournalServiceError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
}

pub type JournalResult<T> = Result<T, JournalServiceError>;

pub async fn create_journal_entry(
    pool: &SqlitePool,
    title: &str,
    content: &str,
) -> JournalResult<JournalEntry> {
    let now = Utc::now();
    let entry_id = sqlx::query(
        "INSERT INTO journal_entries (title, content, created_at) VALUES (?, ?, ?)",
    )
    .bind(title)
    .bind(content)
    .bind(now)
    .execute(pool)
    .await?
    .last_insert_rowid();

    sqlx::query_as("SELECT * FROM journal_entries WHERE id = ?")
        .bind(entry_id)
        .fetch_one(pool)
        .await
        .map_err(JournalServiceError::Database)
}

pub async fn get_all_journal_entries(pool: &SqlitePool) -> JournalResult<Vec<JournalEntry>> {
    sqlx::query_as("SELECT * FROM journal_entries ORDER BY created_at DESC")
        .fetch_all(pool)
        .await
        .map_err(JournalServiceError::Database)
}