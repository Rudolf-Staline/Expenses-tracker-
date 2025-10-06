-- Create Items Table
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    packaging TEXT,
    family TEXT NOT NULL,
    item_type TEXT,
    volume REAL,
    volume_unit TEXT,
    weight REAL,
    weight_unit TEXT,
    archived BOOLEAN NOT NULL DEFAULT 0
);

-- Create Price History Table
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    price REAL NOT NULL,
    effective_date DATETIME NOT NULL, -- Using DATETIME for chrono::DateTime<Utc>
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- Create Expenses Table
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    price_at_time_of_expense REAL NOT NULL,
    expense_date DATE NOT NULL, -- Using DATE for chrono::NaiveDate
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE RESTRICT -- Prevent deleting items with expenses
);

-- Create Daily Adjustments Table
CREATE TABLE IF NOT EXISTS daily_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adjustment_date DATE NOT NULL UNIQUE,
    amount REAL NOT NULL
);