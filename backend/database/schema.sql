CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    embedding_vector DOUBLE PRECISION[] NOT NULL
);

CREATE TABLE IF NOT EXISTS attendances (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_id VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'present'
);

CREATE INDEX IF NOT EXISTS ix_attendances_employee_ts ON attendances(employee_id, timestamp DESC);
