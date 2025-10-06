use app_core::models::{Family, Item, Unit};
use chrono::Utc;
use serde::Serialize;
use sqlx::{FromRow, Row, SqlitePool};
use thiserror::Error;

#[derive(Debug, Serialize)]
pub struct ItemWithPrice {
    pub id: i64,
    pub name: String,
    pub packaging: Option<String>,
    pub family: Family,
    pub item_type: Option<String>,
    pub volume: Option<f64>,
    pub volume_unit: Option<Unit>,
    pub weight: Option<f64>,
    pub weight_unit: Option<Unit>,
    pub archived: bool,
    pub price: Option<f64>,
}

impl<'r> FromRow<'r, sqlx::sqlite::SqliteRow> for ItemWithPrice {
    fn from_row(row: &'r sqlx::sqlite::SqliteRow) -> Result<Self, sqlx::Error> {
        Ok(ItemWithPrice {
            id: row.try_get("id")?,
            name: row.try_get("name")?,
            packaging: row.try_get("packaging")?,
            family: row.try_get("family")?,
            item_type: row.try_get("item_type")?,
            volume: row.try_get("volume")?,
            volume_unit: row.try_get("volume_unit")?,
            weight: row.try_get("weight")?,
            weight_unit: row.try_get("weight_unit")?,
            archived: row.try_get("archived")?,
            price: row.try_get("price")?,
        })
    }
}

#[derive(Error, Debug)]
pub enum ItemServiceError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    #[error("Item with name '{0}' already exists")]
    NameAlreadyExists(String),
    #[error("Item not found with ID: {0}")]
    NotFound(i64),
    #[error("Cannot delete item {0} because it has associated expenses")]
    ItemHasExpenses(i64),
}

pub type ItemResult<T> = Result<T, ItemServiceError>;

pub async fn create_item(
    pool: &SqlitePool,
    name: &str,
    family: Family,
    initial_price: f64,
    packaging: Option<String>,
    item_type: Option<String>,
) -> ItemResult<Item> {
    let mut tx = pool.begin().await?;

    let existing = sqlx::query("SELECT id FROM items WHERE name = ?")
        .bind(name)
        .fetch_optional(&mut *tx)
        .await?;
    if existing.is_some() {
        return Err(ItemServiceError::NameAlreadyExists(name.to_string()));
    }

    let item_id = sqlx::query(
        "INSERT INTO items (name, family, packaging, item_type, archived) VALUES (?, ?, ?, ?, 0)",
    )
    .bind(name)
    .bind(family)
    .bind(packaging)
    .bind(item_type)
    .execute(&mut *tx)
    .await?
    .last_insert_rowid();

    let now = Utc::now();
    sqlx::query("INSERT INTO price_history (item_id, price, effective_date) VALUES (?, ?, ?)")
        .bind(item_id)
        .bind(initial_price)
        .bind(now)
        .execute(&mut *tx)
        .await?;

    tx.commit().await?;
    get_item_by_id(pool, item_id).await
}

pub async fn get_item_by_id(pool: &SqlitePool, id: i64) -> ItemResult<Item> {
    sqlx::query_as("SELECT * FROM items WHERE id = ?")
        .bind(id)
        .fetch_one(pool)
        .await
        .map_err(|e| match e {
            sqlx::Error::RowNotFound => ItemServiceError::NotFound(id),
            _ => ItemServiceError::Database(e),
        })
}

pub async fn get_all_active_items_with_price(pool: &SqlitePool) -> ItemResult<Vec<ItemWithPrice>> {
    sqlx::query_as(
        r#"
        SELECT
            i.*,
            ph.price
        FROM
            items i
        LEFT JOIN
            (
                SELECT
                    item_id,
                    price,
                    ROW_NUMBER() OVER(PARTITION BY item_id ORDER BY effective_date DESC) as rn
                FROM
                    price_history
            ) ph ON i.id = ph.item_id AND ph.rn = 1
        WHERE
            i.archived = 0
        ORDER BY
            i.name
        "#,
    )
    .fetch_all(pool)
    .await
    .map_err(ItemServiceError::Database)
}

pub async fn update_item_price(pool: &SqlitePool, item_id: i64, new_price: f64) -> ItemResult<()> {
    get_item_by_id(pool, item_id).await?;
    let now = Utc::now();
    sqlx::query("INSERT INTO price_history (item_id, price, effective_date) VALUES (?, ?, ?)")
        .bind(item_id)
        .bind(new_price)
        .bind(now)
        .execute(pool)
        .await?;
    Ok(())
}

pub async fn archive_item(pool: &SqlitePool, item_id: i64) -> ItemResult<()> {
    let rows_affected = sqlx::query("UPDATE items SET archived = 1 WHERE id = ?")
        .bind(item_id)
        .execute(pool)
        .await?
        .rows_affected();

    if rows_affected == 0 {
        Err(ItemServiceError::NotFound(item_id))
    } else {
        Ok(())
    }
}

pub async fn delete_item(pool: &SqlitePool, item_id: i64) -> ItemResult<()> {
    let mut tx = pool.begin().await?;

    sqlx::query("SELECT id FROM items WHERE id = ?")
        .bind(item_id)
        .fetch_optional(&mut *tx)
        .await?
        .ok_or(ItemServiceError::NotFound(item_id))?;

    let expense_count: (i64,) =
        sqlx::query_as("SELECT COUNT(*) FROM expenses WHERE item_id = ?")
            .bind(item_id)
            .fetch_one(&mut *tx)
            .await?;

    if expense_count.0 > 0 {
        return Err(ItemServiceError::ItemHasExpenses(item_id));
    }

    sqlx::query("DELETE FROM items WHERE id = ?")
        .bind(item_id)
        .execute(&mut *tx)
        .await?;

    tx.commit().await?;
    Ok(())
}