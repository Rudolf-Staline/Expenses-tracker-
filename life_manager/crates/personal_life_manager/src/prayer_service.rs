use app_core::models::{PrayerRequest, PrayerStatus};
use chrono::Utc;
use sqlx::SqlitePool;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum PrayerServiceError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
}

pub type PrayerResult<T> = Result<T, PrayerServiceError>;

pub async fn create_prayer_request(
    pool: &SqlitePool,
    subject: &str,
    details: Option<&str>,
) -> PrayerResult<PrayerRequest> {
    let now = Utc::now();
    let request_id = sqlx::query(
        "INSERT INTO prayer_requests (subject, details, status, created_at) VALUES (?, ?, ?, ?)",
    )
    .bind(subject)
    .bind(details)
    .bind(PrayerStatus::Pending)
    .bind(now)
    .execute(pool)
    .await?
    .last_insert_rowid();

    sqlx::query_as("SELECT * FROM prayer_requests WHERE id = ?")
        .bind(request_id)
        .fetch_one(pool)
        .await
        .map_err(PrayerServiceError::Database)
}

pub async fn get_all_prayer_requests(pool: &SqlitePool) -> PrayerResult<Vec<PrayerRequest>> {
    sqlx::query_as("SELECT * FROM prayer_requests ORDER BY created_at DESC")
        .fetch_all(pool)
        .await
        .map_err(PrayerServiceError::Database)
}

pub async fn update_prayer_status(
    pool: &SqlitePool,
    id: i64,
    status: PrayerStatus,
) -> PrayerResult<()> {
    sqlx::query("UPDATE prayer_requests SET status = ? WHERE id = ?")
        .bind(status)
        .bind(id)
        .execute(pool)
        .await?;
    Ok(())
}