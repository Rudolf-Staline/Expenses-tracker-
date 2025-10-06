use app_core::models::{DailyAdjustment, Expense};
use chrono::NaiveDate;
use sqlx::{FromRow, SqlitePool};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ExpenseServiceError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    #[error("Item not found with ID: {0}")]
    ItemNotFound(i64),
    #[error("No price history found for item {0} on or before date {1}")]
    NoPriceHistory(i64, NaiveDate),
}

pub type ExpenseResult<T> = Result<T, ExpenseServiceError>;

pub async fn record_expense(
    pool: &SqlitePool,
    item_id: i64,
    quantity: f64,
    expense_date: NaiveDate,
) -> ExpenseResult<Expense> {
    let mut tx = pool.begin().await?;

    sqlx::query("SELECT id FROM items WHERE id = ?")
        .bind(item_id)
        .fetch_optional(&mut *tx)
        .await?
        .ok_or(ExpenseServiceError::ItemNotFound(item_id))?;

    let price_record: Option<(f64,)> = sqlx::query_as(
        r#"
        SELECT price
        FROM price_history
        WHERE item_id = ? AND date(effective_date) <= date(?)
        ORDER BY effective_date DESC
        LIMIT 1
        "#,
    )
    .bind(item_id)
    .bind(expense_date)
    .fetch_optional(&mut *tx)
    .await?;

    let price_at_time_of_expense = price_record
        .map(|r| r.0)
        .ok_or(ExpenseServiceError::NoPriceHistory(item_id, expense_date))?;

    let expense_id = sqlx::query(
        "INSERT INTO expenses (item_id, quantity, price_at_time_of_expense, expense_date) VALUES (?, ?, ?, ?)",
    )
    .bind(item_id)
    .bind(quantity)
    .bind(price_at_time_of_expense)
    .bind(expense_date)
    .execute(&mut *tx)
    .await?
    .last_insert_rowid();

    tx.commit().await?;

    sqlx::query_as("SELECT * FROM expenses WHERE id = ?")
        .bind(expense_id)
        .fetch_one(pool)
        .await
        .map_err(ExpenseServiceError::Database)
}

pub async fn get_expenses_for_period(
    pool: &SqlitePool,
    start_date: NaiveDate,
    end_date: NaiveDate,
) -> ExpenseResult<Vec<Expense>> {
    sqlx::query_as("SELECT * FROM expenses WHERE expense_date BETWEEN ? AND ? ORDER BY expense_date DESC")
        .bind(start_date)
        .bind(end_date)
        .fetch_all(pool)
        .await
        .map_err(ExpenseServiceError::Database)
}

pub async fn record_daily_adjustment(
    pool: &SqlitePool,
    date: NaiveDate,
    amount: f64,
) -> ExpenseResult<DailyAdjustment> {
    sqlx::query(
        "INSERT INTO daily_adjustments (adjustment_date, amount) VALUES (?, ?) ON CONFLICT(adjustment_date) DO UPDATE SET amount = excluded.amount",
    )
    .bind(date)
    .bind(amount)
    .execute(pool)
    .await?;

    sqlx::query_as("SELECT * FROM daily_adjustments WHERE adjustment_date = ?")
        .bind(date)
        .fetch_one(pool)
        .await
        .map_err(ExpenseServiceError::Database)
}

pub async fn calculate_total_for_period(
    pool: &SqlitePool,
    start_date: NaiveDate,
    end_date: NaiveDate,
) -> ExpenseResult<f64> {
    let mut tx = pool.begin().await?;

    let expenses_total: f64 = sqlx::query_scalar::<_, Option<f64>>("SELECT SUM(quantity * price_at_time_of_expense) FROM expenses WHERE expense_date BETWEEN ? AND ?")
        .bind(start_date)
        .bind(end_date)
        .fetch_one(&mut *tx)
        .await?
        .unwrap_or(0.0);

    let adjustments_total: f64 = sqlx::query_scalar::<_, Option<f64>>("SELECT SUM(amount) FROM daily_adjustments WHERE adjustment_date BETWEEN ? AND ?")
        .bind(start_date)
        .bind(end_date)
        .fetch_one(&mut *tx)
        .await?
        .unwrap_or(0.0);

    tx.commit().await?;
    Ok(expenses_total + adjustments_total)
}