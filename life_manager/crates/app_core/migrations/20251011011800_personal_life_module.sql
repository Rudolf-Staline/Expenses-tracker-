-- Create Journal Entries Table
CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL
);

-- Create Prayer Requests Table
CREATE TABLE IF NOT EXISTS prayer_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    details TEXT,
    status TEXT NOT NULL,
    created_at DATETIME NOT NULL
);

-- Create Bible Readings Table
CREATE TABLE IF NOT EXISTS bible_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verses TEXT NOT NULL,
    read_at DATETIME NOT NULL
);