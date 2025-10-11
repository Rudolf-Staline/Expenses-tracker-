use app_core::models::{BibleReading, Family, Item, JournalEntry, PrayerRequest, PrayerStatus};
use expense_manager::{expense_service, item_service::{self, ItemWithPrice}};
use personal_life_manager::{bible_reading_service, journal_service, prayer_service};
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

// --- Journal Commands ---

#[tauri::command]
pub async fn create_journal_entry(
    state: State<'_, AppState>,
    title: String,
    content: String,
) -> CommandResult<JournalEntry> {
    log::info!("Received create_journal_entry with title: {}", title);
    journal_service::create_journal_entry(&state.db_pool, &title, &content)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_all_journal_entries(state: State<'_, AppState>) -> CommandResult<Vec<JournalEntry>> {
    log::info!("Received get_all_journal_entries command");
    journal_service::get_all_journal_entries(&state.db_pool)
        .await
        .map_err(|e| e.to_string())
}

// --- Prayer Request Commands ---

#[tauri::command]
pub async fn create_prayer_request(
    state: State<'_, AppState>,
    subject: String,
    details: Option<String>,
) -> CommandResult<PrayerRequest> {
    prayer_service::create_prayer_request(&state.db_pool, &subject, details.as_deref())
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_all_prayer_requests(state: State<'_, AppState>) -> CommandResult<Vec<PrayerRequest>> {
    prayer_service::get_all_prayer_requests(&state.db_pool)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn update_prayer_status(
    state: State<'_, AppState>,
    id: i64,
    status: PrayerStatus,
) -> CommandResult<()> {
    prayer_service::update_prayer_status(&state.db_pool, id, status)
        .await
        .map_err(|e| e.to_string())
}

// --- Bible Reading Commands ---

#[tauri::command]
pub async fn log_bible_reading(
    state: State<'_, AppState>,
    book: String,
    chapter: i64,
    verses: String,
) -> CommandResult<BibleReading> {
    bible_reading_service::log_bible_reading(&state.db_pool, &book, chapter, &verses)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_all_bible_readings(state: State<'_, AppState>) -> CommandResult<Vec<BibleReading>> {
    bible_reading_service::get_all_bible_readings(&state.db_pool)
        .await
        .map_err(|e| e.to_string())
}