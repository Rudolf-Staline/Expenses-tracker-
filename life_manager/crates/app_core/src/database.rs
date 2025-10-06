use sqlx::{migrate::MigrateDatabase, Sqlite, SqlitePool};
use thiserror::Error;
use std::path::Path;
use dotenvy::dotenv;
use std::env;

#[derive(Error, Debug)]
pub enum DatabaseError {
    #[error("Database connection failed: {0}")]
    ConnectionFailed(sqlx::Error),
    #[error("Database migration failed: {0}")]
    MigrationFailed(sqlx::migrate::MigrateError),
    #[error("Database query failed: {0}")]
    QueryFailed(sqlx::Error),
    #[error("DATABASE_URL not set")]
    DatabaseUrlNotSet,
}

pub type DbResult<T> = Result<T, DatabaseError>;

/// Initializes the database connection and runs migrations.
pub async fn init_db() -> DbResult<SqlitePool> {
    dotenv().ok(); // Load .env file
    let db_url = env::var("DATABASE_URL").map_err(|_| DatabaseError::DatabaseUrlNotSet)?;

    if !Sqlite::database_exists(&db_url).await.unwrap_or(false) {
        log::info!("Creating database {}", db_url);
        match Sqlite::create_database(&db_url).await {
            Ok(_) => log::info!("Create database success"),
            Err(error) => panic!("error: {}", error),
        }
    } else {
        log::info!("Database already exists");
    }

    let db_pool = SqlitePool::connect(&db_url)
        .await
        .map_err(DatabaseError::ConnectionFailed)?;

    // This will look for a `migrations` directory in the crate root (next to `src`)
    // and embed the migrations into the binary at compile time.
    sqlx::migrate!("./migrations")
        .run(&db_pool)
        .await
        .map_err(DatabaseError::MigrationFailed)?;

    Ok(db_pool)
}