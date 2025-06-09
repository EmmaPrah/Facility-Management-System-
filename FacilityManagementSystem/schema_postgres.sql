-- PostgreSQL schema for Facility Management System

CREATE TABLE facilities (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE maintenance_requests (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER NOT NULL REFERENCES facilities(id),
    description TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'Low',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'Pending'
);

-- Cleaning Checklist Tables
CREATE TABLE cleaning_areas (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE cleaning_tasks (
    id SERIAL PRIMARY KEY,
    area_id INTEGER NOT NULL REFERENCES cleaning_areas(id),
    description TEXT NOT NULL
);

CREATE TABLE cleaning_log_entries (
    id SERIAL PRIMARY KEY,
    facility_id INTEGER NOT NULL REFERENCES cleaning_areas(id),
    task_id INTEGER NOT NULL REFERENCES cleaning_tasks(id),
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'Pending',
    notes TEXT
    -- completed_by_user_id INTEGER, -- For future user integration
    -- FOREIGN KEY (completed_by_user_id) REFERENCES users(id)
);

CREATE TABLE expenditures (
    id SERIAL PRIMARY KEY,
    expenditure_date DATE NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    vendor TEXT,
    facility_id INTEGER REFERENCES facilities(id),
    receipt_reference TEXT,
    notes TEXT,
    means_of_payment TEXT,
    buyer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE archived_reports (
    id SERIAL PRIMARY KEY,
    report_type TEXT NOT NULL DEFAULT 'weekly',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_start_date DATE NOT NULL,
    period_end_date DATE NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'success',
    error_message TEXT
);

CREATE TABLE report_recipients (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
