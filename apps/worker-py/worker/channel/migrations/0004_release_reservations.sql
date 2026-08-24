CREATE TABLE release_reservations (
    reservation_id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL REFERENCES content_items(content_id),
    program_id TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    timezone TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    intent_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    cancelled_at TEXT,
    cancellation_reason TEXT
);

CREATE UNIQUE INDEX idx_release_active_content
ON release_reservations(content_id)
WHERE cancelled_at IS NULL;

CREATE UNIQUE INDEX idx_release_active_time
ON release_reservations(scheduled_at)
WHERE cancelled_at IS NULL;

CREATE INDEX idx_release_schedule
ON release_reservations(cancelled_at, scheduled_at);
