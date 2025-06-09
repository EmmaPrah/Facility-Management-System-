CREATE TABLE IF NOT EXISTS facilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS maintenance_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'Low',
    reported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'Pending', -- Pending, In Progress, Resolved
    FOREIGN KEY (facility_id) REFERENCES facilities (id)
);

-- Cleaning Checklist Tables

CREATE TABLE IF NOT EXISTS cleaning_areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS cleaning_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (area_id) REFERENCES cleaning_areas (id)
);

CREATE TABLE IF NOT EXISTS cleaning_log_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'Pending', -- Pending, Completed, Skipped
    notes TEXT,
    -- completed_by_user_id INTEGER, -- For future user integration
    FOREIGN KEY (facility_id) REFERENCES cleaning_areas (id),
    FOREIGN KEY (task_id) REFERENCES cleaning_tasks (id)
    -- FOREIGN KEY (completed_by_user_id) REFERENCES users (id) -- For future user integration
);

DROP TABLE IF EXISTS expenditures;
CREATE TABLE IF NOT EXISTS expenditures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expenditure_date DATE NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    vendor TEXT,
    facility_id INTEGER,
    receipt_reference TEXT,
    notes TEXT,
    means_of_payment TEXT, -- Added for means of payment
    buyer TEXT, -- Added for buyer information
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES facilities (id)
);


CREATE TABLE IF NOT EXISTS archived_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT NOT NULL DEFAULT 'weekly', -- e.g., weekly, monthly
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    file_path TEXT NOT NULL UNIQUE, -- Path to the generated HTML report file
    status TEXT NOT NULL DEFAULT 'success', -- e.g., success, failed
    error_message TEXT -- To store any error if generation failed
);

CREATE TABLE IF NOT EXISTS report_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
