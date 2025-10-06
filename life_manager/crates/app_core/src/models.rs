use serde::{Serialize, Deserialize};
use sqlx::decode::Decode;
use sqlx::encode::{Encode, IsNull};
use sqlx::sqlite::{Sqlite, SqliteArgumentValue, SqliteTypeInfo, SqliteValueRef, SqliteRow};
use sqlx::{FromRow, Type, Row};
use std::str::FromStr;
use strum::{Display, EnumString};
use chrono::{DateTime, Utc, NaiveDate};
use sqlx::error::BoxDynError;

#[derive(Debug, Serialize, Deserialize, Clone, Display, EnumString, Default, PartialEq)]
#[strum(serialize_all = "PascalCase")]
pub enum Unit {
    Gram,
    Kilogram,
    Pound,
    Milliliter,
    Liter,
    Gallon,
    #[default]
    Piece,
    Pack,
}

impl Type<Sqlite> for Unit {
    fn type_info() -> SqliteTypeInfo {
        <String as Type<Sqlite>>::type_info()
    }
}

impl<'q> Encode<'q, Sqlite> for Unit {
    fn encode_by_ref(&self, buf: &mut Vec<SqliteArgumentValue<'q>>) -> IsNull {
        let s = self.to_string();
        <String as Encode<'q, Sqlite>>::encode_by_ref(&s, buf)
    }
}

impl<'r> Decode<'r, Sqlite> for Unit {
    fn decode(value: SqliteValueRef<'r>) -> Result<Self, BoxDynError> {
        let s = <String as Decode<Sqlite>>::decode(value)?;
        Self::from_str(&s).map_err(Into::into)
    }
}


#[derive(Debug, Serialize, Deserialize, Clone, Display, EnumString, Default, PartialEq)]
#[strum(serialize_all = "PascalCase")]
pub enum Family {
    Food,
    Drink,
    Cleaning,
    Hygiene,
    Clothing,
    Electronics,
    Leisure,
    Service,
    Donation,
    #[default]
    Other,
}

impl Type<Sqlite> for Family {
    fn type_info() -> SqliteTypeInfo {
        <String as Type<Sqlite>>::type_info()
    }
}

impl<'q> Encode<'q, Sqlite> for Family {
    fn encode_by_ref(&self, buf: &mut Vec<SqliteArgumentValue<'q>>) -> IsNull {
        let s = self.to_string();
        <String as Encode<'q, Sqlite>>::encode_by_ref(&s, buf)
    }
}

impl<'r> Decode<'r, Sqlite> for Family {
    fn decode(value: SqliteValueRef<'r>) -> Result<Self, BoxDynError> {
        let s = <String as Decode<Sqlite>>::decode(value)?;
        Self::from_str(&s).map_err(Into::into)
    }
}


#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Item {
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
}

impl<'r> FromRow<'r, SqliteRow> for Item {
    fn from_row(row: &'r SqliteRow) -> Result<Self, sqlx::Error> {
        Ok(Item {
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
        })
    }
}

#[derive(Debug, Serialize, Deserialize, FromRow, Clone)]
pub struct PriceHistory {
    pub id: i64,
    pub item_id: i64,
    pub price: f64,
    pub effective_date: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Expense {
    pub id: i64,
    pub item_id: i64,
    pub quantity: f64,
    pub price_at_time_of_expense: f64,
    pub expense_date: NaiveDate,
}

impl<'r> FromRow<'r, SqliteRow> for Expense {
    fn from_row(row: &'r SqliteRow) -> Result<Self, sqlx::Error> {
        Ok(Expense {
            id: row.try_get("id")?,
            item_id: row.try_get("item_id")?,
            quantity: row.try_get("quantity")?,
            price_at_time_of_expense: row.try_get("price_at_time_of_expense")?,
            expense_date: row.try_get("expense_date")?,
        })
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DailyAdjustment {
    pub id: i64,
    pub adjustment_date: NaiveDate,
    pub amount: f64,
}

impl<'r> FromRow<'r, SqliteRow> for DailyAdjustment {
    fn from_row(row: &'r SqliteRow) -> Result<Self, sqlx::Error> {
        Ok(DailyAdjustment {
            id: row.try_get("id")?,
            adjustment_date: row.try_get("adjustment_date")?,
            amount: row.try_get("amount")?,
        })
    }
}