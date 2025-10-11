// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;

use commands::AppState;
use app_core::database;

#[tokio::main]
async fn main() {
    // Initialize logging
    env_logger::init();

    // Initialize the database connection pool
    let db_pool = database::init_db()
        .await
        .expect("Failed to initialize database");

    tauri::Builder::default()
        .manage(AppState { db_pool }) // Add the database pool to the managed state
        .invoke_handler(tauri::generate_handler![
            // Item commands
            commands::create_item,
            commands::get_item,
            commands::get_all_active_items,
            commands::update_item_price,
            commands::archive_item,
            commands::delete_item,
            // Expense commands
            commands::record_expense,
            commands::get_expenses_for_period,
            commands::calculate_total_for_period,
            // Journal commands
            commands::create_journal_entry,
            commands::get_all_journal_entries,
            // Prayer Request commands
            commands::create_prayer_request,
            commands::get_all_prayer_requests,
            commands::update_prayer_status,
            // Bible Reading commands
            commands::log_bible_reading,
            commands::get_all_bible_readings
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}