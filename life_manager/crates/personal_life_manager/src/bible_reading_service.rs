use app_core::models::BibleReading;
use chrono::Utc;
use sqlx::SqlitePool;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum BibleReadingServiceError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
}

pub type BibleReadingResult<T> = Result<T, BibleReadingServiceError>;

pub async fn log_bible_reading(
    pool: &SqlitePool,
    book: &str,
    chapter: i64,
    verses: &str,
) -> BibleReadingResult<BibleReading> {
    let now = Utc::now();
    let reading_id = sqlx::query(
        "INSERT INTO bible_readings (book, chapter, verses, read_at) VALUES (?, ?, ?, ?)",
    )
    .bind(book)
    .bind(chapter)
    .bind(verses)
    .bind(now)
    .execute(pool)
    .await?
    .last_insert_rowid();

    sqlx::query_as("SELECT * FROM bible_readings WHERE id = ?")
        .bind(reading_id)
        .fetch_one(pool)
        .await
        .map_err(BibleReadingServiceError::Database)
}

pub async fn get_all_bible_readings(pool: &SqlitePool) -> BibleReadingResult<Vec<BibleReading>> {
    sqlx::query_as("SELECT * FROM bible_readings ORDER BY read_at DESC")
        .fetch_all(pool)
        .await
        .map_err(BibleReadingServiceError::Database)
}