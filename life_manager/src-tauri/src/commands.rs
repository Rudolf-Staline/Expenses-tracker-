use app_core::models::{Family, Item};
use expense_manager::{item_service::{self, ItemWithPrice}, expense_service};
use sqlx::SqlitePool;
use tauri::State;
use chrono::NaiveDate;

// A generic wrapper for command results to be sent to the frontend.
type CommandResult<T> = Result<T, String>;

// State management for the database pool
pub struct AppState {
    pub db_pool: SqlitePool,
}

// --- Item Commands ---

#[tauri::command]
pub async fn create_item(
    state: State<'_, AppState>,
    name: String,
    family: Family,
    initial_price: f64,
    packaging: Option<String>,
    item_type: Option<String>,
) -> CommandResult<Item> {
    log::info!("Received create_item command with name: {}", name);
    item_service::create_item(&state.db_pool, &name, family, initial_price, packaging, item_type)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_item(state: State<'_, AppState>, id: i64) -> CommandResult<Item> {
    log::info!("Received get_item command for id: {}", id);
    item_service::get_item_by_id(&state.db_pool, id)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn update_item_price(state: State<'_, AppState>, item_id: i64, new_price: f64) -> CommandResult<()> {
    log::info!("Received update_item_price for item_id: {}", item_id);
    item_service::update_item_price(&state.db_pool, item_id, new_price)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn archive_item(state: State<'_, AppState>, item_id: i64) -> CommandResult<()> {
    log::info!("Received archive_item for item_id: {}", item_id);
    item_service::archive_item(&state.db_pool, item_id)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_all_active_items(state: State<'_, AppState>) -> CommandResult<Vec<ItemWithPrice>> {
    log::info!("Received get_all_active_items command");
    item_service::get_all_active_items_with_price(&state.db_pool)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn delete_item(state: State<'_, AppState>, item_id: i64) -> CommandResult<()> {
    log::info!("Received delete_item for item_id: {}", item_id);
    item_service::delete_item(&state.db_pool, item_id)
        .await
        .map_err(|e| e.to_string())
}


// --- Expense Commands ---

#[tauri::command]
pub async fn record_expense(
    state: State<'_, AppState>,
    item_id: i64,
    quantity: f64,
    expense_date: NaiveDate,
) -> CommandResult<app_core::models::Expense> {
    log::info!("Received record_expense for item_id: {}", item_id);
    expense_service::record_expense(&state.db_pool, item_id, quantity, expense_date)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_expenses_for_period(
    state: State<'_, AppState>,
    start_date: NaiveDate,
    end_date: NaiveDate,
) -> CommandResult<Vec<app_core::models::Expense>> {
    log::info!("Received get_expenses_for_period from {} to {}", start_date, end_date);
    expense_service::get_expenses_for_period(&state.db_pool, start_date, end_date)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn calculate_total_for_period(
    state: State<'_, AppState>,
    start_date: NaiveDate,
    end_date: NaiveDate,
) -> CommandResult<f64> {
    log::info!("Received calculate_total_for_period from {} to {}", start_date, end_date);
    expense_service::calculate_total_for_period(&state.db_pool, start_date, end_date)
        .await
        .map_err(|e| e.to_string())
}